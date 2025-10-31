from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Literal

class FilterItem(BaseModel):
    field: str
    op: Literal["eq","ne","gt","lt","ge","le","like","in"] = "eq"
    value: Any

class ODataGetRequest(BaseModel):
    service: str
    entity: str
    fields: Optional[List[str]] = None
    filters: Optional[List[FilterItem]] = None
    top: Optional[int] = Field(default=100, ge=1, le=1000)
    skip: Optional[int] = Field(default=0, ge=0)
    orderby: Optional[str] = None

class ODataPostRequest(BaseModel):
    action: Literal["create","update"] = "create"
    service: str
    entity: str
    key_fields: Optional[Dict[str, Any]] = None       # required for update
    payload: Dict[str, Any]
    confirm: bool = False

class ODataPreviewResponse(BaseModel):
    ok: bool = True
    step: str = "preview"
    url: str
    method: str
    headers_preview: Dict[str, Any]
    payload: Dict[str, Any]

class ODataExecResponse(BaseModel):
    ok: bool
    step: str
    message: str
    data: Any

class ServiceEntity(BaseModel):
    name: str
    path: str
    key_fields: List[str] = []
    fields: List[str] = []

class ServiceDef(BaseModel):
    name: str
    base_path: str
    entities: Dict[str, ServiceEntity]

class ServiceRegistryOut(BaseModel):
    services: Dict[str, ServiceDef]

# --- APPEND: Chat & NLP intent schema ---
from typing import Literal, Union

class IntentGet(BaseModel):
    intent: Literal["get"]
    service: str
    entity: str
    fields: Optional[List[str]] = None
    filters: Optional[List[FilterItem]] = None
    top: Optional[int] = Field(default=100, ge=1, le=1000)
    skip: Optional[int] = Field(default=0, ge=0)
    orderby: Optional[str] = None

class IntentCreate(BaseModel):
    intent: Literal["create"]
    service: str
    entity: str
    payload: Dict[str, Any]

class IntentUpdate(BaseModel):
    intent: Literal["update"]
    service: str
    entity: str
    key_fields: Dict[str, Any]
    payload: Dict[str, Any]

IntentSchema = Union[IntentGet, IntentCreate, IntentUpdate]

class ChatRequest(BaseModel):
    message: str
    # If you want to constrain which service the user can hit via chat
    allowed_services: Optional[List[str]] = None
    preview_only: bool = True   # for create/update: preview first unless explicitly false
    confirm: bool = False       # honor only when preview_only is False

class ChatResponse(BaseModel):
    ok: bool
    stage: Literal["nlp","preview","executed","get"]
    intent: Optional[str] = None
    nlp_json: Optional[Dict[str, Any]] = None
    resolved_endpoint: Optional[str] = None
    result: Any = None
