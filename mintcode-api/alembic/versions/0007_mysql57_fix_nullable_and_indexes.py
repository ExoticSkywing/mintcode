"""mysql 5.7 fix nullable legacy columns and add sha256 unique indexes

Revision ID: 0007_mysql57_fix
Revises: 0006_mysql57_safe
Create Date: 2025-12-21

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0007_mysql57_fix"
down_revision = "0006_mysql57_safe"
branch_labels = None
depends_on = None


def _has_index(bind: sa.Connection, table: str, index_name: str) -> bool:
    rows = bind.execute(sa.text(f"SHOW INDEX FROM `{table}`")).mappings().all()
    return any(str(r.get("Key_name")) == index_name for r in rows)


def _index_columns(bind: sa.Connection, table: str, index_name: str) -> list[str]:
    rows = bind.execute(sa.text(f"SHOW INDEX FROM `{table}`")).mappings().all()
    items = [r for r in rows if str(r.get("Key_name")) == index_name]
    items.sort(key=lambda r: int(r.get("Seq_in_index") or 0))
    return [str(r.get("Column_name")) for r in items]


def _drop_index_if_exists(bind: sa.Connection, table: str, index_name: str) -> None:
    if not _has_index(bind, table, index_name):
        return
    for sql in (
        f"ALTER TABLE `{table}` DROP INDEX `{index_name}`",
        f"DROP INDEX `{index_name}` ON `{table}`",
    ):
        try:
            op.execute(sa.text(sql))
            break
        except Exception:
            continue


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("developer_nonces"):
        cols = {c["name"] for c in insp.get_columns("developer_nonces")}
        if "nonce" in cols:
            op.alter_column(
                "developer_nonces",
                "nonce",
                existing_type=sa.String(length=128),
                nullable=True,
            )

        if "nonce_sha256" in cols:
            if not _has_index(bind, "developer_nonces", "uq_developer_nonces_key_ts_nonce_sha256"):
                op.execute(
                    sa.text(
                        "ALTER TABLE `developer_nonces` ADD UNIQUE INDEX `uq_developer_nonces_key_ts_nonce_sha256` (dev_key_id, ts, nonce_sha256)"
                    )
                )

    if insp.has_table("developer_idempotency_keys"):
        cols = {c["name"] for c in insp.get_columns("developer_idempotency_keys")}
        if "idempotency_key" in cols:
            op.alter_column(
                "developer_idempotency_keys",
                "idempotency_key",
                existing_type=sa.String(length=128),
                nullable=True,
            )

        if "idempotency_key_sha256" in cols:
            if not _has_index(bind, "developer_idempotency_keys", "uq_dev_idem_key_sha256"):
                op.execute(
                    sa.text(
                        "ALTER TABLE `developer_idempotency_keys` ADD UNIQUE INDEX `uq_dev_idem_key_sha256` (dev_key_id, idempotency_key_sha256)"
                    )
                )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("developer_nonces"):
        if _has_index(bind, "developer_nonces", "uq_developer_nonces_key_ts_nonce_sha256"):
            _drop_index_if_exists(bind, "developer_nonces", "uq_developer_nonces_key_ts_nonce_sha256")
        cols = {c["name"] for c in insp.get_columns("developer_nonces")}
        if "nonce" in cols:
            op.alter_column(
                "developer_nonces",
                "nonce",
                existing_type=sa.String(length=128),
                nullable=False,
            )

    if insp.has_table("developer_idempotency_keys"):
        if _has_index(bind, "developer_idempotency_keys", "uq_dev_idem_key_sha256"):
            _drop_index_if_exists(bind, "developer_idempotency_keys", "uq_dev_idem_key_sha256")
        cols = {c["name"] for c in insp.get_columns("developer_idempotency_keys")}
        if "idempotency_key" in cols:
            op.alter_column(
                "developer_idempotency_keys",
                "idempotency_key",
                existing_type=sa.String(length=128),
                nullable=False,
            )
