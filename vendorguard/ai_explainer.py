import json
import os

def explain_findings(vendor: dict, checks: list[dict], status: str) -> tuple[str, str]:
    """Optional OpenAI explanation; deterministic rules decide status. Template fallback works offline."""
    findings = [c for c in checks if c["result"] in ("FAIL", "REVIEW", "UNAVAILABLE")]
    if not findings:
        fallback = f"The configured checks passed. Workflow status: {status}. This reflects only the checks listed and is not a guarantee of vendor legitimacy."
    else:
        details = "; ".join(f'{c["check"]}: {c["details"]}' for c in findings)
        fallback = f"Workflow status: {status}. Items requiring attention: {details}. Resolve these items or complete manual review before relying on the onboarding decision."
    follow_up = _draft_follow_up(vendor, findings)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback + " (Template explanation: OPENAI_API_KEY is not configured.)", follow_up
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        prompt = {
            "vendor_name": vendor.get("vendor_name", ""), "workflow_status": status, "findings": findings,
            "instruction": "Explain findings plainly for a procurement reviewer. Do not invent facts, claim the vendor is legitimate, change the supplied status, or claim a verification occurred without evidence."
        }
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.2,
            messages=[
                {"role": "system", "content": "Explain vendor onboarding checks conservatively. Deterministic checks control the decision. Never claim external verification unless the evidence explicitly says it occurred."},
                {"role": "user", "content": json.dumps(prompt)},
            ],
        )
        return (response.choices[0].message.content or fallback), follow_up
    except Exception:
        return fallback + " (AI explanation unavailable; using deterministic template.)", follow_up

def _draft_follow_up(vendor: dict, findings: list[dict]) -> str:
    name = (vendor.get("vendor_name") or "Vendor").strip()
    if not findings:
        return f"Hello {name},\n\nThank you for submitting your vendor registration. The configured checks did not identify outstanding items. Final onboarding remains subject to your organization's approval process.\n\nRegards,\nProcurement Team"
    lines = []
    for finding in findings:
        if finding["result"] == "UNAVAILABLE":
            lines.append(f'- Verification step unavailable: {finding["check"]}. A reviewer or retry is needed.')
        else:
            lines.append(f'- {finding["check"]}: {finding["details"]}')
    return (f"Hello {name},\n\nThank you for submitting your vendor registration. We need additional information or review before onboarding can proceed:\n" + "\n".join(lines) + "\n\nPlease provide the requested clarification through the approved onboarding channel. Do not send full bank credentials by email.\n\nRegards,\nProcurement Team")
