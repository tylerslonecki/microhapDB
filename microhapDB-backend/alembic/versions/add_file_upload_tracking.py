"""Add file upload tracking table

Revision ID: add_file_upload_tracking
Revises: 0501d6d5ea5e
Create Date: 2025-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_file_upload_tracking'
down_revision: Union[str, None] = '0501d6d5ea5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the file_uploads table to track uploaded files and their associated database versions
    op.create_table('file_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('upload_type', sa.String(), nullable=False),  # 'madc', 'pav', 'supplemental'
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('upload_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('species', sa.String(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=False),
        sa.Column('project_name', sa.String(), nullable=True),  # Only for MADC uploads
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('job_id', sa.String(), nullable=True),  # Reference to background job
        sa.ForeignKeyConstraint(['version', 'species'], ['database_versions.version', 'database_versions.species']),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id']),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('idx_file_uploads_version_species', 'file_uploads', ['version', 'species'])
    op.create_index('idx_file_uploads_upload_date', 'file_uploads', ['upload_date'])
    op.create_index('idx_file_uploads_upload_type', 'file_uploads', ['upload_type'])
    op.create_index('idx_file_uploads_program_id', 'file_uploads', ['program_id'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_file_uploads_program_id', table_name='file_uploads')
    op.drop_index('idx_file_uploads_upload_type', table_name='file_uploads')
    op.drop_index('idx_file_uploads_upload_date', table_name='file_uploads')
    op.drop_index('idx_file_uploads_version_species', table_name='file_uploads')
    
    # Drop the table
    op.drop_table('file_uploads') 