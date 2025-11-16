import os
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()

def require_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Dependency to require authentication.
    Validates JWT token and returns user data.
    """
    token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )
    
    try:
        # Verify JWT token
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret:
            raise HTTPException(
                status_code=500,
                detail="JWT_SECRET not configured"
            )
        
        decoded = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"]
        )
        
        # Return user data from token
        return {
            "userId": decoded.get("userId"),
            "correo": decoded.get("correo"),
            "nombre": decoded.get("nombre")
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
