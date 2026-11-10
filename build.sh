#!/usr/bin/env bash
set -euo pipefail

project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
harness_ref=e73ddff77079dc96b2a7af6e7b843a7ecfbbb11a
blender_ref=fe16888d9e1e5eee3070535a221dd9ae2d671a77
harness_url=https://github.com/xreamm1/blender-wasm.git
blender_url=https://github.com/xreamm1/blender.git
sdk=${EMSDK_ROOT:-/emsdk}
jobs=${BUILD_JOBS:-4}
mkdir -p "$project/work"
cd "$project/work"
export GIT_TERMINAL_PROMPT=0
export NPROC="$jobs"
export CMAKE_BUILD_PARALLEL_LEVEL="$jobs"
export EM_PYTHON=/usr/bin/python3
export WASM_CFLAGS="-O3 -pthread -msimd128 -fexceptions"
export WASM_CXXFLAGS="$WASM_CFLAGS"
ulimit -s unlimited

if [[ ! -d upstream/.git ]]; then
  git init -q upstream
  git -C upstream remote add origin "$harness_url"
fi
cd upstream
git remote set-url origin "$harness_url"
if ! git cat-file -e "$harness_ref^{commit}" 2>/dev/null; then
  git fetch --depth 1 origin "$harness_ref"
fi
git checkout --detach "$harness_ref"
ln -sfnT "$sdk" emsdk
export PATH="$sdk/upstream/emscripten:$PATH"
test -x "$sdk/upstream/emscripten/emcc"

make blender BLENDER_URL="$blender_url"
git -C blender remote set-url origin "$blender_url"
if [[ $(git -C blender rev-parse HEAD) != "$blender_ref" ]]; then
  echo "Unexpected Blender source revision in $(pwd)/blender" >&2
  exit 1
fi
patch_file="$project/patches/0001-persist-browser-projects.patch"
if ! git -C blender apply --reverse --check "$patch_file" 2>/dev/null; then
  git -C blender apply "$patch_file"
fi

# This SDK uses emdawnwebgpu (the Blender fork selects the port in CMake).
# Ninja's stock executable link lacks the demo WasmFS symbols. Its final
# command is reused by the release linker with the required browser flags.
make configure-blender EMSDK="$sdk" NPROC="$jobs" BLENDER_URL="$blender_url" \
  WASM_CFLAGS="$WASM_CFLAGS" WASM_CXXFLAGS="$WASM_CXXFLAGS" \
  WASM_COMPAT="-O3 -pthread -fexceptions -include $(pwd)/cmake/wasm_compat.h"
if ! ninja -j "$jobs" -C build-blender blender 2>&1 | tee "$project/work/ninja.log"; then
  grep -Eq '^FAILED:.* bin/blender\.js( |$)' "$project/work/ninja.log" || exit 1
fi

sed 's/^  -O1 /  -O3 /; s/zstd -f --ultra -21 -T0/zstd -f -10 -T2/g' \
  scripts/link_blender_release.sh > scripts/link_blender_real.sh
BLENDER_GPU=webgpu bash scripts/link_blender_real.sh
rm -f demo/public/favicon.svg demo/public/blender-browser-card-354898ad.png

cp -f "$project/src/index.html" "$project/src/package.json" \
  "$project/src/package-lock.json" "$project/src/vite.config.js" demo/
cp -f "$project/src/src/"* demo/src/
cp -f "$project/src/public/isolation-worker.js" demo/public/
(
  cd demo
  npm ci --no-audit --no-fund
  npm run build -- --outDir "$project/dist" --emptyOutDir
)
for artifact in index.html blender.js blender.wasm.zst assets.tar.zst manifest.json; do
  test -s "$project/dist/$artifact"
done
