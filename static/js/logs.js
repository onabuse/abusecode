import { $, api, esc, fmt, statusPill, timeOf } from "./lib.js";

const state = { offset: 0, limit: 50, model: "", status: "" };

function rowsHtml(items) {
  if (!items.length) {
    return '<tr><td colspan="10" class="px-5 py-8 text-dim">No requests match these filters.</td></tr>';
  }
  return items
    .map((r) => `<tr class="row-hover border-b border-line/70">
      <td class="px-4 py-2.5 text-dim sm:px-5">${esc(timeOf(r.ts))}</td>
      <td class="hidden px-3 py-2.5 text-muted md:table-cell">${esc(r.endpoint || "—")}</td>
      <td class="px-3 py-2.5 text-fg">${esc(r.model || "—")}</td>
      <td class="px-3 py-2.5">${statusPill(r.status)}</td>
      <td class="hidden px-3 py-2.5 text-right text-dim lg:table-cell">${fmt(r.input_tokens)}</td>
      <td class="hidden px-3 py-2.5 text-right text-dim lg:table-cell">${fmt(r.output_tokens)}</td>
      <td class="px-3 py-2.5 text-right text-fg">${fmt(r.total_tokens)}</td>
      <td class="hidden px-3 py-2.5 text-right text-dim sm:table-cell">${fmt(r.latency_ms)} ms</td>
      <td class="hidden px-3 py-2.5 text-accent-soft md:table-cell">${esc(r.key_name || "—")}</td>
      <td class="hidden max-w-[220px] truncate px-5 py-2.5 text-[11px] text-[#f0a0a0] xl:table-cell" title="${esc(r.error || "")}">${esc(r.error || "")}</td>
    </tr>`)
    .join("");
}

async function load() {
  const params = new URLSearchParams({
    limit: state.limit,
    offset: state.offset,
  });
  if (state.model) params.set("model", state.model);
  if (state.status) params.set("status", state.status);

  for (const [id, fmt] of [["export-csv", "csv"], ["export-json", "json"]]) {
    const link = $(id);
    if (link) link.href = `/api/logs/export?format=${fmt}&${params.toString()}`;
  }

  try {
    const data = await api("/api/logs?" + params.toString());
    $("logs").innerHTML = rowsHtml(data.items);
    const start = data.total ? state.offset + 1 : 0;
    const end = Math.min(state.offset + state.limit, data.total);
    $("log-range").textContent = `${start}–${end} of ${data.total}`;
    $("prev").disabled = state.offset <= 0;
    $("next").disabled = state.offset + state.limit >= data.total;
    $("prev").style.opacity = state.offset <= 0 ? ".4" : "1";
    $("next").style.opacity = state.offset + state.limit >= data.total ? ".4" : "1";
  } catch (e) {
    $("logs").innerHTML = `<tr><td colspan="10" class="px-5 py-6 text-[#f0a0a0]">${esc(e.message)}</td></tr>`;
  }
}

async function loadModels() {
  try {
    const rows = await api("/api/models");
    const sel = $("filter-model");
    rows.forEach((r) => {
      const opt = document.createElement("option");
      opt.value = r.model;
      opt.textContent = r.model;
      sel.appendChild(opt);
    });
  } catch {}
}

$("filter-model").addEventListener("change", (e) => {
  state.model = e.target.value;
  state.offset = 0;
  load();
});
$("filter-status").addEventListener("change", (e) => {
  state.status = e.target.value;
  state.offset = 0;
  load();
});
$("filter-limit").addEventListener("change", (e) => {
  state.limit = Number(e.target.value);
  state.offset = 0;
  load();
});
$("prev").addEventListener("click", () => {
  state.offset = Math.max(0, state.offset - state.limit);
  load();
});
$("next").addEventListener("click", () => {
  state.offset += state.limit;
  load();
});
window.addEventListener("app:refresh", load);

loadModels();
load();
