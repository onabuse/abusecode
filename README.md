<h1>abusecode<span style="color:#60a5fa">.</span>router</h1>

Dark, flat OpenAI/OpenCode-compatible proxy with a usage dashboard.
Every request is routed through your saved API keys (with rotation + failover)
and metered in a local SQLite database.

---

### Features

- **Proxy** — forwards `/v1/*` to the OpenCode inference API (`/v1/responses`, `/v1/models`, …)
- **Key vault** — add / enable / disable / delete keys from the dashboard (masked in UI)
- **Rotation + failover** — least-recently-used key first; retries the next key on `401/403/429/5xx`
- **Usage metering** — requests, tokens, latency, status, model, per-key stats
- **Live dashboard** — theme-matched UI, auto-refresh every 5s, hourly traffic chart
- **Streaming aware** — parses token usage from SSE and plain JSON responses

### Quick start

```bash
pip install -r requirements.txt
./run.sh                       # http://localhost:8000
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
and related headers automatically, so clients only need the model + input.

### Configuration (env)

| Variable | Default | Meaning |
|---|---|---|
| `HOST` / `PORT` | `0.0.0.0` / `8000` | bind address |
| `OPENCODE_API_BASE` | `https://opencode.ai/inference` | upstream base |
| `OPENCODE_SESSION` | random per request | default session id |
| `OPENCODE_USER_AGENT` | opencode CLI UA | upstream user agent |
| `ABUSECODE_DB` | `data/abusecode.db` | SQLite path |

### Layout

```
app/config.py   settings
app/db.py       SQLite: keys + usage, stats aggregation
app/main.py     FastAPI: /v1 proxy, /api dashboard, static UI
static/         index.html + app.js (Tailwind CDN)
data/           SQLite database (gitignored)
```

> Keys are stored in plaintext in local SQLite. Run this on your own machine /
> private network; do not expose the dashboard publicly without adding auth.
