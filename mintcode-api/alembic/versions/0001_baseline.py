"""baseline

Revision ID: 0001_baseline
Revises:
Create Date: 2025-12-20

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "voucher_batches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sku_id", sa.String(length=64), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "vouchers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("sku_id", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["voucher_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_vouchers_code"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "redeem_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("voucher_id", sa.Integer(), nullable=False),
        sa.Column("sku_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result_code", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["voucher_id"], ["vouchers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("voucher_id", name="uq_redeem_tasks_voucher_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "sku_provider_config_histories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sku_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column("country", sa.String(length=64), nullable=False),
        sa.Column("operator", sa.String(length=64), nullable=False),
        sa.Column("product", sa.String(length=64), nullable=False),
        sa.Column("reuse", sa.Boolean(), nullable=False),
        sa.Column("voice", sa.Boolean(), nullable=False),
        sa.Column("poll_interval_seconds", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "sku_provider_config_successes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sku_id", sa.String(length=64), nullable=False),
        sa.Column("fingerprint", sa.String(length=40), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column("country", sa.String(length=64), nullable=False),
        sa.Column("operator", sa.String(length=64), nullable=False),
        sa.Column("product", sa.String(length=64), nullable=False),
        sa.Column("reuse", sa.Boolean(), nullable=False),
        sa.Column("voice", sa.Boolean(), nullable=False),
        sa.Column("poll_interval_seconds", sa.Integer(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("total_success_cost", sa.Numeric(12, 4), nullable=False),
        sa.Column("first_success_at", sa.DateTime(), nullable=False),
        sa.Column("last_success_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku_id", "fingerprint", name="uq_sku_provider_config_successes_sku_fp"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "sku_provider_configs",
        sa.Column("sku_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column("country", sa.String(length=64), nullable=False),
        sa.Column("operator", sa.String(length=64), nullable=False),
        sa.Column("product", sa.String(length=64), nullable=False),
        sa.Column("reuse", sa.Boolean(), nullable=False),
        sa.Column("voice", sa.Boolean(), nullable=False),
        sa.Column("poll_interval_seconds", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("sku_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "redeem_task_provider_states",
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("upstream_status", sa.String(length=64), nullable=True),
        sa.Column("price", sa.Numeric(12, 4), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("next_poll_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["redeem_tasks.id"]),
        sa.PrimaryKeyConstraint("task_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )


def downgrade() -> None:
    op.drop_table("redeem_task_provider_states")
    op.drop_table("sku_provider_configs")
    op.drop_table("sku_provider_config_successes")
    op.drop_table("sku_provider_config_histories")
    op.drop_table("redeem_tasks")
    op.drop_table("vouchers")
    op.drop_table("voucher_batches")
