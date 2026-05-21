"""add duplicate check to flow

Revision ID: 6e7a8b9c0d1e
Revises: 8b5ea8075af7
Create Date: 2026-05-19 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '6e7a8b9c0d1e'
down_revision: Union[str, Sequence[str], None] = '8b5ea8075af7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('flows', sa.Column('duplicate_check', sa.Boolean(), nullable=True, server_default='0'))

def downgrade() -> None:
    op.drop_column('flows', 'duplicate_check')