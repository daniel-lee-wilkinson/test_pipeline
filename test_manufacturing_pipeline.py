# test_.py
# Tests for the refactored manufacturing pipeline.
# Complete the refactoring first, then fill in the ... placeholders.
#
# Run with: pytest test_.py -v
import pytest

from unittest.mock import patch, MagicMock

from ingestor import fetch_machine_readings, is_valid_response, get_machine_ids, get_department
from raw_builder import build_raw_database, get_normalized_units, is_high_output, get_shift_label, get_defect_rate
from cleaner import clean_records, is_neg, is_record_complete, get_bounds, is_outlier, is_low_availability, filter_reading_type
from anomaly_detector import is_output_dropping, has_repeat_defects, get_downtime_report, is_critical_downtime, get_anomaly_priority
from kpi_calculator import calc_oee, get_oee_rating, estimate_annual_output, get_throughput_rate, is_world_class_oee
from reporter import generate_shift_summary, get_status_colour, report_exists

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def raw_output_record():
    return {
        "id": "R01",
        "machine_id": "M01",
        "reading_type": "output",
        "date": "2024-03-01",
        "shift": 1,
        "value": "500",
        "unit": "units",
    }


@pytest.fixture
def raw_downtime_record():
    return {
        "id": "R02",
        "machine_id": "M01",
        "reading_type": "downtime",
        "date": "2024-03-01",
        "shift": 1,
        "value": "30",
        "unit": "minutes",
    }


@pytest.fixture
def clean_output_record():
    return {
        "machine_id": "M01",
        "reading_type": "output",
        "date": "2024-03-01",
        "shift": 1,
        "value": 500.0,
        "unit_normalised": "units",
    }


@pytest.fixture
def clean_defect_record():
    return {
        "machine_id": "M01",
        "reading_type": "defects",
        "date": "2024-03-01",
        "shift": 1,
        "value": 25.0,
        "unit_normalised": "count",
    }


@pytest.fixture
def clean_downtime_record():
    return {
        "machine_id": "M01",
        "reading_type": "downtime",
        "date": "2024-03-01",
        "shift": 1,
        "value": 1800.0,  # 30 minutes in seconds
        "unit_normalised": "seconds",
    }


@pytest.fixture
def machine_records(clean_output_record, clean_defect_record, clean_downtime_record):
    return [clean_output_record, clean_defect_record, clean_downtime_record]


# =============================================================================
# ingestor — is_valid_response
# =============================================================================

def test_is_valid_response_returns_false_for_none():
    assert is_valid_response(None) == False


def test_is_valid_response_returns_false_for_empty_list():
    assert is_valid_response([]) == False


def test_is_valid_response_returns_true_for_non_empty():
    assert is_valid_response([{"machine_id": "M01"}]) == True


# =============================================================================
# ingestor — get_machine_ids
# =============================================================================

def test_get_machine_ids_returns_online_machines_only():
    data = [
        {"machine_id": "M01", "online": True,  "machine_type": "press"},
        {"machine_id": "M02", "online": False, "machine_type": "lathe"},
    ]
    result = get_machine_ids(data)
    assert result == ["M01"]


def test_get_machine_ids_excludes_invalid_machine_types():
    data = [
        {"machine_id": "M01", "online": True, "machine_type": "press"},
        {"machine_id": "M02", "online": True, "machine_type": "robot"},  # invalid
    ]
    result = get_machine_ids(data)
    assert result == ["M01"]


# =============================================================================
# ingestor — fetch_machine_readings (mocking)
# =============================================================================

def test_fetch_machine_readings_returns_json_on_success():
    import datetime
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"machine_id": "M01"}]

    with patch("ingestor.requests.get", return_value=mock_resp):
        result = fetch_machine_readings("M01", datetime.date(2024, 3, 1), datetime.date(2024, 3, 7))
        assert result == [{"machine_id": "M01"}]


def test_fetch_machine_readings_returns_none_on_error():
    import datetime
    mock_resp = MagicMock()
    mock_resp.status_code = 503

    with patch("ingestor.requests.get", return_value=mock_resp):
        result = fetch_machine_readings("M01", datetime.date(2024, 3, 1), datetime.date(2024, 3, 7))
        assert result is None


# =============================================================================
# ingestor — get_department
# =============================================================================

@pytest.mark.parametrize("machine_type, expected", [
    ("press",     "Forming"),
    ("lathe",     "Machining"),
    ("welder",    "Fabrication"),
    ("cutter",    "Machining"),
    ("assembler", "Assembly"),
    ("unknown",   "Unknown"),
])
def test_get_department(machine_type, expected):
    assert get_department(machine_type) == expected


