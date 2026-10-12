// src/config/origin.ts
// Single configurable production origin for all public absolute URLs.
//
// Use the same constant everywhere: canonical tag, Open Graph, Twitter card,
// JSON-LD, Astro `site`, and any share fallbacks. For future domain transfers,
// set PUBLIC_SITE_ORIGIN in a .env file at build time; otherwise the default
// below is used.
//
// Example (.env):
//   PUBLIC_SITE_ORIGIN=https://peptide-connect.com
//
// Do NOT override with localhost for production sharing.
const DEFAULT_ORIGIN = 'https://peptide-connect.com';

// Astro exposes `process.env` at build time for .env files. In a non-Node
// context, fall back to the default so imports never crash.
const envOrigin =
   typeof process !== 'undefined'
     ? process.env?.PUBLIC_SITE_ORIGIN
     : undefined;

export const SITE_ORIGIN = envOrigin?.trim() || DEFAULT_ORIGIN;

// Contact email derived from the origin's host, not hardcoded separately.
export const CONTACT_EMAIL = `contact@${new URL(SITE_ORIGIN).hostname}`;
