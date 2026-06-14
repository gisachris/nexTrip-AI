from pydantic import BaseModel, PositiveInt, Field, ConfigDict

class TripDay(BaseModel):
    day: PositiveInt = Field(..., examples=[1])
    activities: list[str] = Field(..., examples=[["Eiffel Tower", "Seine River Walk"]])

class ItineraryCreate(BaseModel):
    trip_id: PositiveInt
    days: list[TripDay] | None = None

class AIActivity(BaseModel):
    time: str = Field(..., description="Time of the activity (e.g., Morning, Afternoon, Evening)")
    activity: str = Field(..., description="Name of the activity")
    location: str = Field(..., description="Location/attraction name")
    description: str = Field(..., description="Description of the activity")
    estimated_cost: float = Field(..., description="Estimated cost of this specific activity")

class AIDay(BaseModel):
    day_number: int = Field(..., description="Day number of the trip")
    theme: str = Field(..., description="Theme for the day")
    estimated_cost: float = Field(..., description="Estimated total cost for this day")
    activities: list[AIActivity] = Field(..., description="List of activities for this day")

class AIItinerarySchema(BaseModel):
    title: str = Field(..., description="Title of the itinerary")
    destination: str = Field(..., description="Destination city/region")
    travel_style: str = Field(..., description="Style of travel (e.g. Cultural, Budget, Adventure)")
    budget: float = Field(..., description="Total budget for the trip")
    estimated_total_cost: float = Field(..., description="Estimated total cost of the itinerary")
    days: list[AIDay] = Field(..., description="List of days in the itinerary")

class ItineraryResponse(BaseModel):
    id: int
    trip_id: PositiveInt
    generated_by_ai: bool
    days: list[TripDay] | None = None
    itinerary_json: AIItinerarySchema | None = None

    model_config = ConfigDict(from_attributes=True)
