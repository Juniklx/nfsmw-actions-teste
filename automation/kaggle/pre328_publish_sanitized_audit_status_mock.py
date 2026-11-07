#!/usr/bin/env python3
"""PRE328 offline allowlist regression: no credentials, raw hit details or paths leaked."""
from pre328_publish_sanitized_audit_status import sanitized_report

source = {
    "status": "AUDIT_OK", "pal_shards_scanned": 131,
    "matches_truncated": False, "owner_verified": False,
    "bounded_matches": [{"file": "secret-file-name", "text": "secret-test-string"}],
    "error_type": "DO_NOT_PUBLISH", "refresh_token": "DO_NOT_PUBLISH",
}
result = sanitized_report("PRE325", source, "123456", "abc123")
rendered = str(result)
assert result["status"] == "AUDIT_OK"
assert result["pal_shards_scanned"] == 131
assert "secret-file-name" not in rendered
assert "secret-test-string" not in rendered
assert "DO_NOT_PUBLISH" not in rendered
assert result["owner_proven"] is False
assert sanitized_report("PRE327", None, "1", "abc")["status"] == "NO_REPORT"
assert sanitized_report("PRE327", {"status": "unexpected"}, "1", "abc")["status"] == "INVALID_STATUS"
assert "file_metadata" not in sanitized_report("PRE327", {"status": "AUDIT_OK", "file_metadata": ["unsafe"]}, "1", "abc")
print("PRE328_MOCK_STATUS AUDIT_OK")
print("PRE328_MOCK_ASSERTIONS 9")
