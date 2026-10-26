import { $, api, copyText, toast } from "./lib.js";

const base = location.origin + "/v1";
$("settings-base").textContent = base;
$("copy-settings-base").addEventListener("click", () => copyText(base));

$("clear-logs").addEventListener("click", async () => {
  if (!confirm("Delete all usage logs? This cannot be undone.")) return;
  try {
    await api("/api/logs", { method: "DELETE" });
    toast("Usage logs cleared");
    window.dispatchEvent(new CustomEvent("app:refresh"));
  } catch (e) {
    toast("Failed: " + e.message, true);
  }
});
