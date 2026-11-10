"""Voice and multimodal API endpoints."""
import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import Response

from nextrip_ai.core.auth import get_current_user
from nextrip_ai.models.user import User
from nextrip_ai.core.multimodal.speech import transcribe_audio, synthesize_speech
from nextrip_ai.core.multimodal.vision import analyze_travel_image
from nextrip_ai.api.routes.voice.schema import (
    TranscriptionResponse, SpeechRequest, ImageAnalysisResponse
)

logger = logging.getLogger(__name__)

voiceRouter = APIRouter(prefix="/voice", tags=["voice & multimodal"])


@voiceRouter.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    file: UploadFile = File(..., description="Audio file (webm, mp3, wav, m4a)"),
    current_user: User = Depends(get_current_user),
):
    """Convert speech audio to text using OpenAI Whisper.
    
    Accepts audio files up to 25MB. Supported formats: webm, mp3, wav, m4a, ogg, flac.
    The transcribed text can be used as input for the agent query endpoint.
    """
    ALLOWED_TYPES = {"audio/webm", "audio/mpeg", "audio/wav", "audio/mp4", "audio/ogg", "audio/flac", "audio/x-m4a"}
    if file.content_type and file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio format: {file.content_type}. Supported: {', '.join(ALLOWED_TYPES)}"
        )
    
    audio_bytes = await file.read()
    if len(audio_bytes) > 25 * 1024 * 1024:  # 25MB limit
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Audio file exceeds 25MB limit.")
    
    try:
        text = transcribe_audio(audio_bytes, filename=file.filename or "audio.webm")
        return TranscriptionResponse(text=text)
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Transcription failed: {str(e)}")


@voiceRouter.post("/speak", response_class=Response)
async def speak(
    payload: SpeechRequest,
    current_user: User = Depends(get_current_user),
):
    """Convert text to speech audio using OpenAI TTS.
    
    Returns an MP3 audio file. Use this to vocalize agent responses or itinerary summaries.
    """
    try:
        audio_bytes = synthesize_speech(payload.text)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=response.mp3"}
        )
    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Speech synthesis failed: {str(e)}")


@voiceRouter.post("/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(..., description="Travel photo (JPEG, PNG, WebP, GIF)"),
    current_user: User = Depends(get_current_user),
):
    """Analyze a travel photo using Claude Vision.
    
    Upload a travel photo and receive AI-powered location identification,
    attraction recognition, and travel recommendations.
    """
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    content_type = file.content_type or "image/jpeg"
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image format: {content_type}. Supported: {', '.join(ALLOWED_TYPES)}"
        )
    
    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image file exceeds 20MB limit.")
    
    try:
        description = analyze_travel_image(image_bytes, media_type=content_type)
        return ImageAnalysisResponse(description=description, media_type=content_type)
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Image analysis failed: {str(e)}")
