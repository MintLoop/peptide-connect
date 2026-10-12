// src/data/catalog.ts
// -----------------------------------------------------------------------------
// CATALOG DATA (B.3.2 — hybrid storefront + evidence posture).
//
// Owner-supplied catalog (B.3.2 amendment): real compound names + owner-set
// prices (shipping included) + neutral research context. This supersedes the
// earlier all-placeholder posture. Truthfulness is preserved by keeping every
// evidence / COA state HONEST — no fabricated purity, testing, supplier
// identity, or certification. The pipeline stays "no record / pending /
// contradictory", so the catalog never implies a verified pass.
//
// The Python `pcconnect/` supplier-intelligence pipeline is a FUTURE data
// source only — it is NOT imported, integrated, or surfaced here.
// -----------------------------------------------------------------------------

import type { AvailabilityStatus } from '../config/site';

/** Documentation / evidence states. Only HONEST states are populated in this
 *  build: `none`, `pending`, and `contradictory`. The remaining three exist for
 *  the B.3.2 evidence taxonomy and are intentionally left unpopulated so we
 *   never fabricate a "verified"/"independently authenticated" result. See
 *   src/pages/documentation.astro. */
export type DocumentationState =
    | 'none'
    | 'pending'
    | 'contradictory'
    | 'seller_submitted'
    | 'manufacturer_supplied'
    | 'lab_issued'
    | 'corroborated'
    | 'independently_authenticated';

export interface ProductVariant {
   id: string;
   label: string;           // e.g. "10 mg"
   price: number;           // owner-set price, USD, shipping included
   status: 'active' | 'coming_soon';
}

export interface Product {
   slug: string;
   name: string;
   compound: string;        // common research name + a neutral chemical descriptor
   family: string;          // chemical-class grouping for the family filter
   route: string;           // research administration context (never a "how to take")
   form: string;            // physical form — "lyophilized powder", "powder", …
   status: AvailabilityStatus;
   documentation: DocumentationState; // honest evidence state (mostly 'none')
   coaAvailable: boolean;    // true only when a real COA record exists — always false
   description: string;
   draftFlag: boolean;
   variants: ProductVariant[];
   tags: string[];          // filterable tags
}

/** DEMO suppliers — no real company names or addresses. */
export interface DemoSupplier {
   id: string;
   name: string;            // placeholder
   region: string;
   evidenceLevel: 'none' | 'unverified' | 'inquiry_only';
   note: string;
}

export const DEMO_SUPPLIERS: DemoSupplier[] = [
   {
    id: 'demo-sup-001',
    name: 'Supplier A (unverified)',
    region: 'Not listed',
    evidenceLevel: 'inquiry_only',
    note: 'No COA on record; no lot traceability. Inquiry only.',
     },
    {
    id: 'demo-sup-002',
    name: 'Supplier B (unverified)',
    region: 'Not listed',
    evidenceLevel: 'none',
    note: 'No published evidence or COA. No lab report on file.',
     },
];

/** HONEST evidence ledger — every row is an empty / pending / contradictory
 *  state. No purity, lab, lot, or date is invented; `corroborated` /
 *   `lab_issued` are never populated so no independent pass is implied. */
export interface DemoCoaRecord {
   compound: string;        // matches a catalog compound, lot, or supplier name
   lotNumber: string | null;
   supplier: string | null;
   date: string | null;
   source: 'seller' | 'manufacturer' | 'lab' | 'independent' | 'none';
   status: 'no_record' | 'pending' | 'contradictory';
   note: string;            // honest empty-state text
}

export const DEMO_COA: DemoCoaRecord[] = [
   {
    compound: 'SS-31',
    lotNumber: null,
    supplier: 'Not linked',
    date: null,
    source: 'none',
    status: 'no_record',
    note: 'No certificate on file for this lot yet. Absence is not a pass.',
     },
    {
    compound: 'Retatrutide',
    lotNumber: null,
    supplier: 'Supplier A (unverified)',
    date: null,
    source: 'seller',
    status: 'pending',
    note: 'A seller-submitted COA was requested from an unverified supplier. Awaiting a lab report; no results on file.',
     },
    {
    compound: 'SLU-PP-332',
    lotNumber: null,
    supplier: 'Not linked',
    date: '2026-09',
    source: 'seller',
    status: 'contradictory',
    note: 'A seller-submitted report conflicts with another entry on file. Not independently corroborated.',
     },
    {
    compound: 'Tirzepatide',
    lotNumber: null,
    supplier: 'Not linked',
    date: null,
    source: 'none',
    status: 'no_record',
    note: 'No certificate on file. A future lot would need its own independent verification.',
     },
];

