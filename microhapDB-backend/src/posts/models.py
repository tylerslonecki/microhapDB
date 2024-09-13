from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import create_engine
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.models import Base, Sequence, UploadBatch, SequenceLog, DATABASE_URL, SYNC_DATABASE_URL

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    submission_time: datetime
    completion_time: Optional[datetime] = None

class QueryRequest(BaseModel):
    query: str

class SequenceResponse(BaseModel):
    id: str
    hapid: str
    alleleid: str
    allelesequence: str
    species: str

class PaginatedSequenceRequest(BaseModel):
    page: int = 1
    size: int = 50
    filter: Optional[str] = None
    filter_field: Optional[str] = None
    species: Optional[str] = None

class PaginatedSequenceResponse(BaseModel):
    total: int
    items: List[SequenceResponse]

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
