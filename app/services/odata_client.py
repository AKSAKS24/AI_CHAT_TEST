import httpx, asyncio, json, time
from typing import Any, Dict
from loguru import logger
from app.core.config import settings
from app.models.schemas import ODataGetRequest, ODataPostRequest, ODataPreviewResponse, ServiceRegistryOut
from app.utils.url_builder import build_get_url, build_entity_key_segment
from app.utils.security import basic_auth_header
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "registry.json"

class ODataService:
    """Service that builds dynamic OData URLs from a JSON registry and executes HTTP calls."""

    def __init__(self):
        self.base_url = settings.SAP_BASE_URL
        if not self.base_url:
            raise RuntimeError("SAP_BASE_URL is not configured in .env")
        self.session = httpx.AsyncClient(timeout=60.0, verify=True)

    def __del__(self):
        try:
            if not self.session.is_closed:
                asyncio.get_event_loop().run_until_complete(self.session.aclose())
        except Exception:
            pass

    # ---------------- Registry ----------------
    def _load_registry(self) -> Dict[str, Any]:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_registry(self) -> ServiceRegistryOut:
        data = self._load_registry()
        return ServiceRegistryOut(**data)

    # ---------------- Auth ----------------
    def _auth_headers(self) -> Dict[str, str]:
        if settings.SAP_AUTH_MODE == "basic":
            return {"Authorization": basic_auth_header(settings.SAP_USERNAME, settings.SAP_PASSWORD)}
        elif settings.SAP_AUTH_MODE == "oauth2":
            # Placeholder: in real-world, fetch & cache token. Keep minimal here.
            return {"Authorization": f"Bearer {settings.OPENAI_API_KEY or 'YOUR_OAUTH_TOKEN'}"}
        else:
            return {}

    # ---------------- CSRF ----------------
    async def _fetch_csrf(self, url_path: str) -> Dict[str, Any]:
        """Fetch CSRF token and cookies for a given service path (not full URL)."""
        headers = {**self._auth_headers(), "X-CSRF-Token": "Fetch", "Accept": "application/json"}
        # Use a HEAD or GET; many SAP systems require GET
        url = f"{self.base_url.rstrip('/')}/{url_path.lstrip('/')}"
        resp = await self.session.get(url, headers=headers)
        resp.raise_for_status()
        token = resp.headers.get("x-csrf-token") or resp.headers.get("X-CSRF-Token")
        if not token:
            logger.warning("CSRF token missing in response headers; check SAP config.")
        cookies = resp.cookies
        return {"token": token, "cookies": cookies}

    # ---------------- GET ----------------
    async def execute_get(self, req: ODataGetRequest):
        registry = self._load_registry()
        svc = registry["services"].get(req.service)
        if not svc:
            raise ValueError(f"Service '{req.service}' not found in registry")
        entity = svc["entities"].get(req.entity)
        if not entity:
            raise ValueError(f"Entity '{req.entity}' not found in service '{req.service}'")
        url = build_get_url(
            base_url=self.base_url,
            base_path=svc["base_path"],
            entity=req.entity,
            fields=req.fields,
            filters=[f.model_dump() if hasattr(f,'model_dump') else f for f in (req.filters or [])],
            top=req.top, skip=req.skip, orderby=req.orderby
        )
        headers = {**self._auth_headers(), "Accept": "application/json"}
        logger.info(f"GET -> {url}")
        r = await self._request_with_retry("GET", url, headers=headers)
        return r.json()

    # ---------------- POST (create/update) ----------------
    async def preview_post(self, req: ODataPostRequest) -> ODataPreviewResponse:
        svc_path, url, method, payload = await self._compose_post(req)
        headers_preview = {"Accept": "application/json", "Content-Type": "application/json"}
        return ODataPreviewResponse(ok=True, url=url, method=method, headers_preview=headers_preview, payload=payload)

    async def execute_post(self, req: ODataPostRequest):
        svc_path, url, method, payload = await self._compose_post(req)
        # 1) fetch CSRF for svc_path (not full URL)
        csrf = await self._fetch_csrf(svc_path)
        headers = {**self._auth_headers(), "Accept": "application/json", "Content-Type": "application/json"}
        if csrf.get("token"):
            headers["X-CSRF-Token"] = csrf["token"]
        logger.info(f"{method} -> {url} (payload keys: {list(payload.keys())})")
        r = await self._request_with_retry(method, url, headers=headers, json=payload, cookies=csrf.get("cookies"))
        # some SAP gateways return 201 with no JSON body on CREATE; handle both
        try:
            return r.json()
        except ValueError:
            return {"status_code": r.status_code, "text": r.text}

    async def _compose_post(self, req: ODataPostRequest):
        if req.action not in ("create","update"):
            raise ValueError("action must be 'create' or 'update'")
        registry = self._load_registry()
        svc = registry["services"].get(req.service)
        if not svc:
            raise ValueError(f"Service '{req.service}' not found in registry")
        entity = svc["entities"].get(req.entity)
        if not entity:
            raise ValueError(f"Entity '{req.entity}' not found in service '{req.service}'")
        base_path = svc["base_path"]
        if req.action == "create" or not req.key_fields:
            url_path = f"{base_path.rstrip('/')}/{req.entity}"
            method = "POST"
        else:
            key_seg = build_entity_key_segment(req.key_fields)
            url_path = f"{base_path.rstrip('/')}/{req.entity}{key_seg}"
            # Many SAP OData updates are via MERGE or PATCH; POST with X-HTTP-Method can also be used.
            method = "PATCH"
        url = f"{self.base_url.rstrip('/')}/{url_path.lstrip('/')}"
        payload = req.payload
        return base_path, url, method, payload

    # ---------------- retry wrapper ----------------
    async def _request_with_retry(self, method: str, url: str, **kwargs):
        max_attempts = 3
        delay = 0.75
        last_exc = None
        for attempt in range(1, max_attempts+1):
            try:
                r = await self.session.request(method, url, **kwargs)
                if r.status_code >= 500:
                    raise httpx.HTTPStatusError("server error", request=r.request, response=r)
                return r
            except Exception as e:
                last_exc = e
                logger.warning(f"Attempt {attempt}/{max_attempts} failed for {method} {url}: {e}")
                await asyncio.sleep(delay * attempt)
        logger.error(f"All attempts failed for {method} {url}")
        if last_exc:
            raise last_exc
        raise RuntimeError("request failed without exception")
