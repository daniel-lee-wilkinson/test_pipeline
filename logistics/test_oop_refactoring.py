# test_oop_refactoring.py
# Tests for the refactored OOP logistics classes.
# Refactor oop_refactoring.py first, then fill in the ... placeholders.
#
# Run with: pytest test_oop_refactoring.py -v

import pytest
import datetime
from oop_refactoring import Shipment, Vehicle, Depot, DeliveryRoute


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def standard_shipment():
    return Shipment(
        shipment_id="S001",
        weight_kg=50.0,
        distance_km=120.0,
        status="delivered",
        priority=1,
        depot_code="HAM",
        scheduled_date=datetime.date(2024, 6, 1),
        actual_date=datetime.date(2024, 6, 1),
    )


@pytest.fixture
def late_shipment():
    return Shipment(
        shipment_id="S002",
        weight_kg=600.0,
        distance_km=800.0,
        status="delivered",
        priority=2,
        depot_code="HAM",
        scheduled_date=datetime.date(2024, 6, 1),
        actual_date=datetime.date(2024, 6, 4),
    )


@pytest.fixture
def failed_shipment():
    return Shipment(
        shipment_id="S003",
        weight_kg=10.0,
        distance_km=50.0,
        status="failed",
        priority=1,
        depot_code="BER",
        scheduled_date=datetime.date(2024, 6, 1),
        actual_date=None,
    )


@pytest.fixture
def van():
    return Vehicle(vehicle_id="V01", vehicle_type="van", depot_code="HAM")


@pytest.fixture
def cargo_bike():
    return Vehicle(vehicle_id="V02", vehicle_type="cargo_bike", depot_code="HAM")


@pytest.fixture
def hamburg_depot():
    return Depot(depot_code="HAM", region="Hamburg", capacity=100)


@pytest.fixture
def route(standard_shipment, late_shipment):
    r = DeliveryRoute(route_id="R001", vehicle_id="V01", date="2024-06-01")
    r.add_stop(standard_shipment)
    r.add_stop(late_shipment)
    return r


# =============================================================================
# Shipment — basic attributes
# =============================================================================
# Hint: after __init__, attributes should be accessible as self.shipment_id etc.

def test_shipment_has_correct_id(standard_shipment):
    assert standard_shipment.shipment_id == ...


def test_shipment_has_correct_weight(standard_shipment):
    assert standard_shipment.weight_kg == ...


def test_shipment_has_correct_status(standard_shipment):
    assert standard_shipment.status == ...


# =============================================================================
# Shipment — is_heavy / is_long_haul
# =============================================================================

def test_is_heavy_returns_false_for_light_shipment(standard_shipment):
    assert standard_shipment.is_heavy() == ...  # 50 kg, threshold is 500


def test_is_heavy_returns_true_for_heavy_shipment(late_shipment):
    assert late_shipment.is_heavy() == ...  # 600 kg


def test_is_long_haul_returns_false_for_short(standard_shipment):
    assert standard_shipment.is_long_haul() == ...  # 120 km


def test_is_long_haul_returns_true_for_long(late_shipment):
    assert late_shipment.is_long_haul() == ...  # 800 km


# =============================================================================
# Shipment — is_delivered / is_failed
# =============================================================================

def test_is_delivered_returns_true_for_delivered(standard_shipment):
    assert standard_shipment.is_delivered() == ...


def test_is_delivered_returns_false_for_failed(failed_shipment):
    assert failed_shipment.is_delivered() == ...


def test_is_failed_returns_true_for_failed(failed_shipment):
    assert failed_shipment.is_failed() == ...


# =============================================================================
# Shipment — is_late / days_overdue
# =============================================================================

def test_is_late_returns_false_when_on_time(standard_shipment):
    assert standard_shipment.is_late() == ...


def test_is_late_returns_true_when_late(late_shipment):
    assert late_shipment.is_late() == ...  # actual 4 June, scheduled 1 June


def test_is_late_returns_false_when_no_actual_date(failed_shipment):
    assert failed_shipment.is_late() == ...


def test_days_overdue_returns_zero_when_on_time(standard_shipment):
    assert standard_shipment.days_overdue() == ...


def test_days_overdue_returns_correct_days(late_shipment):
    assert late_shipment.days_overdue() == ...  # 3 days late


def test_days_overdue_returns_zero_when_no_actual_date(failed_shipment):
    assert failed_shipment.days_overdue() == ...


# =============================================================================
# Shipment — get_delivery_cost
# =============================================================================
# Hint: base=2.50, weight*0.15, distance*0.08, multiplied by priority

def test_get_delivery_cost_standard_priority(standard_shipment):
    # base=2.50, weight=50*0.15=7.50, distance=120*0.08=9.60, multiplier=1.0
    assert standard_shipment.get_delivery_cost() == pytest.approx(19.6)


def test_get_delivery_cost_express_priority(late_shipment):
    # same formula, multiplier=1.5
    assert late_shipment.get_delivery_cost() == pytest.approx(...)


# =============================================================================
# Shipment — get_status_label
# =============================================================================

def test_get_status_label_delivered(standard_shipment):
    assert standard_shipment.get_status_label() == ...


def test_get_status_label_failed(failed_shipment):
    assert failed_shipment.get_status_label() == ...


# =============================================================================
# Shipment — __repr__
# =============================================================================

def test_shipment_repr(standard_shipment):
    assert repr(standard_shipment) == ...  # Hint: "Shipment(S001, delivered, 50.0kg, 120.0km)"


# =============================================================================
# Vehicle — basic attributes
# =============================================================================

