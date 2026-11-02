#!/usr/bin/env python3
"""Sean Yeon blog — static site builder.

    python build.py            # builds ./dist for deployment (pretty URLs)
    python build.py --preview  # builds ./preview with explicit index.html links

Write a post: add content/posts/<slug>.md with front matter
(title, date, category: Work|Life, optional cover, math: true).
"""
import html, re, shutil, sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import markdown
import yaml
from pygments.formatters import HtmlFormatter

ROOT = Path(__file__).parent
PREVIEW = "--preview" in sys.argv
OUT = ROOT / ("preview" if PREVIEW else "dist")
SITE = yaml.safe_load((ROOT / "site.yml").read_text(encoding="utf-8"))
SITE["url"] = SITE["url"].rstrip("/")
import hashlib
SITE_JS_VER = hashlib.md5((ROOT / "static/site.js").read_bytes()).hexdigest()[:8]

# ---------------------------------------------------------------- content
FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.S)


def load(path):
    m = FM.match(path.read_text(encoding="utf-8"))
    return yaml.safe_load(m.group(1)), m.group(2)


def render_md(text):
    return markdown.markdown(
        text,
        extensions=["extra", "sane_lists", "codehilite", "toc"],
        extension_configs={"codehilite": {"guess_lang": False, "css_class": "hl"}},
    )


def plain(html_text):
    return html.unescape(re.sub(r"<[^>]+>", " ", html_text)).split()


posts = []
for f in sorted((ROOT / "content/posts").glob("*.md")):
    meta, body = load(f)
    if meta.get("draft"):
        continue
    body_html = render_md(body)
    words = plain(body_html)
    first_p = re.search(r"<p>(.*?)</p>", body_html, re.S)
    excerpt = " ".join(plain(first_p.group(1))) if first_p else ""
    imgs = re.findall(r'<img[^>]+src="([^"]+)"', body_html)
    d = meta["date"]
    d = d if isinstance(d, datetime) else datetime(d.year, d.month, d.day, 12, tzinfo=timezone.utc)
    posts.append({
        "slug": f.stem,
        "title": str(meta["title"]).strip(),
        "date": d,
        "category": meta.get("category", "Life"),
        "cover": meta.get("cover") or (imgs[0] if imgs else ""),
        "math": meta.get("math") or ("$$" in body or "\\(" in body),
        "html": body_html,
        "excerpt": (excerpt[:180] + "…") if len(excerpt) > 180 else excerpt,
        "minutes": max(1, round(len(words) / 220)),
        "words": len(words),
        "featured": bool(meta.get("featured")),
        "views": int(meta.get("views") or 0),
        "likes": int(meta.get("likes") or 0),
    })

posts.sort(key=lambda p: p["date"], reverse=True)
for i, p in enumerate(posts):
    p["no"] = len(posts) - i  # ledger entry number, oldest = 1

# comment counts (written by the deploy workflow from GitHub Discussions; missing file = 0)
try:
    import json as _json
    COMMENTS = _json.loads((ROOT / "data/comments.json").read_text(encoding="utf-8"))
except Exception:
    COMMENTS = {}
for p in posts:
    p["comments"] = int(COMMENTS.get(p["slug"], 0))

about_meta, about_body = load(ROOT / "content/about.md")

# ---------------------------------------------------------------- links


def href(root, path):
    """path like '' , 'journal/', 'post/x/' -> relative link from a page at depth root."""
    if PREVIEW and (path == "" or path.endswith("/")):
        path = path + "index.html"
    return root + path if path else (root or "./")


def fix_paths(text, root):
    text = re.sub(r'(src|href|poster)="/(?!/)', lambda m: f'{m.group(1)}="{root}', text)
    return re.sub(r"url\(/(?!/)", f"url({root}", text)


def esc(s):
    return html.escape(str(s), quote=True)


def fmt_date(d):
    return d.strftime("%Y-%m-%d")


