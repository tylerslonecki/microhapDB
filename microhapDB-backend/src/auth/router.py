# src/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from .orcid_oauth import get_orcid_token, get_orcid_user_info, ORCID_CLIENT_ID, ORCID_REDIRECT_URI, ORCID_AUTH_URL, get_current_user
from .models import get_session, User
from .utils import create_access_token
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
        token_data = await get_orcid_token(code)
        logging.info(f"Token data: {token_data}")

        if 'access_token' not in token_data:
            logging.error("Access token missing in token data")
            raise HTTPException(status_code=400, detail="Access token missing in token data")

        user_info = await get_orcid_user_info(token_data['access_token'])
        logging.info(f"User info: {user_info}")

        result = await db.execute(select(User).filter(User.orcid == user_info['sub']))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                full_name=user_info.get('name', 'Unknown User'),
                orcid=user_info['sub'],
                is_active=True,
                is_admin=False,  # Default to non-admin; update logic as needed
                access_token=token_data['access_token'],
                token_type=token_data['token_type'],
                refresh_token=token_data['refresh_token'],
                expires_in=token_data['expires_in'],
                scope=token_data['scope']
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        access_token = create_access_token(data={"sub": user.orcid})
        redirect_response = RedirectResponse(url="https://microhapdb.loca.lt")  # Redirect to the frontend home page
        redirect_response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="None")
        return redirect_response

    except HTTPException as e:
        logging.error(f"HTTPException: {e.detail}")
        raise
    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        raise HTTPException(status_code=400, detail="An error occurred during the ORCID callback")


@router.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/admin", response_model=dict)
async def read_admin_data(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return {"message": "Hello, Admin!"}

# response = RedirectResponse(url="http://localhost:8080")