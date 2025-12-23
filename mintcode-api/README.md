# MintCode API

短信验证码兑换服务 API

## 快速开始

### 本地运行（Linux）

1. 创建 `.env`（从 `.env.example` 复制）

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 启动服务

```bash
uvicorn mintcode_api.app:app --reload --host 0.0.0.0 --port 8000
```

访问：
- API 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/health`

### Docker Compose

```bash
docker compose up --build
```

访问：`http://127.0.0.1:8000/docs`

---

## 文档

| 文档 | 说明 |
|------|------|
| [开发者 API](./DEVELOPER_API.md) | 程序化接入文档（HMAC 签名、幂等性、接口说明） |

---

## 管理后台

所有管理端点需要请求头：
- `X-Admin-Key: <ADMIN_API_KEY>`

### 生成卡密

`POST /admin/vouchers/generate`

返回 `text/plain`（每行一个卡密）

---

## 用户界面

| 路径 | 说明 |
|------|------|
| `/admin-ui` | 管理后台 |
| `/redeem-ui` | 用户兑换界面 |
