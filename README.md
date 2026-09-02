# kenny vo, photography.

Self-hosted photography portfolio as a fit-to-window spread viewer.

**Live:** https://kenny-t-vo.github.io/kennyvophotography/

## How it works

The PDF is not sent to the browser. `build.sh` renders every page at 300 dpi and
derives three WebP tiers:

| tier | width | used for | total |
|---|---|---|---|
| `pages/view/` | 1400 px | the spread you read | 4.7 MB |
| `pages/full/` | 2600 px | click-to-zoom detail (native 300 dpi) | 19 MB |
| `pages/thumb/` | 320 px | index grid + blur-up placeholders | 244 KB |

A reader downloads roughly 300 KB per spread instead of the 56 MB PDF. The next and
previous spreads prefetch, so turning a page is instant.

Pages are paired the way the book was set: page 1 alone as the cover, then
2–3, 4–5 … 30–31, then 32 alone. Images that bleed across the gutter line up,
because each leaf is sized to an exact half of the spread.

## Reading it

| | |
|---|---|
| `←` `→` `space` | turn spreads |
| click a page, or `Z` | zoom the spread at full resolution (drag to pan, scroll to zoom) |
| `G` | index of all spreads |
| `F` | fullscreen |
| `Home` / `End` | cover / back cover |
| swipe | turn spreads on touch |

Narrow or portrait windows switch to one page at a time. `#p12` in the URL opens at
that page, so you can link someone straight to a spread.

## Updating the portfolio

The build tools, once:

```bash
brew install poppler webp
pip3 install pillow
```

Then for each new edition of the book:

```bash
./build.sh path/to/kennyvophotography.pdf
git add -A && git commit -m "update portfolio" && git push
```

`build.sh` rewrites the page images, `pages/manifest.json`, `assets/book.js`
(page count and page aspect ratio, read by the viewer) and the social card. Any page
count works; the pairing and the index adapt.

## Editing the viewer

Bump the `?v=` number on the `<script>` and `<link>` tags in `index.html` whenever
you change `assets/app.js` or `assets/style.css`. GitHub Pages caches the HTML and
the assets for ten minutes independently, so without the bump a returning visitor
can load the new page against the old script. The number is arbitrary; any change
to it works.

## Deploying

GitHub Pages serves the repo root as-is. In **Settings → Pages**, set
*Source: Deploy from a branch*, *Branch: `main` / `(root)`*. The `.nojekyll` file
keeps Jekyll from touching the asset folders.

For a custom domain, add a `CNAME` file containing the domain and point a `CNAME`
DNS record at `kenny-t-vo.github.io`.

## Layout

```
index.html          viewer shell
assets/style.css    dark reading room, chrome that fades when idle
assets/app.js       pairing, fit-to-window sizing, zoom lens, index
assets/book.js      generated: page count + aspect ratio
pages/              generated: view / full / thumb WebP tiers
build.sh            PDF → page images
```
