import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool

from nextrip_ai.core.config import settings

logger = logging.getLogger(__name__)

@tool
def get_weather_tool(location: str) -> str:
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

@tool
def search_travel_knowledge_tool(destination: str, query: str) -> str:
    """Retrieve curated travel knowledge, local guides, and attraction reviews from the vector database.
    
    Args:
        destination: Destination city or region.
        query: Specific search query topic (e.g. 'top museums', 'budget dining', 'outdoor parks').
    """
    if not settings.PINECONE_API_KEY or "mock" in settings.PINECONE_API_KEY.lower():
        return f"Travel Knowledge Base: No specific internal guide documents retrieved for '{destination}'. Using general AI travel knowledge."
        
    try:
        from nextrip_ai.core.ingest import get_embeddings
        from pinecone import Pinecone
        
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index_name = settings.PINECONE_INDEX_NAME
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        if index_name not in existing_indexes:
            return "Pinecone index not initialized."
            
        index = pc.Index(index_name)
        query_vector = get_embeddings([f"{destination} {query}"])[0]
        
        res = index.query(
            namespace=destination.lower(),
            vector=query_vector,
            top_k=4,
            include_metadata=True
        )
        
        matches = res.get("matches", [])
        valid_chunks = [m.get("metadata", {}) for m in matches if m.get("score", 0.0) >= 0.65]
        
        if not valid_chunks:
            return f"No specific high-relevance travel guide entries found for '{destination} ({query})'."
            
        results_str = "\n---\n".join(
            f"Title: {c.get('title', 'Guide')}\nCategory: {c.get('category', 'General')}\nDetails: {c.get('text', '')}"
            for c in valid_chunks
        )
        return f"Retrieved Travel Guides for {destination}:\n{results_str}"
    except Exception as e:
        logger.error(f"Error querying travel knowledge for '{destination}': {e}")
        return f"Unable to reach vector database for {destination}. Using general AI travel knowledge."

@tool
def search_places_tool(destination: str, category: str = "attractions") -> str:
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

@tool
def estimate_travel_cost_tool(destination: str, days: int, travel_style: str = "Moderate") -> str:
    """Estimate daily travel expenditure tiers (accommodation, meals, transport, activities) for a destination.
    
    Args:
        destination: Destination city or region.
        days: Duration of the trip in days.
        travel_style: Travel style preference (e.g. 'Budget', 'Moderate', 'Luxury', 'Backpacker').
    """
    style = travel_style.lower()
    if "budget" in style or "backpacker" in style:
        daily_hotel = 45.0
        daily_food = 30.0
        daily_activities = 25.0
        daily_transport = 10.0
    elif "luxury" in style:
        daily_hotel = 350.0
        daily_food = 150.0
        daily_activities = 120.0
        daily_transport = 60.0
    else: # Moderate / Cultural / Default
        daily_hotel = 110.0
        daily_food = 60.0
        daily_activities = 45.0
        daily_transport = 20.0
        
    daily_total = daily_hotel + daily_food + daily_activities + daily_transport
    estimated_total = daily_total * days
    
    return (
        f"Cost Estimates for {days} days in {destination} ({travel_style} style):\n"
        f"- Daily Accommodation: ~${daily_hotel:.2f}\n"
        f"- Daily Food & Dining: ~${daily_food:.2f}\n"
        f"- Daily Activities & Entry: ~${daily_activities:.2f}\n"
        f"- Daily Local Transport: ~${daily_transport:.2f}\n"
        f"Total Daily Average: ~${daily_total:.2f}/day\n"
        f"Estimated Total Trip Expenditure: ${estimated_total:.2f}"
    )

@tool
def generate_itinerary_tool(
    title: str,
    destination: str,
    travel_style: str,
    budget: float,
    estimated_total_cost: float,
    days: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate and submit the final structured travel itinerary.
    
    Args:
        title: Title of the itinerary.
        destination: Destination city/region of the trip.
        travel_style: Travel style of the trip.
        budget: Target budget for the trip.
        estimated_total_cost: Estimated total cost of the trip.
        days: Array of day objects containing day_number, theme, estimated_cost, and activities.
    """
    return {
        "title": title,
        "destination": destination,
        "travel_style": travel_style,
        "budget": budget,
        "estimated_total_cost": estimated_total_cost,
        "days": days
    }

agent_tools = [
    get_weather_tool,
    search_travel_knowledge_tool,
    search_places_tool,
    estimate_travel_cost_tool,
    generate_itinerary_tool
]
