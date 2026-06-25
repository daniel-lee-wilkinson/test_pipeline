# anomaly_detector.py
# Detects production anomalies — sudden drops, repeated defects, downtime patterns.
# Hint: rename, extract variable, extract method, simplify boolean, introduce constant

import statistics
from typing import Any

MAX_DOWNTIME_THRESHOLD_MINS = 60

SECONDS_PER_MINUTE = 60

CRITICAL_DOWNTIME_THRESHOLD = 120

MAX_CONSEC_DAYS = 3

DEFECT_THRESHOLD_PCT = 5

OUTPUT_DROP_THRESHOLD = 0.25

ANOMALY_PRIORITIES = {
    "output_drop": "High",
    "repeat_defects": "High",
    "downtime": "Medium",
    "low_availability": "Medium",
    "energy_spike": "Low"

}



# Hint: rename — poor function and variable names throughout
def is_output_dropping(records):
    """Return True if the latest output is significantly below the recent average."""
    sorted_records = sorted(records, key=lambda r: r["date"])
    most_recent_record = sorted_records[-1]
    last_value = most_recent_record["value"]
    previous_records = sorted_records[:-1]
    total_previous_vals = sum(prev_rec["value"] for prev_rec in previous_records)
    avg_previous = total_previous_vals / len(previous_records)
    # Hint: extract variable — what does 0.25 represent?
    return last_value < avg_previous * (1 - OUTPUT_DROP_THRESHOLD)


# Hint: extract variable — complex one-liner, and introduce constant for 5
def has_repeat_defects(records):
    """Return True if defects exceed 5% of output on more than 3 consecutive days."""

    daily = aggregate_daily_totals(records)
    dates = sorted(daily.keys())
    streak = 0
    for day in dates:
        output = daily[day]["output"]
        defects = daily[day]["defects"]
        # Hint: extract variable — what does this expression mean?
        pct_defects = defects / output * 100
        if output > 0:
            if pct_defects > DEFECT_THRESHOLD_PCT:
                streak += 1
                if streak >= MAX_CONSEC_DAYS:
                    return True
            else:
                streak = 0
        else:
            streak = 0
    return False


def aggregate_daily_totals(records) -> dict[Any, Any]:
    daily_totals = {}
    for r in records:
        record_date = r["date"]
        if record_date not in daily_totals:
            daily_totals[record_date] = {"output": 0, "defects": 0}
        reading_type = r["reading_type"]
        if reading_type == "output":
            daily_totals[record_date]["output"] += r["value"]
        if reading_type == "defects":
            daily_totals[record_date]["defects"] += r["value"]
    return daily_totals


# Hint: extract method — downtime calculation and classification are mixed together
def get_downtime_report(records, machine_id):
    """Return a downtime summary for a machine."""
    avg_daily, total_downtime = calculate_downtime(machine_id, records)

    # classification — could be extracted
    # Hint: introduce constants for 120 and 60
    return classify_downtime(avg_daily, machine_id, total_downtime)


def classify_downtime(avg_daily: int, machine_id, total_downtime: float | int) -> dict[str, float | str | Any]:
    if total_downtime > CRITICAL_DOWNTIME_THRESHOLD:
        severity = "Critical"
    elif total_downtime > MAX_DOWNTIME_THRESHOLD_MINS:
        severity = "Warning"
    else:
        severity = "OK"

    return {
        "machine_id": machine_id,
        "total_downtime_mins": round(total_downtime / SECONDS_PER_MINUTE, 2),
        "avg_daily_downtime_mins": round(avg_daily / SECONDS_PER_MINUTE, 2),
        "severity": severity,
    }


def calculate_downtime(machine_id, records) -> tuple[int, float | int]:
    machine_recs = [r for r in records if r["machine_id"] == machine_id]
    downtime_recs = [r for r in machine_recs if r["reading_type"] == "downtime"]

    in_downtime_recs = (r["value"] for r in downtime_recs)
    total_downtime = sum(in_downtime_recs)
    num_days = len(set(r["date"] for r in downtime_recs))
    avg_daily = round(total_downtime / num_days, 2) if num_days > 0 else 0
    return avg_daily, total_downtime


# Hint: simplify boolean
def is_critical_downtime(total_downtime_seconds):
    # Hint: introduce constant for 7200
    return total_downtime_seconds > 7200


# Hint: replace conditional with lookup
def get_anomaly_priority(anomaly_type):
    return ANOMALY_PRIORITIES.get(anomaly_type, "Unknown")

