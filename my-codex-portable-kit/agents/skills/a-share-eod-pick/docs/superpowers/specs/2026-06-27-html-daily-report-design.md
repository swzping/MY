# HTML Daily Report Design

## Goal

When any daily strategy report is generated, the workspace should save both the existing Markdown report and a same-date HTML report.

## Scope

- Keep `reports/YYYY-MM-DD.md` as the canonical text report.
- Add `reports/YYYY-MM-DD.html` during the same `report_generator.generate(...)` call.
- Build the HTML from the same data files and `selection_result` used by the Markdown report.
- Render historical training and live paper records as browser tables with search, per-page controls, and previous/next pagination.
- Use a self-contained HTML file with inline CSS and JavaScript so it opens directly from disk.
- Do not add a web server, external CDN dependency, or report center index page in this pass.

## Interface

- `report_generator.generate(selection_result)` continues returning the Markdown `Path`.
- New helper functions may expose `render_html_report(...)`, `save_html_report(...)`, and row-building helpers for tests.
- Existing CLI commands need no new arguments because they already call `report_generator.generate(...)`.

## Visual Direction

The page is a compact operations dashboard: calm, high-density, readable, and table-first. Summary cards surface daily recommendation, performance, alerts, and feedback. Historical sections use restrained styling and fixed table controls suited for repeated inspection.

## Testing

- Unit test that `generate(...)` writes both `.md` and `.html`.
- Unit test that the HTML contains the search box, page-size control, pagination controls, and embedded historical rows.
- Existing report rendering tests should continue to pass.
