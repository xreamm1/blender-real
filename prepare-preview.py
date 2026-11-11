"""Package a verified browser release with the Blender Real landing page."""

import argparse
import hashlib
import re
import shutil
import tarfile
from pathlib import Path

import zstandard

DIGEST = "58e1f2b3a6b658094a08a243216201deaf4844e907686c504e6a3bf8bfbdcba4"
ROOT = Path(__file__).resolve().parent


def lower_memory_minimum(output):
    path = output / "blender.wasm.zst"
    wasm = bytearray(zstandard.ZstdDecompressor().decompress(path.read_bytes()))

    def read_uint(offset):
        value, shift = 0, 0
        while True:
            byte = wasm[offset]
            offset += 1
            value |= (byte & 127) << shift
            if byte < 128:
                return value, offset
            shift += 7
            if shift > 28:
                raise ValueError("Invalid Wasm section length")

    offset = 8
    while offset < len(wasm):
        kind = wasm[offset]
        length, start = read_uint(offset + 1)
        if kind == 2:
            _, first = read_uint(start)
            signature = b"\x03env\x06memory\x02\x03"
            if wasm[first:first + len(signature)] != signature:
                raise ValueError("Unexpected Wasm memory import")
            minimum = first + len(signature)
            # Keep the original three-byte LEB encoding and section sizes.
            old, new = b"\x80\x80\x01", b"\x80\xc0\x00"
            if wasm[minimum:minimum + 3] == old:
                wasm[minimum:minimum + 3] = new
                path.write_bytes(zstandard.ZstdCompressor(level=10).compress(wasm))
            elif wasm[minimum:minimum + 3] != new:
                raise ValueError("Unexpected Wasm minimum memory")
            return
        offset = start + length
    raise ValueError("Wasm memory import missing")


def prepare(archive, output):
    with archive.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != DIGEST:
            raise ValueError("Unexpected browser release digest")

    output.mkdir(parents=True, exist_ok=True)
    (output / "assets").mkdir(exist_ok=True)
    with tarfile.open(archive) as bundle:
        script, = [name for name in bundle.getnames()
                   if re.fullmatch(r"dist/assets/index-[\w-]+\.js", name)]
        for name in (script, "dist/blender.js", "dist/blender.wasm.zst",
                     "dist/assets.tar.zst", "dist/manifest.json", "dist/wgsl-cache-gl.bin.zst",
                     "dist/wgsl-cache.json"):
            with bundle.extractfile(name) as source, (output / name[5:]).open("wb") as target:
                shutil.copyfileobj(source, target)
    refresh(output)


def refresh(output):
    lower_memory_minimum(output)
    script, = (output / "assets").glob("index-*.js")
    app = script.read_text(encoding="utf-8")
    module_start = "window.Module={arguments:"
    mobile_start = 'window.Module={INITIAL_MEMORY:window.__BLENDER_MOBILE__?536870912:1073741824,arguments:'
    if module_start in app:
        app = app.replace(module_start, mobile_start, 1)
    elif mobile_start not in app:
        raise ValueError("Unexpected preview module initialization")
    script.write_text(app, encoding="utf-8")

    glue_path = output / "blender.js"
    glue = glue_path.read_text(encoding="utf-8")
    pool = "var pthreadPoolSize = 32;"
    mobile_pool = "var pthreadPoolSize = /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent) || navigator.maxTouchPoints > 1 ? 4 : 32;"
    if pool in glue:
        glue = glue.replace(pool, mobile_pool, 1)
    elif mobile_pool not in glue:
        raise ValueError("Unexpected preview pthread initialization")
    glue_path.write_text(glue, encoding="utf-8")
    page = (ROOT / "src/index.html").read_text(encoding="utf-8")
    page = re.sub(r"    <details id=\"browser-projects\".*?</details>\n", "", page, flags=re.S)
    page = page.replace("/src/styles.css", "./loader.css")
    page = page.replace(
        '<script type="module" src="/src/main.js"></script>',
        f'<script type="module" data-engine="./assets/{script.name}" src="./preview.js"></script>',
    )
    (output / "index.html").write_text(page, encoding="utf-8")
    shutil.copyfile(ROOT / "src/src/styles.css", output / "loader.css")
    shutil.copyfile(ROOT / "src/public/isolation-worker.js", output / "isolation-worker.js")
    shutil.copyfile(ROOT / "src/preview.js", output / "preview.js")
    shutil.copyfile(ROOT / "LICENSE", output / "LICENSE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, nargs="?")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.archive:
        prepare(args.archive, args.output)
    else:
        refresh(args.output)
