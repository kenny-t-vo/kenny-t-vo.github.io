"""Read link annotations out of a PDF.

Rasterising a page to WebP drops them. build.sh calls this and the viewers
lay transparent anchors over the page image. Coordinates are fractions of a
leaf, so render width, display size and zoom don't change them.
"""


def extract(pdf_path, leaves=1):
    """Return {leaf_number: [{x, y, w, h, href}, ...]}.

    `leaves` is how many leaves each PDF page splits into: 1 for portrait, 2 for
    a landscape 2-up. Rectangles are clipped per leaf, so a link crossing the
    gutter comes back as two pieces.

    Raises ImportError if pypdf is missing.
    """
    from pypdf import PdfReader

    links = {}
    reader = PdfReader(pdf_path)

    for page_index, page in enumerate(reader.pages):
        box = page.cropbox if page.get("/CropBox") else page.mediabox
        origin_x, origin_y = float(box.left), float(box.bottom)
        page_w, page_h = float(box.width), float(box.height)
        if page_w <= 0 or page_h <= 0:
            continue
        leaf_w = page_w / leaves

        for ref in (page.get("/Annots") or []):
            try:
                annot = ref.get_object()
            except Exception:
                continue                                  # broken ref
            if annot.get("/Subtype") != "/Link":
                continue
            action = annot.get("/A") or {}
            uri = action.get("/URI")
            rect = annot.get("/Rect")
            if not uri or not rect or len(rect) != 4:
                continue                     # internal jump or malformed

            r = [float(v) for v in rect]
            x0, x1 = sorted((r[0] - origin_x, r[2] - origin_x))
            y0, y1 = sorted((r[1] - origin_y, r[3] - origin_y))

            for j in range(leaves):
                clip_x0 = max(x0, j * leaf_w)
                clip_x1 = min(x1, (j + 1) * leaf_w)
                if clip_x1 - clip_x0 <= 0.5:
                    continue                            # not on this leaf
                n = page_index * leaves + j + 1
                links.setdefault(str(n), []).append({
                    "x": round((clip_x0 - j * leaf_w) / leaf_w, 5),
                    "y": round((page_h - y1) / page_h, 5),   # pdf y up, css y down
                    "w": round((clip_x1 - clip_x0) / leaf_w, 5),
                    "h": round((y1 - y0) / page_h, 5),
                    "href": str(uri),
                })

    return links


def count(links):
    return sum(len(v) for v in links.values())


# ── snapping to the ink, and rendering the highlight chip ────────────────────
#
# InDesign places link rects on the text frame, so each is re-centred on the
# ink in the rendered page. The words are part of the page image, so the hover
# state is an inverted copy of the patch, rendered here.

# band height comes from the rect, which is constant across a text run; ink
# height varies with descenders. 1.25 x rect matches the site's 1.55em band.
_BAND_OVER_RECT = 1.25
_SIDE_OVER_RECT = 0.124  # side padding, x rect height
_INK_MAX_LUM   = 0.75   # darker than this counts as ink
_PAPER_MIN     = 0.50   # minimum paper fraction to render a chip


def _luma(p):
    return (0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]) / 255


def _ink_box(im, rect):
    """Pixel box of the link's own line of ink.

    Scans rows inside the rect's x-range and keeps only the contiguous run of
    inked rows through the rect's centre, which excludes adjacent lines.
    """
    W, H = im.size
    rx0, ry0 = rect["x"] * W, rect["y"] * H
    rw, rh = rect["w"] * W, rect["h"] * H
    wy0, wy1 = max(0, int(ry0 - rh * 0.6)), min(H, int(ry0 + rh * 1.6))
    x0, x1 = max(0, int(rx0)), min(W, int(rx0 + rw))
    if x1 <= x0 or wy1 <= wy0:
        return None

    crop = im.crop((x0, wy0, x1, wy1))
    px = crop.load()
    inked = [any(_luma(px[x, y]) < _INK_MAX_LUM for x in range(crop.width))
             for y in range(crop.height)]
    if not any(inked):
        return None

    centre = int(ry0 + rh / 2) - wy0
    if not (0 <= centre < len(inked)) or not inked[centre]:
        centre = min((i for i, v in enumerate(inked) if v),
                     key=lambda i: abs(i - centre))
    top = centre
    while top > 0 and inked[top - 1]:
        top -= 1
    bot = centre
    while bot < len(inked) - 1 and inked[bot + 1]:
        bot += 1

    cols = [x for y in range(top, bot + 1) for x in range(crop.width)
            if _luma(px[x, y]) < _INK_MAX_LUM]
    if not cols:
        return None
    return (x0 + min(cols), wy0 + top, x0 + max(cols) + 1, wy0 + bot + 1)


