# Financial safety implementation plan

**Goal:** Add the approved financial safety, asset allocation, liabilities, freedom ladder and stress scenarios from the cumulative overview entry.
**Architecture:** Separate finance balances from ledger data, using a dedicated versioned AsyncStorage key. Pure functions calculate metrics; a separate React Native screen renders and edits values. No change to Excel transaction sync.
**Tech stack:** React Native / Expo, react-native-svg, TypeScript, Vitest.

- [x] Add `src/lib/financialSafety.ts` with typed balances, settings, validation, ratios, distribution, freedom target and stress calculations. Missing denominators return null, unknown yields remain explicit. Emergency/planned funds are not double-counted as investment capital. Monthly debt service is included in runway; upcoming maturity shown separately.
- [x] Test baseline 1,000,000 principal / 1.2% = 1,000 monthly, zero and unknown inputs, reserves, home exclusion, negative net worth, inflation, interruptions and target timing using fixed dates.
- [x] Add dedicated persistence with schema validation and visible failures; do not overwrite corrupted saved data. Test roundtrip and invalid data.
- [x] Add `src/components/FinancialSafetyScreen.tsx`: overview, type/channel ring, asset/debt add/edit/remove with confirmation, settings, editable levels, stress cases and recent three complete calendar month expense reference. Exclude user-selected exceptional categories and show excluded amounts.
- [x] Wire cumulative overview entry and return navigation in `App.tsx`; preserve homepage state while navigating.
- [x] Run typecheck and full tests. Exercise local browser input, cancellation, persistence and responsive layout using temporary test data only; restore test changes.

Verification: TypeScript passed; 37 Vitest tests passed. Browser checked overview entry, asset creation, reload persistence, channel composition, remove confirmation, cancellation, 10/30 percent savings toggles and 390px mobile layout. Temporary asset removed; no ledger or workbook modified.