# ---------------------------------------------------------------- style
CSS = r"""
:root{
  /* Ledger book: green-ruled columns, ink, a red-ink mark. Masthead + single reading column. */
  --paper:#F5F7F3; --sheet:#FBFCFA; --ink:#18211D; --muted:#5B6862; --rule:#D6E0D8; --rule-strong:#B9C9BE;
  --green:#1E6A4E; --green-soft:#E3EEE7; --red:#B03A2E;
  --sun:#FFEC9B; --sun-ink:#2B2615; --blush:#FFE0E0; --plum:#4E2A9A;
  --script:"Pinyon Script","Snell Roundhand","Apple Chancery",cursive;
  --display:"IBM Plex Sans Condensed","Arial Narrow",Arial,sans-serif;
  --body:"Source Serif 4",Georgia,"Times New Roman",serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;
  --measure:40rem;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#0F1513; --sheet:#141B18; --ink:#E2E9E4; --muted:#93A39A; --rule:#24302B; --rule-strong:#33443C;
  --green:#6CC39C; --green-soft:#1A2A23; --red:#E58273; --sun:#3A3320; --sun-ink:#F4E9C0; --blush:#3A2629; --plum:#C2AAF5; color-scheme:dark}}
:root[data-theme="dark"]{
  --paper:#0F1513; --sheet:#141B18; --ink:#E2E9E4; --muted:#93A39A; --rule:#24302B; --rule-strong:#33443C;
  --green:#6CC39C; --green-soft:#1A2A23; --red:#E58273; --sun:#3A3320; --sun-ink:#F4E9C0; --blush:#3A2629; --plum:#C2AAF5; color-scheme:dark}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;overflow-x:clip;background:var(--paper);color:var(--ink);font:17px/1.7 var(--body);
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
a{color:var(--green);text-underline-offset:3px;text-decoration-thickness:1px}
a:hover{text-decoration-thickness:2px}
a:focus-visible,button:focus-visible{outline:2px solid var(--green);outline-offset:3px;border-radius:2px}
img{max-width:100%;height:auto}
.wrap{max-width:62rem;margin:0 auto}

/* masthead — Wix "Business Doctor" identity */
.mast{text-align:center;padding-block:1.8rem 0}
.kicker{margin:0;font:500 .74rem/1.4 var(--display);letter-spacing:.42em;text-transform:uppercase;color:var(--ink);padding-left:.42em}
.brand{display:inline-block;margin:.35rem 0 .2rem;font:400 clamp(2.8rem,8vw,4.6rem)/1.15 var(--script);color:var(--plum);text-decoration:none;
  text-shadow:2px 2px 0 color-mix(in srgb,var(--plum) 18%,transparent)}
.brand:hover{text-decoration:none}
.nav{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid var(--ink);border-bottom:1px solid var(--ink);margin-top:.8rem;
  font:500 .92rem/1 var(--display);letter-spacing:.06em}
.nav a{color:var(--ink);text-decoration:none;padding-block:.85rem}
.nav a+a{border-left:1px solid var(--ink)}
.nav a[aria-current="page"]{color:var(--plum)}
.nav a:hover{background:var(--green-soft)}
.nav a.write{color:var(--green)}

/* full-bleed photo bands restored from Wix */
.bleed{width:100vw;margin-left:calc(50% - 50vw)}
.band{min-height:clamp(12rem,38vw,30rem);background:var(--sheet) center/cover no-repeat}
@media (min-width:900px) and (prefers-reduced-motion:no-preference){.band.fixed{background-attachment:fixed}}
.band.thin{min-height:clamp(7rem,14vw,11rem)}
.split{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);margin-top:1.6rem}
.split .photo{min-height:clamp(18rem,40vw,30rem);background:var(--sheet) center/cover no-repeat}
.split .panel{background:var(--sun);display:grid;place-content:center;gap:1.4rem;text-align:center;padding:2.5rem 1.5rem}
.panel h2{margin:0;font:italic 400 clamp(1.8rem,3.4vw,2.5rem)/1.1 var(--body);letter-spacing:.12em;color:var(--sun-ink)}
.panel nav{display:grid;gap:1rem;font:500 .95rem var(--display);letter-spacing:.04em}
.panel a{color:var(--sun-ink);text-decoration:none}
.panel a:hover{text-decoration:underline}
.blush{background:var(--blush);padding-block:2.6rem}
.blush .in{max-width:var(--measure);margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.blush p{margin:0 0 .9rem}
.blush .sig{font:italic 1.05rem var(--body);margin:1.2rem 0 0}
.follow{display:flex;flex-wrap:wrap;gap:.6rem;margin-top:1rem}
.btn{display:inline-block;font:500 .85rem/1 var(--display);letter-spacing:.06em;text-transform:uppercase;padding:.75rem 1.1rem;border:1px solid var(--ink);color:var(--ink);text-decoration:none;background:transparent;cursor:pointer}
.btn.solid{background:var(--ink);color:var(--paper)}
.btn:hover{background:var(--ink);color:var(--paper)}

/* train of thought + sidebar */
.tot{display:grid;grid-template-columns:minmax(0,1fr) 17rem;gap:0 2.5rem;padding-top:2.4rem}
.tot>div{min-width:0}
.tot aside{border-left:1px solid var(--ink);padding-left:2rem;display:grid;gap:2.2rem;align-content:start}
.eyebrow{margin:0 0 1rem;font:500 .95rem/1.3 var(--display);letter-spacing:.32em;text-transform:uppercase}
.side img,.side video{display:block;width:100%;height:auto;border:1px solid var(--rule)}
.side p{margin:.8rem 0 0;font-size:.95rem}
.side .mot{font-style:italic;font-size:.95rem;line-height:1.6}
.side .more{font:500 .88rem var(--display)}
.side+.side{border-top:1px solid var(--ink);padding-top:1.8rem}
.pick{white-space:pre-line;text-align:center;font-size:.92rem;line-height:1.55;margin-top:1rem}
.pick a{font:600 .95rem var(--display);text-decoration:underline}
.contact{background:var(--sun);color:var(--sun-ink);text-align:center;padding-block:3.5rem}
.contact h2{margin:0 0 1rem;font:italic 400 clamp(2rem,4.5vw,3rem)/1.1 var(--body);letter-spacing:.14em}
.contact p{margin:.2rem 0;font:.95rem var(--display)}
.contact form{max-width:28rem;margin:1.8rem auto 0;display:grid;gap:.6rem;text-align:left;padding-inline:16px}
.contact input,.contact textarea{font:inherit;font-size:.95rem;padding:.6rem .7rem;border:1px solid color-mix(in srgb,var(--sun-ink) 25%,transparent);background:var(--sheet);color:var(--ink);width:100%}
.contact textarea{min-height:7rem;resize:vertical}
.contact .btn{justify-self:center;border-color:var(--sun-ink);color:var(--sun-ink)}
.contact .btn:hover{background:var(--sun-ink);color:var(--sun)}
.contact .addr{user-select:all}
.about-banner{margin:1.6rem 0 0}
.about-banner img{display:block;width:100%;height:auto}

/* home */
.hero{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:2rem 3rem;padding-block:3rem 2.5rem;align-items:end}
.hero h1{font:600 clamp(2.2rem,5.5vw,3.6rem)/1.02 var(--display);letter-spacing:-.01em;margin:0;text-wrap:balance}
.hero h1 em{font-style:normal;color:var(--green)}
.hero p{margin:1rem 0 0;color:var(--muted);max-width:32rem}
.motto{margin:0;padding:1rem 0 1rem 1.1rem;border-left:2px solid var(--red);font:italic 1.05rem/1.6 var(--body);color:var(--ink)}
.motto span{display:block}
.motto cite{display:block;margin-top:.5rem;font:500 .72rem/1 var(--mono);font-style:normal;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.accounts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));border-top:1px solid var(--rule-strong);border-bottom:1px solid var(--rule-strong)}
.accounts a{display:block;padding:1rem 1.2rem 1.1rem 0;text-decoration:none;color:var(--ink)}
.accounts a+a{padding-left:1.2rem;border-left:1px solid var(--rule)}
.acct-code{font:500 .72rem/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--green)}
.accounts strong{display:block;font:600 1.35rem/1.2 var(--display);margin-top:.4rem}
.accounts span.d{display:block;color:var(--muted);font-size:.92rem}
.accounts .bal{font:500 .85rem var(--mono);font-variant-numeric:tabular-nums;color:var(--muted)}

/* ledger table */
.sect{display:flex;justify-content:space-between;align-items:baseline;gap:1rem;margin:3rem 0 .6rem}
.sect h2{font:600 1.05rem/1 var(--display);letter-spacing:.12em;text-transform:uppercase;margin:0}
.sect a{font:500 .9rem var(--display)}
.ledger{list-style:none;margin:0;padding:0;border-top:2px solid var(--ink)}
.ledger li{border-bottom:1px solid var(--rule)}
.ledger a.row{display:grid;grid-template-columns:3.2rem 6.6rem 4.4rem minmax(0,1fr) 3rem;gap:0 1rem;align-items:baseline;
  padding-block:.85rem;text-decoration:none;color:var(--ink);
  background-image:linear-gradient(var(--rule),var(--rule));background-size:1px 100%;background-repeat:no-repeat;background-position:3.7rem 0}
.ledger a.row:hover{background-color:var(--green-soft)}
.no,.dt,.mins{font:400 .82rem/1.5 var(--mono);font-variant-numeric:tabular-nums;color:var(--muted)}
.no{text-align:right;padding-right:.2rem}
.mins{text-align:right}
.cat{font:500 .7rem/1.6 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--green)}
.cat.life{color:var(--red)}
.ttl{font:600 1.12rem/1.35 var(--display);min-width:0}
.ex{grid-column:4/6;color:var(--muted);font-size:.93rem;line-height:1.55;margin-top:.15rem}
.filters{display:flex;flex-wrap:wrap;gap:.5rem;margin:.2rem 0 1rem}
.filters button{font:500 .85rem/1 var(--display);letter-spacing:.04em;padding:.5rem .9rem;border:1px solid var(--rule-strong);background:var(--sheet);color:var(--ink);border-radius:999px;cursor:pointer}
.filters button[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.page-h{padding-block:2.6rem 1rem}
.page-h h1{font:600 clamp(2rem,4.5vw,2.8rem)/1.05 var(--display);margin:0}
.page-h p{color:var(--muted);margin:.5rem 0 0}

/* article */
.post{max-width:var(--measure);margin:0 auto;padding-block:2.6rem 1rem}
.meta{display:flex;flex-wrap:wrap;gap:.4rem 1rem;font:400 .82rem/1.4 var(--mono);color:var(--muted);font-variant-numeric:tabular-nums}
.meta .cat{font-size:.78rem}
.post h1{font:600 clamp(2rem,4.6vw,2.9rem)/1.08 var(--display);letter-spacing:-.005em;margin:.7rem 0 1.6rem;text-wrap:balance}
.prose{overflow-wrap:anywhere}
.prose>*+*{margin-top:1.1em}
.prose p{margin:0}
.prose h2,.prose h3{font-family:var(--display);line-height:1.25;margin-top:2em;text-wrap:balance}
.prose h2{font-size:1.5rem}.prose h3{font-size:1.25rem}
.prose ul,.prose ol{padding-left:1.3rem;margin-bottom:0}
.prose li+li{margin-top:.35em}
.prose li p{margin:0}
.prose blockquote{margin-left:0;padding-left:1rem;border-left:2px solid var(--red);font-style:italic}
.prose img{display:block;margin-inline:auto;border:1px solid var(--rule);background:var(--sheet)}
.prose p:has(> img:only-child){margin-top:1.6em;margin-bottom:.5em}
.tbl{overflow-x:auto}
.prose table{border-collapse:collapse;width:100%;font-size:.93rem}
.prose th,.prose td{text-align:left;padding:.55rem .7rem;border-bottom:1px solid var(--rule);vertical-align:top}
.prose th{font:600 .78rem var(--mono);letter-spacing:.08em;text-transform:uppercase;border-bottom:2px solid var(--ink)}
.prose code{font:.88em var(--mono);background:var(--green-soft);padding:.1em .3em;border-radius:3px}
.prose pre{overflow-x:auto;padding:1rem;background:var(--sheet);border:1px solid var(--rule);border-radius:4px;font-size:.86rem;line-height:1.55}
.prose pre code{background:none;padding:0}
.legacy{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--rule);font:400 .8rem/1.5 var(--mono);color:var(--muted)}
.pager{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem;margin-top:1.4rem;border-top:2px solid var(--ink);padding-top:1rem}
.pager a{text-decoration:none;color:var(--ink);min-width:0}
.pager .lbl{display:block;font:500 .72rem var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.pager .t{font:600 1rem/1.35 var(--display)}
.pager .next{text-align:right;grid-column:2}

/* about */
.about{display:grid;grid-template-columns:minmax(0,var(--measure));padding-block:2.6rem 1rem;justify-content:center}
.about figure{margin:0}
.about figure img{border:1px solid var(--rule);filter:grayscale(.15)}
.about figcaption{font:500 .72rem/1.5 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:.6rem}
.about h1{font:600 2.6rem/1.05 var(--display);margin:0 0 1rem}

.subform{display:grid;gap:.55rem;margin-top:1rem;max-width:22rem}
.subform label{font:500 .9rem var(--display)}
.subform input{font:inherit;font-size:1rem;padding:.6rem .1rem;border:0;border-bottom:2px solid #E0337A;background:transparent;color:var(--ink)}
.subform input:focus{outline:none;border-bottom-color:var(--plum)}
.subform button{font:500 1rem/1 var(--display);padding:.95rem 1rem;border:0;background:#6A00F4;color:#fff;cursor:pointer}
.subform button:hover{background:#5200BE}
.subform small{color:var(--muted);font-size:.8rem}
.post .subform{max-width:26rem;margin:1.6rem 0 2rem}
details.other{margin-top:2rem;border-top:1px solid var(--rule);padding-top:1rem}
details.other summary{cursor:pointer;font:500 .95rem var(--display);color:var(--muted)}
.music{position:fixed;right:max(16px,env(safe-area-inset-right,0px));bottom:calc(16px + env(safe-area-inset-bottom,0px));z-index:20;display:flex;flex-direction:column;align-items:flex-end;gap:.5rem}
.music button{display:inline-flex;align-items:center;gap:.55rem;font:500 .85rem/1 var(--display);letter-spacing:.03em;padding:.7rem 1rem;border:1px solid var(--ink);border-radius:999px;background:var(--paper);color:var(--ink);cursor:pointer;box-shadow:0 4px 14px color-mix(in srgb,var(--ink) 18%,transparent)}
.music button:hover{background:var(--ink);color:var(--paper)}
.music .eq{display:inline-flex;gap:2px;align-items:flex-end;height:12px}
.music .eq i{width:3px;background:currentColor;height:4px}
.music[data-playing] .eq i{animation:eq 1s ease-in-out infinite}.music .eq i:nth-child(2){animation-delay:.2s}.music .eq i:nth-child(3){animation-delay:.4s}
@keyframes eq{50%{height:12px}}
@media (prefers-reduced-motion:reduce){.music .eq i{animation:none!important}}
.music .frame{width:min(352px,calc(100vw - 32px));border-radius:12px;overflow:hidden;box-shadow:0 8px 24px color-mix(in srgb,var(--ink) 25%,transparent)}
.music iframe{display:block;width:100%;height:80px;border:0}
.music .frame[hidden]{display:block!important;position:absolute;width:1px;height:1px;overflow:hidden;opacity:0;pointer-events:none}
/* Wix home: photo tiles */
.tiles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:3px;margin-top:1.6rem}
.tile{position:relative;display:block;aspect-ratio:1/1;overflow:hidden;background:#9a9a9a;color:#fff;text-decoration:none}
.tile img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.tile .veil{position:absolute;inset:0;display:flex;flex-direction:column;padding:1.6rem 1.7rem 1.3rem;background:rgba(120,120,120,.55);transition:background .2s}
.tile:hover .veil{background:rgba(70,70,70,.62)}
.tile .by{font:400 .78rem/1.4 var(--display)}
.tile .by span{opacity:.9}
.tile h3{margin:auto 0 .9rem;font:500 clamp(1.15rem,2vw,1.55rem)/1.2 var(--display);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.tile hr,.feat hr,.lcard hr{border:0;border-top:1px solid currentColor;opacity:.45;margin:0 0 .8rem;width:100%}
.stats{display:flex;align-items:center;gap:1.1rem;font:400 .82rem/1 var(--display)}
.stats>span{display:inline-flex;align-items:center;gap:.35rem}
.stats svg{width:17px;height:17px}
.stats .hrt{margin-left:auto;color:#E8455B}
.stats .hrt b{font-weight:400;color:currentColor}
/* featured slider + sea videos */
.feat{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:.4rem;margin-top:2rem;align-items:start}
.slider{position:relative;border:1px solid var(--ink);overflow:hidden}
.slider .track{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none}
.slider .track::-webkit-scrollbar{display:none}
.slide{flex:0 0 100%;scroll-snap-align:start;min-width:0}
.slide a{display:block;color:var(--ink);text-decoration:none}
.slide .ph{aspect-ratio:16/11;background:var(--sheet);overflow:hidden}
.slide .ph img{width:100%;height:100%;object-fit:contain;background:#fff}
.slide .tx{padding:1.4rem 1.6rem 1.3rem}
.dl{margin:0 0 .8rem;font:400 .85rem/1.3 var(--display);color:var(--muted)}
.slide h3,.lcard h3{margin:0 0 .7rem;font:600 1.55rem/1.25 var(--display);text-wrap:balance}
.slide .ex,.lcard .ex{margin:0 0 1.3rem;font:400 1rem/1.6 var(--display);color:var(--muted);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.arw{position:absolute;top:calc((100% - 13rem) / 2);transform:translateY(-50%);width:2.6rem;height:3.4rem;border:0;background:transparent;color:#2B4CC9;font:300 3.2rem/1 var(--body);cursor:pointer}
.arw.prev{left:.4rem}.arw.next{right:.4rem}
.arw:hover{color:var(--plum)}
.fr{min-width:0}
.clips{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.4rem}
.clips video{width:100%;aspect-ratio:1/1;object-fit:cover;display:block;background:#000}
.sea{text-align:center;padding:1rem .8rem 0;font:400 1.02rem/1.75 var(--display)}
.sea p{margin:0 0 1rem}
/* TRAIN OF THOUGHT / Journal cards */
.tot-h{margin:0;font:400 1.35rem/1.2 var(--display);letter-spacing:.42em}
.cardlist{list-style:none;margin:2rem 0 0;padding:0;display:grid;gap:2rem}
.lcard{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);border:1px solid var(--ink);color:var(--ink);text-decoration:none;min-height:20rem;transition:box-shadow .15s}
.lcard:hover{box-shadow:0 6px 18px color-mix(in srgb,var(--ink) 15%,transparent)}
.lcard.noimg{grid-template-columns:minmax(0,1fr);min-height:0}
.lcard.noimg hr{margin-top:1rem}
.lcard .ph{position:relative;overflow:hidden;background:#fff;border-right:1px solid var(--rule)}
.lcard .ph img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:top}
.lcard:not(.noimg){height:21.5rem}
.lcard .tx{display:flex;flex-direction:column;padding:2.2rem 1.8rem 1.4rem;min-width:0}
.lcard .tx .stats{margin-top:0}
.lcard.noimg .tx{padding:2.4rem 1.8rem 1.4rem}
.lcard hr{margin-top:auto}
.lcard .tx .stats,.slide .stats{color:var(--ink)}
@media (max-width:760px){
  .tiles{grid-template-columns:repeat(2,minmax(0,1fr))}
  .tile .veil{padding:1rem}
  .feat{grid-template-columns:minmax(0,1fr)}
  .lcard{grid-template-columns:minmax(0,1fr);min-height:0}
  .lcard:not(.noimg){height:auto}
  .lcard .ph{aspect-ratio:4/3;border-right:0;border-bottom:1px solid var(--rule)}
  .arw{top:calc((100vw - 32px) * 11 / 32)}
}
.poststats{margin-top:2.5rem;padding-top:1rem;border-top:1px solid var(--rule)}
.comments{margin-top:3rem}
/* footer */
.foot{margin-top:4rem;border-top:3px double var(--rule-strong);padding-block:1.4rem 2.4rem;display:flex;flex-wrap:wrap;justify-content:space-between;gap:.8rem 2rem;
  font:400 .82rem/1.6 var(--mono);color:var(--muted)}
.foot .addr{user-select:all}

@media (max-width:760px){
  body{font-size:16.5px}
  .hero{grid-template-columns:minmax(0,1fr);padding-block:2rem 1.8rem}
  .about{grid-template-columns:minmax(0,1fr)}
  .about figure{max-width:12rem}
  .ledger a.row{grid-template-columns:2.4rem minmax(0,1fr) auto;background-position:2.9rem 0}
  .ledger .no{grid-row:1/4}
  .ledger .dt{grid-column:2;grid-row:1}
  .ledger .cat{grid-column:3;grid-row:1;text-align:right}
  .ledger .ttl{grid-column:2/4;grid-row:2}
  .ledger .mins{display:none}
  .ex{grid-column:2/4;grid-row:3}
  .accounts{grid-template-columns:minmax(0,1fr)}
  .split,.tot{grid-template-columns:minmax(0,1fr)}
  .tot aside{border-left:0;padding-left:0;border-top:1px solid var(--ink);padding-top:2rem;margin-top:2.5rem}
  .kicker{letter-spacing:.24em;font-size:.66rem}
  .nav{font-size:.82rem;letter-spacing:.02em}
  .accounts a+a{padding-left:0;border-left:0;border-top:1px solid var(--rule)}
}
@media (prefers-reduced-motion:no-preference){.ledger a.row{transition:background-color .15s}}
"""

