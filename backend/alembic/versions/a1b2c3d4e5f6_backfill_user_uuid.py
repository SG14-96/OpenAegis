"""backfill user_uuid

Revision ID: a1b2c3d4e5f6
Revises: 4e857695b655
Create Date: 2026-04-01 00:00:00.000000

"""
from typing import Sequence, Union

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '4e857695b655'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

users = table('users',
    column('id', sa.Integer),
    column('user_uuid', sa.String),
)


def upgrade() -> None:
    # Add as nullable first so existing rows don't violate the constraint
    op.add_column('users', sa.Column('user_uuid', sa.String(), nullable=True))
    op.create_index('ix_users_user_uuid', 'users', ['user_uuid'], unique=True)

    # Backfill each existing row with a unique uuid
    conn = op.get_bind()
    rows = conn.execute(sa.select(users.c.id)).fetchall()
    for (row_id,) in rows:
        conn.execute(
            users.update()
            .where(users.c.id == row_id)
            .values(user_uuid=str(uuid.uuid4()))
        )

    # Now enforce NOT NULL
    op.alter_column('users', 'user_uuid', nullable=False)


def downgrade() -> None:
    op.drop_index('ix_users_user_uuid', table_name='users')
    op.drop_column('users', 'user_uuid')
