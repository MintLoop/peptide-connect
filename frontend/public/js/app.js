// public/js/app.js
// Client-side enhancements for the Astro static shell.
// No framework — vanilla ES6, zero dependencies. Progressive enhancement only.

/* ---------- Demo banner: dismissible, sessionStorage-persisted ---------- */
(function () {
  const banner = document.getElementById('demo-banner');
  if (!banner) return;
  const key = 'pc-demo-banner-dismissed';
  if (sessionStorage.getItem(key) === '1') {
    banner.setAttribute('data-hidden', '');
    return;
  }
  const close = document.getElementById('demo-banner-close');
  if (close) {
    close.addEventListener('click', () => {
      banner.setAttribute('data-hidden', '');
      sessionStorage.setItem(key, '1');
    });
  }
})();

/* ---------- Mobile navigation drawer ----------
   Contract: hamburger opens/closes; the same button morphs into an X; the
   backdrop / a link click / Escape / resize-to-desktop all close it.
   aria-expanded + aria-controls on the toggle; body scroll locked while open
   so background content doesn't scroll behind the drawer. */
(function () {
  const toggle = document.getElementById('nav-toggle');
  const drawer = document.getElementById('nav-drawer');
  const backdrop = document.getElementById('nav-backdrop');
  if (!toggle || !drawer) return;

  const isOpen = () => toggle.getAttribute('aria-expanded') === 'true';

  function syncBody() {
    document.body.style.overflow = isOpen() ? 'hidden' : '';
  }

  function setOpen(open) {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
    drawer.toggleAttribute('data-open', open);
    if (backdrop) backdrop.toggleAttribute('data-open', open);
    syncBody();
  }

  toggle.addEventListener('click', () => setOpen(!isOpen()));

  // Clicking a link closes the drawer (the click then navigates).
  drawer.querySelectorAll('a[href]').forEach(link => {
    link.addEventListener('click', () => setOpen(false));
  });

  // Backdrop click closes.
  if (backdrop) backdrop.addEventListener('click', () => setOpen(false));

  // Escape closes and returns focus to the toggle.
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isOpen()) {
      setOpen(false);
      toggle.focus();
    }
  });

  // Resize past the mobile breakpoint with the drawer open auto-closes it
  // (the drawer is display:none above 860px, so reset aria/body state).
  window.addEventListener('resize', () => {
    if (window.innerWidth > 860 && isOpen()) setOpen(false);
  });
})();

/* ---------- Active nav link highlight (per-page URL match) ---------- */
(function () {
  const path = location.pathname;
  document.querySelectorAll('[data-nav-link]').forEach((link) => {
    const href = link.getAttribute('href');
    if (href === path || (href !== '/' && path.startsWith(href))) {
      link.setAttribute('data-current', '');
    }
  });
})();

/* ---------- Catalog search / filter (progressive enhancement) ---------- */
(function () {
  const filterEl = document.getElementById('catalog-filter');
  const searchEl = document.getElementById('catalog-search');
  const familyEl = document.getElementById('catalog-family');
  const statusEl = document.getElementById('catalog-status');
  const grid = document.getElementById('catalog-grid');
  const emptyEl = document.getElementById('catalog-empty');
  if (!filterEl || !grid) return;

  // Gather all product cards from the grid
  const cards = Array.from(grid.querySelectorAll('[data-product-card]'));

  function applyFilter() {
    const q = (searchEl?.value || '').trim().toLowerCase();
    const fam = familyEl?.value || '';
    const status = statusEl?.value || '';
    let visible = 0;

    for (const card of cards) {
      const name = (card.dataset.name || '').toLowerCase();
      const compound = (card.dataset.compound || '').toLowerCase();
      const cardFamily = card.dataset.family || '';
      const cardStatus = card.dataset.status || '';

      let show = true;

      // Search
      if (q && !(name.includes(q) || compound.includes(q))) show = false;
      // Family filter
      if (fam && cardFamily !== decodeURIComponent(fam)) show = false;
      // Status filter
      if (status && cardStatus !== status) show = false;

      card.style.display = show ? '' : 'none';
      if (show) visible++;
    }

    if (emptyEl) {
      emptyEl.style.display = visible === 0 ? '' : 'none';
    }
    if (grid.parentElement) {
      grid.parentElement.style.display = visible > 0 ? '' : 'none';
    }
  }

  [searchEl, familyEl, statusEl].forEach((el) => {
    if (el) el.addEventListener('input', applyFilter);
  });
})();

