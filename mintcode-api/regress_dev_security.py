from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request


REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
COMPOSE_FILE = os.path.join(REPO_ROOT, "docker-compose.dev.yml")
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


def _compose(*args: str, env: dict[str, str]) -> str:
    return _run(["docker", "compose", "-f", COMPOSE_FILE, *args], env=env)


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


def _b64_hmac_sha256(secret: str, msg: str) -> str:
    sig = hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(sig).decode("ascii")


def _body_sha256_hex(body_bytes: bytes) -> str:
    return hashlib.sha256(body_bytes).hexdigest()


def _canonical_string(method: str, path: str, query: str, ts: str, nonce: str, body_sha256: str) -> str:
    return "\n".join([method.upper(), path, query or "", ts, nonce, body_sha256])


def _dev_headers(
    *,
    dev_key_id: str,
    dev_secret: str,
    method: str,
    path: str,
    query: str,
    ts: int,
    nonce: str,
    body: dict | None,
    idempotency_key: str | None = None,
) -> dict[str, str]:
    body_bytes = b""
    if body is not None:
        body_bytes = json.dumps(body).encode("utf-8")
    body_sha = _body_sha256_hex(body_bytes)
    canonical = _canonical_string(method, path, query, str(ts), nonce, body_sha)
    sig = _b64_hmac_sha256(dev_secret, canonical)
    h = {
        "X-Dev-Key-Id": dev_key_id,
        "X-Dev-Timestamp": str(ts),
        "X-Dev-Nonce": nonce,
        "X-Dev-Signature": sig,
    }
    if idempotency_key:
        h["Idempotency-Key"] = idempotency_key
    return h


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _env_defaults() -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("ADMIN_API_KEY", "change-me")
    env.setdefault("VOUCHER_SECRET", "change-me-too")
    env.setdefault("FIVESIM_API_KEY", "dummy")
    env.setdefault("DB_AUTO_CREATE_TABLES", "false")
    env.setdefault("REDEEM_PROCESS_MODE", "external")
    return env


