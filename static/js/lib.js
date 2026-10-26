export const $ = (id) => document.getElementById(id);
export const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

export function fmt(n) {
  n = Number(n) || 0;
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(n >= 10_000_000 ? 0 : 1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(n >= 10_000 ? 0 : 1) + "k";
  return String(n);
}

export function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

export function toast(msg, isErr = false) {
  const el = $("toast");
  if (!el) return;
  el.textContent = msg;
  el.style.borderColor = isErr ? "#5a3333" : "#4a5b75";
  el.style.color = isErr ? "#f0a0a0" : "#ededed";
  el.style.opacity = "1";
  clearTimeout(el._t);
  el._t = setTimeout(() => (el.style.opacity = "0"), 2200);
}

export async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith("/api/login") && location.pathname !== "/login") {
      location.href = "/login";
    }
    let msg = res.statusText;
    try {
      const body = await res.json();
      msg = body.detail || body.error?.message || body.error || msg;
    } catch {}
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  const type = res.headers.get("content-type") || "";
  return type.includes("json") ? res.json() : res.text();
}

export function statusClass(status) {
  return status >= 200 && status < 400 ? "pill-ok" : "pill-err";
}

export function statusPill(status) {
  return `<span class="pill ${statusClass(status)}">${status || "ERR"}</span>`;
}

export function timeOf(ts) {
  return new Date(ts).toLocaleTimeString([], {
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

export async function copyText(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      // Android/LAN over plain http has no async clipboard API.
      const field = document.createElement("textarea");
      field.value = text;
      field.setAttribute("readonly", "");
      field.style.position = "fixed";
      field.style.opacity = "0";
      document.body.appendChild(field);
      field.select();
      const ok = document.execCommand("copy");
      field.remove();
      if (!ok) throw new Error("copy failed");
    }
    toast("Copied");
  } catch {
    toast("Copy failed", true);
  }
}

export function debounce(fn, wait = 250) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), wait);
  };
}
