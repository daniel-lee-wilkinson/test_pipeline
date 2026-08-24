# Refactoring Practice: Shipment ETL

`bad_pipeline.py` works just well enough to be dangerous - it's the kind
of script you might inherit at a job. Your task is to turn it into a
correct, well-structured pipeline.

## Setup
```
pip install pandas
```

## Files
- `data/shipments.csv` — messy: comma-formatted quantities ("1,200"),
  weights in mixed units ("500kg" / "1100 lb" / bare numbers), 3 date
  formats, 2 rows with missing warehouse_id
- `data/warehouses.json` — nested `manager` object per warehouse
- `data/skus.csv` — clean product catalog
- `bad_pipeline.py` — **start here.** Run it first and see what happens.
- `etl_refactor_solution.py` — reference version. Don't open until you're
  genuinely stuck or done.

## Step 1: Run it, read it, understand it
```
python bad_pipeline.py
```
It will crash. Before touching anything, read the whole script and
figure out what it's trying to accomplish end to end — extract 3
sources, join them, summarize weight by region, write a report.

## Step 2: Find the bugs (not just the crash)
The crash is the obvious problem. There's a second, quieter one that
won't throw an error - it'll just produce a wrong number. Both involve
the same block of code. Ask yourself: once weight values are parsed
into floats, are they actually all measuring the same unit?

There's also a data-loss issue in how shipments are joined to
warehouses - look at what happens to shipments with a missing
`warehouse_id` when you use `pd.merge(..., on="warehouse_id")` with
the default join type.

## Step 3: Refactor into this structure
Restructure into separate, testable functions (same extract →
transform → load shape you've used before):

```
extract_shipments(path)   -> clean quantity, weight (consistent units!), ship_date
extract_warehouses(path)  -> flatten nested manager object
extract_skus(path)        -> load, already clean
transform_merge(...)      -> LEFT joins + total_weight column
transform_region_summary(...) -> weight by region, excluding cancelled +
                                   rows with no matching warehouse
load_results(...)         -> validate, then write CSV
main()                     -> orchestrates, guarded by if __name__ == "__main__"
```

## General refactoring checklist to apply as you go
- [ ] No top-level executable code outside functions/`main()`
- [ ] No reused variable/function names that shadow each other (there's
      a function defined twice in the original — same name, different body)
- [ ] Use `pathlib.Path` instead of raw path strings
- [ ] Use a `with open(...)` context manager instead of manual open/close
- [ ] Replace the manual for-loop that pulls `manager["name"]` out of a
      dict with `pd.json_normalize`
- [ ] Give every column/variable a clear name (no `df2`, `x`, `y`, `tmp`)
- [ ] Decide LEFT vs INNER joins deliberately, and flag any rows that
      don't match instead of silently dropping them
- [ ] Replace `print()` debugging with either `return`ed values or
      `logging`
- [ ] Add a couple of `assert` validations before writing output
      (e.g. no null IDs, no negative quantities)
- [ ] `to_csv(..., index=False)` so you don't write a stray index column

## Run your version, then compare
```
python your_refactored_file.py
python etl_refactor_solution.py
```
The region totals should match between the two once your unit
conversion and join logic are correct.
