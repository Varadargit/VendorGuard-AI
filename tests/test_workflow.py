from vendorguard.workflow import process_vendor
from vendorguard.db import init_db, save_run

def base_vendor():
    return {
        "vendor_name": "Northstar Supplies Ltd", "country": "India", "tax_id": "29AAAAA0000A1Z5",
        "email": "accounts@northstar.example", "bank_name": "Northstar Supplies Ltd",
        "document_type": "GST registration certificate", "document_provided": True,
        "registry_mode": "demo", "vendor_ref": "TEST-001", "notes": "",
    }

def test_complete_demo_record_passes_configured_checks(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    init_db()
    result = process_vendor(base_vendor())
    assert result["status"] == "Approved"
    assert result["registry_state"] == "ACTIVE"

def test_missing_document_is_pending(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    init_db()
    vendor = base_vendor()
    vendor["document_provided"] = False
    result = process_vendor(vendor)
    assert result["status"] == "Pending"
    assert any(c["check"] == "Required document supplied" and c["result"] == "FAIL" for c in result["checks"])

def test_name_mismatch_is_pending(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    init_db()
    vendor = base_vendor()
    vendor["vendor_name"] = "Different Company Ltd"
    result = process_vendor(vendor)
    assert result["status"] == "Pending"
    assert any(c["check"] == "Company name vs registry" and c["result"] == "REVIEW" for c in result["checks"])
