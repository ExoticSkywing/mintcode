from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMPOSE_FILE = os.path.join(os.path.dirname(__file__), "docker-compose.dev.yml")
BASE_URL = "http://127.0.0.1:8123"


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> str:
    p = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if p.returncode != 0:
        raise RuntimeError(f"command_failed rc={p.returncode} cmd={' '.join(cmd)}\n{p.stdout}")
    return p.stdout


def _http_json(method: str, path: str, body: dict | None, headers: dict[str, str]) -> tuple[int, str]:
    data = None
    h = dict(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE_URL + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def _compose_env_overrides() -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("ADMIN_API_KEY", "change-me")
    env.setdefault("VOUCHER_SECRET", "change-me-too")
    env.setdefault("FIVESIM_API_KEY", "dummy")
    env.setdefault("WORKER_LEASE_SECONDS", "3")
    env.setdefault("BUY_INFLIGHT_SECONDS", "30")
    env.setdefault("MAX_BUY_ATTEMPTS", "3")
    env.setdefault("DB_AUTO_CREATE_TABLES", "false")
    env.setdefault("WORKER_ID", "")
    return env


def _compose(*args: str, env: dict[str, str]) -> str:
    return _run(["docker", "compose", "-f", COMPOSE_FILE, *args], env=env)


def _worker_container_id(env: dict[str, str]) -> str:
    out = _compose("ps", "-q", "worker", env=env).strip()
    if not out:
        raise RuntimeError("worker_container_not_found")
    return out


def _container_state(container_id: str) -> dict:
    out = _run(["docker", "inspect", container_id])
    arr = json.loads(out)
    if not arr:
        return {}
    return arr[0].get("State", {})


def _exec_db(env: dict[str, str], sql: str) -> list[dict]:
    py = (
        "from sqlalchemy import text\n"
        "from mintcode_api.db import SessionLocal\n"
        "db=SessionLocal()\n"
        "try:\n"
        "    res=db.execute(text(\"" + sql.replace("\\", "\\\\").replace('"', '\\"') + "\"))\n"
        "    try:\n"
        "        rows=res.mappings().all()\n"
        "    except Exception:\n"
        "        rows=[]\n"
        "    db.commit()\n"
        "    import json\n"
        "    print(json.dumps([dict(r) for r in rows], default=str))\n"
        "finally:\n"
        "    db.close()\n"
    )
    out = _compose("exec", "-T", "api", "python", "-c", py, env=env)
    return json.loads(out.strip() or "[]")


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    env = _compose_env_overrides()
    cleanup = os.environ.get("REGRESS_CLEANUP", "0") == "1"
    try:
        if cleanup:
            try:
                _compose("down", "-v", env=env)
            except Exception:
                pass

        _compose("up", "-d", "--build", "mysql", "api", env=env)
        _compose("exec", "-T", "api", "sh", "-lc", "alembic upgrade head", env=env)

        _exec_db(
            env,
            "UPDATE redeem_tasks SET status='DONE', processing_owner=NULL, processing_until=NULL "
            "WHERE status IN ('PENDING','WAITING_SMS','PROCESSING','CODE_READY')",
        )

        admin_headers = {"X-Admin-Key": env["ADMIN_API_KEY"]}

        sku_id = f"reg_sku_{int(time.time())}"
        st, _ = _http_json(
            "PUT",
            f"/admin/sku/{sku_id}/provider-config",
            {
                "provider": "fivesim",
                "category": "activation",
                "country": "invalidcountry",
                "operator": "any",
                "product": "telegram",
                "reuse": False,
                "voice": False,
                "poll_interval_seconds": 1,
            },
            admin_headers,
        )
        _assert(st == 200, f"sku_config_failed status={st}")

        st, txt = _http_json(
            "POST",
            "/admin/vouchers/generate",
            {"sku_id": sku_id, "count": 1, "length": 12},
            admin_headers,
        )
        _assert(st == 200, f"voucher_generate_failed status={st} body={txt}")
        voucher = txt.strip().splitlines()[0]

        env_crash = dict(env)
        env_crash["WORKER_CRASH_AFTER_BUY_GUARD_COMMIT"] = "1"
        _compose("up", "-d", "--no-deps", "--force-recreate", "worker", env=env_crash)

        st, out = _http_json("POST", "/redeem", {"code": voucher}, {})
        _assert(st == 200, f"redeem_create_failed status={st} body={out}")
        task = json.loads(out)
        task_id = int(task["task_id"])

        cid = _worker_container_id(env_crash)
        deadline = time.time() + 30
        exit_code = None
        while time.time() < deadline:
            state = _container_state(cid)
            if not state:
                time.sleep(0.5)
                continue
            if not state.get("Running", True):
                exit_code = int(state.get("ExitCode", -1))
                break
            time.sleep(0.5)
        _assert(exit_code == 99, f"worker_did_not_crash exit_code={exit_code}")

        rows = _exec_db(
            env,
            f"SELECT status, processing_until, processing_owner FROM redeem_tasks WHERE id={task_id}",
        )
        _assert(rows and rows[0]["status"] == "PROCESSING", f"unexpected_task_status {rows}")

        st_rows = _exec_db(
            env,
            "SELECT buy_attempts, buy_inflight_until, order_id FROM redeem_task_provider_states WHERE task_id="
            + str(task_id),
        )
        _assert(st_rows and int(st_rows[0]["buy_attempts"]) == 1, f"unexpected_buy_attempts_after_crash {st_rows}")
        _assert(st_rows[0]["order_id"] is None, f"order_id_should_be_null {st_rows}")

        env_nocrash = dict(env)
        env_nocrash["WORKER_CRASH_AFTER_BUY_GUARD_COMMIT"] = "0"
        _compose("up", "-d", "--no-deps", "--force-recreate", "worker", env=env_nocrash)

        time.sleep(float(env["WORKER_LEASE_SECONDS"]) + 1.0)

        st_rows2 = _exec_db(
            env,
            "SELECT buy_attempts, buy_inflight_until, order_id, next_poll_at, last_error FROM redeem_task_provider_states WHERE task_id="
            + str(task_id),
        )
        _assert(int(st_rows2[0]["buy_attempts"]) == 1, f"buy_attempts_changed_within_inflight {st_rows2}")

        rows2 = _exec_db(env, f"SELECT status, processing_until, processing_owner FROM redeem_tasks WHERE id={task_id}")
        _assert(rows2 and rows2[0]["status"] in ("WAITING_SMS", "PROCESSING"), f"unexpected_task_status_2 {rows2}")

        time.sleep(float(env["BUY_INFLIGHT_SECONDS"]) + 2.0)

        st_rows3 = _exec_db(
            env,
            "SELECT buy_attempts, order_id, last_error FROM redeem_task_provider_states WHERE task_id=" + str(task_id),
        )
        _assert(int(st_rows3[0]["buy_attempts"]) >= 2, f"buy_attempts_did_not_increment_after_inflight {st_rows3}")

        print("OK")
        print(
            json.dumps(
                {
                    "task_id": task_id,
                    "buy_attempts": int(st_rows3[0]["buy_attempts"]),
                    "worker_crash_exit_code": exit_code,
                },
                ensure_ascii=False,
            )
        )
        return 0
    finally:
        if cleanup:
            try:
                _compose("down", "-v", env=env)
            except Exception:
                pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(str(e), file=sys.stderr)
        raise
