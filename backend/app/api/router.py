from fastapi import APIRouter

from app.api.conversations import router as conversations_router
from app.api.messages import router as messages_router
from app.api.files import router as files_router

api_router = APIRouter(prefix="/api")
api_router.include_router(conversations_router)
api_router.include_router(messages_router)
api_router.include_router(files_router)
