/* Spread viewer for the photography and work books: fit-to-window facing
   pages, keyboard/swipe navigation, full-resolution zoom lens, and a spread
   index. No dependencies. */

(() => {
  const BOOK = window.BOOK || { pages: 32, aspect: 612 / 792 };
  const N = BOOK.pages;
  const AR = BOOK.aspect;                       // single page width / height
  const pad = n => String(n).padStart(2, '0');
  const url = (tier, n) => `pages/${tier}/${pad(n)}.webp`;

  const stage   = document.getElementById('stage');
  const book    = document.getElementById('book');
  const prevBtn = document.getElementById('prev');
  const nextBtn = document.getElementById('next');
  const folioEl = document.getElementById('folio');
  const totalEl = document.getElementById('total');
  const gridEl  = document.getElementById('grid');
  const gridIn  = document.getElementById('grid-inner');
  const lensEl  = document.getElementById('lens');
  const lensSheet = document.getElementById('lens-sheet');
  const lensFr  = document.getElementById('lens-frame');

  totalEl.textContent = N;

  /* ---------- view model: which pages sit side by side ---------- */

  /* portrait pages open on a lone cover, then pair 2-3, 4-5 ...
     2-up exports were already spreads before build.sh split them into
     leaves, so those pair straight off. */
  const spreads = (() => {
    const out = [];
    let p = 1;
    if (BOOK.pairing !== 'spreads') { out.push([1]); p = 2; }
    for (; p <= N; p += 2) out.push(p === N ? [p] : [p, p + 1]);
    return out;
  })();
  const singles = Array.from({ length: N }, (_, i) => [i + 1]);

  const wantsSpreads = () =>
    window.innerWidth >= 640 && window.innerWidth / window.innerHeight >= 1.1;

  let views = wantsSpreads() ? spreads : singles;
  let page  = 1;                                 // anchor page
  let idx   = 0;                                 // index into `views`

  const findView = p => views.findIndex(v => v.includes(p));

  /* ---------- rendering ---------- */

  const cache = new Map();
  function preload(tier, n) {
    const key = tier + n;
    if (cache.has(key) || n < 1 || n > N) return;
    const img = new Image();
    img.src = url(tier, n);
    cache.set(key, img);
  }

  function render() {
    const view = views[idx];
    book.dataset.leaves = view.length;
    book.classList.toggle('zoomable', true);
    book.replaceChildren(...view.map(n => {
      const leaf = document.createElement('div');
      leaf.className = 'leaf';
      leaf.style.backgroundImage = `url(${url('thumb', n)})`;
      leaf.dataset.page = n;
      const img = new Image();
      img.alt = `Page ${n}`;
      img.decoding = 'async';
      img.src = url('view', n);
      const show = () => img.classList.add('ready');
      img.complete ? show() : img.addEventListener('load', show, { once: true });
      leaf.append(img);

      /* link overlays from the pdf */
      for (const L of (BOOK.links && BOOK.links[n]) || []) {
        const a = document.createElement('a');
        a.className = 'pin';
        a.href = L.href;
        /* the band covers the printed words while hovered, so say where it goes */
        a.title = L.href.replace(/^mailto:/, '').replace(/\?subject=$/, '');
        a.setAttribute('aria-label', a.title);
        if (/^https?:/i.test(L.href)) { a.target = '_blank'; a.rel = 'noopener noreferrer'; }
        /* url() in a custom property resolves against the stylesheet, not the
           page, so hand it an absolute one */
        if (L.chip) a.style.setProperty('--chip', `url(${new URL(L.chip, location.href).href})`);
        a.style.left   = L.x * 100 + '%';
        a.style.top    = L.y * 100 + '%';
        a.style.width  = L.w * 100 + '%';
        a.style.height = L.h * 100 + '%';
        leaf.append(a);
      }
      return leaf;
    }));

    layout();
    folioEl.textContent = view.length > 1 ? `${view[0]}–${view[1]}` : view[0];
    prevBtn.disabled = idx === 0;
    nextBtn.disabled = idx === views.length - 1;
    history.replaceState(null, '', `#p${view[0]}`);

    for (const off of [1, -1, 2]) {
      const v = views[idx + off];
      if (v) v.forEach(n => preload('view', n));
    }
    if (gridIn.childElementCount) markCurrentChip();
  }

  function layout() {
    const cs = getComputedStyle(stage);
    const availW = stage.clientWidth  - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    const availH = stage.clientHeight - parseFloat(cs.paddingTop)  - parseFloat(cs.paddingBottom);
    const leaves = views[idx].length;
    const ar = leaves * AR;

    let w = availW, h = w / ar;
    if (h > availH) { h = availH; w = h * ar; }
    w = Math.max(2, Math.round(w / leaves) * leaves);   // even split, no seam
    h = Math.round(w / ar);

    book.style.width  = w + 'px';
    book.style.height = h + 'px';
  }

  /* ---------- navigation ---------- */

  function goToView(i, anchor) {
    hideHint(false);
    idx = Math.max(0, Math.min(views.length - 1, i));
    page = anchor ?? views[idx][0];
    render();
  }
  function goToPage(p) {
    page = Math.max(1, Math.min(N, p));
    idx = findView(page);
    render();
  }
  const step = d => goToView(idx + d);

  prevBtn.addEventListener('click', () => step(-1));
  nextBtn.addEventListener('click', () => step(1));

  /* re-pair pages when the window shape changes */
  let lastMode = views === spreads;
  function onResize() {
    const mode = wantsSpreads();
    if (mode !== lastMode) {
      lastMode = mode;
      views = mode ? spreads : singles;
      idx = findView(page);
      render();
      if (!lensEl.hidden) openLens(idx);
      offerHint();
    } else {
      layout();
    }
  }
  window.addEventListener('resize', onResize);
  window.addEventListener('orientationchange', () => setTimeout(onResize, 120));

  /* ---------- keyboard ---------- */

  document.addEventListener('keydown', e => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const inLens = !lensEl.hidden;
    const inGrid = !gridEl.hidden;

    switch (e.key) {
      case 'ArrowRight': case 'PageDown': case ' ':
        e.preventDefault();
        inLens ? lensGo(1) : step(1); break;
      case 'ArrowLeft': case 'PageUp':
        e.preventDefault();
        inLens ? lensGo(-1) : step(-1); break;
      case 'Home': e.preventDefault(); inLens ? openLens(0) : goToView(0); break;
      case 'End':  e.preventDefault();
        inLens ? openLens(views.length - 1) : goToView(views.length - 1); break;
      case 'Escape': if (inLens) closeLens(); else if (inGrid) closeGrid(); break;
      case 'g': case 'G': inGrid ? closeGrid() : openGrid(); break;
      case 'z': case 'Z': inLens ? closeLens() : openLens(idx); break;
      case 'f': case 'F': toggleFullscreen(); break;
    }
  });

  /* ---------- pointer: swipe to turn, click to zoom ---------- */

  let down = null;
  stage.addEventListener('pointerdown', e => {
    if (e.button !== 0) return;
    down = { x: e.clientX, y: e.clientY, t: Date.now(), target: e.target };
  });
  stage.addEventListener('pointerup', e => {
    if (!down) return;
    const dx = e.clientX - down.x, dy = e.clientY - down.y;
    const moved = Math.hypot(dx, dy);
    const leaf = down.target.closest?.('.leaf');
    if (moved > 44 && Math.abs(dx) > Math.abs(dy) * 1.4) {
      step(dx < 0 ? 1 : -1);
    } else if (moved < 10 && leaf && Date.now() - down.t < 600
               && !down.target.closest?.('a')) {
      openLens(idx);          // links handle their own taps
    }
    down = null;
  });
  stage.addEventListener('pointercancel', () => { down = null; });

  /* ---------- index overlay ---------- */

  const gridBtn = document.getElementById('grid-btn');
  gridBtn.addEventListener('click', () => (gridEl.hidden ? openGrid() : closeGrid()));

  function buildGrid() {
    gridIn.style.setProperty('--chip-ar', String(2 * AR));
    gridIn.replaceChildren(...spreads.map((view, i) => {
      const chip = document.createElement('button');
      chip.className = 'chip';
      chip.dataset.view = i;
      const pages = document.createElement('div');
      pages.className = 'chip__pages';
      view.forEach(n => {
        const im = new Image();
        im.src = url('thumb', n);
        im.alt = `Page ${n}`;
        im.loading = 'lazy';
        pages.append(im);
      });
      const label = document.createElement('span');
      label.className = 'chip__label';
      label.textContent = i === 0 && BOOK.pairing !== 'spreads' ? 'COVER'
        : view.length > 1 ? `${view[0]}–${view[1]}` : String(view[0]);
      chip.append(pages, label);
      chip.addEventListener('click', () => { closeGrid(); goToPage(view[0]); });
      return chip;
    }));
  }
  function markCurrentChip() {
    const here = views[idx][0];
    gridIn.querySelectorAll('.chip').forEach((c, i) =>
      c.setAttribute('aria-current', String(spreads[i].includes(here))));
  }
  function openGrid() {
    if (!gridIn.childElementCount) buildGrid();
    markCurrentChip();
    gridEl.hidden = false;
    document.body.classList.add('veiled');
    gridBtn.setAttribute('aria-pressed', 'true');
    gridIn.querySelector('[aria-current="true"]')?.scrollIntoView({ block: 'center' });
  }
  function closeGrid() {
    gridEl.hidden = true;
    document.body.classList.remove('veiled');
    gridBtn.setAttribute('aria-pressed', 'false');
  }

  /* ---------- zoom lens ---------- */

  let lensIdx = 0, scale = 1, fitScale = 1, tx = 0, ty = 0, nat = { w: 1, h: 1 };
  const pointers = new Map();
  let pinch = null;

  document.getElementById('zoom-btn')
    .addEventListener('click', () => (lensEl.hidden ? openLens(idx) : closeLens()));

  /* the lens holds the whole spread, so an image crossing the gutter stays
     whole. page size is known up front, so the sheet is laid out and fitted
     before anything loads. */
  function openLens(i) {
    lensIdx = Math.max(0, Math.min(views.length - 1, i));
    const view = views[lensIdx];
    const pw = BOOK.fullWidth || 2600;
    const ph = Math.round(pw / AR);
    nat = { w: pw * view.length, h: ph };

    lensSheet.dataset.leaves = view.length;
    lensSheet.style.width  = nat.w + 'px';
    lensSheet.style.height = nat.h + 'px';
    lensSheet.replaceChildren(...view.map(n => {
      const pg = document.createElement('div');
      pg.className = 'lens__page';
      pg.style.width  = pw + 'px';
      pg.style.height = ph + 'px';
      pg.style.backgroundImage = `url(${url('view', n)})`;   // already cached: no blank frame
      const img = new Image();
      img.alt = `Page ${n}, full resolution`;
      img.decoding = 'async';
      img.draggable = false;
      img.src = url('full', n);
      const show = () => img.classList.add('ready');
      img.complete ? show() : img.addEventListener('load', show, { once: true });
      pg.append(img);
      return pg;
    }));

    lensEl.hidden = false;
    document.body.classList.add('veiled');
    fit();
    (views[lensIdx + 1] || []).forEach(n => preload('full', n));
  }
  function closeLens() {
    lensEl.hidden = true;
    document.body.classList.remove('veiled');
    if (lensIdx !== idx) goToView(lensIdx);
  }
  function lensGo(d) {
    openLens(lensIdx + d);
  }

  function frameBox() {
    return { w: lensFr.clientWidth, h: lensFr.clientHeight };
  }
  function fit() {
    const f = frameBox();
    const m = window.innerWidth < 700 ? 8 : 40;
    fitScale = Math.min((f.w - m * 2) / nat.w, (f.h - m * 2) / nat.h);
    scale = fitScale;
    tx = (f.w - nat.w * scale) / 2;
    ty = (f.h - nat.h * scale) / 2;
    apply();
  }
  function clampPan() {
    const f = frameBox();
    const w = nat.w * scale, h = nat.h * scale;
    tx = w <= f.w ? (f.w - w) / 2 : Math.min(0, Math.max(f.w - w, tx));
    ty = h <= f.h ? (f.h - h) / 2 : Math.min(0, Math.max(f.h - h, ty));
  }
  function apply() {
    clampPan();
    lensSheet.style.transform = `translate3d(${tx}px, ${ty}px, 0) scale(${scale})`;
  }
  function zoomAt(cx, cy, next) {
    const maxS = Math.max(fitScale * 4, 1);
    next = Math.max(fitScale, Math.min(maxS, next));
    const k = next / scale;
    tx = cx - (cx - tx) * k;
    ty = cy - (cy - ty) * k;
    scale = next;
    apply();
  }

  lensFr.addEventListener('wheel', e => {
    e.preventDefault();
    const r = lensFr.getBoundingClientRect();
    zoomAt(e.clientX - r.left, e.clientY - r.top, scale * Math.exp(-e.deltaY * 0.0022));
  }, { passive: false });

  lensFr.addEventListener('dblclick', e => {
    const r = lensFr.getBoundingClientRect();
    zoomAt(e.clientX - r.left, e.clientY - r.top,
           scale > fitScale * 1.05 ? fitScale : Math.max(1, fitScale * 2.5));
  });

  lensFr.addEventListener('pointerdown', e => {
    lensFr.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    lensFr.classList.add('dragging');
    if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), s: scale };
    }
  });
  lensFr.addEventListener('pointermove', e => {
    const p = pointers.get(e.pointerId);
    if (!p) return;
    const dx = e.clientX - p.x, dy = e.clientY - p.y;
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });

    if (pointers.size === 2 && pinch) {
      const [a, b] = [...pointers.values()];
      const d = Math.hypot(a.x - b.x, a.y - b.y);
      const r = lensFr.getBoundingClientRect();
      zoomAt((a.x + b.x) / 2 - r.left, (a.y + b.y) / 2 - r.top, pinch.s * (d / pinch.d));
    } else if (pointers.size === 1) {
      tx += dx; ty += dy; apply();
    }
  });
  const endPointer = e => {
    pointers.delete(e.pointerId);
    if (pointers.size < 2) pinch = null;
    if (!pointers.size) lensFr.classList.remove('dragging');
  };
  lensFr.addEventListener('pointerup', endPointer);
  lensFr.addEventListener('pointercancel', endPointer);

  window.addEventListener('resize', () => { if (!lensEl.hidden) fit(); });

  document.querySelectorAll('[data-close]').forEach(b =>
    b.addEventListener('click', () => (lensEl.hidden ? closeGrid() : closeLens())));
  gridEl.addEventListener('click', e => { if (e.target === gridEl) closeGrid(); });

  /* ---------- fullscreen + idle chrome ---------- */

  const fullBtn = document.getElementById('full-btn');
  function toggleFullscreen() {
    document.fullscreenElement ? document.exitFullscreen()
      : document.documentElement.requestFullscreen?.().catch(() => {});
  }
  fullBtn.addEventListener('click', toggleFullscreen);
  document.addEventListener('fullscreenchange', () =>
    fullBtn.setAttribute('aria-pressed', String(!!document.fullscreenElement)));

  /* --idle-after is defined in style.css */
  const idleAfter = parseFloat(
    getComputedStyle(document.documentElement).getPropertyValue('--idle-after')) || 2600;

  /* ---------- rotate hint ---------- */

  /* upright shows a single leaf with no hint that spreads exist. shown once,
     on touch devices only, and not again after a spread is seen. */
  const hintEl = document.getElementById('rotate-hint');
  const canRotate = matchMedia('(hover: none) and (pointer: coarse)').matches;
  const HINT_KEY = 'kv:spread-hint-done';
  let hintTimer;

  const hintDone = () => {
    try { return localStorage.getItem(HINT_KEY) === '1'; } catch { return false; }
  };
  const retireHint = () => {
    try { localStorage.setItem(HINT_KEY, '1'); } catch { /* private window: fine */ }
  };
  function hideHint(forGood) {
    if (!hintEl) return;
    hintEl.hidden = true;
    clearTimeout(hintTimer);
    if (forGood) retireHint();
  }
  function offerHint() {
    if (!hintEl || !canRotate || hintDone()) return;
    if (views === spreads) return hideHint(true);   // already seen a spread
    hintEl.hidden = false;
    clearTimeout(hintTimer);
    /* 6s, then retire it so it is not shown again */
    hintTimer = setTimeout(() => hideHint(true), 6000);
  }

  let idleTimer;
  const wake = () => {
    document.body.classList.remove('idle');
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => document.body.classList.add('idle'), idleAfter);
  };
  ['pointermove', 'pointerdown', 'keydown', 'wheel'].forEach(ev =>
    window.addEventListener(ev, wake, { passive: true }));
  wake();

  /* ---------- boot ---------- */

  const fromHash = () => {
    const m = location.hash.match(/p?(\d+)/);
    return m ? Math.max(1, Math.min(N, Number(m[1]))) : 1;
  };
  page = fromHash();
  idx = findView(page);
  render();
  offerHint();
  window.addEventListener('hashchange', () => {
    const p = fromHash();
    if (!views[idx].includes(p)) goToPage(p);
  });
})();
