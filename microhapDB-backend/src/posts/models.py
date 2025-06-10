# posts/models.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

from sqlalchemy.orm import sessionmaker
from src.models import Base, Sequence, Accession, AllelePresence, DatabaseVersion, Program, Project, \
    SequencePresence, program_project_association, FileUpload
from src.database import get_session, init_db  # Import the centralized functions and objects


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    submission_time: datetime
    completion_time: Optional[datetime] = None
    file_name: str = None


class QueryRequest(BaseModel):
    query: str


class SequenceResponse(BaseModel):
    alleleid: str
    species: str
    allelesequence: str
    info: Optional[str] = None
    associated_trait: Optional[str] = None


class ColumnFilter(BaseModel):
    value: Optional[str] = None
    matchMode: Optional[str] = None


class PaginatedSequenceRequest(BaseModel):
    page: int = 1
    size: int = 50
    species: Optional[str] = None
    globalFilter: Optional[str] = None
    filters: Optional[Dict[str, ColumnFilter]] = None


class PaginatedSequenceResponse(BaseModel):
    total: int
    items: List[SequenceResponse]


class AccessionRequest(BaseModel):
    alleleid: List[str] = Field(..., example=["allele1", "allele2"])


class AccessionResponse(BaseModel):
    alleleid: str
    accessions: List[str]


class AccessionDetailResponse(BaseModel):
    alleleid: str
    accession: str
    programs: List[str] = []
    projects: List[str] = []


class ProjectBase(BaseModel):
    name: str = Field(..., example="Project Name")
    description: Optional[str] = Field(None, example="Description of the project")


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class ProgramResponse(BaseModel):
    id: int
    name: str
    description: str = None

    class Config:
        orm_mode = True


class ProgramCreate(BaseModel):
    name: str = Field(..., example="Program Name")
    description: Optional[str] = Field(None, example="Description of the program")
    project_ids: Optional[List[int]] = Field(None, example=[1, 2])  # To associate projects upon creation


class SupplementalJobStatusResponse(BaseModel):
    job_id: str
    status: str
    submission_time: datetime
    completion_time: Optional[datetime] = None
    file_name: Optional[str] = None
    missing_allele_ids: Optional[List[str]] = None
    error: Optional[str] = None

    class Config:
        orm_mode = True


class FileUploadResponse(BaseModel):
    """Response model for file upload information"""
    id: int
    file_name: str
    upload_type: str
    file_size: Optional[int] = None
    upload_date: datetime
    version: int
    species: str
    program_name: str
    project_name: Optional[str] = None
    uploaded_by: Optional[str] = None


class VersionStatsResponse(BaseModel):
    """Response model for version statistics"""
    version: int
    species: str
    created_at: datetime
    total_alleles: int
    new_alleles: int
    program_name: str
    description: Optional[str] = None
    uploaded_by: Optional[str] = None
    files: Optional[List[FileUploadResponse]] = None  # Add file information

# # Create an asynchronous engine
# engine = create_async_engine(DATABASE_URL, echo=True)
# # Create a synchronous engine
# # sync_engine = create_engine(SYNC_DATABASE_URL, echo=True)
#
# # Configure sessionmaker for asynchronous usage
# AsyncSessionLocal = sessionmaker(
#     bind=engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
#     autocommit=False,
#     autoflush=False,
# )
#
#
# # # Configure sessionmaker for synchronous usage
# # SyncSessionLocal = sessionmaker(
# #     bind=sync_engine,
# #     autocommit=False,
# #     autoflush=False,
# # )
#
# # Use this function as a dependency in your FastAPI routes
# async def get_session():
#     async with AsyncSessionLocal() as session:
#         yield session
#
#
# # def get_sync_session():
# #     db = SyncSessionLocal()
# #     try:
# #         yield db
# #     finally:
# #         db.close()
#
# async def init_db():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
