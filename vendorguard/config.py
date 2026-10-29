import os
from dotenv import load_dotenv

load_dotenv()

def load_settings():
    return {
        "registry_mode": os.getenv("REGISTRY_MODE", "demo").strip().lower(),
        "external_registry_configured": bool(os.getenv("VENDOR_REGISTRY_URL") and os.getenv("VENDOR_REGISTRY_API_KEY")),
        "ai_enabled": bool(os.getenv("OPENAI_API_KEY")),
        "database_path": os.getenv("DATABASE_PATH", "vendorguard.db"),
    }
