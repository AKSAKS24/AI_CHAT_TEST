# === SAP / OData connection ===
SAP_BASE_URL=https://your.sap.server:443/sap/opu/odata
SAP_AUTH_MODE=basic                 # options: basic, oauth2
SAP_USERNAME=YOUR_SAP_USERNAME
SAP_PASSWORD=YOUR_SAP_PASSWORD

# --- OAuth2 (only if SAP_AUTH_MODE=oauth2) ---
SAP_OAUTH_TOKEN_URL=https://your.sap.server:443/oauth/token
SAP_OAUTH_CLIENT_ID=XXXX
SAP_OAUTH_CLIENT_SECRET=YYYY
SAP_OAUTH_SCOPE=openid

# === App settings ===
APP_NAME=OData AI Backend
APP_ENV=dev                         # dev | prod
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR, CRITICAL
CORS_ORIGINS=["*"]

# === LangChain ===
USE_LANGCHAIN=false                 # true to enable NLP intent routing
OPENAI_API_KEY=
MODEL_NAME=gpt-4o-mini
