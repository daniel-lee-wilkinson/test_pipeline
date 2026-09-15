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
import logging
import time
from typing import Any

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

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

def get_duration(start_time: float) -> float:
	return time.time() - start_time

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
		warehouse = random.choice(WAREHOUSES)
		scanned_time = datetime.datetime(2026, 4, 1) + datetime.timedelta(hours=i)

		scan = {
			"scan_id": f"SCAN-{i:04d}",
			"sku": sku,
			"warehouse": warehouse,
			"movement_type": movement_type,
			"quantity": qty,
			"scanned_at": scanned_time.isoformat(),
			"scanned_by": random.choice(["emp-101", "emp-104", "emp-119", ""]),
		}
		# occasionally corrupt the sku entirely
		if random.random() < 0.06:
			scan["sku"] = "UNKNOWN"
		scans.append(scan)
	return scans


def extract(number_dummies = 50):
	logger.info("Pulling scan records from warehouses...")
	data = generate_dummy_scans(number_dummies)
	logger.info(f"Pulled {len(data)} scan records")
	return data


# ---------------------------------------------------------------------------
# TRANSFORM
# ---------------------------------------------------------------------------
def process_scan(scan, stock_levels):
    """Validates a scan, applies it to stock levels, and flags anything weird.
    Returns (result_dict_or_None, updated_stock_levels)."""
    global records_seen

    records_seen += 1
    qty_ = scan["quantity"]
    sku_ = scan["sku"]
    scan_id_ = scan['scan_id']
    scan_movement_type_ = scan["movement_type"]

    if sku_ not in STARTING_STOCK:
        discrepancies.append(f"{scan_id_}: unknown SKU '{sku_}'")
        return None, stock_levels

    if not scan["scanned_by"]:
        discrepancies.append(f"{scan_id_}: missing employee id")
        return None, stock_levels

    if abs(qty_) > MAX_DAILY_MOVEMENT:
        discrepancies.append(f"{scan_id_}: implausible quantity {qty_}")
        return None, stock_levels

    if scan_movement_type_ == "inbound":
        if qty_ < 0:
            discrepancies.append(f"{scan_id_}: negative quantity on inbound scan")
            return None, stock_levels
        stock_levels[sku_] += qty_

    elif scan_movement_type_ == "outbound":
        if qty_ < 0:
            discrepancies.append(f"{scan_id_}: negative quantity on outbound scan")
            return None, stock_levels
        if stock_levels[sku_] - qty_ < 0:
            discrepancies.append(f"{scan_id_}: outbound would take {sku_} negative, skipping")
            return None, stock_levels
        stock_levels[sku_] -= qty_

    elif scan_movement_type_ == "adjustment":
        stock_levels[sku_] += qty_

    else:
        discrepancies.append(f"{scan_id_}: unknown movement type '{scan_movement_type_}'")
        return None, stock_levels

    result = dict(scan)
    result["stock_after"] = stock_levels[sku_]
    return result, stock_levels

def transform(scans, stock_levels):
    logger.info("Reconciling stock movements...")
    processed = []
    for scan in scans:
        result, stock_levels = process_scan(scan, stock_levels)
        if result is not None:
            processed.append(result)
    logger.info(f"Processed {len(processed)} of {records_seen} scans ({len(discrepancies)} discrepancies)")
    return processed, stock_levels

# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------
def load(processed_scans, stock_levels):
	"""Loads final stock levels and builds a reorder list."""
	logger.info("Loading final stock levels...")

	reorder_list = []
	for sku, level in stock_levels.items():
		if level < REORDER_THRESHOLD:
			reorder_list.append({"sku": sku, "current_stock": level})

	by_warehouse = assign_warehouse(processed_scans)

	logger.info(f"Loaded stock levels for {len(stock_levels)} SKUs")
	return reorder_list, by_warehouse


def assign_warehouse(processed_scans) -> dict[Any, Any]:
	by_warehouse = {}
	for scan in processed_scans:
		wh = scan["warehouse"]
		if wh not in by_warehouse:
			by_warehouse[wh] = 0
		by_warehouse[wh] += 1
	return by_warehouse


def print_report(reorder_list, by_warehouse, stock_levels):
	logger.info("\n--- Final Stock Levels ---")
	for sku, level in stock_levels.items():
		logger.info(f"{sku:10s} stock={level}")

	logger.info("\n--- Reorder List ---")
	if not reorder_list:
		logger.info("Nothing to reorder.")
	for item in reorder_list:
		logger.info(f" - {item['sku']}: only {item['current_stock']} left")

	logger.info("\n--- Scans by Warehouse ---")
	for wh, count in by_warehouse.items():
		logger.info(f"{wh:12s} {count} scans")

	logger.info(f"\n--- Discrepancies ({len(discrepancies)}) ---")
	for d in discrepancies:
		logger.info(f" - {d}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    raw = extract()
    processed, final_stock = transform(raw, dict(STARTING_STOCK))
    reorder_list, by_warehouse = load(processed, final_stock)
    print_report(reorder_list, by_warehouse, final_stock)
    return reorder_list, by_warehouse

if __name__ == "__main__":
	main()
