from fastapi import APIRouter
from app.api.v1.endpoints.chatbot import router as chatbot_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.consent import router as consent_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.psychologist import router as psychologist_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.content import router as content_router
from app.api.v1.endpoints.survey import router as survey_router
from app.api.v1.endpoints.sos import router as sos_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(consent_router, prefix="/consent", tags=["consent"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(psychologist_router, prefix="/psychologist", tags=["psychologist"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(chatbot_router, prefix="/chatbot", tags=["chatbot"])
api_router.include_router(content_router, prefix="/content", tags=["content"])
api_router.include_router(survey_router, prefix="/survey", tags=["survey"])
api_router.include_router(sos_router, prefix="/sos", tags=["sos"])

__all__ = ["api_router"]
