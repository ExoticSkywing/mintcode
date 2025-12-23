# MintCode 开发者 API

本文档描述了用于程序化短信验证码兑换的**开发者 API**。

## 核心原则

- **卡密优先**：`voucher`（卡密）是唯一的用户凭证
- **SKU 隐藏**：卡密在服务端预绑定了固定的供应商配置
- **完成边界**：**一旦验证码送达，服务即完成，卡密即消耗**
- **成本安全**：
  - 同一卡密**同时只能有 1 个活跃任务**
  - **仅在验证码送达前**允许取消

---

## 1. 术语

| 术语 | 说明 |
|------|------|
| **卡密 (Voucher)** | 兑换凭证，没有卡密无法发起任何操作 |
| **兑换任务 (Redeem Task)** | 服务端状态机，代表一次兑换尝试 |
| **公开任务 ID (Public Task ID)** | 暴露给开发者的任务标识符，格式：`t_<随机字符串>`，不可猜测 |

---

## 2. 认证（HMAC + 时间戳 + 随机数）

所有开发者 API 请求都必须签名。

### 2.1 凭证

你将获得：

- `dev_key_id`（公开）
- `dev_key_secret`（私密，请妥善保管）

### 2.2 必需的请求头

| Header | 说明 |
|--------|------|
| `X-Dev-Key-Id` | 你的 `dev_key_id` |
| `X-Dev-Timestamp` | Unix 时间戳（**秒**） |
| `X-Dev-Nonce` | 随机字符串（建议 16+ 字符） |
| `X-Dev-Signature` | 签名字符串（Base64） |

### 2.3 时间窗口

服务端会拒绝请求，如果：

```
abs(服务器当前时间秒 - X-Dev-Timestamp) > 300
```

### 2.4 重放保护

服务端会拒绝请求，如果以下元组在时间窗口内被重用：

```
(X-Dev-Key-Id, X-Dev-Timestamp, X-Dev-Nonce)
```

### 2.5 规范字符串

使用以下字段构建规范字符串：

| 字段 | 说明 |
|------|------|
| `METHOD` | 大写 HTTP 方法 |
| `PATH` | 请求路径（如 `/dev/redeem/t_xxx/wait`），不含域名 |
| `QUERY` | 原始查询字符串，不含前导 `?`（无则为空） |
| `TIMESTAMP` | `X-Dev-Timestamp` |
| `NONCE` | `X-Dev-Nonce` |
| `BODY_SHA256` | 请求体的 SHA256 十六进制；无请求体则为空字节的 SHA256 |

格式：

```
METHOD\nPATH\nQUERY\nTIMESTAMP\nNONCE\nBODY_SHA256
```

### 2.6 签名

```
signature_bytes = HMAC-SHA256(dev_key_secret, canonical_string_bytes)
X-Dev-Signature = Base64(signature_bytes)
```

---

## 3. 幂等性

### 3.1 `POST /dev/redeem`

创建兑换任务时，应提供：

- `Idempotency-Key`：该客户端操作的唯一字符串

如果因超时需要重试，请**复用相同的** `Idempotency-Key`。

---

## 4. 公开任务 ID

所有任务端点使用**不可猜测**的公开 ID：

- 格式：`t_` + URL 安全随机字符串
- 示例：`t_q3kX7m2yWm3aZg6oGm0nqQ`

注意：

- 区分大小写
- 不可排序

---

## 5. 接口

基础 URL 示例：

- `https://<your-domain>`
- `http://localhost:8123`（开发环境）

### 5.1 创建/启动兑换任务

`POST /dev/redeem`

**请求体 JSON**：

```json
{
  "voucher": "你的卡密"
}
```

**请求头**：

- HMAC 签名头（必需）
- `Idempotency-Key`（强烈建议）

**响应字段**：

| 字段 | 说明 |
|------|------|
| `task_id` | 公开任务 ID（`t_...`） |
| `status` | `PENDING` / `WAITING_SMS` / `CODE_READY` / `CANCELED` / `FAILED` / `DONE` |
| `phone` | 手机号（如已获取） |
| `expires_at` | 上游过期时间（如有） |

**行为**：

- 同一卡密**只允许 1 个活跃任务**
- 如果该卡密已有活跃任务，服务端会返回已存在的 `task_id`

### 5.2 等待短信验证码（长轮询）

`GET /dev/redeem/{task_id}/wait?timeout=30`

**查询参数**：

- `timeout`：等待秒数（建议 10~30）

**响应**：

验证码已到达时：
```json
{
  "status": "CODE_READY",
  "code": "123456",
  "final": true,
  "voucher_consumed": true
}
```

尚未到达时：
```json
{
  "status": "WAITING_SMS",
  "retry_after_seconds": 5
}
```

### 5.3 获取任务状态（轮询）

`GET /dev/redeem/{task_id}`

**响应字段**：

- `status`
- `phone`（如有）
- `code`（仅当 `CODE_READY`）
- `expires_at`（如有）

### 5.4 取消（仅在验证码送达前允许）

`POST /dev/redeem/{task_id}/cancel`

**规则**：

- 任务未结束时可取消，包括已获取手机号但**验证码未送达**的阶段
- 任务已是 `CODE_READY` / `DONE` 时会被拒绝

**幂等性**：

- 重复取消应返回相同结果（如：已取消）

---

## 6. 业务规则（必读）

### 6.1 验证码送达即完成

一旦服务端返回 `code`（任务变为 `CODE_READY`）：

- 服务视为**已完成**
- 卡密视为**已消耗**（生命周期结束）
- 验证码在目标平台是否有效，**不在本服务范围内**

### 6.2 无争议边界

| 状态 | 结论 |
|------|------|
| **已出码** | 订单完成，不可退 |
| **未出码** | 可取消或等待过期 |

---

## 7. 错误码

### 7.1 认证错误

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `DEV_AUTH_MISSING_HEADERS` | 401 | 缺少认证头 |
| `DEV_AUTH_INVALID_SIGNATURE` | 401 | 签名无效 |
| `DEV_AUTH_TIMESTAMP_OUT_OF_RANGE` | 401 | 时间戳超出范围 |
| `DEV_AUTH_NONCE_REPLAY` | 401 | 随机数重放 |
| `DEV_AUTH_KEY_DISABLED` | 403 | 密钥已禁用 |

### 7.2 限流

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `DEV_RATE_LIMITED` | 429 | 请求过于频繁，可能包含 `retry_after_seconds` |

### 7.3 业务错误

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `VOUCHER_INVALID` | 404 | 卡密无效 |
| `VOUCHER_CONSUMED` | 409 | 卡密已被使用 |
| `TASK_NOT_FOUND` | 404 | 任务不存在 |
| `TASK_ALREADY_CODE_READY` | 409 | 验证码已送达后请求取消 |
| `IDEMPOTENCY_KEY_CONFLICT` | 409 | 幂等键冲突 |

---

## 8. 最简集成流程（推荐）

1. `POST /dev/redeem`，携带 `voucher` + `Idempotency-Key`

2. 获取 `task_id` 和 `phone`（通常会立即返回）

3. 循环调用 `GET /dev/redeem/{task_id}/wait?timeout=30`，直到：
   - `status=CODE_READY` 并获取到 `code`

4. 如需在验证码送达前停止：
   - `POST /dev/redeem/{task_id}/cancel`

---

## 9. 调试说明

联系技术支持时，请提供：

- `dev_key_id`
- `task_id`（公开 ID）
- `voucher`（可脱敏）
- 请求的时间戳/随机数
- 服务端返回的错误码
