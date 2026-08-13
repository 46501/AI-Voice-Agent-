from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
from app.services.agent_service import AgentService
from app.services.stt_service import STTService
from app.services.tts_service import TTSService
import base64

router = APIRouter()
agent_service = AgentService()
stt_service = STTService()
tts_service = TTSService()

@router.websocket("/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = "default-session"  # Could be passed in connection URL or first message
    print(f"WebSocket connected: {session_id}")
    
    try:
        while True:
            # We expect either JSON commands or binary audio data
            message = await websocket.receive()
            
            if "bytes" in message:
                audio_data = message["bytes"]
                print(f"Received audio blob of size {len(audio_data)} bytes")
                
                # 1. Speech-to-Text
                try:
                    await websocket.send_json({"type": "status", "status": "processing_stt"})
                    transcript = await stt_service.transcribe(audio_data)
                    print(f"Transcript: {transcript}")
                    await websocket.send_json({"type": "transcript", "role": "user", "text": transcript})
                    
                    if not transcript.strip():
                        await websocket.send_json({"type": "status", "status": "idle"})
                        continue
                except Exception as e:
                    print(f"STT Error: {e}")
                    await websocket.send_json({"type": "error", "message": "Failed to understand audio."})
                    continue

                # 2. Agent Logic (LLM + Tools)
                try:
                    await websocket.send_json({"type": "status", "status": "thinking"})
                    response_text, tool_calls = await agent_service.process_message(session_id, transcript)
                    print(f"AI Response: {response_text}")
                    await websocket.send_json({"type": "transcript", "role": "ai", "text": response_text})
                except Exception as e:
                    print(f"Agent Error: {e}")
                    await websocket.send_json({"type": "error", "message": "AI failed to generate response."})
                    continue
                
                # 3. Text-to-Speech
                try:
                    await websocket.send_json({"type": "status", "status": "speaking"})
                    audio_buffer = await tts_service.synthesize(response_text)
                    # Send audio buffer directly as bytes or base64. 
                    # For simplicity in browser, base64 data URI might be easier if we use simple HTML Audio,
                    # but since we use Web Audio API, raw bytes is great.
                    await websocket.send_bytes(audio_buffer)
                    await websocket.send_json({"type": "status", "status": "idle"})
                except Exception as e:
                    print(f"TTS Error: {e}")
                    await websocket.send_json({"type": "error", "message": "Failed to generate speech."})
                    continue
                
            elif "text" in message:
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif data.get("type") == "clear":
                        agent_service.clear_session(session_id)
                        await websocket.send_json({"type": "status", "status": "cleared"})
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        print(f"WebSocket unhandled error: {e}")
