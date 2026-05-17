from pydantic import BaseModel, PositiveInt, Field

class TripDay(BaseModel):
    day: PositiveInt = Field(..., description="The sequential day number", examples=[1])
    activities: list[str] = Field(
        ..., 
        description="List of activity names planned for this day",
        examples=[["Eiffel Tower", "Seine River Walk"]]
    )

class TripItineraryResponse(BaseModel):
    trip_id: PositiveInt = Field(..., description="Unique database ID of the trip", examples=[1])
    days: list[TripDay] = Field(..., description="Chronological list of daily itineraries")
