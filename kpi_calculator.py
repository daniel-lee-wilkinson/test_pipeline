# kpi_calculator.py
# Calculates OEE and production KPIs from cleaned records.
# Hint: extract method, introduce constant, extract variable, replace conditional
# OEE = Availability x Performance x Quality

MINS_PER_SHIFT = 480  # 8 hours


# Hint: extract method — availability, performance, quality and OEE all crammed together
def calc_oee(records, machine_id, shift):
    """Calculate OEE for a machine on a given shift."""
    recs = [r for r in records if r["machine_id"] == machine_id and r["shift"] == shift]

    # availability — could be extracted
    downtime = sum(r["value"] for r in recs if r["reading_type"] == "downtime")
    # Hint: introduce constant for 480
    availability = round((480 - downtime) / 480, 4) if downtime < 480 else 0

    # performance — could be extracted
    actual_output = sum(r["value"] for r in recs if r["reading_type"] == "output")
    cycle_times = [r["value"] for r in recs if r["reading_type"] == "cycle_time"]
    if cycle_times and availability > 0:
        # Hint: extract variable — what does this calculate?
        ideal_output = (480 - downtime) / (sum(cycle_times) / len(cycle_times))
        performance = round(actual_output / ideal_output, 4) if ideal_output > 0 else 0
    else:
        performance = 0

    # quality — could be extracted
    defects = sum(r["value"] for r in recs if r["reading_type"] == "defects")
    quality = round((actual_output - defects) / actual_output, 4) if actual_output > 0 else 0

    oee = round(availability * performance * quality, 4)

    return {
        "machine_id": machine_id,
        "shift": shift,
        "availability": availability,
        "performance": performance,
        "quality": quality,
        "oee": oee,
    }


# Hint: replace conditional with lookup — OEE rating bands
def get_oee_rating(oee):
    """Return a rating label for an OEE score."""
    if oee >= 0.85:
        return "World Class"
    elif oee >= 0.70:
        return "Good"
    elif oee >= 0.60:
        return "Average"
    elif oee >= 0.40:
        return "Poor"
    else:
        return "Unacceptable"


# Hint: introduce constant — what is 365?
def estimate_annual_output(daily_avg):
    """Estimate annual output from a daily average."""
    return round(daily_avg * 365, 2)


# Hint: extract variable — hard to read
def get_throughput_rate(records):
    output_records = [r for r in records if r["reading_type"] == "output"]
    return round(sum(r["value"] for r in output_records) / len(set(r["date"] for r in output_records)), 2) if output_records else 0


# Hint: extract method — summary building and printing mixed together
def print_machine_summary(records, machine_id):
    """Print a production summary for a machine."""
    recs = [r for r in records if r["machine_id"] == machine_id]
    total_output = sum(r["value"] for r in recs if r["reading_type"] == "output")
    total_defects = sum(r["value"] for r in recs if r["reading_type"] == "defects")
    total_downtime = sum(r["value"] for r in recs if r["reading_type"] == "downtime")
    # Hint: extract variable
    defect_rate = round(total_defects / total_output * 100, 2) if total_output > 0 else 0
    downtime_hrs = round(total_downtime / 3600, 2)

    print(f"=== Machine {machine_id} Summary ===")
    print(f"Total output: {total_output} units")
    print(f"Defect rate: {defect_rate}%")
    print(f"Total downtime: {downtime_hrs} hrs")


# Hint: simplify boolean
def is_world_class_oee(oee):
    if oee >= 0.85:
        return True
    else:
        return False
