"""rename_source_to_project_schema

Revision ID: 4c9472b80231
Revises: 0501d6d5ea5e
Create Date: 2025-01-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c9472b80231'
down_revision: Union[str, None] = '0501d6d5ea5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Rename 'sources' table to 'projects' and update all related references
    """
    
    # Step 1: Drop foreign key constraints that reference the sources table
    op.execute("ALTER TABLE program_source_association DROP CONSTRAINT IF EXISTS program_source_association_source_id_fkey;")
    
    # Step 2: Rename the sources table to projects
    op.execute("ALTER TABLE sources RENAME TO projects;")
    
    # Step 3: Rename the index on sources.id to projects.id
    op.execute("ALTER INDEX IF EXISTS ix_sources_id RENAME TO ix_projects_id;")
    
    # Step 4: Rename the association table and its constraints
    op.execute("ALTER TABLE program_source_association RENAME TO program_project_association;")
    
    # Step 5: Rename the columns in the association table
    op.execute("ALTER TABLE program_project_association RENAME COLUMN source_id TO project_id;")
    
    # Step 6: Rename the unique constraint in the association table
    op.execute("ALTER TABLE program_project_association RENAME CONSTRAINT uix_program_source TO uix_program_project;")
    
    # Step 7: Re-create the foreign key constraints with the new names
    op.execute("""
        ALTER TABLE program_project_association 
        ADD CONSTRAINT program_project_association_project_id_fkey 
        FOREIGN KEY (project_id) REFERENCES projects (id);
    """)
    
    # Step 8: Ensure the foreign key constraint to programs table still exists
    op.execute("""
        ALTER TABLE program_project_association 
        ADD CONSTRAINT program_project_association_program_id_fkey 
        FOREIGN KEY (program_id) REFERENCES programs (id);
    """)


def downgrade() -> None:
    """
    Revert the changes: rename 'projects' table back to 'sources'
    """
    
    # Step 1: Drop foreign key constraints
    op.execute("ALTER TABLE program_project_association DROP CONSTRAINT IF EXISTS program_project_association_project_id_fkey;")
    op.execute("ALTER TABLE program_project_association DROP CONSTRAINT IF EXISTS program_project_association_program_id_fkey;")
    
    # Step 2: Rename the association table back
    op.execute("ALTER TABLE program_project_association RENAME TO program_source_association;")
    
    # Step 3: Rename the column back
    op.execute("ALTER TABLE program_source_association RENAME COLUMN project_id TO source_id;")
    
    # Step 4: Rename the unique constraint back
    op.execute("ALTER TABLE program_source_association RENAME CONSTRAINT uix_program_project TO uix_program_source;")
    
    # Step 5: Rename the projects table back to sources
    op.execute("ALTER TABLE projects RENAME TO sources;")
    
    # Step 6: Rename the index back
    op.execute("ALTER INDEX IF EXISTS ix_projects_id RENAME TO ix_sources_id;")
    
    # Step 7: Re-create the original foreign key constraints
    op.execute("""
        ALTER TABLE program_source_association 
        ADD CONSTRAINT program_source_association_source_id_fkey 
        FOREIGN KEY (source_id) REFERENCES sources (id);
    """)
    
    op.execute("""
        ALTER TABLE program_source_association 
        ADD CONSTRAINT program_source_association_program_id_fkey 
        FOREIGN KEY (program_id) REFERENCES programs (id);
    """)
