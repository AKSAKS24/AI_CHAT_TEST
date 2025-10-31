from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from typing import Dict, Any
from app.models.schemas import ChatRequest, ChatResponse, ODataGetRequest, ODataPostRequest
from app.services.odata_client import ODataService
from app.services.nlp_router import available as nlp_available, parse_to_intent

router = APIRouter()

def get_service() -> ODataService:
    return ODataService()

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, service: ODataService = Depends(get_service)):
    if not nlp_available():
        raise HTTPException(status_code=503, detail="NLP (LangChain) is disabled or unavailable")
    try:
        nlp = parse_to_intent(req.message)
    except Exception as e:
        logger.exception("NLP parsing failed")
        raise HTTPException(status_code=400, detail=f"NLP parsing failed: {e}")

    # Optional restriction to allowed_services
    intent = nlp.intent_json
    if req.allowed_services and intent.get("service") not in set(req.allowed_services):
        raise HTTPException(status_code=403, detail="Service not allowed by policy")

    # Route based on intent
    kind = intent.get("intent")
    if kind == "get":
        get_body = ODataGetRequest(**{
            "service": intent["service"],
            "entity": intent["entity"],
            "fields": intent.get("fields"),
            "filters": intent.get("filters"),
            "top": intent.get("top", 100),
            "skip": intent.get("skip", 0),
            "orderby": intent.get("orderby")
        })
        data = await service.execute_get(get_body)
        return ChatResponse(ok=True, stage="get", intent="get", nlp_json=intent, result=data)

    elif kind in ("create","update"):
        post_body = ODataPostRequest(**{
            "action": "create" if kind == "create" else "update",
            "service": intent["service"],
            "entity": intent["entity"],
            "key_fields": intent.get("key_fields"),
            "payload": intent.get("payload") or {},
            "confirm": bool(intent.get("confirm", False) or req.confirm)
        })

        # Always preview first unless explicitly told not to
        if req.preview_only:
            preview = await service.preview_post(post_body)
            return ChatResponse(ok=True, stage="preview", intent=kind, nlp_json=intent, resolved_endpoint=preview.url, result=preview.model_dump())
        else:
            if not post_body.confirm:
                raise HTTPException(status_code=400, detail="confirm must be true to execute create/update")
            data = await service.execute_post(post_body)
            return ChatResponse(ok=True, stage="executed", intent=kind, nlp_json=intent, result=data)

    else:
        raise HTTPException(status_code=400, detail="Unsupported intent")
