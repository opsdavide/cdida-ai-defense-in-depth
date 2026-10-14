import sys
import os
import json
import hmac
import hashlib
import time
import pytest
from unittest.mock import AsyncMock, patch

# Add parent directory to sys.path so we can import gateway modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app, rate_limiter
from rate_limiter import InMemoryRateLimiter
from audit_logger import LOG_SECRET

# Force rate limiter to be in-memory for tests to avoid Redis connection attempts
rate_limiter.active = False
rate_limiter.fallback_limiter = InMemoryRateLimiter()

@pytest.fixture
def client():
    # Clear client history and rate limiter state before each test
    rate_limiter.fallback_limiter.history.clear()
    with TestClient(app) as c:
        yield c

def get_token_for_role(client, role):
    response = client.post(f"/api/v1/auth/token?role={role}")
    assert response.status_code == 200
    return response.json()["access_token"]

def test_rate_limiter_guest_denies_after_threshold(client):
    guest_token = get_token_for_role(client, "guest")
    headers = {"Authorization": f"Bearer {guest_token}"}
    
    with patch("main.http_client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = b'{"status": "success"}'
        
        # Guest can make 5 requests
        for i in range(5):
            res = client.post("/api/v1/inference", json={"prompt": f"Hello world {i}"}, headers=headers)
            assert res.status_code == 200
            
        # The 6th request must be rate limited
        res = client.post("/api/v1/inference", json={"prompt": "Hello world 5"}, headers=headers)
        assert res.status_code == 429
        assert "Rate limit exceeded" in res.json()["detail"]

def test_payload_inspector_blocking(client):
    guest_token = get_token_for_role(client, "guest")
    headers = {"Authorization": f"Bearer {guest_token}"}
    
    # Prompt with length > 500 and repetition ratio > 0.3 to exceed 0.7 risk threshold
    # "hello " * 100 has length 600 and repetition ratio 0.99
    bad_prompt = "hello " * 100
    
    # Even if it bypasses for some reason, we mock the post request to avoid closed client errors
    with patch("main.http_client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        res = client.post("/api/v1/inference", json={"prompt": bad_prompt}, headers=headers)
        assert res.status_code == 400
        assert "Security alert: Prompt rejected" in res.json()["detail"]
        assert "High token repetition ratio" in res.json()["detail"] or "length" in res.json()["detail"]

def test_admin_bypasses_rate_limit_but_subject_to_payload_inspector(client):
    admin_token = get_token_for_role(client, "admin")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    with patch("main.http_client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = b'{"status": "success"}'
        
        # Send 10 requests (far beyond guest limit of 5 and fast enough to test rate limit)
        for i in range(10):
            res = client.post("/api/v1/inference", json={"prompt": f"Hello world {i}"}, headers=headers)
            assert res.status_code == 200
            
        # Verify admin is still subject to the payload inspector
        bad_prompt = "hello " * 100
        res = client.post("/api/v1/inference", json={"prompt": bad_prompt}, headers=headers)
        assert res.status_code == 400
        assert "Security alert: Prompt rejected" in res.json()["detail"]

def test_audit_logs_contain_all_fields_and_valid_signature(client):
    guest_token = get_token_for_role(client, "guest")
    headers = {"Authorization": f"Bearer {guest_token}"}
    
    with patch("main.http_client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = b'{"status": "success"}'
        
        with patch("audit_logger.logger.info") as mock_logger_info:
            res = client.post("/api/v1/inference", json={"prompt": "Test audit log"}, headers=headers)
            assert res.status_code == 200
            
            # Check what was logged
            assert mock_logger_info.called
            log_str = mock_logger_info.call_args[0][0]
            log_data = json.loads(log_str)
            
            # Verify fields
            expected_fields = {"timestamp", "client_ip", "role", "status_code", "latency_ms", "decision", "detail", "signature"}
            assert set(log_data.keys()) == expected_fields
            assert log_data["role"] == "guest"
            assert log_data["status_code"] == 200
            assert log_data["decision"] == "ALLOWED"
            
            # Recalculate HMAC-SHA256 signature to verify integrity
            signature_to_check = log_data.pop("signature")
            serialized_data = json.dumps(log_data, sort_keys=True)
            
            recalculated_signature = hmac.new(
                LOG_SECRET.encode("utf-8"),
                serialized_data.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            assert signature_to_check == recalculated_signature