HL_CSS = HtmlFormatter(style="friendly").get_style_defs(".hl") + (
    "\n@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .hl *{color:inherit!important;background:none!important}}"
    "\n:root[data-theme=dark] .hl *{color:inherit!important;background:none!important}"
)

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500'
         '&family=IBM+Plex+Sans+Condensed:wght@500;600&family=Pinyon+Script&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap">')

KATEX = ('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">'
         '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>'
         '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js" '
         'onload="renderMathInElement(document.querySelector(\'.prose\'),{delimiters:[{left:\'$$\',right:\'$$\',display:true},{left:\'\\\\(\',right:\'\\\\)\',display:false}]})"></script>')


def giscus_block():
    """Comments under each post (GitHub Discussions via giscus) — on once site.yml has the giscus ids."""
    if not (SITE.get("giscus_repo_id") and SITE.get("giscus_category_id")):
        return ""
    return ('<section class="comments" id="comments"><h2 class="eyebrow">Comments</h2>'
            '<script src="https://giscus.app/client.js" data-repo="cpasean/BLOG" '
            f'data-repo-id="{esc(SITE["giscus_repo_id"])}" data-category="{esc(SITE.get("giscus_category", "Comments"))}" '
            f'data-category-id="{esc(SITE["giscus_category_id"])}" data-mapping="pathname" data-strict="1" '
            'data-reactions-enabled="1" data-emit-metadata="0" data-input-position="top" data-theme="preferred_color_scheme" '
            'data-lang="en" data-loading="lazy" crossorigin="anonymous" async></script></section>')


