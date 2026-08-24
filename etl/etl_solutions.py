"""
ETL PRACTICE - SOLUTIONS
=========================
Full worked version of etl_practice.py. Try the exercises yourself first!
Run this directly to see the whole pipeline work end to end:
    python etl_solutions.py
"""

import pandas as pd
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def extract_orders(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["unit_price"] = (
        df["unit_price"].astype(str).str.replace("$", "", regex=False).astype(float)
    )
    df["order_date"] = pd.to_datetime(df["order_date"], format="mixed")
    df["missing_customer"] = df["customer_id"].isna()
    df["quantity"] = df["quantity"].fillna(1)
    return df


def extract_customers(path: Path) -> pd.DataFrame:
    with open(path) as f:
        data = json.load(f)
    df = pd.json_normalize(data, sep="_")
    df["tags"] = df["tags"].apply(lambda t: ",".join(t) if isinstance(t, list) else "")
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    df["email"] = df["email"].fillna("unknown")
    return df


def extract_products(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def transform_merge(orders: pd.DataFrame, customers: pd.DataFrame,
                     products: pd.DataFrame) -> pd.DataFrame:
    merged = pd.merge(orders, customers, on="customer_id", how="left")
    merged = pd.merge(merged, products, on="product_id", how="left")
    merged["line_total"] = merged["quantity"] * merged["unit_price"]
    return merged


def transform_customer_summary(merged: pd.DataFrame) -> pd.DataFrame:
    valid = merged[(~merged["missing_customer"]) & (merged["status"] != "cancelled")]
    summary = (
        valid.groupby(["customer_id", "name"])
        .agg(order_count=("order_id", "count"), total_spend=("line_total", "sum"))
        .reset_index()
        .sort_values("total_spend", ascending=False)
    )
    return summary


def transform_category_month_pivot(merged: pd.DataFrame) -> pd.DataFrame:
    valid = merged[merged["status"] != "cancelled"].copy()
    valid["month"] = valid["order_date"].dt.strftime("%Y-%m")
    pivot = pd.pivot_table(
        valid, index="category", columns="month",
        values="line_total", aggfunc="sum", fill_value=0,
    )
    return pivot


def load_results(customer_summary: pd.DataFrame, out_path: Path) -> None:
    assert customer_summary["customer_id"].notna().all(), "found null customer_id"
    assert (customer_summary["total_spend"] >= 0).all(), "found negative total_spend"
    customer_summary.to_csv(out_path, index=False)


def main():
    orders = extract_orders(DATA_DIR / "orders.csv")
    customers = extract_customers(DATA_DIR / "customers.json")
    products = extract_products(DATA_DIR / "products.csv")
    merged = transform_merge(orders, customers, products)
    summary = transform_customer_summary(merged)
    pivot = transform_category_month_pivot(merged)

    print("Customer summary:")
    print(summary.to_string(index=False))
    print("\nCategory x month revenue:")
    print(pivot)

    out_path = Path(__file__).parent / "customer_summary.csv"
    load_results(summary, out_path)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
