const status = document.getElementById("splash-status");
const mobile = /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent) ||
  navigator.maxTouchPoints > 1;
window.__BLENDER_MOBILE__ = mobile;

function startupError(message) {
  status.textContent = message;
  const row = document.createElement("div");
  row.className = "console-line error";
  row.textContent = message;
  document.getElementById("console-output").append(row);
}

window.addEventListener("error", (event) => {
  if (event.message) startupError(event.message);
});
window.addEventListener("unhandledrejection", (event) => {
  startupError(event.reason?.message || String(event.reason));
});

let startupDeadline;
const splash = document.getElementById("splash");
const observer = new MutationObserver(() => {
  if (splash.classList.contains("done")) {
    clearTimeout(startupDeadline);
    observer.disconnect();
  }
});
observer.observe(splash, { attributes: true, attributeFilter: ["class"] });
document.getElementById("start-btn").addEventListener("click", () => {
  clearTimeout(startupDeadline);
  startupDeadline = setTimeout(() => {
    startupError("Blender is taking longer than expected. Check the startup log for a graphics or memory error. Try an updated Chrome browser and close other tabs before reloading.");
  }, mobile ? 180000 : 90000);
});

try {
  if (!crossOriginIsolated) {
    const workers = navigator.serviceWorker;
    if (!workers || workers.controller) {
      throw new Error("This browser could not enable WebAssembly thread isolation.");
    }
    status.textContent = "Preparing browser isolation…";
    await workers.register("./isolation-worker.js");
    if (!workers.controller) {
      await new Promise((resolve, reject) => {
        const activate = () => { clearTimeout(timeout); resolve(); };
        const timeout = setTimeout(() => {
          workers.removeEventListener("controllerchange", activate);
          reject(new Error("Browser isolation timed out. Reload the page to try again."));
        }, 15000);
        workers.addEventListener("controllerchange", activate, { once: true });
      });
    }
    location.reload();
  } else {
    window.__BARGS = ["--disable-autoexec", ...(mobile ? ["--threads", "2"] : [])];
    window.__CAPENV = {
      MESA_GL_VERSION_OVERRIDE: "4.3",
      MESA_GLSL_VERSION_OVERRIDE: "430",
    };
    await import(document.querySelector("script[data-engine]").dataset.engine);
  }
} catch (error) {
  startupError(error.message);
  document.getElementById("start-btn").disabled = true;
  console.error(error);
}
