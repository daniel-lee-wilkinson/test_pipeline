"""
ETL PRACTICE: Extract, Transform, Load
========================================
Goal: build a small pipeline that reads a messy CSV of orders, a nested
JSON of customers, and a clean CSV of products, then cleans, joins,
reshapes, and aggregates them into a final report.

How to use this file:
1. Read each function's docstring + hint.
2. Fill in the tasks.
3. Run this file: `python etl_practice.py`
   Each step prints a check so you know if you're on track.
4. Stuck? Open etl_solutions.py for a full worked version -
   but try for real first, that's where the learning happens.

Data files (in ./data/):
- orders.csv     -> messy: prices like "$19.99" or "19.99", dates in
                     3 different formats, some missing customer_id/quantity
- customers.json -> nested address dict + tags list, one missing email
- products.csv   -> clean lookup table: product_id, category, base_price
"""

import pandas as pd
import json
from pathlib import Path

DATA_DIR = "/home/daniel/PycharmProjects/test_pipeline/etl"


# ---------------------------------------------------------------------------
# STEP 1: EXTRACT - orders.csv
# ---------------------------------------------------------------------------
def extract_orders(path: Path) -> pd.DataFrame:
    """
    Read orders.csv and clean it up so downstream steps can rely on it:
      - unit_price: strip any "$" and convert to float
      - order_date: parse the 3 different date formats into real
        datetime objects (hint: pandas can often infer this for you)
      - quantity: missing quantities should become 1 (a reasonable default
        for this exercise - a real pipeline might flag these instead)
      - keep rows with missing customer_id, but flag them in a new
        boolean column `missing_customer`

    Return a DataFrame with the same columns as the CSV (order_id,
    customer_id, product_id, quantity, unit_price, order_date, status,
    missing_customer) but cleaned as described above.

    HINT:
      - pd.read_csv(path)
      - df['unit_price'].astype(str).str.replace('$', '', regex=False).astype(float)
      - pd.to_datetime(df['order_date'], format='mixed') handles multiple
        formats in one column (pandas >= 2.0). If that's unavailable,
        try errors='coerce' with a couple of explicit formats and combine.
      - df['missing_customer'] = df['customer_id'].isna()
      - df['quantity'] = df['quantity'].fillna(1)
    """

    df = pd.read_csv(path)
    df["unit_price"] = df["unit_price"].astype(str).str.replace("$", "", regex=False).astype(float)
    df["order_date"] = pd.to_datetime(df["order_date"], format="mixed")
    df["missing_customer"] = df["customer_id"].isna()
    df["quantity"] = df["quantity"].fillna(1)
    return df


# ---------------------------------------------------------------------------
# STEP 2: EXTRACT - customers.json
# ---------------------------------------------------------------------------
def extract_customers(path: Path) -> pd.DataFrame:
    """
    Read customers.json and flatten it into a tabular DataFrame:
      - the nested `address` dict should become separate columns:
        address_street, address_city, address_state, address_zip
      - `tags` (a list) should become a single comma-separated string
        column, e.g. ["newsletter", "vip"] -> "newsletter,vip"
      - `signup_date` should be a real datetime
      - missing `email` should become the string "unknown"

    Return columns: customer_id, name, email, signup_date,
    address_street, address_city, address_state, address_zip, tags

    HINT:
      - json.load(open(path)) gives you a list of dicts
      - pd.json_normalize(data, sep='_') flattens nested dicts
        automatically into address_street, address_city, etc.
      - df['tags'].apply(lambda t: ','.join(t))
      - df['email'].fillna('unknown')
    """

    list_dicts = json.load(open(path))
    df = pd.json_normalize(list_dicts, sep="_")
    df['tags'].apply(lambda t: ','.join(t))
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    df["email"].fillna("unknown")
    return df


# ---------------------------------------------------------------------------
# STEP 3: EXTRACT - products.csv
# ---------------------------------------------------------------------------
def extract_products(path: Path) -> pd.DataFrame:
    """
    Read products.csv. It's already clean - just load it.
    Return columns: product_id, product_name, category, base_price
    """

    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# STEP 4: TRANSFORM - join everything together
# ---------------------------------------------------------------------------
def transform_merge(orders: pd.DataFrame, customers: pd.DataFrame,
                     products: pd.DataFrame) -> pd.DataFrame:
    """
    Join the three DataFrames into one wide table:
      - left-join orders -> customers on customer_id
      - left-join the result -> products on product_id
      - add a new column `line_total` = quantity * unit_price

    Use LEFT joins (not inner) so orders with a missing/unknown
    customer_id still survive - their customer columns will just be NaN.

    HINT:
      - pd.merge(orders, customers, on='customer_id', how='left')
      - pd.merge(result, products, on='product_id', how='left')
      - result['line_total'] = result['quantity'] * result['unit_price']
    """
    result = pd.merge(orders, customers, on='customer_id', how='left')
    all = pd.merge(result, products, on="product_id", how="left")
    all["line_total"] = all["quantity"] * all["unit_price"]
    return all



