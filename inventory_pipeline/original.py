"""
ETL Pipeline - Warehouse Inventory Reconciliation

Extracts raw inventory scan records (simulated, e.g. from handheld
barcode scanners across multiple warehouses), transforms them into
reconciled stock movements (validating, computing running stock levels,
flagging discrepancies), and loads the result into a summary report +
a reorder list.

NOTE: This script works, but it has a bunch of rough edges left in on
purpose (it's meant to be refactored).
"""

import random
import datetime

# ---------------------------------------------------------------------------
# Config, sitting around as globals
# ---------------------------------------------------------------------------
REORDER_THRESHOLD = 15
MAX_DAILY_MOVEMENT = 500
WAREHOUSES = ["WH-EAST", "WH-WEST", "WH-CENTRAL"]
STARTING_STOCK = {
    "SKU-1001": 120,
    "SKU-1002": 45,
    "SKU-1003": 300,
    "SKU-1004": 18,
    "SKU-1005": 60,
}

stock_levels = dict(STARTING_STOCK)
discrepancies = []
records_seen = 0


# ---------------------------------------------------------------------------
# EXTRACT
# ---------------------------------------------------------------------------
def generate_dummy_scans(n=50):
    """Fakes what would come from handheld scanner exports across warehouses."""
    random.seed(21)
    skus = list(STARTING_STOCK.keys())

    scans = []
    for i in range(n):
        sku = random.choice(skus)
        movement_type = random.choice(["inbound", "outbound", "inbound", "outbound", "adjustment"])
        qty = random.choice([1, 2, 5, 10, 20, 50, 999, -5])  # 999 and -5 are bad data
        wh = random.choice(WAREHOUSES)
        ts = datetime.datetime(2026, 4, 1) + datetime.timedelta(hours=i)

        scan = {
            "scan_id": f"SCAN-{i:04d}",
            "sku": sku,
            "warehouse": wh,
            "movement_type": movement_type,
            "quantity": qty,
            "scanned_at": ts.isoformat(),
            "scanned_by": random.choice(["emp-101", "emp-104", "emp-119", ""]),
        }
        # occasionally corrupt the sku entirely
        if random.random() < 0.06:
            scan["sku"] = "UNKNOWN"
        scans.append(scan)
    return scans


def extract():
    print("Pulling scan records from warehouses...")
    data = generate_dummy_scans(50)
    print(f"Pulled {len(data)} scan records")
    return data


# ---------------------------------------------------------------------------
# TRANSFORM
# ---------------------------------------------------------------------------
def process_scan(scan):
    """Validates a scan, applies it to stock levels, and flags anything weird."""
    global records_seen

    records_seen += 1

    if scan["sku"] not in STARTING_STOCK:
        discrepancies.append(f"{scan['scan_id']}: unknown SKU '{scan['sku']}'")
        return None

    if not scan["scanned_by"]:
        discrepancies.append(f"{scan['scan_id']}: missing employee id")
        return None

    qty = scan["quantity"]

    if abs(qty) > MAX_DAILY_MOVEMENT:
        discrepancies.append(f"{scan['scan_id']}: implausible quantity {qty}")
        return None

    sku = scan["sku"]

    if scan["movement_type"] == "inbound":
        if qty < 0:
            discrepancies.append(f"{scan['scan_id']}: negative quantity on inbound scan")
            return None
        stock_levels[sku] += qty
    elif scan["movement_type"] == "outbound":
        if qty < 0:
            discrepancies.append(f"{scan['scan_id']}: negative quantity on outbound scan")
            return None
        if stock_levels[sku] - qty < 0:
            discrepancies.append(f"{scan['scan_id']}: outbound would take {sku} negative, skipping")
            return None
        stock_levels[sku] -= qty
    elif scan["movement_type"] == "adjustment":
        stock_levels[sku] += qty  # adjustments can be positive or negative
    else:
        discrepancies.append(f"{scan['scan_id']}: unknown movement type '{scan['movement_type']}'")
        return None

    result = dict(scan)
    result["stock_after"] = stock_levels[sku]
    return result


def transform(scans):
    print("Reconciling stock movements...")
    processed = []
    for scan in scans:
        result = process_scan(scan)
        if result is not None:
            processed.append(result)
    print(f"Processed {len(processed)} of {records_seen} scans ({len(discrepancies)} discrepancies)")
    return processed


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------
def load(processed_scans):
    """Loads final stock levels and builds a reorder list."""
    print("Loading final stock levels...")

    reorder_list = []
    for sku, level in stock_levels.items():
        if level < REORDER_THRESHOLD:
            reorder_list.append({"sku": sku, "current_stock": level})

    by_warehouse = {}
    for scan in processed_scans:
        wh = scan["warehouse"]
        if wh not in by_warehouse:
            by_warehouse[wh] = 0
        by_warehouse[wh] += 1

    print(f"Loaded stock levels for {len(stock_levels)} SKUs")
    return reorder_list, by_warehouse


def print_report(reorder_list, by_warehouse):
    print("\n--- Final Stock Levels ---")
    for sku, level in stock_levels.items():
        print(f"{sku:10s} stock={level}")

    print("\n--- Reorder List ---")
    if not reorder_list:
        print("Nothing to reorder.")
    for item in reorder_list:
        print(f" - {item['sku']}: only {item['current_stock']} left")

    print("\n--- Scans by Warehouse ---")
    for wh, count in by_warehouse.items():
        print(f"{wh:12s} {count} scans")

    print(f"\n--- Discrepancies ({len(discrepancies)}) ---")
    for d in discrepancies:
        print(f" - {d}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    raw = extract()
    processed = transform(raw)
    reorder_list, by_warehouse = load(processed)
    print_report(reorder_list, by_warehouse)
    return reorder_list, by_warehouse


if __name__ == "__main__":
    main()