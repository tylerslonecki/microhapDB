from pydantic import BaseModel
from typing import Optional
from src.models import Base, User, AdminOrcid, UserToken, DATABASE_URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

class UserResponse(BaseModel):
    id: int
    full_name: Optional[str]
    orcid: str
    is_active: bool
    is_admin: bool

    class Config:
        orm_mode = True

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
