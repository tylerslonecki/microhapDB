# src/auth/dependencies.py

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional
import logging

from .models import User, get_session, AdminOrcid
from .utils import verify_access_token, extract_token_from_header
from src.models import UserRoleEnum

# Use HTTPBearer instead of OAuth2PasswordBearer for better security
security = HTTPBearer(auto_error=False)

async def get_token_from_request(
    request: Request,
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Extract authentication token from request headers or cookies.
    
    Args:
        request: FastAPI request object
        authorization: Optional authorization credentials from header
        
    Returns:
        Token string or None if not found
    """
    # First try to get token from Authorization header
    if authorization and hasattr(authorization, 'credentials') and authorization.credentials:
        return authorization.credentials
    
    # Fallback to extracting from Authorization header manually
    auth_header = request.headers.get("Authorization")
    if auth_header:
        token = extract_token_from_header(auth_header)
        if token:
            return token
    
    # Last resort: check cookies (for backward compatibility)
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        logging.debug("Token found in cookies (consider using Authorization header)")
        return cookie_token
    
    return None

async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """
    Get current user from token, returns None if not authenticated.
    This is for optional authentication scenarios.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        User object or None if not authenticated
    """
    try:
        token = await get_token_from_request(request)
        if not token:
            return None
            
        payload = verify_access_token(token)
        if not payload or isinstance(payload, dict) and "error" in payload:
            return None
            
        orcid = payload.get("sub")
        if not orcid:
            return None
            
        # Get user with optimized loading
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.admin_orcid),
                selectinload(User.tokens),
                selectinload(User.database_versions),
                selectinload(User.collaborations),
                selectinload(User.collaborator_in)
            )
            .filter(User.orcid == orcid)
        )
        
        user = result.scalar_one_or_none()
        if user:
            # Update admin status if needed
            await _update_user_admin_status(user, orcid, db)
            
        return user
        
    except Exception as e:
        logging.warning(f"Error in optional authentication: {e}")
        return None

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_session)
) -> User:
    """
    Get current authenticated user, raises HTTPException if not authenticated.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = await get_token_from_request(request)
        if not token:
            logging.warning("No authentication token found in request")
            raise credentials_exception
        
        payload = verify_access_token(token)
        
        # Check if payload contains an error
        if payload is None or (isinstance(payload, dict) and "error" in payload):
            error_detail = "Could not validate credentials"
            if isinstance(payload, dict) and "error" in payload:
                error_detail = payload["error"]
                logging.warning(f"Token validation error: {error_detail}")
            
            # Provide more specific error messages
            if "expired" in error_detail.lower():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=error_detail,
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        orcid = payload.get("sub")
        if orcid is None:
            logging.warning("No ORCID found in token payload")
            raise credentials_exception
        
        # Use optimized query with eager loading to prevent N+1 queries
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.admin_orcid),
                selectinload(User.tokens),
                selectinload(User.database_versions),
                selectinload(User.collaborations),
                selectinload(User.collaborator_in)
            )
            .filter(User.orcid == orcid)
        )
        
        user = result.scalar_one_or_none()
        if user is None:
            logging.warning(f"User not found for ORCID: {orcid}")
            raise credentials_exception
            
        # Update user's admin status if needed
        await _update_user_admin_status(user, orcid, db)
        
        logging.debug(f"Successfully authenticated user: {user.full_name} ({user.role})")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user and verify admin permissions.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object with admin privileges
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        logging.warning(f"User {current_user.full_name} attempted to access admin endpoint without permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )
    return current_user

async def get_private_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user and verify private user or admin permissions.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object with private access privileges
        
    Raises:
        HTTPException: If user doesn't have private access
    """
    if current_user.role not in [UserRoleEnum.ADMIN.value, UserRoleEnum.PRIVATE_USER.value]:
        logging.warning(f"User {current_user.full_name} attempted to access private endpoint without permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Private user privileges required"
        )
    return current_user

async def get_collaborator_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user and verify collaborator, private user, or admin permissions.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object with collaborator privileges
        
    Raises:
        HTTPException: If user doesn't have collaborator access
    """
    allowed_roles = [UserRoleEnum.ADMIN.value, UserRoleEnum.PRIVATE_USER.value, UserRoleEnum.COLLABORATOR.value]
    if current_user.role not in allowed_roles:
        logging.warning(f"User {current_user.full_name} attempted to access collaborator endpoint without permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Collaborator privileges required"
        )
    return current_user

async def _update_user_admin_status(user: User, orcid: str, db: AsyncSession) -> None:
    """
    Helper function to update user admin status if needed.
    
    Args:
        user: User object to update
        orcid: User's ORCID ID
        db: Database session
    """
    try:
        # Check if the ORCID is in the admin_orcids table
        admin_result = await db.execute(select(AdminOrcid).filter(AdminOrcid.orcid == orcid))
        is_admin_orcid = admin_result.scalar_one_or_none() is not None
        
        # Update user's admin status if needed
        if is_admin_orcid and user.role != UserRoleEnum.ADMIN.value:
            logging.info(f"Updating user {user.full_name} role to admin")
            user.role = UserRoleEnum.ADMIN.value
            await db.commit()
            await db.refresh(user)
    except Exception as e:
        logging.error(f"Error updating user admin status: {e}")
        # Don't raise exception here to avoid breaking authentication
