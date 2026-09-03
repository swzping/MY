# Jizhang Report Analysis Design

## Goal

Upgrade the existing Analysis tab into a monthly and yearly report center powered by the user's imported `history.xlsx` records and any records added inside the app.

## Source Data

`history.xlsx` contains two sheets:

- `收入`: 171 income rows.
- `支出`: 2221 expense rows.

Both sheets use the same core fields: `交易类型`, `日期`, `一级分类`, `二级分类`, `金额`, and `备注`. The app should convert these into the existing `Transaction` shape:

- `type`: `income` or `expense`.
- `amount`: numeric `金额`.
- `category`: prefer `一级分类`; keep original Chinese category labels.
- `date`: `YYYY-MM-DD`, derived from `日期`.
- `note`: combine meaningful `二级分类` and `备注` text when present.

The converted records become part of the app's initial sample data. Locally saved user records still take precedence through the existing AsyncStorage flow.

## User Experience

Keep the existing bottom navigation and reuse the current `analysis` tab. The tab title becomes a report-oriented analysis page.

The page has a compact segmented control:

- `月度`
- `年度`

Default period selection uses the latest date available in the loaded records.

Monthly mode shows:

- Income, expense, net amount, and savings rate.
- Daily expense trend for the selected month.
- Expense category ranking for the selected month.
- Recent records within the selected month.

Yearly mode shows:

- Income, expense, net amount, and savings rate for the selected year.
- Month-by-month income, expense, and net summary.
- Expense category ranking for the selected year.
- Highest-spend months.

## Architecture

Add report-specific analytics functions in `src/lib/analytics.ts` rather than embedding calculations in `App.tsx`.

Planned helpers:

- `getLatestRecordDate(records)`
- `getMonthlyReport(records, monthKey)`
- `getYearlyReport(records, year)`

These helpers aggregate existing `Transaction[]` data and return simple typed report objects for the UI.

## UI Components

Update `AnalysisScreen` in `App.tsx` only. Reuse existing local UI primitives where practical:

- `SegmentButton`
- `MetricCard`
- `ProgressBar`
- `TransactionList`
- `SectionHeader`

Add small visual components only when needed for report clarity, such as month bars, daily bars, and category rows.

## Error Handling

If a selected month or year has no records, show empty-state text instead of blank charts.

If income is zero, savings rate should be `0` rather than causing division errors.

Invalid or missing dates should be ignored by report aggregation.

## Testing

Add focused tests in `src/lib/analytics.test.ts` before implementation:

- Monthly report totals, daily trend, and category ranking.
- Yearly report totals and monthly summaries.
- Latest date selection.
- Zero-income savings rate behavior.

Run:

```bash
npm test -- src/lib/analytics.test.ts
npm run typecheck
```