# =============================================================================
# raw_builder — build_raw_database
# =============================================================================

def test_build_raw_database_parses_units_record(raw_output_record):
    result = build_raw_database([raw_output_record], "M01")
    assert len(result) == 1
    assert result[0]["value"] == 500


def test_build_raw_database_converts_minutes_to_seconds(raw_downtime_record):
    result = build_raw_database([raw_downtime_record], "M01")
    assert result[0]["value"] == 1800  # 30 minutes * 60 = 1800 seconds


def test_build_raw_database_skips_invalid_reading_type():
    record = {"id": "R01", "machine_id": "M01", "reading_type": "temperature",
              "date": "2024-03-01", "shift": 1, "value": "100", "unit": "units"}
    result = build_raw_database([record], "M01")
    assert result == []


def test_build_raw_database_skips_none_value():
    record = {"id": "R01", "machine_id": "M01", "reading_type": "output",
              "date": "2024-03-01", "shift": 1, "value": None, "unit": "units"}
    result = build_raw_database([record], "M01")
    assert result == []


# =============================================================================
# raw_builder — get_normalized_units
# =============================================================================

@pytest.mark.parametrize("unit, expected", [
    ("minutes", "seconds"),
    ("kWh",     "kJ"),
    ("units",   "units"),
    ("count",   "count"),
    ("seconds", "seconds"),
    ("unknown", "unknown"),
])
def test_get_normalized_units(unit, expected):
    assert get_normalized_units(unit) == expected


# =============================================================================
# raw_builder — is_high_output
# =============================================================================

def test_is_high_output_returns_true_above_threshold():
    assert is_high_output(15000) == True


def test_is_high_output_returns_false_below_threshold():
    assert is_high_output(5000) == False


def test_is_high_output_returns_false_at_threshold():
    assert is_high_output(10000) == False  # strictly greater than


# =============================================================================
# raw_builder — get_shift_label
# =============================================================================

@pytest.mark.parametrize("shift, expected", [
    (1, "Morning"),
    (2, "Afternoon"),
    (3, "Night"),
    (4, "Unknown"),
])
def test_get_shift_label(shift, expected):
    assert get_shift_label(shift) == expected


# =============================================================================
# raw_builder — get_defect_rate
# =============================================================================

def test_get_defect_rate_returns_correct_percentage(machine_records):
    result = get_defect_rate(machine_records)
    assert result == 5.0  # 25 defects / 500 output * 100


def test_get_defect_rate_returns_zero_when_no_output():
    records = [{"reading_type": "defects", "value": 10}]
    result = get_defect_rate(records)
    assert result == 0


# =============================================================================
# cleaner — is_neg
# =============================================================================

def test_is_neg_returns_true_for_negative():
    assert is_neg(-1.0) == True


def test_is_neg_returns_false_for_zero():
    assert is_neg(0.0) == False


def test_is_neg_returns_false_for_positive():
    assert is_neg(100.0) == False


# =============================================================================
# cleaner — is_record_complete
# =============================================================================

def test_is_record_complete_returns_true_for_full_record(clean_output_record):
    assert is_record_complete(clean_output_record) == True


def test_is_record_complete_returns_false_when_machine_id_missing():
    record = {"date": "2024-03-01", "value": 100.0, "reading_type": "output", "shift": 1}
    assert is_record_complete(record) == False


def test_is_record_complete_returns_false_when_shift_missing():
    record = {"machine_id": "M01", "date": "2024-03-01", "value": 100.0, "reading_type": "output"}
    assert is_record_complete(record) == False


# =============================================================================
# cleaner — is_outlier
# =============================================================================

def test_is_outlier_returns_true_above_upper():
    assert is_outlier(200, 0, 100) == True


def test_is_outlier_returns_true_below_lower():
    assert is_outlier(-5, 0, 100) == True


def test_is_outlier_returns_false_within_range():
    assert is_outlier(50, 0, 100) == False


# =============================================================================
# cleaner — is_low_availability
# =============================================================================

def test_is_low_availability_returns_true_below_threshold():
    assert is_low_availability(85) == True


def test_is_low_availability_returns_false_above_threshold():
    assert is_low_availability(95) == False


def test_is_low_availability_returns_false_at_threshold():
    assert is_low_availability(90) == False  # strictly less than


# =============================================================================
# anomaly_detector — is_output_dropping
# =============================================================================

