from typing import Dict, Any, Optional
from loguru import logger
from app.core.config import settings
from app.models.schemas import IntentSchema, IntentGet, IntentCreate, IntentUpdate
from app.data.registry_loader import load_registry_services
from pydantic import BaseModel
import json

# LangChain imports kept local so the app runs even if langchain isn't installed
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    LANGCHAIN_AVAILABLE = True
except Exception as e:
    logger.warning("LangChain not available or failed to import: {}", e)
    LANGCHAIN_AVAILABLE = False

class NLPResult(BaseModel):
    intent_json: Dict[str, Any]
    raw_text: str

def available() -> bool:
    return settings.USE_LANGCHAIN and LANGCHAIN_AVAILABLE

def _build_system_prompt() -> str:
    # Registry services guide the model to valid services/entities/fields
    registry = load_registry_services()
    registry_hint = json.dumps(registry, ensure_ascii=False, indent=2)
    return f"""You are an assistant that converts natural language into a STRICT JSON for SAP OData actions.

You must ONLY return minified JSON with keys from one of the following shapes:
1) Get:
{{
  "intent":"get","service":"<SERVICE>","entity":"<ENTITY>",
  "fields":["Field",...],
  "filters":[{{"field":"Field","op":"eq|ne|gt|lt|ge|le|like|in","value":<str|num|list>}}],
  "top":100,"skip":0,"orderby":"Field asc|desc"
}}

2) Create:
{{
  "intent":"create","service":"<SERVICE>","entity":"<ENTITY>","payload":{{ "Field":"Value", ... }}
}}

3) Update:
{{
  "intent":"update","service":"<SERVICE>","entity":"<ENTITY>","key_fields":{{"Key":"Value"}}, "payload":{{ "Field":"Value", ... }}
}}

ALLOWED services/entities/fields (from service registry):
{registry_hint}

Rules:
- Choose a service and entity ONLY from the above registry.
- Prefer valid field names listed.
- Use ISO dates (YYYY-MM-DD) when dates are implied.
- If user asks to create/update, include only fields likely required by the entity.
- Do NOT include commentary or code blocks. ONLY return pure JSON.
"""

def _build_chain():
    model_name = settings.MODEL_NAME or "gpt-4o-mini"
    llm = ChatOpenAI(model=model_name, temperature=0, api_key=settings.OPENAI_API_KEY)
    prompt = ChatPromptTemplate.from_messages([
        ("system", _build_system_prompt()),
        ("human", "{message}")
    ])
    parser = JsonOutputParser()
    return prompt | llm | parser

def parse_to_intent(user_message: str) -> NLPResult:
    if not available():
        raise RuntimeError("LangChain is disabled or unavailable. Set USE_LANGCHAIN=true and install deps.")
    chain = _build_chain()
    intent_json = chain.invoke({"message": user_message})
    logger.info("NLP intent JSON: {}", intent_json)
    # Validate with our Pydantic union schema
    try:
        # Pydantic won't validate Union directly from dict unless we choose the class; do a simple route
        if intent_json.get("intent") == "get":
            IntentGet(**intent_json)
        elif intent_json.get("intent") == "create":
            IntentCreate(**intent_json)
        elif intent_json.get("intent") == "update":
            IntentUpdate(**intent_json)
        else:
            raise ValueError("intent must be one of: get|create|update")
    except Exception as e:
        logger.error("NLP intent validation failed: {}", e)
        raise
    return NLPResult(intent_json=intent_json, raw_text=user_message)
