"""
bad_pipeline.py

This script "works" in the sense that it was written to produce a report,
but it has a lot of problems - some are style/structure issues, and at
least one is an honest-to-god bug that produces wrong numbers (or crashes,
depending on how far it gets before you fix things).

YOUR TASK: refactor this into a clean pipeline. Don't just make it run -
make it correct. See README.md for the full checklist and the target
function structure to aim for.

Do not "fix" this file by deleting the mess and starting over blind -
read through it first and figure out what it's actually trying to do,
the same way you'd approach an ugly script you inherited at a job.
"""

import pandas as pd
import json

KG_PER_KTON = 1_000_000

SHIPMENTS_PATH = "bad_pipeline/shipments.csv"
WH_PATH = "bad_pipeline/warehouses.json"
SKUS_PATH = "bad_pipeline/skus.csv"
REPORT_OUT_PATH = "bad_pipeline/shipment_report.csv"



def parse_weight_to_kg(value):
    value = str(value).strip().lower()
    if "lb" in value:
        pounds = float(value.replace("lb", "").strip())
        return pounds * 0.453592   # conversion factor here
    else:
        return float(value.replace("kg", "").strip())


def extract_shipments(path):
    df = pd.read_csv(path)
    df["quantity"] = (
        df["quantity"].astype(str).str.replace(",", "", regex=False).astype(int)
    )
    df["weight_kg"] = df["weight"].apply(parse_weight_to_kg)

    df["ship_date"] = pd.to_datetime(df["ship_date"], format="mixed")
    df["missing_warehouse"] = df["warehouse_id"].isna()
    return df



def read_json_to_df(path):
    with open(path) as f:
        data = json.load(f)
    return pd.json_normalize(data, sep="_")


def combine_dfs(shipments_df, wh_df, skus_df):
    result = pd.merge(shipments_df, wh_df, on="warehouse_id", how="left")
    final_df = pd.merge(result, skus_df, on="sku_id", how="left")
    return final_df

def calc_tot_weight_by_region_ktons(df):
    open_orders = df[df["status"] != "cancelled"]
    total_weight_by_region = open_orders.groupby("region")["total_weight"].sum()
    total_weight_by_region_rounded = round(total_weight_by_region, 2)
    total_weight_by_region_ktons = total_weight_by_region_rounded / KG_PER_KTON
    return total_weight_by_region_ktons.reset_index()  # -> columns: region, total_weight

def generate_report(df):
    report_df = calc_tot_weight_by_region_ktons(df)
    assert report_df.notna().all().all(), "found null values in region summary"
    assert (report_df["total_weight"] >= 0).all(), "found negative weight"
    report_df.to_csv(REPORT_OUT_PATH, index=False)


def main(wh_path, skus_path, shipments_path):
    wh_df = read_json_to_df(wh_path)
    skus_df = pd.read_csv(skus_path)
    shipments_df = extract_shipments(shipments_path)

    all_df = combine_dfs(shipments_df, wh_df, skus_df)
    all_df["total_weight"] = all_df["quantity"] * all_df["weight_kg"]

    generate_report(all_df)


if __name__ == "__main__":
    main(WH_PATH, SKUS_PATH, SHIPMENTS_PATH)