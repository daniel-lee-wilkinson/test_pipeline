# Data Pipeline Refactoring Exercises

This folder groups several self-contained refactoring exercises in one place.
Each exercise starts with a deliberately messy pipeline script, and the
`solutions/` folder contains a completed refactor for comparison.

## Exercises
- `sales_pipeline_exercise.py` — sales ETL with validation, currency conversion,
  and summary reporting
- `inventory_pipeline_exercise.py` — warehouse inventory reconciliation with
  stock tracking and discrepancy handling
- `web_log_pipeline_exercise.py` — web log processing with parsing,
  classification, and alert generation

## Solutions
- `solutions/sales_pipeline_solution.py`
- `solutions/inventory_pipeline_solution.py`
- `solutions/web_log_pipeline_solution.py`

## How to use
1. Pick an `*_exercise.py` file and run it.
2. Refactor the script into smaller, testable units.
3. Compare your result with the matching file in `solutions/`.

These exercises are copies of the existing standalone practice pipelines so they
can be used from one dedicated folder.
