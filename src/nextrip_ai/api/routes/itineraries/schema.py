from pydantic import BaseModel, PositiveInt, Field, ConfigDict

class TripDay(BaseModel):
    day: PositiveInt = Field(..., examples=[1])
    activities: list[str] = Field(..., examples=[["Eiffel Tower", "Seine River Walk"]])

class ItineraryCreate(BaseModel):
    trip_id: PositiveInt
    days: list[TripDay]

class ItineraryResponse(BaseModel):
    trip_id: PositiveInt
    days: list[TripDay]

    model_config = ConfigDict(from_attributes=True)
