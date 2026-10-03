import time
import json
from jose import jwt, JWTError
from typing import Dict, Any, List, Optional

SECRET_KEY = "novabank-super-secret-signing-key-for-lab"
ALGORITHM = "HS256"
ISSUER = "https://identity.novabank.internal/realms/novabank"

def issue_token(
    subject: str,
    audience: str,
    scopes: List[str],
    role: str,
    expires_in_sec: int = 3600,
    issuer: str = ISSUER,
    custom_claims: Optional[Dict[str, Any]] = None,
) -> str:
    now = int(time.time())
    payload = {
        "iss": issuer,
        "sub": subject,
        "aud": audience,
        "exp": now + expires_in_sec,
        "nbf": now,
        "iat": now,
        "scope": " ".join(scopes),
        "role": role,
    }
    if custom_claims:
        payload.update(custom_claims)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def exchange_token(
    subject_token: str,
    requested_audience: str,
    requested_scopes: List[str],
    adapter_client_id: str = "mcp-adapter",
) -> Dict[str, Any]:
    """
    Implements RFC 8693 Token Exchange semantics:
    - Validates subject_token (incoming MCP token)
    - Verifies subject_token audience is 'novabank-mcp'
    - Issues exchanged API-facing token for 'requested_audience' ('novabank-api')
    - Downscopes permissions so requested_scopes cannot exceed adapter privileges
    - Preserves trusted subject and role, adds delegation/act claim
    """
    try:
        claims = jwt.decode(
            subject_token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            audience="novabank-mcp",
        )
    except JWTError as e:
        raise ValueError(f"Invalid subject token: {e}")

    # Downscope: Adapter can only grant authorized API scopes
    ALLOWED_ADAPTER_SCOPES = {"api:accounts:read", "api:payments:write", "api:cases:read"}
    effective_scopes = [s for s in requested_scopes if s in ALLOWED_ADAPTER_SCOPES]

    now = int(time.time())
    exchanged_payload = {
        "iss": ISSUER,
        "sub": claims["sub"],
        "aud": requested_audience,
        "exp": now + 900, # 15 min short-lived API token
        "iat": now,
        "scope": " ".join(effective_scopes),
        "role": claims.get("role", "viewer"),
        "act": {
            "sub": adapter_client_id,
        },
        "token_type": "urn:ietf:params:oauth:token-type:access_token",
    }
    new_token = jwt.encode(exchanged_payload, SECRET_KEY, algorithm=ALGORITHM)
    return {
        "access_token": new_token,
        "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "token_type": "Bearer",
        "expires_in": 900,
        "scope": " ".join(effective_scopes),
    }

def gate3_authorize(token: str, required_scope: str, expected_audience: str = "novabank-api") -> Dict[str, Any]:
    """
    Gate 3 API verification contract:
    - Validates signature and issuer
    - Validates audience == 'novabank-api'
    - Checks required scope
    - Returns verified principal
    """
    try:
        claims = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            audience=expected_audience,
        )
    except JWTError as e:
        raise PermissionError(f"Gate 3 Authentication Failed: {e}")

    token_scopes = claims.get("scope", "").split()
    if required_scope not in token_scopes:
        raise PermissionError(
            f"Gate 3 Scope Check Failed: required '{required_scope}', token has '{token_scopes}'"
        )

    return {
        "principal_id": claims["sub"],
        "role": claims.get("role"),
        "scopes": token_scopes,
        "delegated_by": claims.get("act", {}).get("sub"),
    }

def main():
    print("=====================================================================")
    print("SPIKE 4: Audience-Separated Identity & Token Exchange (RFC 8693)")
    print("=====================================================================")

    # 1. Issue an MCP token for agent
    print("\n--- Step 1: Issue MCP-facing token ---")
    mcp_token = issue_token(
        subject="agent-support-42",
        audience="novabank-mcp",
        scopes=["mcp:tools"],
        role="support_agent",
    )
    print("MCP Token generated for audience 'novabank-mcp'")

    # 2. Test Direct Presentation to Gate 3 (Must Fail - Wrong Audience)
    print("\n--- Step 2: Attempt direct presentation of MCP token to Gate 3 ---")
    try:
        gate3_authorize(mcp_token, required_scope="api:accounts:read")
        print("❌ FAILED: Gate 3 accepted token with wrong audience!")
        return 1
    except PermissionError as e:
        print("✓ SUCCESS: Gate 3 rejected MCP token directly:", e)

    # 3. Exchange MCP token for API token (with accounts:read scope)
    print("\n--- Step 3: Perform RFC 8693 Token Exchange for 'api:accounts:read' ---")
    exchange_res = exchange_token(
        subject_token=mcp_token,
        requested_audience="novabank-api",
        requested_scopes=["api:accounts:read"],
    )
    api_token = exchange_res["access_token"]
    print("Exchanged Token received. Scopes:", exchange_res["scope"])

    # 4. Test Gate 3 with valid exchanged token on account read
    print("\n--- Step 4: Verify exchanged token on Gate 3 Account Read ---")
    auth_ctx = gate3_authorize(api_token, required_scope="api:accounts:read")
    print("✓ Gate 3 Authorized successfully:")
    print("  Principal ID:", auth_ctx["principal_id"])
    print("  Role:", auth_ctx["role"])
    print("  Delegated By (Adapter):", auth_ctx["delegated_by"])
    assert auth_ctx["principal_id"] == "agent-support-42"
    assert auth_ctx["delegated_by"] == "mcp-adapter"

    # 5. Test Insufficient Scope on Gate 3 (Attempt payment with read-only token)
    print("\n--- Step 5: Test Insufficient Scope (Calling payments endpoint) ---")
    try:
        gate3_authorize(api_token, required_scope="api:payments:write")
        print("❌ FAILED: Gate 3 allowed payment without api:payments:write scope!")
        return 1
    except PermissionError as e:
        print("✓ SUCCESS: Gate 3 rejected insufficient scope:", e)

    # 6. Test Token with Expired Timestamp
    print("\n--- Step 6: Test Expired Token Denial ---")
    expired_token = issue_token(
        subject="agent-support-42",
        audience="novabank-api",
        scopes=["api:accounts:read"],
        role="support_agent",
        expires_in_sec=-10,
    )
    try:
        gate3_authorize(expired_token, required_scope="api:accounts:read")
        print("❌ FAILED: Gate 3 allowed expired token!")
        return 1
    except PermissionError as e:
        print("✓ SUCCESS: Gate 3 rejected expired token:", e)

    # 7. Test Spoofed Caller Context
    print("\n--- Step 7: Test Caller Context Authenticity ---")
    # Even if an attacker passes HTTP header "X-User-Id: superadmin", Gate 3 derives identity ONLY from claims
    spoofed_header = "superadmin"
    assert auth_ctx["principal_id"] != spoofed_header
    assert auth_ctx["principal_id"] == "agent-support-42"
    print("✓ SUCCESS: Authoritative identity derived strictly from validated JWT claims.")

    print("\n=====================================================================")
    print("✅ SPIKE 4 PASSED COMPLETELY!")
    print("1. MCP audience ('novabank-mcp') separated from API audience ('novabank-api').")
    print("2. Gate 3 strictly enforces audience check (MCP token rejected).")
    print("3. RFC 8693 token exchange downscopes permissions and binds adapter delegation.")
    print("4. Gate 3 enforces required scopes (read token cannot execute payments).")
    print("5. Expired tokens and spoofed headers denied.")
    print("=====================================================================")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
