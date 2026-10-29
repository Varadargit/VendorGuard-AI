import re

def validate_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", (value or "").strip()))

def normalize_name(value: str) -> str:
    value = (value or "").lower().strip()
    value = re.sub(r"\b(private limited|pvt ltd|pvt\. ltd\.|limited|ltd|llp|incorporated|inc)\b", " ", value)
    return re.sub(r"[^a-z0-9]", "", value)

def validate_tax_id_format(country: str, tax_id: str) -> tuple[bool, str]:
    tax_id = (tax_id or "").strip().upper()
    if not tax_id:
        return False, "Tax registration ID is missing."
    if country == "India":
        # Structural GSTIN check only. It does not establish that the ID is registered or active.
        pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"
        if not re.fullmatch(pattern, tax_id):
            return False, "The value does not match the expected 15-character GSTIN structure."
        return True, "GSTIN structure looks valid; registration status has not been proven by this format check."
    if country == "United States":
        if len(tax_id) < 5 or len(tax_id) > 20:
            return False, "Tax ID length is outside the configured demo range."
        return True, "Basic length check passed; US tax IDs vary by identifier type and this is not authoritative validation."
    if country == "United Kingdom":
        if not re.fullmatch(r"[A-Z0-9]{8,15}", tax_id):
            return False, "Tax ID must be 8–15 alphanumeric characters under this demo rule."
        return True, "Basic format check passed; this does not verify registration."
    if len(tax_id) < 4:
        return False, "Tax ID is too short under the configured generic rule."
    return True, "Generic non-empty tax ID check passed; country-specific validation is not configured."
