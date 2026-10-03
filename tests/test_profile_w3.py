import sys
import httpx

def main():
    print("=== Running Profile w3 Verification Smoke Test ===")
    base_url = "http://127.0.0.1:9080"
    headers = {"X-API-Key": "gate3-secret-token"}

    with httpx.Client(timeout=10.0) as client:
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
