const CACHE = "abusecode-v3";
const ASSET_TIMEOUT = 3500;
const SHELL = [
  "/",
  "/playground",
  "/keys",
  "/models",
  "/logs",
  "/settings",
  "/static/css/app.css",
  "/static/js/app.js",
  "/static/js/lib.js",
  "/static/js/overview.js",
  "/static/js/playground.js",
  "/static/js/keys.js",
  "/static/js/models.js",
  "/static/js/logs.js",
  "/static/js/settings.js",
  "/static/icon.svg",
  "/static/manifest.webmanifest",
];

const OFFLINE = `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Offline · abusecode.router</title>
<style>
body{margin:0;min-height:100vh;display:grid;place-items:center;background:#171717;color:#ededed;
font-family:ui-sans-serif,system-ui,sans-serif;text-align:center;padding:24px}
p{color:#9a9a9a;max-width:28rem;line-height:1.6}
a{color:#60a5fa}
</style></head><body><div>
<h1>You are offline</h1>
<p>This page has not been cached yet. Reconnect and reload to continue.</p>
<p><a href="/">Go to overview</a></p>
</div></body></html>`;

function withTimeout(promise, ms) {
  return Promise.race([
    promise,
    new Promise((resolve) => setTimeout(() => resolve(null), ms)),
  ]);
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE);
      await Promise.all(
        SHELL.map(async (url) => {
          try {
            const res = await fetch(url, { cache: "reload" });
            // Never cache auth redirects or error pages.
            if (res.ok && !res.redirected) await cache.put(url, res);
          } catch {}
        })
      );
    })()
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
      await self.clients.claim();
    })()
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/v1/")) return;

  if (req.mode === "navigate") {
    event.respondWith(
      (async () => {
        try {
          const res = await fetch(req);
          if (res.ok && !res.redirected) {
            const cache = await caches.open(CACHE);
            await cache.put(req, res.clone());
          }
          return res;
        } catch {
          const cached = await caches.match(req, { ignoreSearch: true });
          if (cached) return cached;
          return new Response(OFFLINE, {
            status: 503,
            headers: { "Content-Type": "text/html; charset=utf-8" },
          });
        }
      })()
    );
    return;
  }

  event.respondWith(
    (async () => {
      const network = fetch(req)
        .then(async (res) => {
          if (res.ok) {
            const cache = await caches.open(CACHE);
            await cache.put(req, res.clone());
          }
          return res;
        })
        .catch(() => null);

      const fresh = await withTimeout(network, ASSET_TIMEOUT);
      if (fresh) return fresh;

      const cached = await caches.match(req);
      if (cached) return cached;

      const retry = await network;
      return retry || new Response("", { status: 504 });
    })()
  );
});
