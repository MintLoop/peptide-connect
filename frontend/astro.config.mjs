import { defineConfig } from 'astro/config';

// Peptide Connect — static site (Phase B shell). No framework integrations:
// the design system is a hand-crafted CSS-token system (public/styles/*.css) and
// the interactive surface is vanilla JS (public/js/app.js). No React, no Tailwind —
// a deliberate departure from GetReta's Astro+React+Tailwind stack.
//
// ROOT-CAUSE NOTE ("[ERROR] module is not defined" under `astro dev`):
//   This scaffold originally registered `integrations: [react()]` with
//   `vite.ssr.noExternal: ['react','react-dom']`, copied from the GetReta base.
//   Nothing in src/ uses React (no .tsx/.jsx, no client:load/visible/idle
//   islands, no `from 'react'`), so the React SSR entry was loaded on EVERY
//   request but rendered nothing. In `astro dev`, noExternal forced Vite to run
//   React's CommonJS entry (node_modules/react/index.js) via its ESM module
//   runner, where the CJS `module` global is undefined -> "module is not defined"
//   -> HTTP 500 on all routes. The production build externalized that bundle, so
//   it "passed" while dev broke — hence the discrepancy. Removing the vestigial
//   integration fixes the real cause without any version change. If the owner
//   wants the tree pruned, `npm rm @astrojs/react react react-dom @types/react
//   @types/react-dom` is safe (none are imported) — no version bump needed.
export default defineConfig({
   site:'https://peptideconnect.example',   // PLACEHOLDER — owner sets real domain (Phase C / B4)
   output: 'static',
   image: {
      // Local raster brand assets only. No remote fetch at build (offline-safe, transferable).
     remotePatterns: [],
    },
});
