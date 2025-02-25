# src/utils.py

from jose import JWTError, jwt
from datetime import datetime, timedelta
import logging

SECRET_KEY = "your_secret_key"  # Ensure this matches the encoding key
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logging.info(f"Token payload: {payload}")
        return payload
    except JWTError as e:
        logging.error(f"JWTError: {e}")
        return None
