# PWA Studio Guardian Lab

A local learning project inspired by a Magento PWA Studio Guardian storefront.

## Run

```bash
npm install
npm run dev
```

If local PWA behavior gets stale while experimenting, unregister `mock-sw.js` from your browser devtools service worker panel and refresh the page.

## Build And Test

```bash
npm test
npm run build
```

## What To Study

- `docs/learning-map.md`
- `docs/source-project-notes.md`
- `src/buildpack`
- `src/graphql`
- `src/lib/authSession.js`
- `src/talons`
- `src/modules`

## Module Concept Map

| Area | Files | Concept taught |
| --- | --- | --- |
| App routes | `src/app/routes.jsx`, `src/buildpack/routeRegistry.js`, `src/buildpack/featureFlags.js` | Buildpack-style registration plus feature-flagged route enablement. |
| Auth + GraphQL | `src/talons/useAuthSession.js`, `src/talons/useProtectedGraphQL.js`, `src/graphql` | Refresh access tokens before protected GraphQL operations. |
| Catalog + cart | `src/modules/catalog`, `src/talons/useCart.js` | Product data loading, tracking, and add-to-cart talon state. |
| Checkout | `src/modules/checkout`, `src/buildpack/paymentRegistry.js` | Cart overview beside registered payment methods. |
| Rewards | `src/modules/rewards` | Points, coupons, store credit, and free-gift merchandising. |
| Health | `src/modules/health` | Service modules and a health-result concept outside core commerce. |
| Offline events | `src/modules/offlineEvents` | Event booking cards and ticket-list concepts. |
| PageBuilder + ads | `src/modules/pageBuilder`, `src/lib/ads.js` | Ad slot metadata, page type naming, ad-pool consumption, and tracking. |

## Why This Exists

The original project is a large Magento PWA Studio storefront. This lab extracts the learning value into a small app you can run locally without Magento, payment credentials, or production APIs.
