import { $, api, copyText, toast } from "./lib.js";

const base = location.origin + "/v1";
$("settings-base").textContent = base;
$("copy-settings-base").addEventListener("click", () => copyText(base));

async function loadHealth() {
  const auth = $("settings-auth");
  const proxy = $("settings-proxy");
  try {
    const h = await api("/api/health");
    auth.textContent = h.dashboard_auth ? "enabled" : "disabled";
    auth.className = "mono text-[12px] " + (h.dashboard_auth ? "text-accent" : "text-dim");
    proxy.textContent = h.proxy_token ? "required" : "open";
    proxy.className = "mono text-[12px] " + (h.proxy_token ? "text-accent" : "text-dim");
  } catch {
    auth.textContent = "unknown";
    proxy.textContent = "unknown";
  }
}

loadHealth();
window.addEventListener("app:refresh", loadHealth);

const clearButton = $("clear-logs");
const clearLabel = clearButton.innerHTML;
let clearArmed = false;
let clearTimer = null;

clearButton.addEventListener("click", async () => {
  if (!clearArmed) {
    clearArmed = true;
    clearButton.textContent = "Tap again to confirm";
    clearTimer = setTimeout(() => {
      clearArmed = false;
      clearButton.innerHTML = clearLabel;
    }, 4000);
    return;
  }
  clearArmed = false;
  clearTimeout(clearTimer);
  try {
    await api("/api/logs", { method: "DELETE" });
    toast("Usage logs cleared");
    window.dispatchEvent(new CustomEvent("app:refresh"));
  } catch (e) {
    toast("Failed: " + e.message, true);
  } finally {
    clearButton.innerHTML = clearLabel;
  }
});
