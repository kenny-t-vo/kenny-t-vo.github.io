# kenny vo, books.

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

Then for each new edition, naming the PDF and the book directory:

```bash
./build.sh "path/to/Photography Portfolio.pdf" photography
./build.sh "path/to/Work Samples.pdf" work
git add -A && git commit -m "update books" && git push
```

`build.sh` rewrites that book's page images, its `book.js` (leaf count, aspect ratio
and pairing mode) and its social card. It touches nothing outside the book directory,
so rebuilding one book cannot disturb the other. Any page count works; the pairing
and the index adapt.

## Editing the viewer

`assets/app.js` and `assets/style.css` are the only copies, shared by both books, so
a fix lands in both at once. When you change either, bump the `?v=` number on the
`<script>` and `<link>` tags in **both** `photography/index.html` and
`work/index.html`. GitHub Pages caches the HTML and the assets for ten minutes
independently, so without the bump a returning visitor can load the new page against
the old script. The number is arbitrary; any change to it works.

The two book shells are otherwise identical apart from their titles and page counts.

## Deploying

This is the user site repo, so GitHub Pages serves the root of `main` at
`kenny-t-vo.github.io`. The `.nojekyll` file keeps Jekyll from touching the asset
folders.

For a custom domain, add a `CNAME` file containing the domain and point a `CNAME`
DNS record at `kenny-t-vo.github.io`.

## Layout

```
index.html            the two books, listed
assets/style.css      shared: dark reading room, chrome that fades when idle
assets/app.js         shared: pairing, fit-to-window sizing, zoom lens, index
photography/
  index.html          book shell
  book.js             generated: leaf count, aspect, pairing mode
  pages/              generated: view / full / thumb WebP tiers
work/                 the same four, for the other book
build.sh              PDF → one book's page images
```
