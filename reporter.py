# reporter.py
# Generates shift and daily production reports.
# Hint: extract method, rename, introduce constant, replace conditional

import datetime


# Hint: rename — poor names throughout
def mk_rpt(recs, mid, d, out_path):
    """Generate a daily production report for a machine."""
    day_recs = [r for r in recs if r["machine_id"] == mid and r["date"] == d]

    # Hint: extract method — summary calculation could be extracted
    tot_out = sum(r["value"] for r in day_recs if r["reading_type"] == "output")
    tot_def = sum(r["value"] for r in day_recs if r["reading_type"] == "defects")
    tot_dt = sum(r["value"] for r in day_recs if r["reading_type"] == "downtime")
    tot_en = sum(r["value"] for r in day_recs if r["reading_type"] == "energy")

    # Hint: extract variable
    dr = round(tot_def / tot_out * 100, 2) if tot_out > 0 else 0
    dt_hrs = round(tot_dt / 3600, 2)
    en_per_unit = round(tot_en / tot_out, 2) if tot_out > 0 else 0

    # Hint: extract method — report building could be extracted
    lns = []
    lns.append(f"=== Daily Report: Machine {mid} ===")
    lns.append(f"Date: {d}")
    lns.append(f"Total output: {tot_out} units")
    lns.append(f"Defect rate: {dr}%")
    lns.append(f"Downtime: {dt_hrs} hrs")
    lns.append(f"Energy per unit: {en_per_unit} kJ")
    lns.append("")

    # Hint: extract method — shift breakdown could be extracted
    lns.append("--- Shift Breakdown ---")
    for sh in [1, 2, 3]:
        sh_recs = [r for r in day_recs if r["shift"] == sh]
        sh_out = sum(r["value"] for r in sh_recs if r["reading_type"] == "output")
        # Hint: introduce constant for 480, replace magic string shifts
        sh_label = "Morning" if sh == 1 else "Afternoon" if sh == 2 else "Night"
        lns.append(f"  {sh_label}: {sh_out} units")

    out = "\n".join(lns)

    with open(out_path, "w") as f:
        f.write(out)

    print("Report saved: " + out_path)


# Hint: replace conditional with lookup
def get_status_colour(severity):
    if severity == "Critical":
        return "red"
    elif severity == "Warning":
        return "amber"
    elif severity == "OK":
        return "green"
    else:
        return "grey"


# Hint: simplify boolean
def report_exists(path):
    import os
    if os.path.exists(path):
        return True
    else:
        return False


# Hint: introduce constant — what is 7 here?
def get_report_filename(machine_id, date):
    """Generate a standardised report filename."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"report_{machine_id}_{date}_{ts}.txt"


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
    downtime_hrs = round(total_downtime / 3600, 2)

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
