import json
import pandas as pd
import streamlit as st

from vendorguard.db import init_db, save_run, list_runs, get_run
from vendorguard.workflow import process_vendor
from vendorguard.config import load_settings

st.set_page_config(page_title="VendorGuard AI", page_icon="🛡️", layout="wide")
init_db()
settings = load_settings()

st.title("🛡️ VendorGuard AI")
st.caption("Vendor onboarding review assistant · evidence-led checks · human review for uncertainty")

with st.sidebar:
    st.header("System status")
    st.write(f"Registry mode: **{settings['registry_mode']}**")
    st.write(f"AI explanations: **{'Enabled' if settings['ai_enabled'] else 'Template fallback'}**")
    st.write(f"External registry credentials: **{'Configured' if settings['external_registry_configured'] else 'Not configured'}**")
    st.warning("A format check is not proof of company legitimacy or bank-account ownership.")
    page = st.radio("Navigate", ["New submission", "Run history", "About & limitations"])

if page == "New submission":
    st.subheader("Submit a vendor for review")
    st.write("Use fictional data for the demo. Do not enter real bank account details or sensitive personal data.")
    with st.form("vendor_form"):
        col1, col2 = st.columns(2)
        with col1:
            vendor_name = st.text_input("Legal company name *", placeholder="Northstar Supplies Ltd")
            country = st.selectbox("Country *", ["India", "United States", "United Kingdom", "Other"])
            tax_id = st.text_input("Tax registration ID *", placeholder="Use a fictional test ID from README for the demo")
            email = st.text_input("Business email *", placeholder="accounts@example.test")
            vendor_ref = st.text_input("Vendor reference (optional)", placeholder="VEND-001")
        with col2:
            bank_name = st.text_input("Bank account holder name *", placeholder="Northstar Supplies Ltd")
            document_type = st.selectbox("Required tax/compliance document", ["GST registration certificate", "Tax registration certificate", "Business registration document"])
            document_provided = st.selectbox("Document supplied?", ["Yes", "No"])
            registry_mode = st.selectbox("Registry source", ["Demo registry (fictional)", "Configured external registry"])
            notes = st.text_area("Reviewer notes (optional)", placeholder="Context supplied by the vendor")
        submitted = st.form_submit_button("Run onboarding checks", type="primary", use_container_width=True)

    if submitted:
        vendor = {
            "vendor_name": vendor_name.strip(), "country": country, "tax_id": tax_id.strip().upper(),
            "email": email.strip(), "bank_name": bank_name.strip(), "document_type": document_type,
            "document_provided": document_provided == "Yes", "vendor_ref": vendor_ref.strip(),
            "notes": notes.strip(), "registry_mode": "external" if registry_mode.startswith("Configured") else "demo",
        }
        with st.status("Running onboarding checks...", expanded=True) as status_box:
            result = process_vendor(vendor)
            st.write("✓ Required-field and format validation")
            st.write("✓ Duplicate detection")
            st.write("✓ Registry lookup")
            st.write("✓ Cross-field consistency checks")
            st.write("✓ Decision rules and explanation")
            run_id = save_run(vendor, result)
            st.write("✓ Audit record saved")
            status_box.update(label="Workflow completed", state="complete", expanded=False)
        st.session_state["latest_run_id"] = run_id
        st.session_state["latest_result"] = result
        st.session_state["latest_vendor"] = vendor

    if "latest_result" in st.session_state:
        result = st.session_state["latest_result"]
        st.divider()
        st.subheader("Latest decision")
        icon = {"Approved": "🟢", "Pending": "🟠", "Rejected": "🔴"}.get(result["status"], "⚪")
        st.markdown(f"## {icon} {result['status']}")
        st.write(result["summary"])
        c1, c2, c3 = st.columns(3)
        c1.metric("Checks passed", result["checks_passed"])
        c2.metric("Items needing attention", result["checks_attention"])
        c3.metric("Registry source", result["registry_source"])
        st.subheader("Check-by-check evidence")
        st.dataframe(pd.DataFrame(result["checks"]), use_container_width=True, hide_index=True)
        st.subheader("Explanation")
        st.write(result["explanation"])
        st.subheader("Follow-up draft (not sent automatically)")
        st.text_area("Review and edit before using", value=result["follow_up"], height=180, key=f"followup_{st.session_state['latest_run_id']}")
        st.caption(f"Run ID: {st.session_state['latest_run_id']} · {result['created_at']}")
        st.download_button("Download result JSON", json.dumps(result, indent=2), file_name=f"vendorguard_run_{st.session_state['latest_run_id']}.json", mime="application/json")

elif page == "Run history":
    st.subheader("Onboarding history")
    runs = list_runs(limit=200)
    if not runs:
        st.info("No runs yet. Submit a vendor from the New submission page.")
    else:
        st.dataframe(pd.DataFrame(runs), use_container_width=True, hide_index=True)
        selected = st.selectbox("Inspect a run", options=[r["id"] for r in runs], format_func=lambda x: f"Run {x} · {next((r['vendor_name'] for r in runs if r['id'] == x), '')}")
        record = get_run(selected)
        if record:
            st.markdown(f"### {record['result']['status']} — {record['vendor']['vendor_name']}")
            st.json(record["result"])

else:
    st.subheader("How VendorGuard AI works")
    st.markdown("""
- **Input validation:** required fields, email syntax and country-specific tax-ID format checks.
- **Duplicate detection:** compares the tax ID against prior submissions in this app's SQLite history.
- **Registry lookup:** fictional local registry by default; optional generic HTTP adapter for an authorized service.
- **Cross-field checks:** compares the submitted company name with registry data and bank-account-holder name.
- **Decision rules:** combines evidence into Approved, Pending or Rejected. AI does not decide the status.
- **AI explanation:** optional LLM-generated explanation; template fallback works without an API key.
- **Audit history:** stores each run and its evidence in SQLite.
""")
    st.warning("This is a case-study prototype, not a production KYC/KYB system. The included registry is fictional and does not verify real businesses. Tax-ID format checks do not prove registration. Name comparison does not verify bank ownership. Document checkboxes do not prove authenticity. Live GST verification, bank verification, sanctions screening, beneficial ownership and document authenticity checks are not implemented by default. Use only fictional test data.")
    st.markdown("See `README.md` for setup, tests, and external integration notes.")
