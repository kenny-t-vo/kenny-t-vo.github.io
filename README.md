# Some books.

Two self-hosted portfolios as fit-to-window spread viewers, sharing one copy of the
viewer between them.

| | |
|---|---|
| **photography.** | https://kenny-t-vo.github.io/photography/ |
| **work samples.** | https://kenny-t-vo.github.io/work/ |

## How it works

The PDFs are not sent to the browser. `build.sh` renders every page and derives
three WebP tiers per leaf:

| tier | width | used for | photography | work |
|---|---|---|---|---|
| `pages/view/` | 1400 px | the spread you read | 5.4 MB | 2.9 MB |
| `pages/full/` | 2600 px | click-to-zoom detail | 23 MB | 10 MB |
| `pages/thumb/` | 320 px | index grid + blur-up placeholders | 276 KB | 196 KB |

A reader downloads roughly 300 KB per spread instead of the whole PDF. The next and
previous spreads prefetch, so turning a page is instant.

## Two export shapes

The books come out of InDesign differently, and `build.sh` detects which is which
from the page aspect ratio:

- **Portrait pages** (photography, 32 × letter). Paired the way the book was set:
  page 1 alone as the cover, then 2–3, 4–5 … 30–31, then 32 alone.
- **Landscape 2-ups** (work samples, 8 × 17″ tall-11″). Already spreads, so each
  page is cut down the middle into two leaves and paired straight back: 1–2, 3–4 …
  The cut is lossless, and it is what gives narrow screens one page at a time.

Either way the viewer receives single leaves plus a `pairing` mode in `book.js`, and
images that bleed across the gutter line up, because each leaf is sized to an exact
half of the spread.

## Reading them

| | |
|---|---|
| `←` `→` `space` | turn spreads |
| click a page, or `Z` | zoom the spread at full resolution (drag to pan, scroll to zoom) |
| `G` | index of all spreads |
| `F` | fullscreen |
| `Home` / `End` | first / last spread |
| swipe | turn spreads on touch |

Narrow or portrait windows switch to one leaf at a time. `#p12` in the URL opens at
that leaf, so you can link someone straight to a spread.

## Updating a book

The build tools, once:

```bash
brew install poppler webp
pip3 install pillow
```

Then for each new edition, naming the PDF and the book directory. **Start with the
pull** — anything edited on github.com lives only there until you fetch it, and a
build on top of a stale clone cannot be pushed:

```bash
git pull --rebase
./build.sh "path/to/Photography Portfolio.pdf" photography
./build.sh "path/to/Work Samples.pdf" work
git add -A && git commit -m "update books" && git push
```

`build.sh` rewrites that book's page images, its `book.js` (leaf count, aspect ratio
and pairing mode) and its social card. It touches nothing outside the book directory,
so rebuilding one book cannot disturb the other. Any page count works; the pairing
and the index adapt.

Two messages worth recognising:

- **"nothing to commit, working tree clean"** — the rebuild produced identical files,
  so the PDF had not actually changed. Not an error, but it stops the `&&` chain
  before the push, so anything committed earlier stays unpushed.
- **"your branch and 'origin/main' have diverged"** — you committed locally while a
  different commit sits on the remote, usually a github.com edit. `git pull --rebase`
  replays your commit on top of it; then push. Nothing is lost either way.

## The knobs

The top of `assets/style.css` is a block of variables, and the gutter — the crease
down the middle of a spread — is the first of them:

```css
--gutter-strength: 1;      /* 1 full · .5 half · 0 off */
--gutter-width: 8.5%;
```

Each book then sets its own, keyed off `<body data-book="…">`:

```css
body[data-book="photography"]{ --gutter-strength: .5; }   /* half */
body[data-book="work"]       { --gutter-strength: 0; }    /* off  */
```

The work samples were drawn as flat spreads, so a crease down the middle would be
inventing a fold the artwork never had. The photography book was set as facing pages,
so it keeps a trace of one. The same block holds the reading ground, the hairline
around the page, the frame margin, and `--idle-after`, which `app.js` reads back out
of the CSS so the delay lives in one place.

## Type

| | | |
|---|---|---|
| **Redaction 35** | titles, book names, the wordmark | shipped with the site |
| **Plantin MT Pro** | everything else, figures included | falls back to Times New Roman |

Redaction 35 (Forest Young and Jeremy Mickel) is under the SIL Open Font License, so
it is self-hosted in `assets/fonts/` with its licence rather than loaded from a CDN.
Plantin is an Adobe font and cannot be redistributed; the stack names it first, so it
appears on any machine that has it — yours, via Adobe Fonts — and everyone else gets
Times New Roman, which was drawn from Plantin and is its closest living relative.

Two families, not three: the folios and index labels are set in the body face rather
than a monospace, so the interface reads as one voice.

Sizes come from six steps in `assets/type.css` (`--t1` … `--t6`) and nothing sits
between them: 30 / 18 / 14 / 12.5 / 11 / 10.5. Spacing runs on one rhythm, `--s1` …
`--s5`. Nothing on any page moves: the inverted hover band is drawn with `box-shadow`
rather than padding, so hovering can never reflow a line.

## Editing the viewer

`assets/type.css`, `assets/style.css` and `assets/app.js` are the only copies, shared
by every page, so a fix lands everywhere at once. When you change any of them, bump
the `?v=` number on the `<link>` and `<script>` tags in **all three** of `index.html`,
`photography/index.html` and `work/index.html`. GitHub Pages caches the HTML and the
assets for ten minutes independently, so without the bump a returning visitor can load
the new page against the old stylesheet. The number is arbitrary; any change works.

The two book shells are otherwise identical apart from their titles and page counts.

## Deploying

This is the user site repo, so GitHub Pages serves the root of `main` at
`kenny-t-vo.github.io`. The `.nojekyll` file keeps Jekyll from touching the asset
folders.

For a custom domain, add a `CNAME` file containing the domain and point a `CNAME`
DNS record at `kenny-t-vo.github.io`.

## Layout

```
index.html            the two books, and where else to find you
assets/type.css       shared: the face, the six sizes, the two link colours
assets/style.css      shared: the knobs, then the viewer
assets/app.js         shared: pairing, fit-to-window sizing, zoom lens, index
assets/fonts/         Redaction 35 + its licence
photography/
  index.html          book shell
  book.js             generated: leaf count, aspect, pairing mode
  pages/              generated: view / full / thumb WebP tiers
work/                 the same three, for the other book
cv/                   two pages, one spread, no controls — and the pdf itself
build.sh              PDF → one book's page images
```
