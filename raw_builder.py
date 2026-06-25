# raw_builder.py
# Parses API responses and builds a raw production database.
# Hint: extract method, replace conditional with lookup, introduce constant
SECS_PER_MINUTE = 60
SECS_PER_HOUR = 3600
MAX_OUTPUT_READING = 10000

VALID_READING_TYPES = ["output", "downtime", "defects", "energy", "cycle_time"]
VALID_UNITS = ["units", "minutes", "count", "kWh", "seconds"]
SHIFT_LABELS = {
    1: "Morning",
    2: "Afternoon",
    3: "Night"
}

NORMALIZED_UNITS = {
    "minutes":"seconds",
    "kWh":"kJ",
    "units":"units",
    "count":"count",
    "seconds":"seconds"
}

def is_valid_entry(entry):
    if entry.get("reading_type") not in VALID_READING_TYPES:
        print("Bad type: " + str(entry.get("reading_type")))
        return False
    if entry.get("unit") not in VALID_UNITS:
        print("Bad unit: " + str(entry.get("unit")))
        return False
    if entry.get("value") is None:
        print("No value: " + str(entry.get("id")))
        return False
    return True


def normalise_value(value, unit):
    v = float(value)
    if unit == "minutes":
        return v * SECS_PER_MINUTE
    elif unit == "kWh":
        return v * SECS_PER_HOUR
    else:
        return v


# Hint: extract method — validation, unit normalisation, and record building are all mixed together
def build_raw_database(data, machine_id):
    records = []
    for entry in data:
        if not is_valid_entry(entry):
            continue
        normalised_value = normalise_value(entry["value"], entry["unit"])
        records.append({
            "machine_id": machine_id,
            "reading_type": entry["reading_type"],
            "date": entry["date"],
            "shift": entry["shift"],
            "value": round(normalised_value, 2),
            "unit_normalised": get_normalized_units(entry["unit"]),
        })
    return records

# Hint: replace conditional with lookup

def get_normalized_units(unit):
    return NORMALIZED_UNITS.get(unit, "unknown")


# Hint: introduce constant — what is 10000 here?
def is_high_output(value):
    """Flag unusually high output readings."""
    return value > MAX_OUTPUT_READING


# Hint: replace conditional with lookup
def get_shift_label(shift):
    return SHIFT_LABELS.get(shift, "Unknown")

# Hint: extract variable — hard to read in one line
def get_defect_rate(records):
    sum_output = sum(r["value"] for r in records if r["reading_type"] == "output")
    sum_defects = sum(r["value"] for r in records if r["reading_type"] == "defects")
    return round(
        sum_defects / sum_output * 100, 2
    ) if sum_output > 0 else 0