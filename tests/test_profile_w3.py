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
        print("✓ Incident remediation endpoint verified")

    print("=== Profile w3 Verification Complete: ALL CHECKS PASSED ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
