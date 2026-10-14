import hmac
import hashlib
import json
import os
import logging
from datetime import datetime, timezone

# Configure Logger to print JSON format for structured auditing
logger = logging.getLogger("api_gateway.audit")

# Secret key for log signing: fallback to JWT_SECRET or a hardcoded default
LOG_SECRET = os.getenv("LOG_SIGNING_KEY", os.getenv("JWT_SECRET", "super_secret_log_signing_key"))

def log_audit_event(ip: str, role: str, status_code: int, latency_ms: float, decision: str, detail: str = ""):
    """
    Utility function to log security and access events.
    Each log entry is serialized as structured JSON and signed cryptographically
    using HMAC-SHA256 to ensure tamper-evident logging.
    """
    # 1. Structure the audit log record (insertion order is preserved)
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "client_ip": ip,
        "role": role,
        "status_code": status_code,
        "latency_ms": round(latency_ms, 2),
        "decision": decision,
        "detail": detail
    }
    
    # 2. Serialize data deterministically to generate signature
    # Using sort_keys=True ensures key order consistency regardless of platform
    serialized_data = json.dumps(log_data, sort_keys=True)
    
    # 3. Calculate HMAC-SHA256 signature
    signature = hmac.new(
        LOG_SECRET.encode("utf-8"),
        serialized_data.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    # 4. Inject signature into final log record
    log_data["signature"] = signature
    
    # 5. Output raw JSON log to be collected by Nginx/container logs
    logger.info(json.dumps(log_data))
