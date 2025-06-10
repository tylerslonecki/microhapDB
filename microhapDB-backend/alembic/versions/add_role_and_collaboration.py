"""add role and collaboration tables

Revision ID: add_role_and_collaboration
Revises: previous_revision
Create Date: 2024-03-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text, Enum

# revision identifiers, used by Alembic.
revision = 'add_role_and_collaboration'
down_revision = None  # Update this with your previous migration revision
branch_labels = None
depends_on = None

def upgrade():
    # This migration has been fixed in a later migration (1cd67418e0e8_fix_user_role_enum.py)
    # We're making this a no-op to avoid the "type user_role already exists" error
    pass

def downgrade():
    # This migration has been fixed in a later migration, so downgrade should be a no-op
    pass 