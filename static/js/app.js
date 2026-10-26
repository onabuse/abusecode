import { $, api } from "./lib.js";

const sidebar = $("sidebar");
const backdrop = $("backdrop");
const menuButton = $("menu-toggle");

function setSidebar(open) {
  if (!sidebar || !backdrop) return;
  sidebar.classList.toggle("-translate-x-full", !open);
  backdrop.classList.toggle("hidden", !open);
  menuButton?.setAttribute("aria-expanded", String(open));
  document.body.classList.toggle("overflow-hidden", open);
}

$("menu-toggle")?.addEventListener("click", () => setSidebar(true));
$("sidebar-close")?.addEventListener("click", () => setSidebar(false));
backdrop?.addEventListener("click", () => setSidebar(false));
window.addEventListener("keydown", (e) => e.key === "Escape" && setSidebar(false));
sidebar?.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => setSidebar(false)));
window.addEventListener("resize", () => {
  if (window.innerWidth >= 1024) setSidebar(false);
});

$("global-refresh")?.addEventListener("click", () => {
  window.dispatchEvent(new CustomEvent("app:refresh"));
});

$("logout")?.addEventListener("click", async () => {
  try {
    await api("/api/logout", { method: "POST" });
  } catch {}
  location.href = "/login";
});

const baseOrigin = $("base-origin");
if (baseOrigin) baseOrigin.textContent = location.origin + "/v1";

async function pollHealth() {
  try {
    const h = await api("/api/health");
    $("health").textContent = h.active_keys ? `${h.active_keys} key${h.active_keys > 1 ? "s" : ""}` : "no keys";
    $("health-dot").style.background = h.active_keys ? "#60a5fa" : "#c96a6a";
    $("health").title = `${h.upstream} · v${h.version}`;
  } catch {
    $("health").textContent = "offline";
    $("health-dot").style.background = "#c96a6a";
  }
}

pollHealth();
setInterval(pollHealth, 15000);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js").catch(() => {});
  });
}
