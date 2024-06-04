from pydantic import BaseModel
from typing import Optional
from src.models import Base, User, AllowedOrcid, DATABASE_URL, SYNC_DATABASE_URL
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

# Create an asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=True)
# Create a synchronous engine
sync_engine = create_engine(SYNC_DATABASE_URL, echo=True)

# Configure sessionmaker for asynchronous usage
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Configure sessionmaker for synchronous usage
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# Use this function as a dependency in your FastAPI routes
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

def get_sync_session():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
