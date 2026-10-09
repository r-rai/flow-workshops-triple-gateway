"""Tests for W4 Public Evidence DB and Importer."""
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
import pytest
from scripts.w4_public_evidence import build_evidence_db, validate_run


def test_validate_run_sanitizes_and_projects():
    raw_run = {
        "run_id": "run-test123",
        "scenario": "permitted_payment",
        "state": "completed",
        "events": [
            {
                "label": "test",
                "boundary": "Gate 2",
                "arguments": {"account_id": "acc-101", "access_token": "secret-token"},
                "response": {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy.sig"},
            }
        ],
        "private_field_to_strip": "confidential",
    }
    cleaned = validate_run(raw_run)
    assert "private_field_to_strip" not in cleaned
    assert cleaned["run_id"] == "run-test123"
    # access_token stripped
    assert "access_token" not in cleaned["events"][0]["arguments"]
    # JWT replaced
    assert cleaned["events"][0]["response"]["token"] == "[credential redacted]"


def test_build_evidence_db_integration():
    source = Path("workshops/w4/evidence/incident-2026-10-05T170259Z.json")
    assert source.exists()

    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "test.sqlite"
        manifest_path = Path(td) / "manifest.json"

        manifest = build_evidence_db(source, db_path, manifest_path)
        assert manifest["run_count"] == 11
        assert len(manifest["sha256"]) == 64
        assert manifest_path.exists()

        # Check DB directly
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        count = conn.execute("SELECT count(*) FROM runs").fetchone()[0]
        assert count == 11
        conn.close()



def test_nested_and_text_credentials_removed_without_hiding_flow():
    raw = {"run_id": "run-secret-fixture", "scenario": "permitted_payment", "events": [{
        "label": "Recorded tool request", "status_code": 403,
        "identity": {"sub": "payments-agent", "scope": "api:payments:write"},
        "arguments": {"amount": 25000, "beneficiary": "vendor-alpha"},
        "response": {"password": "FAKE_PASSWORD_CANARY", "secret_key": "FAKE_SECRET_CANARY",
                     "cookie": "FAKE_COOKIE_CANARY", "error": "Bearer FAKE_OPAQUE_CREDENTIAL_CANARY",
                     "reason": "Beneficiary prohibited"}}]}
    clean = validate_run(raw)
    serialized = json.dumps(clean)
    assert "CANARY" not in serialized
    event = clean["events"][0]
    assert event["arguments"] == raw["events"][0]["arguments"]
    assert event["identity"] == raw["events"][0]["identity"]
    assert event["response"]["reason"] == "Beneficiary prohibited"
