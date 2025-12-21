"""audit logs

Revision ID: 0005_audit_logs
Revises: 0004_dev_api
Create Date: 2025-12-21

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "0005_audit_logs"
down_revision = "0004_dev_api"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("actor_type", sa.String(length=32), nullable=False),
            sa.Column("actor_id", sa.String(length=128), nullable=False),
            sa.Column("ip", sa.String(length=64), nullable=True),
            sa.Column("action", sa.String(length=64), nullable=False),
            sa.Column("target_type", sa.String(length=32), nullable=True),
            sa.Column("target_id", sa.String(length=128), nullable=True),
            sa.Column("detail_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("audit_logs"):
        op.drop_table("audit_logs")