def _isolate(patch, keep_top, keep_bottom):
    """White out everything above and below the link's own line of type.

    The band is taller than the ink and on tight leading reaches the adjacent
    lines, which would otherwise show inverted in the chip.
    """
    from PIL import ImageDraw
    out = patch.copy()
    d = ImageDraw.Draw(out)
    if keep_top > 0:
        d.rectangle([0, 0, out.width, keep_top - 1], fill=(255, 255, 255))
    if keep_bottom < out.height:
        d.rectangle([0, keep_bottom, out.width, out.height], fill=(255, 255, 255))
    return out


def _chip(crop):
    """Invert and recolour the patch: paper to #0000ee, ink to white, on a
    linear ramp so the antialiasing survives."""
    g = crop.convert("L")
    light = g.point(lambda v: 255 - v)                       # ink -> bright
    blue = g.point(lambda v: round(238 + 17 * (255 - v) / 255))
    from PIL import Image
    return Image.merge("RGB", (light, light, blue))


def fit_to_ink(links, leaf_image, chip_dir, chip_url):
    """Re-centre every rect on its ink and render its highlight chip.

    `leaf_image(n)` returns the full-resolution render of leaf n, or None.
    Returns a new links dict; rects that can't be fitted pass through as is.
    """
    import glob, os, subprocess
    # chips are named by leaf and index, which change between editions
    for stale in glob.glob(f"{chip_dir}/*.webp"):
        os.remove(stale)
    os.makedirs(chip_dir, exist_ok=True)
    out = {}

    for leaf, items in links.items():
        im = leaf_image(int(leaf))
        if im is None:
            out[leaf] = items
            continue
        W, H = im.size

        boxes = [_ink_box(im, r) for r in items]

        fitted = []
        for i, (r, b) in enumerate(zip(items, boxes)):
            if not b:
                fitted.append(r)
                continue
            rect_h = r["h"] * H
            band_h = rect_h * _BAND_OVER_RECT
            pad_h = rect_h * _SIDE_OVER_RECT
            cy = (b[1] + b[3]) / 2          # centred on the ink, sized off the rect
            x0 = max(0, b[0] - pad_h)
            x1 = min(W, b[2] + pad_h)
            y0 = max(0, cy - band_h / 2)
            y1 = min(H, cy + band_h / 2)

            entry = dict(r)
            entry.update(x=round(x0 / W, 5), y=round(y0 / H, 5),
                         w=round((x1 - x0) / W, 5), h=round((y1 - y0) / H, 5))

            patch = im.crop((int(x0), int(y0), int(x1), int(y1)))
            patch = _isolate(patch, int(b[1] - y0), int(b[3] - y0))
            paper = sum(1 for p in patch.getdata() if _luma(p) > 0.78)
            if paper / max(1, patch.width * patch.height) >= _PAPER_MIN:
                name = f"{leaf}-{i}.webp"
                tmp = f"{chip_dir}/.{leaf}-{i}.png"
                _chip(patch).save(tmp)          # Pillow here has no webp writer
                subprocess.run(["cwebp", "-quiet", "-lossless", "-m", "6",
                                "-metadata", "none", tmp,
                                "-o", f"{chip_dir}/{name}"], check=True)
                os.remove(tmp)
                entry["chip"] = f"{chip_url}/{name}"
            fitted.append(entry)
        out[leaf] = fitted

    return out
