from sqlalchemy import create_engine, Column, Integer, String, PrimaryKeyConstraint, ForeignKeyConstraint, Identity, \
    ForeignKey, Boolean, DateTime, BigInteger, Text, UniqueConstraint, Index, Table, Enum
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func, text
from sqlalchemy import event
import uuid
import enum
from .config import get_species_partition_commands

Base = declarative_base()

class UserRoleEnum(str, enum.Enum):
    ADMIN = "admin"
    PRIVATE_USER = "private_user"
    COLLABORATOR = "collaborator"
    PUBLIC = "public"

    def __str__(self):
        return self.value

# Association Table for Programs and Projects
program_project_association = Table(
    'program_project_association',
    Base.metadata,
    Column('program_id', Integer, ForeignKey('programs.id'), primary_key=True),
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True),
    UniqueConstraint('program_id', 'project_id', name='uix_program_project')
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    orcid = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(ENUM('admin', 'private_user', 'collaborator', 'public', name='user_role'), default='public', nullable=False)

    # Relationships - Change lazy loading to selectin loading
    admin_orcid = relationship("AdminOrcid", back_populates="user", uselist=False, lazy="selectin")
    tokens = relationship("UserToken", back_populates="user", lazy="selectin")
    database_versions = relationship("DatabaseVersion", back_populates="user", lazy="selectin")
    collaborations = relationship("Collaboration", foreign_keys="Collaboration.user_id", back_populates="user", lazy="selectin")
    collaborator_in = relationship("Collaboration", foreign_keys="Collaboration.collaborator_id", back_populates="collaborator", lazy="selectin")

    @property
    def is_admin(self):
        """Checks if the user is an admin based solely on their role."""
        return self.role == UserRoleEnum.ADMIN.value


class UserToken(Base):
    __tablename__ = "user_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    access_token = Column(String, nullable=False)
    token_type = Column(String, nullable=False)
    refresh_token = Column(String)
    expires_in = Column(BigInteger)
    scope = Column(String)

    user = relationship("User", back_populates="tokens", lazy="selectin")


class AdminOrcid(Base):
    __tablename__ = "admin_orcids"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    orcid = Column(String, unique=True, nullable=False)

    user = relationship("User", back_populates="admin_orcid", lazy="selectin")


class Program(Base):
    __tablename__ = 'programs'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())

    database_versions = relationship("DatabaseVersion", back_populates="program", lazy="selectin")
    sequence_presences = relationship("SequencePresence", back_populates="program", lazy="selectin")

    projects = relationship(
        "Project",
        secondary=program_project_association,
        back_populates="programs",
        lazy="selectin"
    )


class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationship to Programs
    programs = relationship(
        "Program",
        secondary=program_project_association,
        back_populates="projects",
        lazy="selectin"
    )


class Sequence(Base):
    __tablename__ = 'sequence_table'
    # Remove hapid, make alleleid and species the primary key
    alleleid = Column(String, primary_key=True, nullable=False, index=True)
    species = Column(String, primary_key=True, nullable=False, index=True)
    allelesequence = Column(Text, nullable=False)
    info = Column(Text, nullable=True)
    associated_trait = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    last_modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    version_added = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint('allelesequence', 'species', name='uix_allelesequence_species'),
        ForeignKeyConstraint(
            ['version_added', 'species'],
            ['database_versions.version', 'database_versions.species']
        ),
        {'postgresql_partition_by': 'LIST (species)'},
    )

    program_presences = relationship("SequencePresence", back_populates="sequence", lazy="selectin")
    allele_presence = relationship("AllelePresence", back_populates="allele", lazy="selectin")
    added_in_version = relationship("DatabaseVersion", lazy="selectin")


class DatabaseVersion(Base):
    __tablename__ = 'database_versions'
    version = Column(Integer, primary_key=True)
    species = Column(String, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=False)
    description = Column(Text, nullable=True)
    changes_summary = Column(Text, nullable=True)

    user = relationship("User", back_populates="database_versions", lazy="selectin")
    program = relationship("Program", back_populates="database_versions", lazy="selectin")

    __table_args__ = (
        UniqueConstraint('species', 'version', name='uix_species_version'),
    )


