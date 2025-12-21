"""developer api security

Revision ID: 0004_dev_api
Revises: 0003_buy_guard
Create Date: 2025-12-21

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "0004_dev_api"
down_revision = "0003_buy_guard"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # redeem_tasks.public_id
    redeem_cols = {c["name"] for c in insp.get_columns("redeem_tasks")}
    if "public_id" not in redeem_cols:
        op.add_column("redeem_tasks", sa.Column("public_id", sa.String(length=64), nullable=True))

    try:
        uniqs = {u.get("name") for u in insp.get_unique_constraints("redeem_tasks")}
    except Exception:
        uniqs = set()
    if "uq_redeem_tasks_public_id" not in uniqs:
        op.create_unique_constraint("uq_redeem_tasks_public_id", "redeem_tasks", ["public_id"])

    # developer_keys
    if not insp.has_table("developer_keys"):
        op.create_table(
            "developer_keys",
            sa.Column("dev_key_id", sa.String(length=64), primary_key=True),
            sa.Column("dev_key_secret", sa.String(length=128), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("name", sa.String(length=128), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    # developer_nonces
    if not insp.has_table("developer_nonces"):
        op.create_table(
            "developer_nonces",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("dev_key_id", sa.String(length=64), nullable=False),
            sa.Column("ts", sa.Integer(), nullable=False),
            sa.Column("nonce", sa.String(length=128), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["dev_key_id"], ["developer_keys.dev_key_id"]),
            sa.UniqueConstraint("dev_key_id", "ts", "nonce", name="uq_developer_nonces_key_ts_nonce"),
        )

    # developer_rate_limits
    if not insp.has_table("developer_rate_limits"):
        op.create_table(
            "developer_rate_limits",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("scope", sa.String(length=32), nullable=False),
            sa.Column("scope_id", sa.String(length=128), nullable=False),
            sa.Column("window_start_ts", sa.Integer(), nullable=False),
            sa.Column("count", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint(
                "scope",
                "scope_id",
                "window_start_ts",
                name="uq_developer_rate_limits_scope_window",
            ),
        )

    # developer_idempotency_keys
    if not insp.has_table("developer_idempotency_keys"):
        op.create_table(
            "developer_idempotency_keys",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("dev_key_id", sa.String(length=64), nullable=False),
            sa.Column("idempotency_key", sa.String(length=128), nullable=False),
            sa.Column("request_sha256", sa.String(length=64), nullable=False),
            sa.Column("task_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["dev_key_id"], ["developer_keys.dev_key_id"]),
            sa.ForeignKeyConstraint(["task_id"], ["redeem_tasks.id"]),
            sa.UniqueConstraint("dev_key_id", "idempotency_key", name="uq_dev_idem_key"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("developer_idempotency_keys"):
        op.drop_table("developer_idempotency_keys")
    if insp.has_table("developer_rate_limits"):
        op.drop_table("developer_rate_limits")
    if insp.has_table("developer_nonces"):
        op.drop_table("developer_nonces")
    if insp.has_table("developer_keys"):
        op.drop_table("developer_keys")

    cols = {c["name"] for c in insp.get_columns("redeem_tasks")}
    if "public_id" in cols:
        # best-effort: drop constraint then column
        try:
            op.drop_constraint("uq_redeem_tasks_public_id", "redeem_tasks", type_="unique")
        except Exception:
            pass
        op.drop_column("redeem_tasks", "public_id")
