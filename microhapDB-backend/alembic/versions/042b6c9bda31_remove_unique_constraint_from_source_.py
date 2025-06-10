"""remove_unique_constraint_from_source_name

Revision ID: 042b6c9bda31
Revises: 23cb66a604b3
Create Date: 2025-03-12 11:44:22.390548

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '042b6c9bda31'
down_revision: Union[str, None] = '23cb66a604b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the unique constraint on the source name column
    op.drop_constraint('sources_name_key', 'sources', type_='unique')


def downgrade() -> None:
    # Re-add the unique constraint if needed to rollback
    op.create_unique_constraint('sources_name_key', 'sources', ['name'])
