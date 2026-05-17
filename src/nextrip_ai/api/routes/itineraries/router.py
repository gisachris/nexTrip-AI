from fastapi import APIRouter

itineraryRouter = APIRouter(
    prefix="/itineraries",
    tags=["itineraries"]
)

@itineraryRouter.get("/{itineraryId}")
def getItineraryById(itineraryId: int):
    pass

@itineraryRouter.post("/")
def createItinerary():
    pass