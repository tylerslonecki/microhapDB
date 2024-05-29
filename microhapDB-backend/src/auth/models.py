# src/auth/models.py

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, DateTime, BigInteger
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

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    orcid = Column(String, unique=True, index=True)  # Add ORCID field
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    access_token = Column(String)
    token_type = Column(String)
    refresh_token = Column(String)
    expires_in = Column(BigInteger)
    scope = Column(String)

class UserResponse(BaseModel):
    id: int
    full_name: Optional[str]
    orcid: str
    is_active: bool
    is_admin: bool

    class Config:
        orm_mode = True

class AllowedOrcid(Base):
    __tablename__ = "allowed_orcids"
    orcid = Column(String, primary_key=True, index=True)
    is_admin = Column(Boolean, default=False)

class Sequence(Base):
    __tablename__ = 'sequence_table'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hapID = Column(UUID(as_uuid=True), unique=True, index=True, default=uuid.uuid4)
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
    hapID = Column(UUID(as_uuid=True), ForeignKey('sequence_table.hapID'))
    batch_id = Column(Integer, ForeignKey('upload_batches.id'))
    was_new = Column(Boolean, default=True)
    sequence = relationship("Sequence", back_populates="logs")
    batch = relationship("UploadBatch", back_populates="sequences")

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    submission_time: datetime
    completion_time: Optional[datetime] = None

DATABASE_URL = "postgresql+asyncpg://postgres_user:bipostgres@postgres/microhaplotype"

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
