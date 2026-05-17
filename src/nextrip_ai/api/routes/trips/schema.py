from pydantic import BaseModel, Field, PositiveInt

class TripBase(BaseModel):
    destination: str = Field(..., description="The trip destination", examples=["France", "Paris"])
    days: PositiveInt = Field(..., description="How many days the trip will take", examples=[7])
    budget: PositiveInt = Field(..., description="The trip Budget in USD", examples=["$2500"])
    trip_style: str = Field(..., description="The type of Trip", examples=["adventure", "tourism"])

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    destination: str | None
    days: PositiveInt | None
    budget: PositiveInt | None
    trip_Style: str | None

class TripResponse(TripBase):
    id: PositiveInt
    message: str