# ---------------------------------------------------------------------------
# STEP 5: TRANSFORM - aggregate by customer
# ---------------------------------------------------------------------------
def transform_customer_summary(merged: pd.DataFrame) -> pd.DataFrame:
    """
    Build a per-customer summary, EXCLUDING rows with missing_customer=True
    and status='cancelled' (cancelled orders shouldn't count as spend).

    Return columns: customer_id, name, order_count, total_spend
    sorted by total_spend descending.

    HINT:
      - filter: df[(~df['missing_customer']) & (df['status'] != 'cancelled')]
      - .groupby(['customer_id', 'name']).agg(
            order_count=('order_id', 'count'),
            total_spend=('line_total', 'sum')
        ).reset_index()
      - .sort_values('total_spend', ascending=False)
    """

    valid = merged[(~merged["missing_customer"]) & (merged["status"] != "cancelled")]
    summary = (
        valid.groupby(["customer_id", "name"])
        .agg(order_count=("order_id", "count"), total_spend=("line_total", "sum"))
        .reset_index()
        .sort_values("total_spend", ascending=False)
    )
    return summary

# ---------------------------------------------------------------------------
# STEP 6: TRANSFORM - reshape into a category x month revenue pivot
# ---------------------------------------------------------------------------
def transform_category_month_pivot(merged: pd.DataFrame) -> pd.DataFrame:
    """
    Build a pivot table: rows = category, columns = order month
    (as 'YYYY-MM' strings), values = sum of line_total.
    Exclude cancelled orders. Fill missing combinations with 0.

    HINT:
      - month = merged['order_date'].dt.strftime('%Y-%m')
      - pd.pivot_table(df, index='category', columns=month,
                        values='line_total', aggfunc='sum', fill_value=0)
    """

    valid = merged[merged["status"] != "cancelled"]
    month = valid["order_date"].dt.strftime("%Y-%m")
    df = pd.pivot_table(
        valid, index="category", columns=month,
        values="line_total", aggfunc="sum", fill_value=0
    )
    return df

# ---------------------------------------------------------------------------
# STEP 7: LOAD - write results out + basic validation
# ---------------------------------------------------------------------------
def load_results(customer_summary: pd.DataFrame, out_path: Path) -> None:
    """
    Before writing, VALIDATE:
      - no nulls in customer_id or total_spend
      - total_spend is never negative
    Raise an AssertionError with a clear message if a check fails.

    Then write customer_summary to out_path as CSV (no index column).

    HINT:
      - assert customer_summary['customer_id'].notna().all(), "..."
      - assert (customer_summary['total_spend'] >= 0).all(), "..."
      - customer_summary.to_csv(out_path, index=False)
    """
    assert customer_summary["customer_id"].notna().all(), "found null customer_id"
    assert (customer_summary["total_spend"] >= 0).all(), "found negative total_spend"
    customer_summary.to_csv(out_path, index=False)



# ---------------------------------------------------------------------------
# PIPELINE RUNNER - don't edit below, just run the file
# ---------------------------------------------------------------------------
def main():
    print("Step 1: extract_orders...")
    orders = extract_orders("orders.csv")
    assert orders["unit_price"].dtype.kind == "f", "unit_price should be float"
    assert pd.api.types.is_datetime64_any_dtype(orders["order_date"]), "order_date should be datetime"
    print(f"  OK - {len(orders)} orders, {orders['missing_customer'].sum()} missing customer_id\n")

    print("Step 2: extract_customers...")
    customers = extract_customers("customers.json")
    assert "address_city" in customers.columns, "address should be flattened"
    print(f"  OK - {len(customers)} customers\n")

    print("Step 3: extract_products...")
    products = extract_products("products.csv")
    print(f"  OK - {len(products)} products\n")

    print("Step 4: transform_merge...")
    merged = transform_merge(orders, customers, products)
    assert "line_total" in merged.columns
    assert len(merged) == len(orders), "left join should keep every order row"
    print(f"  OK - merged shape {merged.shape}\n")

    print("Step 5: transform_customer_summary...")
    summary = transform_customer_summary(merged)
    print(summary.to_string(index=False))
    print()

    print("Step 6: transform_category_month_pivot...")
    pivot = transform_category_month_pivot(merged)
    print(pivot)
    print()

    print("Step 7: load_results...")
    out_path = Path(__file__).parent / "customer_summary.csv"
    load_results(summary, out_path)
    print(f"  OK - wrote {out_path}")


if __name__ == "__main__":
    main()
