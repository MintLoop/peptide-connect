// build-logo-svgs.mjs
// Generates the full Peptide Connect logo system from the measured geometry
// (brand/geometry.json). Pure Node, zero deps. One source of truth = geometry.json.
//
// Variants produced into ../public/brand/:
//   pc-mark-full.svg                  icon, full color, tight square (favicons derive from this)
//   pc-mark-reversed.svg              icon for dark backgrounds (navy node -> light)
//   pc-mark-mono.svg                  one-color, uses currentColor (single-color variant)
//   pc-logo-horizontal.svg            mark + stacked wordmark, light bg (navy + teal)
//   pc-logo-horizontal-reversed.svg   mark + stacked wordmark, dark bg (white + teal)
//   pc-logo-stacked.svg               mark centered over stacked wordmark, light bg
//
// The mark: 4 asymmetric circular nodes + 5 straight teal strokes + 1 navy anchor node.
// No hexagon, no extra node, no flower. See brand/geometry.json for the measured coords.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const geom = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'brand', 'geometry.json'), 'utf8'));
const OUT = path.join(__dirname, '..', 'public', 'brand');
fs.mkdirSync(OUT, { recursive: true });

// Palette tokens. Navy node + teal nodes on light; navy anchor flips to pale-mint on dark
// (a white/pale node on a dark background keeps the mark legible). Brand values are
// hardcoded here to match geometry.colors exactly; edit geometry.json to change the mark.
const PALETTES = {
   light: { teal: geom.colors.teal, anchor: geom.colors.navy, text: geom.colors.navy, accent: geom.colors.teal },
    dark:  { teal: geom.colors.teal, anchor: '#EAF5F2', text: '#F7F9FA', accent: geom.colors.teal },
    };

// node lookup by id
const nodeById = () => Object.fromEntries(geom.nodes.map(n => [n.id, n]));

// Mark glyph into a square cell (size, at top-left x,y).
//   palette: 'light' | 'dark'   mode: 'color' | 'mono'   color: single color for mono
function markGlyph({ size = 100, x = 0, y = 0, palette = 'light', mode = 'color', color = 'currentColor' } = {}) {
  const pal = PALETTES[palette] || PALETTES.light;
  const nodes = nodeById();
  // tight bounding box so the mark fills the cell
  let minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9;
  for (const n of geom.nodes) {
   minX = Math.min(minX, n.x - n.r); minY = Math.min(minY, n.y - n.r);
    maxX = Math.max(maxX, n.x + n.r); maxY = Math.max(maxY, n.y + n.r);
   }
  const spanW = maxX - minX, spanH = maxY - minY;
  const scale = size / Math.max(spanW, spanH);
  const padX = (size - spanW * scale) / 2, padY = (size - spanH * scale) / 2;
  const fx = n => (n.x - minX) * scale + padX + x;
  const fy = n => (n.y - minY) * scale + padY + y;
  const fr = n => n.r * scale;

  let out = `<g class="pc-mark" role="img" aria-label="Peptide Connect constellation mark">`;
  // edges underneath the nodes. All 5 strokes are teal (measured); mono mode forces `color`.
  const edgeStroke = Math.max(geom.edgeStrokeWidth * scale * 0.85, size * 0.028);
  for (const e of geom.edges) {
    const a = nodes[e.from], b = nodes[e.to];
    const stroke = mode === 'mono' ? color : pal.teal;
    out += `<line x1="${fx(a).toFixed(2)}" y1="${fy(a).toFixed(2)}" x2="${fx(b).toFixed(2)}" y2="${fy(b).toFixed(2)}" ` +
        `stroke="${stroke}" stroke-width="${edgeStroke.toFixed(2)}" stroke-linecap="round"/>`;
   }
   // nodes on top
  for (const n of geom.nodes) {
    let fill;
    if (mode === 'mono') fill = color;
    else fill = n.color === 'navy' ? pal.anchor : pal.teal;
    out += `<circle cx="${fx(n).toFixed(2)}" cy="${fy(n).toFixed(2)}" r="${fr(n).toFixed(2)}" fill="${fill}"/>`;
   }
  out += `</g>`;
  return out;
}

function svgDoc(viewW, viewH, body, { title, bg = 'transparent' } = {}) {
  const bgAttr = bg && bg !== 'transparent' ? ` style="background:${bg}"` : '';
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${viewW} ${viewH}" width="${viewW}" height="${viewH}"${bgAttr}>` +
      `${title ? `<title>${title}</title>` : ''}${body}</svg>\n`;
}

function write(name, content) {
  fs.writeFileSync(path.join(OUT, name), content);
  console.log('  wrote', name.padEnd(34), `(${Buffer.byteLength(content)} B)`);
}

const FONT = `-apple-system, BlinkMacSystemFont, "Segoe UI", Inter, system-ui, sans-serif`;

// 1..3 icon variants (tight 92px mark centered in a 100 square)
write('pc-mark-full.svg',     svgDoc(100, 100, markGlyph({ size: 88, x: 6, y: 6, palette: 'light' }), { title: 'Peptide Connect' }));
write('pc-mark-reversed.svg', svgDoc(100, 100, markGlyph({ size: 88, x: 6, y: 6, palette: 'dark' })));
write('pc-mark-mono.svg',     svgDoc(100, 100, markGlyph({ size: 88, x: 6, y: 6, mode: 'mono', color: 'currentColor' })));

// 4..5 horizontal lockups: mark (left, ~120px) + two-line wordmark (right)
function horizontal(palette) {
  const W = 640, H = 150;
  const body =
    markGlyph({ size: 118, x: 8, y: 16, palette }) +
    `<text x="156" y="80"  font-family="${FONT}" font-size="56" font-weight="800" letter-spacing="-0.5" ` +
     `fill="${PALETTES[palette].text}">PEPTIDE</text>` +
    `<text x="156" y="134" font-family="${FONT}" font-size="56" font-weight="800" letter-spacing="14" ` +
     `fill="${PALETTES[palette].accent}">CONNECT</text>`;
  return svgDoc(W, H, body, { title: 'Peptide Connect' });
}
write('pc-logo-horizontal.svg',          horizontal('light'));
write('pc-logo-horizontal-reversed.svg', horizontal('dark'));

// 6 stacked lockup: mark centered above the two-line wordmark
function stacked() {
  const W = 360, H = 300;
  const body =
    markGlyph({ size: 150, x: 105, y: 16 }) +
    `<text x="180" y="200" text-anchor="middle" font-family="${FONT}" font-size="44" font-weight="800" ` +
     `letter-spacing="-0.5" fill="${PALETTES.light.text}">PEPTIDE</text>` +
    `<text x="180" y="244" text-anchor="middle" font-family="${FONT}" font-size="30" font-weight="700" ` +
     `letter-spacing="9" fill="${PALETTES.light.accent}">CONNECT</text>`;
  return svgDoc(W, H, body, { title: 'Peptide Connect' });
}
write('pc-logo-stacked.svg', stacked());

console.log('Logo variants written:', OUT);
