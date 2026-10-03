"""Live read-only checks. Exchanges tokens but performs no financial mutations."""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import httpx
from jose import jwt
from src.core.config import settings
from src.core.security import create_jwt_token

out = Path(__file__).parent
base = "http://127.0.0.1:9080"
key = {"X-API-Key": settings.API_KEY_SECRET}
results = {}
def response_body(response):
    try:
        return {k: v for k, v in response.json().items() if k != "access_token"}
    except ValueError:
        return {"raw": response.text[:500]}
with httpx.Client(timeout=10) as client:
    source = create_jwt_token("exchange-audit-viewer", "novabank-mcp", ["mcp:tools"], role="viewer")
    standard = {"grant_type": "urn:ietf:params:oauth:grant-type:token-exchange", "subject_token": source, "subject_token_type": "urn:ietf:params:oauth:token-type:access_token", "audience": "novabank-api", "scope": "api:accounts:read"}
    exchanges = []
    for path, encoding in [("/oauth/token", "form"), ("/oauth/token", "json"), ("/api/v1/oauth/token", "json")]:
        r = client.post(base + path, headers=key, **({"data": standard} if encoding == "form" else {"json": standard}))
        exchanges.append({"path": path, "encoding": encoding, "status": r.status_code, "body": response_body(r)})
    results["normal_token_exchange"] = exchanges

    # An issuer-signed viewer token with no audience demonstrates missing exchange authorization.
    claims = {"iss": settings.JWT_ISSUER, "sub": "exchange-audit-viewer", "role": "viewer", "scope": "api:accounts:read", "iat": int(time.time()), "exp": int(time.time()) + 60}
    no_aud_source = jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    initial = client.get(base + "/api/v1/payments", headers={**key, "Authorization": "Bearer " + no_aud_source})
    escalation = {**standard, "subject_token": no_aud_source, "scope": "api:payments:write"}
    r = client.post(base + "/oauth/token", json=escalation)
    record = {"source_claims": claims, "source_payments_list_status": initial.status_code, "exchange_status": r.status_code}
    if r.status_code == 200:
        body = r.json(); exchanged = body.pop("access_token")
        record["response_without_token"] = body
        record["exchanged_claims"] = jwt.get_unverified_claims(exchanged)
        record["exchanged_payments_list_status"] = client.get(base + "/api/v1/payments", headers={**key, "Authorization": "Bearer " + exchanged}).status_code
    else:
        record["error"] = r.json()
    results["viewer_scope_escalation"] = record
    for name, value in [("missing", None), ("unsupported", "not-a-token-type")]:
        request = {**standard, "subject_token": no_aud_source}
        if value is None: request.pop("subject_token_type")
        else: request["subject_token_type"] = value
        r = client.post(base + "/oauth/token", json=request)
        results[f"subject_token_type_{name}"] = {"status": r.status_code, "body": response_body(r)}

    # This pre-audit task existed in the original DB backup and remains readable after API restart.
    db = sqlite3.connect("/tmp/novabank-reaudit-backup/api.sqlite")
    db.row_factory = sqlite3.Row
    task = db.execute("select * from a2a_tasks limit 1").fetchone()
    if task:
        token = create_jwt_token(task["owner_id"], "novabank-api", ["api:a2a:tasks"], role=task["owner_role"])
        r = client.get(base + "/api/v1/a2a/tasks/" + task["id"], headers={**key, "Authorization": "Bearer " + token})
        results["a2a_survives_api_restart"] = {"backup_task_id": task["id"], "backup_owner": task["owner_id"], "status": r.status_code, "body": r.json()}
    db.close()
    results["jaeger_services"] = client.get("http://127.0.0.1:16686/api/services").json()

containers = json.loads(subprocess.check_output(["docker", "inspect", *subprocess.check_output(["docker", "compose", "ps", "-q"], text=True).split()]))
results["runtime"] = [{"name": c["Name"], "service": c["Config"]["Labels"]["com.docker.compose.service"], "image": c["Config"]["Image"], "image_id": c["Image"], "memory_limit": c["HostConfig"]["Memory"], "port_bindings": c["HostConfig"]["PortBindings"], "networks": list(c["NetworkSettings"]["Networks"]), "running": c["State"]["Running"], "restarts": c["RestartCount"]} for c in containers]
results["aggregate_memory_caps_bytes"] = sum(c["memory_limit"] for c in results["runtime"])
network_code = '''import socket,json,urllib.request
r={}
for host,port in [("api",8000),("apisix",9080)]:
 try:
  s=socket.create_connection((host,port),timeout=2);s.close();r[host]="connected"
 except Exception as e:r[host]=type(e).__name__+": "+str(e)
q=urllib.request.Request("http://apisix:9080/api/v1/accounts/acc-101",headers={"X-API-Key":"gate3-secret-token"})
r["gate3_account_status"]=urllib.request.urlopen(q,timeout=5).status
print(json.dumps(r))'''
results["worker_network"] = json.loads(subprocess.check_output(["docker", "exec", "novabank-workshops-worker-1", "python", "-c", network_code], text=True))
source_files = {"api": ["src/api/routes/oauth.py", "src/api/routes/a2a.py", "src/services/banking.py", "src/services/approvals.py", "src/core/security.py"], "adapter": ["src/adapter/server.py"], "worker": ["src/worker/kafka_consumer.py", "src/worker/activities.py"]}
checks = []
for service, files in source_files.items():
    code = "import hashlib,json; from pathlib import Path; print(json.dumps({p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in " + repr(files) + "}))"
    hashes = json.loads(subprocess.check_output(["docker", "exec", f"novabank-workshops-{service}-1", "python", "-c", code], text=True))
    for filename in files:
        local = hashlib.sha256(Path(filename).read_bytes()).hexdigest()
        checks.append({"service": service, "file": filename, "source_sha256": local, "runtime_sha256": hashes[filename], "match": hashes[filename] == local})
results["runtime_source_checks"] = checks
manifest = json.loads(Path("config/manifest.json").read_text())
digests = []
for service, entry in manifest["pinned_images"].items():
    installed = json.loads(subprocess.check_output(["docker", "image", "inspect", entry["image"]]))[0]["RepoDigests"]
    digests.append({"service": service, "manifest_digest": entry["digest"], "installed_repo_digests": installed, "matches": any(d.split("@")[-1] == entry["digest"] for d in installed)})
results["third_party_image_digests"] = digests
out.joinpath("live-readonly-probes.json").write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
