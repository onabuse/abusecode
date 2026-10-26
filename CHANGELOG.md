# Changelog

## 1.2.0 — 2026-10-26

### Fixed

- **Mobile menu was completely dead.** `app.js` used an optional-chaining
  assignment (`$("base-origin")?.textContent = ...`), which is invalid
  JavaScript. The whole ES module failed to parse, so no event listeners were
  attached. Rewritten as a guarded assignment, with `aria-expanded`, body
  scroll lock and automatic close when resizing to desktop.
- **Failover attempts were double-counted.** One client request that retried
  across keys wrote several usage rows, inflating request counts and lowering
  the success rate. Intermediate attempts now only update key health; usage is
  logged once for the final outcome.
- **Playground hid HTTP errors.** Streaming requests that returned `401/429/5xx`
  were parsed as SSE and showed an empty response. Errors are now decoded and
  displayed for both stream and non-stream requests.
- **Proxy token blocked the dashboard playground.** With
  `ABUSECODE_PROXY_TOKEN` set, same-origin browser calls from the dashboard were
  rejected. Same-origin requests now pass, while external clients still need the
  token.
- **7-day chart overflowed the canvas.** Bar width had a hard minimum of 2px and
  a fixed gap, so 168 bars ran off the right edge. Gap and width now scale with
  the selected range.
- **Model catalog stayed stale after key changes.** Adding, toggling or deleting
  a key now invalidates the cached `/v1/models` result.
- **Cooling keys were reported as active.** `/api/health`, `/api/stats` and the
  overview card now show available keys and a separate cooling count. The keys
  page shows a cooling pill, cooldown time and a Reset action.
- **Dashboard cookies leaked upstream.** `build_headers` forwarded `Cookie`,
  `Origin`, `Referer`, `Sec-Fetch-*` and proxy tokens to the provider. Those are
  now stripped before the request leaves the proxy.
- **Copy failed on Android over LAN http.** The async clipboard API is
  unavailable outside secure contexts; added a `execCommand` fallback.
- **Expired sessions left blank pages.** A `401` from `/api/*` now redirects to
  `/login` instead of silently failing every fetch.
- **Duplicate keys could be saved.** Adding an already-stored key returns `409`,
  so rotation cannot retry the same credential twice.
- **Logs export ignored paging.** CSV/JSON export only receives the active
  filters, not `limit`/`offset`.
- **Auto-sync messages were opaque.** Commits now list the changed files.

### Added

- `node --check` syntax test for every `static/js/*.js` module, so a parse error
  like the menu bug fails CI instead of shipping.
- Tests for proxy-token auth, same-origin bypass, catalog invalidation and
  cooling-key stats.
- This changelog.

## 1.1.0

- Multi-page dashboard (overview, playground, keys, models, logs, settings).
- Key vault with rotation, failover, health and cooldown.
- Usage metering, stats, filters, pagination and CSV/JSON export.
- Optional dashboard auth and proxy token.
- Responsive dark UI, PWA manifest and service worker.
- Docker, compose, Render, GitHub Actions CI + GHCR image.
