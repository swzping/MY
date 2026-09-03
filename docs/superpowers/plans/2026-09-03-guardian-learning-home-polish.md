# Guardian Learning Home Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the Guardian RN Learning app home, member summary, toolbar, and product list so the demo feels closer to the source app.

**Architecture:** Add reusable UI components under `src/core/components`, keep the branded home override in `src/override/features/home`, and keep product rendering shared through `ProductCard`. Use pure view-model helpers for formatting and summary data so UI behavior has test coverage.

**Tech Stack:** React Native 0.79, React Native Paper, Apollo reactive variables, Jest.

---

## Files

- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/helpers/homeViewModel.js`: formats member/product summary state for the polished screens.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/__tests__/homeViewModel.test.js`: verifies member and product summary formatting.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/components/LearningToolbar.js`: Guardian-like top toolbar with logo, search, wishlist, notification, and cart badge.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/components/LoyaltySummaryCard.js`: home member card inspired by the source app LoyaltyCard.
- Modify `/Users/edy/Documents/MY/guardian-rn-learning/src/core/data/mockData.js`: enrich product and user mock data.
- Modify `/Users/edy/Documents/MY/guardian-rn-learning/src/core/components/ProductCard.js`: compact product tile with image placeholder, badge, brand/category, price, and CTA.
- Modify `/Users/edy/Documents/MY/guardian-rn-learning/src/override/features/home/HomeScreen.js`: replace rough demo content with toolbar, loyalty card, shortcut row, promotion band, and featured products.
- Modify `/Users/edy/Documents/MY/guardian-rn-learning/src/core/features/catalog/CatalogScreen.js`: add toolbar, PLP header, sort/filter pills, and two-column product grid.

## Tasks

- [ ] Write failing tests for `buildMemberSummary` and `buildProductListSummary`.
- [ ] Implement `homeViewModel.js` and enrich mock data.
- [ ] Add `LearningToolbar` and `LoyaltySummaryCard`.
- [ ] Redesign `ProductCard` as a compact commerce tile.
- [ ] Rework override Home and Catalog screens.
- [ ] Run `yarn test --runInBand`.
- [ ] Run Babel transform smoke check for `src`, `App.js`, and `index.js`.
- [ ] Commit the UI polish changes only.

## Self-Review

- Scope is limited to home, member summary, product listing, toolbar, shared product card, and supporting tests.
- No production SDKs or real API calls are introduced.
- Existing `shouwang` changes remain untouched.
