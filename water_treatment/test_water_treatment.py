# test_water_treatment.py
# Tests for the refactored water treatment OOP pipeline.
# Refactor water_treatment.py first, then fill in the ... placeholders.
#
# Run with: pytest test_water_treatment.py -v

import pytest
from water_treatment import Sensor, WaterSample, TreatmentStage, TreatmentPlant


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def ph_sensor():
    return Sensor(
        sensor_id="S01",
        sensor_type="ph",
        stage="filtration",
        location="Tank A",
    )


@pytest.fixture
def turbidity_sensor():
    return Sensor(
        sensor_id="S02",
        sensor_type="turbidity",
        stage="filtration",
        location="Tank B",
        active=False,
    )


@pytest.fixture
def safe_sample():
    return WaterSample(
        sample_id="W01",
        stage="filtration",
        date="2024-06-01",
        ph=7.2,
        turbidity=1.5,
        chlorine=0.8,
        conductivity=450,
        temperature=18.0,
    )


@pytest.fixture
def unsafe_sample():
    return WaterSample(
        sample_id="W02",
        stage="filtration",
        date="2024-06-01",
        ph=9.5,        # too high
        turbidity=6.0, # too high
        chlorine=0.8,
        conductivity=450,
        temperature=18.0,
    )


@pytest.fixture
def critical_sample():
    return WaterSample(
        sample_id="W03",
        stage="disinfection",
        date="2024-06-01",
        ph=5.0,        # too low — critical
        turbidity=1.0,
        chlorine=0.05, # too low — critical
        conductivity=450,
        temperature=18.0,
    )


@pytest.fixture
def filtration_stage():
    return TreatmentStage(
        stage_id="ST01",
        stage_type="filtration",
        capacity_litres=10000,
    )


@pytest.fixture
def plant():
    return TreatmentPlant(
        plant_id="P01",
        name="Hamburg North",
        location="Hamburg",
        daily_capacity_litres=50000,
    )


@pytest.fixture
def loaded_stage(filtration_stage, safe_sample, unsafe_sample):
    filtration_stage.add_sample(safe_sample)
    filtration_stage.add_sample(unsafe_sample)
    return filtration_stage


@pytest.fixture
def loaded_plant(plant, safe_sample, unsafe_sample, critical_sample):
    plant.add_sample(safe_sample)
    plant.add_sample(unsafe_sample)
    plant.add_sample(critical_sample)
    return plant


# =============================================================================
# Sensor — basic attributes
# =============================================================================

def test_sensor_has_correct_id(ph_sensor):
    assert ph_sensor.sensor_id == "S01"


def test_sensor_has_correct_type(ph_sensor):
    assert ph_sensor.sensor_type == "ph"


def test_sensor_is_active_by_default(ph_sensor):
    assert ph_sensor.active == True


def test_sensor_can_be_inactive(turbidity_sensor):
    assert turbidity_sensor.active == False


# =============================================================================
# Sensor — methods
# =============================================================================

def test_get_sensor_unit_for_ph(ph_sensor):
    assert ph_sensor.get_sensor_unit() == "pH"  # Hint: check SENSOR_UNITS


def test_get_sensor_unit_for_turbidity(turbidity_sensor):
    assert turbidity_sensor.get_sensor_unit() == "NTU"


def test_get_alert_level_for_ph(ph_sensor):
    assert ph_sensor.get_alert_level() == "Critical"  # Hint: check ALERT_LEVELS


def test_is_sensor_active_returns_true(ph_sensor):
    assert ph_sensor.is_sensor_active() == ...


def test_is_sensor_active_returns_false_for_inactive(turbidity_sensor):
    assert turbidity_sensor.is_sensor_active() == ...


def test_is_valid_sensor_type_returns_true_for_ph(ph_sensor):
    assert ph_sensor.is_valid_sensor_type() == ...


def test_deactivate_sensor(ph_sensor):
    ph_sensor.deactivate()
    assert ph_sensor.active == ...


def test_sensor_repr(ph_sensor):
    assert repr(ph_sensor) == "Sensor(S01, ph, filtration)"  # Hint: "Sensor(S01, ph, filtration)"


