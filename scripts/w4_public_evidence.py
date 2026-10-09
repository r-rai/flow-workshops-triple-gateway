#!/usr/bin/env python3
"""Offline importer for Workshop 4 public observation evidence.

Takes curated rehearsal evidence JSON, projects and sanitizes fields,
and creates an immutable SQLite database and SHA256 manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

ALLOWED_RUN_FIELDS = {
    "run_id",
    "scenario",
    "inference_mode",
    "state",
    "started_at",
    "identities",
    "events",
    "effects",
    "trace_id",
    "trace_status",
    "ticket",
    "delegation",
    "sandbox",
    "trace_services",
    "arguments",
    "proposal",
    "approval",
    "payment",
    "task",
    "mismatch_task",
    "reason",
    "service_result",
    "outage_verified",
}

FORBIDDEN_KEY_SUBSTRINGS = (
    "password",
    "secret_key",
    "api_key",
    "private_key",
    "signing_key",
    "raw_token",
)


def sanitize(value):
    if isinstance(value, dict):
        return {
            k: sanitize(v)
            for k, v in value.items()
            if not any(part in k.lower().replace("-", "_") for part in FORBIDDEN_KEY_SUBSTRINGS)
            and k.lower().replace("-", "_") not in (
                "access_token",
                "subject_token",
                "authorization",
                "api_key",
                "reasoning",
                "reasoning_content",
                "thinking",
                "raw_token",
                "cookie",
                "set_cookie",
                "refresh_token",
            )
        }
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, str):
        # Replace synthetic 400k filler characters in budget-denial recording
        if "Review incident xxxx" in value or (value.startswith("Review incident ") and value.count("x") > 10000):
            filler_count = value.count("x")
            value = f"Review incident [Synthetic budget-exhaustion input: {filler_count:,} filler characters; omitted for readability]"
        value = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer [credential redacted]", value)
        return re.sub(
            r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
            "[credential redacted]",
            value,
        )
    return value


def validate_run(run: dict) -> dict:
    if not isinstance(run, dict):
        raise ValueError("Run must be a dictionary")
    run_id = run.get("run_id")
    if not run_id or not isinstance(run_id, str):
        raise ValueError(f"Invalid run_id: {run_id}")
    scenario = run.get("scenario")
    if not scenario or not isinstance(scenario, str):
        raise ValueError(f"Invalid scenario in run {run_id}")

    # Project to allowed fields only
    projected = {k: v for k, v in run.items() if k in ALLOWED_RUN_FIELDS}

    # Ensure no forbidden substrings in keys
    for k in projected.keys():
        for f in FORBIDDEN_KEY_SUBSTRINGS:
            if f in k.lower():
                raise ValueError(f"Forbidden key pattern '{f}' in run {run_id} ({k})")

    # Sanitize content
    sanitized = sanitize(projected)
    return sanitized


def build_evidence_db(source_path: Path, db_path: Path, manifest_path: Path) -> dict:
    with open(source_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    runs = data.get("runs", [])
    if not runs or len(runs) < 10:
        raise ValueError(f"Expected at least 10 runs in evidence, got {len(runs)}")

    # Ensure DB directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE runs (
            id TEXT PRIMARY KEY,
            scenario TEXT NOT NULL,
            state TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """
    )
    cur.execute(
        """
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """
    )

    clean_runs = []
    seen_ids = set()
    for r in runs:
        cleaned = validate_run(r)
        rid = cleaned["run_id"]
        if rid in seen_ids:
            raise ValueError(f"Duplicate run ID detected: {rid}")
        seen_ids.add(rid)
        clean_runs.append(cleaned)
        cur.execute(
            "INSERT INTO runs (id, scenario, state, data) VALUES (?, ?, ?, ?)",
            (rid, cleaned["scenario"], cleaned.get("state", "unknown"), json.dumps(cleaned)),
        )

    timestamp = data.get("timestamp", "2026-10-05T170259Z")
    cur.execute("INSERT INTO metadata (key, value) VALUES ('timestamp', ?)", (timestamp,))
    cur.execute("INSERT INTO metadata (key, value) VALUES ('run_count', ?)", (str(len(clean_runs)),))
    cur.execute("INSERT INTO metadata (key, value) VALUES ('version', '1.0.0')")

    conn.commit()
    conn.close()

    # Make file read-only on filesystem
    os.chmod(db_path, 0o444)

    # Calculate SHA256 of DB
    hasher = hashlib.sha256()
    with open(db_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    db_hash = hasher.hexdigest()

    manifest = {
        "source_file": str(source_path),
        "capture_timestamp": timestamp,
        "run_count": len(clean_runs),
        "run_ids": [r["run_id"] for r in clean_runs],
        "scenarios": [r["scenario"] for r in clean_runs],
        "db_file": db_path.name,
        "sha256": db_hash,
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def main():
    parser = argparse.ArgumentParser(description="Build W4 Public Evidence DB")
    parser.add_argument(
        "--source",
        default="workshops/w4/evidence/incident-2026-10-05T170259Z.json",
        help="Path to curated rehearsal evidence JSON",
    )
    parser.add_argument(
        "--output-db",
        default="data/w4-public-evidence.sqlite",
        help="Path to output SQLite database",
    )
    parser.add_argument(
        "--manifest",
        default="data/w4-public-evidence-manifest.json",
        help="Path to output JSON manifest",
    )
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        print(f"Error: source evidence {source} not found.", file=sys.stderr)
        sys.exit(1)

    out_db = Path(args.output_db)
    manifest_p = Path(args.manifest)

    print(f"Importing evidence from {source}...")
    manifest = build_evidence_db(source, out_db, manifest_p)
    print(f"Evidence DB created at {out_db} (mode 0444)")
    print(f"Runs imported: {manifest['run_count']}")
    print(f"SHA256: {manifest['sha256']}")
    print(f"Manifest saved to {manifest_p}")


if __name__ == "__main__":
    main()
