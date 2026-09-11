"""
ETL Pipeline - Web Server Log Processing

Extracts raw web server log lines (simulated), transforms them into
structured events (parsing, classifying, flagging suspicious activity),
and loads the result into a summary report + an in-memory "alerts" store.

NOTE: This script works, but it has a bunch of rough edges left in on
purpose (it's meant to be refactored).
"""

import random
import datetime

# ---------------------------------------------------------------------------
# Config, sitting around as globals
# ---------------------------------------------------------------------------
SLOW_REQUEST_MS = 800
ERROR_STATUS_CODES = [400, 401, 403, 404, 500, 502, 503]
SUSPICIOUS_PATHS = ["/admin", "/wp-login.php", "/.env", "/config.php"]
KNOWN_BOTS = ["Googlebot", "Bingbot", "AhrefsBot"]

total_lines = 0
parse_failures = 0
alerts = []


# ---------------------------------------------------------------------------
# EXTRACT
# ---------------------------------------------------------------------------
def generate_dummy_logs(n=60):
    """Fakes lines you'd normally read from an nginx/apache access log."""
    random.seed(7)
    ips = ["203.0.113.5", "198.51.100.23", "192.0.2.77", "203.0.113.99", "10.0.0.4"]
    paths = ["/", "/home", "/api/orders", "/api/users", "/login",
             "/admin", "/wp-login.php", "/static/app.js", "/.env"]
    methods = ["GET", "GET", "GET", "POST", "PUT", "DELETE"]
    agents = ["Mozilla/5.0", "Googlebot", "Bingbot", "curl/7.68.0", "AhrefsBot", ""]
    statuses = [200, 200, 200, 200, 301, 404, 500, 403, 401]

    lines = []
    for i in range(n):
        ip = random.choice(ips)
        method = random.choice(methods)
        path = random.choice(paths)
        status = random.choice(statuses)
        duration_ms = random.choice([12, 45, 80, 150, 300, 900, 1500, -1])
        agent = random.choice(agents)
        ts = datetime.datetime(2026, 3, 1) + datetime.timedelta(minutes=i * 3)

        # most lines are well-formed, a few are garbage on purpose
        if random.random() < 0.08:
            line = f"MALFORMED LINE {i} ??? {ip}"
        else:
            line = (f'{ip} - - [{ts.strftime("%d/%b/%Y:%H:%M:%S")}] '
                    f'"{method} {path} HTTP/1.1" {status} {duration_ms} "{agent}"')
        lines.append(line)
    return lines


def extract():
    print("Reading log lines...")
    lines = generate_dummy_logs(60)
    print(f"Read {len(lines)} lines")
    return lines


# ---------------------------------------------------------------------------
# TRANSFORM
# ---------------------------------------------------------------------------
def parse_line(line):
    """Parses one raw log line into a dict, or None if it can't be parsed."""
    global parse_failures

    try:
        ip = line.split(" ")[0]
        ts_part = line.split("[")[1].split("]")[0]
        request_part = line.split('"')[1]
        method, path, _ = request_part.split(" ")
        after_request = line.split('"')[2].strip().split(" ")
        status = int(after_request[0])
        duration_ms = int(after_request[1])
        agent = line.split('"')[3]

        ts = datetime.datetime.strptime(ts_part, "%d/%b/%Y:%H:%M:%S")

        return {
            "ip": ip,
            "timestamp": ts,
            "method": method,
            "path": path,
            "status": status,
            "duration_ms": duration_ms,
            "agent": agent,
        }
    except Exception:
        parse_failures += 1
        print(f"Could not parse line: {line}")
        return None


def classify_event(event):
    """Bolts a 'category' and any alert flags onto the event, all at once."""
    if event["agent"] in KNOWN_BOTS:
        event["category"] = "bot"
    elif event["status"] in ERROR_STATUS_CODES:
        event["category"] = "error"
    elif event["duration_ms"] > SLOW_REQUEST_MS:
        event["category"] = "slow"
    else:
        event["category"] = "normal"

    if event["path"] in SUSPICIOUS_PATHS:
        alerts.append(f"Suspicious path hit: {event['ip']} -> {event['path']}")

    if event["duration_ms"] < 0:
        alerts.append(f"Bad duration value for {event['ip']} on {event['path']}")

    if event["status"] == 500:
        alerts.append(f"Server error for {event['ip']} on {event['path']}")

    return event


def transform(lines):
    global total_lines
    print("Parsing and classifying events...")
    events = []
    for line in lines:
        total_lines += 1
        parsed = parse_line(line)
        if parsed is None:
            continue
        classified = classify_event(parsed)
        events.append(classified)
    print(f"Parsed {len(events)} of {total_lines} lines ({parse_failures} failures)")
    return events


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------
def load(events):
    """Loads into a fake in-memory store and builds a category summary."""
    print("Loading events...")
    fake_store = []
    for e in events:
        fake_store.append(e)

    summary = {}
    for e in events:
        cat = e["category"]
        if cat not in summary:
            summary[cat] = {"count": 0, "total_duration_ms": 0}
        summary[cat]["count"] += 1
        summary[cat]["total_duration_ms"] += max(e["duration_ms"], 0)

    print(f"Loaded {len(fake_store)} events")
    return fake_store, summary


def print_report(summary):
    print("\n--- Event Category Summary ---")
    for cat, stats in sorted(summary.items(), key=lambda x: -x[1]["count"]):
        avg = stats["total_duration_ms"] / stats["count"] if stats["count"] else 0
        print(f"{cat:10s} count={stats['count']:3d}  avg_duration={avg:.1f}ms")

    print(f"\n--- Alerts ({len(alerts)}) ---")
    for a in alerts:
        print(f" - {a}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    raw = extract()
    events = transform(raw)
    store, summary = load(events)
    print_report(summary)
    return store, summary


if __name__ == "__main__":
    main()