class Accession(Base):
    __tablename__ = "accessions"
    accession_id = Column(Integer, primary_key=True, index=True)
    accession_name = Column(String, unique=True, nullable=False)

    # Relationships
    allele_presence = relationship("AllelePresence", back_populates="accession", lazy="selectin")


Index('idx_accession_name', Accession.accession_name)


class AllelePresence(Base):
    __tablename__ = "allele_presence"
    alleleid = Column(String, primary_key=True)
    species = Column(String, primary_key=True)
    accession_id = Column(Integer, ForeignKey('accessions.accession_id'), primary_key=True)
    # presence is implicitly True by virtue of existing in this table
    version_added = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint('alleleid', 'accession_id', name='uix_allele_presence'),
        ForeignKeyConstraint(
            ['alleleid', 'species'],
            ['sequence_table.alleleid', 'sequence_table.species']
        ),
        ForeignKeyConstraint(
            ['version_added', 'species'],
            ['database_versions.version', 'database_versions.species']
        )
    )

    allele = relationship("Sequence", back_populates="allele_presence", lazy="selectin")
    accession = relationship("Accession", back_populates="allele_presence", lazy="selectin")
    added_in_version = relationship("DatabaseVersion", lazy="selectin", overlaps="allele,allele_presence")


Index('idx_alleleid', AllelePresence.alleleid)
Index('idx_accession_id', AllelePresence.accession_id)


class SequencePresence(Base):
    __tablename__ = 'sequence_presence'
    program_id = Column(Integer, ForeignKey('programs.id'), primary_key=True)
    alleleid = Column(String, primary_key=True, nullable=False)
    species = Column(String, primary_key=True, nullable=False)
    presence = Column(Boolean, nullable=False, default=True)
    version_added = Column(Integer, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ['alleleid', 'species'],
            ['sequence_table.alleleid', 'sequence_table.species'],
            ondelete='CASCADE'
        ),
        ForeignKeyConstraint(
            ['version_added', 'species'],
            ['database_versions.version', 'database_versions.species']
        ),
    )

    program = relationship("Program", back_populates="sequence_presences", lazy="selectin")
    sequence = relationship(
        "Sequence",
        back_populates="program_presences",
        lazy="selectin"
    )
    added_in_version = relationship("DatabaseVersion", lazy="selectin", overlaps="program_presences,sequence")


class Collaboration(Base):
    __tablename__ = "collaborations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    collaborator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_modified_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="collaborations", lazy="selectin")
    collaborator = relationship("User", foreign_keys=[collaborator_id], back_populates="collaborator_in", lazy="selectin")

    __table_args__ = (
        UniqueConstraint('user_id', 'collaborator_id', name='uix_user_collaborator'),
    )


class FileUpload(Base):
    """Model to track uploaded files and their associated database versions"""
    __tablename__ = 'file_uploads'
    
    id = Column(Integer, primary_key=True)
    file_name = Column(String, nullable=False)
    upload_type = Column(String, nullable=False)  # 'madc', 'pav', 'supplemental'
    file_size = Column(BigInteger, nullable=True)
    upload_date = Column(DateTime, default=func.now(), nullable=False)
    version = Column(Integer, nullable=False)
    species = Column(String, nullable=False)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=False)
    project_name = Column(String, nullable=True)  # Only for MADC uploads
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    job_id = Column(String, nullable=True)  # Reference to background job
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['version', 'species'],
            ['database_versions.version', 'database_versions.species']
        ),
        Index('idx_file_uploads_version_species', 'version', 'species'),
        Index('idx_file_uploads_upload_date', 'upload_date'),
        Index('idx_file_uploads_upload_type', 'upload_type'),
        Index('idx_file_uploads_program_id', 'program_id'),
    )
    
    # Relationships
    database_version = relationship("DatabaseVersion", lazy="selectin")
    program = relationship("Program", lazy="selectin")
    user = relationship("User", lazy="selectin")


# Use SQLAlchemy event listener to create partitions after the base table is created
@event.listens_for(Base.metadata, 'after_create')
def create_partitions(target, connection, **kw):
    partition_commands = get_species_partition_commands()
    for command in partition_commands:
        connection.execute(text(command))