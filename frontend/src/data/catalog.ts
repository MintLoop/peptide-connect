// src/data/catalog.ts
// -----------------------------------------------------------------------------
// DEMO CATALOG. All products, suppliers, and COA records are DEMO data:
//   - No real compound names, no real lot numbers, no real supplier names.
//   - No purity claims, no COA data, no prices beyond illustrative placeholders.
//   - Clearly labeled in the UI via the DEMO banner and per-card badges.
//
// Phase C will replace this with a Supabase-backed product catalog.
// -----------------------------------------------------------------------------

import type { AvailabilityStatus } from '../config/site';

export interface ProductVariant {
   id: string;
   label: string;         // e.g. "10 mg"
   price: number | null;  // null = "inquire only" / not publicly listed
   status: 'active' | 'coming_soon';
}

export interface Product {
   slug: string;
   name: string;
   compound: string;      // IUPAC or common research name (DEMO)
   family: string;        // compound family / category
   route: string;         // "parenteral", "oral", "subcutaneous" — research context
   form: string;          // "lyophilized powder", "solution"
   status: AvailabilityStatus;
   coaAvailable: boolean; // always false in DEMO
   description: string;
   draftFlag: boolean;
   variants: ProductVariant[];
   tags: string[];        // filterable tags
}

/** DEMO suppliers — no real company names or addresses. */
export interface DemoSupplier {
   id: string;
   name: string;          // placeholder
   region: string;
   evidenceLevel: 'none' | 'unverified' | 'inquiry_only';
   note: string;
}

export const DEMO_SUPPLIERS: DemoSupplier[] = [
   {
    id: 'demo-sup-001',
    name: 'Demo Supplier North',
    region: 'Placeholder region',
    evidenceLevel: 'inquiry_only',
    note: 'DEMO — no COA, no lot traceability, no real data. Inquiry only.',
   },
   {
    id: 'demo-sup-002',
    name: 'Demo Supplier West',
    region: 'Placeholder region',
    evidenceLevel: 'none',
    note: 'DEMO — no published evidence. No COA on file.',
   },
];

/** DEMO COA records — all "no record published". No fabricated purity data. */
export interface DemoCoaRecord {
   compound: string;      // matches Product.name or compound
   lotNumber: string | null;
   labName: string | null;
   date: string | null;
   status: 'no_record' | 'pending' | 'unverified';
   note: string;          // honest empty-state text
}

export const DEMO_COA: DemoCoaRecord[] = [
    // Intentionally empty at the record level — the "no_record" statuses
    // are the honest empty state for every entry. COA Explorer shows what
    // is known (nothing is yet verified) without fabricating any numbers.
   {
     compound: 'DEMO-Compound-A',
     lotNumber: null,
     labName: null,
     date: null,
     status: 'no_record',
     note: 'No COA published for this lot yet. Independent verification not yet obtained.',
    },
   {
     compound: 'DEMO-Compound-B',
     lotNumber: null,
     labName: null,
     date: null,
     status: 'no_record',
     note: 'No COA published for this lot yet. No supplier COA on file.',
    },
   {
     compound: 'DEMO-Compound-C',
     lotNumber: null,
     labName: null,
     date: null,
     status: 'pending',
     note: 'COA requested from Demo Supplier North. Awaiting lab report. No results published.',
    },
];

export const PRODUCTS: Product[] = [
   {
    slug: 'demo-aa',
    name: 'Demo Compound A',
    compound: 'DEMO-Compound-A (research-use placeholder)',
    family: 'Placeholder family',
   route: 'parenteral (placeholder)',
    form: 'lyophilized powder (placeholder)',
    status: 'inquire',
    coaAvailable: false,
    description:
     'DEMO PRODUCT — placeholder for a research compound. For laboratory ' +
     'research use only. Not for human or veterinary consumption. ' +
     'No purity, potency, or clinical claims are implied.',
    draftFlag: true,
    variants: [
      { id: 'demo-aa-10', label: '10 mg (DEMO)', price: null, status: 'active' },
      { id: 'demo-aa-25', label: '25 mg (DEMO)', price: null, status: 'active' },
      { id: 'demo-aa-50', label: '50 mg (DEMO)', price: null, status: 'coming_soon' },
    ],
    tags: ['placeholder', 'demo', 'research'],
   },
   {
    slug: 'demo-bb',
    name: 'Demo Compound B',
    compound: 'DEMO-Compound-B (research-use placeholder)',
    family: 'Placeholder family',
   route: 'subcutaneous (placeholder)',
    form: 'lyophilized powder (placeholder)',
    status: 'available',
    coaAvailable: false,
    description:
     'DEMO PRODUCT — placeholder compound. For laboratory research use only. ' +
     'All data shown is clearly flagged as DEMO. No real compound, no real lot.',
    draftFlag: true,
    variants: [
      { id: 'demo-bb-10', label: '10 mg (DEMO)', price: null, status: 'active' },
      { id: 'demo-bb-20', label: '20 mg (DEMO)', price: null, status: 'active' },
    ],
    tags: ['placeholder', 'demo', 'research'],
   },
   {
    slug: 'demo-cc',
    name: 'Demo Compound C',
    compound: 'DEMO-Compound-C (research-use placeholder)',
    family: 'Peptide sequence family (placeholder)',
   route: 'subcutaneous (placeholder)',
    form: 'solution (placeholder)',
    status: 'not_available',
    coaAvailable: false,
    description:
     'DEMO PRODUCT — placeholder. Currently unavailable for inquiry. ' +
     'No real compound, no real lot, no COA. Available status: not_available.',
    draftFlag: true,
    variants: [
      { id: 'demo-cc-10', label: '10 mg (DEMO)', price: null, status: 'active' },
    ],
    tags: ['placeholder', 'demo', 'research'],
   },
   {
    slug: 'demo-dd',
    name: 'Demo Compound D',
    compound: 'DEMO-Compound-D (research-use placeholder)',
    family: 'Placeholder family',
   route: 'parenteral (placeholder)',
    form: 'lyophilized powder (placeholder)',
    status: 'inquire',
    coaAvailable: false,
    description:
     'DEMO PRODUCT — placeholder. For laboratory research use only. ' +
     'Inquiry-only compound: no public pricing. Contact to request pricing.',
    draftFlag: true,
    variants: [
      { id: 'demo-dd-10', label: '10 mg (DEMO)', price: null, status: 'active' },
      { id: 'demo-dd-50', label: '50 mg (DEMO)', price: null, status: 'active' },
      { id: 'demo-dd-100', label: '100 mg (DEMO)', price: null, status: 'coming_soon' },
    ],
    tags: ['placeholder', 'demo', 'research'],
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

export const CATALOG_META = {
   total: PRODUCTS.length,
   demo: true,
   dataDate: '2026-10-09', // DEMO data version
   note: 'All products, suppliers, and COA records in this catalog are DEMO data.',
};
