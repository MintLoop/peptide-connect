# Dev-server runtime fix: "[ERROR] module is not defined"

**Date:** 2026-10-10 · **Scope:** restore a clean `npm run dev` (Phase B) · **No version changes**

## Symptom
`npm run dev` started, but every route returned **HTTP 500**:
```
[ERROR] module is not defined
  Stack trace:
   at node_modules/react/index.js:6:3
```
`/`, `/catalog`, `/catalog/demo-aa`, `/coa` all 500. Yet `npm run build`
reportedly passed with 17 pages.

## Root cause (not a version incompatibility)
The app uses **zero React** — verified: no `.tsx/.jsx`, no `from 'react'`,
no `client:load`/`client:visible`/`client:idle` islands. But `astro.config.mjs`
still registered `integrations: [react()]` plus
`vite.ssr.noExternal: ['react','react-dom']` — copied verbatim from the
GetReta scaffold (whose stack **is** Astro+React+Tailwind).

Because of `noExternal`, in `astro dev` Vite's SSR pipeline **forces React's
CommonJS entry through its ESM module runner** on every request, instead of
externalizing it to a real Node `require`. React's entry `node_modules/react/index.js`
is:
```js
3  if (process.env.NODE_ENV === 'production') {
4    module.exports = require('./cjs/react.production.js');
5  } else {
6    module.exports = require('./cjs/react.development.js');   // module is not defined
7  }
```
In the ESM runner scope the CommonJS `module` global is undefined →
`module is not defined` → 500 on every route. The `--verbose` trace confirmed the
chain:
```
vite:transform @astrojs/react/server.js
astro:vite Error when evaluating SSR module @astrojs/react/server.js: module is not defined
  at eval (.../node_modules/react/index.js:8:3)
  at ESModulesEvaluator.runInlinedModule (vite/node/module-runner.js:1070:6)
  at SSRCompatModuleRunner.directRequest (...)
```
**Why the build "passed":** the static production build **externalizes** that
React SSR bundle, so the CJS entry resolves normally (nothing in src/ actually
renders a React component, so the external bundle is inert). Dev doesn't
externalize it → breaks. Same code, two different module-resolution paths.

## Fix (smallest justified — no version change)
Removed the vestigial integration entirely. `astro.config.mjs`:
- deleted `import react from '@astrojs/react';`
- deleted `integrations: [react()]`
- deleted `vite: { ssr: { noExternal: ['react','react-dom'] } }`

`output: 'static'` and the `image` remotePatterns config are unchanged.
React/react-dom remain in `node_modules` but are now unreferenced. No upgrades
to Astro (5.18.2), React (19.3.0), or Node (26.7.0) were made.

## Verification
- `astro dev` on a fresh port: `GET / /catalog /catalog/demo-aa` → **HTTP 200**
  (correct `<title>`, demo banner present). Dev log: **0 ERROR** lines after the
  requests; `grep -c '@astrojs/react|react/index.js'` → **0** (React no longer
  evaluated per request).
- `npm run build` → **17 pages, 0 errors** (regression check).

## Optional follow-up (not required; no version bump)
`npm rm @astrojs/react react react-dom @types/react @types/react-dom` is safe —
none are imported — but that would rewrite `package-lock.json`, so it's left to
the owner rather than done here.
