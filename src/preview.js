const status = document.getElementById("splash-status");

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
    window.__BARGS = ["--disable-autoexec"];
    window.__CAPENV = {
      MESA_GL_VERSION_OVERRIDE: "4.3",
      MESA_GLSL_VERSION_OVERRIDE: "430",
    };
    await import(document.querySelector("script[data-engine]").dataset.engine);
  }
} catch (error) {
  status.textContent = error.message;
  document.getElementById("start-btn").disabled = true;
  console.error(error);
}