export const PRODUCTS: Product[] = [
   {
    slug: 'ss-31',
    name: 'SS-31',
    compound: 'SS-31 · 31-residue synthetic peptide',
    family: 'Peptide',
   route: 'Subcutaneous (research context)',
    form: 'Lyophilized powder',
    status: 'available',
    documentation: 'none',
    coaAvailable: false,
    description:
      'A 31-residue synthetic peptide used as a research material. Catalog ' +
      'entry for provenance and inquiry only — no purity, potency, or clinical ' +
      'claims are implied. For laboratory research use only. Not for human or ' +
      'veterinary consumption.',
    draftFlag: true,
    variants: [
        { id: 'ss-31-10', label: '10 mg', price: 85, status: 'active' },
        { id: 'ss-31-50', label: '50 mg', price: 245, status: 'active' },
      ],
    tags: ['peptide', 'research', 'available'],
     },
   {
    slug: '5-amino-1mq',
    name: '5-Amino-1MQ',
    compound: '5-Amino-1MQ · A1 adenosine-receptor agonist',
    family: 'Small molecule',
   route: 'Oral (research context)',
    form: 'Lyophilized powder',
    status: 'available',
    documentation: 'pending',
    coaAvailable: false,
    description:
      'A small-molecule A1 adenosine-receptor agonist examined as a research ' +
      'material. Catalog entry for provenance and inquiry only — no purity, ' +
      'potency, or clinical claims. For laboratory research use only. Not for ' +
      'human or veterinary consumption.',
    draftFlag: true,
    variants: [
        { id: '5amt-10', label: '10 mg', price: 50, status: 'active' },
        { id: '5amt-50', label: '50 mg', price: 80, status: 'active' },
      ],
    tags: ['small-molecule', 'research', 'available'],
     },
   {
    slug: 'nad-plus',
    name: 'NAD+',
    compound: 'NAD+ · nicotinamide adenine dinucleotide',
    family: 'Coenzyme',
   route: 'Oral or injectable (research context)',
    form: 'Powder',
    status: 'available',
    documentation: 'none',
    coaAvailable: false,
    description:
      'Nicotinamide adenine dinucleotide (NAD+), a coenzyme examined in ' +
      'research. Catalog entry for provenance and inquiry only — no clinical ' +
      'or safety claims. For laboratory research use only. Not for human or ' +
      'veterinary consumption.',
    draftFlag: true,
    variants: [
        { id: 'nad-1000', label: '1,000 mg', price: 75, status: 'active' },
      ],
    tags: ['coenzyme', 'research', 'available'],
     },
    {
    slug: 'tirzepatide',
    name: 'Tirzepatide',
    compound: 'Tirzepatide · GIP / GLP-1 analog',
    family: 'Peptide',
   route: 'Subcutaneous (research context)',
    form: 'Lyophilized powder',
    status: 'inquire',
    documentation: 'none',
    coaAvailable: false,
    description:
      'A dual GIP / GLP-1 analog examined in research. Catalog entry for ' +
      'inquiry only — no clinical or safety claims. For laboratory research ' +
      'use only. Not for human or veterinary consumption.',
    draftFlag: true,
    variants: [
        { id: 'tira-20', label: '20 mg', price: 100, status: 'active' },
        { id: 'tira-40', label: '40 mg', price: 130, status: 'active' },
      ],
    tags: ['peptide', 'incretin', 'research'],
     },
    {
    slug: 'retatrutide',
    name: 'Retatrutide',
    compound: 'Retatrutide · GCG / GLP-1 / GIP analog',
    family: 'Peptide',
   route: 'Subcutaneous (research context)',
    form: 'Lyophilized powder',
    status: 'inquire',
    documentation: 'pending',
    coaAvailable: false,
    description:
      'A triple GCG / GLP-1 / GIP analog examined in research. Catalog entry ' +
      'for inquiry only — no clinical or safety claims. For laboratory ' +
      'research use only. Not for human or veterinary consumption.',
    draftFlag: true,
    variants: [
        { id: 'ret-20', label: '20 mg', price: 125, status: 'active' },
        { id: 'ret-40', label: '40 mg', price: 150, status: 'active' },
      ],
    tags: ['peptide', 'incretin', 'research'],
     },
    {
    slug: 'mots-c',
    name: 'MOTS-c',
    compound: 'MOTS-c · mtDNA-encoded secreted factor',
    family: 'Peptide',
   route: 'Subcutaneous (research context)',
    form: 'Lyophilized powder',
    status: 'available',
    documentation: 'none',
    coaAvailable: false,
    description:
      'An mtDNA-encoded secreted factor examined in research. Catalog entry ' +
      'for provenance and inquiry only — no clinical claims. For laboratory ' +
      'research use only. Not for human or veterinary consumption.',
    draftFlag: true,
    variants: [
        { id: 'mots-20', label: '20 mg', price: 95, status: 'active' },
      ],
    tags: ['peptide', 'research', 'available'],
     },
    {
    slug: 'klow-80',
    name: 'KLOW-80',
    compound: 'KLOW-80 · peptide mixture',
    family: 'Peptide',
   route: 'Subcutaneous (research context)',
    form: 'Lyophilized powder',
    status: 'available',
    documentation: 'none',
    coaAvailable: false,
    description:
      'An amino-acid-rich peptide mixture examined as a research material. ' +
      'Catalog entry for provenance and inquiry only — no clinical claims. For ' +
      'laboratory research use only. Not for human or veterinary consumption.',
    draftFlag: true,
    variants: [
        { id: 'klow-80', label: '80 mg', price: 180, status: 'active' },
      ],
    tags: ['peptide', 'research', 'available'],
     },
    {
    slug: 'selank',
    name: 'Selank',
    compound: 'Selank · synthetic peptide',
    family: 'Peptide',
   route: 'Oral (research context)',
    form: 'Lyophilized powder',
    status: 'available',
    documentation: 'none',
    coaAvailable: false,
    description:
      'A synthetic peptide examined as a research material. Catalog entry for ' +
      'provenance and inquiry only — no clinical claims. For laboratory ' +
      'research use only. Not for human or veterinary consumption.',
    draftFlag: true,
    variants: [
        { id: 'selank-10', label: '10 mg', price: 60, status: 'active' },
      ],
    tags: ['peptide', 'research', 'available'],
     },
   {
    slug: 'semex',
    name: 'Semax',
    compound: 'Semax · synthetic peptide',
    family: 'Peptide',
   route: 'Subcutaneous (research context)',
    form: 'Lyophilized powder',
    status: 'available',
    documentation: 'none',
    coaAvailable: false,
    description:
      'A synthetic peptide examined in research. Catalog entry for provenance ' +
      'and inquiry only — no clinical claims. For laboratory research use ' +
      'only. Not for human or veterinary consumption.',
    draftFlag: true,
    variants: [
        { id: 'semex-10', label: '10 mg', price: 60, status: 'active' },
      ],
    tags: ['peptide', 'research', 'available'],
     },
    {
    slug: 'slu-pp-332',
    name: 'SLU-PP-332',
    compound: 'SLU-PP-332 · synthetic peptide',
    family: 'Peptide',
   route: 'Subcutaneous (research context)',
    form: 'Lyophilized powder',
    status: 'inquire',
    documentation: 'pending',
    coaAvailable: false,
    description:
      'A synthetic peptide examined in research. Catalog entry for inquiry ' +
      'only — no clinical claims. For laboratory research use only. Not for ' +
      'human or veterinary consumption.',
    draftFlag: true,
    variants: [
        { id: 'slupp-5', label: '5 mg', price: 90, status: 'active' },
      ],
    tags: ['peptide', 'research'],
     },
   {
    slug: 'wolverine',
    name: 'Wolverine (BPC-157 + TB-500)',
    compound: 'Wolverine · BPC-157 + TB-500 blend',
    family: 'Peptide',
   route: 'Subcutaneous blend (research context)',
    form: '2 × lyophilized powder (10 mg + 10 mg)',
    status: 'inquire',
    documentation: 'none',
    coaAvailable: false,
    description:
      'A combined BPC-157 + TB-500 research blend, shipped as two lyophilized ' +
      'powders. Catalog entry for inquiry only — no clinical claims. For ' +
      'laboratory research use only. Not for human or veterinary consumption.',
    draftFlag: true,
    variants: [
        { id: 'wol-10-10', label: '10 mg + 10 mg', price: 135, status: 'active' },
      ],
    tags: ['peptide', 'research'],
     },
];

