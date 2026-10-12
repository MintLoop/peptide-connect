# Peptide Connect — B.3.2 Proposal: Scientific Editorial + Hybrid Brand Identity

**Status:** PROPOSAL — awaiting owner approval. **No implementation yet.**
**Date:** 2026-10-11 · **Repo:** `peptide-connect/`, frontend at `frontend/` · HEAD `15a84de` "first workable demo"
**Constraint:** B.3.1 (brand rendering, light/dark, accessible toggle, Molecular Signal) is complete and verified — preserved untouched. `pcconnect/` Python pipeline is a future data source only — **not** refactored, integrated, or exposed here. No payment/backend. No deploy/push.

---

## 1. Positioning (from the strategic amendment)

Identity becomes a **hybrid**: a research-materials **storefront** supported by an **evidence / supplier-intelligence platform** — not exclusively one or the other.

- **Journey 1 — Catalog:** discover materials → review product info → submit an inquiry. *(primary commercial action)*
- **Journey 2 — Evidence:** explore compounds, suppliers, lots, and available analytical documentation (may include records **outside** the store's own inventory).

**Brand message (preferred, used as the hero headline + tagline):**
> **Research materials, connected to the evidence.**

**Supporting copy:**
> Explore research materials, examine available analytical documentation, and trace the evidence behind supplier and lot claims.

The catalog stays the primary CTA; the evidence journey is presented as a first-class, credible feature — not marginalized, and not the whole identity. Internal terms (schema names, pipeline paths, "Phase C") never appear in public copy.

---

## 2. Recommended homepage copy (primary CTA = Catalog)

| Element | Before | After (proposed) |
|---|---|---|
| Eyebrow | "Evidence-first · Research peptide catalog" | `Research materials · Evidence-connected` |
| Headline | "A transparent catalog for the research-peptide market." | **Research materials, connected to the evidence.** |
| Lead | (3-line "turns scattered lab reports…") | **Explore research materials, examine available analytical documentation, and trace the evidence behind supplier and lot claims.** |
| Primary CTA | "Browse catalog" | **Browse a catalog** |
| Secondary CTA | "COA Explorer" | **Explore documentation** → `/documentation` |
| Demo note | "DEMO BUILD — no real products, prices…" | Reworded to fit real-catalog posture (see Decision D1) |

**Two-journey framing:** a compact, non-decorative block sits between hero and "how requests work," stating the two ways to use the site (find & request materials / trace the evidence), each linking to its journey. No new gradients, particles, glass, or molecule art. The frozen constellation remains the sole hero focal point; only its surrounding spacing/typography is refined.

**Spacing/typography:** establish a small, repeatable vertical rhythm (section block = eyebrow → title → lead → content with fixed `--space-*` gaps); tighten the oversized intro→first-section gaps flagged in §9 while keeping deliberate whitespace between sections. Default theme **DARK** per amendment; light mode fully retained.

---

## 3. Recommended navigation (two journeys, minimal disruption)

Current (7): `Catalog · COA Explorer · Request · Order status · FAQ · About · Contact`

Proposed (7, one rename + one optional regroup):
`Catalog · Documentation · Request · Order status · FAQ · About · Contact`

- **`COA Explorer` → `Documentation`** (`/documentation` = current `/coa`): the broader **evidence journey** entry point (compounds, lots, suppliers, COAs). Route keeps working; only the public-facing label/section broadens.
- Optional (if you prefer): visually cluster into two runs — **transact** (`Catalog · Request · Order status`) and **trust/info** (`Documentation · FAQ · About · Contact`) — via a subtle divider, no extra nesting.

Protected: the theme toggle, hamburger/drawer, focus behavior, and BrandMark auto swap are **not** altered.

---

## 4. Catalog + product card refinement (Milestone A)

- **Data (Decision D1):** populate the catalog with the owner-provided list (**11 compounds, 15 variants** — incl. the owner-added **Tirzepatide** 20 mg $100 · 40 mg $130, **shipping-included** prices), replacing the 4 DEMO placeholders:

  | Compound | Variants · price (shipping incl.) |
  |---|---|
  | SS-31 | 10 mg **$85** · 50 mg **$245** |
  | 5-Amino-1MQ | 10 mg **$50** · 50 mg **$80** |
  | NAD+ | 1,000 mg **$75** |
  | Tirzepatide | 20 mg **$100** · 40 mg **$130** |
  | Retatrutide | 20 mg **$125** · 40 mg **$150** |
  | MOTS-c | 20 mg **$95** |
  | KLOW-80 | 80 mg **$180** |
  | Selank | 10 mg **$60** |
  | Semax | 10 mg **$60** |
  | SLU-PP-332 | 5 mg **$90** |
  | Wolverine (BPC-157 + TB-500) | 10 mg + 10 mg **$135** |

- **Product card** — stronger name hierarchy (name dominant), a consistent spec block (family · form · route · size), a single clear **price** line ("$85 · shipping included"), and an availability status pill. **Reduce pills:** keep only meaningful states (availability, and one "documentation status"); drop variant pills in favor of a tidy variant/price list. "Request" CTA becomes obvious and primary; "View details" secondary. Proportions consistent across the grid.
- **Truthfulness (non-negotiable):**
  - COAs / evidence for every item remain **honest empty states** ("no independent COA yet" / "requested — pending") — **no fabricated purity, testing, supplier, or certification.**
  - No live payment/checkout; prices are shown as catalog (shipping included) but the action stays an **inquiry**.
  - Real compound names are used as **research materials only** — no clinical/effectiveness/medicinal claims; research-use-only disclaimers retained everywhere.

*(Interpretation flag: the amendment's price list supersedes the earlier "no real products, prices" placeholder posture. If you instead want the catalog to stay 4 DEMO placeholders and defer real data to Phase C, pick that in Decision D1.)*

---

## 5. Evidence / COA experience (Milestone B) — 5 documentation types, honestly labeled

Refine the COA Explorer into a distinctive evidence feature that **distinguishes without implying universal verification**. Introduce a source/state taxonomy and a customer-readable legend; all DEMO rows use honest states (nothing "verified"); the pipeline is *not* integrated.

| Documentation type (source) | Customer label | DEMO state shown |
|---|---|---|
| Seller-provided | "Seller-submitted" | available (clearly not independent) / none |
| Manufacturer-provided | "Manufacturer-supplied" | none / pending |
| Laboratory-issued | "Lab-issued COA" | none / pending |
| Independently authenticated / corroborated | "Independently corroborated" | none yet — explicitly "not yet obtained" |
| Missing / pending / contradictory | "Not on record / pending / conflicting" | the honest empty + "conflicting" state |

- Public labels use plain language (no `VENDOR_COA`/`INDEPENDENTLY_SOURCED` jargon).
- A short legend explains each type and states plainly that **a record's absence is not a pass** and that **not every report is independently verified.**
- The explorer can surface **lots/suppliers/compounds outside the store's own catalog** (Journey 2's "records unrelated to inventory").
- Product-detail COA gate wording updated to reference the evidence states honestly.

---

## 6. Secondary pages (Milestone B) — engineering language → plain demo-state

- **About:** rewritten around — what PC provides, why documentation transparency matters, how catalog + inquiry work, and the distinction between *available evidence* and *unknown information*. Not a certification authority; no invented founder/team/lab/address/partnership.
- **Contact:** "Resend + Svix webhooks" → "Contact requests are not yet enabled in this demonstration." Keep the email/research notices.
- **Request / Order status:** "In Phase C …" phrasing → "This build is a frontend demonstration. No live order or payment is processed." Keep the journey stepper and consent gates.
- **FAQ:** plain, honest demo-state answers; add two-journey + evidence-type Q's.
- **DemoBanner / EditPage:** reword to the real-catalog posture (illustrative catalog, no live orders/COAs).

---

## 7. Protected (will NOT be modified in behavior)

Approved brand geometry · SVG generation · BrandMark theme-switching (B.3.1) · theme persistence · sun/moon a11y · **Molecular Signal animation** (B.3.1) · responsive nav/drawer · catalog filtering behavior · request/order demo behavior · COA evidence-state logic · the **`pcconnect/` Python pipeline** (future source only). Shared CSS changes are allowed only where they don't break the above.

---

## 8. Exact files likely to change

**Milestone A — homepage, catalog, shared tokens/components**
- `src/config/site.ts` — hybrid tagline/description; nav rename (`COA Explorer`→`Documentation`); default theme dark
- `src/pages/index.astro` — new headline/copy, two-journey block, "Explore documentation" CTA, hero spacing/typography
- `src/data/catalog.ts` — 11 real compounds (15 variants, incl. Tirzepatide) + shipping-incl. prices; evidence-state taxonomy; honest DEMO COAs/suppliers
- `src/components/ProductCard.astro` — hierarchy, price line, fewer/meaningful pills, proportions
- `src/pages/catalog/index.astro` — filter UX, grid proportions, spacing
- `src/components/StatusBadge.astro` (+ a small documentation-status badge)
- `public/styles/tokens.css` — repeatable spacing rhythm (brand core **frozen**, no motion change)
- `public/styles/app.css` — buttons/cards/section-gap/badge/nav consistency (non-breaking)
- `src/components/Nav.astro` / `Footer.astro` / `DemoBanner.astro` / `PageHeader.astro` — label/copy only

**Milestone B — about, contact, request, order, faq, documentation wording**
- `src/pages/about.astro` — full rewrite
- `src/pages/contact.astro` · `request.astro` · `order.astro` · `faq.astro` — plain demo-state copy
- `src/pages/coa.astro` (route `/documentation`) — 5-type evidence taxonomy + legend + customer labels
- `src/pages/catalog/[slug].astro` — COA/evidence gating wording
- `src/components/EditPage.astro` — draft-flag wording
- `src/config/site.ts` — legal-entity note

---

## 9. Process & verification (per §11–§12)

Approve → **Milestone A** (build + verify) → then **Milestone B**. After each: production build; targeted browser checks in **dark + light** at **375 / 768 / 1440** covering nav, filtering, demo inquiry, theme persistence, BrandMark selection, constellation (unchanged), no horizontal overflow, readable notices/status labels. B.3.1 re-confirmed intact at the end. No deploy/push/new repo/payment/Phase C.
