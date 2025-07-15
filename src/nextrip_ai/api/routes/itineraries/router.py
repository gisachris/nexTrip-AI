from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from nextrip_ai.core.dependencies import get_db, get_current_user
from nextrip_ai.models.user import User
from nextrip_ai.models.trip import Trip
from nextrip_ai.models.itinerary import Itinerary
from nextrip_ai.api.routes.itineraries.schema import ItineraryCreate, ItineraryResponse

itineraryRouter = APIRouter(prefix="/itineraries", tags=["itineraries"])

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
    itinerary = Itinerary(trip_id=payload.trip_id, days=[d.model_dump() for d in payload.days])
    db.add(itinerary)
    db.commit()
    db.refresh(itinerary)
    return itinerary
