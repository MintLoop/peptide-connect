# Peptide Connect — Website Brand Asset Kit

Approved visual source: **Constellation** (four asymmetric circular nodes and connecting strokes). This kit contains raster assets prepared for initial site integration. Preserve the approved reference board as the visual source of truth.

| File | Use |
| --- | --- |
| peptide-connect-logo-full.webp | Fast-loading horizontal logo on a light background; PNG is the lossless master |
| peptide-connect-icon.webp | Standalone molecular mark in app UI; PNG is the lossless master |
| peptide-connect-header-dark.webp | Wide dark header/masthead background with reversed wordmark; PNG is the lossless master |
| favicon-16.png / -24.png / -32.png / -48.png | Browser/tab and compact interface tests |
| favicon-180.png | Apple touch icon candidate |
| favicon-192.png / -512.png | Web app manifest icons |

## Color tokens

- Deep navy: #102D38
- Bio teal: #12A89D
- Pale mint: #EAF5F2
- Off-white: #F7F9FA

## Implementation guidance

1. Use the **transparent full-color horizontal logo** over light website backgrounds. Its navy wordmark will not contrast sufficiently against navy backgrounds.
2. Use the **dark header art** as a standalone masthead graphic or promotional banner. For a responsive navigation bar, prefer a live CSS background and separate logo/icon so it can reflow on small screens.
3. Use **icon-only** assets for tabs, small buttons, PWA and social avatars. Verify the actual small-size legibility on the intended browser backgrounds.
4. Set explicit width/height to avoid layout shift, appropriate alt text, and serve WebP where supported.
5. The image-generated PNGs contain subtle painted/raster edge artifacts. They are suitable for prototype integration. Before branding signoff or sale, reconstruct and check a faithful vector SVG and font licensing. Do not automatically trace and mistake the result for an exact master.
6. Do not mistake these branding concept assets for a registered trademark or cleared commercial mark. Conduct a similarity review before public launch.

## Qwen handoff

Keep these filenames stable under your site's public brand assets directory. Treat the approved Constellation design as frozen, do not substitute a flower or generic hexagon, and develop page layouts around the brand palette without copying third-party site visuals.
