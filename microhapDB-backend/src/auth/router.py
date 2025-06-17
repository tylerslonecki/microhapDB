# src/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from .orcid_oauth import get_orcid_token, get_orcid_user_info, ORCID_CLIENT_ID, ORCID_REDIRECT_URI, ORCID_AUTH_URL
from .models import UserResponse
from src.models import User, AdminOrcid, UserToken, UserRoleEnum, Collaboration
from src.database import get_session, AsyncSessionLocal
from .utils import create_access_token, create_refresh_token, verify_access_token, verify_refresh_token, get_token_exp_time
from .dependencies import get_current_user, get_admin_user, get_token_from_request
from sqlalchemy.future import select
import logging
from typing import List, Set
import os
from urllib.parse import urlparse
import jwt
from datetime import datetime, timedelta
import time
import asyncio
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text

router = APIRouter()

# In-memory store for used authorization codes to prevent reuse
# In production, consider using Redis or database-backed storage
used_auth_codes: Set[str] = set()
code_lock = asyncio.Lock()  # Async lock for thread-safe access

async def is_code_used_or_mark_used(code: str) -> bool:
    """
    Check if an authorization code has been used, and mark it as used if not.
    Returns True if the code was already used, False if it's new (and now marked as used).
    """
    async with code_lock:
        if code in used_auth_codes:
            return True  # Code was already used
        
        # Add code to used set
        used_auth_codes.add(code)
        
        # Clean up old codes periodically (optional, to prevent memory bloat)
        # In a production environment, you'd want a more sophisticated cleanup mechanism
        if len(used_auth_codes) > 1000:  # Arbitrary limit
            # Remove roughly half of the codes (simple cleanup)
            codes_to_remove = list(used_auth_codes)[:500]
            for old_code in codes_to_remove:
                used_auth_codes.discard(old_code)
        
        return False  # Code is new and now marked as used

# src/auth/router.py
@router.get("/login")
async def login_with_orcid():
    """Initiate ORCID OAuth login flow."""
    login_url = (
        f"{ORCID_AUTH_URL}?client_id={ORCID_CLIENT_ID}"
        f"&response_type=code"
        f"&scope=/authenticate"
        f"&redirect_uri={ORCID_REDIRECT_URI}"
        f"&prompt=login"
    )
    return RedirectResponse(login_url)


