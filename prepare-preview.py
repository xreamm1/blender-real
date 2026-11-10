"""Package a verified browser release with the Blender Real landing page."""

import argparse
import hashlib
import re
import shutil
import tarfile
from pathlib import Path

DIGEST = "58e1f2b3a6b658094a08a243216201deaf4844e907686c504e6a3bf8bfbdcba4"
ROOT = Path(__file__).resolve().parent


def prepare(archive, output):
    with archive.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != DIGEST:
            raise ValueError("Unexpected browser release digest")

    output.mkdir(parents=True, exist_ok=True)
    (output / "assets").mkdir(exist_ok=True)
    with tarfile.open(archive) as bundle:
        names = bundle.getnames()
        script, = [name for name in names if re.fullmatch(r"dist/assets/index-[\w-]+\.js", name)]
        css, = [name for name in names if re.fullmatch(r"dist/assets/index-[\w-]+\.css", name)]
        for name in (script, css, "dist/blender.js", "dist/blender.wasm.zst",
                     "dist/assets.tar.zst", "dist/manifest.json", "dist/wgsl-cache-gl.bin.zst",
                     "dist/wgsl-cache.json"):
            with bundle.extractfile(name) as source, (output / name[5:]).open("wb") as target:
                shutil.copyfileobj(source, target)

    page = (ROOT / "src/index.html").read_text(encoding="utf-8")
    page = re.sub(r"    <details id=\"browser-projects\".*?</details>\n", "", page, flags=re.S)
    page = page.replace("/src/styles.css", f"./{css[5:]}")
    page = page.replace(
        '<script type="module" src="/src/main.js"></script>',
        f'<script type="module" data-engine="./{script[5:]}" src="./preview.js"></script>',
    )
    (output / "index.html").write_text(page, encoding="utf-8")
    shutil.copyfile(ROOT / "src/public/isolation-worker.js", output / "isolation-worker.js")
    shutil.copyfile(ROOT / "src/preview.js", output / "preview.js")
    shutil.copyfile(ROOT / "LICENSE", output / "LICENSE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    prepare(args.archive, args.output)
