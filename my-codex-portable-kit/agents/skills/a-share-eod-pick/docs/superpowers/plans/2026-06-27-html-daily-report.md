# HTML Daily Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a same-date self-contained HTML report whenever a Markdown daily report is generated.

**Architecture:** Extend `scripts/report_generator.py` with HTML rendering and saving helpers that reuse the existing loaders and formatting helpers. Keep CLI behavior stable by making `generate(...)` save both outputs while returning the Markdown path.

**Tech Stack:** Python standard library, existing JSON data files, inline HTML/CSS/JavaScript.

---

### Task 1: Lock HTML Output Behavior

**Files:**
- Modify: `tests/test_feedback_loop.py`

- [ ] Add a test that calls `report_generator.generate(...)` in a temporary reports directory and asserts both `2026-06-26.md` and `2026-06-26.html` exist.
- [ ] Add a test that seeds historical and live samples, calls `render_html_report(...)`, and asserts the HTML includes `historySearch`, `historyPageSize`, `data-table="historical"`, `data-table="live"`, and sample stock data.
- [ ] Run `python3 -m unittest tests.test_feedback_loop.ReportFeedbackSummaryTests -v` and confirm the new tests fail because HTML helpers are missing.

### Task 2: Implement Self-Contained HTML Rendering

**Files:**
- Modify: `scripts/report_generator.py`

- [ ] Add `_html_escape`, `_json_script`, and table row-building helpers.
- [ ] Add `render_html_report(selection_result)` that renders summary sections plus two interactive tables.
- [ ] Add `save_html_report(content, date_str)` and update `generate(...)` to save Markdown and HTML.
- [ ] Run `python3 -m unittest tests.test_feedback_loop.ReportFeedbackSummaryTests -v` and confirm the tests pass.

### Task 3: Verify Existing Report Tests

**Files:**
- Existing tests only.

- [ ] Run `python3 -m unittest tests.test_feedback_loop tests.test_training_split -v`.
- [ ] If unrelated existing dirty-worktree failures appear, report them with exact failing test names and do not revert user changes.
