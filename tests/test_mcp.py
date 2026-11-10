"""Tests for MCP server tools."""
import pytest
from unittest.mock import patch, MagicMock

import nextrip_ai.mcp.server as mcp_server
from nextrip_ai.mcp.server import get_weather, search_places


class TestMCPWeatherTool:
    """Verify MCP weather tool returns formatted weather data."""
    
    @patch("nextrip_ai.mcp.server.urllib.request.urlopen")
    def test_get_weather_success(self, mock_urlopen):
        # Mock geocoding response
        geo_response = MagicMock()
        geo_response.read.return_value = b'{"results":[{"latitude":48.85,"longitude":2.35,"name":"Paris","country":"France"}]}'
        geo_response.__enter__ = lambda s: s
        geo_response.__exit__ = MagicMock(return_value=False)
        
        # Mock weather response
        weather_response = MagicMock()
        weather_response.read.return_value = b'{"current_weather":{"temperature":22,"windspeed":10,"weathercode":0}}'
        weather_response.__enter__ = lambda s: s
        weather_response.__exit__ = MagicMock(return_value=False)
        
        mock_urlopen.side_effect = [geo_response, weather_response]
        
        result = get_weather("Paris")
        assert "Paris" in result
        assert "22" in result
    
    @patch("nextrip_ai.mcp.server.urllib.request.urlopen")
    def test_get_weather_unknown_location(self, mock_urlopen):
        geo_response = MagicMock()
        geo_response.read.return_value = b'{"results":[]}'
        geo_response.__enter__ = lambda s: s
        geo_response.__exit__ = MagicMock(return_value=False)
        
        mock_urlopen.return_value = geo_response
        
        result = get_weather("Nonexistentville")
        assert "unavailable" in result.lower() or "not found" in result.lower()


class TestMCPPlacesTool:
    """Verify MCP places tool returns place listings."""
    
    @patch("nextrip_ai.mcp.server.urllib.request.urlopen")
    def test_search_places_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'[{"display_name":"Eiffel Tower, Paris","type":"attraction"}]'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        
        mock_urlopen.return_value = mock_response
        
        result = search_places("Paris", "attractions")
        assert "Eiffel Tower" in result