@router.get("/callback")
async def orcid_callback(code: str, response: Response, db: AsyncSession = Depends(get_session)):
    """Handle ORCID OAuth callback and create user session."""
    logging.info(f"Received ORCID callback with code: {code[:10]}...")
    
    # Check if this authorization code has already been used
    if await is_code_used_or_mark_used(code):
        logging.warning(f"Authorization code {code[:10]}... has already been used")
        # Instead of raising an error, redirect to frontend with a message
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
        error_redirect_url = f"{frontend_url}/?error=duplicate_request"
        return RedirectResponse(url=error_redirect_url)
    
    try:
        # Fetch ORCID token data
        logging.info("Exchanging code for ORCID token...")
        token_data = await get_orcid_token(code)
        logging.info(f"Token data received: {list(token_data.keys())}")

        if 'access_token' not in token_data:
            logging.error("Access token missing in token data")
            raise HTTPException(status_code=400, detail="Access token missing in token data")

        # Get the ORCID ID from the token response
        orcid_id = token_data.get('orcid')
        if not orcid_id:
            logging.error("ORCID ID missing in token data")
            raise HTTPException(status_code=400, detail="ORCID ID missing in token data")

        # Fetch user info using ORCID access token and the correct ORCID ID
        logging.info("Getting ORCID user info...")
        user_info = await get_orcid_user_info(token_data['access_token'], orcid_id, token_data.get('name'))
        logging.info(f"User info retrieved for ORCID: {user_info['sub']}")

        # Combine given_name and family_name to create the full name
        full_name = f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip()
        if not full_name:
            full_name = 'Unknown User'

        # Check if the user already exists in the database
        result = await db.execute(select(User).filter(User.orcid == user_info['sub']))
        user = result.scalar_one_or_none()

        # Check for admin status via the AdminOrcid table
        admin_result = await db.execute(select(AdminOrcid).filter(AdminOrcid.orcid == user_info['sub']))
        admin_orcid = admin_result.scalar_one_or_none()
        
        # Determine the appropriate role
        user_role = UserRoleEnum.ADMIN.value if admin_orcid else UserRoleEnum.PUBLIC.value

        if user is None:
            # Create new user
            user = User(
                full_name=full_name,
                orcid=user_info['sub'],
                is_active=True,
                role=user_role
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logging.info(f"Created new user: {user.full_name} ({user.role})")
            
            # If the user is an admin, ensure they have an AdminOrcid entry
            if user.role == UserRoleEnum.ADMIN.value and not admin_orcid:
                admin_orcid = AdminOrcid(user_id=user.id, orcid=user_info['sub'])
                db.add(admin_orcid)
                await db.commit()
        else:
            # Update existing user
            user.full_name = full_name  # Update name in case it changed
            
            # Update admin role if needed
            if admin_orcid and user.role != UserRoleEnum.ADMIN.value:
                logging.info(f"Updating existing user {user.full_name} role to admin")
                user.role = UserRoleEnum.ADMIN.value
            elif user.role == UserRoleEnum.ADMIN.value and not admin_orcid:
                logging.info(f"Creating AdminOrcid entry for existing admin user {user.full_name}")
                admin_orcid = AdminOrcid(user_id=user.id, orcid=user_info['sub'])
                db.add(admin_orcid)
            
            await db.commit()
            await db.refresh(user)

        # Handle token storage in UserToken table
        token_result = await db.execute(select(UserToken).filter(UserToken.user_id == user.id))
        user_token = token_result.scalar_one_or_none()

        if user_token is None:
            # Create a new token record
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
            # Update existing token record
            user_token.access_token = token_data['access_token']
            user_token.token_type = token_data['token_type']
            user_token.refresh_token = token_data['refresh_token']
            user_token.expires_in = token_data['expires_in']
            user_token.scope = token_data['scope']

        await db.commit()

        # Create JWT access and refresh tokens for frontend authentication
        access_token = create_access_token(
            data={"sub": user.orcid, "role": user.role},
            expires_delta=timedelta(hours=24)
        )
        
        refresh_token = create_refresh_token(
            data={"sub": user.orcid}
        )

        # Get frontend URL from environment or use default
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
        
        # Redirect to frontend with token
        redirect_url = f"{frontend_url}/?token={access_token}"
        
        # Create redirect response
        redirect_response = RedirectResponse(url=redirect_url)
        
        # Set secure cookies for tokens
        is_production = os.getenv("ENVIRONMENT") == "production"
        
        # Set access token cookie
        redirect_response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=is_production,  # Only secure in production (HTTPS)
            samesite="lax",
            max_age=86400  # 24 hours
        )
        
        # Set refresh token cookie (longer expiration, more secure)
        redirect_response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=is_production,
            samesite="lax",
            max_age=2592000  # 30 days
        )

        logging.info(f"User {user.full_name} successfully authenticated")
        return redirect_response

    except Exception as e:
        logging.error(f"Error in ORCID callback: {str(e)}", exc_info=True)
        # Redirect to frontend home page with error
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
        error_redirect_url = f"{frontend_url}/?error={str(e)}"
        return RedirectResponse(url=error_redirect_url)

@router.get("/status")
async def auth_status(current_user: User = Depends(get_current_user)):
    """
    Get the current user's authentication status and role information.
    Requires valid authentication.
    """
    try:
        # Since we're using get_current_user dependency, we know the user is authenticated
        return {
            "is_authenticated": True,
            "is_admin": current_user.is_admin,
            "username": current_user.full_name,
            "role": current_user.role
        }
    except Exception as e:
        logging.error(f"Unexpected error in auth_status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/check")
