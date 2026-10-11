# Peptide Connect — Phase A Deliverable (v0.1)

**Date:** 2026-10-09 · **Author:** Menta coordinator (lead full-stack pass) · **Status:** PROPOSED — awaiting owner approval before Phase B
**Brief version:** QWEN_BUILD_BRIEF v0.1 · **Scope of this phase:** audit + research only. No code built, no external writes, no deploys, no secret changes. GetReta production and the existing `peptide-connect` pipeline were read, **not** modified.

> **Reading note on sources.** GetReta and the existing `peptide-connect` pipeline were read from disk (verified). `getreta.net` was read live (verified). `rarevbiolabs.com`, `leolab.co.uk`, `purelabpeptides.com`, `canadapeptidesupply.ca`, `aminoclub.com` patterns were pulled from search + extract (treated as **untrusted reference data**, patterns only — nothing cloned). `leonlab.pro` and `purelabpeptides.com` were **WAF-blocked (HTTP 403)** and could not be read; see Blocking Question B3. `getreta.net` and the logo assets below are **verified**; reference-site claims are **inferred**.

---

## 0. TL;DR for the owner (read this first)

1. **The single biggest issue is a name collision, not a technical one.** The repo at `Mintloop/Sites/peptide-connect/` already contains a *different product* — an LLM-driven "supplier intelligence" pipeline (`pcconnect/`, ~2,400 LOC + a 348-line pytest suite, 11 source adapters, 7 canonical JSON schemas, no git remote). The brief describes a **web commerce/catalog property** that shares the name "Peptide Connect" but has none of that code. **These are two products.** Recommendation: build the web property in a **new, separate repo** (`peptideconnect-website` — see B1) and keep the pipeline intact behind a feature flag it can later *consume* as its "COA Explorer."
2. **The existing pipeline is a gift for the "future COA Explorer."** Its `analytical.schema.json` and `dossier.schema.json` already model supplier/compound/lot/lab-report/chain-of-custody/provenance with an evidence-state vocabulary (`VERIFIED/UNVERIFIED/CONTRADICTED/...`). The brief's "future COA/lot-verification module" can be defined against this existing schema instead of reinvented — a major de-risk.
3. **GetReta is an excellent, security-hardened substrate** to *extract and generalize*, but not to *fork wholesale*: its orders backend is JSON-file-stored and single-process, its admin auth is a header-password + guess-proof URL (not real sessions, no rate limiting). The comms layer (Resend + Svix webhook signature verification, fail-safe adapters), the order-state model, the Supabase migration, and the admin console UI are all reusable and superior to starting from zero.
4. **Approved logo exists but only as 3 raster PNGs, not a vector source.** Two are the *approved* constellation (stacked + horizontal), one is the **rejected flower/hexagon** the brief says to avoid. **Phase B needs the original vector source, or we reconstruct the four-unequal-node geometry from the raster** — the latter is a fidelity risk for "precise vector SVG." See B2.
5. **No new paid services are required for MVP.** Vercel (free tier) + Supabase (free tier) + optional FastAPI/Cloud Run covers catalog, inquiry, admin, and comms. Payment is explicitly out of scope until legal/provider review.
6. **This is a regulated-adjacent domain (research peptides, "not for human consumption," possible export-control sensitivity).** The build must ship in a "research-use-only" legal posture, with every claim flagged as draft-for-owner-review and **no** fabricated COA/purity/legal data. The existing pipeline's evidence-state discipline is the right guardrail and should carry into the web layer.

---

## 1. Architecture audit

### 1.1 GetReta (the reference implementation) — *verified from disk + live site*

**Repo:** `Mintloop/Sites/getreta/` · remote `git@github.com:MintLoop/getreta.git` · clean tree · 7 commits.

