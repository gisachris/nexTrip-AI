"""Speech-to-Text and Text-to-Speech services using OpenAI APIs."""
import logging
from io import BytesIO
from openai import OpenAI

from nextrip_ai.core.config import settings

logger = logging.getLogger(__name__)


def get_openai_client() -> OpenAI:
    """Get an OpenAI client instance."""
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Convert speech audio to text using OpenAI Whisper API.
    
    Args:
        audio_bytes: Raw audio file bytes.
        filename: Original filename with extension (for format detection).
        
    Returns:
        Transcribed text string.
    """
    client = get_openai_client()
    
    audio_file = BytesIO(audio_bytes)
    audio_file.name = filename
    
    transcript = client.audio.transcriptions.create(
        model=settings.OPENAI_STT_MODEL,
        file=audio_file,
        language="en"
    )
    
    return transcript.text


def synthesize_speech(text: str) -> bytes:
    """
    Convert text to speech audio using OpenAI TTS API.
    
    Args:
        text: Text to convert to speech.
        
    Returns:
        Audio bytes in MP3 format.
    """
    client = get_openai_client()
    
    response = client.audio.speech.create(
        model=settings.OPENAI_TTS_MODEL,
        voice=settings.OPENAI_TTS_VOICE,
        input=text,
        response_format="mp3"
    )
    
    return response.content
