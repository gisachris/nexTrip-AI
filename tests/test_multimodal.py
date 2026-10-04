"""Tests for multimodal (voice + vision) functionality."""
import pytest
from unittest.mock import patch, MagicMock
from nextrip_ai.core.multimodal.speech import transcribe_audio, synthesize_speech
from nextrip_ai.core.multimodal.vision import analyze_travel_image


class TestTranscribeAudio:
    """Verify speech-to-text transcription via OpenAI Whisper."""
    
    @patch("nextrip_ai.core.multimodal.speech.get_openai_client")
    def test_transcribe_returns_text(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = MagicMock(text="Plan a trip to Paris")
        mock_client_fn.return_value = mock_client
        
        result = transcribe_audio(b"fake-audio-bytes", filename="test.mp3")
        assert result == "Plan a trip to Paris"
        mock_client.audio.transcriptions.create.assert_called_once()
    
    @patch("nextrip_ai.core.multimodal.speech.get_openai_client")
    def test_transcribe_passes_filename(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = MagicMock(text="test")
        mock_client_fn.return_value = mock_client
        
        transcribe_audio(b"audio", filename="recording.webm")
        call_args = mock_client.audio.transcriptions.create.call_args
        assert call_args.kwargs["file"].name == "recording.webm"


class TestSynthesizeSpeech:
    """Verify text-to-speech synthesis via OpenAI TTS."""
    
    @patch("nextrip_ai.core.multimodal.speech.get_openai_client")
    def test_synthesize_returns_bytes(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.audio.speech.create.return_value = MagicMock(content=b"fake-mp3-bytes")
        mock_client_fn.return_value = mock_client
        
        result = synthesize_speech("Hello, welcome to Paris!")
        assert result == b"fake-mp3-bytes"
        mock_client.audio.speech.create.assert_called_once()


class TestAnalyzeTravelImage:
    """Verify image analysis via Claude Vision."""
    
    @patch("nextrip_ai.core.multimodal.vision.Anthropic")
    def test_analyze_returns_description(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is the Eiffel Tower in Paris, France.")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client
        
        result = analyze_travel_image(b"fake-image-bytes", media_type="image/jpeg")
        assert "Eiffel Tower" in result
        mock_client.messages.create.assert_called_once()
    
    @patch("nextrip_ai.core.multimodal.vision.Anthropic")
    def test_analyze_uses_custom_prompt(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="A beach scene")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client
        
        analyze_travel_image(b"img", media_type="image/png", user_prompt="What beach is this?")
        call_args = mock_client.messages.create.call_args
        messages = call_args.kwargs["messages"]
        text_block = messages[0]["content"][1]
        assert text_block["text"] == "What beach is this?"
