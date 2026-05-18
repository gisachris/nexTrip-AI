<p align="center">
  <img src="src/nextrip_ai/static/images/logo.png" alt="nexTrip AI Logo" width="200"/>
</p>

<p align="center">
  <em>nexTrip AI is an AI powered vacation planner. From finding the most attractive and cost efficient locations around the globe to booking and itinerary planning. Planning your next Trip has never been easier.</em>
</p>

---

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- 🌍 **Destination Suggestions** — Discover the most attractive and cost-efficient travel destinations around the globe tailored to your preferences
- 🗓️ **Itinerary Generation** — Automatically generate detailed, day-by-day travel plans based on your destination, budget, and travel style
- 📡 **Real-time Information** — Fetch up-to-date data on maps, weather forecasts, and pricing to keep your plans accurate
- 🧠 **Conversation Context** — Remembers your preferences and past interactions to deliver a seamless, personalized planning experience
- 📚 **Knowledge Retrieval (RAG)** — Leverages a retrieval-augmented generation system to provide rich, accurate travel knowledge
- 🔧 **Tool Integration** — Connects to external APIs, search engines, and mapping services to power intelligent recommendations
- 🎙️ **Multimodal Input** — Interact via text, voice, or images for a natural and flexible user experience
- 🔒 **Secure & Production-ready** — Built with security, evaluation, and scalability in mind from the ground up

---

## Getting Started

### Prerequisites

- [Python](https://www.python.org/downloads/) >= 3.14
- [Poetry](https://python-poetry.org/docs/#installation) >= 2.0.0

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/gisachris/nexTrip-ai.git
   cd nexTrip-ai
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Start the application:
   ```bash
   poetry run start
   ```

The API will be available at `http://localhost:8000`.

---

## Usage

Once the application is running at `http://localhost:8000`, you can interact with the following API endpoints:

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login and receive a JWT token |
| `GET` | `/users/me` | Get the currently authenticated user |

**Register payload:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Login payload:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### Trips

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/trips` | Get all trips |
| `GET` | `/trips/{tripId}` | Get a trip by ID |
| `POST` | `/trips` | Create a new trip |
| `PATCH` | `/trips/{tripId}` | Update a trip |
| `DELETE` | `/trips/{tripId}` | Delete a trip |

**Create/Update trip payload:**
```json
{
  "destination": "Paris",
  "days": 7,
  "budget": 2500,
  "trip_style": "adventure"
}
```

### Itineraries

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/itineraries/{itineraryId}` | Get an itinerary by ID |
| `POST` | `/itineraries` | Generate a new itinerary |

**Itinerary response:**
```json
{
  "trip_id": 1,
  "days": [
    { "day": 1, "activities": ["Eiffel Tower", "Seine River Walk"] }
  ]
}
```

---

## Configuration

Create a `.env` file in the project root with the following variables:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nextrip_ai_db
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Secret key used to sign JWT tokens — use a long random string in production |
| `ALGORITHM` | JWT signing algorithm — `HS256` by default |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | How long a JWT token remains valid in minutes |

---

## Architecture

The project follows a clean layered structure:

```
src/nextrip_ai/
├── api/
│   └── routes/
│       ├── auth/         # Register, login, user profile
│       ├── trips/        # Trip CRUD
│       └── itineraries/  # Itinerary creation and retrieval
├── core/
│   ├── config.py         # Environment-based settings
│   ├── database.py       # SQLAlchemy engine and session
│   ├── security.py       # Password hashing and JWT
│   └── dependencies.py   # Reusable FastAPI dependencies
├── models/
│   ├── user.py           # User database model
│   ├── trip.py           # Trip database model
│   └── itinerary.py      # Itinerary database model
├── main.py               # App entry point, router registration
└── run.py                # Uvicorn server launcher
```

**Key design decisions:**
- Each route group owns its schemas alongside its router
- `core/` is shared infrastructure with no business logic
- JWT authentication is handled via `HTTPBearer` — token is passed in the `Authorization: Bearer <token>` header
- Itinerary days and activities are stored as JSON in PostgreSQL
- All trip and itinerary routes are scoped to the authenticated user — users can only access their own data
- API is fully documented via Swagger at `/docs`

---

## Contributing

This project is developed and maintained solely by [gisachris](https://github.com/gisachris).

For inquiries, suggestions, or collaboration requests, reach out at gisachrismunyangaju@gmail.com.

---

## License

Copyright © 2026 gisachris. All Rights Reserved.

This project and its source code are proprietary. No part of this codebase may be copied, modified, distributed, or used in any form without explicit written permission from the owner.
