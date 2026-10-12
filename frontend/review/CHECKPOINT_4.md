# Peptide Connect — Checkpoint 4: Phase B Audit & Phase C Recommendations
**Date:** 2026-10-10 · **Status:** PROPOSED for owner visual review · **Build:** Astro 5.18.2, static

---

## 0. TL;DR
- **Consolidated** the prior `peptide-connect-web/` scaffold (uncommitted, no `src/`)
  into the canonical repo at `peptide-connect/frontend/`, preserving the
  Python pipeline (`pcconnect/`, 22 passing tests) and the approved brand assets.
- **Built Phase B** as a static, responsive, offline-safe shell: 17 pages,
  production build green, DEMO posture enforced everywhere.
- **Two real bugs found & fixed during review:** 
  1. `src/styles/*.css` was linked as `/styles/…` but in Astro *static* mode
     `src/` is not served → every page shipped **unstyled**. Fixed by making
     `public/styles/` the served copy.
  2. Mobile hamburger button had an inline `style="display:none;"`
     that **overrode** the `@media(max-width:860px)` rule → the toggle was
     invisible on mobile. Moved the desktop-hide into CSS so the media query wins.
- **B.3.1 Final: Brand Rendering & Motion** completed 2026-10-11:
  - Theme-aware BrandMark with `auto` variant (CSS swap between full/reversed).
  - Distinct sun (#E07A5F) and moon (#F7F9FA) toggle icons, aria-labels, persistence.
  - Hero constellation "Molecular Signal" entrance with anchor fade+scale, 5-stroke staggered draw, teal node illuminate, transient signal, force-visible fallback via settle() cancel+revert, prefers-reduced-motion guard, no-JS fallback.
  - Verified in real browser (both themes), all 5 strokes drawn, 4 nodes visible (anchor fixed), no console errors, screenshots in `review/b31/home-{light,dark}-theme.png`.
- **No blockers remaining.** Ready for owner visual review, then Phase C.

---

## 1. What shipped (Phase B deliverables)
| # | Deliverable | File(s) | Status |
|---|---|---|---|
| 1 | Homepage w/ branding + nav | `src/pages/index.astro` | ✅ hero (constellation on navy), how-it-works, values |
| 2 | Searchable catalog (demo) | `src/pages/catalog/index.astro`, `src/data/catalog.ts` | ✅ search + family + status filters, DEMO-labeled |
| 3 | Product detail | `src/pages/catalog/[slug].astro` | ✅ specs, variants, COA gate, request CTA |
| 4 | Cart / request-order shell | `src/pages/request.astro` | ✅ form shell, consent gates, DEMO confirm |
| 5 | Order-status placeholder | `src/pages/order.astro` | ✅ PII-free lookup, honest "not found" |
| 6 | COA Explorer (empty states) | `src/pages/coa.astro` | ✅ ledger of honest no-record/pending rows |
| 7 | Admin dashboard shell | `src/pages/admin.astro` | ✅ noindex, non-interactive, access deferred |
| 8 | Centralized branding + config | `src/config/site.ts` | ✅ single source of truth |
| 9 | Mobile layouts | `Nav.astro` drawer, responsive grids | ✅ hamburger + drawer verified @390px |
| + | Content/legal pages | `about/faq/contact/privacy/terms/shipping` | ✅ DRAFT-flagged |
| + | 404 | `src/pages/404.astro` | ✅ |

## 2. Verification evidence
- **Build:** `npm run build` → **17 pages, 0 errors** (`dist/` produced).
- **Python:** `/usr/bin/python3 -m pytest tests/test_v0.py` → **22 passed**
  (pipeline untouched; canonical repo still 2 commits, clean except new `frontend/`).
- **Brand:** 6/6 approved SVGs well-formed, each = **4 nodes + 5 teal strokes**
  (the frozen 4-node constellation; no 5th node / hexagon / flower). Geometry
  single-source: `frontend/brand/geometry.json`.
- **Screenshots:** `frontend/review/*.png` (desktop + 390px mobile home + open drawer).
- **No `undefined`/`null`/raw-`${}` leaks** in rendered HTML (grep-verified).
- **B.3.1 verification:** Screenshots in `frontend/review/b31/home-{light,dark}-theme.png`;
  all 5 strokes drawn, 4 nodes visible (anchor fixed), no console errors, reduced-motion
  and no-JS fallback verified via code guard + source inspection.

## 3. DEMO posture (brief-compliant)
- Persistent top banner on every page: "DEMO BUILD — … no real products, prices,
  suppliers, COAs, or customer information are shown."
- Catalog is a 4-item **DEMO** set; all variants inquiry-only (no real prices);
  every COA row is `no_record` / `pending` — **no fabricated purity or test data.**
- No live payment, no production email, no unverified supplier/COA claims.
- Admin is a non-interactive `noindex` shell that explicitly defers auth to Phase C.

## 4. Unresolved / minor
- **None blocking.** Minor polish candidates (non-blocking): product-card size
  badges could use more inter-card spacing on narrow widths; COA "Requested —
  awaiting lab" vs "No record" could get two distinct icon treatments.
- **Owner decisions needed** (Phase C, from PHASE_A B1–B9): real domain
  (`peptideconnect.example` is a placeholder), legal entity name, inbound email
  + sender domain for Resend, admin auth model (recommend cookie sessions),
  catalog starter (keep DEMO vs empty), and B3 (`leonlab.pro` WAF-blocked —
  unverified; no action taken).

## 5. B.3.1 Final: Brand Rendering & Motion (completed 2026-10-11)

Completed as part of Milestone 4 (visual polish & branding):

- **Theme-aware BrandMark** — header/nav now correctly shows standard (light) or reversed (dark) logos via CSS swap (`auto` variant), no JS dependency, no layout shift.
- **Theme toggle** — distinct sun (`#E07A5F`) and moon (`#F7F9FA`) icons, `aria-label` always describes next action, `aria-pressed` synced, keyboard focus ring, persists via `localStorage`.
- **Hero constellation entrance** — "Molecular Signal" entrance (~1.4–1.8s) with anchor fade+scale, 5-stroke staggered draw, teal node illuminate, transient teal signal, settle() cancel+revert fallback, prefers-reduced-motion guard, no-JS fallback (source SVG has no hidden state).
- **Build & verification** — `npm run build` → 17 pages, 0 errors; verified in real browser (both themes), 5/5 strokes drawn, 4/4 nodes visible (anchor fix), no console errors, screenshots in `review/b31/home-{light,dark}-theme.png`.
- **Files changed** — `src/components/BrandMark.astro`, `src/components/Nav.astro`, `public/styles/app.css`, `public/js/app.js`.

All three defects from the B.3.1 scope are now resolved and verified.

## 6. Phase C recommendations (ordered)
1. **Supabase project** (isolated ref, anon/auth/service_role, **RLS
   deny-by-default** + `REVOKE auto_expose` — PHASE_A R4). Migration template
   from GetReta's `0001_create_orders_schema.sql`, extended with
   `products, categories, variants, orders, order_items, order_events,
   communications, coa_*` (schema-aligned to
   `pcconnect/schemas/{analytical,dossier,lineage}.json`), `audit_log`,
   `site_config`, `admins`.
2. **FastAPI/Cloud Run API** reusing GetReta `server/comm/` (Resend +
   **Svix HMAC verify**, fail-safe, PII-minimized). Add product CRUD,
   request→status, `GET /status/:code` (PII-free), config read/write,
   append-only audit log. **Auth = server sessions** (httpOnly cookie) +
   rate limit + input validation + bot check (hCaptcha/Turnstile).
3. **Wire the frontend islands:** catalog filter (server or client),
   PDP COA gate (link only when record exists), request cart→review→confirm
   (human confirmation, **no auto-fulfillment**, no live payment),
   `/order/:code` live lookup, admin console (reuse GetReta UI shape),
   **COA Explorer** flips on when verified COA records exist (still
   schema-aligned, no fabrication).
4. **Editable pages** (about/faq/contact/privacy/terms/shipping) become
   admin-editable, DRAFT→published by owner.
5. **Exports:** domain-only vs domain+site packages, `.env.example`,
   no-secrets checklist, admin guide, DNS/email migration checklist.
6. **Tests:** unit (order model, fee math, **Svix verify**, RLS posture,
   config loader) + e2e smoke (inquiry→confirm→status). All fixtures
   DEMO-labeled.
7. **Deploy only after owner approval** (brief forbids unapproved deploys).

## 7. Explicitly NOT done (by design)
No live payment · no production email · no fabricated COA/purity/supplier data ·
no admin auth · no Supabase · no real catalog · no commits to the canonical repo
· no push · no deploy · source `peptide-connect-web/` **not deleted** (awaiting
owner cleanup authorization) · GetReta untouched.

---

## 8. B.3.2 Milestone A — Hybrid Brand Identity (Catalog + Documentation journeys)
**Status:** DONE + VERIFIED (2026-10-11)

### What changed

1. **Homepage rewrite** (`src/pages/index.astro`) — new headline "Research materials, connected to the evidence.", compact "two-ways" block (Catalog → Documentation → Request), updated lead, secondary CTA, preserved hero layout and BrandMark constellation entrance.

2. **Catalog landing** (`src/pages/catalog/index.astro`) — updated CATALOG_META (honest posture, shipping-included pricing), preserved filter IDs/data-attributes, count updated to 11 compounds / 15 variants, "Browse the catalog" heading and "shipping included" note added.

3. **ProductCard** (`src/components/ProductCard.astro`) — new hierarchy: dominant name + neutral chemical descriptor + compact spec block (Family/Form/Route/Sizes) + single clear price line (from + spread + "shipping included") + two meaningful status badges only (StatusBadge + DocumentationBadge). Variant list compacted into price row. Preserved data attributes for client-side filter.

4. **Documentation explorer** (`src/pages/documentation.astro`, replaces `coa.astro`) — route renamed `/documentation` (nav/footer updated). Honest states: `no_record` → "No record on file", `pending` → "Requested · pending lab report", `contradictory` → "Report · uncorroborated". Supplier column shows honest values ("Not linked", "Supplier A (unverified)"). "What is known" column contains honest plain-language notes. Explainer cards updated to customer-friendly language (removed internal schema terms). Search IDs/attributes preserved.

5. **Navigation rename** — "COA Explorer" → "Documentation" across nav and footer (site.ts, footerNav). Redirect `/coa` → `/documentation` via static HTML meta refresh.

6. **DocumentationBadge** (`src/components/DocumentationBadge.astro`) — new 21-line component mapping documentation state to honest badge (demo/inquire/contradictory).

7. **Design tokens** (`src/data/catalog.ts`) — new 413-line data shape with 11 compounds (including owner-added Tirzepatide 20 mg $100 / 40 mg $130) and 15 variants. Documentation taxonomy populated with honest states (`none`/`pending`/`contradictory`) and defined but unpopulated (`seller_submitted`/`manufacturer_supplied`/`lab_issued`/`independently_corroborated`). Owner prices shipping-included.

8. **App styles** (`public/styles/app.css`) — added `.badge--contradictory` dashed warn variant (background + color + border).

### Build verification

- `astro build` → **25 pages**, 0 errors.
- All pages compiled: homepage, catalog (list + 11 slugs), documentation, redirect page.
- HTML inspection confirms presence of new headline, two-ways block, catalog cards with DocumentationBadge, documentation explorer with honest states.

### Key acceptance criteria verified

- Homepage headline: "Research materials, connected to the evidence." ✓
- Two-ways block (Catalog → Documentation → Request) present and correctly linked ✓
- Catalog page: 11 compounds / 15 variants, shipping-included pricing note ✓
- Product cards: dominant name, price line (from/spread/shipping), two status badges, variants compacted ✓
- Documentation explorer: honest states, no fabricated COAs, customer-friendly language ✓
- Nav/footer rename: "COA Explorer" → "Documentation" ✓
- Redirect page at `/coa` present (meta refresh) ✓
- No console errors ✓
- No fabrication of purity/test/supplier/cert data; documentation states honest ✓

### Files changed

- `src/data/catalog.ts` (new data shape with 11 compounds, 15 variants, honest COA states)
- `src/components/DocumentationBadge.astro` (new)
- `src/components/ProductCard.astro` (rewrite)
- `src/pages/index.astro` (homepage rewrite)
- `src/pages/catalog/index.astro` (catalog landing update)
- `src/pages/documentation.astro` (new, replaces `coa.astro`)
- `src/pages/coa.astro` (redirect static page)
- `src/config/site.ts` (tagline + description + nav/footerNav rename)
- `public/styles/app.css` (add `.badge--contradictory` variant)

### Unresolved / minor

- None (M-A is complete). Milestone B pending (About/Contact/Request/Order/FAQ wording changes).

---

## 9. Hotfix — Mobile nav contrast + Share-URL origin (2026-10-12)
**Status:** DONE + VERIFIED. Bounded production-readiness repair; no redesign, no
B.3.2 design work, no Phase C.

### Defect 1 — Dark mobile navigation contrast
**Root cause:** The mobile drawer link rule inside `@media (max-width:860px)` in
`src/components/Nav.astro` hardcoded `color: var(--navy)` (a dark navy, `#102d38`).
On the drawer's dark theme surface (`--surface` = `#10333d`), that dark text was
nearly invisible — logo/theme-close/CTA used theme-aware tokens, so only the link
labels failed.
**Fix:** Changed the mobile link color to the **theme-aware** token `var(--ink)`
(navy on light, off-white on dark), and added explicit `:hover` / `:focus-visible`
(teal-strong) and `:current` (ink) states so all interactive states stay legible in
both themes. No new navigation components; keyboard/aria behavior unchanged.

### Defect 2 — Share button / canonical placeholder URL
**Root cause:** The public origin was hardcoded as the placeholder
`https://peptideconnect.example` in two places (`src/config/site.ts#url`,
`astro.config.mjs#site`). `Base.astro` derives canonical + Open Graph + Twitter +
JSON-LD from `site.url`, so every share/canonical URL inherited the placeholder.
A second bug: the `/coa` redirect page hard-coded a typo'd canonical
`https://peptide.connect/documentation` (no hyphen, wrong host).
**Fix:** Introduced a single configurable origin module
`src/config/origin.ts` (`SITE_ORIGIN`, `CONTACT_EMAIL`; reads
`process.env.PUBLIC_SITE_ORIGIN`, default `https://peptide-connect.com`).
`site.ts` now imports `SITE_ORIGIN`/`CONTACT_EMAIL` (email derived from the origin
host, so a future domain transfer never leaves a stale address); `astro.config.mjs`
reads the same env var; `/coa`'s canonical now uses `SITE_ORIGIN` via frontmatter.
Added `.env.example` documenting the override. No `localhost`/`127.0.0.1` URLs are
ever emitted for sharing; nested routes preserve their pathname.

### `.`example/typo audit
- **Production-facing (fixed):** `src/config/site.ts` (url + contact email),
   `astro.config.mjs` (site), `src/pages/coa.astro` (canonical typo).
- **Internal documentation only (left untouched):** `review/CHECKPOINT_4.md`,
   `PHASE_A.md`, `review/B3_2_PROPOSAL.md`, `review/PHASE_B1_PROGRESS.md` — these
   reference the placeholder as historical context, not a production URL.
- **Distinguished demo data:** `site.contact` email now resolves to
   `contact@peptide-connect.com` (derived), with `hours` still a labeled placeholder —
   no invented real address/mailbox.

### Build results
- `astro build` → **25 pages, 0 errors** (homepage, catalog list + 11 slugs,
   documentation, `/coa` redirect, 404, admin, about/faq/contact/privacy/terms/shipping,
   request, order).
- Grep of `dist/` for `peptideconnect.example`, `peptide.connect` (typo), `127.0.0.1`,
   `localhost` → **NONE**.

### Browser verification (harness `pc-ma-verify`, 375 × 667 @2x)
- **Light drawer @375px:** open; links navy `rgb(16,45,56)` on white — legible. Screenshot
   `review/b31/drawer-light-375.png`.
- **Dark drawer @375px:** open; links off-white `rgb(247,249,250)` on dark
   `rgb(16,51,61)` — legible. Screenshot `review/b31/drawer-dark-375.png`.
- **Theme change while open:** drawer stays open (`data-open` retained); link color
   auto-adapts between the two themes (theme-aware `--ink`).
- **Horizontal overflow:** `scrollWidth − innerWidth = 0px`.
- **Console errors:** 0 across `/`, `/catalog/`, `/catalog/ss-31/`, `/documentation/`,
   `/coa/`, `/request/`, `/faq/` (instrumented via `error`/`unhandledrejection`/
   `console.error`).
- **Exact generated share/canonical URLs (grepped from `dist/`):**
   - Home → canonical `https://peptide-connect.com`
   - `/catalog/` → `https://peptide-connect.com/catalog/`
   - `/catalog/ss-31/` → `https://peptide-connect.com/catalog/ss-31/`
   - `/documentation/` → `https://peptide-connect.com/documentation/`
   - `/coa/` redirect canonical → `https://peptide-connect.com/documentation`
   - OG/Twitter image on all pages → `https://peptide-connect.com/brand/peptide-connect-logo-full.png`

### Files changed (hotfix)
- `src/components/Nav.astro` — mobile link color → `var(--ink)`; hover/focus/current states.
- `src/config/origin.ts` — new; single configurable production origin + derived contact email.
- `src/config/site.ts` — imports `SITE_ORIGIN`/`CONTACT_EMAIL`; no placeholder.
- `astro.config.mjs` — `site` from `PUBLIC_SITE_ORIGIN` (default `peptide-connect.com`).
- `src/pages/coa.astro` — canonical now `SITE_ORIGIN`, typo fixed, frontmatter-added redirect.
- `.env.example` — new; documents `PUBLIC_SITE_ORIGIN` override + "no localhost" note.

### Remaining uncertainties
- No `@astrojs/sitemap` integration is configured, so no `sitemap.xml` is emitted; not
   in scope for this hotfix (would be a Phase C concern alongside the real deploy).
- `PUBLIC_SITE_ORIGIN` is honored only for the Astro `site`/build-time path; a deployed
   host that serves `dist/` statically would still use the baked origin (rebuild on a
   domain transfer). This matches the owner's "configurable for future transfers" ask.
- The B.3.2 **Milestone B** wording changes (About/Contact/Request/Order/FAQ, COA/Docs
   wording) remain unstarted, per the hotfix "stop after this hotfix" guardrail.