// Helper: look up a product by slug.
export function findProduct(slug: string): Product | undefined {
   return PRODUCTS.find(p => p.slug === slug);
}

// Helper: list all filterable tags.
export function allTags(): string[] {
   return Array.from(new Set(PRODUCTS.flatMap(p => p.tags))).sort();
}

// Helper: list all compound families.
export function allFamilies(): string[] {
   return Array.from(new Set(PRODUCTS.map(p => p.family))).sort();
}

// Helper: owner-set price range across all variants of a product.
export function priceRange(product: Product): { min: number; max: number } {
   const prices = product.variants.map(v => v.price);
   return { min: Math.min(...prices), max: Math.max(...prices) };
}

// Customer-understandable label for each documentation / evidence state.
const DOC_LABELS: Record<DocumentationState, string> = {
   none: 'No certificate on record',
   pending: 'Requested · pending lab report',
   contradictory: 'Report on file · uncorroborated',
   seller_submitted: 'Seller-submitted · not independent',
   manufacturer_supplied: 'Manufacturer-supplied',
   lab_issued: 'Lab-issued COA',
   corroborated: 'Corroborated',
   independently_authenticated: 'Independently authenticated',
};

export function documentationLabel(state: DocumentationState): string {
   return DOC_LABELS[state] ?? 'Not specified';
}

export const CATALOG_META = {
   total: PRODUCTS.length,
   demo: true,
   dataDate: '2026-10-11', // catalog version
   note:
      'Names and prices are owner-supplied catalog data for this ' +
      'demonstration. Certificates of analysis are shown as honest empty / ' +
      'pending states; no purity, testing, supplier, or certification is ' +
      'fabricated. A "no record" result is a successful, honest outcome — not ' +
      'a passed test.',
   pricing: 'All shown prices include shipping.',
};
