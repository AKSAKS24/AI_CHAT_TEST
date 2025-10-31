from fastapi import APIRouter
from app.api.odata import router as odata_router

api_router = APIRouter()
api_router.include_router(odata_router, prefix="/odata", tags=["odata"])

# Conditionally include /api/chat when NLP is available
from app.core.config import settings
try:
    from app.api.chat import router as chat_router  # noqa
    from app.services.nlp_router import available as _nlp_available
    if _nlp_available():
        api_router.include_router(chat_router, tags=["chat"])
except Exception:
    # If LangChain isn't installed, we simply skip mounting chat routes
    pass
