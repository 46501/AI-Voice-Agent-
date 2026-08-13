import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    STT_MODEL = os.getenv("STT_MODEL", "whisper-1")
    TTS_MODEL = os.getenv("TTS_MODEL", "tts-1")
    TTS_VOICE = os.getenv("TTS_VOICE", "alloy")
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    VAD_SILENCE_MS = int(os.getenv("VAD_SILENCE_MS", "800"))
    
config = Config()