/* ---------- COA Explorer search ---------- */
(function () {
  const searchEl = document.getElementById('coa-search');
  const results = document.getElementById('coa-results');
  if (!results) return;

  const rows = Array.from(results.querySelectorAll('[data-coa-row]'));

  searchEl?.addEventListener('input', () => {
    const q = (searchEl?.value || '').trim().toLowerCase();
    let visible = 0;
    for (const row of rows) {
      const text = (row.dataset.compound || '').toLowerCase() +
        ' ' + (row.dataset.lot || '').toLowerCase();
      const show = !q || text.includes(q);
      row.parentElement.style.display = show ? '' : 'none';
      if (show) visible++;
    }
    // If all are hidden, show an explicit empty message
    const emptyMsg = document.getElementById('coa-empty-results');
    if (emptyMsg) emptyMsg.style.display = visible === 0 ? '' : 'none';
  });
})();

/* ---------- Cart / order request (demo) ---------- */
(function () {
  const form = document.getElementById('request-form');
  if (!form) return;

  const DEMO_NOTICE =
    'DEMO: This form does not submit to a real backend. No data is sent, ' +
    'no order is created, no payment is processed. Click "Submit request" to see the confirmation flow.';

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    // Show a DEMO confirmation message
    let notice = document.getElementById('request-notice');
    if (!notice) {
      notice = document.createElement('div');
      notice.id = 'request-notice';
      notice.className = 'callout callout--warn';
      form.after(notice);
    }
    notice.innerHTML =
      '<strong class="callout__title">DEMO — not submitted</strong>' +
      DEMO_NOTICE +
      '<p style="margin-top:.75rem;color:var(--muted);font-size:var(--fs-sm);">' +
      'Phase C will wire this to a backend (Supabase / FastAPI) with ' +
      'real order creation, status tracking, and email confirmation.</p>';
    notice.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    form.reset();
   });
})();

/* ---------- Order status lookup (demo) ---------- */
(function () {
  const orderSearch = document.getElementById('order-search');
  const out = document.getElementById('order-result');
  if (!orderSearch || !out) return;
  orderSearch.addEventListener('submit', (e) => {
    e.preventDefault();
    const code = (orderSearch.value || '').trim();
    if (!code) {
      out.innerHTML =
         '<div class="callout"><p style="margin:0">Enter a tracking code to look up an order (DEMO).</p>' +
         '<p style="margin:.5rem 0 0;color:var(--muted);font-size:var(--fs-sm);">' +
         'Demo codes are not real. Phase C will wire this to the order backend.</p></div>';
       return;
      }
      // Demo: always "not found" — no fabricated order data, no real PII.
      out.innerHTML =
         '<div class="callout callout--info">' +
         '<strong class="callout__title">Order not found (DEMO)</strong>' +
         '<p style="margin:0;">' +
         'No order with code <code class="mono">' +
        code.replace(/[<>&]/g, '') +
        '</code> exists in this demo build. ' +
        'Phase C will serve real, PII-free order status from the backend.</p></div>';
   });
})();

