"""add_role_column_to_users

Revision ID: 8af4d8da6e9f
Revises: 1cd67418e0e8
Create Date: 2025-03-12 12:05:21.268422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Enum, text


# revision identifiers, used by Alembic.
revision: str = '8af4d8da6e9f'
down_revision: Union[str, None] = '1cd67418e0e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if the users table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check if the users table exists
    tables = inspector.get_table_names()
    if 'users' not in tables:
        # If the users table doesn't exist, we don't need to do anything
        # The table will be created with the role column by the previous migration
        return
    
    # Check if the role column already exists
    columns = inspector.get_columns('users')
    column_names = [column['name'] for column in columns]
    
    if 'role' not in column_names:
        # Create a SQLAlchemy Enum that references the existing PostgreSQL enum type
        user_role_enum = Enum('admin', 'private_user', 'collaborator', 'public',
                            name='user_role',
                            create_type=False)  # Don't create the type, it already exists
        
        # Add the role column to the users table
        op.add_column('users', sa.Column('role', user_role_enum, nullable=False, server_default='public'))
        
        # Log that we've added the column
        print("Added 'role' column to 'users' table")


def downgrade() -> None:
    # Check if the users table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check if the users table exists
    tables = inspector.get_table_names()
    if 'users' not in tables:
        # If the users table doesn't exist, we don't need to do anything
        return
    
    # Check if the role column exists
    columns = inspector.get_columns('users')
    column_names = [column['name'] for column in columns]
    
    if 'role' in column_names:
        # Drop the role column
        op.drop_column('users', 'role')
        
        # Log that we've dropped the column
        print("Dropped 'role' column from 'users' table")
