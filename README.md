<h1>abusecode<span style="color:#60a5fa">.</span>router</h1>

Dark, production-style **OpenCode-compatible proxy + usage dashboard**.
Route requests through your saved keys with automatic **rotation, failover and cooldown**,
then watch traffic, tokens and key health in a responsive dashboard.

Built with **FastAPI · Jinja2 · TailwindCSS · SQLite**.

---

### Features

- **Proxy** — forwards `/v1/*` to the OpenCode inference API (`/responses`, `/models`, …)
- **Key vault** — add / enable / disable / delete keys (masked in UI)
- **Rotation + failover** — least-recently-used key first, retries next key on `401/403/429/5xx`
- **Key health + cooldown** — failed keys cool down (honors upstream `Retry-After`)
- **Dashboard auth** — optional admin token + signed session cookie (`/login`)
- **Proxy auth** — optional client token for `/v1/*`
- **Usage metering** — requests, tokens, latency, status, per-model and per-key stats
- **Logs** — filters, pagination, CSV/JSON export
- **Model catalog** — live upstream `/v1/models` with search (cached)
- **Playground** — send a real prompt, stream the response, see usage
- **Responsive + PWA** — installable on Android / Windows, adaptive tables, mobile sidebar
- **Ops** — Docker, docker-compose, GitHub Actions CI + GHCR image, pytest suite, ruff

### Quick start

```bash
pip install -r requirements.txt
npm install && npm run build:css     # only needed if editing templates/CSS
./run.sh                              # http://localhost:8000
```

Add a key in the dashboard, then point any client at:

```bash
BASE=http://localhost:8000/v1

curl $BASE/models

curl $BASE/responses \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4.1-flash-free","input":"hello","stream":false}'
```

The proxy injects `Authorization`, `x-opencode-client`, `x-opencode-session`
and related headers, so clients only send the model + input.

### Auth

| Variable | Effect |
|---|---|
| `ABUSECODE_ADMIN_TOKEN` | Protects the dashboard + `/api/*`; enables `/login`. Empty = open. |
| `ABUSECODE_SECRET` | Signs the session cookie (auto-generated per process if empty). |
| `ABUSECODE_PROXY_TOKEN` | When set, `/v1/*` requires `Authorization: Bearer <token>` or `x-proxy-token`. |

### Configuration

| Variable | Default | Meaning |
|---|---|---|
| `HOST` / `PORT` | `0.0.0.0` / `8000` | bind address |
| `ABUSECODE_DB` | `data/abusecode.db` | SQLite path |
| `OPENCODE_API_BASE` | `https://opencode.ai/inference` | upstream base |
| `OPENCODE_SESSION` | random per request | default session id |
| `OPENCODE_USER_AGENT` | opencode CLI UA | upstream user agent |
| `ABUSECODE_SESSION_MAX_AGE` | `43200` | session cookie lifetime (seconds) |

### API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | status, version, active keys |
| `GET` | `/api/stats?hours=24` | totals + hourly series + breakdowns |
| `GET` | `/api/keys` · `POST` · `PATCH /{id}` · `DELETE /{id}` | key management |
| `GET` | `/api/logs?limit&offset&model&status` | paginated logs |
| `GET` | `/api/logs/export?format=csv\|json` | export logs |
| `GET` | `/api/models` · `/api/endpoints` · `/api/key-usage` | breakdowns |
| `GET` | `/api/catalog?refresh=true` | upstream model catalog |
| `ALL` | `/v1/{path}` | proxied upstream API |

### Pages

`/` overview · `/playground` · `/keys` · `/models` · `/logs` · `/settings`

### Layout

```
app/
  config.py            settings
  db.py                SQLite schema, key health, stats
  security.py          auth middleware, tokens
  schemas.py           request models
  services/
    upstream.py        headers, usage parsing, failover, cooldown
    client.py          shared httpx client
  routers/
    pages.py           server-rendered pages
    auth.py            login/logout
    keys.py            key API
    usage.py           stats/logs/catalog/export API
    proxy.py           /v1 proxy
templates/             base + partials + pages (Jinja2)
static/
  css/input.css        Tailwind source (builds app.css)
  js/                  ES modules per page
  manifest.webmanifest, sw.js, icon.svg
tests/                 pytest suite
scripts/autosync.*     auto commit + push watcher
```

### Development

```bash
pip install -r requirements-dev.txt
npm install
npm run watch:css      # in one terminal
uvicorn app.main:app --reload
pytest                 # 13 tests
ruff check app tests
```

### Deploy

- **Docker:** `docker compose up --build`
- **Render:** `render.yaml` (auto-deploys on push)
- **GHCR:** CI builds `ghcr.io/onabuse/abusecode:latest` on every push to `main`

### Auto-sync to GitHub

A watcher commits and pushes every change:

```bash
./scripts/autosync.sh start     # background
./scripts/autosync.sh status
./scripts/autosync.sh stop
```

Runtime files (`*.log`, `autosync.pid`) are gitignored.

> Keys are stored in local SQLite. Run this on your own machine / private
> network, or set `ABUSECODE_ADMIN_TOKEN` + `ABUSECODE_PROXY_TOKEN` before exposing it.
