from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.database import get_session
from src.models import User, Collaboration, UserRoleEnum
from src.auth.dependencies import get_current_user

async def check_data_access(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> bool:
    """
    Check if the current user has access to the specified user's data.
    Returns True if the current user is:
    1. The owner of the data
    2. An admin
    3. A collaborator with the owner
    4. The data is public
    """
    if current_user.is_admin or current_user.id == user_id:
        return True
    
    # Check for collaboration
    # Use eagerly loaded relationship data instead of executing additional query
    collaboration = any(collab.user_id == user_id for collab in current_user.collaborator_in)
    
    if collaboration:
        return True
    
    # Check if the data is public
    result = await db.execute(
        select(User).options(selectinload(User.admin_orcid)).filter(User.id == user_id)
    )
    data_owner = result.scalar_one_or_none()
    
    if data_owner and data_owner.role == UserRoleEnum.PUBLIC:
        return True
    
    return False

async def get_accessible_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> dict:
    """
    Get a dictionary containing the user's access level and accessible data IDs.
    """
    if current_user.is_admin:
        return {
            "access_level": "admin",
            "accessible_user_ids": None  # None indicates access to all users
        }
    
    accessible_ids = [current_user.id]
    
    # Get users who have collaborated with the current user
    # Use eagerly loaded relationship data instead of executing additional query
    collaborator_ids = [collaboration.user_id for collaboration in current_user.collaborator_in]
    accessible_ids.extend(collaborator_ids)
    
    return {
        "access_level": current_user.role,
        "accessible_user_ids": accessible_ids
    }

async def require_admin_access(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure the user has admin access."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def require_private_access(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure the user has private access."""
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.PRIVATE_USER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Private access required"
        )
    return current_user

async def require_collaborator_access(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure the user has collaborator access."""
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.PRIVATE_USER, UserRoleEnum.COLLABORATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Collaborator access required"
        )
    return current_user 