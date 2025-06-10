# src/auth/utils.py

from jose import JWTError, jwt
from datetime import datetime, timedelta
import logging
import os
import secrets
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

# Get secret key from environment variable or generate a secure one
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    logging.warning("JWT_SECRET_KEY not set in environment variables. Generating a new key for this session.")
    SECRET_KEY = secrets.token_urlsafe(64)  # Generate secure random key
    logging.warning(f"Generated secret key: {SECRET_KEY[:16]}... (store this in your environment variables)")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 30

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the provided data.
    
    Args:
        data: Dictionary containing the claims to encode
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logging.info(f"Created access token for user: {data.get('sub', 'unknown')}")
        return encoded_jwt
    except Exception as e:
        logging.error(f"Error creating access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token"
        )

def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with the provided data.
    
    Args:
        data: Dictionary containing the claims to encode
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logging.info(f"Created refresh token for user: {data.get('sub', 'unknown')}")
        return encoded_jwt
    except Exception as e:
        logging.error(f"Error creating refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create refresh token"
        )

def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT access token.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != "access":
            logging.warning(f"Invalid token type: {payload.get('type')}")
            return {"error": "Invalid token type"}
        
        # Check if token is expired
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            logging.warning("Token has expired")
            return {"error": "Token has expired"}
            
        logging.debug(f"Successfully verified token for user: {payload.get('sub')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        logging.warning("Token signature has expired")
        return {"error": "Token has expired"}
    except jwt.JWTClaimsError as e:
        logging.warning(f"JWT claims error: {e}")
        return {"error": "Invalid token claims"}
    except jwt.JWTError as e:
        logging.warning(f"JWT verification error: {e}")
        return {"error": "Could not validate token"}
    except Exception as e:
        logging.error(f"Unexpected error verifying token: {e}")
        return {"error": "Token verification failed"}

def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT refresh token.
    
    Args:
        token: JWT refresh token string to verify
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != "refresh":
            logging.warning(f"Invalid refresh token type: {payload.get('type')}")
            return None
        
        logging.debug(f"Successfully verified refresh token for user: {payload.get('sub')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        logging.warning("Refresh token has expired")
        return None
    except jwt.JWTError as e:
        logging.warning(f"Refresh token verification error: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error verifying refresh token: {e}")
        return None

def extract_token_from_header(authorization: str) -> Optional[str]:
    """
    Extract Bearer token from Authorization header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Token string or None if invalid format
    """
    if not authorization:
        return None
        
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            return None
        return token
    except ValueError:
        return None

def get_token_exp_time(token: str) -> Optional[datetime]:
    """
    Get the expiration time of a token without verifying it.
    
    Args:
        token: JWT token string
        
    Returns:
        Expiration datetime or None if invalid
    """
    try:
        # Decode without verification to get expiration
        unverified_payload = jwt.get_unverified_claims(token)
        exp_timestamp = unverified_payload.get("exp")
        
        if exp_timestamp:
            return datetime.utcfromtimestamp(exp_timestamp)
        return None
    except Exception as e:
        logging.warning(f"Could not extract expiration from token: {e}")
        return None
