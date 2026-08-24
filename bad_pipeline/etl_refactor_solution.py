"""
etl_refactor_solution.py

A clean, modular refactor of bad_pipeline.py. Try your own refactor
first - this is here for comparison once you're done, or if you get
stuck on a specific step.

Key fixes beyond restructuring:
  - weight cleaning now strips BOTH "kg" and "lb" AND converts lb -> kg,
    so total_weight is in consistent units (bad_pipeline.py either
    crashed on "lb" values or, if you patched the crash without adding
    the unit conversion, silently mixed kg and lb in the same sum)
  - warehouse join is a LEFT join with a `missing_warehouse` flag,
    instead of an inner join that silently drops shipments with no
    warehouse_id
"""

import json
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_PATH = Path(__file__).parent / "shipment_report.csv"

LB_TO_KG = 0.45359237


def extract_shipments(path: Path) -> pd.DataFrame:
    """Read shipments.csv and clean quantity, weight, and ship_date."""
    df = pd.read_csv(path)

    df["quantity"] = (
        df["quantity"].astype(str).str.replace(",", "", regex=False).astype(float)
    )

    df["weight_kg"] = df["weight"].apply(_parse_weight_to_kg)
    df = df.drop(columns=["weight"])

    df["ship_date"] = pd.to_datetime(df["ship_date"], format="mixed")

    df["missing_warehouse"] = df["warehouse_id"].isna()

    return df


def _parse_weight_to_kg(raw: str) -> float:
    """Parse a weight string like '500kg' or '1100 lb' into a float in kg."""
    text = str(raw).strip().lower()
    if "lb" in text:
        number = float(text.replace("lb", "").strip())
        return number * LB_TO_KG
    return float(text.replace("kg", "").strip())


def extract_warehouses(path: Path) -> pd.DataFrame:
    """Read warehouses.json and flatten the nested manager object."""
    with open(path) as f:
        data = json.load(f)
    df = pd.json_normalize(data, sep="_")
    df["manager_email"] = df["manager_email"].fillna("unknown")
    return df


def extract_skus(path: Path) -> pd.DataFrame:
    """Read the SKU catalog. Already clean."""
    return pd.read_csv(path)


def transform_merge(shipments: pd.DataFrame, warehouses: pd.DataFrame,
                     skus: pd.DataFrame) -> pd.DataFrame:
    """Left-join shipments to warehouses and skus, then add total_weight_kg."""
    merged = pd.merge(shipments, warehouses, on="warehouse_id", how="left")
    merged = pd.merge(merged, skus, on="sku_id", how="left")
    merged["total_weight_kg"] = merged["quantity"] * merged["weight_kg"]
    return merged


def transform_region_summary(merged: pd.DataFrame) -> pd.DataFrame:
    """Total shipped weight by region, excluding cancelled and unmatched-warehouse rows."""
    valid = merged[(~merged["missing_warehouse"]) & (merged["status"] != "cancelled")]
    summary = (
        valid.groupby("region")["total_weight_kg"]
        .sum()
        .reset_index()
        .sort_values("total_weight_kg", ascending=False)
    )
    return summary


def load_results(merged: pd.DataFrame, out_path: Path) -> None:
    """Validate and write the full shipment report (not just the summary)."""
    assert merged["shipment_id"].notna().all(), "found null shipment_id"
    assert (merged["quantity"] >= 0).all(), "found negative quantity"
    merged.to_csv(out_path, index=False)


def main():
    shipments = extract_shipments(DATA_DIR / "shipments.csv")
    warehouses = extract_warehouses(DATA_DIR / "warehouses.json")
    skus = extract_skus(DATA_DIR / "skus.csv")

    merged = transform_merge(shipments, warehouses, skus)
    summary = transform_region_summary(merged)

    logger.info("Region summary (kg shipped, excludes cancelled/unmatched):")
    logger.info("\n%s", summary.to_string(index=False))

    n_missing = merged["missing_warehouse"].sum()
    if n_missing:
        logger.warning("%d shipments have no matching warehouse_id", n_missing)

    load_results(merged, OUTPUT_PATH)
    logger.info("Wrote %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
