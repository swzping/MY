# A-share EOD Pick Execution And Evaluation Design

## Goal

Make historical training, daily paper recommendations, and optimizer validation
comparable under one auditable execution and evaluation contract. This phase does
not change factor definitions, weights, or selection thresholds.

## Scope

Add an execution-and-evaluation boundary that receives a selected candidate and
its market data, then returns a normalized trade outcome or an explicit
non-execution reason. The boundary will be used by backtesting, live-paper
validation, and optimizer candidate evaluation.

The common contract will record:

- Signal date and selected timestamp.
- Intended tail-window entry price, its source, and fallback status.
- Next-trading-day exit price and its source.
- Execution eligibility, including suspension and limit-up/limit-down checks.
- Configured commission, stamp duty, and slippage in gross and net returns.
- A structured non-execution reason when either leg cannot be filled.

## Execution Rules

The default paper model is a long position opened at the configured tail entry
window on T and exited at the next trading day's opening auction price on T+1.
The evaluator applies adverse slippage on both legs and trading costs only to
filled trades. A missing or invalid price, suspension, or an unfillable limit
condition produces a skipped sample rather than an assumed fill.

The evaluator distinguishes a true strategy empty day from a selected but
unfillable candidate. This prevents coverage, win rate, and average return from
silently mixing signal quality with data or execution failures.

## Time-Split Validation

Optimizer candidate generation uses only the earlier chronological training
partition. Candidate acceptance is evaluated only on the later validation
partition. The production configuration may change only when the candidate meets
all validation gates relative to the incumbent:

- Net average return does not decline.
- Maximum drawdown and maximum consecutive loss do not worsen beyond configured
  tolerance.
- Participation remains within the configured range.
- The result is based on enough executable validation trades.

The existing full-history figures remain descriptive only. They cannot be used as
the acceptance criterion for a configuration update.

## Metrics And Reporting

Performance outputs will publish gross and net results separately, plus selected
days, executable trades, strategy empty days, skipped executions, execution
coverage, win rate, average return, cumulative return, maximum drawdown, and
maximum consecutive loss. Every summary is segmented into historical training,
out-of-sample validation, and live-paper samples.

The report will disclose the execution-model parameters and any data fallback so
an apparent improvement can be traced to a signal change rather than a pricing
assumption.

## Components

`execution_model` will own price selection, fill eligibility, cost application,
and normalized outcome creation. `backtest_runner` and `validator` will call it
instead of independently deriving returns. `optimizer` will consume the
normalized outcomes and time-split metrics. `feedback_loop` and
`report_generator` will render the common metrics without recomputing returns.

The persisted trade and sample schemas remain backward compatible: new fields
are additive, while older records without execution metadata are labelled as
legacy and excluded from strict execution-quality gates.

## Error Handling

Failures in a single symbol or date must create an auditable skipped outcome and
continue the run. A run-level data-source failure is reported with source and
affected dates; it must not be converted to a successful empty-day result.

## Tests

Tests will cover adverse entry/exit slippage, cost arithmetic, limit and
suspension skips, missing-price fallbacks, separation of empty versus skipped
days, chronological split isolation, optimizer rejection on weaker net
out-of-sample results, and report metric segmentation.

## Non-Goals

This phase does not tune factors, broaden the stock universe, add a new model,
or make real trades. Those decisions follow only after the new metrics establish
a reliable baseline.
