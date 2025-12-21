# mintcode-api

## Local (Linux)

1) Create `.env` (copy from `.env.example`)

2) Install deps

```bash
pip install -r requirements.txt
```

3) Run

```bash
uvicorn mintcode_api.app:app --reload --host 0.0.0.0 --port 8000
```

Open:
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`

## Docker Compose

```bash
docker compose up --build
```

Open:
- `http://127.0.0.1:8000/docs`

## Admin API

All admin endpoints require header:
- `X-Admin-Key: <ADMIN_API_KEY>`

## Developer API

See: `DEVELOPER_API.md`

### Generate vouchers

`POST /admin/vouchers/generate`

Returns `text/plain` (one code per line).
