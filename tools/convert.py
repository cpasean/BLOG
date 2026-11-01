"""One-off: convert extracted Wix posts (JSON) into Markdown files with front matter."""
import json, re, sys
from pathlib import Path
from markdownify import markdownify as md

SRC = Path(sys.argv[1])        # folder with posts_*.json
OUT = Path(sys.argv[2])        # content/posts
OUT.mkdir(parents=True, exist_ok=True)
WIX = "https://static.wixstatic.com/media/"

posts = []
for f in sorted(SRC.glob("posts_*.json")):
    posts += json.loads(f.read_text(encoding="utf-8"))

def yq(s):  # YAML-safe double-quoted string
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

for p in posts:
    html = p["h"].replace('src="W:', f'src="{WIX}')
    html = re.sub(r"<u>(.*?)</u>", r"\1", html)           # underline -> plain (links already styled)
    html = re.sub(r"</?figure>", "", html)
    body = md(html, heading_style="ATX", bullets="-", strip=["br"])
    body = re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"
    cat = p["c"] or "Life"
    cover = (WIX + p["v"]) if p["v"] else ""
    fm = [
        "---",
        f"title: {yq(p['t'].strip())}",
        f"date: {p['d']}",
        f"category: {cat}",
    ]
    if cover:
        fm.append(f"cover: {cover}")
    fm.append(f"legacy_url: https://aicpasean.wixsite.com/mysite/post/{p['s']}")
    fm.append("---\n")
    (OUT / f"{p['s']}.md").write_text("\n".join(fm) + "\n" + body, encoding="utf-8")

print(len(posts), "posts written")
