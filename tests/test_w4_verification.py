"""Regression coverage for verification against an existing participant stack."""
import os
from pathlib import Path
import runpy
import subprocess
import sys

import httpx
from jose import jwt
import pytest


@pytest.mark.parametrize("audience,secret,issuer", [
    ("flobank-api", "flobank-super-secret-signing-key-for-lab", "https://identity.flobank.internal/realms/flobank"),
    ("novabank-api", "participant-custom-signing-secret", "https://identity.novabank.internal/realms/novabank"),
])
def test_verification_uses_running_api_credentials(monkeypatch, capsys, audience, secret, issuer):
    original_run = subprocess.run
    container_env = dict(os.environ, API_AUDIENCE=audience, JWT_SECRET_KEY=secret,
                         JWT_ISSUER=issuer, JWT_ALGORITHM="HS256", GATE3_API_KEY="participant-key")

    def docker_exec(command, **kwargs):
        assert command[:7] == ["docker", "compose", "exec", "-T", "api", "python", "-c"]
        # Execute the actual container-side program with isolated runtime settings.
        return original_run([sys.executable, "-c", command[7]], env=container_env, **kwargs)

    monkeypatch.setattr(subprocess, "run", docker_exec)
    real_client = httpx.Client

    def gateway(request):
        if request.url.path == "/api/v1/accounts/acc-101":
            try:
                jwt.decode(request.headers["Authorization"].removeprefix("Bearer "),
                           secret, algorithms=["HS256"], audience=audience, issuer=issuer)
            except Exception:
                return httpx.Response(401, json={"detail": "Invalid bearer token"})
            if request.headers["X-API-Key"] != "participant-key":
                return httpx.Response(401, json={"detail": "Invalid API key"})
            return httpx.Response(200, json={"name": "Checking"})
        if request.url.path == "/.well-known/agent.json":
            return httpx.Response(200, json={"name": "PaymentsAgent"})
        return httpx.Response(200, json={})

    monkeypatch.setattr(httpx, "Client", lambda **kw: real_client(transport=httpx.MockTransport(gateway), **kw))
    module = runpy.run_path(str(Path(__file__).with_name("test_profile_w4.py")))
    assert module["main"]() == 0
    output = capsys.readouterr().out
    assert "ALL CHECKS PASSED" in output
    assert secret not in output
    assert "participant-key" not in output


def test_gate3_failure_reports_service_response(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess(a[0], 0, '{"Authorization":"Bearer test","X-API-Key":"test"}', ""))
    real_client = httpx.Client

    def gateway(request):
        if request.url.path == "/api/v1/accounts/acc-101":
            return httpx.Response(401, json={"detail": "Invalid audience"})
        return httpx.Response(200, json={})

    monkeypatch.setattr(httpx, "Client", lambda **kw: real_client(transport=httpx.MockTransport(gateway), **kw))
    module = runpy.run_path(str(Path(__file__).with_name("test_profile_w4.py")))
    with pytest.raises(AssertionError, match="Gate 3.*401.*Invalid audience"):
        module["main"]()


@pytest.mark.parametrize("result", [
    subprocess.CalledProcessError(1, ["docker"], output="secret-token", stderr="secret-key"),
    subprocess.TimeoutExpired(["docker"], 15, output="secret-token"),
    subprocess.CompletedProcess(["docker"], 0, "secret-token", ""),
    subprocess.CompletedProcess(["docker"], 0, '{"Authorization":"secret-token"}', ""),
])
def test_unavailable_credentials_fail_without_exposing_secrets(monkeypatch, capsys, result):
    def docker_exec(*args, **kwargs):
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(subprocess, "run", docker_exec)
    module = runpy.run_path(str(Path(__file__).with_name("test_profile_w4.py")))
    assert module["main"]() == 1
    output = capsys.readouterr().out
    assert "./scripts/workshop status" in output
    assert "secret-token" not in output
    assert "secret-key" not in output
