import os
import time
import jwt
from typing import Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_dev_key_change_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

security_scheme = HTTPBearer()

def create_access_token(role: str, expires_in: int = 3600) -> str:
    """
    Creates a JWT token with a specified role claim.
    """
    if role not in ["admin", "employee", "guest"]:
        raise ValueError("Invalid role. Role must be admin, employee, or guest.")
    
    payload = {
        "role": role,
        "exp": time.time() + expires_in,
        "iat": time.time()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user_claims(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and validate claims from the JWT.
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        role = payload.get("role")
        if not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing required 'role' claim."
            )
        if role not in ["admin", "employee", "guest"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid role in token claim."
            )
        return {"role": role, "token": token}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired."
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
