"""Lift live hyperlinks out of a PDF.

Rasterising a page to WebP drops its link annotations. build.sh extracts them
here and the viewers overlay transparent anchors on the image.

Coordinates are fractions of a leaf, so they survive render width, display
size, and zoom.
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
