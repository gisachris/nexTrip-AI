from pydantic import BaseModel, Field, PositiveInt, ConfigDict

class TripBase(BaseModel):
    destination: str = Field(..., examples=["Paris"])
    days: PositiveInt = Field(..., examples=[5])
    budget: PositiveInt = Field(..., examples=[1500])
    trip_style: str = Field(..., examples=["budget"])

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    destination: str | None = None
    days: PositiveInt | None = None
    budget: PositiveInt | None = None
    trip_style: str | None = None

class TripResponse(TripBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
