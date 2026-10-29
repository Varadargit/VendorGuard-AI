from vendorguard.validators import validate_email, validate_tax_id_format, normalize_name

def test_email_validation():
    assert validate_email("user@example.com")
    assert not validate_email("not-an-email")

def test_india_gstin_structure_only():
    ok, _ = validate_tax_id_format("India", "29AAAAA0000A1Z5")
    assert ok
    ok, _ = validate_tax_id_format("India", "BAD-ID")
    assert not ok

def test_name_normalization():
    assert normalize_name("Northstar Supplies Ltd") == normalize_name("Northstar Supplies Limited")