def test_is_output_dropping_returns_true_when_latest_below_average():
    records = [
        {"date": "2024-03-01", "value": 500},
        {"date": "2024-03-02", "value": 490},
        {"date": "2024-03-03", "value": 300},  # big drop
    ]
    assert is_output_dropping(records) == True


def test_is_output_dropping_returns_false_when_stable():
    records = [
        {"date": "2024-03-01", "value": 500},
        {"date": "2024-03-02", "value": 495},
        {"date": "2024-03-03", "value": 498},
    ]
    assert is_output_dropping(records) == False


# =============================================================================
# anomaly_detector — is_critical_downtime
# =============================================================================

def test_is_critical_downtime_returns_true_above_threshold():
    assert is_critical_downtime(8000) == True


def test_is_critical_downtime_returns_false_below_threshold():
    assert is_critical_downtime(3600) == False


def test_is_critical_downtime_returns_false_at_threshold():
    assert is_critical_downtime(7200) == False  # strictly greater than


# =============================================================================
# anomaly_detector — get_anomaly_priority
# =============================================================================

@pytest.mark.parametrize("anomaly_type, expected", [
    ("output_drop",      "High"),
    ("repeat_defects",   "High"),
    ("downtime",         "Medium"),
    ("low_availability", "Medium"),
    ("energy_spike",     "Low"),
    ("unknown",          "Unknown"),
])
def test_get_anomaly_priority(anomaly_type, expected):
    assert get_anomaly_priority(anomaly_type) == expected


# =============================================================================
# kpi_calculator — get_oee_rating
# =============================================================================

@pytest.mark.parametrize("oee, expected", [
    (0.90, "World Class"),
    (0.75, "Good"),
    (0.65, "Average"),
    (0.50, "Poor"),
    (0.30, "Unacceptable"),
    (0.85, "World Class"),  # boundary: >= 0.85
    (0.70, "Good"),         # boundary: >= 0.70
    (0.40, "Poor"),         # boundary: >= 0.40
])
def test_get_oee_rating(oee, expected):
    assert get_oee_rating(oee) == expected


# =============================================================================
# kpi_calculator — estimate_annual_output
# =============================================================================

def test_estimate_annual_output_multiplies_by_365():
    assert estimate_annual_output(100) == 36500


def test_estimate_annual_output_rounds_to_2dp():
    result = estimate_annual_output(1.555)
    assert result == 567.57  # 1.555 * 365


# =============================================================================
# kpi_calculator — is_world_class_oee
# =============================================================================

def test_is_world_class_oee_returns_true_above_threshold():
    assert is_world_class_oee(0.90) == True


def test_is_world_class_oee_returns_false_below_threshold():
    assert is_world_class_oee(0.70) == False


def test_is_world_class_oee_returns_true_at_threshold():
    assert is_world_class_oee(0.85) == True  # >= 0.85


# =============================================================================
# reporter — get_status_colour
# =============================================================================

@pytest.mark.parametrize("severity, expected", [
    ("Critical", "red"),
    ("Warning",  "amber"),
    ("OK",       "green"),
    ("unknown",  "grey"),
])
def test_get_status_colour(severity, expected):
    assert get_status_colour(severity) == expected


# =============================================================================
# reporter — report_exists (mocking)
# =============================================================================

def test_report_exists_returns_true_when_file_exists():
    with patch("reporter.os.path.exists", return_value=True):
        assert report_exists("some/path/report.txt") == True


def test_report_exists_returns_false_when_file_missing():
    with patch("reporter.os.path.exists", return_value=False):
        assert report_exists("some/path/report.txt") == False


# =============================================================================
# reporter — generate_shift_summary
# =============================================================================

def test_generate_shift_summary_returns_none_for_invalid_machine_id(machine_records):
    result = generate_shift_summary(machine_records, "", 1)
    assert result is None


def test_generate_shift_summary_returns_none_for_invalid_shift(machine_records):
    result = generate_shift_summary(machine_records, "M01", 4)
    assert result is None


def test_generate_shift_summary_returns_correct_output(machine_records):
    result = generate_shift_summary(machine_records, "M01", 1)
    assert result["total_output"] == 500


def test_generate_shift_summary_returns_correct_defect_rate(machine_records):
    result = generate_shift_summary(machine_records, "M01", 1)
    assert result["defect_rate"] == 5.0  # 25 / 500 * 100


def test_generate_shift_summary_includes_output_per_m2_when_floor_area_given(machine_records):
    result = generate_shift_summary(machine_records, "M01", 1, floor_area_m2=500)
    assert result["output_per_m2"] == 1.0  # 500 units / 500 m2