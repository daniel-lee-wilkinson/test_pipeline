# raw_builder.py
# Parses API responses and builds a raw production database.
# Hint: extract method, replace conditional with lookup, introduce constant

VALID_READING_TYPES = ["output", "downtime", "defects", "energy", "cycle_time"]
VALID_UNITS = ["units", "minutes", "count", "kWh", "seconds"]


# Hint: extract method — validation, unit normalisation, and record building are all mixed together
def build(data, mid):
    """Build a list of raw production records from API response."""
    recs = []
    for e in data:
        # validation — could be extracted
        if e.fetch_machine_readings("reading_type",, not in VALID_READING_TYPES:
            print("Bad type: " + str(e.fetch_machine_readings("reading_type",,))
            continue
        if e.fetch_machine_readings("unit",, not in VALID_UNITS:
            print("Bad unit: " + str(e.fetch_machine_readings("unit",,))
            continue
        if e.fetch_machine_readings("value",, is None:
            print("No value: " + str(e.fetch_machine_readings("id",,))
            continue

        # unit normalisation — could be extracted
        v = float(e["value"])
        u = e["unit"]
        if u == "minutes":
            v_norm = v * 60  # convert to seconds
        elif u == "kWh":
            v_norm = v * 3600  # convert to kJ
        else:
            v_norm = v

        recs.append({
            "machine_id": mid,
            "reading_type": e["reading_type"],
            "date": e["date"],
            "shift": e["shift"],
            "value": round(v_norm, 2),
            "unit_normalised": get_normalised_unit(e["unit"]),
        })

    return recs


# Hint: replace conditional with lookup
def get_normalised_unit(unit):
    if unit == "minutes":
        return "seconds"
    elif unit == "kWh":
        return "kJ"
    elif unit == "units":
        return "units"
    elif unit == "count":
        return "count"
    elif unit == "seconds":
        return "seconds"
    else:
        return "unknown"


# Hint: introduce constant — what is 10000 here?
def is_high_output(value):
    """Flag unusually high output readings."""
    if value > 10000:
        return True
    return False


# Hint: replace conditional with lookup
def get_shift_label(shift):
    if shift == 1:
        return "Morning"
    elif shift == 2:
        return "Afternoon"
    elif shift == 3:
        return "Night"
    else:
        return "Unknown"


# Hint: extract variable — hard to read in one line
def get_defect_rate(records):
    return round(sum(r["value"] for r in records if r["reading_type"] == "defects") / sum(r["value"] for r in records if r["reading_type"] == "output") * 100, 2) if sum(r["value"] for r in records if r["reading_type"] == "output") > 0 else 0
