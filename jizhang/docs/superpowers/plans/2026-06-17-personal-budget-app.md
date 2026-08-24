# Personal Budget App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a mobile-first personal bookkeeping app with recording, budgets, bill analysis, and local persistence.

**Architecture:** Use an Expo React Native app with TypeScript. Keep business behavior in tested helper modules, keep persistence isolated behind an async storage adapter, and keep UI state in the main app component for this first version.

**Tech Stack:** Expo, React Native, TypeScript, Vitest, AsyncStorage.

---

## File Structure

- `package.json`: npm scripts and dependencies.
- `app.json`: Expo app configuration.
- `App.tsx`: native app shell, tab navigation, form state, and screen composition.
- `src/data/categories.ts`: predefined income and expense categories.
- `src/data/sampleData.ts`: seed records and default budgets.
- `src/lib/types.ts`: shared data types.
- `src/lib/analytics.ts`: pure helpers for totals, budgets, category summaries, and trends.
- `src/lib/storage.ts`: AsyncStorage-compatible load, save, and fallback logic.
- `src/lib/analytics.test.ts`: unit tests for derived financial views.
- `src/lib/storage.test.ts`: unit tests for persistence fallback behavior.

## Tasks

### Task 1: Project Scaffold

**Files:**
- Create: `package.json`
- Create: `index.html`
- Create: `src/main.tsx`
- Create: `src/App.tsx`
- Create: `src/styles.css`

- [ ] **Step 1: Create minimal Vite React scaffold**

Create the package, host page, React entry point, placeholder app, and base CSS. The app should render text reading `记账 App`.

- [ ] **Step 2: Install dependencies**

Run: `npm install`

- [ ] **Step 3: Run build**

Run: `npm run build`

Expected: Vite completes successfully and writes `dist/`.

### Task 2: Analytics Helpers With TDD

**Files:**
- Create: `src/lib/types.ts`
- Create: `src/data/categories.ts`
- Create: `src/data/sampleData.ts`
- Create: `src/lib/analytics.test.ts`
- Create: `src/lib/analytics.ts`

- [ ] **Step 1: Write failing analytics tests**

Add tests covering monthly totals, budget status, category spending, seven-day trend, and validation.

- [ ] **Step 2: Verify tests fail**

Run: `npm test -- --run src/lib/analytics.test.ts`

Expected: FAIL because the analytics module does not exist yet.

- [ ] **Step 3: Implement minimal analytics helpers**

Create types, categories, sample data, and analytics functions needed by the tests.

- [ ] **Step 4: Verify tests pass**

Run: `npm test -- --run src/lib/analytics.test.ts`

Expected: PASS.

### Task 3: Storage Helpers With TDD

**Files:**
- Create: `src/lib/storage.test.ts`
- Create: `src/lib/storage.ts`

- [ ] **Step 1: Write failing storage tests**

Add tests for loading fallback data, saving and loading app data, and corrupted JSON fallback.

- [ ] **Step 2: Verify tests fail**

Run: `npm test -- --run src/lib/storage.test.ts`

Expected: FAIL because the storage module does not exist yet.

- [ ] **Step 3: Implement storage helpers**

Create load and save helpers using an injectable Storage-like interface.

- [ ] **Step 4: Verify tests pass**

Run: `npm test -- --run src/lib/storage.test.ts`

Expected: PASS.

### Task 4: Mobile App UI

**Files:**
- Modify: `src/App.tsx`
- Modify: `src/styles.css`

- [ ] **Step 1: Build app screens**

Implement bottom navigation with Home, Record, Budget, and Analysis tabs. Wire the record form, budget editor, transaction list, and analysis summaries to the tested helper modules.

- [ ] **Step 2: Build responsive visual style**

Implement the clean light visual direction: neutral background, white panels, compact text, green budget health, amber near-limit state, red overspending state, and phone-first layout.

- [ ] **Step 3: Run tests**

Run: `npm test -- --run`

Expected: PASS.

- [ ] **Step 4: Run build**

Run: `npm run build`

Expected: PASS.

### Task 5: Browser Verification

**Files:**
- No source file changes expected unless verification reveals a UI problem.

- [ ] **Step 1: Start dev server**

Run: `npm run dev -- --host 127.0.0.1`

Expected: Vite prints a localhost URL.

- [ ] **Step 2: Open app in browser**

Open the Vite URL in the in-app browser and verify the app renders.

- [ ] **Step 3: Exercise core workflow**

Verify: add an expense, add income, change budget, switch analysis tab, reload page, and confirm data persists.

- [ ] **Step 4: Final verification**

Run: `npm test -- --run && npm run build`

Expected: PASS.
