from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy.future import select
import os
from src.models import Base

# Get echo setting from environment (default to False for production)
ECHO_SQL = os.getenv("ECHO_SQL", "false").lower() == "true"

# Get database URL from environment with fallback to AWS RDS
DATABASE_URL_ENV = os.getenv("DATABASE_URL")

# If environment variable is provided, use it; otherwise use hardcoded AWS RDS URL
if DATABASE_URL_ENV:
    # Convert sync URL to async URL if needed
    if DATABASE_URL_ENV.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL_ENV.replace("postgresql://", "postgresql+asyncpg://", 1)
        SYNC_DATABASE_URL = DATABASE_URL_ENV
    else:
        DATABASE_URL = DATABASE_URL_ENV
        SYNC_DATABASE_URL = DATABASE_URL_ENV.replace("postgresql+asyncpg://", "postgresql://", 1)
else:
    # AWS Async (for FastAPI)
    DATABASE_URL = "postgresql+asyncpg://postgres:bipostgres@database-1.czwgjenckjul.us-east-2.rds.amazonaws.com:5432/haplosearch"
    # AWS Sync (for Alembic)
    SYNC_DATABASE_URL = "postgresql://postgres:bipostgres@database-1.czwgjenckjul.us-east-2.rds.amazonaws.com:5432/haplosearch"

# Create engines for both async and sync operations
engine = create_async_engine(
    DATABASE_URL, 
    echo=ECHO_SQL, 
    pool_pre_ping=True,
    pool_size=20,  # Increase pool size for large uploads
    max_overflow=30,  # Allow more overflow connections
    pool_timeout=30,  # Timeout for getting connection from pool
    pool_recycle=3600,  # Recycle connections every hour
)
sync_engine = create_engine(
    SYNC_DATABASE_URL, 
    echo=ECHO_SQL, 
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
)

# Configure sessionmaker for asynchronous usage
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_session():
    """Dependency that yields an async session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize the database by creating all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def load_relationship(obj, relationship_name):
    """
    Explicitly load a relationship to avoid lazy loading issues.
    
    Args:
        obj: The SQLAlchemy model instance
        relationship_name: The name of the relationship to load
    
    Returns:
        The loaded relationship data
    """
    if hasattr(obj, relationship_name):
        # Get the session from the object
        session = AsyncSession.object_session(obj)
        if session:
            # Create a query that loads the relationship
            stmt = select(obj.__class__).where(obj.__class__.id == obj.id).options(selectinload(getattr(obj.__class__, relationship_name)))
            result = await session.execute(stmt)
            refreshed_obj = result.scalar_one()
            return getattr(refreshed_obj, relationship_name)
    return getattr(obj, relationship_name, None)