# kenny vo.

My site, at <https://kenny-t-vo.github.io/>: photography, work samples, cv and
writing. Plain HTML, CSS and JS on GitHub Pages. Two scripts build the generated
parts: `build.sh` renders the PDFs to images and `writings.py` turns markdown into
pages. The commands I actually run are in [UPDATING.md](UPDATING.md).

## Layout

```
index.html            home: the four sections and links elsewhere
assets/type.css       shared: faces, sizes, colours, the hover band
assets/style.css      the PDF viewer; tunable values at the top
assets/app.js         the PDF viewer: pairing, fit-to-window, zoom lens, index
assets/writing.css    the writing pages
assets/fonts/         Redaction 35 and its licence
assets/social.png     share card
photography/          book shell; book.js and pages/ are generated
work/                 same, for the work samples
cv/
  index.html          builds itself from pages.js
  pages.js            generated: page count, aspect, links
  pages/              generated: one lossless tier
  Vo_Kenny_CV.pdf     generated: copy for the download link
writings/
  src/                markdown, one file per piece; images in src/images/
  index.html          generated: the list
  <slug>/index.html   generated: one piece
  images/             generated: copy of src/images/
build.sh              PDF → page images
writings.py           markdown → writing pages
linkmap.py            PDF link annotations → rects as fractions of a leaf
```

## PDFs

The PDFs themselves are not served, apart from the cv's download copy.
`build.sh <pdf> <dir>` renders every page to WebP. `photography` and `work` get
three tiers:

| tier | width | use | photography | work |
|---|---|---|---|---|
| `pages/view/` | 1400 px | the spread | 5.3 MB | 3.0 MB |
| `pages/full/` | 2600 px | zoom | 18 MB | 8.1 MB |
| `pages/thumb/` | 320 px | index grid, blur-up placeholder | 272 KB | 196 KB |

A spread loads about 350 KB, and the neighbouring spreads prefetch. The page shape
sets the pairing:

- Portrait pages (photography, 32 leaves): 1 alone as the cover, then 2–3, 4–5 …
  30–31, then 32 alone.
- Landscape 2-ups (work, 16 leaves): each page is cut down the middle and paired
  back 1–2, 3–4 …, so narrow screens can show one leaf at a time.

`book.js` records the leaf count, aspect and pairing. `cv` instead gets one
lossless 2000 px tier, which is sharper and smaller than lossy for type, plus
`pages.js` and a copy of the PDF. `build.sh` writes only inside the directory it
is given.

Needs `brew install poppler webp` and `pip3 install pillow pypdf`.

### Links

Rasterising drops a PDF's link annotations, so `linkmap.py` reads them with pypdf
and the viewers lay transparent anchors back over the image. Rects are clipped per
leaf; a link across the gutter becomes two. InDesign places link rects on the text
frame, so the build re-centres each one on the ink underneath it and renders an
inverted blue copy of that patch to show on hover. There are 14 links across the
three documents and the patches total 56 KB. Links work in the reading view, not in
the zoom lens. Without pypdf the build still runs and prints a warning.

### Reading

| | |
|---|---|
| `←` `→` `space` | turn |
| click, or `Z` | zoom at full resolution; drag to pan, scroll to zoom |
| `G` | index |
| `F` | fullscreen |
| `Home` / `End` | first / last |
| swipe | turn, on touch |

Narrow or portrait windows show one leaf at a time. `#p12` in the URL opens at
leaf 12.

### Tuning

The top of `assets/style.css` holds the viewer's variables: gutter crease strength
and width, ground colour, page hairline, frame margin, and `--idle-after`, which
`app.js` reads. The crease is set per book:

```css
body[data-book="photography"]{ --gutter-strength:.25; }
body[data-book="cv"]         { --gutter-strength:.25; }
body[data-book="work"]       { --gutter-strength:0; }
```

Work is off because its spreads were drawn flat.

## Writing

`writings.py` builds every `.md` in `writings/src/` into `writings/<filename>/` and
rebuilds the index, newest first. A `.docx` is converted first if pandoc is
installed. `_name.md` is a draft and is skipped. Deleting a source removes its page
on the next run.

Front matter, all optional:

```
---
title: on drawing.
date: 2026-09-09
standfirst: one line under the title.
---
```

Without it the first heading is the title and the file's modification date is the
date. Images go in `writings/src/images/`, in a subfolder per piece if there are
many, and are written `![alt](images/name.jpg "caption")`. An image alone in a
paragraph becomes a figure with that caption. Footnotes, links, quotes, lists,
tables and code all render. Needs `pip3 install markdown`.

## Type

Redaction 35 for titles and the wordmark, Plantin MT Pro for everything else,
including folios and labels. Redaction is SIL OFL and self-hosted in
`assets/fonts/`. Plantin is an Adobe font and can't be redistributed, so the stack
names it first and it shows only where it is installed, as on my machine through
Adobe Fonts. Everyone else gets Times New Roman, which was drawn from Plantin.

`assets/type.css` has six sizes, `--t1` to `--t6`: 22 / 16 / 14 / 12.5 / 11 /
10.5 px. Spacing is `--s1` to `--s5`: 6 / 12 / 22 / 40 / 72 px. The hover band is
an absolutely positioned pseudo-element, so hovering never reflows a line.

## Caching

Every page links its CSS and JS with `?v=N`. GitHub Pages caches HTML and assets
separately for ten minutes, so after editing anything in `assets/` N has to go up
on every page, or a returning visitor gets new HTML against old CSS. The bump
command is in UPDATING.md.

## Deploying

This is the user-site repo, so Pages serves `main` at the root of
`kenny-t-vo.github.io`. `.nojekyll` stops Jekyll from processing the asset folders.
For a custom domain, add a `CNAME` file with the domain and point a DNS `CNAME`
record at `kenny-t-vo.github.io`.
