from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
import logging
import urllib.request
import urllib.parse
from anthropic import Anthropic
from pydantic import ValidationError

from nextrip_ai.core.config import settings
from nextrip_ai.core.dependencies import get_db, get_current_user
from nextrip_ai.models.user import User
from nextrip_ai.models.trip import Trip
from nextrip_ai.models.itinerary import Itinerary
from nextrip_ai.api.routes.itineraries.schema import ItineraryCreate, ItineraryResponse, AIItinerarySchema

logger = logging.getLogger(__name__)

itineraryRouter = APIRouter(prefix="/itineraries", tags=["itineraries"])

# Define structured tool schema to force Claude output JSON
tool_schema = {
    "name": "generate_itinerary",
    "description": "Generate a structured travel itinerary matching the required schema exactly.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the itinerary"
            },
            "destination": {
                "type": "string",
                "description": "Destination city/region of the trip"
            },
            "travel_style": {
                "type": "string",
                "description": "Travel style of the trip"
            },
            "budget": {
                "type": "number",
                "description": "The target budget for the trip"
            },
            "estimated_total_cost": {
                "type": "number",
                "description": "The estimated total cost of the trip"
            },
            "days": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "day_number": {
                            "type": "integer",
                            "description": "Day number, starting from 1"
                        },
                        "theme": {
                            "type": "string",
                            "description": "Theme for this day"
                        },
                        "estimated_cost": {
                            "type": "number",
                            "description": "Estimated total cost for this day"
                        },
                        "activities": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "time": {
                                        "type": "string",
                                        "description": "Time of day (e.g. Morning, Afternoon, Evening)"
                                    },
                                    "activity": {
                                        "type": "string",
                                        "description": "Name of the activity"
                                    },
                                    "location": {
                                        "type": "string",
                                        "description": "Location or attraction name"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Description of what the traveler will do"
                                    },
                                    "estimated_cost": {
                                        "type": "number",
                                        "description": "Estimated cost for this activity"
                                    }
                                },
                                "required": ["time", "activity", "location", "description", "estimated_cost"]
                            }
                        }
                    },
                    "required": ["day_number", "theme", "estimated_cost", "activities"]
                }
            }
        },
        "required": ["title", "destination", "travel_style", "budget", "estimated_total_cost", "days"]
    }
}

# Define structured tool schemas
weather_tool_schema = {
    "name": "get_weather",
    "description": "Look up real-time current weather conditions and forecast for a given destination.",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city/region to look up the weather for (e.g. 'Paris', 'Tokyo')."
            }
        },
        "required": ["location"]
    }
}

def get_weather(location: str) -> str:
    """Retrieve weather forecast using Open-Meteo's geocoding and forecast APIs."""
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
        return f"Weather in {name}, {country}: {temp}Â°C, {desc}. Wind speed: {windspeed} km/h."
    except Exception as e:
        return f"Error looking up weather for '{location}': {str(e)}"

def call_claude_to_generate(trip: Trip, messages: list = None) -> tuple[dict, list]:
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    system_prompt = (
        "You are an expert travel planner.\n\n"
        "Your task is to create realistic travel itineraries based on trip information and weather conditions.\n\n"
        "Follow these rules strictly:\n"
        "1. Only recommend attractions, restaurants, landmarks, museums, parks, and activities located inside the specified destination.\n"
        "2. Do not recommend locations outside the destination city or region.\n"
        "3. Respect the provided budget.\n"
        "4. Distribute activities realistically throughout the day.\n"
        "5. Avoid impossible schedules.\n"
        "6. Consider travel time between attractions.\n"
        "7. Include a mix of sightseeing, meals, relaxation, and local experiences.\n"
        "8. Do not invent fictional locations.\n"
        "9. Use well-known and verifiable attractions whenever possible.\n"
        "10. Look up the weather conditions for the destination city using the get_weather tool BEFORE generating the final itinerary, and use the retrieved weather details to optimize the travel plan (e.g., recommend indoor activities if it is rainy/cold, outdoor if sunny/warm).\n"
        "11. Return ONLY the final JSON itinerary via the generate_itinerary tool call.\n"
        "12. Do not include markdown.\n"
        "13. Do not include explanations.\n"
        "14. Do not include code blocks.\n"
        "15. The final itinerary must match the required schema exactly."
    )

    user_prompt = (
        f"Generate a travel itinerary using the following trip details.\n\n"
        f"Trip Details:\n"
        f"Destination: {trip.destination}\n"
        f"Number of Days: {trip.days}\n"
        f"Budget: {trip.budget}\n"
        f"Travel Style: {trip.trip_style}\n\n"
        f"Requirements:\n"
        f"* Use the get_weather tool to look up the current weather and forecast for {trip.destination} first.\n"
        f"* Adjust the activities and suggestions based on the weather forecast.\n"
        f"* Create a detailed itinerary for every day.\n"
        f"* Keep activities geographically sensible.\n"
        f"* Avoid excessive travel between locations.\n"
        f"* Include morning, afternoon, and evening activities.\n"
        f"* Include meal suggestions.\n"
        f"* Estimate approximate activity costs.\n"
        f"* Keep total estimated spending within the trip budget.\n"
        f"* Focus on attractions matching the travel style.\n"
        f"* Only include places located within the destination area.\n"
        f"* Use real attractions and locations.\n"
        f"* Use the generate_itinerary tool to return the final result."
    )

    if not messages:
        messages = [{"role": "user", "content": user_prompt}]
        
    tools = [tool_schema, weather_tool_schema]

    for _ in range(5):
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=4000,
            temperature=0.3,
            system=system_prompt,
            messages=messages,
            tools=tools
        )
        
        # Add assistant response to message history
        assistant_content = []
        for block in response.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
        
        messages.append({"role": "assistant", "content": assistant_content})
        
        tool_use_calls = [block for block in response.content if block.type == "tool_use"]
        
        if not tool_use_calls:
            messages.append({
                "role": "user",
                "content": "Please generate the itinerary by invoking the generate_itinerary tool."
            })
            continue
            
        tool_results = []
        generate_itinerary_input = None
        
        for tool_call in tool_use_calls:
            if tool_call.name == "get_weather":
                loc = tool_call.input.get("location", trip.destination)
                weather_info = get_weather(loc)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": f"Weather lookup results: {weather_info}"
                })
            elif tool_call.name == "generate_itinerary":
                generate_itinerary_input = tool_call.input
                
        if generate_itinerary_input is not None:
            return generate_itinerary_input, messages
            
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
            
    raise ValueError("Claude did not invoke the generate_itinerary tool after 5 turns.")

