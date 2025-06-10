"""fix_species_specific_versioning

Revision ID: 0501d6d5ea5e
Revises: 8466cecf4550
Create Date: 2025-06-05 17:00:03.511541

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0501d6d5ea5e'
down_revision: Union[str, None] = '8466cecf4550'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Drop existing foreign key constraints
    op.execute("ALTER TABLE sequence_table DROP CONSTRAINT IF EXISTS sequence_table_version_added_fkey;")
    op.execute("ALTER TABLE allele_presence DROP CONSTRAINT IF EXISTS allele_presence_version_added_fkey;")
    op.execute("ALTER TABLE sequence_presence DROP CONSTRAINT IF EXISTS sequence_presence_version_added_fkey;")
    
    # Step 2: Create a temporary table with the new structure
    op.execute("""
        CREATE TABLE database_versions_temp (
            version INTEGER NOT NULL,
            species VARCHAR NOT NULL,
            created_at TIMESTAMP,
            uploaded_by INTEGER,
            program_id INTEGER NOT NULL,
            description TEXT,
            changes_summary TEXT,
            PRIMARY KEY (version, species),
            FOREIGN KEY(uploaded_by) REFERENCES users (id),
            FOREIGN KEY(program_id) REFERENCES programs (id),
            CONSTRAINT uix_temp_species_version UNIQUE (species, version)
        );
    """)
    
    # Step 3: Migrate data with species-specific version numbers
    op.execute("""
        INSERT INTO database_versions_temp (version, species, created_at, uploaded_by, program_id, description, changes_summary)
        SELECT 
            ROW_NUMBER() OVER (PARTITION BY species ORDER BY created_at, version) as version,
            species,
            created_at,
            uploaded_by,
            program_id,
            description,
            changes_summary
        FROM database_versions
        ORDER BY species, created_at, version;
    """)
    
    # Step 4: Update foreign key references in dependent tables
    # Store the mapping of old version to new (species, version) pair
    op.execute("""
        CREATE TEMPORARY TABLE version_mapping AS
        SELECT 
            old_dv.version as old_version,
            new_dv.version as new_version,
            new_dv.species as species
        FROM database_versions old_dv
        JOIN database_versions_temp new_dv ON (
            old_dv.species = new_dv.species AND
            old_dv.created_at = new_dv.created_at AND
            old_dv.program_id = new_dv.program_id
        );
    """)
    
    # Update sequence_table version_added references
    op.execute("""
        UPDATE sequence_table
        SET version_added = vm.new_version
        FROM version_mapping vm
        WHERE sequence_table.version_added = vm.old_version
        AND sequence_table.species = vm.species;
    """)
    
    # Update allele_presence version_added references
    op.execute("""
        UPDATE allele_presence 
        SET version_added = vm.new_version
        FROM version_mapping vm
        WHERE allele_presence.version_added = vm.old_version
        AND allele_presence.species = vm.species;
    """)
    
    # Update sequence_presence version_added references
    op.execute("""
        UPDATE sequence_presence
        SET version_added = vm.new_version
        FROM version_mapping vm
        WHERE sequence_presence.version_added = vm.old_version
        AND sequence_presence.species = vm.species;
    """)
    
    # Step 5: Drop the old table and rename the new one
    op.drop_table('database_versions')
    op.execute("ALTER TABLE database_versions_temp RENAME TO database_versions;")
    
    # Step 6: Rename the constraint back to the original name
    op.execute("""
        ALTER TABLE database_versions 
        RENAME CONSTRAINT uix_temp_species_version TO uix_species_version;
    """)
    
    # Step 7: Add the new foreign key constraints with composite keys
    op.execute("""
        ALTER TABLE sequence_table 
        ADD CONSTRAINT sequence_table_version_species_fkey 
        FOREIGN KEY (version_added, species) 
        REFERENCES database_versions (version, species);
    """)
    
    op.execute("""
        ALTER TABLE allele_presence 
        ADD CONSTRAINT allele_presence_version_species_fkey 
        FOREIGN KEY (version_added, species) 
        REFERENCES database_versions (version, species);
    """)
    
    op.execute("""
        ALTER TABLE sequence_presence 
        ADD CONSTRAINT sequence_presence_version_species_fkey 
        FOREIGN KEY (version_added, species) 
        REFERENCES database_versions (version, species);
    """)


def downgrade() -> None:
    # This downgrade is complex as it would need to recreate the global versioning
    # For safety, we'll just raise an error if someone tries to downgrade
    raise NotImplementedError("Downgrade from species-specific versioning to global versioning is not supported. "
                            "This would require manual intervention to avoid data loss.")