# =============================================================================
# WaterSample — basic attributes
# =============================================================================

def test_sample_has_correct_id(safe_sample):
    assert safe_sample.sample_id == "W01"


def test_sample_has_correct_ph(safe_sample):
    assert safe_sample.ph == 7.2


def test_sample_has_correct_stage(safe_sample):
    assert safe_sample.stage == "filtration"


# =============================================================================
# WaterSample — safety checks
# =============================================================================

def test_is_ph_safe_returns_true_for_safe_sample(safe_sample):
    assert safe_sample.is_ph_safe() == True  # ph=7.2, range 6.5-8.5


def test_is_ph_safe_returns_false_for_unsafe_sample(unsafe_sample):
    assert unsafe_sample.is_ph_safe() == False  # ph=9.5


def test_is_turbidity_safe_returns_true(safe_sample):
    assert safe_sample.is_turbidity_safe() == True  # 1.5 NTU, max 4.0


def test_is_turbidity_safe_returns_false(unsafe_sample):
    assert unsafe_sample.is_turbidity_safe() == False  # 6.0 NTU


def test_is_chlorine_safe_returns_true(safe_sample):
    assert safe_sample.is_chlorine_safe() == True  # 0.8, range 0.2-4.0


def test_is_chlorine_safe_returns_false_too_low(critical_sample):
    assert critical_sample.is_chlorine_safe() == False  # 0.05 mg/L


def test_is_sample_safe_returns_true_for_safe(safe_sample):
    assert safe_sample.is_sample_safe() == True


def test_is_sample_safe_returns_false_for_unsafe(unsafe_sample):
    assert unsafe_sample.is_sample_safe() == False


# =============================================================================
# WaterSample — get_failed_parameters
# =============================================================================

def test_get_failed_parameters_returns_empty_for_safe(safe_sample):
    assert safe_sample.get_failed_parameters() == ...


def test_get_failed_parameters_returns_ph_and_turbidity(unsafe_sample):
    failed = unsafe_sample.get_failed_parameters()
    assert "ph" in failed
    assert "turbidity" in failed
    assert len(failed) == ...  # only ph and turbidity fail


def test_get_failed_parameters_returns_ph_and_chlorine(critical_sample):
    failed = critical_sample.get_failed_parameters()
    assert "ph" in failed
    assert "chlorine" in failed


# =============================================================================
# WaterSample — boundary tests
# =============================================================================

@pytest.mark.parametrize("ph, expected", [
    (6.5,  True),   # lower boundary — inclusive
    (8.5,  True),   # upper boundary — inclusive
    (6.49, False),  # just below
    (8.51, False),  # just above
    (7.0,  True),   # typical safe
])
def test_ph_boundary(ph, expected):
    sample = WaterSample("W99", "filtration", "2024-06-01",
                         ph=ph, turbidity=1.0, chlorine=1.0,
                         conductivity=400, temperature=15.0)
    assert sample.is_ph_safe() == expected


@pytest.mark.parametrize("turbidity, expected", [
    (4.0,  True),   # boundary — inclusive
    (4.01, False),  # just above
    (0.0,  True),   # clean water
])
def test_turbidity_boundary(turbidity, expected):
    sample = WaterSample("W99", "filtration", "2024-06-01",
                         ph=7.0, turbidity=turbidity, chlorine=1.0,
                         conductivity=400, temperature=15.0)
    assert sample.is_turbidity_safe() == expected


# =============================================================================
# WaterSample — __repr__
# =============================================================================

def test_safe_sample_repr(safe_sample):
    assert repr(safe_sample) == ...  # Hint: "WaterSample(W01, filtration, 2024-06-01, SAFE)"


def test_unsafe_sample_repr(unsafe_sample):
    assert repr(unsafe_sample) == ...  # Hint: "WaterSample(W02, filtration, 2024-06-01, UNSAFE)"


# =============================================================================
# TreatmentStage — basic attributes
# =============================================================================

def test_stage_has_correct_id(filtration_stage):
    assert filtration_stage.stage_id == ...


def test_stage_starts_with_no_samples(filtration_stage):
    assert len(filtration_stage.samples) == ...


