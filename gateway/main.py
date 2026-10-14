import os
import json
import time
import logging
import httpx
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from pydantic import BaseModel
from auth import get_current_user_claims, create_access_token
from rate_limiter import RedisRateLimiter, get_rate_limiter_policy
from payload_inspector import PayloadInspector
from audit_logger import log_audit_event

# Configure Logger to print JSON format for structured auditing
logging.basicConfig(level=logging.INFO, format="%(message)s")

app = FastAPI(title="AI API Gateway (Security Shield)")

# Initialize Rate Limiter backend
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
rate_limiter = RedisRateLimiter(REDIS_URL)

# Initialize Payload Inspector
payload_inspector = PayloadInspector()

# HTTPX client for routing requests to internal AI backend
AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://ai-application-server:5001")
http_client = httpx.AsyncClient(base_url=AI_SERVER_URL)

class InferenceRequest(BaseModel):
    prompt: str

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()

@app.post("/api/v1/auth/token")
def get_token(role: str = "guest"):
    """
    Demo endpoint to generate a JWT token for a specific role (admin, employee, guest).
    """
    try:
        token = create_access_token(role)
        return {"access_token": token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/inference")
async def inference(
    request: Request,
    payload: InferenceRequest,
    claims: dict = Depends(get_current_user_claims)
):
    start_time = time.time()
    role = claims["role"]
    
    # Retrieve real client IP passed by Nginx, or fall back to direct request host
    client_ip = request.headers.get("x-real-ip", request.client.host if request.client else "unknown")
    client_id = f"{role}:{client_ip}"
    
    # 1. Dynamic Rate Limiting check (Admin Bypass)
    rate_limit_bypassed = False
    if role == "admin":
        rate_limit_bypassed = True
    else:
        policy = get_rate_limiter_policy(role)
        if not rate_limiter.is_allowed(client_id, policy["limit"], policy["window"]):
            latency_ms = (time.time() - start_time) * 1000
            log_audit_event(
                client_ip, 
                role, 
                429, 
                latency_ms, 
                "BLOCKED", 
                f"Rate limit exceeded (Max: {policy['limit']}/{policy['window']}s)"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for role '{role}'. Allowed: {policy['limit']}/{policy['window']}s"
            )

    # 2. Payload Heuristics Inspection check (Always active, even for admin)
    risk_score, reasons = payload_inspector.inspect(client_id, payload.prompt)
    if risk_score >= payload_inspector.risk_threshold:
        latency_ms = (time.time() - start_time) * 1000
        log_audit_event(
            client_ip, 
            role, 
            400, 
            latency_ms, 
            "BLOCKED", 
            f"Payload inspection failed (Score: {risk_score:.2f}, Reasons: {', '.join(reasons)})"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security alert: Prompt rejected. Reasons: {', '.join(reasons)}"
        )

    # 3. Request Forwarding to internal AI Application Server
    try:
        response = await http_client.post("/inference", json={"text": payload.prompt}, timeout=30.0)
        latency_ms = (time.time() - start_time) * 1000
        
        detail = "admin bypass - rate limiting not applied" if rate_limit_bypassed else ""
        log_audit_event(client_ip, role, response.status_code, latency_ms, "ALLOWED", detail)
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers={"Content-Type": "application/json"}
        )
    except httpx.HTTPError as e:
        latency_ms = (time.time() - start_time) * 1000
        log_audit_event(client_ip, role, 502, latency_ms, "FAILED", f"Error communicating with AI backend: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error forwarding request to the AI application server."
        )
