#!/usr/bin/env bash
# Render a PDF into the pages one document needs.
#   ./build.sh path/to/book.pdf <dir>
# e.g. ./build.sh "~/portfolio.pdf" photography
#      ./build.sh "~/cv.pdf" cv
#
# Books (photography, work) get three lossy tiers and handle both export shapes:
#   portrait pages  -> paired as cover, 2-3, 4-5 ... last alone
#   landscape 2-ups -> already spreads; split into leaves, paired 1-2, 3-4 ...
#
# The cv is different and gets its own path: one lossless tier, because it is
# type rather than photographs, and lossless is both crisper and smaller there.
# It has no zoom and no index, so it needs no other tier.
#
# Requires: poppler (pdftoppm), webp (cwebp), python3 with Pillow.
#   brew install poppler webp && pip3 install pillow
set -euo pipefail

PDF="${1:?usage: ./build.sh path/to/document.pdf <dir>}"
BOOK="${2:?usage: ./build.sh path/to/document.pdf <dir>}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$ROOT/$BOOK"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# ── the cv: one lossless tier, plus the pdf itself for download ──────────────
if [ "$BOOK" = "cv" ]; then
  CV_W=2000
  echo "→ cv: rendering at ${CV_W}px wide, lossless"
  mkdir -p "$DEST/pages"
  rm -f "$DEST/pages"/*.webp
  pdftoppm -png -scale-to-x "$CV_W" -scale-to-y -1 "$PDF" "$WORK/p"
  n=0
  for f in "$WORK"/p-*.png; do
    n=$((n + 1))
    cwebp -quiet -lossless -m 6 -metadata none "$f" -o "$DEST/pages/$n.webp"
    echo "  page $n"
  done
  cp "$PDF" "$DEST/Vo_Kenny_CV.pdf"
  echo "→ copied the pdf itself for the download link"

  # cv/index.html lists its pages by hand; say so if the count no longer matches
  TAGS=$(grep -c '<img src="pages/' "$DEST/index.html" || true)
  if [ "$n" -ne "$TAGS" ]; then
    echo "⚠  $n pages rendered but cv/index.html has $TAGS <img> tags."
    echo "   Edit cv/index.html so the two match, or the extra pages will not show."
  fi
  du -sh "$DEST/pages"
  exit 0
fi

FULL_W=2600   # px per leaf in the zoom tier; the master renders straight to it

read -r PTS_W PTS_H < <(pdfinfo "$PDF" | awk '/^Page size:/ {print $3, $5}')
LEAVES=$(python3 -c "print(2 if $PTS_W/$PTS_H > 1.3 else 1)")
echo "→ ${PTS_W}x${PTS_H} pts, $LEAVES leaf/leaves per page"

echo "→ rendering masters at $((FULL_W * LEAVES)) px wide"
pdftoppm -png -scale-to-x $((FULL_W * LEAVES)) -scale-to-y -1 "$PDF" "$WORK/m"

mkdir -p "$DEST/pages/full" "$DEST/pages/view" "$DEST/pages/thumb"
WORK="$WORK" DEST="$DEST" LEAVES="$LEAVES" FULL_W="$FULL_W" PDF="$PDF" python3 - <<'PY'
from PIL import Image
import glob, os, subprocess, json

work, dest = os.environ["WORK"], os.environ["DEST"]
leaves, full_w = int(os.environ["LEAVES"]), int(os.environ["FULL_W"])
TIERS = [("full", full_w, 88),   # click-to-zoom detail
         ("view", 1400, 88),     # what the spread shows
         ("thumb", 320, 80)]     # index grid + blur-up placeholder

masters = sorted(glob.glob(f"{work}/m-*.png"))

# a landscape export is already a spread: cut it back into leaves so the
# viewer can pair them itself, and so narrow screens get one page at a time
pages = []
for f in masters:
    im = Image.open(f).convert("RGB")
    if leaves == 2:
        half = im.width // 2
        pages += [im.crop((0, 0, half, im.height)), im.crop((half, 0, im.width, im.height))]
    else:
        pages.append(im)

for n, im in enumerate(pages, 1):
    for tier, w, q in TIERS:
        tmp = f"{work}/_scaled.png"
        (im if im.width == w else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)).save(tmp)
        subprocess.run(["cwebp", "-q", str(q), "-m", "6", "-sharp_yuv",
                        "-metadata", "none", tmp, "-o", f"{dest}/pages/{tier}/{n:02d}.webp"],
                       check=True, capture_output=True)
    print(f"  page {n:02d}", flush=True)

# ── live hyperlinks ──────────────────────────────────────────────────────
# The artwork prints its links blue and underlined, but the real targets live
# in the PDF as annotations, and rasterising throws them away. Lift the
# rectangles out so the viewer can lay transparent anchors over the page.
# Stored as fractions of a leaf, so they hold at any render size, and clipped
# per leaf so a link crossing the gutter survives the split.
links = {}
try:
    from pypdf import PdfReader
    reader = PdfReader(os.environ["PDF"])
    for pi, page in enumerate(reader.pages):
        box = page.cropbox if page.get("/CropBox") else page.mediabox
        ox, oy = float(box.left), float(box.bottom)
        pw, ph = float(box.width), float(box.height)
        lw = pw / leaves
        for ref in (page.get("/Annots") or []):
            try: o = ref.get_object()
            except Exception: continue
            if o.get("/Subtype") != "/Link": continue
            uri = (o.get("/A") or {}).get("/URI")
            rect = o.get("/Rect")
            if not uri or not rect or len(rect) != 4: continue
            r = [float(v) for v in rect]
            x0, x1 = sorted((r[0] - ox, r[2] - ox))
            y0, y1 = sorted((r[1] - oy, r[3] - oy))
            for j in range(leaves):
                cx0, cx1 = max(x0, j * lw), min(x1, (j + 1) * lw)
                if cx1 - cx0 <= 0.5: continue          # not on this leaf
                n = pi * leaves + j + 1
                links.setdefault(str(n), []).append({
                    "x": round((cx0 - j * lw) / lw, 5),
                    "y": round((ph - y1) / ph, 5),     # pdf y is up, css y is down
                    "w": round((cx1 - cx0) / lw, 5),
                    "h": round((y1 - y0) / ph, 5),
                    "href": str(uri),
                })
    print(f"→ carried over {sum(len(v) for v in links.values())} hyperlink(s)")
except ImportError:
    print("⚠  pypdf not installed — hyperlinks NOT carried over (pip3 install pypdf)")

first = pages[0]
aspect = round(first.width / first.height, 6)
pairing = "spreads" if leaves == 2 else "cover"
open(f"{dest}/book.js", "w").write(
    "/* generated by build.sh — do not edit by hand */\n"
    "window.BOOK = {\n"
    f"  pages: {len(pages)},\n"
    f"  aspect: {aspect},   /* leaf width / height */\n"
    f"  fullWidth: {full_w},     /* px width of the zoom tier */\n"
    f'  pairing: "{pairing}",   /* "cover": 1, 2-3 ... N alone | "spreads": 1-2, 3-4 ... */\n'
    "  /* live links lifted from the pdf, as fractions of a leaf */\n"
    f"  links: {json.dumps(links, indent=2)}\n"
    "};\n")

card = Image.new("RGB", (1200, 630), (14, 14, 14))
cov = pages[0] if leaves == 1 else Image.open(masters[0]).convert("RGB")
h = 520; w = round(cov.width * h / cov.height)
if w > 1160: w, h = 1160, round(cov.height * 1160 / cov.width)
card.paste(cov.resize((w, h), Image.LANCZOS), ((1200 - w) // 2, (630 - h) // 2))
card.save(f"{dest}/pages/social.jpg", quality=88, optimize=True)
print(f"→ {len(pages)} leaves, aspect {aspect}, pairing {pairing}")
PY

du -sh "$DEST/pages"
