"""preserve measurement metric

Revision ID: 84a48e80c794
Revises: de53ff9734c8
Create Date: 2026-11-05 23:30:20.931524

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84a48e80c794'
down_revision: Union[str, Sequence[str], None] = 'de53ff9734c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    # 1. Add metric as nullable
    op.add_column(
        "measurements",
        sa.Column("metric", sa.String(length=50), nullable=True),
    )

    # 2. Backfill existing measurements
    op.execute("""
        UPDATE measurements AS m
        SET metric = s.metric
        FROM sensors AS s
        WHERE m.sensor_id = s.id
    """)

    # 3. Require metric for future measurements
    op.alter_column(
        "measurements",
        "metric",
        existing_type=sa.String(length=50),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("measurements", "metric")