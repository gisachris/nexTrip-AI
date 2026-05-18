from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from pathlib import Path
from nextrip_ai.core.database import engine, Base
from nextrip_ai.models import user, trip, itinerary
from nextrip_ai.api.routes.auth.router import authRouter
from nextrip_ai.api.routes.trips.router import trips_router
from nextrip_ai.api.routes.itineraries.router import itineraryRouter

Base.metadata.create_all(bind=engine)

app = FastAPI(title="nexTrip AI", description="AI powered vacation planner API", version="0.1.0")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(authRouter, tags=["authentication"])
app.include_router(trips_router)
app.include_router(itineraryRouter)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    for path in schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi
@app.get("/", response_class=FileResponse)
def home():
    return str(STATIC_DIR / "index.html")