**Stack**
| Layer | What / where | Notes |
|---|---|---|
| Frontend | Astro 5 + React 19 islands + Tailwind 3.4 → static `dist/` | `astro.config.mjs` sets `site: 'https://getreta.com'` (note: live domain is `getreta.net`) |
| Catalog | `src/data/catalog.ts` | TS types `Product/PriceTier/Add-on/GoPack`; `goPackItems()` computes pack totals from catalog prices = single source of truth. 8 products, 4 go-packs. |
| Order form | `src/components/ContactForm.tsx` | POSTs `/api/orders`, **mailto fallback** if API down; platform fee `PLATFORM_FEE_RATE=0.05` capped `25`; 21+ / research-only consent checkboxes; source & payment dropdowns. |
| Card | `src/components/ProductCard.tsx` | Renders blurb, pricing, dosing field. |
| Legal pages | `src/pages/{index,terms,privacy,disclaimer}.astro` | Editable content pages. |
| Seller console | `public/admin.html` | Single-file, password-gated (`sessionStorage`), printable **4×6 label**, dashboard (leads/stalled/cut). Dark UI. |
| Backend | `server/app.py` (~600 LOC, FastAPI + uvicorn) | Serves `dist/` AND a JSON order store. Endpoints below. |
| Comms | `server/comm/` (7 modules) | Resend sender + **Svix webhook signature verification** + normalized events + idempotency + audit trail. Provider-neutral, degrade-safe. |
| DB (target) | `supabase/migrations/0001_create_orders_schema.sql` | `orders/order_items/order_events`, NUMERIC money invariants, **RLS deny-by-default**, services_role server path. |
| Tickets | `registry/tickets.yaml` + `tickets/` buckets | Backlog/active/done/archive; authoritative status. |

