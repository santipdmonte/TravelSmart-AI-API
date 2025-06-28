from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from routes.travel_classifier_routes import travel_classifier_router
from routes.document_analyzer_router import document_analyzer_router
from routes.itinerary import itinerary_router
from routes.user_routes import router as auth_router, user_router
from database import engine
from dependencies import get_db
from models.itinerary import Base as ItineraryBase
from models.user import Base as UserBase

import uvicorn

app = FastAPI(
    title="TravelSmart AI API",
    description="AI-powered travel planning and user management API",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
ItineraryBase.metadata.create_all(bind=engine)
UserBase.metadata.create_all(bind=engine)

# Include routes
app.include_router(auth_router)  # Authentication routes (/auth)
app.include_router(user_router)  # User management routes (/users)
app.include_router(itinerary_router)  # Itinerary routes
# app.include_router(travel_classifier_router)
# app.include_router(document_analyzer_router)

@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