def music_widget():
    """Background music like the Wix player. Behaviour lives in static/site.js (Spotify iFrame API)."""
    track = SITE.get("music_spotify_track")
    if not track:
        return ""
    label = esc(SITE.get("music_label", "Music"))
    return (f'<div class="music" id="music" data-uri="spotify:track:{esc(track)}"><div class="frame" hidden></div>'
            f'<button type="button" id="music-btn" aria-expanded="false" aria-label="Play music" title="{label}">'
            '<span class="eq" aria-hidden="true"><i></i><i></i><i></i></span><span class="lbl">Music</span></button></div>')


def page(*, root, title, body, current="", desc=None, canonical="", image="", math=False, fragment=False):
    desc = desc or SITE["description"]
    full_title = title if title == SITE["title"] else f"{title} · {SITE['title']}"
    nav = "".join(
        f'<a href="{href(root, p)}"{" aria-current=\"page\"" if current == k else ""}>{k}</a>'
        for k, p in (("Home", ""), ("Journal", "journal/"), ("About", "about/"))
    ) + (f'<a class="write" href="{esc(SITE["editor_url"])}" target="_blank" rel="noopener">✎ Write</a>' if SITE.get("editor_url") else "")
    og_img = f"{SITE['url']}{image}" if image.startswith("/") else image
    head = (
        f"<title>{esc(full_title)}</title>"
        '<meta name="claude:viewport-fit-sides" content="cover">'
        f'<meta name="description" content="{esc(desc)}">'
        + (f'<meta name="follow.it-verification-code" content="{esc(SITE["follow_it_verification"])}"/>' if SITE.get("follow_it_verification") else "")
        + f''
        f'<link rel="canonical" href="{SITE["url"]}/{canonical}">'
        f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">'
        f'<meta property="og:type" content="{"article" if canonical.startswith("post/") else "website"}">'
        + (f'<meta property="og:image" content="{esc(og_img)}">' if og_img else "")
        + f'<link rel="alternate" type="application/rss+xml" title="{esc(SITE["title"])}" href="{root}feed.xml">'
        + (f'<meta name="gc" content="{esc(SITE["goatcounter"])}">' if SITE.get("goatcounter") else "")
        + FONTS + (KATEX if math else "")
        + f"<style>{CSS}{HL_CSS if '<div class=\"hl\"' in body else ''}</style>"
    )
    content = (
        f'<div class="wrap"><header class="mast"><p class="kicker">{esc(SITE.get("kicker", SITE["tagline"]))}</p>'
        f'<a class="brand" href="{href(root, "")}">{esc(SITE.get("brand", SITE["title"]))}</a>'
        f'<nav class="nav" aria-label="Main">{nav}</nav></header>'
        f"<main>{fix_paths(body, root)}</main>"
        + music_widget()
        + f'<script src="{root}site.js?v={SITE_JS_VER}" defer></script>'
        f'<footer class="foot"><span>© {datetime.now().year} {esc(SITE["author"])}, CPA</span>'
        f'<span>Contact: <span class="addr">{esc(SITE["email"])}</span></span>'
        + (f'<span><a href="{esc(SITE["editor_url"])}" target="_blank" rel="noopener">Write a post</a></span>' if SITE.get("editor_url") else "")
        + f'<span><a href="{href(root, "subscribe/")}">Subscribe</a></span></footer></div>'
    )
    if fragment:  # artifact preview root: skeleton is added by the host
        return '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">' + head + content
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            f"{head}</head><body>{content}</body></html>")


