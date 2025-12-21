"""mysql 5.7 safe dev key uniqueness

Revision ID: 0006_mysql57_safe
Revises: 0005_audit_logs
Create Date: 2025-12-21

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0006_mysql57_safe"
down_revision = "0005_audit_logs"
branch_labels = None
depends_on = None


def _has_index(insp: sa.Inspector, table: str, index_name: str) -> bool:
    try:
        bind = insp.bind
        if bind is None:
            return False
        rows = bind.execute(sa.text(f"SHOW INDEX FROM `{table}`")).mappings().all()
        return any(str(r.get("Key_name")) == index_name for r in rows)
    except Exception:
        return False


def _mysql_indexes(bind: sa.Connection, table: str) -> list[dict[str, object]]:
    rows = bind.execute(sa.text(f"SHOW INDEX FROM `{table}`")).mappings().all()
    return [dict(r) for r in rows]


def _drop_index_if_exists(bind: sa.Connection, table: str, index_name: str) -> None:
    idxs = _mysql_indexes(bind, table)
    if any(str(r.get("Key_name")) == index_name for r in idxs):
        for sql in (
            f"ALTER TABLE `{table}` DROP INDEX `{index_name}`",
            f"DROP INDEX `{index_name}` ON `{table}`",
        ):
            try:
                op.execute(sa.text(sql))
                break
            except Exception:
                continue


def _index_columns(bind: sa.Connection, table: str, index_name: str) -> list[str]:
    idxs = _mysql_indexes(bind, table)
    items = [r for r in idxs if str(r.get("Key_name")) == index_name]
    items.sort(key=lambda r: int(r.get("Seq_in_index") or 0))
    return [str(r.get("Column_name")) for r in items]


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("developer_nonces"):
        cols = {c["name"] for c in insp.get_columns("developer_nonces")}
        if "nonce_sha256" not in cols:
            op.add_column("developer_nonces", sa.Column("nonce_sha256", sa.String(length=64), nullable=True))
        if "nonce_raw" not in cols:
            op.add_column("developer_nonces", sa.Column("nonce_raw", sa.String(length=256), nullable=True))

        cols = {c["name"] for c in insp.get_columns("developer_nonces")}
        has_nonce = "nonce" in cols
        if has_nonce:
            op.execute(
                "UPDATE developer_nonces SET nonce_raw = nonce WHERE nonce_raw IS NULL AND nonce IS NOT NULL"
            )

        op.execute(
            "UPDATE developer_nonces SET nonce_sha256 = SHA2(COALESCE(nonce_raw" + (", nonce" if has_nonce else "") + ", ''), 256) "
            "WHERE nonce_sha256 IS NULL"
        )

        op.execute(
            "DELETE dn1 FROM developer_nonces dn1 "
            "JOIN developer_nonces dn2 "
            "ON dn1.dev_key_id=dn2.dev_key_id AND dn1.ts=dn2.ts AND dn1.nonce_sha256=dn2.nonce_sha256 "
            "AND dn1.id > dn2.id"
        )

        desired = ["dev_key_id", "ts", "nonce_sha256"]
        existing_cols = _index_columns(bind, "developer_nonces", "uq_developer_nonces_key_ts_nonce")
        if existing_cols and existing_cols != desired:
            _drop_index_if_exists(bind, "developer_nonces", "uq_developer_nonces_key_ts_nonce")
            existing_cols = _index_columns(bind, "developer_nonces", "uq_developer_nonces_key_ts_nonce")
        if not existing_cols:
            op.execute(
                sa.text(
                    "ALTER TABLE `developer_nonces` ADD UNIQUE INDEX `uq_developer_nonces_key_ts_nonce` (dev_key_id, ts, nonce_sha256)"
                )
            )

        op.alter_column(
            "developer_nonces",
            "nonce_sha256",
            existing_type=sa.String(length=64),
            nullable=False,
        )

    if insp.has_table("developer_idempotency_keys"):
        cols = {c["name"] for c in insp.get_columns("developer_idempotency_keys")}
        if "idempotency_key_sha256" not in cols:
            op.add_column(
                "developer_idempotency_keys",
                sa.Column("idempotency_key_sha256", sa.String(length=64), nullable=True),
            )
        if "idempotency_key_raw" not in cols:
            op.add_column(
                "developer_idempotency_keys",
                sa.Column("idempotency_key_raw", sa.String(length=256), nullable=True),
            )

        cols = {c["name"] for c in insp.get_columns("developer_idempotency_keys")}
        has_idem = "idempotency_key" in cols
        if has_idem:
            op.execute(
                "UPDATE developer_idempotency_keys SET idempotency_key_raw = idempotency_key "
                "WHERE idempotency_key_raw IS NULL AND idempotency_key IS NOT NULL"
            )

        op.execute(
            "UPDATE developer_idempotency_keys SET idempotency_key_sha256 = SHA2(COALESCE(idempotency_key_raw" + (", idempotency_key" if has_idem else "") + ", ''), 256) "
            "WHERE idempotency_key_sha256 IS NULL"
        )

        op.execute(
            "DELETE d1 FROM developer_idempotency_keys d1 "
            "JOIN developer_idempotency_keys d2 "
            "ON d1.dev_key_id=d2.dev_key_id AND d1.idempotency_key_sha256=d2.idempotency_key_sha256 "
            "AND d1.id > d2.id"
        )

        desired = ["dev_key_id", "idempotency_key_sha256"]
        existing_cols = _index_columns(bind, "developer_idempotency_keys", "uq_dev_idem_key")
        if existing_cols and existing_cols != desired:
            _drop_index_if_exists(bind, "developer_idempotency_keys", "uq_dev_idem_key")
            existing_cols = _index_columns(bind, "developer_idempotency_keys", "uq_dev_idem_key")
        if not existing_cols:
            op.execute(
                sa.text(
                    "ALTER TABLE `developer_idempotency_keys` ADD UNIQUE INDEX `uq_dev_idem_key` (dev_key_id, idempotency_key_sha256)"
                )
            )

        op.alter_column(
            "developer_idempotency_keys",
            "idempotency_key_sha256",
            existing_type=sa.String(length=64),
            nullable=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("developer_nonces"):
        cols = {c["name"] for c in insp.get_columns("developer_nonces")}
        if "nonce" not in cols:
            op.add_column("developer_nonces", sa.Column("nonce", sa.String(length=128), nullable=True))
        cols = {c["name"] for c in insp.get_columns("developer_nonces")}
        if "nonce_raw" in cols:
            op.execute("UPDATE developer_nonces SET nonce = nonce_raw WHERE nonce IS NULL")

        try:
            uniqs = {u.get("name") for u in insp.get_unique_constraints("developer_nonces")}
        except Exception:
            uniqs = set()
        if "uq_developer_nonces_key_ts_nonce" in uniqs:
            op.drop_constraint("uq_developer_nonces_key_ts_nonce", "developer_nonces", type_="unique")
        op.create_unique_constraint(
            "uq_developer_nonces_key_ts_nonce",
            "developer_nonces",
            ["dev_key_id", "ts", "nonce"],
        )

        cols = {c["name"] for c in insp.get_columns("developer_nonces")}
        if "nonce_sha256" in cols:
            op.drop_column("developer_nonces", "nonce_sha256")
        if "nonce_raw" in cols:
            op.drop_column("developer_nonces", "nonce_raw")

    if insp.has_table("developer_idempotency_keys"):
        cols = {c["name"] for c in insp.get_columns("developer_idempotency_keys")}
        if "idempotency_key" not in cols:
            op.add_column("developer_idempotency_keys", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
        cols = {c["name"] for c in insp.get_columns("developer_idempotency_keys")}
        if "idempotency_key_raw" in cols:
            op.execute("UPDATE developer_idempotency_keys SET idempotency_key = idempotency_key_raw WHERE idempotency_key IS NULL")

        try:
            uniqs = {u.get("name") for u in insp.get_unique_constraints("developer_idempotency_keys")}
        except Exception:
            uniqs = set()
        if "uq_dev_idem_key" in uniqs:
            op.drop_constraint("uq_dev_idem_key", "developer_idempotency_keys", type_="unique")
        op.create_unique_constraint(
            "uq_dev_idem_key",
            "developer_idempotency_keys",
            ["dev_key_id", "idempotency_key"],
        )

        cols = {c["name"] for c in insp.get_columns("developer_idempotency_keys")}
        if "idempotency_key_sha256" in cols:
            op.drop_column("developer_idempotency_keys", "idempotency_key_sha256")
        if "idempotency_key_raw" in cols:
            op.drop_column("developer_idempotency_keys", "idempotency_key_raw")
