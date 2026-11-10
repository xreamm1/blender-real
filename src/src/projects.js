const root = "/projects/";
const panel = document.getElementById("browser-projects");
const status = document.getElementById("project-status");
const input = document.getElementById("project-import");
const buttons = panel.querySelectorAll("button");

function projectPath(path) {
  const name = path.slice(root.length);
  if (!path.startsWith(root) || !/^[^/\\\u0000]+\.blend$/i.test(name)) {
    throw new Error("Use a .blend filename directly inside /projects.");
  }
  return path;
}

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("blender-real-projects", 1);
    request.onupgradeneeded = () => request.result.createObjectStore("projects");
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    request.onblocked = () => reject(new Error("Close other Blender tabs and reload."));
  });
}

export async function setupProjects(module) {
  const report = (error) => {
    status.textContent = error.message;
    console.error(error);
  };
  try {
    const db = await openDatabase();
    db.onversionchange = () => db.close();
    module.FS.mkdir("/projects");

    await new Promise((resolve, reject) => {
      const tx = db.transaction("projects");
      const cursor = tx.objectStore("projects").openCursor();
      cursor.onsuccess = () => {
        const row = cursor.result;
        if (!row) return;
        try {
          module.FS.writeFile(projectPath(row.key), row.value);
          row.continue();
        } catch (error) {
          tx.abort();
          reject(error);
        }
      };
      tx.oncomplete = resolve;
      tx.onabort = () => reject(tx.error ?? new Error("Project restore aborted."));
    });

    function persist(path, bytes, replace) {
      return new Promise((resolve, reject) => {
        const tx = db.transaction("projects", "readwrite");
        const store = tx.objectStore("projects");
        if (replace) store.put(bytes, path);
        else store.add(bytes, path);
        tx.oncomplete = resolve;
        tx.onabort = () => reject(tx.error?.name === "ConstraintError"
          ? new Error("That project already exists. Rename the file before importing.")
          : tx.error ?? new Error("Project save aborted."));
      });
    }

    window.blenderPersistProject = (path) => {
      try {
        projectPath(path);
        const bytes = module.FS.readFile(path);
        status.textContent = "Saving to browser storage…";
        persist(path, bytes, true).then(() => {
          status.textContent = "Saved to browser storage.";
        }).catch(report);
      } catch (error) {
        report(error);
      }
    };

    function browse(mode) {
      module.ccall(`blender_web_file_${mode}_at`, null, ["string"], [root]);
      module.canvas.focus();
    }

    document.getElementById("project-open").onclick = () => browse("open");
    document.getElementById("project-save").onclick = () => browse("save");
    input.onchange = async () => {
      const [file] = input.files;
      if (!file) return;
      input.value = "";
      input.disabled = true;
      try {
        const path = projectPath(root + file.name);
        const bytes = new Uint8Array(await file.arrayBuffer());
        await persist(path, bytes, false);
        module.FS.writeFile(path, bytes);
        status.textContent = `Imported ${file.name}.`;
        browse("open");
      } catch (error) {
        report(error);
      } finally {
        input.disabled = false;
      }
    };
    for (const button of buttons) button.disabled = false;
    input.disabled = false;
    status.textContent = "Browser storage ready.";
  } catch (error) {
    report(error);
  }
}
