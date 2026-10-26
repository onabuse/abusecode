import { $, api, copyText, toast } from "./lib.js";

const base = location.origin + "/v1";
$("settings-base").textContent = base;
$("copy-settings-base").addEventListener("click", () => copyText(base));

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
