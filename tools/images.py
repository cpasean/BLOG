"""Shrink big photos uploaded from a phone or camera so pages load fast.

Runs in the deploy workflow before build.py. A JPEG/PNG/WebP in static/images that is wider or taller
than 2400 px, or larger than 1.5 MB, is resized (keeping its shape) and saved under the same name,
so every link to it keeps working. Phone photos are also turned the right way up.
Prints "changed" when files were changed so the workflow commits them back.
"""
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
MAX_SIDE = 2400
MAX_BYTES = 1_500_000


def main():
    changed = False
    for f in sorted((ROOT / "static/images").iterdir()):
        ext = f.suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"} or not f.is_file():
            continue
        size = f.stat().st_size
        try:
            im = Image.open(f)
            im.load()
        except Exception:
            continue
        if max(im.size) <= MAX_SIDE and size <= MAX_BYTES:
            continue
        im = ImageOps.exif_transpose(im)
        im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        tmp = f.with_name(f.stem + ".tmp" + ext)
        if ext in {".jpg", ".jpeg"}:
            im.convert("RGB").save(tmp, "JPEG", quality=82, optimize=True, progressive=True)
        elif ext == ".webp":
            im.save(tmp, "WEBP", quality=82)
        else:
            im.save(tmp, "PNG", optimize=True)
        if tmp.stat().st_size < size:
            tmp.replace(f)
            changed = True
            print(f"resized {f.name}: {size:,} -> {f.stat().st_size:,} bytes")
        else:
            tmp.unlink()
    if changed:
        print("changed")


if __name__ == "__main__":
    main()
