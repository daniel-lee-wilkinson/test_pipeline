"""
ETL Pipeline - Sales Data Processing

Extracts raw sales records (simulated from a CSV/API), transforms them
(cleaning, currency conversion, categorization), and loads the result
into a summary report + a "database" (in-memory list of dicts).

NOTE: This script works, but it has a bunch of rough edges on purpose
(it's meant to be refactored). Some things to think about while reading:
- global state
- functions doing more than one job
- magic numbers / hardcoded config buried in logic
- inconsistent error handling (some silent, some print-and-continue)
- repeated code across transform steps
- mixing I/O (print) with business logic
- no type hints, no tests, no logging
"""

import random
import datetime
from typing import Any
import time
import logging

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# "Config" - just sitting here as globals
# ---------------------------------------------------------------------------
EXCHANGE_RATES = {"USD": 1.0,
				  "EUR": 1.08,
				  "GBP": 1.27,
				  "JPY": 0.0067}
TAX_RATE = 0.0825
DISCOUNT_THRESHOLD = 500
DISCOUNT_RATE = 0.1
VALID_CATEGORIES = ["electronics", "clothing", "home", "toys", "beauty"]

processed_count = 0
error_count = 0
skipped_rows = []


def validate_row_present(row, column_name):
	if row.get(column_name) is None:
		return False
	return True


def convert_currency(row) -> float | None:
	rate = EXCHANGE_RATES.get(row["currency"])
	return rate


def calculate_discount(rate: float, row) -> float:
	subtotal = row["unit_price"] * row["quantity"] * rate
	if subtotal > DISCOUNT_THRESHOLD:
		subtotal = subtotal - (subtotal * DISCOUNT_RATE)
	return subtotal


def reject_row(row, reason: str):
	global error_count
	error_count += 1
	skipped_rows.append(row)
	logger.warning(f"Rejecting {row.get('order_id', '?')}: {reason}")
	return None


def generate_data_dictionary(rate: float, row: object, subtotal: float, total: float) -> dict[Any, Any]:
	new_row = dict(row)
	new_row["unit_price_usd"] = round(row["unit_price"] * rate, 2)
	new_row["subtotal_usd"] = round(subtotal, 2)
	new_row["total_usd"] = round(total, 2)
	new_row["order_date"] = datetime.date.fromisoformat(row["order_date"])
	return new_row


# ---------------------------------------------------------------------------
# EXTRACT
# ---------------------------------------------------------------------------
def generate_dummy_data(n: object = 40) -> list[Any]:
	"""Fakes what would normally come from a CSV export or an API call."""
	random.seed(42)
	customers = ["Alice Chen", "Bob Martinez", "Carla Ruiz", "Dev Patel",
				 "Erin Walsh", "Farid Haidari", "Grace Kim", "Hana Suzuki"]
	products = {
		"electronics": ["Laptop", "Headphones", "Monitor", "Keyboard"],
		"clothing": ["T-Shirt", "Jeans", "Jacket"],
		"home": ["Blender", "Lamp", "Rug"],
		"toys": ["Lego Set", "Puzzle"],
		"beauty": ["Lotion", "Shampoo"],
	}
	currencies = ["USD", "EUR", "GBP", "JPY", "ZAR"]  # ZAR is intentionally unsupported

	rows = []
	for i in range(n):
		cat = random.choice(list(products.keys()))
		row = {
			"order_id": f"ORD-{1000 + i}",
			"customer": random.choice(customers),
			"product": random.choice(products[cat]),
			"category": cat if random.random() > 0.05 else "gizmos",  # bad category sometimes
			"quantity": random.choice([1, 1, 1, 2, 3, 5, -1]),  # occasional bad data
			"unit_price": round(random.uniform(5, 800), 2),
			"currency": random.choice(currencies),
			"order_date": (datetime.date(2025, 1, 1) +
						   datetime.timedelta(days=random.randint(0, 300))).isoformat(),
		}
		# sprinkle in some missing/null fields
		if random.random() < 0.08:
			row["unit_price"] = None
		if random.random() < 0.05:
			row["customer"] = ""
		rows.append(row)
	return rows


def extract() -> list[Any]:
	logger.info("Extracting data...")
	data = generate_dummy_data(40)
	logger.info(f"Extracted {len(data)} rows")
	return data


# ---------------------------------------------------------------------------
# TRANSFORM
# ---------------------------------------------------------------------------
def clean_and_convert(row: object) -> dict[Any, Any] | None:
    if not validate_row_present(row, "customer"):
        return reject_row(row, "missing customer")

    if not validate_row_present(row, "unit_price"):
        return reject_row(row, "missing unit_price")

    if row["quantity"] <= 0:
        return reject_row(row, "invalid quantity")

    if row["category"] not in VALID_CATEGORIES:
        row["category"] = "uncategorized"

    rate = convert_currency(row)
    if rate is None:
        return reject_row(row, "currency unsupported")

    subtotal = calculate_discount(rate, row)
    total = subtotal + (subtotal * TAX_RATE)
    return generate_data_dictionary(rate, row, subtotal, total)

def transform(rows: object) -> list[Any]:
	global processed_count
	logger.info("Transforming data...")
	cleaned = []
	for row in rows:
		result = clean_and_convert(row)
		if result is not None:
			cleaned.append(result)
			processed_count += 1
	logger.info(f"Transformed {processed_count} rows, {error_count} errors")
	return cleaned


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------
def load(rows: object) -> tuple[list[Any], dict[Any, Any]]:
	"""Loads into a fake in-memory DB and also builds a summary report."""
	logger.info("Loading data...")
	fake_db = []
	for row in rows:
		fake_db.append(row)

	# build category summary right here too, because why not
	summary = {}
	for row in rows:
		cat = row["category"]
		if cat not in summary:
			summary[cat] = {"orders": 0, "revenue": 0.0}
		summary[cat]["orders"] += 1
		summary[cat]["revenue"] += row["total_usd"]

	logger.info(f"Loaded {len(fake_db)} rows into DB")
	return fake_db, summary


def print_report(summary: dict) -> None:
	logger.info("\n--- Category Summary ---")
	for cat, stats in sorted(summary.items(), key=lambda x: -x[1]["revenue"]):
		logger.info(f"{cat:15s} orders ={stats['orders']:3d} revenue = ${stats['revenue']:.2f}")
	logger.info("\n----End Summary----")

def get_duration(start_time: float) -> float:
	return time.time() - start_time


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    start_time = time.time()

    try:
        raw = extract()
        clean = transform(raw)
        db, summary = load(clean)
    except Exception:
        logger.exception("Pipeline failed unexpectedly")
        raise  # or: sys.exit(1)

    print_report(summary)
    logger.info(f"Skipped {len(skipped_rows)} rows due to bad data")
    logger.info(f"took {get_duration(start_time):.4e}s")
    return db, summary

if __name__ == "__main__":
	main()