def validate_itinerary(data: dict, trip: Trip) -> list[str]:
    errors = []
    
    # 1. Pydantic Validation
    try:
        validated = AIItinerarySchema.model_validate(data)
    except ValidationError as e:
        for err in e.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            errors.append(f"Schema validation error at '{loc}': {err['msg']}")
        return errors
        
    # 2. Day Count Check
    if len(validated.days) != trip.days:
        errors.append(f"Day count ({len(validated.days)}) does not match trip duration ({trip.days})")
        
    # 3. Destination Match
    dest = validated.destination
    if trip.destination.lower() not in dest.lower() and dest.lower() not in trip.destination.lower():
        errors.append(f"Destination '{dest}' does not match trip destination '{trip.destination}'")
        
    # 4. Budget Limit Check
    est_total = validated.estimated_total_cost
    limit = trip.budget * 1.10
    if est_total > limit:
        errors.append(f"Estimated total cost {est_total} exceeds budget {trip.budget} by more than 10% (limit is {limit})")
        
    return errors

@itineraryRouter.get("/{trip_id}", response_model=ItineraryResponse)
def getItineraryByTripId(trip_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    itinerary = db.query(Itinerary).filter(Itinerary.trip_id == trip_id).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return itinerary

@itineraryRouter.post("/", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
def createItinerary(payload: ItineraryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trip = db.query(Trip).filter(Trip.id == payload.trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if db.query(Itinerary).filter(Itinerary.trip_id == payload.trip_id).first():
        raise HTTPException(status_code=400, detail="Itinerary already exists for this trip")

    # Manual creation flow (backwards compatibility)
    if payload.days is not None:
        itinerary = Itinerary(
            trip_id=payload.trip_id,
            days=[d.model_dump() for d in payload.days],
            generated_by_ai=False,
            itinerary_json=None
        )
        db.add(itinerary)
        db.commit()
        db.refresh(itinerary)
        return itinerary

    # AI Itinerary Generation Flow with Agentic Feedback Retry
    attempts = 0
    max_attempts = 3
    messages = None
    validation_errors = []
    itinerary_data = None

    while attempts < max_attempts:
        attempts += 1
        try:
            logger.info(f"AI Generation attempt {attempts} for trip_id {trip.id}")
            itinerary_data, messages = call_claude_to_generate(trip, messages)
            validation_errors = validate_itinerary(itinerary_data, trip)
            if not validation_errors:
                break
            else:
                logger.error(f"Validation failed on attempt {attempts}: {validation_errors}")
                # Append validation feedback for the next retry
                feedback_str = (
                    "The generated itinerary failed validation with the following errors:\n"
                    + "\n".join(f"- {err}" for err in validation_errors)
                    + "\nPlease correct these errors and generate the itinerary again using the generate_itinerary tool."
                )
                messages.append({"role": "user", "content": feedback_str})
        except Exception as e:
            logger.error(f"Error on attempt {attempts} during AI generation: {str(e)}")
            validation_errors = [str(e)]
            # If Claude API failed completely or had a network error, reset messages list
            messages = None

    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI itinerary generation failed validation or errored: {'; '.join(validation_errors)}"
        )

    itinerary = Itinerary(
        trip_id=payload.trip_id,
        days=None,
        generated_by_ai=True,
        itinerary_json=itinerary_data
    )
    db.add(itinerary)
    db.commit()
    db.refresh(itinerary)
    return itinerary
