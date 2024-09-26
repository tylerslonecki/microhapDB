from sqlalchemy import create_engine, Column, Integer, String, PrimaryKeyConstraint, ForeignKeyConstraint, Identity, \
    ForeignKey, Boolean, DateTime, BigInteger, Text, UniqueConstraint
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
    full_name = Column(String, nullable=False)
    orcid = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    admin_orcid = relationship("AdminOrcid", back_populates="user", uselist=False)
    tokens = relationship("UserToken", back_populates="user")

    @property
    def is_admin(self):
        """Checks if the user is an admin by verifying the presence of an AdminOrcid relationship."""
        return self.admin_orcid is not None


class UserToken(Base):
    __tablename__ = "user_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    access_token = Column(String, nullable=False)
    token_type = Column(String, nullable=False)
    refresh_token = Column(String)
    expires_in = Column(BigInteger)
    scope = Column(String)

    user = relationship("User", back_populates="tokens")


class AdminOrcid(Base):
    __tablename__ = "admin_orcids"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    orcid = Column(String, unique=True, nullable=False)

    user = relationship("User", back_populates="admin_orcid")


class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())

    upload_batches = relationship("UploadBatch", back_populates="project")
    sequence_presences = relationship("SequencePresence", back_populates="project")


class Sequence(Base):
    __tablename__ = 'sequence_table'
    hapid = Column(UUID(as_uuid=True), default=uuid.uuid4)
    alleleid = Column(String, nullable=False, index=True)
    allelesequence = Column(Text, nullable=False)
    species = Column(String, nullable=False, index=True)

    __table_args__ = (
        PrimaryKeyConstraint('hapid', 'species'),
        UniqueConstraint('allelesequence', 'species', name='uix_allelesequence_species'),
        {'postgresql_partition_by': 'LIST (species)'},
        
    )

    project_presences = relationship("SequencePresence", back_populates="sequence")
    logs = relationship("SequenceLog", back_populates="sequence")


class UploadBatch(Base):
    __tablename__ = 'upload_batches'
    id = Column(Integer, primary_key=True)
    species = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)

    sequences = relationship("SequenceLog", back_populates="batch")
    user = relationship("User")
    project = relationship("Project", back_populates="upload_batches")

    __table_args__ = (
        UniqueConstraint('species', 'version', name='uix_species_version'),
    )


class SequenceLog(Base):
    __tablename__ = 'sequence_logs'
    id = Column(Integer, Identity(), nullable=False)
    hapid = Column(UUID(as_uuid=True), nullable=False)
    species = Column(String, nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey('upload_batches.id'), nullable=False)
    was_new = Column(Boolean, default=True)
    alleleid = Column(String, nullable=False)
    allelesequence = Column(Text, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('id', 'species'),
        ForeignKeyConstraint(
            ['hapid', 'species'],
            ['sequence_table.hapid', 'sequence_table.species']
        ),
        {'postgresql_partition_by': 'LIST (species)'},
    )

    batch = relationship("UploadBatch", back_populates="sequences")
    sequence = relationship(
        "Sequence",
        primaryjoin=(
            "and_(SequenceLog.hapid == Sequence.hapid, SequenceLog.species == Sequence.species)"
        ),
        back_populates="logs"
    )


class SequencePresence(Base):
    __tablename__ = 'sequence_presence'
    project_id = Column(Integer, ForeignKey('projects.id'), primary_key=True)
    hapid = Column(UUID(as_uuid=True), nullable=False)
    species = Column(String, nullable=False)
    presence = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        PrimaryKeyConstraint('project_id', 'hapid', 'species'),
        ForeignKeyConstraint(
            ['hapid', 'species'],
            ['sequence_table.hapid', 'sequence_table.species'],
            ondelete='CASCADE'
        ),
    )

    project = relationship("Project", back_populates="sequence_presences")
    sequence = relationship(
        "Sequence",
        primaryjoin=(
            "and_(SequencePresence.hapid == Sequence.hapid, SequencePresence.species == Sequence.species)"
        ),
        back_populates="project_presences"
    )


# Configuration for the database URL
DATABASE_URL = "postgresql+asyncpg://postgres_user:bipostgres@postgres/microhaplotype"
# SYNC_DATABASE_URL = "postgresql://postgres_user:bipostgres@postgres/microhaplotype"

# Create an asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=True)
# sync_engine = create_engine(SYNC_DATABASE_URL, echo=True)

# Configure sessionmaker for asynchronous usage
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# # Configure sessionmaker for synchronous usage
# SyncSessionLocal = sessionmaker(
#     bind=sync_engine,
#     autocommit=False,
#     autoflush=False,
# )

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


# def get_sync_session():
#     db = SyncSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# Function to initialize the database and create partitions
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Use SQLAlchemy event listener to create partitions after the base table is created
@event.listens_for(Base.metadata, 'after_create')
def create_partitions(target, connection, **kw):
    partition_commands = [
        "CREATE TABLE IF NOT EXISTS sequence_table_sweetpotato PARTITION OF sequence_table FOR VALUES IN ('sweetpotato');",
        "CREATE TABLE IF NOT EXISTS sequence_table_blueberry PARTITION OF sequence_table FOR VALUES IN ('blueberry');",
        "CREATE TABLE IF NOT EXISTS sequence_table_alfalfa PARTITION OF sequence_table FOR VALUES IN ('alfalfa');",
        "CREATE TABLE IF NOT EXISTS sequence_table_cranberry PARTITION OF sequence_table FOR VALUES IN ('cranberry');",
        "CREATE TABLE IF NOT EXISTS sequence_logs_sweetpotato PARTITION OF sequence_logs FOR VALUES IN ('sweetpotato');",
        "CREATE TABLE IF NOT EXISTS sequence_logs_blueberry PARTITION OF sequence_logs FOR VALUES IN ('blueberry');",
        "CREATE TABLE IF NOT EXISTS sequence_logs_alfalfa PARTITION OF sequence_logs FOR VALUES IN ('alfalfa');",
        "CREATE TABLE IF NOT EXISTS sequence_logs_cranberry PARTITION OF sequence_logs FOR VALUES IN ('cranberry');"
    ]
    for command in partition_commands:
        connection.execute(text(command))
