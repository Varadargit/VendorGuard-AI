from datetime import datetime, timezone
from .validators import validate_email, validate_tax_id_format, normalize_name
from .registry import lookup_demo_registry, lookup_external_registry
from .ai_explainer import explain_findings

def process_vendor(vendor: dict) -> dict:
    checks = []
    def add(name, result, details):
        checks.append({"check": name, "result": result, "details": details})

    required = ["vendor_name", "country", "tax_id", "email", "bank_name"]
    missing = [key for key in required if not str(vendor.get(key, "")).strip()]
    add("Required fields", "FAIL" if missing else "PASS", "Missing: " + ", ".join(missing) if missing else "All required text fields are present.")

    email_ok = validate_email(vendor.get("email", ""))
    add("Email syntax", "PASS" if email_ok else "FAIL", "Email has basic valid syntax; ownership has not been verified." if email_ok else "Email is missing or does not match the basic expected format.")

    tax_ok, tax_message = validate_tax_id_format(vendor.get("country", ""), vendor.get("tax_id", ""))
    add("Tax ID format", "PASS" if tax_ok else "FAIL", tax_message)

    if vendor.get("document_provided"):
        add("Required document supplied", "PASS", f'{vendor.get("document_type", "Required document")} marked as supplied; document authenticity/content has not been verified.')
    else:
        add("Required document supplied", "FAIL", f'Missing required document: {vendor.get("document_type", "required document")}.' )

    from .db import find_duplicate_tax_id
    duplicate = find_duplicate_tax_id(vendor.get("tax_id", ""))
    add("Duplicate submission", "REVIEW" if duplicate else "PASS", f"Tax ID matches prior local run #{duplicate}. Review the existing record before creating another vendor." if duplicate else "No prior local run with this tax ID was found.")

    mode = vendor.get("registry_mode", "demo")
    registry = lookup_external_registry(vendor.get("tax_id", ""), vendor.get("country", "")) if mode == "external" else lookup_demo_registry(vendor.get("tax_id", ""))
    registry_state = registry.get("state", "UNKNOWN")
    record = registry.get("record") or {}
    if registry_state in ("ACTIVE", "APPROVED", "VERIFIED"):
        add("Registry lookup", "PASS", f'{registry["source"]}: {registry["message"]}')
    elif registry_state in ("INACTIVE", "REVOKED", "SUSPENDED"):
        add("Registry lookup", "FAIL", f'{registry["source"]}: record state is {registry_state}. {registry["message"]}')
    elif registry_state == "NOT_FOUND":
        add("Registry lookup", "REVIEW", registry["message"])
    else:
        add("Registry lookup", "UNAVAILABLE", f'{registry["source"]}: {registry["message"]}')

    if record.get("company_name"):
        submitted_name = normalize_name(vendor.get("vendor_name", ""))
        registered_name = normalize_name(record.get("company_name", ""))
        if submitted_name and submitted_name == registered_name:
            add("Company name vs registry", "PASS", "Submitted name matches the registry name after basic normalization.")
        else:
            add("Company name vs registry", "REVIEW", f'Submitted name "{vendor.get("vendor_name")}" differs from registry name "{record.get("company_name")}".')
    else:
        add("Company name vs registry", "UNAVAILABLE", "No registry company name was available to compare.")

    submitted_name = normalize_name(vendor.get("vendor_name", ""))
    bank_name = normalize_name(vendor.get("bank_name", ""))
    if submitted_name and bank_name and submitted_name == bank_name:
        add("Company vs bank account holder", "PASS", "Names match after basic normalization. This does not verify bank account ownership.")
    else:
        add("Company vs bank account holder", "REVIEW", "Names differ after basic normalization; this may have a legitimate explanation. Verify through an approved process.")

    hard_fail_checks = {"Required fields", "Email syntax", "Tax ID format", "Required document supplied"}
    hard_fail = any(c["result"] == "FAIL" and c["check"] in hard_fail_checks for c in checks)
    inactive = any(c["check"] == "Registry lookup" and c["result"] == "FAIL" for c in checks)
    review = any(c["result"] in ("REVIEW", "UNAVAILABLE") for c in checks)
    if inactive:
        status = "Rejected"
        summary = "The configured registry response indicates an inactive/revoked/suspended record. Human review is required before any final action."
    elif hard_fail:
        status = "Pending"
        summary = "Required information or a configured validation failed. The submission needs correction before approval."
    elif review:
        status = "Pending"
        summary = "One or more checks need clarification, manual review, or an unavailable verification source. No unsupported legitimacy claim has been made."
    else:
        status = "Approved"
        summary = "All configured checks passed. This is approval within the demo workflow only, not a guarantee of real-world legitimacy."

    explanation, follow_up = explain_findings(vendor, checks, status)
    passed = sum(c["result"] == "PASS" for c in checks)
    attention = sum(c["result"] in ("FAIL", "REVIEW", "UNAVAILABLE") for c in checks)
    return {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "status": status,
        "summary": summary, "checks": checks, "checks_passed": passed, "checks_attention": attention,
        "registry_source": registry.get("source", "Unknown"), "registry_state": registry_state,
        "explanation": explanation, "follow_up": follow_up,
        "limitations": [
            "Demo registry records are fictional unless a configured external provider is used.",
            "Tax ID format checks do not prove registration status.",
            "Bank account ownership is not verified by name comparison.",
            "Document supplied status does not prove document authenticity.",
        ],
    }
