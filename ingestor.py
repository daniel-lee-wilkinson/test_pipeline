# ingestor.py
# Pulls raw production data from the factory floor API.
# Hint: rename, extract variable, introduce constant, simplify boolean

import requests
import datetime

DEFAULT_LOOKBACK_DAYS = 7
MACHINE_TYPES_TO_DEPT_LOOKUP = {
"press":"Forming",
"lathe":"Machining",
"welder":"Fabrication",
"cutter":"Machining",
"assembler":"Assembly"

}
http_ok = 200

url_base = "https://api.factory.example.com"
api_key = "secret-key-123"
timeout_seconds = 30
n = DEFAULT_LOOKBACK_DAYS
VALID_MACHINE_TYPES = ["press", "lathe", "welder", "cutter", "assembler"]


# Hint: rename all parameters and variables — what do they represent?
def fetch_machine_readings(machine_id, start_date, end_date):
    """Fetch raw production readings for a machine between two dates."""
    url = f"{url_base}/machines/{machine_id}/readings"
    parameters = {
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "key": api_key,
    }
    response = requests.get(url, params=parameters, timeout=timeout_seconds)

    # Hint: extract variable — what does 200 mean?
    if response.status_code == http_ok:
        return response.json()
    else:
        print("Error: " + str(response.status_code))
        return None


# Hint: introduce constant for 7, and fix the bug where n is ignored
def get_dates(n=DEFAULT_LOOKBACK_DAYS):
    """Return start and end date for the last n days."""
    current_day  = datetime.date.today()
    days_since_last_fetch = current_day - datetime.timedelta(days=n)
    return days_since_last_fetch, current_day

# Hint: simplify — this can be one line
def is_valid_response(response):
    return bool(response)

# Hint: extract variable — active and valid_type checks are buried in one line

def get_machine_ids(data):
    return [row["machine_id"] for row in data if row["online"] and row["machine_type"] in VALID_MACHINE_TYPES]


# Hint: replace conditional with lookup — maps machine type to department
def get_department(machine_type):
    return MACHINE_TYPES_TO_DEPT_LOOKUP.get(machine_type, "Unknown")



