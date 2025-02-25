from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.models import Base

# AWS Async (for FastAPI)
DATABASE_URL = "postgresql+asyncpg://postgres:bipostgres@database-1.czwgjenckjul.us-east-2.rds.amazonaws.com:5432/haplosearch"
# AWS Sync (for Alembic)
SYNC_DATABASE_URL = "postgresql://postgres:bipostgres@database-1.czwgjenckjul.us-east-2.rds.amazonaws.com:5432/haplosearch"

# Create engines for both async and sync operations
engine = create_async_engine(DATABASE_URL, echo=True)
sync_engine = create_engine(SYNC_DATABASE_URL, echo=True)

# Configure sessionmaker for asynchronous usage
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