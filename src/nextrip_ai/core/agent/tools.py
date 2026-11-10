import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool

from nextrip_ai.core.config import settings

logger = logging.getLogger(__name__)


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
    search_travel_knowledge_tool,
    estimate_travel_cost_tool,
    generate_itinerary_tool
]

