# kpi_calculator.py
# Calculates OEE and production KPIs from cleaned records.
# Hint: extract method, introduce constant, extract variable, replace conditional
# OEE = Availability x Performance x Quality
from typing import Any

MINS_PER_SHIFT = 480
SECONDS_PER_HOUR = 3600
DAYS_PER_YEAR = 365

MINS_PER_SHIFT = 480  # 8 hours


OEE_THRESHOLDS = [
    (0.85, "World Class"),
    (0.70, "Good"),
    (0.60, "Average"),
    (0.40, "Poor"),
]



# Hint: extract method — availability, performance, quality and OEE all crammed together
def calc_oee(records, machine_id, shift):
    """Calculate OEE for a machine on a given shift."""
    recs = [r for r in records if r["machine_id"] == machine_id and r["shift"] == shift]

    # availability — could be extracted
    downtime = sum(r["value"] for r in recs if r["reading_type"] == "downtime")
    # Hint: introduce constant for 480
    availability = round((MINS_PER_SHIFT - downtime) / MINS_PER_SHIFT, 4) if downtime < MINS_PER_SHIFT else 0

    # performance — could be extracted
    actual_output, performance = calc_performance(availability, downtime, recs)

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


def calc_performance(availability: float | int, downtime: int, recs: list[Any]) -> tuple[int, float | int]:
    actual_output = sum(r["value"] for r in recs if r["reading_type"] == "output")
    cycle_times = [r["value"] for r in recs if r["reading_type"] == "cycle_time"]
    if cycle_times and availability > 0:
        # Hint: extract variable — what does this calculate?
        ideal_output = (MINS_PER_SHIFT - downtime) / (sum(cycle_times) / len(cycle_times))
        performance = round(actual_output / ideal_output, 4) if ideal_output > 0 else 0
    else:
        performance = 0
    return actual_output, performance


# Hint: replace conditional with lookup — OEE rating bands - not easy to use a lookup for bands, so use conditional
def get_oee_rating(oee):
    for threshold, rating in OEE_THRESHOLDS:
        if oee >= threshold:
            return rating
    return "Unacceptable"

# Hint: introduce constant — what is 365?
def estimate_annual_output(daily_avg):
    """Estimate annual output from a daily average."""
    return round(daily_avg * DAYS_PER_YEAR, 2)


# Hint: extract variable — hard to read
def get_throughput_rate(records):
    output_records = [r for r in records if r["reading_type"] == "output"]
    sum_val = sum(r["value"] for r in output_records)
    nr_records = len(set(r["date"] for r in output_records))
    return round(sum_val / nr_records, 2) if output_records else 0


# Hint: extract method — summary building and printing mixed together
def print_machine_summary(records, machine_id):
    """Print a production summary for a machine."""
    total_defects, total_downtime, total_output = get_prod_summary(machine_id, records)
    # Hint: extract variable
    defect_rate = round(total_defects / total_output * 100, 2) if total_output > 0 else 0
    downtime_hrs = round(total_downtime / SECONDS_PER_HOUR, 2)

    print_prod_summary(defect_rate, downtime_hrs, machine_id, total_output)


def print_prod_summary(defect_rate: float | int, downtime_hrs: float, machine_id, total_output: int):
    print(f"=== Machine {machine_id} Summary ===")
    print(f"Total output: {total_output} units")
    print(f"Defect rate: {defect_rate}%")
    print(f"Total downtime: {downtime_hrs} hrs")


def get_prod_summary(machine_id, records) -> tuple[int, int, int]:
    recs = [r for r in records if r["machine_id"] == machine_id]
    total_output = sum(r["value"] for r in recs if r["reading_type"] == "output")
    total_defects = sum(r["value"] for r in recs if r["reading_type"] == "defects")
    total_downtime = sum(r["value"] for r in recs if r["reading_type"] == "downtime")
    return total_defects, total_downtime, total_output


# Hint: simplify boolean
def is_world_class_oee(oee):
    return oee >= 0.85