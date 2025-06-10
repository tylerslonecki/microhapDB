# src/auth/orcid_oauth.py

import os
import logging
import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from .models import User, get_session
from .utils import create_access_token, verify_access_token

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get ORCID credentials from environment variables
ORCID_CLIENT_ID = os.getenv("ORCID_CLIENT_ID")
ORCID_CLIENT_SECRET = os.getenv("ORCID_CLIENT_SECRET")
ORCID_REDIRECT_URI = os.getenv("ORCID_REDIRECT_URI")
ORCID_AUTH_URL = os.getenv("ORCID_AUTH_URL", "https://sandbox.orcid.org/oauth/authorize")
ORCID_TOKEN_URL = os.getenv("ORCID_TOKEN_URL", "https://sandbox.orcid.org/oauth/token")
ORCID_API_URL = os.getenv("ORCID_API_URL", "https://sandbox.orcid.org/v3.0")

# Enhanced logging for debugging
logger.info(f"ORCID Environment Variables:")
logger.info(f"ORCID_CLIENT_ID: {ORCID_CLIENT_ID if ORCID_CLIENT_ID else 'NOT SET'}")
logger.info(f"ORCID_CLIENT_SECRET: {'*****' if ORCID_CLIENT_SECRET else 'NOT SET'}")
logger.info(f"ORCID_REDIRECT_URI: {ORCID_REDIRECT_URI if ORCID_REDIRECT_URI else 'NOT SET'}")
logger.info(f"ORCID_AUTH_URL: {ORCID_AUTH_URL}")
logger.info(f"ORCID_TOKEN_URL: {ORCID_TOKEN_URL}")
logger.info(f"ORCID_API_URL: {ORCID_API_URL}")

# Verify required environment variables
if not ORCID_CLIENT_ID or not ORCID_CLIENT_SECRET or not ORCID_REDIRECT_URI:
    logger.error("CRITICAL: Missing ORCID credentials in environment variables!")
    logger.error("Please check your .env file and ensure ORCID_CLIENT_ID, ORCID_CLIENT_SECRET, and ORCID_REDIRECT_URI are set.")

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{ORCID_AUTH_URL}?client_id={ORCID_CLIENT_ID}&response_type=code&scope=/authenticate&redirect_uri={ORCID_REDIRECT_URI}",
    tokenUrl=ORCID_TOKEN_URL,
)

async def get_orcid_token(code: str) -> dict:
    """
    Exchange authorization code for ORCID access token.
    """
    try:
        logger.info(f"Exchanging code for token at {ORCID_TOKEN_URL}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ORCID_TOKEN_URL,
                data={
                    'client_id': ORCID_CLIENT_ID,
                    'client_secret': ORCID_CLIENT_SECRET,
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': ORCID_REDIRECT_URI,
                    'scope': '/authenticate'
                },
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            
            logger.info(f"Token response status: {response.status_code}")
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"Token error: {error_text}")
                
                # Parse error response to provide better error messages
                try:
                    error_data = response.json()
                    error_type = error_data.get('error', 'unknown_error')
                    error_description = error_data.get('error_description', 'No description provided')
                    
                    if error_type == 'invalid_grant' and 'Reused authorization code' in error_description:
                        logger.error(f"Authorization code reuse detected: {error_description}")
                        raise HTTPException(
                            status_code=409, 
                            detail="Authorization code has already been used. This may be due to a duplicate request."
                        )
                    elif error_type == 'invalid_grant':
                        logger.error(f"Invalid authorization grant: {error_description}")
                        raise HTTPException(
                            status_code=400, 
                            detail="Invalid or expired authorization code. Please try logging in again."
                        )
                    else:
                        logger.error(f"ORCID OAuth error: {error_type} - {error_description}")
                        raise HTTPException(
                            status_code=response.status_code, 
                            detail=f"ORCID authentication failed: {error_description}"
                        )
                except ValueError:
                    # If we can't parse the JSON error response, fall back to generic error
                    logger.error(f"Could not parse ORCID error response: {error_text}")
                    raise HTTPException(
                        status_code=response.status_code, 
                        detail=f"ORCID token error: {error_text}"
                    )
            
            token_data = response.json()
            logger.info(f"Token obtained successfully. Type: {token_data.get('token_type')}")
            return token_data
    except httpx.RequestError as e:
        logger.error(f"Request error getting ORCID token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to ORCID: {str(e)}")
    except HTTPException:
        # Re-raise HTTPExceptions (our custom error handling above)
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting ORCID token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error during authentication: {str(e)}")

