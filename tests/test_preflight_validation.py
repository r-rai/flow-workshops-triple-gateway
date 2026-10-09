import json
import os
import subprocess
import sys
import tempfile
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSHOP_SCRIPT = os.path.join(REPO_ROOT, "scripts", "workshop")

def run_workshop_preflight(manifest_path: str = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if manifest_path:
        env["WORKSHOP_MANIFEST_PATH"] = manifest_path
    elif "WORKSHOP_MANIFEST_PATH" in env:
        del env["WORKSHOP_MANIFEST_PATH"]

    return subprocess.run(
        [WORKSHOP_SCRIPT, "preflight"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

def test_preflight_cli_positive_default():
    """Verify that actual ./scripts/workshop preflight succeeds against default config/manifest.json."""
    res = run_workshop_preflight()
    assert res.returncode == 0, f"Preflight failed:\nstdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    with open(os.path.join(REPO_ROOT, "config", "manifest.json")) as f:
        pinned_count = len(json.load(f)["pinned_images"])
    assert f"All {pinned_count} pinned digests verified" in res.stdout
    assert "Preflight PASSED" in res.stdout

def test_preflight_cli_negative_malformed_json():
    """Verify ./scripts/workshop preflight fails-closed on malformed manifest JSON."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write("{ invalid json content ...")
        tmp_name = f.name
    try:
        res = run_workshop_preflight(manifest_path=tmp_name)
        assert res.returncode != 0
        assert "Failed to read or parse" in res.stdout or "Failed to read or parse" in res.stderr
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

def test_preflight_cli_negative_missing_pinned_images():
    """Verify ./scripts/workshop preflight fails-closed when pinned_images is missing."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write(json.dumps({"manifest_version": "1.0"}))
        tmp_name = f.name
    try:
        res = run_workshop_preflight(manifest_path=tmp_name)
        assert res.returncode != 0
        assert "no pinned_images mapping" in res.stdout or "no pinned_images mapping" in res.stderr
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

def test_preflight_cli_negative_digest_mismatch():
    """Verify ./scripts/workshop preflight fails-closed when an image digest does not match."""
    # Load actual manifest and tamper with one digest
    with open(os.path.join(REPO_ROOT, "config", "manifest.json")) as f:
        manifest = json.load(f)

    # Change apisix expected digest
    manifest["pinned_images"]["apisix"]["digest"] = "sha256:0000000000000000000000000000000000000000000000000000000000000000"

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(manifest, f)
        tmp_name = f.name
    try:
        res = run_workshop_preflight(manifest_path=tmp_name)
        assert res.returncode != 0
        assert "digest mismatch for" in res.stdout or "digest mismatch for" in res.stderr
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

def test_preflight_cli_negative_missing_image_inspection():
    """Verify ./scripts/workshop preflight fails-closed when an expected image does not exist."""
    with open(os.path.join(REPO_ROOT, "config", "manifest.json")) as f:
        manifest = json.load(f)

    manifest["pinned_images"]["nonexistent"] = {
        "image": "flobank-nonexistent-image:latest",
        "digest": "sha256:deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(manifest, f)
        tmp_name = f.name
    try:
        res = run_workshop_preflight(manifest_path=tmp_name)
        assert res.returncode != 0
        assert "inspection failed for" in res.stdout or "inspection failed for" in res.stderr
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))
