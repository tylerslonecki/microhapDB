from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.future import select
from sqlalchemy.sql import func
import uuid
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

Base = declarative_base()

class Sequence(Base):
    __tablename__ = 'sequence_table'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hapID = Column(UUID(as_uuid=True), unique=True, index=True, default=uuid.uuid4)  # Ensure it's indexed for better performance on joins
    alleleID = Column(String)
    alleleSequence = Column(String)
    logs = relationship("SequenceLog", back_populates="sequence")

class UploadBatch(Base):
    __tablename__ = 'upload_batches'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    sequences = relationship("SequenceLog", back_populates="batch")

class SequenceLog(Base):
    __tablename__ = 'sequence_log'
    id = Column(Integer, primary_key=True)
    hapID = Column(UUID(as_uuid=True), ForeignKey('sequence_table.hapID'))  # Changed to refer hapID
    batch_id = Column(Integer, ForeignKey('upload_batches.id'))
    was_new = Column(Boolean, default=True)
    sequence = relationship("Sequence", back_populates="logs")
    batch = relationship("UploadBatch", back_populates="sequences")

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    submission_time: datetime
    completion_time: Optional[datetime] = None

# Configuration for the database URL
DATABASE_URL = "postgresql+asyncpg://postgres_user:bipostgres@postgres/microhaplotype"
# Configuration for the synchronous database URL
SYNC_DATABASE_URL = "postgresql://postgres_user:bipostgres@postgres/microhaplotype"

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

# Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

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
