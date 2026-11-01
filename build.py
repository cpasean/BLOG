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
    })

posts.sort(key=lambda p: p["date"], reverse=True)
for i, p in enumerate(posts):
    p["no"] = len(posts) - i  # ledger entry number, oldest = 1

about_meta, about_body = load(ROOT / "content/about.md")

# ---------------------------------------------------------------- links


def href(root, path):
    """path like '' , 'journal/', 'post/x/' -> relative link from a page at depth root."""
    if PREVIEW and (path == "" or path.endswith("/")):
        path = path + "index.html"
    return root + path if path else (root or "./")


def fix_paths(text, root):
    return re.sub(r'(src|href)="/(?!/)', lambda m: f'{m.group(1)}="{root}', text)


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
  --display:"IBM Plex Sans Condensed","Arial Narrow",Arial,sans-serif;
  --body:"Source Serif 4",Georgia,"Times New Roman",serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;
  --measure:40rem;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#0F1513; --sheet:#141B18; --ink:#E2E9E4; --muted:#93A39A; --rule:#24302B; --rule-strong:#33443C;
  --green:#6CC39C; --green-soft:#1A2A23; --red:#E58273; color-scheme:dark}}
:root[data-theme="dark"]{
  --paper:#0F1513; --sheet:#141B18; --ink:#E2E9E4; --muted:#93A39A; --rule:#24302B; --rule-strong:#33443C;
  --green:#6CC39C; --green-soft:#1A2A23; --red:#E58273; color-scheme:dark}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.7 var(--body);
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
a{color:var(--green);text-underline-offset:3px;text-decoration-thickness:1px}
a:hover{text-decoration-thickness:2px}
a:focus-visible,button:focus-visible{outline:2px solid var(--green);outline-offset:3px;border-radius:2px}
img{max-width:100%;height:auto}
.wrap{max-width:62rem;margin:0 auto}

/* masthead */
.mast{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:.5rem 1.5rem;
  padding-block:1.4rem 1rem;border-bottom:3px double var(--rule-strong)}
.brand{font:600 1.5rem/1 var(--display);letter-spacing:.01em;color:var(--ink);text-decoration:none}
.brand small{display:block;margin-top:.35rem;font:500 .72rem/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.nav{display:flex;gap:1.25rem;font:500 .95rem/1 var(--display);letter-spacing:.03em}
.nav a{color:var(--muted);text-decoration:none;padding-block:.3rem}
.nav a[aria-current="page"],.nav a:hover{color:var(--ink);box-shadow:inset 0 -2px 0 var(--green)}

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
.about{display:grid;grid-template-columns:minmax(0,14rem) minmax(0,var(--measure));gap:2.5rem;padding-block:2.6rem 1rem;justify-content:center}
.about figure{margin:0}
.about figure img{border:1px solid var(--rule);filter:grayscale(.15)}
.about figcaption{font:500 .72rem/1.5 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:.6rem}
.about h1{font:600 2.6rem/1.05 var(--display);margin:0 0 1rem}

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
         '&family=IBM+Plex+Sans+Condensed:wght@500;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap">')

KATEX = ('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">'
         '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>'
         '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js" '
         'onload="renderMathInElement(document.querySelector(\'.prose\'),{delimiters:[{left:\'$$\',right:\'$$\',display:true},{left:\'\\\\(\',right:\'\\\\)\',display:false}]})"></script>')


def page(*, root, title, body, current="", desc=None, canonical="", image="", math=False, fragment=False):
    desc = desc or SITE["description"]
    full_title = title if title == SITE["title"] else f"{title} · {SITE['title']}"
    nav = "".join(
        f'<a href="{href(root, p)}"{" aria-current=\"page\"" if current == k else ""}>{k}</a>'
        for k, p in (("Home", ""), ("Journal", "journal/"), ("About", "about/"))
    )
    og_img = f"{SITE['url']}{image}" if image.startswith("/") else image
    head = (
        f"<title>{esc(full_title)}</title>"
        '<meta name="claude:viewport-fit-sides" content="cover">'
        f'<meta name="description" content="{esc(desc)}">'
        f'<link rel="canonical" href="{SITE["url"]}/{canonical}">'
        f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">'
        f'<meta property="og:type" content="{"article" if canonical.startswith("post/") else "website"}">'
        + (f'<meta property="og:image" content="{esc(og_img)}">' if og_img else "")
        + f'<link rel="alternate" type="application/rss+xml" title="{esc(SITE["title"])}" href="{root}feed.xml">'
        + FONTS + (KATEX if math else "")
        + f"<style>{CSS}{HL_CSS if '<div class=\"hl\"' in body else ''}</style>"
    )
    content = (
        f'<div class="wrap"><header class="mast"><a class="brand" href="{href(root, "")}">{esc(SITE["title"])}'
        f'<small>{esc(SITE["tagline"])} · {esc(SITE["location"])}</small></a><nav class="nav" aria-label="Main">{nav}</nav></header>'
        f"<main>{fix_paths(body, root)}</main>"
        f'<footer class="foot"><span>© {datetime.now().year} {esc(SITE["author"])}, CPA</span>'
        f'<span>Contact: <span class="addr">{esc(SITE["email"])}</span></span>'
        f'<span><a href="{root}feed.xml">RSS</a></span></footer></div>'
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

# home
motto = "".join(f"<span>{esc(m)}</span>" for m in SITE["motto"])
accounts = "".join(
    f'<a href="{href("", "journal/")}#{c.lower()}"><span class="acct-code">Account · {esc(c)}</span>'
    f'<strong>{esc(c)}</strong><span class="d">{esc(d)}</span>'
    f'<span class="bal">{counts[c]} entries · last {lastdate[c]}</span></a>'
    for c, d in SITE["categories"].items()
)
home = (
    '<section class="hero"><div><h1>Accounting for numbers, <em>and for a life well kept.</em></h1>'
    f'<p>{esc(SITE["description"])}</p></div>'
    f'<blockquote class="motto">{motto}<cite>Sean, 1.1.2021</cite></blockquote></section>'
    f'<nav class="accounts" aria-label="Categories">{accounts}</nav>'
    f'<div class="sect"><h2>Latest entries</h2><a href="{href("", "journal/")}">All {len(posts)} entries →</a></div>'
    + ledger_rows(posts[:8], "")
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
    + "</div>" + ledger_rows(posts, "../")
    + """<script>(function(){var b=[].slice.call(document.querySelectorAll('.filters button')),r=[].slice.call(document.querySelectorAll('.ledger li'));
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
        f'<p class="legacy">Originally published on Wix, {p["date"].strftime("%B %Y")}.</p>{pager}</article>'
    )
    write(f"post/{p['slug']}/index.html", page(
        root=root, title=p["title"], body=body, current="Journal", desc=p["excerpt"] or p["title"],
        canonical=f"post/{p['slug']}/", image=p["cover"], math=p["math"]))

# about
photo = about_meta.get("photo", "")
about = (
    '<section class="about">'
    + (f'<figure><img src="{esc(photo)}" alt="Portrait of Sean Yeon"><figcaption>Sean Yeon · CPA, New Jersey</figcaption></figure>' if photo else "")
    + f'<div><h1>About</h1><div class="prose">{render_md(about_body)}</div></div></section>'
)
write("about/index.html", page(root="../", title="About", body=about, current="About", canonical="about/", image=photo))

# 404
BASE = "/" + SITE["url"].split("://", 1)[1].partition("/")[2].strip("/")  # e.g. "/BLOG" on a project site
BASE = BASE.rstrip("/") + "/"
write("404.html", page(root=BASE, title="Page not found", body='<section class="page-h"><h1>No such entry</h1>'
                       '<p>This page is not in the ledger. Try the <a href="/journal/">Journal</a>.</p></section>'))

# feed + sitemap
items = "".join(
    f"<item><title>{esc(p['title'])}</title><link>{SITE['url']}/post/{p['slug']}/</link>"
    f"<guid>{SITE['url']}/post/{p['slug']}/</guid><pubDate>{format_datetime(p['date'])}</pubDate>"
    f"<category>{esc(p['category'])}</category><description>{esc(p['excerpt'])}</description></item>"
    for p in posts[:30]
)
write("feed.xml", f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{esc(SITE["title"])}</title>'
      f'<link>{SITE["url"]}/</link><description>{esc(SITE["description"])}</description>{items}</channel></rss>')
urls = ["", "journal/", "about/"] + [f"post/{p['slug']}/" for p in posts]
write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
      + "".join(f"<url><loc>{SITE['url']}/{u}</loc></url>" for u in urls) + "</urlset>")
write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE['url']}/sitemap.xml\n")
write(".nojekyll", "")

print(f"Built {len(posts)} posts → {OUT.relative_to(ROOT)}/")
