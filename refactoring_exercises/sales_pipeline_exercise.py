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

# ---------------------------------------------------------------------------
# "Config" - just sitting here as globals
# ---------------------------------------------------------------------------
EXCHANGE_RATES = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27, "JPY": 0.0067}
TAX_RATE = 0.0825
DISCOUNT_THRESHOLD = 500
DISCOUNT_RATE = 0.1
VALID_CATEGORIES = ["electronics", "clothing", "home", "toys", "beauty"]

processed_count = 0
error_count = 0
skipped_rows = []


# ---------------------------------------------------------------------------
# EXTRACT
# ---------------------------------------------------------------------------
def generate_dummy_data(n=40):
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


def extract():
    print("Extracting data...")
    data = generate_dummy_data(40)
    print(f"Extracted {len(data)} rows")
    return data


# ---------------------------------------------------------------------------
# TRANSFORM
# ---------------------------------------------------------------------------
def clean_and_convert(row):
    """Does validation, currency conversion, tax, AND discounting all at once."""
    global error_count, skipped_rows

    if not row.get("customer"):
        error_count += 1
        skipped_rows.append(row)
        return None

    if row.get("unit_price") is None:
        error_count += 1
        skipped_rows.append(row)
        return None

    if row["quantity"] <= 0:
        error_count += 1
        skipped_rows.append(row)
        return None

    if row["category"] not in VALID_CATEGORIES:
        row["category"] = "uncategorized"

    rate = EXCHANGE_RATES.get(row["currency"])
    if rate is None:
        print(f"Warning: unsupported currency {row['currency']} for {row['order_id']}, skipping")
        error_count += 1
        skipped_rows.append(row)
        return None

    subtotal = row["unit_price"] * row["quantity"] * rate

    if subtotal > DISCOUNT_THRESHOLD:
        subtotal = subtotal - (subtotal * DISCOUNT_RATE)

    total = subtotal + (subtotal * TAX_RATE)

    new_row = dict(row)
    new_row["unit_price_usd"] = round(row["unit_price"] * rate, 2)
    new_row["subtotal_usd"] = round(subtotal, 2)
    new_row["total_usd"] = round(total, 2)
    new_row["order_date"] = datetime.date.fromisoformat(row["order_date"])
    return new_row


def transform(rows):
    global processed_count
    print("Transforming data...")
    cleaned = []
    for row in rows:
        result = clean_and_convert(row)
        if result is not None:
            cleaned.append(result)
            processed_count += 1
    print(f"Transformed {processed_count} rows, {error_count} errors")
    return cleaned


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------
def load(rows):
    """Loads into a fake in-memory DB and also builds a summary report."""
    print("Loading data...")
    fake_db = []
    for r in rows:
        fake_db.append(r)

    # build category summary right here too, because why not
    summary = {}
    for r in rows:
        cat = r["category"]
        if cat not in summary:
            summary[cat] = {"orders": 0, "revenue": 0.0}
        summary[cat]["orders"] += 1
        summary[cat]["revenue"] += r["total_usd"]

    print(f"Loaded {len(fake_db)} rows into DB")
    return fake_db, summary


def print_report(summary):
    print("\n--- Category Summary ---")
    for cat, stats in sorted(summary.items(), key=lambda x: -x[1]["revenue"]):
        print(f"{cat:15s} orders={stats['orders']:3d}  revenue=${stats['revenue']:.2f}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    raw = extract()
    clean = transform(raw)
    db, summary = load(clean)
    print_report(summary)
    print(f"\nSkipped {len(skipped_rows)} rows due to bad data")
    return db, summary


if __name__ == "__main__":
    main()