**Backend API** (`server/app.py`)
| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /api/orders` | none | create order → `{ok,id,code}`; 6-char non-guessable status code (`_short_code`, unambiguous alphabet); anti-loss mirror (best-effort, never blocks); status `new`. |
| `GET /api/admin` | `x-admin-pass` | list orders (newest first), `count`. |
| `PATCH /api/orders/{id}` | `x-admin-pass` | set status (`new/in-progress/shipped/fulfilled/cancelled`), timestamps it, mirrors. |
| `GET /api/status/{code}` | none | **public, PII-free** status lookup (masked id, progress steps, next) — the customer tracking flow. |
| `GET /api/summary` | `x-admin-pass` | dashboard metrics: leads, active, shipped, stalled (`STALL_HOURS` default 48), revenue by source/product/month/day, "your cut" (`CUT_PCT/CUT_FLAT/CUT_BASE`). |
| `GET /api/export.csv` | `x-admin-pass` | flat CSV of all orders incl. line items + cut. |
| `GET /api/health` | none | liveness. |
| `/<console-token>` | `x-admin-pass` | serve `admin.html` at a random 24-char filename so `/admin.html` is not guessable. |

**Order data model (JSON today, Supabase migration target)** — `id`, `code`, `created`, `name`, `phone`, `email`, `source`, `street/city/state/zip`, `items[]` (`product/size/qty/unit/pack`), `addons[]`, `payment`, `notes`, `status`, `total`. Supabase target adds `fulfillment_mode (ship/pickup)`, `shipping_*`, `tracking_number`, NUMERIC `subtotal/shipping_fee/platform_fee/customer_total/seller_amount` with reconciliation CHECKs, `payment_status`, append-only `order_events` lifecycle.

**Comms layer (`server/comm/`) — the strongest reusable asset.** `EmailSender` abstract boundary → `ResendEmailSender` (stdlib `urllib`, no new dep, modeled on the repo's fail-safe mirror pattern: **a send failure returns a failed `SendOutcome`, never raises, never masquerades as success**). `svix_verify.py` re-implements Resend's Svix HMAC-SHA256 verification over the **raw body** with constant-time compare + replay tolerance — correct and self-contained. `handlers.py` dedupes on provider message id and records only metadata (never inbound content/attachments). `repository.py` is an in-memory seam that T-103's Supabase table is meant to back. `config.py` loads `RESEND_*` env vars, degrade-safe (absent key → `NOT_CONFIGURED`, no crash).

**Security posture (verified) — what's good and what must change for PC**
Good: timing-safe admin header compare (`hmac.compare_digest`); PII-free public status lookup; anti-loss mirror; fail-safe comms; RLS deny-by-default + service_role in the migration; address "gate" (`ADDRESS_CONFIRMED=false` holds placeholder address on labels).
**Gaps the brief explicitly requires PC to close:**
- Admin auth is a **shared secret in a header + a guess-proof URL filename** — not real sessions, not per-user, **no rate limiting, no bot protection, no CSRF, no access logs**. Brief §"Architecture and security" requires server-enforced auth **and** authz, rate limiting, validation, bot protection, PII minimization, webhook authenticity, access logs, backups.
- **Storage is a JSON file** — not concurrent-safe, single-process, no schema enforcement at write time.
- `data/orders.json` on disk contains **real PII** (one 2026-09-17 test order, full name/phone/email/address).
- Front-end fee (5% in `ContactForm`) is **displayed but not stored** in the order payload; backend "cut" is a separate 0%-default system — a known discrepancy (audit doc flags commit-msg "8%" vs code "5%"). PC should make fee handling single-sourced and stored.

**Deployment:** no `vercel.json`, no deploy scripts in-repo; supports Vercel/standalone/VPS by shape. Live `getreta.net` (verified) = the storefront rendered above: "Contact-only catalog · no checkout," per-vial pricing + durations, go-packs, 1–3-day US shipping $11 / Anaheim pickup, 21+ consent, "For laboratory research use only."

### 1.2 The existing `peptide-connect` repo — *verified from disk; a name collision*

**Repo:** `Mintloop/Sites/peptide-connect/` · **no git remote** · clean tree · 2 commits (`f27cac8`, `785c67c`). This is **not** the web property. It is a **deterministic + LLM supplier-intelligence pipeline** (`AGENTS_BRIEF.md`, `RUNBOOK.md`, `contracts/`, `MASTER_PACK.md` = a 792-line evidence-rules contract).

**What it is (~2,400 LOC + 348-line `tests/test_v0.py`, 11 adapters, 7 schemas):**
- `pcconnect/pipeline.py` (483) orchestrates a 7-tier model routing flow (Tier 0 deterministic → 1 `qwen27b` extraction → 1V `qwen3-vl` visual → 1E `bge-m3` retrieval → OCR `glm-ocr` → 2 `granite30b` skeptic → 3 `qwen3.8:125b` adjudicator) over a 528-record synthetic fixture set labeled "synthetic."
- `pcconnect/schemas/` = **7 canonical JSON Schemas** (`analytical`, `dossier`, `observation`, `lineage`, `extraction`, `adjudication`, `envelope`) with an `evidence-state` vocabulary (`VERIFIED/LIKELY/POSSIBLE/UNVERIFIED/CONTRADICTED/UNRESOLVED/INSUFFICIENT_EVIDENCE`) and `provenance` enum (`VENDOR_COA/INDEPENDENTLY_SOURCED/PC_CONTROLLED_PURCHASE/...`).
- `pcconnect/moa/` = a "Model-of-Agreement" escalation panel (Router → Resolver → Skeptic → Adjudicator) that opens only on material unresolved issues; "agreement is not evidence."
- Hard rules (MASTER_PACK): never convert a claim into a fact; preserve `source_id` on every assertion; never fabricate lot numbers / report IDs / entities / dates; "absence of evidence ≠ failure of evidence."

**Why it matters:** (a) It is the **natural home** of the brief's "future COA/lot-verification module" — the `analytical`/`dossier`/`lineage` schemas already define supplier/compound/lot/lab-report/chain-of-custody/data-evidence **provenance-backed and anti-fabrication**. PC-web's COA Explorer should be **feature-flagged and schema-aligned to these** rather than designed fresh. (b) It means "Peptide Connect" is potentially **two products sharing a name, a brand, and a domain namespace** — the exact separation the brief demands for a transferable/sellable asset. This is the top blocking question (B1).

### 1.3 Reference sites — *inferred (patterns only; not cloned)*

- **getreta.net (verified live):** contact-only catalog, per-vial pricing + "typical duration," go-packs, consent-gated inquiry, $11 / 1–3-day US ship / Anaheim pickup, research-use-only framing. **This is the direct analogue** of what PC-web is: same owner, same posture, higher polish. Most reuse flows from here.
- **rarevbiolabs.com (extracted, untrusted):** 21-product catalog, "login to see prices," per-product strength variants + "Full Kit / Single Vial," explicit "Research Use Only / not for human consumption," **no published COAs** (an aggregator flagged this). Pattern takeaways: variant/strength selectors, configurable price visibility ("login to see prices"), research-disclaimer everywhere.
- **leolab.co.uk / leolab.co.za (search, untrusted; `leonlab.pro` = 403 WAF, **not** a verifiable peptide site):** 99%-purity marketing, "out of stock" states, large catalog, reconstitution instructions, "3rd-party tested" claims. Pattern takeaways: availability states, reconstitution/how-to content, "out of stock" UX. **Caution:** heavy marketing/purity claims — **do not copy**; PC stays "no invented purity/legal claims."
- **purelabpeptides.com / canadapeptidesupply.ca / aminoclub.com (search, untrusted; purelabpeptides 403 WAF):** the **COA-explorer pattern** the brief anticipates — per-lot COA cards (product + lot + purity + lab + date + PDF), a searchable COA library by compound/lot number, an 8-assay panel (purity HPLC, net content, identity, appearance, fentanyl screen, heavy metals ICP-MS, sterility PCR, endotoxin USP<85>), ISO 17025 / ICH Q6B references, "a different lot does not verify your batch" honesty. **This is the template PC-web's future COA Explorer should honor in shape, not copy in content.**
- **chemverify / Janoshik Analytics (search, untrusted):** independent batch-verification pattern (enter lot → retrieve results). Reinforces "verification, not self-certification."

**Net reference signal:** the domain's *differentiator* is **provenance + verification honesty** (lot-level COA, independent vs self-reported, "what's unknown"), not price/purity puffery. PC-web should lean into that; it's also the most defensible legal posture.

### 1.4 What the brief requires that GetReta does *not* yet provide

| Requirement (brief) | GetReta today | PC delta |
|---|---|---|
| Catalog: search, filters, category tags, variant/strength selectors | Static cards, no client search/filter | Build catalog view + filtering |
| Product details: editable specs, COA links only when records exist | No per-product detail page | New PDP + COA gate |
| Inquiry/request-order + optional cart + review + human confirmation + **tracking code masked id + status** | Has POST + `code` + public status; **no cart/review confirmation step** | Add cart/review/confirm; keep status flow |
| Secure admin: product CRUD, requests queue, status transitions, stalled orders, CSV export, **editable site/company/contact/policy config + basic audit logs** | Has orders queue/status/stalled/CSV; **no product CRUD, no site-config editor, minimal audit** | Add product CRUD + config editor + audit log |
| COA Explorer: feature-flagged schema, honest empty states, **never fabricate** | Absent, but schemas exist in pipeline | Build behind flag, schema-aligned, empty-safe |
| Editable pages (About/FAQ/Contact/Privacy/Terms/Shipping/Returns), **flagged as drafts** | Static legal pages | Editable + DRAFT banners |
| Server-enforced auth/authz, rate limiting, validation, bot protection, PII minimization, webhook authenticity, access logs, backups | Header secret + token + mirror + Svix verify | Real sessions + rate limit + validation + bot check + access logs |
| Centralized brand/business config | Scattered constants (`SELLER_EMAIL` etc.) | One config object, env-driven |
| Buyer-ready export/import, standalone w/o secrets | None | Add export/import + no-secrets checklist |

---

## 2. Reuse matrix

Legend: **REUSE** = copy/adapt as-is. **EXTRACT** = generalize into a shared module. **REWRITE** = replace. **NEW** = build. **OMIT** = don't bring.

| GetReta / pipeline asset | Decision | PC treatment | Risk / note |
|---|---|---|---|
| Astro+React+Tailwind shell, `Base.astro` layout, component style | **REUSE** | Adopt as PC-web scaffold (rename brand, recolor to PC palette) | Swap favicon (vial emoji → constellation icon); swap copy. |
| `catalog.ts` data shape (`Product/PriceTier/Add-on/GoPack`, `goPackItems`) | **EXTRACT** | Generalize into a schema-driven catalog model (add: category, status `available/not_available/inquire`, per-variant, COA ref, `draft` flag). GetReta's 8 products become *examples*, not content. | Don't copy GetReta's specific products/prices (that's his business content). |
| `ContactForm.tsx` (inquiry, consent, mailto fallback, fee display) | **EXTRACT** | Generalize to a multi-step inquiry: line items → review → confirm. Keep mailto fallback. Make fee single-sourced + stored (fix GetReta's display-only bug). | Add cart + review/confirm + bot protection (hCaptcha/Turnstile). |
| `ProductCard.tsx` | **EXTRACT** | Generalize; add variant selector, status badge, "COA available" indicator (only when record exists). | — |
| `public/admin.html` (console UI: dashboard, orders, 4×6 label, status toggles) | **REUSE** (UI) / **REWRITE** (auth) | Reuse the dark-console UI shell for PC admin; **replace** client-side password/`sessionStorage` + guess-proof token with real server sessions. | This is the largest security upgrade. |
| `server/app.py` order endpoints + `_short_code` + public status + summary/CSV + mirror | **EXTRACT** | Generalize to PC's inquiry/order API; keep the good idioms; move storage to Supabase; add product-CRUD + config + audit routes. | JSON store → Postgres. |
| `server/comm/` (Resend sender, **Svix verify**, handlers, models, repository, config) | **REUSE** | Copy the comms layer near-verbatim into PC; it's provider-neutral, fail-safe, and correct. Point at PC's `RESEND_*`/`PC_*` env + Supabase-backed repository. | Highest-value reuse; keep tests. |
| `supabase/migrations/0001_create_orders_schema.sql` | **EXTRACT** | Use as the PC migration template (RLS deny-by-default, NUMERIC invariants, service_role path); add `products`, `categories`, `orders` (rename from getreta), `communications`, `coa_*`, `audit_log`, `site_config` tables with the same deny-by-default posture. | `auto_expose_new_tables` must be REVOKE'd per GetReta skill note or PII leaks to anon. |
| Pipeline `schemas/{analytical,dossier,lineage,observation}.json` | **REUSE** (schema alignment) | PC's COA Explorer is defined against these exact schemas (provenance + evidence-state + anti-fabrication). Ship empty + honest empty-states. | Schema is the contract; keep it stable. |
| Pipeline `pcconnect/*`, `contracts/`, `prompts/`, `scripts/`, `tests/test_v0.py` | **OMIT from PC-web** (keep in its own repo) | Do **not** fold the 2,400-LOC LLM pipeline into the web repo. It's a separate product. PC-web can *query* it later via a feature-flagged adapter. | Keeps products separable (brief §"clearly separable"). |
| GetReta `getreta.net` content (prices, phone, go-packs, copy) | **OMIT** | Do not copy his business content. Use as the *shape* reference only. | — |
| Reference sites (rarev/leolab/purelab/aminoclub) | **OMIT** (copy) / **inspired-by** (patterns) | Take UX patterns (variant selectors, "login to see prices," out-of-stock, COA-by-lot honesty); **never** copy imagery/CSS/wording/claims. | Brief §"Do not copy." |
| Approved constellation logo | **REUSE** (frozen) | Reconstruct as precise vector SVG from the source; 375/1440 + 16/24/32px favicons. **Not** the flower/hexagon. | Needs vector source (B2). |

---

## 3. Proposed site map

```
peptideconnect (TBD domain — see B5)
│
├── /                       Home
│     · Original hero (constellation mark; research-first positioning; NO health/dosing claims)
│     · Catalog search + quick filters (by compound family / status / price-visibility)
│     · Concise "How it works" (browse → inquire → confirm → track)
│     · Trust section — ONLY where verifiable (e.g. "COA available per lot when published"); else omitted
│     · FAQ (subset; full at /faq)
│     · Contact CTA (→ /contact)
│
├── /catalog                Catalog (search, filters, category tags)
│     · Grid + list toggle; filters: name, compound family, availability
│       (available / not available / inquire), price visibility (public/login/hidden), COA flag
│     · "Inquire" status renders a request CTA not a price
│
├── /product/:slug          Product detail
│     · Editable spec block (form, route, packaging, storage — as data, not claims)
│     · Variant/strength selector
│     · Availability state + request CTA
│     · "Certificate of analysis" block — links ONLY when a record exists; honest "no COA published for this lot yet" otherwise
│     · Original description (no therapeutic/dosing promises; DRAFT flag until owner review)
│
├── /request                Inquiry / request-order journey (optional cart)
│     · Cart (optional) → Review → Confirm
│     · Human confirmation (owner sees it in admin, replies; NOT auto-fulfilled)
│     · Returns a unique tracking code + masked identifier (e.g. #A3F9 → masked, no PII shown)
│     · No live payment (until legal + provider suitability assessed)
│
├── /order/:code            Public order status (masked id, no PII; reuse GetReta's `/api/status/:code`)
│
├── /coa                    COA / Lot Verification Explorer  — FEATURE-FLAGGED
│     · Search by compound / lot / supplier
│     · Cards: compound, lot, purity, lab, date, method, chain-of-custody, document link
│     · Honest empty states when none; NEVER fabricate purity/verification/legal data
│     · Schema-aligned to the pipeline's analytical/dossier/lineage schemas
│
├── /admin                  Secure admin (server-enforced session; NOT public URLs)
│     · Dashboard (leads, active, stalled, revenue, cut) — reuse GetReta console UI
│     · Product CRUD (add/edit/retire; categories; variants; COA attach)
│     · Requests queue + status transitions (new → confirmed → ready → shipped → closed; cancel)
│     · Stalled-order view; CSV export (orders + audit)
│     · Site configuration editor (name, domain, logo, contact, categories,
│       catalog visibility rules, request modes, shipping/pickup, email sender, legal entity)
│     · Audit log (who/when/what for every mutation)
│
├── /about  /faq  /contact  /privacy  /terms  /shipping  /returns   Editable pages
│     · Each carries a "DRAFT — pending owner review" banner until signed off
│
└── (config, not a page)  site_config: name, domain, logo, contact, categories,
        catalog visibility, request modes (inquire/ship/pickup), email sender, legal entity
        — one source of truth shared by build + admin; transferable.
```

**Navigation:** Home · Catalog · COA (flagged) · FAQ · Contact, footer legal (Privacy/Terms/Shipping/Returns/About) + admin link (authenticated, not in public nav).

---

## 4. MVP scope (Phase C boundary)

**In** (MVP, DEMO data only until owner replaces with real catalog):
- Static, responsive, SEO'd shell with the frozen constellation identity (horizontal/stacked/reversed/one-color/icon-only + real 16/24/32 favicons).
- Catalog (search + filters + category tags + availability states + configurable price visibility).
- Product detail (editable specs, variant selector, COA gate w/ honest empties, no claims).
- Inquiry journey: optional cart → review → confirm → human confirmation → tracking code + masked id → public `/order/:code` status.
- Admin: real **server session** auth (not header-secret), product CRUD, requests queue + status transitions + stalled, CSV export, **site-config editor**, **audit log**; 4×6 label print reused; bot protection (hCaptcha/Turnstile).
- Comms: resuse `server/comm/` (Resend + Svix verify, fail-safe) → order confirmations + admin notifications; Supabase-backed repository.
- DB: Supabase Postgres, RLS deny-by-default, service_role server path, per-site isolated project/credentials; migration + seed (DEMO) + env template.
- Auth/authz **server-enforced**; rate limiting; input validation; PII minimization; structured access logs; scheduled snapshots.
- Editable legal/company pages with **DRAFT** flags.
- Feature-flagged **COA Explorer** = schema-aligned to pipeline, **empty-safe, zero fabricated data**.
- Exports: (a) **domain-only** package, (b) **domain + website** package; `no-secrets` checklist; DNS + email migration checklist; admin guide.
- Tests: unit (order model, fee math, svix verify, RLS posture, config loader) + e2e smoke (inquiry→confirm→status); clearly **DEMO-labelled** fixtures.

**Explicitly OUT of MVP** (gated, brief-compliant): live payment (no legal + provider assessment yet); real catalog/prices/suppliers (owner enters in admin, DEMO until then); auto-fulfillment; scraping/third-party ingestion from the pipeline (feature-flagged later); marketing/open-click analytics.

---

## 5. Implementation sequence (mapped to brief's Phase B–D)

**Phase B — Identity + shell (static, responsive, no data)**
1. Recreate constellation as **precise vector SVG** (frozen; 5 variants) from the approved *source*; render real 16/24/32 PNG (native 1:1 + nearest-neighbor enlarged; light/dark); fix fused-node/disappearing-link issues at small size. *(blocked on B2 vector source)*
2. Single licensed type family + type scale, optical spacing, min-size/contrast/clear-space/color tokens → design tokens (CSS vars + Tailwind theme) in PC palette (`#102D38 / #12A89D / #EAF5F2 / #F7F9FA`).
3. Static shell: Base layout, nav/footer, 375px mobile + 1440px desktop review, semantic a11y, keyboard behavior, SEO metadata, responsive images. No content claims.

**Phase C — Data + journey + admin + tests (DEMO-labelled)**
4. Supabase project + isolation (dedicated ref, anon/auth/service_role creds, RLS deny-by-default). Migration: `products, categories, variants, orders, order_items, order_events, communications, coa_* (aligned to pipeline schemas), audit_log, site_config, admins(sessions)`. `.env.example` + migration scripts.
5. FastAPI/Cloud Run API: reuse `server/comm/`; add product-CRUD, requests→status, `GET /status/:code`, config read/write, audit log. Auth = **server sessions** (cookie, httpOnly, or Supabase Auth JWT) + per-route authz; rate limiting; `pydantic`/zod validation; bot check; PII minimization; structured access logging.
6. Frontend islands: catalog/filter, PDP/variant/COA-gate, inquiry cart→review→confirm, `/order/:code`, admin console (reuse GetReta UI), editable pages w/ DRAFT flags, COA Explorer (flagged, empty-safe).
7. Exports (domain-only / domain+site), no-secrets checklist, admin guide, DNS/email migration checklist.
8. Tests + e2e smoke; DEMO-labelled fixtures.

**Phase D — Handoff package**
9. Separate domain-only vs domain+site packages; documented ownership; DNS + email migration steps; config, export/import, admin guide, no-secrets checklist. Deploy **only after owner approval** (brief forbids unapproved deploys).

**Gates/worker model (from the GetReta skill):** per-ticket worker briefs run via the menta pipeline with `npm run build` green = truth, an adversarial different-family model reviews the diff for defects, coordinator spot-checks constants by grep (never trust self-report), **Ben merges** — nothing commits without his go. This discipline carries into PC-web.

---

## 6. Risks & mitigations (register)

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | **Name collision**: two "Peptide Connect" products (pipeline vs web) risk a tangled, un-sellable asset | HIGH | Separate repos (B1); COA Explorer schema-aligned, decoupled via feature flag; no cross-imports. |
| R2 | **Logo fidelity**: raster-only source may not reconstruct the *four unequal* nodes precisely | HIGH | Get vector source (B2); else reconstruct + pixel-diff against approved PNGs at 16/24/32 + 1440. |
| R3 | **Security downgrade if we fork GetReta as-is**: header-secret auth, JSON store, no rate limit | HIGH | Real server sessions, Supabase RLS deny-by-default, rate limit, validation, bot check, PII min, access logs (reuse Svix verify). |
| R4 | **PII leak via Supabase auto_expose** | HIGH | `REVOKE` new public tables from anon/authenticated; service_role server path only; test with a deny posture assertion. |
| R5 | **Regulatory**: research-peptide domain, "not for human/therapeutic," possible export-control sensitivity | HIGH | Research-use-only posture; all claims DRAFT; no purity/legal/dosing fabrication; owner + (flagged) legal review; COA module honest/empty-safe. |
| R6 | **Fabricated data** (COA/purity/suppliers/prices) | HIGH | DEMO-labelled fixtures only; empty-state-first; "never invent" guardrail (inherit from MASTER_PACK rules). |
| R7 | **Reference-site content copied unintentionally** | MED | Patterns-only; grep-diff a "forbidden strings" list (rarev/leolab/purelab wording) before ship. |
| R8 | **Email sender not configured** | LOW | `server/comm/` degrade-safe (`NOT_CONFIGURED`); mailto fallback on inquiry; no crash. |
| R9 | **Transferability**: secrets entangled w/ GetReta/MintLoop infra | MED | Per-site creds, isolated DB, `.env.example`, no-secrets checklist, export/import. |
| R10 | **Fleet/resource**: building may load heavy models | LOW | Serialize per Menta guard; Phase A touches no fleet. |

---

## 7. Genuinely blocking questions (need owner answer before Phase B)

> These are the only things I won't proceed past without a decision. Everything else I can resolve with sensible, clearly-labeled defaults.

- **B1 — Repo & product boundary.** The `peptide-connect/` repo already holds a *different, LLM-based* product (the supplier-intelligence pipeline). **Build the web property in a NEW repo** (I propose `Mintloop/Sites/peptideconnect-website/`, its own git + Vercel + Supabase), keep the pipeline untouched, and align the COA Explorer to its schemas via a feature flag rather than merging code. *Or* do you intend the web property to *become* the pipeline's front-end (in which case the pipeline's `pcconnect` package stays the canonical module)? **Recommendation: new repo, decoupled.** *(This is the one that changes the most downstream.)*
- **B2 — Logo vector source.** I found **3 raster PNGs** in `~/Downloads` (`image.png` = approved *stacked* constellation, `image(1).png` = approved *horizontal* constellation, `image(2).png` = the **rejected flower/hexagon** — do not use). The brief requires a *precise vector SVG* of the **four unequal nodes + intentional connections**. **Do you have the original vector source (AI/SVG/CDR) for the approved constellation?** If yes, where, and which orientation is the canonical master (stacked or horizontal)? If no, I reconstruct from the approved PNGs and verify fidelity by pixel-diff at 16/24/32/1440 — a fidelity risk I'd flag. *(Blocks the identity portion of Phase B.)*
- **B3 — "leonlab.pro" reference.** It is **WAF-blocked (403)** and does not resolve as a verifiable peptide vendor — the live peptide sites are `leolab.co.uk`, `leolab.co.za`, `leoresearchgroup.com`. **Did you mean one of those, or is `leonlab.pro` a private/internal reference I can't see?** The brief also names `rarevbiolabs.com` and `leonlab.pro`; I verified `rarevbiolabs.com` and `getreta.net` but could not read either WAF-locked site. **If `leonlab.pro` matters, please attach a screenshot** (per the brief's "request screenshots when inaccessible"). *Low impact: I can proceed on verified sources only if you confirm.*
- **B4 — Domain + legal entity + email.** For the transferable/buyer-ready package I need: **target domain** (e.g. `peptideconnect.co`? `peptide-connect.*`?), a **legal entity name** (for footer + policies + COA "issued by"), and an **inbound email + sender domain** (for Resend + webhooks). Placeholders are fine to stub, but I need the *names* to avoid hardcoding GetReta's (`getreta.net`, its phone, its `orders@/support@`).
- **B5 — Auth model preference.** Server sessions via **cookie auth** vs **Supabase Auth (JWT/email-magic-link)** vs minimal **API-key for admin**? **Recommend cookie sessions** (simple, server-enforced, no account sprawl) unless you want password-based admin logins (Supabase Auth).
- **B6 — Payment posture confirmation.** Confirm: **no live payment in MVP** (inquiry → human confirmation only). And if a buyer later wants checkout, is **Stripe** the intended provider? (Assessment only; no integration now.)
- **B7 — Brand config ownership.** Who edits the site-config (name/logo/contact/policies/catalog visibility): **you in the admin panel, or via a config file?** Recommendation: **both** — admin panel writes to `site_config` (single source of truth), with an `.env`/migration for infra-level settings (domain, creds, sender). Confirm.
- **B8 — Catalog starter content.** Should the MVP ship with a **DEMO catalog** (clearly labelled, e.g. a hand of common research peptides with `inquire` status, no real prices) so the site is demonstrable, or an **empty catalog with only the empty states**? Recommendation: **small DEMO set, labelled DEMO**, replaced by you in admin. Confirm.
- **B9 — Admin account provisioning.** How is the **first admin** created (env-seeded on first boot vs a one-time setup route vs Supabase Auth manual)? Recommendation: **env-seeded first admin on boot** + audit log of the seed. Confirm.

---

## 8. What I'm deliberately NOT doing in Phase A (brief compliance)

- No code built, no deploys, no purchases, no external writes, no secret/API/DNS/email changes.
- GetReta production **read-only** (verified clean tree; not touched). Existing `peptide-connect` pipeline **not modified**.
- No fabricated catalog, suppliers, prices, COA results, purity, or legal claims.
- No cloning of any reference site's imagery/CSS/wording (patterns only).
- This doc created in a **new location** (`Mintloop/Sites/peptide-connect-web/`) so neither existing repo is dirtied; it can become the web repo in B1 or be moved.

---

**Next step pending your answers to B1–B9 (minimum: B1, B2, B3, B4).** On approval I begin **Phase B** with the identity + static shell. I've left everything as a **proposal** — nothing is committed, deployed, or written into production or the existing repos.
