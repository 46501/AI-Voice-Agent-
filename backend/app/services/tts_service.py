import openai
from app.config import config

client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)

class TTSService:
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize text to speech using OpenAI TTS.
        Returns mp3 audio bytes.
        """
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
            
        response = await client.audio.speech.create(
            model=config.TTS_MODEL,
            voice=config.TTS_VOICE,
            input=text
        )
        return response.read()
