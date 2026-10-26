import { $, api, toast } from "./lib.js";

const out = $("pg-output");
const statusPill = $("pg-status");
const meta = $("pg-meta");
let controller = null;

function setStatus(text, ok = true) {
  statusPill.textContent = text;
  statusPill.className = "pill " + (ok ? "pill-ok" : "pill-err");
}

function textFrom(obj) {
  if (!obj || typeof obj !== "object") return "";
  if (typeof obj.output_text === "string") return obj.output_text;
  if (Array.isArray(obj.output)) {
    const parts = [];
    for (const o of obj.output) {
      for (const c of o.content || []) {
        if ((c.type === "output_text" || c.type === "text") && c.text) parts.push(c.text);
      }
    }
    if (parts.length) return parts.join("");
  }
  if (Array.isArray(obj.choices) && obj.choices[0]?.message?.content) {
    return obj.choices[0].message.content;
  }
  return "";
}

function usageFrom(obj) {
  if (!obj) return null;
  if (obj.usage) return obj.usage;
  if (obj.response?.usage) return obj.response.usage;
  if (obj.message?.usage) return obj.message.usage;
  return null;
}

async function loadCatalog() {
  try {
    const cat = await api("/api/catalog");
    const sel = $("pg-model");
    const models = (cat.data || []).map((m) => m.id).filter(Boolean);
    if (!models.length) return;
    models.sort((a, b) => (a.endsWith("-free") ? -1 : 0) - (b.endsWith("-free") ? -1 : 0));
    sel.innerHTML = models
      .map((id) => `<option value="${id}">${id}${id.endsWith("-free") ? " · free" : ""}</option>`)
      .join("");
  } catch {}
}

async function send(e) {
  e.preventDefault();
  const model = $("pg-model").value;
  const input = $("pg-input").value.trim();
  const stream = $("pg-stream").checked;
  const max = Number($("pg-max").value) || 512;
  if (!input) return toast("Enter a prompt", true);

  controller?.abort();
  controller = new AbortController();
  out.textContent = "";
  out.scrollTop = 0;
  meta.textContent = "…";
  setStatus("running");
  const started = performance.now();

  try {
    const res = await fetch("/v1/responses", {
      method: "POST",
      signal: controller.signal,
      headers: { "Content-Type": "application/json", Accept: stream ? "text/event-stream" : "application/json" },
      body: JSON.stringify({ model, input, stream, max_output_tokens: max }),
    });

    const reqId = res.headers.get("x-abuse-request-id") || "";
    setStatus(String(res.status), res.ok);

    if (!res.ok) {
      const raw = await res.text();
      let message = raw;
      try {
        const body = JSON.parse(raw);
        message = body?.error?.message || body?.detail || JSON.stringify(body, null, 2);
      } catch {}
      out.textContent = message || `HTTP ${res.status}`;
      meta.textContent = `HTTP ${res.status} · ${reqId}`;
      return;
    }

    if (!stream) {
      const body = await res.json();
      out.textContent = textFrom(body) || JSON.stringify(body, null, 2);
      const u = usageFrom(body);
      const ms = Math.round(performance.now() - started);
      meta.textContent = `${ms} ms${u ? ` · ${u.total_tokens ?? (u.input_tokens || 0) + (u.output_tokens || 0)} tok` : ""} · ${reqId}`;
      return;
    }

    if (!res.body) throw new Error("No response body");
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let text = "";
    let usage = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        const t = line.trim();
        if (!t.startsWith("data:")) continue;
        const data = t.slice(5).trim();
        if (!data || data === "[DONE]") continue;
        let obj;
        try {
          obj = JSON.parse(data);
        } catch {
          continue;
        }
        if (typeof obj.delta === "string") text += obj.delta;
        else if (obj.response) {
          const full = textFrom(obj.response);
          if (full) text = full;
        }
        if (obj.type === "error" || obj.error) {
          text += "\n" + (obj.error?.message || JSON.stringify(obj.error));
        }
        usage = usageFrom(obj) || usage;
        out.textContent = text || data;
      }
    }

    if (!text) text = "(empty response)";
    out.textContent = text;
    const ms = Math.round(performance.now() - started);
    const tok = usage
      ? usage.total_tokens ?? (usage.input_tokens || 0) + (usage.output_tokens || 0)
      : null;
    meta.textContent = `${ms} ms${tok != null ? ` · ${tok} tok` : ""} · ${reqId}`;
  } catch (err) {
    setStatus("error", false);
    out.textContent = String(err.message || err);
    meta.textContent = "—";
  }
}

$("pg-form").addEventListener("submit", send);
$("pg-clear").addEventListener("click", () => {
  out.textContent = "Response will appear here…";
  meta.textContent = "—";
  setStatus("idle");
});

loadCatalog();
