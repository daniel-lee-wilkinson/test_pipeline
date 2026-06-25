# anomaly_detector.py
# Detects production anomalies — sudden drops, repeated defects, downtime patterns.
# Hint: rename, extract variable, extract method, simplify boolean, introduce constant

import statistics


# Hint: rename — poor function and variable names throughout
def chk_drop(recs):
    """Return True if the latest output is significantly below the recent average."""
    s = sorted(recs, key=lambda r: r["date"])
    lst = s[-1]["value"]
    prev = s[:-1]
    avg = sum(r["value"] for r in prev) / len(prev)
    # Hint: extract variable — what does 0.25 represent?
    return lst < avg * (1 - 0.25)


# Hint: extract variable — complex one-liner, and introduce constant for 5
def has_repeat_defects(records):
    """Return True if defects exceed 5% of output on more than 3 consecutive days."""
    daily = {}
    for r in records:
        if r["date"] not in daily:
            daily[r["date"]] = {"output": 0, "defects": 0}
        if r["reading_type"] == "output":
            daily[r["date"]]["output"] += r["value"]
        if r["reading_type"] == "defects":
            daily[r["date"]]["defects"] += r["value"]
    dates = sorted(daily.keys())
    streak = 0
    for d in dates:
        o = daily[d]["output"]
        df = daily[d]["defects"]
        # Hint: extract variable — what does this expression mean?
        if o > 0 and df / o * 100 > 5:
            streak += 1
            # Hint: introduce constant for 3
            if streak >= 3:
                return True
        else:
            streak = 0
    return False


# Hint: extract method — downtime calculation and classification are mixed together
def get_downtime_report(records, machine_id):
    """Return a downtime summary for a machine."""
    machine_recs = [r for r in records if r["machine_id"] == machine_id]
    downtime_recs = [r for r in machine_recs if r["reading_type"] == "downtime"]

    total_downtime = sum(r["value"] for r in downtime_recs)
    num_days = len(set(r["date"] for r in downtime_recs))
    avg_daily = round(total_downtime / num_days, 2) if num_days > 0 else 0

    # classification — could be extracted
    # Hint: introduce constants for 120 and 60
    if total_downtime > 120:
        severity = "Critical"
    elif total_downtime > 60:
        severity = "Warning"
    else:
        severity = "OK"

    return {
        "machine_id": machine_id,
        "total_downtime_mins": round(total_downtime / 60, 2),
        "avg_daily_downtime_mins": round(avg_daily / 60, 2),
        "severity": severity,
    }


# Hint: simplify boolean
def is_critical_downtime(total_downtime_seconds):
    # Hint: introduce constant for 7200
    if total_downtime_seconds > 7200:
        return True
    else:
        return False


# Hint: replace conditional with lookup
def get_anomaly_priority(anomaly_type):
    if anomaly_type == "output_drop":
        return "High"
    elif anomaly_type == "repeat_defects":
        return "High"
    elif anomaly_type == "downtime":
        return "Medium"
    elif anomaly_type == "low_availability":
        return "Medium"
    elif anomaly_type == "energy_spike":
        return "Low"
    else:
        return "Unknown"
