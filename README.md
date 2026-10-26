<h1>abusecode<span style="color:#60a5fa">.</span>router</h1>

Dark, flat OpenCode-compatible proxy with a full usage dashboard.
Route any client through one endpoint; keys are stored locally, rotated with
automatic failover + cooldown, and every call is metered.

---

### Features

- **Proxy** — forwards `/v1/*` to the OpenCode inference API (`/v1/responses`, `/v1/models`, …)
- **Key vault** — add / enable / disable / delete keys; masked in the UI
- **Rotation + failover + cooldown** — least-recently-used key first, retries the next key on `401/403/429/5xx`, and temporarily parks failing keys
- **Usage metering** — requests, tokens, latency, status, model, per-key stats
- **Model catalog** — live `/v1/models` with search and free/paid badges
- **Playground** — send a real prompt through the proxy (streaming SSE supported)
- **Logs** — filters, pagination, CSV/JSON export
- **Auth** — optional dashboard login and optional proxy token
- **Responsive + PWA** — works on Android, iOS, Windows, desktop; installable
- **Ops-ready** — Docker, docker compose, Render blueprint, GHCR image build, tests + lint CI

### Quick start

```bash
pip install -r requirements.txt
npm install && npm run build:css      # only needed after editing CSS/templates
./run.sh                              # http://localhost:8000
```

Open the dashboard, add a key, then point any client at:

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
| `ABUSECODE_ADMIN_TOKEN` | Enables `/login`; protects dashboard + `/api/*`. Empty = open |
| `ABUSECODE_PROXY_TOKEN` | Requires `Authorization: Bearer <token>` (or `x-proxy-token`) on `/v1/*`. Empty = open |
| `ABUSECODE_SECRET` | Signs the session cookie (auto-generated if empty) |

### API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | status + upstream + key count |
| `GET` | `/api/stats?hours=24` | totals, series, breakdowns |
| `GET` | `/api/logs?limit&offset&model&status` | paginated logs |
| `GET` | `/api/logs/export?format=csv\|json` | download logs |
| `GET` | `/api/models` | usage by model |
| `GET` | `/api/catalog?refresh=true` | upstream model catalog (cached 60s) |
| `GET/POST/PATCH/DELETE` | `/api/keys` | key management |
| `ALL` | `/v1/{path}` | proxied OpenCode API |

### Configuration

| Variable | Default | Meaning |
|---|---|---|
| `HOST` / `PORT` | `0.0.0.0` / `8000` | bind address |
| `OPENCODE_API_BASE` | `https://opencode.ai/inference` | upstream base |
| `OPENCODE_SESSION` | random per request | default session id |
| `OPENCODE_USER_AGENT` | opencode CLI UA | upstream user agent |
| `ABUSECODE_DB` | `data/abusecode.db` | SQLite path |
| `ABUSECODE_DATA` | `data` | data directory |
| `ABUSECODE_SESSION_MAX_AGE` | `43200` | session cookie lifetime (s) |

### Layout

```
app/
  main.py            app factory, lifespan, middleware, routers
  config.py          settings
  db.py              SQLite: keys, usage, health, stats
  security.py        dashboard auth + proxy token
  routers/           pages, auth, keys, usage, proxy
  services/          upstream client, failover, usage parsing
templates/           Jinja2 (base, partials, pages, login)
static/              css (Tailwind build), js modules, manifest, sw
tests/               pytest suite
scripts/             autosync watcher
```

### Development

```bash
pip install -r requirements-dev.txt
npm run watch:css        # Tailwind in watch mode
pytest                   # 13 tests
ruff check app tests
```

### Auto-sync to GitHub

A watcher commits and pushes every change automatically:

```bash
./scripts/autosync.sh start     # background (logs: .git/autosync.log)
./scripts/autosync.sh status
./scripts/autosync.sh stop
```

### Deploy

**Render** — connect the repo; `render.yaml` builds the Dockerfile and auto-deploys on push.

**Docker**

```bash
docker compose up --build          # http://localhost:8000
```

**GHCR** — every push to `main` builds and publishes
`ghcr.io/onabuse/abusecode:latest` via GitHub Actions.

> Keys live in local SQLite (plaintext). Run privately or set `ABUSECODE_ADMIN_TOKEN`
> and `ABUSECODE_PROXY_TOKEN` before exposing it. On ephemeral hosts, mount a
> volume at `ABUSECODE_DATA` or the DB resets on redeploy.
