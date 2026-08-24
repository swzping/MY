# Personal Budget App Design

Date: 2026-06-16

## Goal

Build a mobile-first personal bookkeeping app for daily use. The app should let a user record income and expenses quickly, set budgets, and analyze bills without requiring login or a backend in the first version.

## Product Scope

The first version includes four main areas:

- Home: monthly overview, budget health, quick entry, and recent records.
- Bookkeeping: add income or expense records with amount, category, date, and note.
- Budget: set a monthly total budget and optional category budgets.
- Analysis: review income, expense, category split, seven-day trend, and largest spending categories.

Cloud sync, multi-user sharing, bank import, OCR receipt scanning, and account authentication are out of scope for this first version.

## User Experience

The app is mobile-first and should feel like a real app rather than a landing page. It uses bottom navigation with four tabs:

- Home
- Record
- Budget
- Analysis

The home screen prioritizes fast comprehension. Within a few seconds, the user should see monthly spending, monthly income, remaining budget, budget usage progress, and recent bills. A prominent quick-entry control lets the user add a record without hunting through menus.

## Visual Direction

Use a clean, practical light interface:

- Soft neutral background.
- White panels with restrained borders and radius no larger than 8px.
- Green for healthy budget states.
- Amber for near-limit states.
- Red for overspending or negative warnings.
- Compact typography suited to a phone-sized interface.

Avoid a marketing hero, decorative gradients, and overly card-heavy composition. The app should feel calm, useful, and easy to scan.

## Data Model

Records:

- id
- type: income or expense
- amount
- category
- date
- note
- createdAt

Budgets:

- monthlyBudget
- categoryBudgets keyed by category

Categories are predefined for the first version:

- Expense: Food, Transport, Shopping, Housing, Entertainment, Health, Study, Other
- Income: Salary, Side Income, Gift, Other

## Data Flow

The app stores data in browser local storage. On startup it loads saved records and budgets, falling back to seeded sample data if no saved data exists. Any add, edit, delete, or budget change updates local state and persists the latest snapshot.

Derived views are calculated from records:

- Monthly income and expense totals.
- Remaining budget and budget usage percentage.
- Category spending totals.
- Seven-day spending trend.
- Recent bill list.

## Components

Suggested component boundaries:

- App shell: bottom navigation and active tab state.
- Home summary: monthly metrics and budget progress.
- Record form: income or expense entry.
- Budget editor: total and category budget controls.
- Analysis dashboard: charts and summary insights.
- Transaction list: reusable list for recent and filtered records.
- Storage helpers: load, save, and reset local data.
- Analytics helpers: date filtering, totals, trends, and category aggregation.

## Error Handling

The app should prevent invalid records:

- Amount must be greater than zero.
- Category is required.
- Date is required.

When local storage is unavailable or corrupted, the app should fall back to sample data and avoid crashing. Budget warnings should be visual and non-blocking.

## Testing And Verification

Manual verification should cover:

- App loads on a mobile-sized viewport.
- User can add an expense and an income.
- Home totals update after adding a record.
- Monthly budget can be changed.
- Category budget status updates based on expenses.
- Analysis charts and category summaries update from records.
- Data persists after page reload.

Automated tests, if the project setup supports them, should focus on analytics helpers and storage fallback behavior.
