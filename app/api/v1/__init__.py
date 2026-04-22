from fastapi import APIRouter
from app.api.v1.endpoints.chatbot import router as chatbot_router

api_router = APIRouter()
api_router.include_router(chatbot_router, prefix="/chatbot", tags=["chatbot"])

__all__ = ["api_router"]