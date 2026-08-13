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
    
    # Database
    # Default to sqlite for local direct running if postgres is not available
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./voxai.db")
    
    # Authentication
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week
    
    # Tool APIs
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
    
config = Config()
