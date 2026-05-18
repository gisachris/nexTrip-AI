from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.openapi.utils import get_openapi
from nextrip_ai.core.database import engine, Base
from nextrip_ai.models import user, trip, itinerary
from nextrip_ai.api.routes.auth.router import authRouter
from nextrip_ai.api.routes.trips.router import trips_router
from nextrip_ai.api.routes.itineraries.router import itineraryRouter

Base.metadata.create_all(bind=engine)

app = FastAPI(title="nexTrip AI", description="AI powered vacation planner API", version="0.1.0")

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
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>nexTrip AI</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
                font-family: 'Segoe UI', sans-serif;
                color: white;
            }
            .container {
                text-align: center;
                padding: 60px 40px;
                background: rgba(255,255,255,0.05);
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                max-width: 600px;
                width: 90%;
            }
            .logo { font-size: 48px; margin-bottom: 10px; }
            h1 { font-size: 42px; font-weight: 700; letter-spacing: -1px; }
            h1 span { color: #38bdf8; }
            p {
                margin-top: 16px;
                font-size: 16px;
                color: rgba(255,255,255,0.6);
                line-height: 1.6;
            }
            .badge {
                display: inline-block;
                margin-top: 30px;
                padding: 10px 24px;
                background: #38bdf8;
                color: #0f2027;
                border-radius: 999px;
                font-weight: 600;
                font-size: 14px;
                text-decoration: none;
            }
            .badge:hover { background: #7dd3fc; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">✈️</div>
            <h1>nex<span>Trip</span> AI</h1>
            <p>Your AI-powered vacation planner. Discover destinations, generate itineraries, and plan your perfect trip.</p>
            <a class="badge" href="/docs">Explore the API →</a>
        </div>
    </body>
    </html>
    """
