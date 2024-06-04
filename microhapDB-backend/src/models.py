from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, DateTime, BigInteger, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func, text
from sqlalchemy import event
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    orcid = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    access_token = Column(String)
    token_type = Column(String)
    refresh_token = Column(String)
    expires_in = Column(BigInteger)
    scope = Column(String)

class AllowedOrcid(Base):
    __tablename__ = "allowed_orcids"
    orcid = Column(String, primary_key=True, index=True)
    is_admin = Column(Boolean, default=False)

class Sequence(Base):
    __tablename__ = 'sequence_table'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hapid = Column(UUID(as_uuid=True), unique=True, index=True, default=uuid.uuid4)
    alleleid = Column(String)
    allelesequence = Column(Text)
    species = Column(String, index=True)
    logs = relationship("SequenceLog", back_populates="sequence")

class UploadBatch(Base):
    __tablename__ = 'upload_batches'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    sequences = relationship("SequenceLog", back_populates="batch")

class SequenceLog(Base):
    __tablename__ = 'sequence_log'
    id = Column(Integer, primary_key=True)
    hapid = Column(UUID(as_uuid=True), ForeignKey('sequence_table.hapid'))
    batch_id = Column(Integer, ForeignKey('upload_batches.id'))
    was_new = Column(Boolean, default=True)
    species = Column(String, index=True)
    sequence = relationship("Sequence", back_populates="logs")
    batch = relationship("UploadBatch", back_populates="sequences")

# Configuration for the database URL
DATABASE_URL = "postgresql+asyncpg://postgres_user:bipostgres@postgres/microhaplotype"
SYNC_DATABASE_URL = "postgresql://postgres_user:bipostgres@postgres/microhaplotype"

# Create an asynchronous engine
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

# Configure sessionmaker for synchronous usage
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

def get_sync_session():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to initialize the database and create partitions
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Create partitioned table and partitions
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS sequence_table (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                hapid UUID UNIQUE,
                alleleid TEXT,
                allelesequence TEXT,
                species TEXT
            ) PARTITION BY LIST (species);
        '''))
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS sequence_log (
                id SERIAL PRIMARY KEY,
                hapid UUID REFERENCES sequence_table(hapid),
                batch_id INTEGER REFERENCES upload_batches(id),
                was_new BOOLEAN DEFAULT TRUE,
                species TEXT
            ) PARTITION BY LIST (species);
        '''))

# Use SQLAlchemy event listener to create partitions after the base table is created
@event.listens_for(Base.metadata, 'after_create')
def create_partitions(target, connection, **kw):
    partition_commands = [
        "CREATE TABLE IF NOT EXISTS sequence_table_sweetpotato PARTITION OF sequence_table FOR VALUES IN ('sweetpotato');",
        "CREATE TABLE IF NOT EXISTS sequence_table_blueberry PARTITION OF sequence_table FOR VALUES IN ('blueberry');",
        "CREATE TABLE IF NOT EXISTS sequence_table_alfalfa PARTITION OF sequence_table FOR VALUES IN ('alfalfa');",
        "CREATE TABLE IF NOT EXISTS sequence_table_cranberry PARTITION OF sequence_table FOR VALUES IN ('cranberry');",
        "CREATE TABLE IF NOT EXISTS sequence_log_sweetpotato PARTITION OF sequence_log FOR VALUES IN ('sweetpotato');",
        "CREATE TABLE IF NOT EXISTS sequence_log_blueberry PARTITION OF sequence_log FOR VALUES IN ('blueberry');",
        "CREATE TABLE IF NOT EXISTS sequence_log_alfalfa PARTITION OF sequence_log FOR VALUES IN ('alfalfa');",
        "CREATE TABLE IF NOT EXISTS sequence_log_cranberry PARTITION OF sequence_log FOR VALUES IN ('cranberry');"
    ]
    for command in partition_commands:
        connection.execute(text(command))
