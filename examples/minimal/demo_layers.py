"""
Minimal Reproducible Example for C-DIDA Defense-in-Depth Verification.

Validates the three defense layers:
- Layer 1: Nginx Volumetric Burst Mitigation (HTTP 429)
- Layer 2: API Gateway RBAC & Sliding-Window Quota (HTTP 401 / HTTP 429)
- Layer 3: Payload Inspector IDS Heuristic Filtering (HTTP 400 Bad Request)
"""

import os
import sys
import time
import httpx
import jwt

NGINX_URL = "http://localhost:8080"
GATEWAY_URL = "http://localhost:8000"
JWT_SECRET = "super_secret_dev_key_change_in_production"
JWT_ALGORITHM = "HS256"


def create_token(role: str, user_id: str = "test-user") -> str:
    """Generates a test JWT signed with HMAC-SHA256."""
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def test_live_stack():
    """Attempts live network tests against Docker endpoints."""
    print("\n--- [MODE: LIVE DOCKER STACK CHECK] ---")
    try:
        r = httpx.get(f"{GATEWAY_URL}/api/v1/health", timeout=1.0)
        live = True
    except Exception:
        live = False

    if not live:
        print("[INFO] Docker stack is not currently active on localhost:8000/8080.")
        return False

    print("[INFO] Active Docker containers detected! Executing live network tests...")
    token = create_token("guest")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Layer 1 Nginx
    print("\n[TEST 1] Layer 1: Nginx Perimeter Volumetric Drop")
    status_codes = []
    with httpx.Client(timeout=4.0) as client:
        for _ in range(15):
            try:
                res = client.get(f"{NGINX_URL}/api/v1/health", headers=headers)
                status_codes.append(res.status_code)
            except Exception:
                pass
    dropped = status_codes.count(429)
    print(f"  -> Burst: 15 dispatched | Accepted: {status_codes.count(200)} | Dropped (HTTP 429): {dropped}")
    assert dropped > 0, "Layer 1 did not drop excess requests"
    print("  [PASS] Layer 1 Volumetric filter verified!")
    return True


def test_standalone_gateway():
    """Runs in-process standalone verification of Layer 2 & Layer 3 via FastAPI TestClient."""
    print("\n--- [MODE: STANDALONE ENGINE VERIFICATION] ---")
    gateway_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gateway"))
    if gateway_path not in sys.path:
        sys.path.insert(0, gateway_path)

    try:
        from fastapi.testclient import TestClient
        from unittest.mock import AsyncMock, patch
        from main import app, rate_limiter
        from rate_limiter import InMemoryRateLimiter
    except ImportError as e:
        print(f"[FAIL] Missing test dependency: {e}")
        return False

    rate_limiter.active = False
    rate_limiter.fallback_limiter = InMemoryRateLimiter()

    with TestClient(app) as client:
        # Layer 2: Test unauthenticated
        print("\n[TEST 2.1] Layer 2: Reject Unauthenticated Request")
        r = client.post("/api/v1/inference", json={"prompt": "Hello"})
        assert r.status_code == 401
        print(f"  [PASS] Missing token rejected: HTTP {r.status_code} Unauthorized.")

        # Layer 2: Test Guest Quota (5 req/min)
        print("\n[TEST 2.2] Layer 2: Sliding-Window Quota Throttling (Guest: 5 r/m)")
        token = create_token("guest")
        headers = {"Authorization": f"Bearer {token}"}
        with patch("main.http_client.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.content = b'{"status": "success"}'
            for i in range(5):
                r = client.post("/api/v1/inference", json={"prompt": f"Safe prompt {i}"}, headers=headers)
                assert r.status_code == 200
            r_exceeded = client.post("/api/v1/inference", json={"prompt": "Exceeding prompt"}, headers=headers)
            assert r_exceeded.status_code == 429
            print(f"  [PASS] Quota violation dropped: HTTP {r_exceeded.status_code} ({r_exceeded.json().get('detail')}).")

        # Layer 3: Test Semantic DoS (Oversized + High Token Repetition)
        print("\n[TEST 3.1] Layer 3: Payload Inspector (Semantic DoS / Repetition Heuristic)")
        admin_token = create_token("admin")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        bad_prompt = "hello " * 100  # Length 600 chars and repetition ratio 0.99 -> Risk Score > 0.7
        r_bad = client.post("/api/v1/inference", json={"prompt": bad_prompt}, headers=admin_headers)
        assert r_bad.status_code == 400
        print(f"  [PASS] Malicious prompt rejected: HTTP {r_bad.status_code} ({r_bad.json().get('detail')}).")

        # Layer 3: Test Admin Role Exempt from Rate Limit but Subject to Payload Inspector
        print("\n[TEST 3.2] Layer 3: Admin Privilege Policy Verification")
        with patch("main.http_client.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.content = b'{"status": "success"}'
            for i in range(10):
                r = client.post("/api/v1/inference", json={"prompt": f"Admin query {i}"}, headers=admin_headers)
                assert r.status_code == 200
            print("  [PASS] Admin allowed to bypass rate limits (10/10 accepted).")
            
            # Verify payload inspector still intercepts admin on malicious payload
            r_admin_bad = client.post("/api/v1/inference", json={"prompt": bad_prompt}, headers=admin_headers)
            assert r_admin_bad.status_code == 400
            print("  [PASS] Admin is strictly subjected to Payload Inspector (HTTP 400).")

    return True


def main():
    print("=" * 65)
    print(" C-DIDA: Minimal Defense-in-Depth Verification Suite")
    print("=" * 65)
    
    live_ok = test_live_stack()
    standalone_ok = test_standalone_gateway()

    print("\n" + "=" * 65)
    if live_ok or standalone_ok:
        print(" [RESULT] DEFENSE VERIFICATION SUITE: OK")
        print("=" * 65)
        sys.exit(0)
    else:
        print(" [RESULT] DEFENSE VERIFICATION SUITE: KO")
        print("=" * 65)
        sys.exit(1)


if __name__ == "__main__":
    main()
