from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
import re
import uuid
import time
from loguru import logger
from app.services.agent_service import AgentService
from app.services.stt_service import STTService
from app.services.tts_service import TTSService

router = APIRouter()
agent_service = AgentService()
stt_service = STTService()
tts_service = TTSService()

SENTENCE_END_REGEX = re.compile(r'([.?!]["\']?)')

async def process_voice_pipeline(websocket: WebSocket, session_id: str, turn_id: str, audio_data: bytes):
    current_stage = "stt"
    try:
        t0 = time.time()
        logger.info(f"[VOICE] session={session_id} turn={turn_id} state=STT_START")
        await websocket.send_json({"type": "status", "status": "processing_stt", "turn_id": turn_id})
        
        # 1. STT
        transcript = await stt_service.transcribe(audio_data)
        stt_latency = int((time.time() - t0) * 1000)
        logger.info(f"[VOICE] session={session_id} turn={turn_id} state=STT_DONE latency={stt_latency}ms transcript='{transcript}'")
        
        await websocket.send_json({
            "type": "transcript", 
            "role": "user", 
            "text": transcript,
            "turn_id": turn_id,
            "metrics": {"stt_ms": stt_latency}
        })
        
        if not transcript.strip():
            await websocket.send_json({"type": "status", "status": "idle", "turn_id": turn_id})
            return

        # 2. LLM Stream
        current_stage = "llm"
        await websocket.send_json({"type": "status", "status": "thinking", "turn_id": turn_id})
        logger.info(f"[VOICE] session={session_id} turn={turn_id} state=LLM_START")
        
        t_llm_start = time.time()
        buffer = ""
        tts_tasks = []
        full_ai_text = ""
        has_started_speaking = False
        first_token_latency = None
        
        async def synthesize_and_send(text_chunk: str, chunk_index: int):
            if not text_chunk.strip():
                return None
            try:
                t_tts_start = time.time()
                current_stage = "tts"
                audio_bytes = await tts_service.synthesize(text_chunk)
                tts_latency = int((time.time() - t_tts_start) * 1000)
                logger.info(f"[VOICE] session={session_id} turn={turn_id} chunk={chunk_index} state=TTS_DONE latency={tts_latency}ms text='{text_chunk}'")
                return audio_bytes, tts_latency
            except Exception as e:
                logger.error(f"[VOICE] TTS Error on chunk: {e}")
                return None, 0

        chunk_counter = 0
        first_audio_latency = None

        async for token in agent_service.process_message_stream(session_id, transcript):
            if isinstance(token, dict) and token.get("type") == "tool_call":
                logger.info(f"[VOICE] session={session_id} turn={turn_id} state=TOOL_CALL tool={token['name']}")
                await websocket.send_json({
                    "type": "transcript",
                    "role": "tool",
                    "text": f"Using {token['name']}...",
                    "turn_id": turn_id
                })
                continue
                
            if first_token_latency is None:
                first_token_latency = int((time.time() - t_llm_start) * 1000)
                logger.info(f"[VOICE] session={session_id} turn={turn_id} state=LLM_FIRST_TOKEN latency={first_token_latency}ms")
                
            buffer += token
            full_ai_text += token
            
            await websocket.send_json({
                "type": "transcript", 
                "role": "ai", 
                "text": full_ai_text, 
                "partial": True, 
                "turn_id": turn_id
            })
            
            if SENTENCE_END_REGEX.search(buffer):
                parts = SENTENCE_END_REGEX.split(buffer, 1)
                sentence = parts[0] + parts[1]
                buffer = parts[2] if len(parts) > 2 else ""
                
                chunk_counter += 1
                tts_tasks.append(asyncio.create_task(synthesize_and_send(sentence, chunk_counter)))
                
                if not has_started_speaking and len(tts_tasks) == 1:
                    result = await tts_tasks[0]
                    if result and result[0]:
                        audio_bytes, tts_ms = result
                        if first_audio_latency is None:
                            first_audio_latency = int((time.time() - t0) * 1000)
                            logger.info(f"[VOICE] session={session_id} turn={turn_id} state=FIRST_AUDIO_READY total_latency={first_audio_latency}ms")
                        
                        await websocket.send_json({
                            "type": "status", 
                            "status": "speaking", 
                            "turn_id": turn_id,
                            "metrics": {"llm_first_token_ms": first_token_latency, "first_audio_ms": first_audio_latency, "tts_ms": tts_ms}
                        })
                        await websocket.send_bytes(audio_bytes)
                    has_started_speaking = True
                    tts_tasks.pop(0)
        
        if buffer.strip():
            chunk_counter += 1
            tts_tasks.append(asyncio.create_task(synthesize_and_send(buffer, chunk_counter)))
            
        for task in tts_tasks:
            result = await task
            if result and result[0]:
                audio_bytes, tts_ms = result
                if not has_started_speaking:
                    if first_audio_latency is None:
                        first_audio_latency = int((time.time() - t0) * 1000)
                    await websocket.send_json({
                        "type": "status", 
                        "status": "speaking", 
                        "turn_id": turn_id,
                        "metrics": {"llm_first_token_ms": first_token_latency, "first_audio_ms": first_audio_latency, "tts_ms": tts_ms}
                    })
                    has_started_speaking = True
                await websocket.send_bytes(audio_bytes)
                
        total_latency = int((time.time() - t0) * 1000)
        logger.info(f"[VOICE] session={session_id} turn={turn_id} state=TURN_COMPLETE total_latency={total_latency}ms")
        
        await websocket.send_json({
            "type": "transcript", 
            "role": "ai", 
            "text": full_ai_text, 
            "partial": False, 
            "turn_id": turn_id,
            "metrics": {"total_ms": total_latency}
        })
        await websocket.send_json({"type": "status", "status": "idle", "turn_id": turn_id})
        
    except asyncio.CancelledError:
        logger.warning(f"[VOICE] session={session_id} turn={turn_id} state=INTERRUPTED")
        raise
    except Exception as e:
        logger.error(f"[VOICE] session={session_id} turn={turn_id} state=ERROR error='{e}'")
        error_code = "UNKNOWN_ERROR"
        user_message = "Something went wrong while connecting to the AI. Please try again in a moment."
        debug_message = str(e)
        
        if "API key" in debug_message or "invalid_api_key" in debug_message or "401" in debug_message:
            error_code = "INVALID_API_KEY"
            user_message = "The AI service is temporarily unavailable. Please try again later."
        elif current_stage == "stt":
            error_code = "STT_FAILED"
            user_message = "I couldn't understand your voice. Please try again."
        elif current_stage == "llm":
            error_code = "LLM_FAILED"
            user_message = "I couldn't generate a response right now. Please try again."
        elif current_stage == "tts":
            error_code = "TTS_FAILED"
            user_message = "I generated a response but couldn't play the voice."
            
        await websocket.send_json({
            "type": "error", 
            "code": error_code,
            "stage": current_stage,
            "user_message": user_message,
            "debug_message": debug_message,
            "turn_id": turn_id
        })

