# Guardian RN Learning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `/Users/edy/Documents/MY/guardian-rn-learning`, a lightweight React Native CLI-style learning app that demonstrates the main architecture and special features of `app-guardian`.

**Architecture:** The app uses a small React Native project with `src/core` for reusable base behavior and `src/override` for brand-specific overrides. Mock services and pure helpers make the business flows testable without production GraphQL, Firebase, private SDKs, or native credentials.

**Tech Stack:** React Native 0.79, React 19, React Navigation, Apollo Client reactive variables, AsyncStorage, React Native Paper, Jest, Babel module resolver.

---

## File Structure

- Create `/Users/edy/Documents/MY/guardian-rn-learning/package.json`: scripts and dependencies.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/app.json`: React Native app metadata.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/index.js`: app registry entry.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/App.js`: root provider and launch init.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/babel.config.js`: React Native Babel preset and `@app` alias.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/metro.config.js`: Metro default config.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/jest.config.js`: Jest setup for pure logic tests.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/aliases.json`: `@app` override-first mapping.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/config/modules.js`: feature module registry.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/override/config/modules.js`: brand override of module labels and switches.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/data/mockData.js`: products, coupons, and link examples.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/services/cache.js`: Apollo reactive variables.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/services/mockGraphql.js`: mock query/mutation service layer.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/helpers/storage.js`: JSON storage wrapper.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/helpers/cartLogic.js`: pure cart calculations.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/helpers/deepLink.js`: pure deep-link parser and scanner resolver.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/helpers/navigation.js`: navigation ref and guarded navigation helper.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/hooks/useAppInitialize.js`: load persisted mock app state.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/components/*`: compact Button, Screen, ProductCard, SnackbarHost.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/navigation/*`: root stack, auth stack, app stack, tabs.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/core/features/*`: auth, home, catalog, detail, cart, coupon wallet, scanner, account, maintenance screens.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/override/features/home/HomeScreen.js`: override-first home example.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/src/override/styles/theme.js`: Guardian-inspired theme.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/__tests__/cartLogic.test.js`: cart tests.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/__tests__/deepLink.test.js`: link and scanner tests.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/docs/project-analysis.md`: source project technical summary.
- Create `/Users/edy/Documents/MY/guardian-rn-learning/docs/learning-guide.md`: study route and exercises.

## Task 1: Scaffold Project

**Files:**
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/package.json`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/app.json`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/index.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/App.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/babel.config.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/metro.config.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/jest.config.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/aliases.json`

- [ ] **Step 1: Create React Native project shell**

Write the root config files with React Native CLI-compatible scripts and override-first aliasing.

- [ ] **Step 2: Run package metadata check**

Run: `node -e "JSON.parse(require('fs').readFileSync('package.json','utf8')); console.log('package ok')"`

Expected: `package ok`

- [ ] **Step 3: Commit scaffold**

Run: `git -C /Users/edy/Documents/MY add guardian-rn-learning && git -C /Users/edy/Documents/MY commit -m "feat: scaffold guardian rn learning app"`

## Task 2: Add Pure Domain Logic With Tests

**Files:**
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/data/mockData.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/helpers/cartLogic.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/helpers/deepLink.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/__tests__/cartLogic.test.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/__tests__/deepLink.test.js`

- [ ] **Step 1: Write tests for cart and links**

Tests cover adding an item, changing quantity, applying valid and invalid coupons, parsing Guardian product/category/brand/CMS links, and resolving scanner input.

- [ ] **Step 2: Run tests to verify missing implementation fails**

Run: `yarn test --runInBand`

Expected: test runner reports missing modules or failing expectations.

- [ ] **Step 3: Implement pure helpers and mock data**

Implement cart reducer helpers and deep-link/scanner resolver with deterministic mock data.

- [ ] **Step 4: Run tests to verify pass**

Run: `yarn test --runInBand`

Expected: all tests pass.

- [ ] **Step 5: Commit pure logic**

Run: `git -C /Users/edy/Documents/MY add guardian-rn-learning && git -C /Users/edy/Documents/MY commit -m "feat: add guardian learning domain logic"`

## Task 3: Add State, Services, And App Initialization

**Files:**
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/services/cache.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/services/mockGraphql.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/helpers/storage.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/hooks/useAppInitialize.js`
- Modify: `/Users/edy/Documents/MY/guardian-rn-learning/App.js`

- [ ] **Step 1: Add Apollo reactive variables**

Create reactive variables for loading, snackbar, maintenance, user token, user type, cart items, cart quantity, selected coupon, selected product, reward points, and remote config.

- [ ] **Step 2: Add mock GraphQL-like services**

Expose async helpers for products, product by barcode, URL resolver, coupons, login, logout, and remote config.

- [ ] **Step 3: Wire app initialization**

Load persisted token/cart values and mock remote config, then update reactive variables.

- [ ] **Step 4: Run tests**

Run: `yarn test --runInBand`

Expected: all tests pass.

- [ ] **Step 5: Commit state and services**

Run: `git -C /Users/edy/Documents/MY add guardian-rn-learning && git -C /Users/edy/Documents/MY commit -m "feat: add guardian learning app state"`

## Task 4: Build Navigation And Screens

**Files:**
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/config/modules.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/override/config/modules.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/helpers/navigation.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/navigation/AppNavigator.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/navigation/AuthStack.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/navigation/AppStack.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/navigation/AppTabs.js`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/core/features/*`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/src/override/features/home/HomeScreen.js`

- [ ] **Step 1: Add module config**

Define enabled modules and labels for auth, home, catalog, product detail, cart, coupons, scanner, account, and maintenance.

- [ ] **Step 2: Add navigation shell**

Implement auth/main switching, bottom tabs, maintenance gate, and stack routes.

- [ ] **Step 3: Add learning screens**

Implement compact screens that exercise login, catalog, product detail, cart, coupon wallet, scanner simulator, account, and maintenance flows.

- [ ] **Step 4: Add override home**

Create a visible override home screen that imports core data and shows why `@app` resolves to override first.

- [ ] **Step 5: Run tests**

Run: `yarn test --runInBand`

Expected: all tests pass.

- [ ] **Step 6: Commit UI and navigation**

Run: `git -C /Users/edy/Documents/MY add guardian-rn-learning && git -C /Users/edy/Documents/MY commit -m "feat: add guardian learning app screens"`

## Task 5: Add Documentation And Final Verification

**Files:**
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/README.md`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/docs/project-analysis.md`
- Create: `/Users/edy/Documents/MY/guardian-rn-learning/docs/learning-guide.md`

- [ ] **Step 1: Write source project analysis**

Summarize architecture, technology choices, special business features, and how they map into the learning app.

- [ ] **Step 2: Write learning guide**

Add setup commands, study order, practice tasks, and extension ideas.

- [ ] **Step 3: Run tests**

Run: `yarn test --runInBand`

Expected: all tests pass.

- [ ] **Step 4: Run dependency or install check**

Run: `yarn install --mode=skip-builds` if supported by Yarn version, otherwise `yarn install --ignore-scripts`.

Expected: dependencies resolve, or document why native environment install was not completed.

- [ ] **Step 5: Commit docs and verification fixes**

Run: `git -C /Users/edy/Documents/MY add guardian-rn-learning && git -C /Users/edy/Documents/MY commit -m "docs: document guardian rn learning app"`

## Self-Review

- Spec coverage: covered source analysis, core/override, module switches, navigation, reactive vars, mock GraphQL, app init, commerce flows, scanner/deep-link simulator, maintenance, docs, tests, and run commands.
- Placeholder scan: no placeholder requirements remain.
- Type consistency: planned helper names, directories, and reactive-state names are consistent across tasks.
