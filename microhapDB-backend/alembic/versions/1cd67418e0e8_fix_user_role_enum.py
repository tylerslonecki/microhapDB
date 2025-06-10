"""fix_user_role_enum

Revision ID: 1cd67418e0e8
Revises: 042b6c9bda31
Create Date: 2025-03-12 12:02:45.845633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, Enum


# revision identifiers, used by Alembic.
revision: str = '1cd67418e0e8'
down_revision: Union[str, None] = '042b6c9bda31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This migration is a fix for the issue where the user_role enum type already exists
    # but the add_role_and_collaboration migration tries to create it again.
    
    # Check if the users table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # If users table doesn't exist, create it using the existing enum type
    if 'users' not in tables:
        # Create a SQLAlchemy Enum that references the existing PostgreSQL enum type
        user_role_enum = Enum('admin', 'private_user', 'collaborator', 'public',
                            name='user_role',
                            create_type=False)  # Don't create the type, it already exists
        
        # Create users table
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('orcid', sa.String(length=19), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('last_modified_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('role', user_role_enum, nullable=False, server_default='public'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('orcid')
        )
    
    # If collaborations table doesn't exist, create it
    if 'collaborations' not in tables:
        # Create collaborations table
        op.create_table(
            'collaborations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('collaborator_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('last_modified_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['collaborator_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'collaborator_id', name='uix_user_collaborator')
        )
        
        # Create index on collaborations
        op.create_index('ix_collaborations_user_id', 'collaborations', ['user_id'])
        op.create_index('ix_collaborations_collaborator_id', 'collaborations', ['collaborator_id'])


def downgrade() -> None:
    # This is a fix migration, so downgrade should be a no-op
    pass