# =============================================================================
# TreatmentStage — add_sample / get_stage_label
# =============================================================================

def test_add_sample_increases_count(filtration_stage, safe_sample):
    filtration_stage.add_sample(safe_sample)
    assert len(filtration_stage.samples) == ...


def test_get_stage_label_for_filtration(filtration_stage):
    assert filtration_stage.get_stage_label() == ...  # Hint: check STAGE_LABELS


# =============================================================================
# TreatmentStage — get_stage_pass_rate
# =============================================================================

def test_get_stage_pass_rate_returns_100_when_all_safe(filtration_stage, safe_sample):
    filtration_stage.add_sample(safe_sample)
    assert filtration_stage.get_stage_pass_rate() == ...


def test_get_stage_pass_rate_returns_50_when_half_safe(loaded_stage):
    assert loaded_stage.get_stage_pass_rate() == ...  # 1 safe, 1 unsafe


def test_get_stage_pass_rate_returns_0_when_no_samples(filtration_stage):
    assert filtration_stage.get_stage_pass_rate() == ...


# =============================================================================
# TreatmentStage — get_average_ph / get_average_turbidity
# =============================================================================

def test_get_average_ph(loaded_stage):
    # safe: 7.2, unsafe: 9.5 → mean = 8.35
    assert loaded_stage.get_average_ph() == ...


def test_get_average_turbidity(loaded_stage):
    # safe: 1.5, unsafe: 6.0 → mean = 3.75
    assert loaded_stage.get_average_turbidity() == ...


def test_get_average_ph_returns_none_when_no_samples(filtration_stage):
    assert filtration_stage.get_average_ph() is ...


# =============================================================================
# TreatmentPlant — basic attributes
# =============================================================================

def test_plant_has_correct_id(plant):
    assert plant.plant_id == ...


def test_plant_starts_with_no_samples(plant):
    assert len(plant.samples) == ...


# =============================================================================
# TreatmentPlant — get_plant_pass_rate / is_plant_compliant
# =============================================================================

def test_get_plant_pass_rate_returns_100_when_all_safe(plant, safe_sample):
    plant.add_sample(safe_sample)
    assert plant.get_plant_pass_rate() == ...


def test_get_plant_pass_rate_correct(loaded_plant):
    # 1 safe out of 3 total = 33.33%
    assert plant.get_plant_pass_rate() == ...


def test_is_plant_compliant_returns_true_when_pass_rate_high(plant, safe_sample):
    plant.add_sample(safe_sample)
    assert plant.is_plant_compliant() == ...  # 100% >= 95%


def test_is_plant_compliant_returns_false_when_pass_rate_low(loaded_plant):
    assert loaded_plant.is_plant_compliant() == ...  # 33% < 95%


# =============================================================================
# TreatmentPlant — has_critical_failure
# =============================================================================

def test_has_critical_failure_returns_false_when_all_safe(plant, safe_sample):
    plant.add_sample(safe_sample)
    assert plant.has_critical_failure() == ...


def test_has_critical_failure_returns_true_when_ph_fails(plant, critical_sample):
    plant.add_sample(critical_sample)
    assert plant.has_critical_failure() == ...  # ph=5.0 fails


# =============================================================================
# TreatmentPlant — get_worst_stage
# =============================================================================

def test_get_worst_stage_returns_stage_with_lowest_pass_rate(loaded_plant):
    # filtration: 1 safe 1 unsafe = 50%, disinfection: 0 safe 1 unsafe = 0%
    assert loaded_plant.get_worst_stage() == ...


def test_get_worst_stage_returns_none_when_no_samples(plant):
    assert plant.get_worst_stage() is ...


# =============================================================================
# TreatmentPlant — __repr__
# =============================================================================

def test_plant_repr_compliant(plant, safe_sample):
    plant.add_sample(safe_sample)
    assert repr(plant) == ...  # Hint: "TreatmentPlant(P01, Hamburg North, COMPLIANT)"


def test_plant_repr_non_compliant(loaded_plant):
    assert repr(loaded_plant) == ...  # Hint: "TreatmentPlant(P01, Hamburg North, NON-COMPLIANT)"