async def check_auth_status(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Check authentication status without requiring authentication.
    Returns authentication status and user info if authenticated, or unauthenticated status if not.
    This endpoint is used by the frontend to determine login state.
    """
    try:
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        if not token:
            token = request.cookies.get("access_token")
        if not token:
            return {
                "is_authenticated": False,
                "message": "No token found"
            }

        payload = verify_access_token(token)
        
        # Check if payload contains an error
        if payload is None or (isinstance(payload, dict) and "error" in payload):
            error_message = "Invalid token"
            if isinstance(payload, dict) and "error" in payload:
                error_message = payload["error"]
            
            return {
                "is_authenticated": False,
                "message": error_message
            }

        orcid = payload.get("sub")
        if not orcid:
            logging.info("No ORCID found in token payload")
            return {
                "is_authenticated": False,
                "message": "Invalid token payload"
            }

        logging.info(f"Looking up user with ORCID: {orcid}")
        # First check if the ORCID is in the admin_orcids table
        admin_result = await db.execute(select(AdminOrcid).filter(AdminOrcid.orcid == orcid))
        is_admin_orcid = admin_result.scalar_one_or_none() is not None
        
        # Then get the user
        user_result = await db.execute(select(User).filter(User.orcid == orcid))
        user = user_result.scalar_one_or_none()
        
        if not user:
            logging.info(f"No user found for ORCID {orcid}")
            return {
                "is_authenticated": False,
                "message": "User not found"
            }

        # If the user is in admin_orcids but their role isn't admin, update it
        if is_admin_orcid and user.role != UserRoleEnum.ADMIN.value:
            user.role = UserRoleEnum.ADMIN.value
            await db.commit()
            logging.info(f"Updated user {user.full_name} to admin role")

        logging.info(f"User found: {user.full_name}, admin: {is_admin_orcid}, role: {user.role}")
        return {
            "is_authenticated": True,
            "is_admin": is_admin_orcid,
            "username": user.full_name,
            "role": user.role
        }

    except Exception as e:
        logging.error(f"Unexpected error in check_auth_status: {str(e)}", exc_info=True)
        return {
            "is_authenticated": False,
            "message": f"Internal server error: {str(e)}"
        }

@router.post("/refresh")
async def refresh_token(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Refresh an expired access token using a valid refresh token.
    """
    try:
        # Try to get refresh token from cookies first, then from body
        refresh_token_value = request.cookies.get("refresh_token")
        
        if not refresh_token_value:
            # Try to get from request body as fallback
            body = await request.json()
            refresh_token_value = body.get("refresh_token")
        
        if not refresh_token_value:
            logging.warning("No refresh token provided in refresh request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token required"
            )
        
        # Verify the refresh token
        payload = verify_refresh_token(refresh_token_value)
        if not payload:
            logging.warning("Invalid refresh token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        orcid = payload.get("sub")
        if not orcid:
            logging.warning("No ORCID found in refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload"
            )
        
        # Find the user by ORCID
        user_result = await db.execute(select(User).filter(User.orcid == orcid))
        user = user_result.scalar_one_or_none()
        
        if not user:
            logging.warning(f"User not found for ORCID in refresh token: {orcid}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Check if user is still active
        if not user.is_active:
            logging.warning(f"Inactive user attempted token refresh: {user.full_name}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Create new access token with current user role
        new_access_token = create_access_token(
            data={"sub": user.orcid, "role": user.role},
            expires_delta=timedelta(hours=24)
        )
        
        # Optionally create new refresh token for rotation
        new_refresh_token = create_refresh_token(
            data={"sub": user.orcid}
        )
        
        logging.info(f"Token refreshed successfully for user: {user.full_name}")
        
        # Return new tokens
        response_data = {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": 86400  # 24 hours
        }
        
        response = JSONResponse(content=response_data)
        
        # Update cookies with new tokens
        is_production = os.getenv("ENVIRONMENT") == "production"
        
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=is_production,
            samesite="lax",
            max_age=86400  # 24 hours
        )
        
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=is_production,
            samesite="lax",
            max_age=2592000  # 30 days
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error refreshing token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Logout user and invalidate tokens.
    """
    try:
        # Get current user if possible (for logging)
        user = None
        try:
            token = await get_token_from_request(request)
            if token:
                payload = verify_access_token(token)
                if payload and not isinstance(payload, dict) or "error" not in payload:
                    orcid = payload.get("sub")
                    if orcid:
                        user_result = await db.execute(select(User).filter(User.orcid == orcid))
                        user = user_result.scalar_one_or_none()
        except Exception:
            pass  # Ignore errors during user lookup
        
        # Create response
        response = JSONResponse(content={"message": "Logged out successfully"})
        
        # Clear authentication cookies
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/")
        
        # Log successful logout
        if user:
            logging.info(f"User {user.full_name} logged out successfully")
        else:
            logging.info("Anonymous user logged out")
        
        return response
        
    except Exception as e:
        logging.error(f"Error during logout: {e}")
        # Still return success to prevent client-side errors
        response = JSONResponse(content={"message": "Logged out successfully"})
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/")
        return response



@router.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/admin", response_model=dict)
async def read_admin_data(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return {"message": "Hello, Admin!"}

# Admin endpoints for user management
@router.get("/admin/users", response_model=List[UserResponse])
async def list_users(current_user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

@router.put("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: UserRoleEnum,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.role = role
        await session.commit()
        return {"message": f"User role updated to {role.value}"}

@router.post("/admin/users/{user_id}/collaborator/{collaborator_id}")
async def add_collaborator(
    user_id: int,
    collaborator_id: int,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    async with AsyncSessionLocal() as session:
        # Verify both users exist
        user_result = await session.execute(select(User).filter(User.id == user_id))
        collaborator_result = await session.execute(select(User).filter(User.id == collaborator_id))
        
        user = user_result.scalar_one_or_none()
        collaborator = collaborator_result.scalar_one_or_none()
        
        if not user or not collaborator:
            raise HTTPException(status_code=404, detail="User or collaborator not found")
        
        # Create collaboration
        collaboration = Collaboration(
            user_id=user_id,
            collaborator_id=collaborator_id
        )
        session.add(collaboration)
        await session.commit()
        
        return {"message": "Collaborator added successfully"}

@router.delete("/admin/users/{user_id}/collaborator/{collaborator_id}")
async def remove_collaborator(
    user_id: int,
    collaborator_id: int,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Collaboration).filter(
                Collaboration.user_id == user_id,
                Collaboration.collaborator_id == collaborator_id
            )
        )
        collaboration = result.scalar_one_or_none()
        
        if not collaboration:
            raise HTTPException(status_code=404, detail="Collaboration not found")
        
        await session.delete(collaboration)
        await session.commit()
        
        return {"message": "Collaborator removed successfully"}

@router.get("/admin/users/{user_id}/collaborators", response_model=List[UserResponse])
async def get_user_collaborators(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    async with AsyncSessionLocal() as session:
        # Get all collaborator IDs for this user
        result = await session.execute(
            select(Collaboration.collaborator_id).filter(
                Collaboration.user_id == user_id
            )
        )
        collaborator_ids = result.scalars().all()
        
        if not collaborator_ids:
            return []
        
        # Get all collaborator user objects
        result = await session.execute(
            select(User).filter(
                User.id.in_(collaborator_ids)
            )
        )
        collaborators = result.scalars().all()
        
        return collaborators

@router.get("/users/me/collaborators", response_model=List[UserResponse])
async def get_my_collaborators(current_user: User = Depends(get_current_user)):
    """
    Get a list of the current user's collaborators.
    """
    async with AsyncSessionLocal() as session:
        # Get all collaborator IDs for the current user
        result = await session.execute(
            select(Collaboration.collaborator_id).filter(
                Collaboration.user_id == current_user.id
            )
        )
        collaborator_ids = result.scalars().all()
        
        if not collaborator_ids:
            return []
        
        # Get all collaborator user objects
        result = await session.execute(
            select(User).filter(
                User.id.in_(collaborator_ids)
            )
        )
        collaborators = result.scalars().all()
        
        return collaborators

@router.post("/users/me/collaborators/{collaborator_id}")
async def add_my_collaborator(
    collaborator_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Add a collaborator for the current user.
    Private users can add collaborators directly.
    """
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.PRIVATE_USER]:
        raise HTTPException(
            status_code=403,
            detail="Only admins and private users can add collaborators"
        )
    
    if collaborator_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot add yourself as a collaborator"
        )
    
    async with AsyncSessionLocal() as session:
        # Verify the collaborator exists
        result = await session.execute(
            select(User).filter(User.id == collaborator_id)
        )
        collaborator = result.scalar_one_or_none()
        
        if not collaborator:
            raise HTTPException(
                status_code=404,
                detail="Collaborator not found"
            )
        
        # Check if the collaboration already exists
        result = await session.execute(
            select(Collaboration).filter(
                Collaboration.user_id == current_user.id,
                Collaboration.collaborator_id == collaborator_id
            )
        )
        existing_collaboration = result.scalar_one_or_none()
        
        if existing_collaboration:
            return {"message": "Collaboration already exists"}
        
        # Create the collaboration
        collaboration = Collaboration(
            user_id=current_user.id,
            collaborator_id=collaborator_id
        )
        session.add(collaboration)
        await session.commit()
        
        return {"message": "Collaborator added successfully"}

@router.delete("/users/me/collaborators/{collaborator_id}")
async def remove_my_collaborator(
    collaborator_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Remove a collaborator for the current user.
    """
    async with AsyncSessionLocal() as session:
        # Check if the collaboration exists
        result = await session.execute(
            select(Collaboration).filter(
                Collaboration.user_id == current_user.id,
                Collaboration.collaborator_id == collaborator_id
            )
        )
        collaboration = result.scalar_one_or_none()
        
        if not collaboration:
            raise HTTPException(
                status_code=404,
                detail="Collaboration not found"
            )
        
        # Delete the collaboration
        await session.delete(collaboration)
        await session.commit()
        
        return {"message": "Collaborator removed successfully"}

@router.get("/users", response_model=List[UserResponse])
async def list_all_users(current_user: User = Depends(get_current_user)):
    """
    List all users in the system (for collaboration management).
    This endpoint is available to all authenticated users.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        return users

@router.post("/admin/orcids", response_model=dict)
async def add_admin_orcid(
    orcid: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new admin ORCID. Only existing admins can add new admins.
    """
    # Check if current user is an admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can add new admin ORCIDs")
    
    # Check if the ORCID is already an admin
    result = await db.execute(select(AdminOrcid).filter(AdminOrcid.orcid == orcid))
    existing_admin = result.scalar_one_or_none()
    if existing_admin:
        return {"message": f"ORCID {orcid} is already an admin"}
    
    # Check if the user exists
    result = await db.execute(select(User).filter(User.orcid == orcid))
    user = result.scalar_one_or_none()
    
    # Create a new AdminOrcid entry
    new_admin_orcid = AdminOrcid(orcid=orcid)
    if user:
        # If user exists, link them and update their role
        new_admin_orcid.user_id = user.id
        user.role = UserRoleEnum.ADMIN.value
    
    db.add(new_admin_orcid)
    await db.commit()
    
    return {"message": f"ORCID {orcid} has been added as an admin"}


@router.get("/admin/orcids", response_model=List[str])
async def list_admin_orcids(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    List all admin ORCIDs. Only admins can view this list.
    """
    # Check if current user is an admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can view admin ORCIDs")
    
    # Get all admin ORCIDs
    result = await db.execute(select(AdminOrcid))
    admin_orcids = result.scalars().all()
    
    return [admin.orcid for admin in admin_orcids]


@router.delete("/admin/orcids/{orcid}", response_model=dict)
async def remove_admin_orcid(
    orcid: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Remove an admin ORCID. Only admins can remove admin ORCIDs.
    Cannot remove your own admin status.
    """
    # Check if current user is an admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can remove admin ORCIDs")
    
    # Cannot remove your own admin status
    if current_user.orcid == orcid:
        raise HTTPException(status_code=400, detail="Cannot remove your own admin status")
    
    # Find the admin ORCID entry
    result = await db.execute(select(AdminOrcid).filter(AdminOrcid.orcid == orcid))
    admin_orcid = result.scalar_one_or_none()
    
    if not admin_orcid:
        raise HTTPException(status_code=404, detail=f"ORCID {orcid} is not an admin")
    
    # Find the user and update their role if they exist
    result = await db.execute(select(User).filter(User.orcid == orcid))
    user = result.scalar_one_or_none()
    if user and user.role == UserRoleEnum.ADMIN.value:
        user.role = UserRoleEnum.PUBLIC.value  # Demote to public user
    
    # Remove the admin ORCID entry
    await db.delete(admin_orcid)
    await db.commit()
    
    return {"message": f"ORCID {orcid} has been removed as an admin"}

class CreateUserRequest(BaseModel):
    full_name: str
    orcid: str
    role: UserRoleEnum = UserRoleEnum.PUBLIC
    is_active: bool = True

@router.post("/admin/users", response_model=UserResponse)
async def create_user_directly(
    user_data: CreateUserRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Create a new user directly without requiring ORCID authentication.
    Only admins can create users this way.
    """
    
    # Validate ORCID format
    import re
    orcid_pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
    if not re.match(orcid_pattern, user_data.orcid):
        raise HTTPException(
            status_code=400,
            detail="Invalid ORCID format. Use: 0000-0000-0000-0000"
        )
    
    # Check if user with this ORCID already exists
    result = await db.execute(select(User).filter(User.orcid == user_data.orcid))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail=f"User with ORCID {user_data.orcid} already exists"
        )
    
    try:
        # Create new user
        new_user = User(
            full_name=user_data.full_name,
            orcid=user_data.orcid,
            is_active=user_data.is_active,
            role=user_data.role.value
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        # If the user is an admin, ensure they have an AdminOrcid entry
        if new_user.role == UserRoleEnum.ADMIN.value:
            admin_orcid = AdminOrcid(user_id=new_user.id, orcid=user_data.orcid)
            db.add(admin_orcid)
            await db.commit()
        
        logging.info(f"Admin {current_user.full_name} created new user: {new_user.full_name} ({new_user.role})")
        
        return new_user
        
    except Exception as e:
        await db.rollback()
        logging.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )

class BulkCreateUsersRequest(BaseModel):
    data: str  # CSV data as string

class BulkUserResult(BaseModel):
    name: str
    orcid: str
    success: bool
    message: str

@router.post("/admin/users/bulk", response_model=List[BulkUserResult])
async def bulk_create_users(
    request: BulkCreateUsersRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Bulk create users from CSV data.
    Format: Full Name, ORCID, Role
    """
    import re
    import csv
    from io import StringIO
    
    results = []
    orcid_pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
    valid_roles = [role.value for role in UserRoleEnum]
    
    try:
        # Parse CSV data
        csv_data = StringIO(request.data)
        reader = csv.reader(csv_data)
        
        for line_num, row in enumerate(reader, 1):
            if len(row) < 3:
                results.append(BulkUserResult(
                    name=f"Line {line_num}",
                    orcid="N/A",
                    success=False,
                    message="Invalid CSV format. Expected: Full Name, ORCID, Role"
                ))
                continue
            
            full_name = row[0].strip()
            orcid = row[1].strip()
            role = row[2].strip().lower()
            
            # Validate data
            if not full_name:
                results.append(BulkUserResult(
                    name=f"Line {line_num}",
                    orcid=orcid,
                    success=False,
                    message="Full name is required"
                ))
                continue
            
            if not re.match(orcid_pattern, orcid):
                results.append(BulkUserResult(
                    name=full_name,
                    orcid=orcid,
                    success=False,
                    message="Invalid ORCID format"
                ))
                continue
            
            if role not in valid_roles:
                results.append(BulkUserResult(
                    name=full_name,
                    orcid=orcid,
                    success=False,
                    message=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
                ))
                continue
            
            # Check if user already exists
            result = await db.execute(select(User).filter(User.orcid == orcid))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                results.append(BulkUserResult(
                    name=full_name,
                    orcid=orcid,
                    success=False,
                    message="User with this ORCID already exists"
                ))
                continue
            
            # Create user
            try:
                new_user = User(
                    full_name=full_name,
                    orcid=orcid,
                    is_active=True,
                    role=role
                )
                
                db.add(new_user)
                await db.commit()
                await db.refresh(new_user)
                
                # If admin, add to AdminOrcid table
                if role == UserRoleEnum.ADMIN.value:
                    admin_orcid = AdminOrcid(user_id=new_user.id, orcid=orcid)
                    db.add(admin_orcid)
                    await db.commit()
                
                results.append(BulkUserResult(
                    name=full_name,
                    orcid=orcid,
                    success=True,
                    message=f"User created with role: {role}"
                ))
                
                logging.info(f"Admin {current_user.full_name} bulk created user: {full_name} ({role})")
                
            except Exception as e:
                await db.rollback()
                results.append(BulkUserResult(
                    name=full_name,
                    orcid=orcid,
                    success=False,
                    message=f"Database error: {str(e)}"
                ))
                logging.error(f"Error creating user {full_name}: {str(e)}")
    
    except Exception as e:
        logging.error(f"Error parsing bulk user data: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Invalid CSV data format"
        )
    
    return results

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Delete a user and all associated data.
    Only admins can delete users.
    """
    
    # Check if user exists
    result = await db.execute(select(User).filter(User.id == user_id))
    user_to_delete = result.scalar_one_or_none()
    
    if not user_to_delete:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if user_to_delete.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )
    
    try:
        # Delete associated records first (due to foreign key constraints)
        
        # Delete user tokens
        await db.execute(
            text("DELETE FROM user_tokens WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        
        # Delete collaborations where this user is involved
        await db.execute(
            text("DELETE FROM collaborations WHERE user_id = :user_id OR collaborator_id = :user_id"),
            {"user_id": user_id}
        )
        
        # Delete admin orcid record if exists
        await db.execute(
            text("DELETE FROM admin_orcids WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        
        # Delete database versions uploaded by this user
        await db.execute(
            text("UPDATE database_versions SET uploaded_by = NULL WHERE uploaded_by = :user_id"),
            {"user_id": user_id}
        )
        
        # Delete file uploads by this user  
        await db.execute(
            text("UPDATE file_uploads SET uploaded_by = NULL WHERE uploaded_by = :user_id"),
            {"user_id": user_id}
        )
        
        # Finally delete the user
        await db.delete(user_to_delete)
        await db.commit()
        
        logging.info(f"Admin {current_user.full_name} deleted user: {user_to_delete.full_name} ({user_to_delete.orcid})")
        
        return {"message": f"User {user_to_delete.full_name} has been successfully deleted"}
        
    except Exception as e:
        await db.rollback()
        logging.error(f"Error deleting user {user_to_delete.full_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete user"
        )

# response = RedirectResponse(url="http://localhost:8080")