from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
import logging
from anthropic import Anthropic

from nextrip_ai.core.config import settings
from nextrip_ai.core.dependencies import get_db, get_current_user
from nextrip_ai.models.user import User
from nextrip_ai.models.trip import Trip
from nextrip_ai.models.itinerary import Itinerary
from nextrip_ai.api.routes.itineraries.schema import ItineraryCreate, ItineraryResponse

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

def call_claude_to_generate(trip: Trip) -> dict:
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    system_prompt = (
        "You are an expert travel planner.\n\n"
        "Your task is to create realistic travel itineraries based on trip information provided by the user.\n\n"
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
        "10. Return ONLY valid JSON via the tool call.\n"
        "11. Do not include markdown.\n"
        "12. Do not include explanations.\n"
        "13. Do not include code blocks.\n"
        "14. The response must match the required schema exactly."
    )

    user_prompt = (
        f"Generate a travel itinerary using the following trip details.\n\n"
        f"Trip Details:\n"
        f"Destination: {trip.destination}\n"
        f"Number of Days: {trip.days}\n"
        f"Budget: {trip.budget}\n"
        f"Travel Style: {trip.trip_style}\n\n"
        f"Requirements:\n"
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
        f"* Use the generate_itinerary tool to return the result."
    )

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=4000,
        temperature=0.3,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        tools=[tool_schema],
        tool_choice={"type": "tool", "name": "generate_itinerary"}
    )
    
    tool_use = next((c for c in response.content if c.type == "tool_use"), None)
    if not tool_use:
        raise ValueError("Claude did not invoke the generate_itinerary tool.")
    
    return tool_use.input

def validate_itinerary(data: dict, trip: Trip) -> list[str]:
    errors = []
    
    required_top_level = ["title", "destination", "travel_style", "budget", "estimated_total_cost", "days"]
    for field in required_top_level:
        if field not in data:
            errors.append(f"Missing top-level required field: {field}")
            
    if "estimated_total_cost" in data:
        try:
            val = float(data["estimated_total_cost"])
        except (ValueError, TypeError):
            errors.append("estimated_total_cost must be a number")
            
    days = data.get("days", [])
    if not isinstance(days, list) or len(days) == 0:
        errors.append("days array is empty or not a list")
    else:
        if len(days) != trip.days:
            errors.append(f"Day count ({len(days)}) does not match trip duration ({trip.days})")
            
        for i, day in enumerate(days):
            day_num = day.get("day_number")
            if day_num is None:
                errors.append(f"Day at index {i} is missing day_number")
            if "theme" not in day:
                errors.append(f"Day at index {i} is missing theme")
            if "estimated_cost" not in day:
                errors.append(f"Day at index {i} is missing estimated_cost")
            
            activities = day.get("activities", [])
            if not isinstance(activities, list):
                errors.append(f"Day at index {i} activities is not a list")
            else:
                for j, act in enumerate(activities):
                    for act_field in ["time", "activity", "location", "description", "estimated_cost"]:
                        if act_field not in act:
                            errors.append(f"Activity {j} on Day {day_num} is missing: {act_field}")
                            
    dest = data.get("destination", "")
    if trip.destination.lower() not in dest.lower() and dest.lower() not in trip.destination.lower():
        errors.append(f"Destination '{dest}' does not match trip destination '{trip.destination}'")
        
    est_total = data.get("estimated_total_cost", 0)
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

    # AI Itinerary Generation Flow
    attempts = 0
    itinerary_data = None
    validation_errors = []

    while attempts < 2:
        attempts += 1
        try:
            logger.info(f"AI Generation attempt {attempts} for trip_id {trip.id}")
            itinerary_data = call_claude_to_generate(trip)
            validation_errors = validate_itinerary(itinerary_data, trip)
            if not validation_errors:
                break
            else:
                logger.error(f"Validation failed on attempt {attempts}: {validation_errors}")
        except Exception as e:
            logger.error(f"Error on attempt {attempts} during AI generation: {str(e)}")
            validation_errors = [str(e)]

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