/* ---------- Request form: prefill from ?product=slug ---------- */
(function () {
  const prefill = document.getElementById('request-prefill');
  if (!prefill) return;
  const params = new URLSearchParams(location.search);
  const slug = params.get('product');
  if (!slug) return;
  // DEMO catalog is rendered server-side; we can't fetch data here offline,
  // so we surface the intent and defer the actual fill to the backend (Phase C).
  prefill.textContent =
     'You arrived from a product request (product slug: ' +
     slug.replace(/[<>&"]/g, '') +
     '). Phase C will prefill this form with product details from the catalog backend.';
  prefill.style.display = 'block';
})();

/* ---------- Theme toggle ----------
   Reads the no-flash boot decision from <html data-theme>; the button flips
   it, persists an explicit choice to localStorage, and reflects the new state.
   Explicit choice wins over system preference. */
(function () {
  const key = 'pc-theme';
  const root = document.documentElement;
  const btn = document.getElementById('theme-toggle');

   // The accessible label + title always name the NEXT action (what clicking does),
    // so the toggle's meaning is explicit and stays in sync with the live theme state.
  function labelFor(current) {
    return current === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
    }
  function reflect(current) {
    if (!btn) return;
    btn.setAttribute('aria-pressed', current === 'dark' ? 'true' : 'false');
    btn.setAttribute('aria-label', labelFor(current));
    btn.setAttribute('title', labelFor(current));
    }
  function apply(theme) {
    root.setAttribute('data-theme', theme);
    root.style.colorScheme = theme;
    try { localStorage.setItem(key, theme); } catch (e) {}
    reflect(theme);
     }
   // Mirror the boot-applied theme onto the label as soon as the module runs.
  reflect(root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light');

  if (btn) {
    btn.addEventListener('click', () => {
      const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      apply(next);
       // Let other listeners react; the explicit choice already wins over the system pref.
      try { window.dispatchEvent(new CustomEvent('pc:themechange', { detail: { theme: next } })); } catch (e) {}
      });
    }
  // Follow system changes only when the user has NOT made an explicit choice.
  if (window.matchMedia) {
   const mq = window.matchMedia('(prefers-color-scheme: dark)');
   const on = mq.addEventListener ? function (cb) { mq.addEventListener('change', cb); } : null;
   if (on) on((e) => {
    let saved = null;
    try { saved = localStorage.getItem(key); } catch (err) {}
    if (!saved) apply(e.matches ? 'dark' : 'light');
    });
  }
})();

/* ---------- Hero constellation "Molecular Signal" entrance ----------
   One restrained entrance on the inline approved mark (4 nodes + 5 strokes;
   geometry comes from the frozen approved SVG, never re-authored here):
     1) the anchor node fades + subtly scales into place,
     2) the five strokes draw outward in a controlled staggered sequence,
     3) the teal nodes illuminate as their strokes reach them,
     4) a single subtle teal signal travels one existing connection, then fades,
     5) everything settles into the complete, recognizable static mark.
   - runs ONCE per page load; no continuous motion, spinning, or looping,
   - prefers-reduced-motion OR no-JS (or no Web Animations API) shows the
     complete static mark (the hidden start-state is applied here in JS only,
     so an absent/failed script leaves the mark fully visible),
   - the signal is a transient element that is removed on settle, so the
     settled DOM is exactly the approved geometry (no extra nodes/particles),
   - a force-visible fallback guarantees the mark is never left hidden, even
     in a backgrounded tab, and uses CSS transitions/opacity (no library). */
(function () {
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
   // The complete mark shows on its own; nothing below hides it unless we run.
  const hero = document.querySelector('.hero');
  const svg = hero && hero.querySelector('svg[aria-label*="constellation"], svg.pc-anim');
  if (!svg) return;
   // No heavy dependency: guard so reduced-motion / unsupported leave the full mark.
  if (reduce || typeof svg.animate !== 'function') return;

  const EASE = 'cubic-bezier(0.2, 0.7, 0.3, 1)';
  svg.classList.add('pc-anim');
  const lines = Array.from(svg.querySelectorAll('line'));
  const nodes = Array.from(svg.querySelectorAll('circle'));
  if (!lines.length && !nodes.length) return;

   // Measure each stroke length for the draw-in animation.
  lines.forEach(l => {
    l.__len = Math.hypot(l.x2.baseVal.value - l.x1.baseVal.value, l.y2.baseVal.value - l.y1.baseVal.value);
    });

  // Anchor = the single non-teal node (the navy/mint hub in the approved mark);
   // the remaining nodes are the teal ones that "illuminate" as they connect.
  const TEAL = '12A89D';
  const isTeal = n => {
    const h = (n.getAttribute('fill') || '').toUpperCase().replace(/[^0-9A-F]/g, '');
    return h === TEAL;
    };
   let anchor = nodes.find(n => !isTeal(n));
  if (!anchor && nodes.length) {
    let max = -1;
    nodes.forEach(n => { const r = n.r.baseVal.value || 0; if (r > max) { max = r; anchor = n; } });
    }
  const tealNodes = anchor ? nodes.filter(n => n !== anchor) : nodes;

   // Hidden start state (JS-only) so a no-JS load keeps the full mark visible.
  lines.forEach(l => {
    l.style.strokeDasharray = String(l.__len);
    l.style.strokeDashoffset = String(l.__len);
     });
  nodes.forEach(n => {
    n.style.opacity = '0';
    n.style.transformBox = 'fill-box';
    n.style.transformOrigin = 'center';
    n.style.transform = 'scale(0.35)';
    });

   // Final-state guarantee (belt-and-suspenders): whatever happens, the mark
    // becomes fully visible and any transient signal is removed, so the settled
     // DOM equals the approved geometry and the total entrance is <= ~1.6s.
  let settled = false;
  function settle() {
    if (settled) return;
    settled = true;
      // Cancel any in-flight WAAPI effects so a forwards-fill can't trap an
     // element (e.g. the anchor) in its hidden start state, then clear the
      // inline start-styles so the mark reverts to the source SVG geometry
      // (fully drawn, fully opaque) — exactly the approved static mark.
    [lines, nodes, Array.from(svg.querySelectorAll('.pc-signal'))].flat()
      .forEach(el => {
        try {
          if (el.getAnimations) el.getAnimations().forEach(a => a.cancel());
         } catch (e) {}
        });
    Array.from(svg.querySelectorAll('.pc-signal')).forEach(el => el.remove());
    lines.forEach(l => {
      l.style.strokeDasharray = '';
      l.style.strokeDashoffset = '';
       });
    nodes.forEach(n => {
      n.style.opacity = '';
      n.style.transform = '';
      n.style.transformBox = '';
      n.style.transformOrigin = '';
       });
     }
   window.setTimeout(settle, 1800);   // total entrance target ≈ 1.5s; never exceeds 1.8s

  try {
    // 1) Anchor node fades + scales into place.
   if (anchor) {
   anchor.animate(
     [{ opacity: 0, transform: 'scale(0.35)' }, { opacity: 1, transform: 'scale(1)' }],
         { duration: 300, delay: 0, easing: EASE, fill: 'forwards' });
    }
   // 2) The five strokes draw outward in a staggered sequence.
   lines.forEach((l, i) => {
    l.animate(
      [{ strokeDashoffset: l.__len }, { strokeDashoffset: 0 }],
      { duration: 420, delay: 160 + i * 120, easing: EASE, fill: 'forwards' });
     });
   // 3) Teal nodes illuminate as their connections reach them.
  tealNodes.forEach((n, i) => {
    n.animate(
      [{ opacity: 0, transform: 'scale(0.35)' }, { opacity: 1, transform: 'scale(1)' }],
      { duration: 320, delay: 560 + i * 110, easing: EASE, fill: 'forwards' });
    });
     // 4) A single subtle signal travels one existing connection, then fades out.
   if (lines[0]) {
    const l0 = lines[0];
    const x1 = l0.x1.baseVal.value, y1 = l0.y1.baseVal.value;
    const x2 = l0.x2.baseVal.value, y2 = l0.y2.baseVal.value;
    const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    dot.setAttribute('class', 'pc-signal');
    dot.setAttribute('r', '2.2');
    dot.setAttribute('cx', String(x1));
    dot.setAttribute('cy', String(y1));
    dot.style.fill = 'var(--teal, #12A89D)';
    dot.style.filter = 'drop-shadow(0 0 3px rgba(18, 168, 157, 0.55))';
     dot.style.opacity = '0';
   svg.appendChild(dot);
    dot.animate(
    [
       { cx: String(x1), cy: String(y1), opacity: 0 },
       { cx: String(x1 + (x2 - x1) * 0.5), cy: String(y1 + (y2 - y1) * 0.5), opacity: 1, offset: 0.35 },
       { cx: String(x2), cy: String(y2), opacity: 1, offset: 0.75 },
       { cx: String(x2), cy: String(y2), opacity: 0 }
       ],
     { duration: 520, delay: 980, easing: EASE, fill: 'forwards' });
    }
    } catch (err) {
      // Any failure reveals the complete mark at once — never leave it hidden.
     settle();
    }
})();

    /* ---------- Admin: non-interactive shell ---------- */
    (function () {
    const adminLock = document.getElementById('admin-lock');
    if (adminLock) {
    adminLock.addEventListener('click', () => {
      const msg = document.getElementById('admin-lock-msg');
      if (msg) {
        msg.style.display = 'block';
        msg.innerHTML = '<strong>Access denied.</strong> ' +
          'The admin panel requires a server-side session and a non-guessable ' +
          'URL token (Phase C). This is a frontend shell only — no mutations ' +
          'are performed here, and no real data is exposed.';
      }
    });
  }
})();
