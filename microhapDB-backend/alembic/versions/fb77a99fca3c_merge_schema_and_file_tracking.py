"""merge_schema_and_file_tracking

Revision ID: fb77a99fca3c
Revises: 4c9472b80231, add_file_upload_tracking
Create Date: 2025-06-09 15:11:36.374059

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb77a99fca3c'
down_revision: Union[str, None] = ('4c9472b80231', 'add_file_upload_tracking')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
