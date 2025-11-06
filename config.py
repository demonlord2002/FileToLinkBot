import os

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BIN_CHANNEL = int(os.getenv("BIN_CHANNEL", "0"))
DATABASE_URL = os.getenv("DATABASE_URL", "")

# FQDN will be added after first deployment
FQDN = os.getenv("FQDN", "")
HAS_SSL = os.getenv("HAS_SSL", "True").lower() == "true"
PORT = int(os.getenv("PORT", "8080"))
NO_PORT = os.getenv("NO_PORT", "True").lower() == "true"
