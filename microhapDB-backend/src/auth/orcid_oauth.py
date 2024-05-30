# src/auth/orcid_oauth.py

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from .models import User, get_session, get_sync_session
from .utils import create_access_token, verify_access_token
import logging

logging.basicConfig(level=logging.INFO)

ORCID_CLIENT_ID = "APP-59Y81DPMGGM8ETSL"
ORCID_CLIENT_SECRET = "7f8876ff-57ad-4021-a3ce-14dfc367d181"
ORCID_REDIRECT_URI = "https://myfastapiapp.loca.lt/auth/callback"
ORCID_AUTH_URL = "https://orcid.org/oauth/authorize"
ORCID_TOKEN_URL = "https://orcid.org/oauth/token"

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=ORCID_AUTH_URL,
    tokenUrl=ORCID_TOKEN_URL,
)

async def get_orcid_token(code: str):
    logging.info(f"Exchanging code {code} for token")
    async with httpx.AsyncClient() as client:
        response = await client.post(ORCID_TOKEN_URL, data={
            'client_id': ORCID_CLIENT_ID,
            'client_secret': ORCID_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': ORCID_REDIRECT_URI,
        })
        logging.info(f"ORCID token response status: {response.status_code}")
        response.raise_for_status()
        return response.json()

async def get_orcid_user_info(access_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get('https://orcid.org/oauth/userinfo', headers={
            'Authorization': f'Bearer {access_token}',
        })
        response.raise_for_status()
        return response.json()


def get_user_sync(orcid: str, sync_session: Session):
    return sync_session.query(User).filter(User.orcid == orcid).one_or_none()

async def get_current_user(request: Request, db: AsyncSession = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        # If token is not found in headers, try cookies
        if not token:
            token = request.cookies.get("access_token")
        if token is None:
            raise credentials_exception
        logging.info("Checkpoint_1")
        logging.info(token)
        payload = verify_access_token(token)
        if payload is None:
            raise credentials_exception
        logging.info("Checkpoint_2")
        orcid = payload.get("sub")
        if orcid is None:
            raise credentials_exception
        logging.info("Checkpoint_3")

        # Use synchronous session to query the user
        sync_session = next(get_sync_session())
        user = get_user_sync(orcid, sync_session)
        sync_session.close()

        logging.info("Checkpoint_4")
        if user is None:
            raise credentials_exception
        return user
    except Exception as e:
        logging.error(f"Error fetching user info: {e}")
        raise credentials_exception