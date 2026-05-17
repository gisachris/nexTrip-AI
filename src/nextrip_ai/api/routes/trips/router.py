from fastapi import APIRouter

trips_router = APIRouter(
    prefix= "/trips",
    tags= ["trips", "voyages"]
)


@trips_router.get("/")
def getTrips():
    pass

@trips_router.get("/{tripId}")
def getTripById(tripId: int):
    pass

@trips_router.post("/")
def createTrip():
    pass

@trips_router.patch("/{tripId}")
def updateTrip(tripId: int):
    pass

@trips_router.delete("/{tripId")
def deleteTrip(tripId: int):
    pass