def ledger_rows(items, root, excerpts=True):
    rows = []
    for p in items:
        c = p["category"]
        rows.append(
            f'<li data-cat="{esc(c.lower())}"><a class="row" href="{href(root, "post/" + p["slug"] + "/")}">'
            f'<span class="no">{p["no"]:03d}</span><span class="dt">{fmt_date(p["date"])}</span>'
            f'<span class="cat {esc(c.lower())}">{esc(c)}</span><span class="ttl">{esc(p["title"])}</span>'
            f'<span class="mins">{p["minutes"]} min</span>'
            + (f'<span class="ex">{esc(p["excerpt"])}</span>' if excerpts and p["excerpt"] else "")
            + "</a></li>"
        )
    return '<ol class="ledger" reversed>' + "".join(rows) + "</ol>"


def write(rel, text):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- build
if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(ROOT / "static", OUT)

counts = {c: sum(p["category"] == c for p in posts) for c in SITE["categories"]}
lastdate = {c: next((fmt_date(p["date"]) for p in posts if p["category"] == c), "") for c in SITE["categories"]}


def subscribe_form(key):
    """Email sign-up (Wix-style). Posts to the follow.it form set in site.yml (subscribe_action)."""
    action = SITE.get("subscribe_action")
    if not action:
        return ""
    return (f'<form class="subform" action="{esc(action)}" method="post" target="_blank">'
            f'<label for="sub-{key}">Email address *</label>'
            f'<input id="sub-{key}" type="email" name="email" placeholder="you@example.com" required autocomplete="email">'
            '<button type="submit">Subscribe</button>'
            '<small>New posts arrive in your inbox. Unsubscribe anytime.</small></form>')


