import openai
import io
from app.config import config

# We need a client instance
client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)

class STTService:
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio bytes using OpenAI Whisper.
        We'll treat the bytes as a webm file since frontend uses MediaRecorder with webm.
        """
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
            
        # Create an in-memory file-like object with a name so the API knows the format
        file_obj = io.BytesIO(audio_bytes)
        file_obj.name = "audio.webm"
        
        response = await client.audio.transcriptions.create(
            model=config.STT_MODEL,
            file=file_obj,
            response_format="text"
        )
        return response
