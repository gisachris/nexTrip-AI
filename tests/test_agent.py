import pytest
from langchain_core.messages import HumanMessage
from nextrip_ai.core.agent.tools import (
    get_weather_tool,
    search_travel_knowledge_tool,
    search_places_tool,
    estimate_travel_cost_tool,
    generate_itinerary_tool
)
from nextrip_ai.core.agent.graph import agent_graph, validate_itinerary_data

def test_get_weather_tool_success():
    """Verify that get_weather_tool fetches weather context."""
    res = get_weather_tool.invoke({"location": "Paris"})
    assert "Weather" in res or "temperature" in res.lower()

def test_search_travel_knowledge_tool_mock():
    """Verify that search_travel_knowledge_tool operates cleanly in mock mode."""
    res = search_travel_knowledge_tool.invoke({"destination": "Paris", "query": "museums"})
    assert "Travel Knowledge" in res or "Paris" in res

def test_search_places_tool():
    """Verify that search_places_tool finds destination attractions."""
    res = search_places_tool.invoke({"destination": "Tokyo", "category": "attractions"})
    assert "Places in Tokyo" in res or "Tokyo" in res

def test_estimate_travel_cost_tool():
    """Verify that estimate_travel_cost_tool returns structured budget estimates."""
    res = estimate_travel_cost_tool.invoke({"destination": "Rome", "days": 3, "travel_style": "Moderate"})
    assert "Cost Estimates for 3 days in Rome" in res
    assert "Estimated Total Trip Expenditure" in res

def test_generate_itinerary_tool():
    """Verify that generate_itinerary_tool formats dictionary payload."""
    payload = {
        "title": "Paris Adventure",
        "destination": "Paris",
        "travel_style": "Cultural",
        "budget": 1000.0,
        "estimated_total_cost": 800.0,
        "days": []
    }
    res = generate_itinerary_tool.invoke(payload)
    assert res["destination"] == "Paris"
    assert res["budget"] == 1000.0

def test_validate_itinerary_data_success():
    """Verify that valid itinerary data passes validation."""
    valid_data = {
        "title": "Explore Paris",
        "destination": "Paris, France",
        "travel_style": "Cultural",
        "budget": 1000.0,
        "estimated_total_cost": 850.0,
        "days": [
            {
                "day_number": 1,
                "theme": "Museums",
                "estimated_cost": 425.0,
                "activities": [
                    {
                        "time": "Morning",
                        "activity": "Louvre Museum",
                        "location": "Louvre",
                        "description": "See Mona Lisa",
                        "estimated_cost": 150.0
                    }
                ]
            },
            {
                "day_number": 2,
                "theme": "Sights",
                "estimated_cost": 425.0,
                "activities": [
                    {
                        "time": "Afternoon",
                        "activity": "Eiffel Tower",
                        "location": "Eiffel Tower",
                        "description": "City views",
                        "estimated_cost": 200.0
                    }
                ]
            }
        ]
    }
    errors = validate_itinerary_data(valid_data, destination="Paris", days=2, budget=1000.0)
    assert len(errors) == 0

def test_agent_graph_execution():
    """Verify that compiled agent_graph executes state workflow cleanly."""
    initial_state = {
        "messages": [HumanMessage(content="Plan a 2-day Paris trip for $1000")],
        "destination": "Paris",
        "days": 2,
        "budget": 1000.0,
        "trip_style": "Cultural",
        "itinerary_data": None,
        "validation_errors": [],
        "attempts": 0
    }
    final_state = agent_graph.invoke(initial_state)
    assert "messages" in final_state
    assert final_state.get("itinerary_data") is not None