ICON_EYE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M1.5 12S5.5 5 12 5s10.5 7 10.5 7-4 7-10.5 7S1.5 12 1.5 12Z" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'
ICON_CMT = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h16v12H8l-4 4V4Z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>'
ICON_HRT = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20s-7.5-4.6-9.3-9.2C1.4 7.4 3.6 4 7 4c2 0 3.5 1.1 5 3 1.5-1.9 3-3 5-3 3.4 0 5.6 3.4 4.3 6.8C19.5 15.4 12 20 12 20Z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>'


def date_line(p):
    return f'{p["date"]:%b} {p["date"].day}, {p["date"].year} · {p["minutes"]} min read'


def stats(p, words=False):
    # views = visits counted on this site (GoatCounter); Wix history is kept in the post files only
    v = p["views"] if SITE.get("views_include_wix") else 0
    c = p["comments"]
    if words:
        return (f'<div class="stats"><span><span class="vc" data-slug="{esc(p["slug"])}" data-base="{v}">{v}</span> views</span>'
                f'<span>{c} comments</span><span class="hrt" title="{p["likes"]} likes">{ICON_HRT}<b>{(p["likes"] or "") if SITE.get("views_include_wix") else ""}</b></span></div>')
    return (f'<div class="stats"><span>{ICON_EYE}<span class="vc" data-slug="{esc(p["slug"])}" data-base="{v}">{v}</span></span>'
            f'<span>{ICON_CMT}{c}</span><span class="hrt" title="{p["likes"]} likes">{ICON_HRT}<b>{(p["likes"] or "") if SITE.get("views_include_wix") else ""}</b></span></div>')


def photo_card(p, root):
    """Wix-style tile: photo fills the square, text over a grey veil."""
    img = f'<img src="{esc(p["cover"])}" alt="" loading="lazy">' if p["cover"] else ""
    return (f'<a class="tile" href="{href(root, "post/" + p["slug"] + "/")}">{img}<div class="veil">'
            f'<div class="by">{esc(SITE["author"])}<br><span>{date_line(p)}</span></div>'
            f'<h3>{esc(p["title"])}</h3><hr>{stats(p)}</div></a>')


def list_card(p, root):
    """TRAIN OF THOUGHT card: photo left (when the post has one), text right."""
    img = (f'<div class="ph"><img src="{esc(p["cover"])}" alt="" loading="lazy"></div>' if p["cover"] else "")
    return (f'<li data-cat="{esc(p["category"].lower())}"><a class="lcard{" noimg" if not p["cover"] else ""}" href="{href(root, "post/" + p["slug"] + "/")}">{img}'
            f'<div class="tx"><p class="dl">{date_line(p)}</p><h3>{esc(p["title"])}</h3>'
            f'<p class="ex">{esc(p["excerpt"])}</p><hr>{stats(p, words=True)}</div></a></li>')


def card_list(items, root):
    return '<ol class="cardlist">' + "".join(list_card(p, root) for p in items) + "</ol>"


def featured_slider(items, root):
    slides = "".join(
        f'<article class="slide"><a href="{href(root, "post/" + p["slug"] + "/")}">'
        + (f'<div class="ph"><img src="{esc(p["cover"])}" alt="" loading="lazy"></div>' if p["cover"] else '<div class="ph"></div>')
        + f'<div class="tx"><p class="dl">{date_line(p)}</p><h3>{esc(p["title"])}</h3><p class="ex">{esc(p["excerpt"])}</p><hr>{stats(p)}</div></a></article>'
        for p in items)
    return ('<div class="slider" data-slider><div class="track">' + slides + '</div>'
            '<button type="button" class="arw prev" aria-label="Previous featured post">&#8249;</button>'
            '<button type="button" class="arw next" aria-label="Next featured post">&#8250;</button></div>')

# home — section order restored from the Wix home page
motto = "".join(f"<span>{esc(m)}</span>" for m in SITE["motto"])
pick = next((p for p in posts if p["slug"] == SITE.get("my_pick")), None)
pick_text = SITE.get("my_pick_text", "").strip()
if pick and not pick_text:
    pick_text = re.sub(r"<[^>]+>", "\n", pick["html"])
    pick_text = re.sub(r"\n\s*\n+", "\n", html.unescape(pick_text)).strip()
