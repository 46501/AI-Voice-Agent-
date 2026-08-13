from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
import re
from app.services.agent_service import AgentService
from app.services.stt_service import STTService
from app.services.tts_service import TTSService

router = APIRouter()
agent_service = AgentService()
stt_service = STTService()
tts_service = TTSService()

# Regex to split on sentence endings (. ? ! optionally followed by quotes)
SENTENCE_END_REGEX = re.compile(r'([.?!]["\']?)')

async def process_voice_pipeline(websocket: WebSocket, session_id: str, audio_data: bytes):
    """
    Handles STT -> LLM Stream -> Sentence Chunking -> TTS Concurrency -> Audio dispatch
    This runs as a cancelable Task.
    """
    try:
        # 1. STT
        await websocket.send_json({"type": "status", "status": "processing_stt"})
        transcript = await stt_service.transcribe(audio_data)
        print(f"Transcript: {transcript}")
        await websocket.send_json({"type": "transcript", "role": "user", "text": transcript})
        
        if not transcript.strip():
            await websocket.send_json({"type": "status", "status": "idle"})
            return

        # 2. LLM Stream & TTS Dispatch
        await websocket.send_json({"type": "status", "status": "thinking"})
        
        buffer = ""
        tts_tasks = []
        full_ai_text = ""
        has_started_speaking = False
        
        async def synthesize_and_send(text_chunk: str):
            """Helper to synthesize a chunk and return the audio bytes."""
            if not text_chunk.strip():
                return None
            try:
                return await tts_service.synthesize(text_chunk)
            except Exception as e:
                print(f"TTS Error on chunk: {e}")
                return None

        # Process the stream
        async for token in agent_service.process_message_stream(session_id, transcript):
            buffer += token
            full_ai_text += token
            
            # Send transcript update to UI incrementally (optional, but good for UX)
            # For simplicity, we can send a "partial_transcript" or just wait.
            # Let's send the full text so far as a single message to update the bubble.
            await websocket.send_json({"type": "transcript", "role": "ai", "text": full_ai_text, "partial": True})
            
            # Check for sentence boundaries
            if SENTENCE_END_REGEX.search(buffer):
                # Split at the first sentence boundary
                parts = SENTENCE_END_REGEX.split(buffer, 1)
                sentence = parts[0] + parts[1] # text + punctuation
                buffer = parts[2] if len(parts) > 2 else ""
                
                # Dispatch TTS task for this sentence
                tts_tasks.append(asyncio.create_task(synthesize_and_send(sentence)))
                
                # If this is the first chunk, we can immediately wait for it and send it to reduce TTFB
                if not has_started_speaking and len(tts_tasks) == 1:
                    audio_bytes = await tts_tasks[0]
                    if audio_bytes:
                        await websocket.send_json({"type": "status", "status": "speaking"})
                        await websocket.send_bytes(audio_bytes)
                    has_started_speaking = True
                    tts_tasks.pop(0) # Remove it since we processed it
        
        # Process any remaining text in buffer
        if buffer.strip():
            tts_tasks.append(asyncio.create_task(synthesize_and_send(buffer)))
            
        # Await and send remaining TTS tasks in order
        for task in tts_tasks:
            audio_bytes = await task
            if audio_bytes:
                if not has_started_speaking:
                    await websocket.send_json({"type": "status", "status": "speaking"})
                    has_started_speaking = True
                await websocket.send_bytes(audio_bytes)
                
        # Final transcript update to mark it as complete
        await websocket.send_json({"type": "transcript", "role": "ai", "text": full_ai_text, "partial": False})
        await websocket.send_json({"type": "status", "status": "idle"})
        
    except asyncio.CancelledError:
        print(f"Pipeline cancelled for session {session_id}")
        raise
    except Exception as e:
        print(f"Pipeline Error: {e}")
        await websocket.send_json({"type": "error", "message": "Failed to process voice."})

@router.websocket("/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = "default-session"
    print(f"WebSocket connected: {session_id}")
    
    current_task: asyncio.Task | None = None
    
    try:
        while True:
            message = await websocket.receive()
            
            if "bytes" in message:
                audio_data = message["bytes"]
                print(f"Received audio blob of size {len(audio_data)} bytes")
                
                # Cancel any existing task (implicit barge-in logic if they send audio early)
                if current_task and not current_task.done():
                    current_task.cancel()
                    
                current_task = asyncio.create_task(process_voice_pipeline(websocket, session_id, audio_data))
                
            elif "text" in message:
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif data.get("type") == "clear":
                        agent_service.clear_session(session_id)
                        await websocket.send_json({"type": "status", "status": "cleared"})
                    elif data.get("type") == "interrupt":
                        print("Interrupt received! Cancelling current task.")
                        if current_task and not current_task.done():
                            current_task.cancel()
                        await websocket.send_json({"type": "status", "status": "idle"})
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")
        if current_task and not current_task.done():
            current_task.cancel()
    except Exception as e:
        print(f"WebSocket unhandled error: {e}")
