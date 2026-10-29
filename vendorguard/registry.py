import json
import os
import urllib.request
import urllib.error
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "demo_registry.json"

def lookup_demo_registry(tax_id: str) -> dict:
    try:
        records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        records = []
    key = (tax_id or "").strip().upper()
    match = next((r for r in records if r.get("tax_id", "").upper() == key), None)
    if not match:
        return {"source": "Fictional demo registry", "state": "NOT_FOUND", "message": "Tax ID was not found in the fictional demo registry. This is not evidence that the real company does not exist.", "record": None}
    return {"source": "Fictional demo registry", "state": match.get("status", "UNKNOWN"), "message": "Matched a fictional test record. This is not real-world verification.", "record": match}

def lookup_external_registry(tax_id: str, country: str) -> dict:
    """Generic adapter for a verification service you are authorized to use.

    Expected POST JSON request: {"tax_id": "...", "country": "..."}
    Expected response JSON: {"status": "ACTIVE|INACTIVE|NOT_FOUND|...", "company_name": "...", "message": "..."}
    This is not wired to any government registry by default.
    """
    url = os.getenv("VENDOR_REGISTRY_URL")
    api_key = os.getenv("VENDOR_REGISTRY_API_KEY")
    if not url or not api_key:
        return {"source": "External registry", "state": "UNAVAILABLE", "message": "External registry URL/API credentials are not configured.", "record": None}
    payload = json.dumps({"tax_id": tax_id, "country": country}).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST", headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))
        return {"source": "Configured external registry", "state": str(body.get("status", "UNKNOWN")).upper(), "message": body.get("message", "External registry response received."), "record": body}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        return {"source": "Configured external registry", "state": "UNAVAILABLE", "message": f"External registry request failed: {type(exc).__name__}.", "record": None}
