# VendorGuard AI — Vendor Onboarding Review Assistant

A runnable case-study project that accepts a structured vendor submission, runs deterministic checks, looks up a local fictional demo registry (or calls a configured authorized registry adapter), prepares an explanation and follow-up draft, and stores the result in SQLite.

## Features

- Streamlit submission form, live run status, result view, and run-history dashboard
- Required-field and basic email syntax checks
- Country-specific tax-ID **format-only** checks (GSTIN structure for India; not authoritative verification)
- Duplicate detection against this app's prior submissions
- Company-name comparison against a returned registry record
- Company name vs. bank account-holder name comparison (not proof of account ownership)
- Required document supplied/not supplied flag (does not inspect document authenticity)
- Approved / Pending / Rejected workflow outcomes
- Optional AI-generated explanations using OpenAI; deterministic template fallback works without a key
- Editable follow-up draft (no email is sent automatically)
- JSON result download, SQLite audit history, and pytest tests

## Run locally (Windows PowerShell)

1. Install Python 3.10 or newer.
2. Extract this ZIP and open PowerShell in the `VendorGuardAI` folder.
3. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

5. Optional: copy `.env.example` to `.env` and add an OpenAI API key if you want LLM-generated explanations. The app works without it.

6. Start the app:

   ```powershell
   streamlit run app.py
   ```

7. Open the local URL Streamlit prints in the terminal.

## Demo test data

Use fictional records from `data/demo_registry.json`. The included records are invented for the demo and **must not be treated as real GST registrations**.

Happy-path example:

- Company name: `Northstar Supplies Ltd`
- Country: `India`
- Tax ID: `29AAAAA0000A1Z5`
- Email: `accounts@northstar.example`
- Bank account holder name: `Northstar Supplies Ltd`
- Document supplied: `Yes`
- Registry source: `Demo registry (fictional)`

Expected outcome: **Approved within the demo workflow**, because the test record is active and the configured checks pass. This does not verify a real vendor.

Edge cases to demonstrate:

1. **Missing document:** change Document supplied to `No` → Pending, with a follow-up draft.
2. **Registry name mismatch:** submit the test tax ID above but use a different company name → Pending/manual review.
3. **Duplicate submission:** run the same tax ID twice → the second run flags the previous local run and becomes Pending.
4. **Inactive demo record:** use `29CCCCC2222C1Z7` with company name `Apex Trading Ltd` → registry indicates inactive; the workflow marks it Rejected and clearly shows the evidence is fictional.

## Tests

```powershell
pytest -q
```

## Optional external registry adapter

The app contains a generic HTTP adapter, not a preconfigured government integration. Only configure it if you have access and permission to use a real verification provider.

Set these in `.env`:

```env
VENDOR_REGISTRY_URL=https://your-authorized-provider.example/api/lookup
VENDOR_REGISTRY_API_KEY=your_api_key
```

The app sends a `POST` request with JSON `{"tax_id":"...", "country":"..."}` and expects a JSON response similar to:

```json
{"status":"ACTIVE","company_name":"Example Registered Ltd","message":"Registration returned by provider"}
```

Adapt the request/response mapping to the provider's official documentation before use. The generic adapter does not itself connect to GSTN, a bank, or a sanctions database. A service timeout or unconfigured provider is reported as `UNAVAILABLE`, not as a successful verification.

## AI explanation

If `OPENAI_API_KEY` is set in `.env`, the app uses the configured `OPENAI_MODEL` (default `gpt-4o-mini`) to explain findings. The status is always decided by Python rules, not by the model. Avoid sending real sensitive vendor data to an AI API without appropriate authorization and privacy review.

## Limitations and safe claims

This is a case-study prototype, **not a production KYC/KYB system**. The included registry is fictional. GSTIN format checks do not establish registration status. Name comparison does not prove bank-account ownership. A checkbox does not verify document authenticity. Live tax/company verification, bank verification, sanctions/PEP screening, beneficial ownership and legal legitimacy checks are not implemented by default. Production deployment requires authorized data providers, security/privacy controls, provider-specific integration, and compliance review. Use fictional data for the case study.
