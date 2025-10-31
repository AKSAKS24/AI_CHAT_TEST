from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from app.models.schemas import (
    ODataGetRequest,
    ODataPostRequest,
    ODataPreviewResponse,
    ODataExecResponse,
    ServiceRegistryOut,
)
from app.services.odata_client import ODataService
from app.core.config import settings

router = APIRouter()

def get_service() -> ODataService:
    return ODataService()

@router.get("/registry", response_model=ServiceRegistryOut)
def get_registry(service: ODataService = Depends(get_service)):
    """Return the dynamic service/entity/field registry used to build OData URLs."""
    return service.get_registry()

@router.post("/get", response_model=ODataExecResponse)
async def odata_get(request: ODataGetRequest, service: ODataService = Depends(get_service)):
    """Execute a GET on the target entity with optional filters."""
    logger.info(f"GET flow: service={request.service}, entity={request.entity}, filters={request.filters}")
    try:
        data = await service.execute_get(request)
        return ODataExecResponse(ok=True, step="get", message="GET executed", data=data)
    except Exception as e:
        logger.exception("GET failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/post/preview", response_model=ODataPreviewResponse)
async def odata_post_preview(request: ODataPostRequest, service: ODataService = Depends(get_service)):
    """Return a preview of the POST (create/update) call: resolved URL, payload, headers (sans secrets)."""
    logger.info(f"POST preview: action={request.action} service={request.service} entity={request.entity}")
    try:
        preview = await service.preview_post(request)
        return preview
    except Exception as e:
        logger.exception("POST preview failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/post/confirm", response_model=ODataExecResponse)
async def odata_post_confirm(request: ODataPostRequest, service: ODataService = Depends(get_service)):
    """Execute the POST (create/update) ONLY when confirm=True."""
    if not request.confirm:
        raise HTTPException(status_code=400, detail="confirm must be true to execute POST")
    logger.info(f"POST execute: action={request.action} service={request.service} entity={request.entity}")
    try:
        data = await service.execute_post(request)
        return ODataExecResponse(ok=True, step="post", message="POST executed", data=data)
    except Exception as e:
        logger.exception("POST execution failed")
        raise HTTPException(status_code=500, detail=str(e))