intro = "".join(f"<p>{esc(x.strip())}</p>" for x in SITE.get("intro", "").split("\n\n") if x.strip())
featured = [p for p in posts if p["featured"] and p["cover"]] or [p for p in posts if p["cover"]][:8]
home = (
    '<section class="split bleed" aria-label="Welcome">'
    '<div class="photo" style="background-image:url(/images/bg-wheat.jpg)" role="img" aria-label="Wheat field at sunset"></div>'
    '<div class="panel"><h2>Life &amp; Thoughts</h2><nav aria-label="Sections">'
    f'<a href="{href("", "journal/")}#life">Life &amp; Thoughts</a>'
    f'<a href="{href("", "about/")}">About</a>'
    f'<a href="{href("", "journal/")}#work">Financial Freedom</a></nav></div></section>'
    '<section class="tiles" aria-label="Latest posts">' + "".join(photo_card(p, "") for p in posts[:6]) + '</section>'
    '<section class="feat"><div class="fl">' + featured_slider(featured, "") + '</div>'
    '<div class="fr"><div class="clips">'
    '<video src="/images/sea-sunset.mp4" poster="/images/sea-sunset.jpg" autoplay muted loop playsinline preload="metadata" aria-label="Sunset over the sea"></video>'
    '<video src="/images/coffee.mp4" poster="/images/coffee.jpg" autoplay muted loop playsinline preload="metadata" aria-label="Espresso pouring into a cup"></video></div>'
    f'<div class="sea">{intro}</div></div></section>'
    '<section class="blush bleed"><div class="in"><p class="sig">From the bottom of my heart,</p>'
    + (subscribe_form("band") or f'<div class="follow"><a class="btn solid" href="{href("", "subscribe/")}">Subscribe</a></div>')
    + '</div></section>'
    '<div class="band thin fixed bleed" style="background-image:url(/images/bg-handwriting.jpg)" role="img" aria-label="Handwritten I CHOOSE"></div>'
    '<section class="tot"><div>'
    f'<div class="sect" style="margin-top:0"><h2 class="eyebrow tot-h">Train of thought</h2><a href="{href("", "journal/")}">All {len(posts)} entries →</a></div>'
    + card_list(posts[:8], "")
    + '</div><aside>'
    '<div class="side"><h2 class="eyebrow">About me</h2>'
    f'<a href="{esc(SITE["instagram_personal"])}" target="_blank" rel="noopener"><img src="/images/about-collage.jpg" alt="Photos of Sean Yeon" width="246" height="246" loading="lazy"></a>'
    f'<p>{esc(SITE["tagline"])}</p><div class="mot">{"<br>".join(f"{i}. {esc(m)}" for i, m in enumerate(SITE["motto"], 1))}</div>'
    f'<p class="more"><a href="{href("", "about/")}">Read more →</a></p></div>'
    '<div class="side"><h2 class="eyebrow">Click me</h2>'
    f'<a href="{esc(SITE["instagram_blog"])}" target="_blank" rel="noopener"><img src="/images/247b38f1425a4a52b28bc87c58d06333.jpg" alt="Hiking in the Swiss Alps" loading="lazy"></a></div>'
    + (f'<div class="side"><h2 class="eyebrow">Subscribe</h2>{subscribe_form("side")}</div>' if SITE.get("subscribe_action") else "")
    + '<div class="side"><h2 class="eyebrow">My pick<br>of the month</h2>'
    '<video src="/images/my-pick.mp4" poster="/images/my-pick-poster.jpg" autoplay muted loop playsinline preload="metadata" aria-label="Writing in a notebook"></video>'
    + (f'<div class="pick"><a href="{href("", "post/" + pick["slug"] + "/")}">{esc(pick["title"])}</a>\n{esc(pick_text)}</div>' if pick and pick_text else
       (f'<div class="pick"><a href="{href("", "post/" + pick["slug"] + "/")}">{esc(pick["title"])}</a></div>' if pick else ""))
    + '</div></aside></section>'
    '<div class="band fixed bleed" style="background-image:url(/images/bg-agenda.jpg);margin-top:3rem" role="img" aria-label="Leather agenda notebook"></div>'
    '<section class="contact bleed" id="contact"><h2>Contact Sean</h2>'
    f'<p>{esc(SITE.get("address", ""))}</p><p><span class="addr">{esc(SITE["email"])}</span></p>'
    '<form id="cf"><input id="cf-name" name="name" placeholder="Name" autocomplete="name">'
    '<input id="cf-subject" name="subject" placeholder="Subject" required>'
    '<textarea id="cf-msg" name="message" placeholder="Type your message here..." required></textarea>'
    '<button class="btn" type="submit">Send by email</button></form>'
    f'<script>document.getElementById("cf").addEventListener("submit",function(e){{e.preventDefault();var f=e.target;'
    f'location.href="mailto:{SITE["email"]}?subject="+encodeURIComponent(f.subject.value)+"&body="+encodeURIComponent(f.message.value+"\\n\\n"+f.name.value)}})</script>'
    '</section>'
)
write("index.html", page(root="", title=SITE["title"], body=home, current="Home"))
if PREVIEW:
    write("_root.html", page(root="", title=SITE["title"], body=home, current="Home", fragment=True))

# journal
journal = (
    f'<section class="page-h"><h1>Journal</h1><p>{len(posts)} entries since {fmt_date(posts[-1]["date"])[:4]}, newest first.</p></section>'
    '<div class="filters" role="group" aria-label="Filter by category">'
    '<button type="button" id="f-all" data-f="all" aria-pressed="true">All</button>'
    + "".join(f'<button type="button" id="f-{c.lower()}" data-f="{c.lower()}" aria-pressed="false">{c} · {counts[c]}</button>' for c in SITE["categories"])
    + "</div>" + card_list(posts, "../")
    + """<script>(function(){var b=[].slice.call(document.querySelectorAll('.filters button')),r=[].slice.call(document.querySelectorAll('.cardlist li'));
function set(f){b.forEach(function(x){x.setAttribute('aria-pressed',String(x.dataset.f===f))});r.forEach(function(li){li.hidden=f!=='all'&&li.dataset.cat!==f})}
b.forEach(function(x){x.addEventListener('click',function(){set(x.dataset.f);history.replaceState(null,'',x.dataset.f==='all'?location.pathname:'#'+x.dataset.f)})});
function fromHash(){var h=location.hash.slice(1);set(b.some(function(x){return x.dataset.f===h})?h:'all')}window.addEventListener('hashchange',fromHash);fromHash()})();</script>"""
)
write("journal/index.html", page(root="../", title="Journal", body=journal, current="Journal", canonical="journal/"))