def main() -> int:
    env = _env_defaults()
    cleanup = os.environ.get("REGRESS_CLEANUP", "0") == "1"

    try:
        if cleanup:
            try:
                _compose("down", "-v", env=env)
            except Exception:
                pass

        _compose("up", "-d", "--build", "mysql", "api", env=env)
        _compose("exec", "-T", "api", "sh", "-lc", "alembic upgrade head", env=env)

        admin_headers = {"X-Admin-Key": env["ADMIN_API_KEY"]}

        st, out = _http_json("POST", "/admin/dev-keys", {"name": "regress_dev_security"}, admin_headers)
        _assert(st == 200, f"create_dev_key_failed status={st} body={out}")
        dk = json.loads(out)
        dev_key_id = str(dk["dev_key_id"])
        dev_secret = str(dk["dev_key_secret"])

        sku_id = f"reg_sku_{int(time.time())}"
        st, out = _http_json(
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
        _assert(st == 200, f"sku_config_failed status={st} body={out}")

        st, txt = _http_json("POST", "/admin/vouchers/generate", {"sku_id": sku_id, "count": 2, "length": 12}, admin_headers)
        _assert(st == 200, f"voucher_generate_failed status={st} body={txt}")
        vouchers = [x for x in txt.strip().splitlines() if x.strip()]
        _assert(len(vouchers) >= 2, f"voucher_generate_insufficient {vouchers}")
        v1, v2 = vouchers[0], vouchers[1]

        path = "/dev/redeem"
        ts = int(time.time())
        nonce = "n1_" + str(int(time.time() * 1000))
        body = {"voucher": v1}
        headers = _dev_headers(
            dev_key_id=dev_key_id,
            dev_secret=dev_secret,
            method="POST",
            path=path,
            query="",
            ts=ts,
            nonce=nonce,
            body=body,
            idempotency_key="idem_a",
        )
        st1, out1 = _http_json("POST", path, body, headers)
        _assert(st1 == 200, f"dev_redeem_create_failed status={st1} body={out1}")
        r1 = json.loads(out1)
        task_id = str(r1.get("task_id") or "")
        _assert(task_id.startswith("t_"), f"public_task_id_invalid {task_id}")

        nonce2 = "n2_" + str(int(time.time() * 1000))
        headers2 = _dev_headers(
            dev_key_id=dev_key_id,
            dev_secret=dev_secret,
            method="POST",
            path=path,
            query="",
            ts=ts,
            nonce=nonce2,
            body=body,
            idempotency_key="idem_a",
        )
        st2, out2 = _http_json("POST", path, body, headers2)
        _assert(st2 == 200, f"dev_redeem_idempotency_failed status={st2} body={out2}")
        r2 = json.loads(out2)
        _assert(str(r2.get("task_id")) == task_id, f"idempotency_not_same_task {task_id} {r2}")

        nonce3 = "n3_" + str(int(time.time() * 1000))
        headers3 = _dev_headers(
            dev_key_id=dev_key_id,
            dev_secret=dev_secret,
            method="POST",
            path=path,
            query="",
            ts=ts,
            nonce=nonce3,
            body={"voucher": v2},
            idempotency_key="idem_a",
        )
        st3, out3 = _http_json("POST", path, {"voucher": v2}, headers3)
        _assert(st3 == 409, f"idempotency_conflict_expected_409 got={st3} body={out3}")
        _assert("IDEMPOTENCY_KEY_CONFLICT" in out3, f"idempotency_conflict_detail_missing {out3}")

        nonce_replay = "nr_" + str(int(time.time() * 1000))
        headers_nr = _dev_headers(
            dev_key_id=dev_key_id,
            dev_secret=dev_secret,
            method="GET",
            path=f"/dev/redeem/{task_id}",
            query="",
            ts=ts,
            nonce=nonce_replay,
            body=None,
        )
        stg1, _ = _http_json("GET", f"/dev/redeem/{task_id}", None, headers_nr)
        _assert(stg1 == 200, f"dev_redeem_get_failed status={stg1}")
        stg2, outg2 = _http_json("GET", f"/dev/redeem/{task_id}", None, headers_nr)
        _assert(stg2 == 401, f"nonce_replay_expected_401 got={stg2} body={outg2}")
        _assert("DEV_AUTH_NONCE_REPLAY" in outg2, f"nonce_replay_detail_missing {outg2}")

        st, out = _http_json("POST", "/admin/dev-keys", {"name": "regress_dev_security_rl"}, admin_headers)
        _assert(st == 200, f"create_dev_key_rl_failed status={st} body={out}")
        dk_rl = json.loads(out)
        dev_key_id_rl = str(dk_rl["dev_key_id"])
        dev_secret_rl = str(dk_rl["dev_key_secret"])

        rate_limit_ts = int(time.time())
        rate_limit_path = f"/dev/redeem/{task_id}"
        ok = 0
        blocked = 0
        for i in range(0, 70):
            n = f"rl_{rate_limit_ts}_{i}_{int(time.time() * 1000)}"
            h = _dev_headers(
                dev_key_id=dev_key_id_rl,
                dev_secret=dev_secret_rl,
                method="GET",
                path=rate_limit_path,
                query="",
                ts=rate_limit_ts,
                nonce=n,
                body=None,
            )
            stx, outx = _http_json("GET", rate_limit_path, None, h)
            if stx == 200:
                ok += 1
                continue
            if stx == 429:
                blocked += 1
                _assert("DEV_RATE_LIMITED" in outx, f"rate_limit_detail_missing {outx}")
                break
            raise AssertionError(f"rate_limit_unexpected_status={stx} body={outx}")

        _assert(ok >= 60, f"rate_limit_ok_too_low ok={ok}")
        _assert(blocked >= 1, f"rate_limit_not_triggered ok={ok} blocked={blocked}")

        print("OK")
        print(json.dumps({"dev_key_id": dev_key_id, "task_id": task_id, "rate_limit_ok": ok}, ensure_ascii=False))
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
