"""preserve measurement device identity

Revision ID: de53ff9734c8
Revises: 0312360aa9d6
Create Date: 2026-11-05 22:55:03.394117

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de53ff9734c8'
down_revision: Union[str, Sequence[str], None] = '0312360aa9d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add the column, initially allowing NULL
    op.add_column(
        "measurements",
        sa.Column("device_id", sa.Integer(), nullable=True),
    )

    # 2. Populate existing records using sensor ownership
    op.execute("""
        UPDATE measurements AS m
        SET device_id = s.device_id
        FROM sensors AS s
        WHERE m.sensor_id = s.id
    """)

    # 3. Make the column mandatory
    op.alter_column(
        "measurements",
        "device_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # 4. Create a named foreign-key constraint
    op.create_foreign_key(
        "fk_measurements_device_id",
        "measurements",
        "devices",
        ["device_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_measurements_device_id",
        "measurements",
        type_="foreignkey",
    )

    op.drop_column("measurements", "device_id")