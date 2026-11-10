"""Image understanding service using Anthropic Claude Vision."""
import base64
import logging
from anthropic import Anthropic

from nextrip_ai.core.config import settings

logger = logging.getLogger(__name__)


def analyze_travel_image(image_bytes: bytes, media_type: str = "image/jpeg", user_prompt: str | None = None) -> str:
    """
    Analyze a travel photo using Claude Vision and return a description.
    
    Args:
        image_bytes: Raw image file bytes.
        media_type: MIME type of the image (e.g. 'image/jpeg', 'image/png').
        user_prompt: Optional custom prompt. Defaults to travel-focused analysis.
        
    Returns:
        Description string from Claude Vision.
    """
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    prompt = user_prompt or (
        "You are an expert travel advisor. Analyze this travel photo and provide:\n"
        "1. Location identification (city, country, landmark if recognizable)\n"
        "2. Key attractions or points of interest visible\n"
        "3. Season/weather assessment from visual cues\n"
        "4. Travel recommendations based on what you see\n"
        "Be specific and actionable. If you can identify the exact location, say so."
    )
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
    )
    
    return response.content[0].text
