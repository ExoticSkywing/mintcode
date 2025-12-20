"""redeem task processing lease

Revision ID: 0002_processing_lease
Revises: 0001_baseline
Create Date: 2025-12-20

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_processing_lease"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("redeem_tasks")}
    if "processing_owner" not in cols:
        op.add_column("redeem_tasks", sa.Column("processing_owner", sa.String(length=64), nullable=True))
    if "processing_until" not in cols:
        op.add_column("redeem_tasks", sa.Column("processing_until", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("redeem_tasks", "processing_until")
    op.drop_column("redeem_tasks", "processing_owner")
