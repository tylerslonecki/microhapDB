"""merge role and collaboration with initial migration

Revision ID: 23cb66a604b3
Revises: 26baaf267e89, add_role_and_collaboration
Create Date: 2025-03-07 11:23:52.720650

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23cb66a604b3'
down_revision: Union[str, None] = ('26baaf267e89', 'add_role_and_collaboration')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
