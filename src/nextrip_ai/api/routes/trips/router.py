from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from nextrip_ai.core.dependencies import get_db, get_current_user
from nextrip_ai.models.user import User
from nextrip_ai.models.trip import Trip
from nextrip_ai.api.routes.trips.schema import TripCreate, TripUpdate, TripResponse

trips_router = APIRouter(prefix="/trips", tags=["trips"])

@trips_router.get("/", response_model=list[TripResponse])
def getTrips(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Trip).filter(Trip.user_id == current_user.id).all()

@trips_router.get("/{tripId}", response_model=TripResponse)
def getTripById(tripId: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trip = db.query(Trip).filter(Trip.id == tripId, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@trips_router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def createTrip(payload: TripCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trip = Trip(**payload.model_dump(), user_id=current_user.id)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip

@trips_router.patch("/{tripId}", response_model=TripResponse)
def updateTrip(tripId: int, payload: TripUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trip = db.query(Trip).filter(Trip.id == tripId, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(trip, key, value)
    db.commit()
    db.refresh(trip)
    return trip

@trips_router.delete("/{tripId}", status_code=status.HTTP_204_NO_CONTENT)
def deleteTrip(tripId: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trip = db.query(Trip).filter(Trip.id == tripId, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    db.delete(trip)
    db.commit()
