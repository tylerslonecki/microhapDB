from sqlalchemy import create_engine, Column, Integer, String, PrimaryKeyConstraint, ForeignKeyConstraint, Identity, \
    ForeignKey, Boolean, DateTime, BigInteger, Text, UniqueConstraint, Index, Table
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func, text
from sqlalchemy import event
import uuid

Base = declarative_base()

# Association Table for Programs and Sources
program_source_association = Table(
    'program_source_association',
    Base.metadata,
    Column('program_id', Integer, ForeignKey('programs.id'), primary_key=True),
    Column('source_id', Integer, ForeignKey('sources.id'), primary_key=True),
    UniqueConstraint('program_id', 'source_id', name='uix_program_source')
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    orcid = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    admin_orcid = relationship("AdminOrcid", back_populates="user", uselist=False)
    tokens = relationship("UserToken", back_populates="user")
    database_versions = relationship("DatabaseVersion", back_populates="user")

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


class Program(Base):
    __tablename__ = 'programs'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())

    database_versions = relationship("DatabaseVersion", back_populates="program")
    sequence_presences = relationship("SequencePresence", back_populates="program")

    sources = relationship(
        "Source",
        secondary=program_source_association,
        back_populates="programs"
    )


class Source(Base):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationship to Programs
    programs = relationship(
        "Program",
        secondary=program_source_association,
        back_populates="sources"
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
    version_added = Column(Integer, ForeignKey('database_versions.version'), nullable=False)

    __table_args__ = (
        UniqueConstraint('allelesequence', 'species', name='uix_allelesequence_species'),
        {'postgresql_partition_by': 'LIST (species)'},
    )

    program_presences = relationship("SequencePresence", back_populates="sequence")
    allele_presence = relationship("AllelePresence", back_populates="allele")
    added_in_version = relationship("DatabaseVersion")


class DatabaseVersion(Base):
    __tablename__ = 'database_versions'
    version = Column(Integer, primary_key=True, autoincrement=True)
    species = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=False)
    description = Column(Text, nullable=True)
    changes_summary = Column(Text, nullable=True)

    user = relationship("User", back_populates="database_versions")
    program = relationship("Program", back_populates="database_versions")

    __table_args__ = (
        UniqueConstraint('species', 'version', name='uix_species_version'),
    )


class Accession(Base):
    __tablename__ = "accessions"
    accession_id = Column(Integer, primary_key=True, index=True)
    accession_name = Column(String, unique=True, nullable=False)

    # Relationships
    allele_presence = relationship("AllelePresence", back_populates="accession")


Index('idx_accession_name', Accession.accession_name)


class AllelePresence(Base):
    __tablename__ = "allele_presence"
    alleleid = Column(String, primary_key=True)
    species = Column(String, primary_key=True)
    accession_id = Column(Integer, ForeignKey('accessions.accession_id'), primary_key=True)
    # presence is implicitly True by virtue of existing in this table
    version_added = Column(Integer, ForeignKey('database_versions.version'), nullable=False)

    __table_args__ = (
        UniqueConstraint('alleleid', 'accession_id', name='uix_allele_presence'),
        ForeignKeyConstraint(
            ['alleleid', 'species'],
            ['sequence_table.alleleid', 'sequence_table.species']
        )
    )

    allele = relationship("Sequence", back_populates="allele_presence")
    accession = relationship("Accession", back_populates="allele_presence")
    added_in_version = relationship("DatabaseVersion")


Index('idx_alleleid', AllelePresence.alleleid)
Index('idx_accession_id', AllelePresence.accession_id)


class SequencePresence(Base):
    __tablename__ = 'sequence_presence'
    program_id = Column(Integer, ForeignKey('programs.id'), primary_key=True)
    alleleid = Column(String, primary_key=True, nullable=False)
    species = Column(String, primary_key=True, nullable=False)
    presence = Column(Boolean, nullable=False, default=True)
    version_added = Column(Integer, ForeignKey('database_versions.version'), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ['alleleid', 'species'],
            ['sequence_table.alleleid', 'sequence_table.species'],
            ondelete='CASCADE'
        ),
    )

    program = relationship("Program", back_populates="sequence_presences")
    sequence = relationship(
        "Sequence",
        back_populates="program_presences"
    )
    added_in_version = relationship("DatabaseVersion")


# Use SQLAlchemy event listener to create partitions after the base table is created
@event.listens_for(Base.metadata, 'after_create')
def create_partitions(target, connection, **kw):
    partition_commands = [
        "CREATE TABLE IF NOT EXISTS sequence_table_sweetpotato PARTITION OF sequence_table FOR VALUES IN ('sweetpotato');",
        "CREATE TABLE IF NOT EXISTS sequence_table_blueberry PARTITION OF sequence_table FOR VALUES IN ('blueberry');",
        "CREATE TABLE IF NOT EXISTS sequence_table_alfalfa PARTITION OF sequence_table FOR VALUES IN ('alfalfa');",
        "CREATE TABLE IF NOT EXISTS sequence_table_cranberry PARTITION OF sequence_table FOR VALUES IN ('cranberry');"
    ]
    for command in partition_commands:
        connection.execute(text(command))