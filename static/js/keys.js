import { $, api, esc, fmt, toast } from "./lib.js";

function renderKeys(keys) {
  const box = $("keys");
  $("key-count").textContent = keys.length + (keys.length === 1 ? " key" : " keys");
  if (!keys.length) {
    box.innerHTML = '<p class="text-sm text-dim">No keys yet.</p>';
    return;
  }
  box.innerHTML = keys
    .map((k) => {
      const last = k.last_used_at ? new Date(k.last_used_at).toLocaleString() : "never used";
      return `<div class="tile flex flex-col gap-2 px-3 py-2.5 sm:flex-row sm:items-center sm:justify-between">
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <span class="h-1.5 w-1.5 rounded-full ${k.active ? "bg-accent" : "bg-[#555]"}"></span>
            <span class="mono truncate text-[13px] text-fg">${esc(k.name)}</span>
            <span class="pill ${k.active ? "pill-ok" : "pill-idle"}">${k.active ? "active" : "off"}</span>
          </div>
          <div class="mono mt-1 truncate text-[11px] text-dim">${esc(k.masked)} · ${esc(last)}</div>
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <button data-act="toggle" data-id="${k.id}" data-active="${k.active ? 1 : 0}"
            class="btn btn-ghost px-2.5 py-1 text-[11px]">${k.active ? "Disable" : "Enable"}</button>
          <button data-act="del" data-id="${k.id}"
            class="btn btn-danger px-2.5 py-1 text-[11px]">Delete</button>
        </div>
      </div>`;
    })
    .join("");

  box.querySelectorAll("button[data-act]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      if (btn.dataset.act === "toggle") patchKey(id, btn.dataset.active !== "1");
      else if (confirm("Delete this key? This cannot be undone.")) delKey(id);
    });
  });
}

function renderUsage(rows) {
  const body = $("key-usage");
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="4" class="px-5 py-6 text-dim">No usage yet.</td></tr>';
    return;
  }
  body.innerHTML = rows
    .map((r) => `<tr class="row-hover border-b border-line/70">
      <td class="px-5 py-2.5 text-accent-soft">${esc(r.name)}</td>
      <td class="px-3 py-2.5 text-right text-fg">${fmt(r.n)}</td>
      <td class="px-3 py-2.5 text-right text-fg">${fmt(r.tok)}</td>
      <td class="px-5 py-2.5 text-right ${r.err ? "text-[#f0a0a0]" : "text-dim"}">${fmt(r.err)}</td>
    </tr>`)
    .join("");
}

async function patchKey(id, active) {
  try {
    await api(`/api/keys/${id}`, { method: "PATCH", body: JSON.stringify({ active }) });
    toast(active ? "Key enabled" : "Key disabled");
    await load();
  } catch (e) {
    toast("Failed: " + e.message, true);
  }
}

async function delKey(id) {
  try {
    await api(`/api/keys/${id}`, { method: "DELETE" });
    toast("Key deleted");
    await load();
  } catch (e) {
    toast("Failed: " + e.message, true);
  }
}

async function addKey(ev) {
  ev.preventDefault();
  const name = $("key-name").value.trim() || "key";
  const api_key = $("key-value").value.trim();
  if (!api_key) return toast("Enter an API key", true);
  try {
    await api("/api/keys", { method: "POST", body: JSON.stringify({ name, api_key }) });
    $("key-name").value = "";
    $("key-value").value = "";
    toast("Key saved");
    await load();
  } catch (e) {
    toast("Failed: " + e.message, true);
  }
}

async function load() {
  try {
    const [keys, usage] = await Promise.all([api("/api/keys"), api("/api/key-usage")]);
    renderKeys(keys);
    renderUsage(usage);
  } catch (e) {
    console.error(e);
  }
}

$("add-key").addEventListener("submit", addKey);
window.addEventListener("app:refresh", load);
load();
