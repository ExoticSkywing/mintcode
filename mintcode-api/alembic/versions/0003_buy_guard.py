"""buy guard fields

Revision ID: 0003_buy_guard
Revises: 0002_processing_lease
Create Date: 2025-12-20

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_buy_guard"
down_revision = "0002_processing_lease"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("redeem_task_provider_states")}
    if "buy_attempts" not in cols:
        op.add_column(
            "redeem_task_provider_states",
            sa.Column("buy_attempts", sa.Integer(), nullable=False, server_default="0"),
        )
    if "last_buy_attempt_at" not in cols:
        op.add_column(
            "redeem_task_provider_states",
            sa.Column("last_buy_attempt_at", sa.DateTime(), nullable=True),
        )
    if "buy_inflight_until" not in cols:
        op.add_column(
            "redeem_task_provider_states",
            sa.Column("buy_inflight_until", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("redeem_task_provider_states")}
    if "buy_inflight_until" in cols:
        op.drop_column("redeem_task_provider_states", "buy_inflight_until")
    if "last_buy_attempt_at" in cols:
        op.drop_column("redeem_task_provider_states", "last_buy_attempt_at")
    if "buy_attempts" in cols:
        op.drop_column("redeem_task_provider_states", "buy_attempts")
