# cleaner.py
# Cleans raw production records — removes invalid readings, detects outliers.
# Hint: extract method, simplify boolean, rename, extract variable

import statistics

MINIMUM_UPTIME_THRESHOLD = 90

# Hint: extract method — does too many things at once
def clean_records(records):
    """Remove negative values, zero-output records, and statistical outliers."""
    out = []
    vals = [r["value"] for r in records]

    # outlier bounds — could be extracted
    mean_value = statistics.mean(vals)
    stdev = statistics.stdev(vals)
    lower_value = mean_value - (3 * stdev)
    upper_value = mean_value + (3 * stdev)

    for record in records:
        val = record["value"]
        machine_id = record["machine_id"]
        date = record["date"]

        # negative check — could be extracted
        if is_neg(val):
            print(f"Negative reading for {machine_id} on {date}: {val}")
            continue


        # zero output check — could be extracted
        if is_zero_output(record["reading_type"], val):
            print(f"Zero output for {machine_id} on {date}")
            continue

        # outlier check — could be extracted
        if is_outlier(val, lower_value, upper_value):
            print(f"Outlier for {machine_id} on {date}: {val}")
            continue

        out.append(record)

    return out


# Hint: simplify boolean
def is_neg(value):
    return value < 0

def is_zero_output(reading_type, value):
    return reading_type == "output" and value == 0

# Hint: simplify boolean
def is_record_complete(record):
    return all(record.get(field) is not None for field in ["machine_id", "date", "value", "reading_type", "shift"])


def filter_reading_type(records, reading_type):
    """Return records matching a given reading type."""
    return [r for r in records if r["reading_type"] == reading_type]


# Hint: extract variable — both mean and stdev are called twice
def get_bounds(vals):
    stdev = statistics.stdev(vals)
    mean = statistics.mean(vals)
    return mean - 3 * stdev, mean + 3 * stdev


def is_outlier(v, lo, hi):
    return v < lo or v > hi


# Hint: introduce constant — what is 90 here?
def is_low_availability(uptime_pct):
    """Return True if machine availability is below acceptable threshold."""
    return uptime_pct < MINIMUM_UPTIME_THRESHOLD