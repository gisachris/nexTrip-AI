from fastapi import FastAPI
from nextrip_ai.core.database import engine, Base
from nextrip_ai.models import user, trip, itinerary, document_manifest
from nextrip_ai.api.routes.auth.router import authRouter
from nextrip_ai.api.routes.trips.router import trips_router
from nextrip_ai.api.routes.itineraries.router import itineraryRouter

Base.metadata.create_all(bind=engine)

app = FastAPI(title="nexTrip AI", description="AI powered vacation planner API", version="0.1.0")

app.include_router(authRouter, tags=["authentication"])
app.include_router(trips_router)
app.include_router(itineraryRouter)

@app.get("/")
def home():
    return {"message": "welcome to nexTrip AI"}