# posts
for i, p in enumerate(posts):
    root = "../../"
    newer = posts[i - 1] if i > 0 else None
    older = posts[i + 1] if i + 1 < len(posts) else None
    pager = '<nav class="pager" aria-label="More entries">'
    if older:
        pager += f'<a href="{href(root, "post/" + older["slug"] + "/")}"><span class="lbl">← Earlier</span><span class="t">{esc(older["title"])}</span></a>'
    if newer:
        pager += f'<a class="next" href="{href(root, "post/" + newer["slug"] + "/")}"><span class="lbl">Later →</span><span class="t">{esc(newer["title"])}</span></a>'
    pager += "</nav>"
    prose = re.sub(r"<table>", '<div class="tbl"><table>', p["html"]).replace("</table>", "</table></div>")
    prose = prose.replace("<img ", '<img loading="lazy" ')
    body = (
        f'<article class="post"><div class="meta"><span>No. {p["no"]:03d}</span><time datetime="{fmt_date(p["date"])}">{p["date"]:%B} {p["date"].day}, {p["date"].year}</time>'
        f'<span class="cat {esc(p["category"].lower())}">{esc(p["category"])}</span><span>{p["minutes"]} min read</span></div>'
        f'<h1>{esc(p["title"])}</h1><div class="prose">{prose}</div>'
        f'<div class="poststats">{stats(p, words=True)}</div>'
        + giscus_block()
        + f''
        f'<p class="legacy">Originally published on Wix, {p["date"].strftime("%B %Y")}.</p>{pager}</article>'
    )
    write(f"post/{p['slug']}/index.html", page(
        root=root, title=p["title"], body=body, current="Journal", desc=p["excerpt"] or p["title"],
        canonical=f"post/{p['slug']}/", image=p["cover"], math=p["math"]))

# about
photo = about_meta.get("photo", "")
about = (
    (f'<figure class="about-banner"><img src="{esc(photo)}" alt="Sean Yeon with colleagues"></figure>' if photo else "")
    + f'<section class="about"><div><h1>About</h1><div class="prose">{render_md(about_body)}</div></div></section>'
    '<div class="band fixed bleed" style="background-image:url(/images/bg-about.jpg);margin-top:3rem" role="img" aria-label="Travel photo"></div>'
)
write("about/index.html", page(root="../", title="About", body=about, current="About", canonical="about/", image=photo))

# 404
BASE = "/" + SITE["url"].split("://", 1)[1].partition("/")[2].strip("/")  # e.g. "/BLOG" on a project site
BASE = BASE.rstrip("/") + "/"
write("404.html", page(root=BASE, title="Page not found", body='<section class="page-h"><h1>No such entry</h1>'
                       '<p>This page is not in the ledger. Try the <a href="/journal/">Journal</a>.</p></section>'))


# subscribe page — friendly landing instead of raw XML
feed_url = f"{SITE['url']}/feed.xml"
from urllib.parse import quote
subscribe = (
    '<section class="post"><h1>Subscribe</h1><div class="prose">'
    '<p>Enter your email address and every new post will be sent to your inbox.</p>'
    + subscribe_form("page") +
    '<details class="other"><summary>Other ways to follow</summary>'
    '<p>Use a news reader app instead of email:</p>'
    f'<p class="follow"><a class="btn" href="https://feedly.com/i/subscription/feed/{quote(feed_url, safe="")}" target="_blank" rel="noopener">Feedly</a>'
    f'<a class="btn" href="https://www.inoreader.com/?add_feed={quote(feed_url, safe="")}" target="_blank" rel="noopener">Inoreader</a>'
    f'<a class="btn" href="{esc(SITE["instagram_blog"])}" target="_blank" rel="noopener">Instagram</a></p>'
    f'<p>Feed address: <code style="user-select:all">{esc(feed_url)}</code></p></details>'
    '</div></section>'
)
thanks = (
    '<section class="post"><h1>Thank you for subscribing</h1><div class="prose">'
    '<p>Your subscription is confirmed. New posts will arrive in your inbox.</p>'
    f'<p class="follow"><a class="btn solid" href="{href("../", "")}">Back to the blog</a>'
    f'<a class="btn" href="{href("../", "journal/")}">Browse all entries</a></p>'
    '</div></section>'
)
write("thanks/index.html", page(root="../", title="Thank you", body=thanks, canonical="thanks/"))
write("subscribe/index.html", page(root="../", title="Subscribe", body=subscribe, canonical="subscribe/"))
write("feed.xsl", f'''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" encoding="UTF-8"/>
<xsl:template match="/rss/channel">
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title><xsl:value-of select="title"/> · RSS feed</title>
<style>body{{margin:0;padding:2rem max(16px,env(safe-area-inset-left,0px));font:17px/1.6 Georgia,serif;background:#F5F7F3;color:#18211D}}
main{{max-width:40rem;margin:0 auto}}.note{{background:#FFEC9B;padding:1rem 1.2rem;margin-bottom:2rem}}
a{{color:#1E6A4E}}h1{{font-family:Arial Narrow,Arial,sans-serif}}li{{margin:.6rem 0}}small{{color:#5B6862}}
@media (prefers-color-scheme:dark){{body{{background:#0F1513;color:#E2E9E4}}.note{{background:#3A3320}}a{{color:#6CC39C}}small{{color:#93A39A}}}}</style></head>
<body><main><div class="note"><strong>This is an RSS feed.</strong> Copy this page's address into a reader app to follow the blog,
or see <a href="subscribe/">easy ways to subscribe</a>.</div>
<h1><xsl:value-of select="title"/></h1><p><xsl:value-of select="description"/></p>
<ul><xsl:for-each select="item"><li><a href="{{link}}"><xsl:value-of select="title"/></a><br/><small><xsl:value-of select="substring(pubDate,6,11)"/></small></li></xsl:for-each></ul>
<p><a href="./">← Back to the blog</a></p></main></body></html>
</xsl:template></xsl:stylesheet>''')

# feed + sitemap
items = "".join(
    f"<item><title>{esc(p['title'])}</title><link>{SITE['url']}/post/{p['slug']}/</link>"
    f"<guid>{SITE['url']}/post/{p['slug']}/</guid><pubDate>{format_datetime(p['date'])}</pubDate>"
    f"<category>{esc(p['category'])}</category><description>{esc(p['excerpt'])}</description></item>"
    for p in posts[:30]
)
write("feed.xml", f'<?xml version="1.0" encoding="UTF-8"?><?xml-stylesheet type="text/xsl" href="feed.xsl"?><rss version="2.0"><channel><title>{esc(SITE["title"])}</title>'
      f'<link>{SITE["url"]}/</link><description>{esc(SITE["description"])}</description>{items}</channel></rss>')
urls = ["", "journal/", "about/", "subscribe/"] + [f"post/{p['slug']}/" for p in posts]
write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
      + "".join(f"<url><loc>{SITE['url']}/{u}</loc></url>" for u in urls) + "</urlset>")
write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE['url']}/sitemap.xml\n")
write(".nojekyll", "")

print(f"Built {len(posts)} posts → {OUT.relative_to(ROOT)}/")
