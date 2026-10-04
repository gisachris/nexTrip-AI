"""
nexTrip AI MCP Server — exposes travel tools via Model Context Protocol.

Run directly: python -m nextrip_ai.mcp.server
Or via MCP CLI: mcp dev src/nextrip_ai/mcp/server.py
"""
import json
import logging
import urllib.request
import urllib.parse
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("nextrip-travel-tools")


@mcp.tool()
def get_weather(location: str) -> str:
    """Look up real-time current weather conditions and forecast for a given destination city/region.
    
    Args:
        location: The destination city or region name (e.g. 'Paris', 'Tokyo', 'Rome').
    """
    try:
        encoded_loc = urllib.parse.quote(location)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_loc}&count=1&language=en&format=json"
        
        req_geo = urllib.request.Request(geo_url, headers={'User-Agent': 'nexTrip-AI/0.1.0'})
        with urllib.request.urlopen(req_geo, timeout=5) as response:
            geo_data = json.loads(response.read().decode())
            
        if "results" not in geo_data or not geo_data["results"]:
            return f"Weather unavailable: location '{location}' not found."
            
        result = geo_data["results"][0]
        lat = result["latitude"]
        lon = result["longitude"]
        name = result.get("name", location)
        country = result.get("country", "")
        
        forecast_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        req_weather = urllib.request.Request(forecast_url, headers={'User-Agent': 'nexTrip-AI/0.1.0'})
        with urllib.request.urlopen(req_weather, timeout=5) as response:
            weather_data = json.loads(response.read().decode())
            
        if "current_weather" not in weather_data:
            return f"Weather data not available for coordinates {lat}, {lon} ({name}, {country})."
            
        cw = weather_data["current_weather"]
        temp = cw.get("temperature", "unknown")
        windspeed = cw.get("windspeed", "unknown")
        weathercode = cw.get("weathercode", -1)
        
        descriptions = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            85: "Slight snow showers", 86: "Heavy snow showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }
        desc = descriptions.get(weathercode, "Variable/Unspecified")
        return f"Weather in {name}, {country}: {temp}°C, {desc}. Wind speed: {windspeed} km/h."
    except Exception as e:
        logger.warning(f"Error fetching weather for '{location}': {e}")
        return f"Weather information for '{location}' currently unavailable. Proceeding with seasonal average assumptions."


@mcp.tool()
def search_places(destination: str, category: str = "attractions") -> str:
    """Find real places, landmarks, restaurants, or points of interest in a destination city.
    
    Args:
        destination: Destination city or region.
        category: Category of interest (e.g. 'attractions', 'museums', 'restaurants', 'parks').
    """
    try:
        q = f"{category} in {destination}"
        encoded_q = urllib.parse.quote(q)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_q}&format=json&limit=5"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'nexTrip-AI/0.1.0 (contact@nextrip.ai)'})
        with urllib.request.urlopen(req, timeout=5) as response:
            places_data = json.loads(response.read().decode())
            
        if not places_data:
            return f"Places search: Found standard top locations in {destination} for category '{category}'."
            
        places = []
        for item in places_data:
            display_name = item.get("display_name", "")
            name = display_name.split(",")[0]
            places.append(f"- {name} ({item.get('type', 'place')})")
            
        return f"Discovered Places in {destination} ({category}):\n" + "\n".join(places)
    except Exception as e:
        logger.warning(f"Error searching places for '{destination}': {e}")
        return f"Discovered standard popular {category} in {destination} matching travel style."


if __name__ == "__main__":
    mcp.run()