async def get_orcid_user_info(access_token: str, orcid_id: str = None, name: str = None) -> dict:
    """
    Fetch user information from ORCID API using the access token.
    If we only have /authenticate scope, we'll use the name from the token response.
    """
    try:
        if not orcid_id:
            logger.warning("No ORCID ID provided to get_orcid_user_info. Using access token as fallback.")
            parts = access_token.split('/')
            if len(parts) > 1:
                orcid_id = parts[1]
            else:
                orcid_id = parts[0]
        
        logger.info(f"Getting user info for ORCID ID: {orcid_id}")
        
        # If we have a name from the token response, use it directly
        # This is useful when we only have /authenticate scope
        if name:
            logger.info(f"Using name from token response: {name}")
            # Try to split the name into given_name and family_name
            name_parts = name.split(' ', 1)
            given_name = name_parts[0] if len(name_parts) > 0 else ''
            family_name = name_parts[1] if len(name_parts) > 1 else ''
            
            user_info = {
                'sub': orcid_id,
                'given_name': given_name,
                'family_name': family_name
            }
            
            logger.info(f"User info created from token data for {given_name} {family_name}")
            return user_info
        
        # Otherwise, try to get the info from the ORCID API
        # Use the public API endpoint format
        user_api_url = f"{ORCID_API_URL}/{orcid_id}/person"
        logger.info(f"User API URL: {user_api_url}")
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                user_api_url,
                headers={
                    'Accept': 'application/vnd.orcid+json',
                    'Authorization': f'Bearer {access_token}'
                }
            )
            
            logger.info(f"User info response status: {response.status_code}")
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"User info error: {error_text}")
                # If we can't get the user info from the API, create a basic user info object
                user_info = {
                    'sub': orcid_id,
                    'given_name': '',
                    'family_name': ''
                }
                logger.info(f"Created basic user info due to API error")
                return user_info
            
            try:
                user_data = response.json()
                logger.info(f"User data received: {user_data}")
                
                # Extract name from the response with more detailed logging
                name_data = user_data.get('name', {})
                logger.info(f"Name data: {name_data}")
                
                given_name = name_data.get('given-names', {}).get('value', '')
                family_name = name_data.get('family-name', {}).get('value', '')
                
                user_info = {
                    'sub': orcid_id,
                    'given_name': given_name,
                    'family_name': family_name
                }
                
                logger.info(f"User info retrieved successfully for {given_name} {family_name}")
                return user_info
            except ValueError as e:
                # If we can't parse the JSON, create a basic user info object
                logger.error(f"Error parsing user data JSON: {str(e)}")
                user_info = {
                    'sub': orcid_id,
                    'given_name': '',
                    'family_name': ''
                }
                logger.info(f"Created basic user info due to JSON parsing error")
                return user_info
    except httpx.RequestError as e:
        logger.error(f"Request error getting ORCID user info: {str(e)}")
        # If we can't connect to ORCID, create a basic user info object
        user_info = {
            'sub': orcid_id,
            'given_name': '',
            'family_name': ''
        }
        logger.info(f"Created basic user info due to connection error")
        return user_info
    except Exception as e:
        logger.error(f"Unexpected error getting ORCID user info: {str(e)}")
        # If there's any other error, create a basic user info object
        user_info = {
            'sub': orcid_id,
            'given_name': '',
            'family_name': ''
        }
        logger.info(f"Created basic user info due to unexpected error")
        return user_info


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
        payload = verify_access_token(token)
        if payload is None:
            raise credentials_exception
        orcid = payload.get("sub")
        if orcid is None:
            raise credentials_exception

        # Use async session to query the user
        stmt = select(User).filter(User.orcid == orcid)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception
        return user
    except Exception as e:
        logging.error(f"Error fetching user info: {e}")
        raise credentials_exception
