"""Link plugin_settings to alarm_settings

Revision ID: b1c2d3e4f5a6
Revises: 70da65da9f35
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = '70da65da9f35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('alarm_settings', sa.Column('alarm_name', sa.String(), nullable=False))
    op.create_unique_constraint('uq_alarm_settings_alarm_name', 'alarm_settings', ['alarm_name'])

    op.add_column('plugin_settings', sa.Column('alarm_settings_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_plugin_settings_alarm_settings_id',
        'plugin_settings', 'alarm_settings',
        ['alarm_settings_id'], ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('fk_plugin_settings_alarm_settings_id', 'plugin_settings', type_='foreignkey')
    op.drop_column('plugin_settings', 'alarm_settings_id')

    op.drop_constraint('uq_alarm_settings_alarm_name', 'alarm_settings', type_='unique')
    op.drop_column('alarm_settings', 'alarm_name')
