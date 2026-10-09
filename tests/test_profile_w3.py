import sys
import subprocess
import httpx

def verify_temporal_ui(client):
    # Resolve the actual published port, including .env TEMPORAL_UI_PORT overrides.
    port = subprocess.run(
        ["docker", "compose", "--profile", "w3", "port", "temporal-ui", "8080"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert port, "Temporal UI is not running; start the w3 profile"
    base = f"http://{port}"
    page = client.get(base)
    page.raise_for_status()
    assert "text/html" in page.headers.get("content-type", ""), "Temporal UI page unavailable"
    namespaces = client.get(f"{base}/api/v1/namespaces")
    namespaces.raise_for_status()
    assert any(
        ns["namespaceInfo"]["name"] == "default"
        for ns in namespaces.json()["namespaces"]
    ), "Temporal UI cannot access the default namespace"
    workflows = client.get(f"{base}/api/v1/namespaces/default/workflows")
    workflows.raise_for_status()
    assert isinstance(workflows.json().get("executions", []), list), "Temporal UI workflow listing unavailable"
    print(f"✓ Temporal UI and workflow listing verified ({base})")

def main():
    print("=== Running Profile w3 Verification Smoke Test ===")
    base_url = "http://127.0.0.1:9080"
    headers = {"X-API-Key": "gate3-secret-token"}

    with httpx.Client(timeout=10.0) as client:
        verify_temporal_ui(client)
        # Check incident read
        r_inc = client.get(f"{base_url}/api/v1/incidents/inc-901", headers=headers)
        assert r_inc.status_code == 200, f"Failed to get incident: {r_inc.status_code}"
        assert r_inc.json()["id"] == "inc-901"
        print("✓ Incident retrieval verified:", r_inc.json()["service_name"])

        # Check remediation
        r_rem = client.post(
            f"{base_url}/api/v1/incidents/inc-901/remediate",
            headers=headers,
            json={"action": "restart_service"}
        )
        assert r_rem.status_code in (200, 400) # 400 if already remediated in this run
        # Check Temporal connectivity
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        assert s.connect_ex(('127.0.0.1', 7233)) == 0, "Temporal port 7233 unreachable"
        s.close()
        print("✓ Temporal server connectivity verified (7233)")

        # Check Kafka connectivity
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.settimeout(2.0)
        assert s2.connect_ex(('127.0.0.1', 9092)) == 0, "Kafka port 9092 unreachable"
        s2.close()
        print("✓ Kafka broker connectivity verified (9092)")

    print("=== Profile w3 Verification Complete: ALL CHECKS PASSED ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
