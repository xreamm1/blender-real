# Blender Real by xreamm

Build the Blender 5.3 browser port from C/C++ and run its UI in a single browser tab. The pinned Blender fork contains the GHOST web backend, browser input callbacks, OffscreenCanvas window, and native WebGPU rendering backend. This repository adds the container build, frontend, local server, and IndexedDB project library.

## Build and run

Use an x86-64 Linux Docker engine with several hours available. Budget at least 50 GB of free disk and 24 GB of available RAM for dependencies, Blender objects, and the final optimized link.

```sh
docker build -t blender-real .
docker run --rm --init --mount "type=bind,src=$PWD,dst=/project" blender-real
python3 serve.py
```

In Windows PowerShell, use `python serve.py`. Open `http://localhost:8080` in a recent WebGPU-enabled desktop browser, then click **Launch Blender**. The build keeps intermediates in `work/` and writes the site to `dist/`. Set `-e BUILD_JOBS=2` on the Docker run if memory is constrained. If using an alternate server, serve the same-origin assets over HTTPS or localhost, with `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp`.

The **Build Blender for the browser** GitHub Actions workflow is manually runnable. It uploads `dist/` as an artifact and publishes successful builds from `main` to [GitHub Pages](https://xreamm1.github.io/blender-real/). On Pages the frontend installs a same-origin service worker to add the isolation headers, then reloads once. If the hosted runner runs out of disk, memory, or time, use a runner with the resources above.

## Projects

Expand **Browser projects** after the viewport appears. **Import .blend** copies a local file into browser storage, and **Open** opens Blender's file browser in `/projects/`. Use **Save as** and save the file directly inside that folder. Subsequent Blender saves to that path update IndexedDB. Wait for **Saved to browser storage** before closing the tab. Files are scoped to the site's origin. The upstream local-folder workflow remains available through Blender's File menu on supported browsers.

The pinned port uses Emscripten WasmFS for assets and browser I/O. IndexedDB stores the project bytes directly through a small JS bridge because Emscripten's legacy IDBFS is unavailable with WasmFS. The frontend disables automatic execution of Python embedded in imported projects.

## Source and compatibility

- The [browser integration fork](https://github.com/xreamm1/blender-wasm/tree/e73ddff77079dc96b2a7af6e7b843a7ecfbbb11a) supplies dependency builds, asset packaging, and the base SPA.
- The [pinned Blender fork](https://github.com/xreamm1/blender/tree/fe16888d9e1e5eee3070535a221dd9ae2d671a77) supplies [GHOST browser input](https://github.com/xreamm1/blender/blob/fe16888d9e1e5eee3070535a221dd9ae2d671a77/intern/ghost/intern/GHOST_SystemWeb.cc) and the [WebGPU context](https://github.com/xreamm1/blender/blob/fe16888d9e1e5eee3070535a221dd9ae2d671a77/source/blender/gpu/webgpu/webgpu_context.cc). The patch in `patches/` connects successful native saves to browser storage.
- Emscripten 6.0.1 uses `--use-port=emdawnwebgpu` in place of the removed `-sUSE_WEBGPU=1`. The browser link uses `-O3`, pthreads, `-sPROXY_TO_PTHREAD=1`, and `-sALLOW_MEMORY_GROWTH=1`. [Emscripten settings](https://github.com/emscripten-core/emscripten/blob/6.0.1/tools/settings.py)

This is an experimental Blender port. The selected WebGPU configuration disables Cycles and several desktop integrations. The full container build and browser runtime have yet to be verified for this repository.

See [LICENSE](LICENSE) and the pinned source repositories for upstream license and attribution details.
