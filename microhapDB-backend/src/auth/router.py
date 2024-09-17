# src/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from .orcid_oauth import get_orcid_token, get_orcid_user_info, ORCID_CLIENT_ID, ORCID_REDIRECT_URI, ORCID_AUTH_URL, get_current_user
from .models import get_session, User, AdminOrcid, UserToken
from .utils import create_access_token, verify_access_token
from sqlalchemy.future import select
import logging

router = APIRouter()

@router.get("/login")
async def login_with_orcid():
    return RedirectResponse(f"{ORCID_AUTH_URL}?client_id={ORCID_CLIENT_ID}&response_type=code&scope=/authenticate&redirect_uri={ORCID_REDIRECT_URI}")


@router.get("/callback")
async def orcid_callback(code: str, response: Response, db: AsyncSession = Depends(get_session)):
    logging.info(f"Received code: {code}")
    try:
        # Fetch ORCID token data
        token_data = await get_orcid_token(code)
        logging.info(f"Token data: {token_data}")

        if 'access_token' not in token_data:
            logging.error("Access token missing in token data")
            raise HTTPException(status_code=400, detail="Access token missing in token data")

        # Fetch user info using ORCID access token
        user_info = await get_orcid_user_info(token_data['access_token'])
        logging.info(f"User info: {user_info}")

        # Combine given_name and family_name to create the full name
        full_name = f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip()

        # Check if the user already exists in the database
        result = await db.execute(select(User).filter(User.orcid == user_info['sub']))
        user = result.scalar_one_or_none()

        # Check for admin status via the AdminOrcid table
        result = await db.execute(select(AdminOrcid).filter(AdminOrcid.orcid == user_info['sub']))
        admin_orcid = result.scalar_one_or_none()

        if user is None:
            # If user doesn't exist, create a new user
            user = User(
                full_name=full_name if full_name else 'Unknown User',
                orcid=user_info['sub'],
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Handle token storage in UserToken table
        token_result = await db.execute(select(UserToken).filter(UserToken.user_id == user.id))
        user_token = token_result.scalar_one_or_none()

        if user_token is None:
            # Create a new token if none exists for the user
            user_token = UserToken(
                user_id=user.id,
                access_token=token_data['access_token'],
                token_type=token_data['token_type'],
                refresh_token=token_data['refresh_token'],
                expires_in=token_data['expires_in'],
                scope=token_data['scope']
            )
            db.add(user_token)
        else:
            # Update token if it already exists
            user_token.access_token = token_data['access_token']
            user_token.token_type = token_data['token_type']
            user_token.refresh_token = token_data['refresh_token']
            user_token.expires_in = token_data['expires_in']
            user_token.scope = token_data['scope']

        await db.commit()

        # Create access token for frontend authentication
        access_token = create_access_token(data={"sub": user.orcid})
        redirect_response = RedirectResponse(url="https://microhapdb.loca.lt")
        redirect_response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="None")
        return redirect_response

    except HTTPException as e:
        logging.error(f"HTTPException: {e.detail}")
        raise
    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        raise HTTPException(status_code=400, detail="An error occurred during the ORCID callback")

@router.get("/status")
async def auth_status(request: Request, db: AsyncSession = Depends(get_session)):
    token = request.cookies.get("access_token")
    logging.info(f"Token: {token}")
    if not token:
        raise HTTPException(status_code=401, detail="Token not found")

    payload = verify_access_token(token)
    logging.info(f"Payload: {payload}")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    orcid = payload.get("sub")
    logging.info(f"Orcid: {orcid}")
    if not orcid:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(User).filter(User.orcid == orcid))
    user = result.scalar_one_or_none()
    logging.info(f"User: {user}")
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # admin_orcid = await db.execute(select(AdminOrcid).filter(AdminOrcid.orcid == orcid))
    # admin_orcid_record = admin_orcid.scalar_one_or_none()
    #
    # is_admin = admin_orcid_record.is_admin if admin_orcid_record else False
    admin_orcid = await db.execute(select(AdminOrcid).filter(AdminOrcid.orcid == orcid))
    admin_orcid_record = admin_orcid.scalar_one_or_none()
    is_admin = admin_orcid_record is not None  # Check if an AdminOrcid record exists


    return {
        "is_authenticated": True,
        "is_admin": is_admin,
        "full_name": user.full_name,
    }


@router.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/admin", response_model=dict)
async def read_admin_data(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return {"message": "Hello, Admin!"}

# response = RedirectResponse(url="http://localhost:8080")