@router.websocket("/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info(f"[WEBSOCKET] Connected session={session_id}")
    
    current_task: asyncio.Task | None = None
    active_turn_id: str | None = None
    
    try:
        while True:
            message = await websocket.receive()
            
            if "bytes" in message:
                audio_data = message["bytes"]
                turn_id = str(uuid.uuid4())
                active_turn_id = turn_id
                
                if current_task and not current_task.done():
                    logger.info(f"[WEBSOCKET] session={session_id} received audio while task running. Cancelling previous task.")
                    current_task.cancel()
                    
                current_task = asyncio.create_task(process_voice_pipeline(websocket, session_id, turn_id, audio_data))
                
            elif "text" in message:
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif data.get("type") == "clear":
                        agent_service.clear_session(session_id)
                        await websocket.send_json({"type": "status", "status": "cleared"})
                    elif data.get("type") == "interrupt":
                        logger.info(f"[WEBSOCKET] session={session_id} received explicit INTERRUPT")
                        if current_task and not current_task.done():
                            current_task.cancel()
                        active_turn_id = None
                        await websocket.send_json({"type": "status", "status": "idle"})
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        logger.info(f"[WEBSOCKET] Disconnected session={session_id}")
        if current_task and not current_task.done():
            current_task.cancel()
    except Exception as e:
        logger.error(f"[WEBSOCKET] Unhandled error session={session_id}: {e}")
