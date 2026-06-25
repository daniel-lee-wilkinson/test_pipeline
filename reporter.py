# reporter.py
# Generates shift and daily production reports.
# Hint: extract method, rename, introduce constant, replace conditional

import datetime
from typing import Any

SECS_PER_HOUR = 3600

SEVERITY_COLORS = {

    "Critical": "red",
    "Warning": "amber",
    "OK": "green"

}


# Hint: rename — poor names throughout
def make_report(records, machine_id, date, out_path):
    """Generate a daily production report for a machine."""
    day_recs = [r for r in records if r["machine_id"] == machine_id and r["date"] == date]

    # Hint: extract method — summary calculation could be extracted
    tot_defects, tot_downtime, tot_energy, tot_output = summary_stats(day_recs)

    # Hint: extract variable
    share_defects_of_output = tot_defects / tot_output
    defect_rate = round(share_defects_of_output * 100, 2) if tot_output > 0 else 0
    downtime_hours = round(tot_downtime / SECS_PER_HOUR, 2)
    en_per_unit = round(tot_energy / tot_output, 2) if tot_output > 0 else 0

    # Hint: extract method — report building could be extracted
    lns = print_report(date, defect_rate, downtime_hours, en_per_unit, machine_id, tot_output)

    # Hint: extract method — shift breakdown could be extracted
    report_output = shift_breakdown(day_recs, lns)

    with open(out_path, "w") as f:
        f.write(report_output)

    print("Report saved: " + out_path)


def shift_breakdown(day_recs: list[Any], lns: list[Any]):
    lns.append("--- Shift Breakdown ---")
    for shift in [1, 2, 3]:
        shift_records = [r for r in day_recs if r["shift"] == shift]
        shift_output = sum(r["value"] for r in shift_records if r["reading_type"] == "output")
        # Hint: introduce constant for 480, replace magic string shifts
        shift_label = "Morning" if shift == 1 else "Afternoon" if shift == 2 else "Night"
        lns.append(f"  {shift_label}: {shift_output} units")

    out = "\n".join(lns)
    return out


def print_report(d, defect_rate: float | int, downtime_hours: float, en_per_unit: float | int, mid, tot_output: int) -> \
list[Any]:
    lns = []
    lns.append(f"=== Daily Report: Machine {mid} ===")
    lns.append(f"Date: {d}")
    lns.append(f"Total output: {tot_output} units")
    lns.append(f"Defect rate: {defect_rate}%")
    lns.append(f"Downtime: {downtime_hours} hrs")
    lns.append(f"Energy per unit: {en_per_unit} kJ")
    lns.append("")
    return lns


def summary_stats(day_recs: list[Any]) -> tuple[int, int, int, int]:
    tot_output = sum(r["value"] for r in day_recs if r["reading_type"] == "output")
    tot_defects = sum(r["value"] for r in day_recs if r["reading_type"] == "defects")
    tot_downtime = sum(r["value"] for r in day_recs if r["reading_type"] == "downtime")
    tot_energy = sum(r["value"] for r in day_recs if r["reading_type"] == "energy")
    return tot_defects, tot_downtime, tot_energy, tot_output


# Hint: replace conditional with lookup

def get_status_colour(severity):
    return SEVERITY_COLORS.get(severity, "grey")

# Hint: simplify boolean
def report_exists(path):
    import os
    return os.path.exists(path)


# Hint: introduce constant — what is 7 here?
def get_report_filename(machine_id, date):
    """Generate a standardised report filename."""
    today_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"report_{machine_id}_{date}_{today_date}.txt"


# Hint: extract method — validates inputs then builds summary, all in one go
def generate_shift_summary(records, machine_id, shift, floor_area_m2=None):
    """Generate a summary dict for a single shift."""
    if machine_id is None or machine_id == "":
        print("Invalid machine ID")
        return None
    if shift not in [1, 2, 3]:
        print("Invalid shift: " + str(shift))
        return None

    shift_recs = [r for r in records if r["machine_id"] == machine_id and r["shift"] == shift]
    if len(shift_recs) == 0:
        print("No records found for shift")
        return None

    total_output = sum(r["value"] for r in shift_recs if r["reading_type"] == "output")
    total_defects = sum(r["value"] for r in shift_recs if r["reading_type"] == "defects")
    total_downtime = sum(r["value"] for r in shift_recs if r["reading_type"] == "downtime")

    # Hint: extract variable
    defect_rate = round(total_defects / total_output * 100, 2) if total_output > 0 else 0
    downtime_hrs = round(total_downtime / SECS_PER_HOUR, 2)

    summary = {
        "machine_id": machine_id,
        "shift": shift,
        "total_output": total_output,
        "defect_rate": defect_rate,
        "downtime_hrs": downtime_hrs,
    }

    # Hint: introduce constant for 1000
    if floor_area_m2 and floor_area_m2 > 0:
        summary["output_per_m2"] = round(total_output / floor_area_m2, 2)

    return summary
