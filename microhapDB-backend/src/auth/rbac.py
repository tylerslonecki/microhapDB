from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import get_session, User, UserRoleEnum, Collaboration
from .dependencies import get_current_user

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_private_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.PRIVATE_USER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_collaborator_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.PRIVATE_USER, UserRoleEnum.COLLABORATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def check_collaboration_access(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> bool:
    """
    Check if the current user has access to the specified user's data through collaboration.
    Returns True if the current user is:
    1. The owner of the data
    2. An admin
    3. A collaborator with the owner
    """
    if current_user.id == user_id or current_user.is_admin:
        return True
    
    # Check for collaboration
    result = await db.execute(
        select(Collaboration).filter(
            Collaboration.user_id == user_id,
            Collaboration.collaborator_id == current_user.id
        )
    )
    collaboration = result.scalar_one_or_none()
    
    return collaboration is not None

async def get_accessible_user_ids(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> list[int]:
    """
    Get a list of user IDs that the current user has access to.
    This includes:
    1. The user's own ID
    2. IDs of users who have collaborated with the current user
    3. All user IDs if the current user is an admin
    """
    if current_user.is_admin:
        result = await db.execute(select(User.id))
        return [user.id for user in result.scalars().all()]
    
    accessible_ids = [current_user.id]
    
    # Get users who have collaborated with the current user
    result = await db.execute(
        select(Collaboration.user_id).filter(
            Collaboration.collaborator_id == current_user.id
        )
    )
    collaborator_ids = result.scalars().all()
    accessible_ids.extend(collaborator_ids)
    
    return accessible_ids 