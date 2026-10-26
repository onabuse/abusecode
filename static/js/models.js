import { $, api, esc, fmt } from "./lib.js";

function renderModels(rows) {
  const body = $("models-body");
  const totalReq = rows.reduce((a, r) => a + r.n, 0);
  $("model-summary").textContent = `${rows.length} model${rows.length === 1 ? "" : "s"} · ${fmt(totalReq)} requests`;
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="8" class="px-5 py-6 text-dim">No traffic yet.</td></tr>';
    return;
  }
  const max = Math.max(...rows.map((r) => r.n), 1);
  body.innerHTML = rows
    .map((r) => {
      const pct = Math.max(3, Math.round((r.n / max) * 100));
      return `<tr class="row-hover border-b border-line/70">
        <td class="px-4 py-3 text-fg sm:px-5">${esc(r.model)}</td>
        <td class="hidden px-3 py-3 sm:table-cell">
          <div class="h-1.5 w-full overflow-hidden rounded-full bg-line">
            <div class="h-full rounded-full bg-accent/70" style="width:${pct}%"></div>
          </div>
        </td>
        <td class="px-3 py-3 text-right text-fg">${fmt(r.n)}</td>
        <td class="hidden px-3 py-3 text-right text-dim lg:table-cell">${fmt(r.inp)}</td>
        <td class="hidden px-3 py-3 text-right text-dim lg:table-cell">${fmt(r.outp)}</td>
        <td class="px-3 py-3 text-right text-fg">${fmt(r.tok)}</td>
        <td class="hidden px-3 py-3 text-right text-dim md:table-cell">${fmt(r.lat)} ms</td>
        <td class="hidden px-5 py-3 text-right md:table-cell ${r.err ? "text-[#f0a0a0]" : "text-dim"}">${fmt(r.err)}</td>
      </tr>`;
    })
    .join("");
}

function renderEndpoints(rows) {
  const box = $("endpoints");
  if (!rows.length) {
    box.innerHTML = '<p class="text-sm text-dim">No traffic yet.</p>';
    return;
  }
  const max = Math.max(...rows.map((r) => r.n), 1);
  box.innerHTML = rows
    .map((r) => {
      const pct = Math.max(4, Math.round((r.n / max) * 100));
      return `<div>
        <div class="flex items-center justify-between">
          <span class="mono text-[12px] text-fg">/${esc(r.endpoint)}</span>
          <span class="mono text-[11px] text-dim">${fmt(r.n)} · ${fmt(r.tok)} tok</span>
        </div>
        <div class="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-line">
          <div class="h-full rounded-full bg-accent/70" style="width:${pct}%"></div>
        </div>
      </div>`;
    })
    .join("");
}

async function load() {
  try {
    const [models, endpoints] = await Promise.all([
      api("/api/models"),
      api("/api/endpoints"),
    ]);
    renderModels(models);
    renderEndpoints(endpoints);
  } catch (e) {
    console.error(e);
  }
}

window.addEventListener("app:refresh", load);
load();
