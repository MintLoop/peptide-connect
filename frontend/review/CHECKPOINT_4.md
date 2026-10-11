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