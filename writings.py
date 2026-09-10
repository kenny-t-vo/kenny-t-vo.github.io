#!/usr/bin/env python3
"""Turn writings/src/*.md into the pages under writings/.

    ./writings.py

Drop a markdown file in writings/src/ and run it. Pictures go in
writings/src/images/ and are referenced as images/name.jpg. A .docx is
converted first if pandoc is installed.

Front matter is optional:

    ---
    title: On something
    date: 2026-09-09
    standfirst: one line under the title
    ---

Without it the first heading becomes the title and the file's date is used.

Requires: pip3 install markdown
"""
import html
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "writings" / "src"
OUT = ROOT / "writings"

MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]


def asset_version():
    """The ?v= the rest of the site is on, so these pages never fall behind."""
    m = re.search(r"\?v=(\d+)", (ROOT / "index.html").read_text())
    return m.group(1) if m else "1"


V = asset_version()

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — kenny vo.</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#ffffff">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:image" content="https://kenny-t-vo.github.io/assets/social.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' fill='%23fff'/><rect x='6' y='7' width='9' height='18' fill='%230000ee'/><rect x='17' y='7' width='9' height='18' fill='%230000ee'/></svg>">
<link rel="preload" as="font" type="font/woff2" href="{up}assets/fonts/redaction-35-400.woff2" crossorigin>
<link rel="stylesheet" href="{up}assets/type.css?v={v}">
<link rel="stylesheet" href="{up}assets/writing.css?v={v}">
</head>
<body>
<div class="column">

  <nav class="masthead">
    <a class="invert" href="{home}">kenny vo.</a>
    {section}
  </nav>

{body}

</div>
</body>
</html>
"""


def read_front_matter(text):
    """Split the leading --- block off, as plain key: value lines."""
    meta = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].strip().splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip().lower()] = v.strip()
            text = text[end + 4:]
    return meta, text.lstrip("\n")


def figures(markup):
    """A paragraph holding nothing but an image becomes a figure; the image's
    title becomes its caption. The title is pulled out separately rather than
    in the same pattern — a lazy prefix will happily match it as ordinary
    attribute text and leave the capture group empty."""
    def swap(m):
        img = m.group(1)
        cap = re.search(r'title="([^"]*)"', img)
        caption = f"\n<figcaption>{cap.group(1)}</figcaption>" if cap else ""
        return f"<figure>{img}{caption}</figure>"
    return re.sub(r'<p>(<img[^>]*/?>)</p>', swap, markup)


def to_markdown(path):
    """Markdown as written, or converted out of a .docx by pandoc."""
    if path.suffix.lower() != ".docx":
        return path.read_text(encoding="utf-8")
    if not shutil.which("pandoc"):
        print(f"  ! {path.name} needs pandoc:  brew install pandoc")
        return None
    return subprocess.run(
        ["pandoc", "--wrap=none", "-t", "markdown_strict+footnotes", str(path)],
        capture_output=True, text=True, check=True).stdout


def display_date(iso):
    try:
        d = datetime.strptime(iso, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return iso or ""
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def build_piece(path, md):
    import markdown

    meta, body = read_front_matter(md)
    conv = markdown.Markdown(extensions=["footnotes", "tables", "attr_list",
                                         "smarty", "sane_lists"])
    markup = figures(conv.convert(body))
    # images/ sits beside the pieces, and a piece is a directory deeper
    markup = markup.replace('src="images/', 'src="../images/')
    markup = markup.replace('href="images/', 'href="../images/')

    title = meta.get("title")
    if not title:
        m = re.search(r"<h1[^>]*>(.*?)</h1>", markup, re.S)
        title = re.sub(r"<[^>]+>", "", m.group(1)) if m else path.stem
        markup = re.sub(r"<h1[^>]*>.*?</h1>", "", markup, count=1, flags=re.S)

    iso = meta.get("date") or date.fromtimestamp(path.stat().st_mtime).isoformat()
    stand = meta.get("standfirst", "")

    head = [f"  <h1>{html.escape(title)}</h1>"]
    if iso:
        head.append(f'  <p class="dateline">{display_date(iso)}.</p>')
    if stand:
        head.append(f'  <p class="standfirst">{html.escape(stand)}</p>')

    page = PAGE.format(
        title=html.escape(title),
        desc=html.escape(stand or title),
        up="../../", v=V, home="../../",
        section='<a class="invert" href="../">writings.</a>',
        body="\n".join(head) + f"\n\n  <article>\n{markup}\n  </article>",
    )
    return {"slug": path.stem, "title": title, "iso": iso,
            "stand": stand, "html": page}


def build_index(pieces):
    if pieces:
        rows = []
        for p in pieces:
            about = (f'\n      <p class="about">{html.escape(p["stand"])}</p>'
                     if p["stand"] else "")
            rows.append(
                f'    <li>\n'
                f'      <div class="row">'
                f'<a class="name invert" href="{p["slug"]}/">{html.escape(p["title"])}</a>'
                f'<span class="when">{display_date(p["iso"])}.</span></div>'
                f'{about}\n    </li>')
        body = ('  <h1>writings.</h1>\n\n  <ul class="pieces">\n'
                + "\n".join(rows) + "\n  </ul>")
    else:
        body = '  <h1>writings.</h1>\n\n  <p class="empty">nothing here yet.</p>'

    return PAGE.format(
        title="writings", desc="essays and notes.",
        up="../", v=V, home="../",
        section="",          # the h1 already says it

        body=body,
    )


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    sources = sorted(p for p in SRC.iterdir()
                     if p.suffix.lower() in (".md", ".markdown", ".docx")
                     and not p.name.startswith("_"))   # _name.md is a draft

    pieces = []
    for path in sources:
        md = to_markdown(path)
        if md is None:
            continue
        piece = build_piece(path, md)
        target = OUT / piece["slug"]
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(piece["html"], encoding="utf-8")
        pieces.append(piece)
        print(f"  {piece['slug']}/  {piece['title']}")

    pieces.sort(key=lambda p: p["iso"], reverse=True)
    (OUT / "index.html").write_text(build_index(pieces), encoding="utf-8")

    # pictures travel with the source
    src_img = SRC / "images"
    if src_img.is_dir():
        dest = OUT / "images"
        shutil.rmtree(dest, ignore_errors=True)
        shutil.copytree(src_img, dest)
        print(f"  images/  {len(list(dest.iterdir()))} file(s)")

    # a piece whose source is gone should stop being published
    live = {p["slug"] for p in pieces}
    for d in OUT.iterdir():
        if d.is_dir() and d.name not in ("src", "images") and d.name not in live:
            shutil.rmtree(d)
            print(f"  removed {d.name}/ (no source)")

    print(f"→ {len(pieces)} piece(s)")


if __name__ == "__main__":
    main()
