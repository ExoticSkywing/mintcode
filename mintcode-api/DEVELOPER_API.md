# MintCode Developer API (External Mode)

This document describes the **Developer API** for programmatic SMS-number redemption.

Principles:

- Voucher-first: **`voucher` is the only user-facing credential**.
- SKU is hidden: voucher is pre-bound to a fixed provider config on the server.
- Completion boundary: **once a code is delivered, the service is completed and the voucher is consumed**.
- Cost safety:
  - Same voucher allows **only 1 active task at a time**.
  - `cancel` is allowed **only before code is delivered**.

---

## 1. Terminology

- **Voucher**: the redeem credential (卡密). Without a voucher, nothing can be started.
- **Redeem Task**: server-side state machine representing one redemption attempt.
- **Public Task ID**: the task identifier exposed to developers, **non-guessable**, format `t_<random>`.

---

## 2. Authentication (HMAC + timestamp + nonce)

Every request to the Developer API must be signed.

### 2.1 Credentials

You will be issued:

- `dev_key_id` (public)
- `dev_key_secret` (private, keep it safe)

### 2.2 Required headers

- `X-Dev-Key-Id`: your `dev_key_id`
- `X-Dev-Timestamp`: Unix timestamp **in seconds**
- `X-Dev-Nonce`: random string (recommend 16+ chars)
- `X-Dev-Signature`: signature string (Base64)

### 2.3 Timestamp window

Server will reject requests if:

- `abs(server_now_seconds - X-Dev-Timestamp) > 300`

### 2.4 Replay protection

Server will reject requests if the tuple below is reused within the accepted time window:

- `(X-Dev-Key-Id, X-Dev-Timestamp, X-Dev-Nonce)`

### 2.5 Canonical string

Build a canonical string using **exactly** the following fields:

- `METHOD`: uppercase HTTP method
- `PATH`: request path (e.g. `/dev/redeem/t_xxx/wait`), without scheme/host
- `QUERY`: raw query string without leading `?` (empty if none)
- `TIMESTAMP`: `X-Dev-Timestamp`
- `NONCE`: `X-Dev-Nonce`
- `BODY_SHA256`: sha256 hex of request body bytes; for requests without body use sha256 of empty bytes

Canonical format:

```
METHOD\nPATH\nQUERY\nTIMESTAMP\nNONCE\nBODY_SHA256
```

### 2.6 Signature

- `signature_bytes = HMAC-SHA256(dev_key_secret, canonical_string_bytes)`
- `X-Dev-Signature = Base64(signature_bytes)`

---

## 3. Idempotency

### 3.1 `POST /dev/redeem`

For creating a redeem task, you should provide:

- `Idempotency-Key`: a unique string for this client operation

If you retry the same operation due to timeouts, reuse the same `Idempotency-Key`.

---

## 4. Public Task ID

All task endpoints use a **non-guessable** public ID:

- Format: `t_` + URL-safe random string
- Example: `t_q3kX7m2yWm3aZg6oGm0nqQ`

Notes:

- Case-sensitive
- Not sortable

---

## 5. Endpoints

Base URL examples:

- `https://<your-domain>`
- `http://localhost:8123` (dev compose)

### 5.1 Create / Start a redeem task

`POST /dev/redeem`

Request JSON:

- `voucher`: string

Headers:

- HMAC headers (required)
- `Idempotency-Key` (strongly recommended)

Response fields (typical):

- `task_id`: public task id (`t_...`)
- `status`: `PENDING` / `WAITING_SMS` / `CODE_READY` / `CANCELED` / `FAILED` / `DONE`
- `phone`: phone number if already available
- `expires_at`: upstream expiry time if available

Behavior:

- Same voucher allows **only 1 active task**.
- If the voucher already has an active task, the server may return the existing `task_id`.

### 5.2 Wait for SMS code (long-poll)

`GET /dev/redeem/{task_id}/wait?timeout=30`

Query:

- `timeout`: seconds to wait (suggest 10~30)

Response:

- If code is available:
  - `status=CODE_READY`
  - `code`: string
  - `final=true`
  - `voucher_consumed=true`
- If not yet available:
  - `status=WAITING_SMS`
  - `retry_after_seconds`: integer

### 5.3 Get task status (poll)

`GET /dev/redeem/{task_id}`

Response:

- `status`
- `phone` (if available)
- `code` (only if `CODE_READY`)
- `expires_at` (if available)

### 5.4 Cancel (allowed before code is delivered)

`POST /dev/redeem/{task_id}/cancel`

Rules:

- Allowed when task is not final, including the stage where phone is already obtained but **code not delivered**.
- Rejected if task is already `CODE_READY` / `DONE`.

Idempotency:

- Repeating cancel should return the same result (e.g. already canceled).

---

## 6. Business rules (must-read)

### 6.1 Code delivery means completion

Once the server returns `code` (task becomes `CODE_READY`):

- The service is considered completed.
- The voucher is considered consumed (lifecycle ended).
- Whether the code works on a target platform is outside this service scope.

### 6.2 No-dispute boundary

- **Code delivered = completed**
- **No code = you may cancel or wait until expiry**

---

## 7. Errors

### 7.1 Auth errors

- `DEV_AUTH_MISSING_HEADERS` (401)
- `DEV_AUTH_INVALID_SIGNATURE` (401)
- `DEV_AUTH_TIMESTAMP_OUT_OF_RANGE` (401)
- `DEV_AUTH_NONCE_REPLAY` (401)
- `DEV_AUTH_KEY_DISABLED` (403)

### 7.2 Rate limit

- `DEV_RATE_LIMITED` (429)
  - may include `retry_after_seconds`

### 7.3 Business errors

- `VOUCHER_INVALID` (400/404)
- `VOUCHER_CONSUMED` (409)
- `TASK_NOT_FOUND` (404)
- `TASK_ALREADY_CODE_READY` (409)  
  Returned when cancel is requested after code is delivered.
- `IDEMPOTENCY_KEY_CONFLICT` (409)

---

## 8. Minimal integration flow (recommended)

1) `POST /dev/redeem` with `voucher` + `Idempotency-Key`

2) Receive `task_id` and (usually) `phone`

3) Call `GET /dev/redeem/{task_id}/wait?timeout=30` in a loop until:

- `status=CODE_READY` and you receive `code`

4) If you need to stop before code is delivered:

- `POST /dev/redeem/{task_id}/cancel`

---

## 9. Notes for debugging

When contacting support, provide:

- `dev_key_id`
- `task_id` (public)
- `voucher` (or a redacted form)
- request timestamp/nonce
- server returned `error.code`
