# Phase B.1 — Consolidated UX & Responsive Repair · Progress Log
Repo: `peptide-connect/` · Frontend: `frontend/` · Astro 5.18.2 static · Vanilla JS (no React/Tailwind)
Owner direction: repair existing shell, reposition as **seller-first storefront**, improve polish.
Constraints: canonical repo + Python pipeline untouched; 4-node constellation frozen; DEMO posture preserved;
no fabricated product/COA/supplier/pricing; no live payment/email; no framework/dep upgrades.

## Milestone 1 — Global layout & readability (P0) — DONE + VERIFIED
Files: `src/components/PageHeader.astro`, `src/components/Nav.astro`,
`src/pages/catalog/[slug].astro`, `src/pages/index.astro` (hero), `public/styles/app.css`.

Defects corrected (measured before → after):
- **Heading flush-left / clipped past left edge.** `PageHeader` was rendered un-wrapped with
  zero horizontal padding (`h1.left = 0`). Wrapped in `.container` → every heading now carries
  the responsive gutter (`h1.left = 16px @320–400, 31px @768, 155px @1440`). Added an
  `uncontainer` opt-out for the 404 page (which wraps the header itself).
- **Hero heading nearly invisible (navy on navy).** `.hero h1` inherited `var(--ink)`
  (#102D38) against the navy gradient → `color: rgb(16,45,56)`. Now explicit `var(--on-dark)`
  → `rgb(247,249,250)`. Verified readable.
- **Product detail overflow.** `1.3fr .7fr` grid never collapsed → **+221px overflow @320px**.
  Now `.product-layout` collapses to 1 column @≤860px. Overflow now **0px on all 7 pages at
  320/375/390/400/768/1440**.
- **Inconsistent gutters / empty space.** Unified `.container` gutter across header + sections.

## Milestone 2 — Navigation & interactions (P0) — DONE + VERIFIED
Files: `src/components/Nav.astro`, `public/js/app.js`, `src/components/DemoBanner.astro`,
`public/styles/app.css`.
- **Drawer couldn't open (M2 root cause).** `#nav-drawer` carried inline `display:flex` which
  overrode the `@media(max-width:860px)` `position:fixed` rule → drawer never became a drawer
  (stayed `position:static`). Removed the inline style; drawer is now `position:fixed` on mobile.
  Measured: desktop `toggle=display:none, drawer=static/flex`; mobile `toggle=inline-flex,
  drawer=fixed`.
- **Hamburger visible on desktop.** Stray duplicate `display:inline-flex` in `.nav__toggle`
  (last-declaration-wins) kept it always visible. Fixed → `display:none` on desktop.
- Full contract verified via real browser events: open, X-morph, link-click close, backdrop
  close, Escape close (+focus return), resize-to-desktop auto-close, body scroll-lock,
  aria-expanded/aria-controls/aria-label in sync.
- **Demo banner compact on mobile.** Shortened copy + `@media(max-width:520px)` smaller font/
  padding so it doesn't occupy a large share of the mobile viewport (still fully disclosed).

## Verification (M1+M2)
- `npm run build` → 17 pages, 0 errors.
- Overflow matrix: **7 pages × 6 widths, all 0px**.
- Nav interactions: all close-paths pass; 0 `undefined` leaks; DEMO banner intact on all pages.
- Before/after screenshots: `frontend/review/before/` + `frontend/review/after/`.
- Note: the browser harness decorates tab titles with a 🐴 glyph; on-disk `dist` titles are
  clean (verified by grep) — a harness artifact, not a code defect.

## Milestone 3 — Seller-first storefront (P1) — DONE + VERIFIED
Files: `src/pages/index.astro`, `src/pages/request.astro`, `src/components/ProductCard.astro`,
`public/styles/app.css`, `public/js/app.js` (journey CSS).
Homepage restructured to seller-first order:
1. Product-focused hero + prominent **Browse catalog** CTA (primary) + COA Explorer (secondary).
2. **Featured compounds** — 2×2 demo product cards: status badges, family/form/route, variant
   tags, **View details + Request** buttons (DEMO-labeled). Verified 2×2 grid, all 4 DEMO items.
3. "How requests work" 3-step **j: Browse → Request/confirm → Track**.
4. **Verification over marketing** (COA transparency, supporting): COA Explorer link + 3 points
   (honest empty states, claims≠facts).
5. **FAQ + contact** quick CTA row, plus research-use callout.
Request experience: added a **4-step journey stepper** + a **request summary** + a
**configuration-ready payment placeholder** (no real Zelle/crypto/wallet/payment details —
explicitly "not processed / Phase C"). No live payment.
ProductCard: added a Request CTA to the card; Unavailable items show a disabled "Unavailable"
badge instead of a Request button.
Overflow re-checked after M3: **7 pages × 6 widths, all 0px**.

## Milestone 4 — Visual polish & branding (P2) — DONE + VERIFIED
Files: `src/components/BrandMark.astro`, `src/components/Nav.astro`, `public/styles/app.css`, `public/js/app.js`.

### B.3.1 Final: Brand Rendering & Motion

**What changed:**

1. **Theme-aware BrandMark (header/footer):** Added `variant="auto"` rendering both `pc-mark-full.svg` (standard, navy anchor) and `pc-mark-reversed.svg` (reversed, teal). CSS rules swap visibility via `:root[data-theme="dark"]` on `.pc-brandmark__dark` / `.pc-brandmark__light`. Header now displays standard (light) or reversed (dark) logos; footer continues using reversed logo on dark surfaces. No JS toggles or color filters — instant theme switch with no layout shift. Reuses existing SVG assets.

2. **Theme toggle (sun + moon):** Replaced a single radially-symmetric sun icon with two distinct inline SVGs: sun (`#E07A5F`) in light, moon (`#F7F9FA`) in dark. One icon visible at a time via `:root[data-theme]` CSS swap. Added `aria-label="Switch to dark mode"` / `"Switch to light mode"` (next action) and `aria-pressed` synced to state. Keyboard focus ring via `:focus-visible`. Theme preference persists via `localStorage.pc-theme`; reload respects saved choice.

3. **Hero constellation entrance (Molecular Signal):** Rewrote 5-stroke constellation entrance (~1.4–1.8s) using Web Animations API + CSS transforms (no external library):
   - Anchor node fades and subtly scales into place.
   - Five strokes draw outward in a staggered sequence.
   - Teal nodes illuminate as strokes connect.
   - Single transient teal signal travels along one connection then fades.
   - Everything settles to the complete, approved static mark.
   - Force-visible fallback: `settle()` at 1.8s cancels any in-flight WAAPI animations (which could trap the anchor at opacity 0, scale 0.35) and clears inline start styles, reverting the SVG to its source geometry (fully drawn, fully opaque). The transient signal is removed on settle, so settled DOM exactly matches approved geometry.
   - `prefers-reduced-motion` guard checks `window.matchMedia('(prefers-reduced-motion: reduce)')` and skips entrance (showing the static mark). No-JS fallback is guaranteed because the source SVG has no inline hidden state (`opacity:0`/`strokeDashoffset`), and the entrance only applies entrance class if JS is available; if JS fails, the mark appears as is.

4. **No external animation libraries:** Uses CSS transitions (no-transition) and native Web Animations API only. Performance via transforms + opacity.

**Verification evidence (browser harness `pc-verify`):**

- Build: `npm run build` → 17 pages, 0 errors.
- Theme-aware branding:
  - Light header: `pc-mark-full.svg` (navy), sun icon visible (`#E07A5F`), `aria-label="Switch to dark mode"` → correct.
  - Dark header: `pc-mark-reversed.svg` (teal/mint), moon icon visible (`#F7F9FA`), `aria-label="Switch to light mode"` → correct.
  - Footer: reversed logo on dark surfaces (existing, confirmed).
  - Brand swap happens instantly on toggle; no JS dependency for header mark (CSS-driven).
- Theme toggle:
  - Sun & moon icons are visually distinct; no single-icon rotation used.
  - Only one icon visible at a time; `aria-label` always describes next action; `aria-pressed` mirrors state.
  - `localStorage.pc-theme` persists across reload.
  - Keyboard focus ring (`:focus-visible` box-shadow) applied.
- Hero constellation:
  - All 5 strokes settle to `strokeDashoffset: 0px`, `opacity: 1`.
  - All 4 nodes settle to `opacity: 1`, `transform: none`. Anchor (node index 1) was previously trapped at opacity 0, scale 0.35 — now fixed by `settle()` cancel+revert.
  - Transient `.pc-signal` element removed on settle; settled DOM matches approved geometry.
  - Animation duration: ~1.5s for active render; hard guarantee at 1.8s (settle fallback).
  - `prefers-reduced-motion` guard skips entrance; no-JS fallback guaranteed (built HTML has no hidden inline state — confirmed via grep for `opacity="0"` / `stroke-dashoffset` in `dist/`).
  - No console errors.
- Screenshots: `frontend/review/b31/home-light-theme.png` (226KB, navy header logo, sun icon, fully visible constellation) and `frontend/review/b31/home-dark-theme.png` (207KB, teal header logo, moon icon, fully visible constellation). Vision analysis confirms legible brand marks and distinct toggle icons in both themes.

**Files changed:**
- `src/components/BrandMark.astro` — added `auto` variant (full + reversed, CSS theme swap).
- `src/components/Nav.astro` — `variant="auto"`, dual sun+moon toggle with CSS swap + focus ring.
- `public/styles/app.css` — brand swap rules and `.theme-toggle:focus-visible` box-shadow.
- `public/js/app.js` — toggle aria sync IIFE (label, pressed, reflect, apply, boot) and Molecular Signal constellation entrance (anchor fade+scale, 5-stroke staggered draw, teal node illuminate, transient signal, settle cancel+revert, prefers-reduced-motion guard).

**Unresolved / minor:**
- Reduced-motion verification via `matchMedia` guard exists but harness cannot force system preference changes; documented that the fallback is code-verified.

---

## B.3.2 Milestone A — Hybrid Brand Identity (Catalog + Documentation journeys)

**Status:** DONE + VERIFIED

**What changed:**

1. **Homepage rewrite:** New headline "Research materials, connected to the evidence." and a compact "two-ways" block emphasizing Catalog (primary) + Documentation (secondary). Secondary CTA "Request" under the hero. Two-column hero layout preserved; BrandMark constellation entrance unchanged.

2. **Catalog landing (`src/pages/catalog/index.astro`):** Updated CATALOG_META to reflect new posture (honest, shipping-included pricing). Search filter bar preserved (IDs & data-attributes unchanged). Featured compound count updated (11 compounds / 15 variants). "Browse the catalog" heading and "shipping included" pricing note added.

3. **ProductCard (`src/components/ProductCard.astro`):** New hierarchy — dominant name under bold headline, neutral chemical descriptor below, compact spec block (Family/Form/Route/Sizes), single clear price line (from + spread + "shipping included"), two meaningful status badges only (StatusBadge + DocumentationBadge). Variant list compacted into price row. Preserved data attributes (`data-product-card`, `data-name`, `data-compound`, `data-family`, `data-status`) for client-side filter.

4. **Documentation explorer (`src/pages/documentation.astro`, formerly coa.astro):** Route renamed `/documentation` (nav now points to this). Updated to honest states (`no_record` → "No record on file", `pending` → "Requested · pending lab report", `contradictory` → "Report · uncorroborated"). Supplier column shows honest values ("Not linked", "Supplier A (unverified)"). "What is known" column contains honest plain-language notes. Explainer cards updated to customer-friendly language (removed internal schema terms; honest empty states explained). Search inputs preserved (#coa-search, #coa-results, [data-coa-row], data-compound, data-lot).

5. **Navigation rename:** "COA Explorer" → "Documentation" across nav and footer (site.ts, footerNav, nav). Redirect `/coa` → `/documentation` via meta refresh (no server redirect needed for static build).

6. **New DocumentationBadge component (`src/components/DocumentationBadge.astro`):** Single-badge representation of documentation state using honest labels only. Badge classes: `badge--demo` (neutral), `badge--inquire` (amber), `badge--contradictory` (dashed warn). Handles future full taxonomy while keeping honest posture now.

7. **Design tokens (`src/data/catalog.ts`):** New data shape reflecting owner-supplied prices with "shipping included". 11 compounds (including owner-added **Tirzepatide 20 mg $100, 40 mg $130**) and 15 variants. Documentation state taxonomy (`none`/`pending`/`contradictory` populated; `seller_submitted`/`manufacturer_supplied`/`lab_issued`/`independently_corroborated` defined but unpopulated). Honest COA/supplier states across data.

8. **App styles (`public/styles/app.css`):** Added `.badge--contradictory` dashed warn variant (background + color + border, same as `.badge--draft`) for "Report · uncorroborated" badge.

**Build verification:**
- `astro build` → 25 pages, 0 errors.
- All pages compiled: homepage, catalog (list + 11 slugs), documentation (replacing coa), redirect page (/coa → /documentation).
- No console errors; all HTML inspection confirms presence of new headline, two-ways block, catalog cards with DocumentationBadge, documentation explorer with honest states.

**Key acceptance criteria verified:**
- Homepage headline is "Research materials, connected to the evidence." ✓
- Two-ways block (Catalog → Documentation → Request) present and correctly linked ✓
- Catalog page shows 11 compounds / 15 variants with shipping-included pricing note ✓
- Product cards show dominant name, price line with from/spread/shipping, two meaningful status badges, variant compacted ✓
- Documentation explorer shows honest states, no fabricated COAs, customer-friendly language ✓
- Nav/footer rename "COA Explorer" → "Documentation" ✓
- Redirect page at /coa present (meta refresh) ✓
- No console errors ✓
- No fabrication of purity/test/supplier/cert data; documentation states honest ✓

**Files changed:**
- `src/data/catalog.ts` (new 413-line data shape with 11 compounds, 15 variants, honest COA states)
- `src/components/DocumentationBadge.astro` (new, 21 lines)
- `src/components/ProductCard.astro` (rewrite, 4231 bytes)
- `src/pages/index.astro` (homepage rewrite, 11733 bytes)
- `src/pages/catalog/index.astro` (catalog landing update, 3308 bytes)
- `src/pages/documentation.astro` (new, 5533 bytes, replaces coa.astro)
- `src/pages/coa.astro` (redirect static page, 444 bytes)
- `src/config/site.ts` (tagline + description + nav/footerNav rename, COA Explorer → Documentation)
- `public/styles/app.css` (add `.badge--contradictory` variant)

**Unresolved / minor:**
- None (M-A is complete). Milestone B is pending (About/Contact/Request/Order/FAQ wording changes).

---
