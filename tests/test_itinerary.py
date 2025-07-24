import pytest
from nextrip_ai.api.routes.itineraries.router import get_weather, validate_itinerary
from nextrip_ai.models.trip import Trip
from nextrip_ai.api.routes.itineraries.schema import AIItinerarySchema

def test_get_weather_success():
    """Verify that get_weather can look up weather for a real city (Paris) successfully."""
    res = get_weather("Paris")
    assert "Weather in Paris" in res or "temperature" in res.lower()
    assert "Error" not in res

def test_get_weather_failure():
    """Verify that get_weather handles unknown locations gracefully."""
    res = get_weather("ThisIsNotARealCityName12345")
    assert "Weather unavailable" in res or "not found" in res.lower()

def test_validate_itinerary_correct():
    """Verify that a correct itinerary passes validation."""
    trip = Trip(destination="Paris", days=2, budget=1000, trip_style="Cultural")
    
    valid_data = {
        "title": "Beautiful Paris Itinerary",
        "destination": "Paris, France",
        "travel_style": "Cultural",
        "budget": 1000.0,
        "estimated_total_cost": 850.0,
        "days": [
            {
                "day_number": 1,
                "theme": "Museums & History",
                "estimated_cost": 450.0,
                "activities": [
                    {
                        "time": "Morning",
                        "activity": "Louvre Museum Tour",
                        "location": "Louvre Museum",
                        "description": "Explore masterpieces including the Mona Lisa.",
                        "estimated_cost": 150.0
                    },
                    {
                        "time": "Afternoon",
                        "activity": "Seine River Cruise",
                        "location": "Seine River",
                        "description": "Relax on a cruise along the Seine.",
                        "estimated_cost": 300.0
                    }
                ]
            },
            {
                "day_number": 2,
                "theme": "Landmarks & Cafes",
                "estimated_cost": 400.0,
                "activities": [
                    {
                        "time": "Morning",
                        "activity": "Eiffel Tower Visit",
                        "location": "Eiffel Tower",
                        "description": "Go up to the top floor of the tower.",
                        "estimated_cost": 250.0
                    },
                    {
                        "time": "Afternoon",
                        "activity": "Cafe Break",
                        "location": "Saint-Germain",
                        "description": "Enjoy french pastry and espresso.",
                        "estimated_cost": 150.0
                    }
                ]
            }
        ]
    }
    
    errors = validate_itinerary(valid_data, trip)
    assert len(errors) == 0

def test_validate_itinerary_validation_errors():
    """Verify that validation errors are correctly captured (e.g. wrong destination, budget overrun, wrong day count)."""
    trip = Trip(destination="Paris", days=2, budget=1000, trip_style="Cultural")
    
    invalid_data = {
        "title": "Beautiful Paris Itinerary",
        "destination": "Tokyo, Japan",
        "travel_style": "Cultural",
        "budget": 1000.0,
        "estimated_total_cost": 1500.0,
        "days": [
            {
                "day_number": 1,
                "theme": "Museums & History",
                "estimated_cost": 450.0,
                "activities": [
                    {
                        "time": "Morning",
                        "activity": "Louvre Museum Tour",
                        "location": "Louvre Museum",
                        "description": "Explore masterpieces.",
                        "estimated_cost": 450.0
                    }
                ]
            }
        ]
    }
    
    errors = validate_itinerary(invalid_data, trip)
    assert len(errors) > 0
    assert any("does not match trip destination" in e for e in errors)
    assert any("exceeds budget" in e for e in errors)
    assert any("duration" in e or "Day count" in e for e in errors)