def test_vehicle_has_correct_id(van):
    assert van.vehicle_id == ...


def test_vehicle_has_correct_type(van):
    assert van.vehicle_type == ...


# =============================================================================
# Vehicle — is_active / is_electric
# =============================================================================

def test_is_active_returns_true_by_default(van):
    assert van.is_active() == ...


def test_is_electric_returns_false_for_van(van):
    assert van.is_electric() == ...


def test_is_electric_returns_true_for_cargo_bike(cargo_bike):
    assert cargo_bike.is_electric() == ...


# =============================================================================
# Vehicle — get_fuel_estimate / get_carbon_kg
# =============================================================================

def test_get_fuel_estimate_for_van(van):
    assert van.get_fuel_estimate(100) == ...  # 100 km * 0.12


def test_get_fuel_estimate_for_cargo_bike(cargo_bike):
    assert cargo_bike.get_fuel_estimate(100) == ...  # cargo bike uses no fuel


def test_get_carbon_kg_for_van(van):
    assert van.get_carbon_kg(100) == ...  # 100 km * 0.17


# =============================================================================
# Vehicle — get_vehicle_label
# =============================================================================

def test_get_vehicle_label_for_van(van):
    assert van.get_vehicle_label() == ...


def test_get_vehicle_label_for_cargo_bike(cargo_bike):
    assert cargo_bike.get_vehicle_label() == ...


# =============================================================================
# Vehicle — __repr__
# =============================================================================

def test_vehicle_repr(van):
    assert repr(van) == ...  # Hint: "Vehicle(V01, van, HAM)"


# =============================================================================
# Depot — basic attributes
# =============================================================================

def test_depot_has_correct_code(hamburg_depot):
    assert hamburg_depot.depot_code == ...


def test_depot_starts_with_empty_shipments(hamburg_depot):
    assert len(hamburg_depot.shipments) == ...


# =============================================================================
# Depot — add_shipment / get_total_shipments
# =============================================================================

def test_add_shipment_increases_count(hamburg_depot, standard_shipment):
    hamburg_depot.add_shipment(standard_shipment)
    assert hamburg_depot.get_total_shipments() == ...


def test_add_multiple_shipments(hamburg_depot, standard_shipment, late_shipment):
    hamburg_depot.add_shipment(standard_shipment)
    hamburg_depot.add_shipment(late_shipment)
    assert hamburg_depot.get_total_shipments() == ...


# =============================================================================
# Depot — get_delivery_rate
# =============================================================================

def test_get_delivery_rate_returns_100_when_all_delivered(hamburg_depot, standard_shipment):
    hamburg_depot.add_shipment(standard_shipment)
    assert hamburg_depot.get_delivery_rate() == ...


def test_get_delivery_rate_returns_correct_rate(hamburg_depot, standard_shipment, failed_shipment):
    # Hint: failed_shipment has depot_code BER not HAM — add a HAM failed one
    ham_failed = Shipment("S999", 10.0, 50.0, "failed", 1, "HAM",
                          datetime.date(2024, 6, 1), None)
    hamburg_depot.add_shipment(standard_shipment)
    hamburg_depot.add_shipment(ham_failed)
    assert hamburg_depot.get_delivery_rate() == ...  # 1 delivered, 1 failed = 50.0%


# =============================================================================
# Depot — is_over_capacity
# =============================================================================

def test_is_over_capacity_returns_false_when_under(hamburg_depot, standard_shipment):
    hamburg_depot.add_shipment(standard_shipment)
    assert hamburg_depot.is_over_capacity() == ...  # 1 shipment, capacity 100


def test_is_over_capacity_returns_true_when_over():
    small_depot = Depot("HAM", "Hamburg", capacity=1)
    small_depot.add_shipment(Shipment("S001", 10.0, 50.0, "delivered", 1, "HAM",
                                      datetime.date(2024, 6, 1), datetime.date(2024, 6, 1)))
    small_depot.add_shipment(Shipment("S002", 10.0, 50.0, "delivered", 1, "HAM",
                                      datetime.date(2024, 6, 1), datetime.date(2024, 6, 1)))
    assert small_depot.is_over_capacity() == ...  # 2 shipments, capacity 1


# =============================================================================
# DeliveryRoute — basic structure
# =============================================================================

def test_route_starts_with_no_stops():
    r = DeliveryRoute("R001", "V01", "2024-06-01")
    assert len(r) == ...


def test_add_stop_increases_length(route):
    assert len(route) == ...  # fixture adds 2 stops


# =============================================================================
# DeliveryRoute — calculations
# =============================================================================

def test_get_total_route_distance(route):
    # standard: 120 km, late: 800 km
    assert route.get_total_route_distance() == ...


def test_get_total_route_weight(route):
    # standard: 50 kg, late: 600 kg
    assert route.get_total_route_weight() == ...


def test_get_route_completion_rate(route):
    # both delivered = 100%
    assert route.get_route_completion_rate() == ...


def test_has_failed_stop_returns_false_when_all_delivered(route):
    assert route.has_failed_stop() == ...


def test_has_failed_stop_returns_true_when_one_failed(route, failed_shipment):
    route.add_stop(failed_shipment)
    assert route.has_failed_stop() == ...


def test_get_heaviest_stop_returns_correct_shipment(route):
    heaviest = route.get_heaviest_stop()
    assert heaviest.shipment_id == ...  # late_shipment has 600 kg


# =============================================================================
# DeliveryRoute — __repr__ / __len__
# =============================================================================

def test_route_repr(route):
    assert repr(route) == ...  # Hint: "DeliveryRoute(R001, V01, 2024-06-01, 2 stops)"
