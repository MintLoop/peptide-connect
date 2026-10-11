// src/config/site.ts
// -----------------------------------------------------------------------------
// Centralized branding + configuration — the single source of truth shared by
// every layout, page, and component. In Phase C this becomes the editable
// `site_config` (admin panel + .env for infra). Nothing here is hardcoded
// elsewhere: brand tokens, nav, legal entity, and contact all live here.
//
// DEMO DATA POSTURE: this build ships on clearly-labeled DEMO data only. No real
// catalog, prices, suppliers, COAs, or customer PII. See `demo` flags below.
// -----------------------------------------------------------------------------

export type AvailabilityStatus = 'available' | 'inquire' | 'not_available';

export interface NavItem {
  label: string;
  href: string;
}

export interface SiteConfig {
  name: string;
  shortName: string;
  tagline: string;
  description: string;
  url: string;
  brand: {
    navy: string;
    teal: string;
    paleMint: string;
    offWhite: string;
  };
  legal: {
    entity: string;
    jurisdiction: string;
  };
  contact: {
    email: string;
    hours: string;
  };
  nav: NavItem[];
  footerNav: { title: string; links: NavItem[] };
  researchDisclaimer: string;
  demoBanner: string;
}

export const site: SiteConfig = {
  name: 'Peptide Connect',
  shortName: 'Peptide Connect',
  tagline:
    'Evidence-first supplier intelligence and verification for the research-peptide market.',
  description:
    'Peptide Connect turns fragmented laboratory reports, supplier COAs, and ' +
    'directories into structured, provenance-backed supplier evidence — ' +
    'distinguishing what is claimed, what is independently verified, and what is ' +
    'still unknown.',
  // PLACEHOLDER domain — owner sets the real domain in Phase C (B4). Kept as a
  // placeholder so the build is offline-safe and transferable.
  url: 'https://peptideconnect.example',

  brand: {
    navy: '#102D38',
    teal: '#12A89D',
    paleMint: '#EAF5F2',
    offWhite: '#F7F9FA',
  },

  legal: {
    // Placeholder entity — no real legal name is hardcoded. Set in Phase C.
    entity: 'Peptide Connect (placeholder legal entity — set in Phase C)',
    jurisdiction: 'Unspecified',
  },

  contact: {
    email: 'contact@peptideconnect.example',
    hours: 'Response window: business hours, placeholder — set in Phase C.',
  },

  // Public navigation. Admin is intentionally NOT in public nav (authenticated).
  nav: [
    { label: 'Catalog', href: '/catalog' },
    { label: 'COA Explorer', href: '/coa' },
    { label: 'Request', href: '/request' },
    { label: 'Order status', href: '/order' },
    { label: 'FAQ', href: '/faq' },
    { label: 'About', href: '/about' },
    { label: 'Contact', href: '/contact' },
  ],

  footerNav: [
    {
      title: 'Product',
      links: [
        { label: 'Catalog', href: '/catalog' },
        { label: 'COA Explorer', href: '/coa' },
        { label: 'Request an order', href: '/request' },
        { label: 'Order status', href: '/order' },
      ],
    },
    {
      title: 'Company',
      links: [
        { label: 'About', href: '/about' },
        { label: 'FAQ', href: '/faq' },
        { label: 'Contact', href: '/contact' },
      ],
    },
    {
      title: 'Legal',
      links: [
        { label: 'Privacy', href: '/privacy' },
        { label: 'Terms', href: '/terms' },
        { label: 'Shipping & Returns', href: '/shipping' },
      ],
    },
  ],

  researchDisclaimer:
    'For laboratory research use only. Not for human or veterinary ' +
    'consumption. These materials are not intended to diagnose, treat, cure, or ' +
    'prevent any disease.',

  demoBanner:
    'DEMO BUILD — demo catalog, demo suppliers, and demo order data. No real ' +
    'products, prices, suppliers, COAs, or customer information are shown. ' +
    'Certificates of analysis are not fabricated.',
};

// Whether the site is on DEMO data. Toggled in Phase C when a real catalog,
// backend, and auth exist. Everything that would otherwise emit unverified
// claims branches on this.
export const DEMO = true;
