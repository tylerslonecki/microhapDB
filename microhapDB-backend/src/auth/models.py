from pydantic import BaseModel
from typing import Optional
from src.models import Base, User, AdminOrcid, UserToken, UserRoleEnum  # Keep model definitions here
from src.database import get_session  # Import the session generator from database.py

class UserResponse(BaseModel):
    id: int
    full_name: Optional[str]
    orcid: str
    is_active: bool
    is_admin: bool
    role: UserRoleEnum

    class Config:
        orm_mode = True

# No need to reinitialize the engine or session here.
