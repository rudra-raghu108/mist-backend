"""
Main API router for SRM Guide Bot
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, ai_training

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(ai_training.router, prefix="/ai-training", tags=["AI Training"])
