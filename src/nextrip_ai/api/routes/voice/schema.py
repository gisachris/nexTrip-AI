"""Pydantic schemas for voice endpoints."""
from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    text: str = Field(..., description="Transcribed text from audio input")


class SpeechRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech", json_schema_extra={"example": "Plan a 3-day trip to Paris with a cultural focus."})


class ImageAnalysisResponse(BaseModel):
    description: str = Field(..., description="AI-generated description and analysis of the travel image")
    media_type: str = Field(..., description="MIME type of the uploaded image")
