# ETL Practice: Extract, Transform, Load

A small self-contained pipeline exercise using pandas. Mixed data sources
on purpose: a messy CSV, a nested JSON file, and a clean lookup CSV.

## Setup
```
pip install pandas
```

## Files
- `data/orders.csv` — messy: `$`-prefixed prices, 3 different date formats,
  missing customer_id and quantity values
- `data/customers.json` — nested address object + tags list, one missing email
- `data/products.csv` — clean product lookup table
- `etl_practice.py` — **start here.** 7 TODO functions, each with a
  docstring spec and a hint. Run it to get pass/fail checks as you go.
- `etl_solutions.py` — full worked solution. Try the exercise first.

## Run
```
python etl_practice.py      # your version, fails until TODOs are filled in
python etl_solutions.py     # reference version, works end to end
```

## What it covers
1. **Extract** — reading CSV/JSON, cleaning currency strings, parsing
   mixed date formats, flattening nested JSON, filling missing values
2. **Transform** — left joins across 3 tables, derived columns,
   groupby aggregation, pivot tables
3. **Load** — validation asserts before writing output

## Suggested order
Do the functions top to bottom — each one builds on the last, and
`main()` in `etl_practice.py` checks your work at each step as you run it.
