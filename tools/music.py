"""Background music: shrink uploaded audio to a web-friendly size and switch the player to it.

Runs in the deploy workflow before build.py.
  1. Any audio file dropped into music-upload/ (via GitHub web "Upload files") is compressed
     to static/music/<name>.mp3, the original is removed, and content/music.yml is pointed at it.
  2. If the file set in the editor (content/music.yml) is still large, it is compressed in place.
Prints "changed" when files were changed so the workflow commits them back.
"""
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
UPLOAD = ROOT / "music-upload"
OUTDIR = ROOT / "static/music"
CONF = ROOT / "content/music.yml"
AUDIO = {".mp3", ".m4a", ".aac", ".wav", ".ogg", ".flac", ".wma", ".aiff", ".aif"}
BITRATE = "96k"            # ~0.7 MB per minute, still clear for background music
MAX_KEEP = 4 * 1024 * 1024  # files at or under 4 MB are left as they are


def slug(name):
    s = re.sub(r"[^\w]+", "-", name.lower(), flags=re.UNICODE).strip("-")
    s = re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9-]", "", s)).strip("-")  # keep URLs plain ASCII
    return s or "music"


def compress(src, dst):
    tmp = dst.with_suffix(".tmp.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vn", "-map_metadata", "-1",
                    "-ac", "2", "-ar", "44100", "-codec:a", "libmp3lame", "-b:a", BITRATE, str(tmp)], check=True)
    tmp.replace(dst)
    print(f"compressed {src.name}: {src.stat().st_size if src.exists() else 0:,} -> {dst.stat().st_size:,} bytes",
          file=sys.stderr)


def newest_upload(files):
    """The most recently committed upload wins when several are present."""
    def when(p):
        out = subprocess.run(["git", "log", "-1", "--format=%ct", "--", str(p)], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip()
        return int(out or 0)
    return max(files, key=lambda p: (when(p), p.name))


def main():
    conf = yaml.safe_load(CONF.read_text(encoding="utf-8")) if CONF.exists() else {}
    conf = conf or {}
    changed = False

    uploads = [p for p in UPLOAD.glob("*") if p.is_file() and p.suffix.lower() in AUDIO] if UPLOAD.exists() else []
    if uploads:
        src = newest_upload(uploads)
        OUTDIR.mkdir(parents=True, exist_ok=True)
        for old in OUTDIR.glob("*.mp3"):  # keep only the current track
            old.unlink()
        dst = OUTDIR / f"{slug(src.stem)}.mp3"
        compress(src, dst)
        for p in uploads:
            p.unlink()
        conf["file"] = f"/music/{dst.name}"
        conf["title"] = src.stem.replace("_", " ").strip()
        changed = True
    else:
        f = (conf.get("file") or "").strip()
        path = ROOT / "static" / f.lstrip("/") if f.startswith("/") else None
        if path and path.exists() and (path.stat().st_size > MAX_KEEP or path.suffix.lower() != ".mp3"):
            dst = path.with_suffix(".mp3")
            src = path.rename(path.with_name(path.stem + ".orig" + path.suffix))
            compress(src, dst)
            src.unlink()
            conf["file"] = "/" + str(dst.relative_to(ROOT / "static")).replace("\\", "/")
            changed = True

    if changed:
        CONF.write_text(
            "# 배경음악 — 편집기(✎ Write → Background music)에서 올리거나, GitHub의 music-upload 폴더에 올리면\n"
            "# 자동으로 웹용 크기로 줄여서 홈 오른쪽 아래 재생 버튼에 연결됩니다.\n"
            + yaml.safe_dump({"title": conf.get("title", ""), "file": conf.get("file", "")},
                             allow_unicode=True, sort_keys=False),
            encoding="utf-8")
        print("changed")


if __name__ == "__main__":
    main()
