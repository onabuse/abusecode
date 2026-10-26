import { $, api, fmt, esc, statusPill, timeOf, copyText, debounce } from "./lib.js";

const base = location.origin + "/v1";
let lastSeries = [];
$("base-url").textContent = base;
$("copy-base").addEventListener("click", () => copyText(base));

function renderStats(s) {
  $("stat-requests").textContent = fmt(s.requests);
  $("stat-tokens").textContent = fmt(s.tokens);
  $("stat-rate").textContent = (s.success_rate ?? 100).toFixed(1) + "%";
  $("stat-latency").textContent = "avg " + fmt(s.avg_latency) + " ms";
  $("stat-keys").textContent = fmt(s.active_keys);
  const sub = $("stat-keys-sub");
  if (sub) sub.textContent = s.cooling_keys ? `${s.cooling_keys} cooling down` : "rotation ready";
  renderModels(s.by_model || []);
  renderRecent(s.recent || []);
  lastSeries = s.series || [];
  drawChart(lastSeries);
}

function renderModels(models) {
  const box = $("models");
  if (!models.length) {
    box.innerHTML = '<p class="text-sm text-dim">No traffic yet.</p>';
    return;
  }
  const max = Math.max(...models.map((m) => m.n), 1);
  box.innerHTML = models
    .slice(0, 6)
    .map((m) => {
      const pct = Math.max(4, Math.round((m.n / max) * 100));
      return `<div>
        <div class="flex items-center justify-between gap-2">
          <span class="mono truncate text-[12px] text-fg">${esc(m.model)}</span>
          <span class="mono text-[11px] text-dim">${fmt(m.n)} · ${fmt(m.tok)} tok</span>
        </div>
        <div class="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-line">
          <div class="h-full rounded-full bg-accent/70" style="width:${pct}%"></div>
        </div>
      </div>`;
    })
    .join("");
}

function renderRecent(rows) {
  const body = $("recent");
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="6" class="px-5 py-6 text-dim">No requests yet.</td></tr>';
    return;
  }
  body.innerHTML = rows
    .slice(0, 8)
    .map((r) => `<tr class="row-hover border-b border-line/70">
      <td class="px-4 py-2.5 text-dim sm:px-5">${esc(timeOf(r.ts))}</td>
      <td class="hidden px-3 py-2.5 text-muted md:table-cell">${esc(r.endpoint || "—")}</td>
      <td class="px-3 py-2.5 text-fg">${esc(r.model || "—")}</td>
      <td class="px-3 py-2.5">${statusPill(r.status)}</td>
      <td class="px-3 py-2.5 text-right text-fg">${fmt(r.total_tokens)}</td>
      <td class="hidden px-5 py-2.5 text-right text-dim sm:table-cell">${fmt(r.latency_ms)} ms</td>
    </tr>`)
    .join("");
}

function roundRect(ctx, x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function drawChart(series) {
  const canvas = $("chart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth || 600;
  const h = 192;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);

  const padB = 20;
  const padT = 8;
  const chartH = h - padB - padT;
  const max = Math.max(1, ...series.map((p) => p.count));
  const n = series.length || 24;
  // Keep 7d/30d ranges inside the canvas instead of overflowing to the right.
  const gap = n > 96 ? 1 : n > 48 ? 2 : 3;
  const bw = Math.max(1, (w - gap * (n - 1)) / n);

  ctx.strokeStyle = "#252525";
  ctx.lineWidth = 1;
  for (let g = 0; g <= 3; g++) {
    const y = padT + (chartH / 3) * g + 0.5;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  series.forEach((p, i) => {
    const x = i * (bw + gap);
    const totalH = (p.count / max) * chartH;
    const errH = (p.errors / max) * chartH;
    if (totalH > 0) {
      const grad = ctx.createLinearGradient(0, padT, 0, padT + chartH);
      grad.addColorStop(0, "rgba(96,165,250,0.95)");
      grad.addColorStop(1, "rgba(30,109,212,0.45)");
      ctx.fillStyle = grad;
      roundRect(ctx, x, padT + chartH - totalH, bw, totalH, 2);
      ctx.fill();
    }
    if (errH > 0) {
      ctx.fillStyle = "rgba(201,106,106,0.9)";
      roundRect(ctx, x, padT + chartH - errH, bw, errH, 2);
      ctx.fill();
    }
  });

  ctx.fillStyle = "#9a9a9a";
  ctx.font = '10px "JetBrains Mono", monospace';
  ctx.textBaseline = "top";
  const every = Math.ceil(n / 6);
  series.forEach((p, i) => {
    if (i % every !== 0) return;
    const d = new Date(p.t);
    const label = hours <= 24
      ? String(d.getHours()).padStart(2, "0") + "h"
      : d.getMonth() + 1 + "/" + d.getDate();
    ctx.fillText(label, i * (bw + gap), h - padB + 5);
  });
}

let hours = 24;

async function load() {
  try {
    renderStats(await api(`/api/stats?hours=${hours}`));
  } catch (e) {
    console.error(e);
  }
}

$("range")?.addEventListener("change", (e) => {
  hours = Number(e.target.value) || 24;
  load();
});

window.addEventListener("app:refresh", load);
window.addEventListener("resize", debounce(() => drawChart(lastSeries), 150));
load();
setInterval(load, 5000);
