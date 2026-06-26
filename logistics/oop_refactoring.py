# oop_refactoring.py
# Refactor procedural code into classes.
# Each section below is a group of functions that belong together.
# Hints tell you what class to create and which functions become methods.
#
# General pattern:
#   1. Create a class with __init__ that takes the data as parameters
#   2. Move each function in as a method — the dict argument becomes self
#   3. Replace dict["key"] with self.key
#   4. Remove the first argument (the dict) from each method signature
from docutils.nodes import status

HEAVY_THRESHOLD_KG = 500
LONG_HAUL_THRESHOLD_KM = 500
COST_PER_KG_KM = 0.002
BASE_DELIVERY_COST = 2.50

PRIORITY_MULTIPLIERS = {1: 1.0, 2: 1.5, 3: 2.5}
CARBON_FACTORS = {
    "truck": 0.21,
    "van": 0.17,
    "cargo_bike": 0.0,
    "drone": 0.01,
}
FUEL_RATES = {
    "truck": 0.35,
    "van": 0.12,
    "cargo_bike": 0.0,
    "drone": 0.05,
}


# =============================================================================
# SECTION 1: Shipment
# Hint: create a Shipment class.
# __init__ should take: shipment_id, weight_kg, distance_km, status, priority,
#                       depot_code, scheduled_date, actual_date=None
# All the functions below take a shipment dict — make them methods instead.
# =============================================================================

class Shipment:

    def __init__(self, shipment_id, weight_kg, distance_km, status, priority,
                 depot_code, scheduled_date, actual_date=None):
        self.shipment_id = shipment_id
        self.weight_kg = weight_kg
        self.distance_km = distance_km
        self.status = status
        self.priority = priority
        self.depot_code = depot_code
        self.scheduled_date = scheduled_date
        self.actual_date = actual_date

    def is_heavy(self):
        return self.weight_kg > HEAVY_THRESHOLD_KG


    def is_long_haul(self):
        return self.distance_km > LONG_HAUL_THRESHOLD_KM


    def is_delivered(self):
        return self.status == "delivered"


    def is_failed(self):
        return self.status == "failed"


    def is_late(self):
        if self.actual_date is None:
            return False
        return self.actual_date > self.scheduled_date


    def days_overdue(self):
        if self.actual_date is None:
            return 0
        delta = self.actual_date - self.scheduled_date
        return max(delta.days, 0)


    def get_delivery_cost(self):
        multiplier = PRIORITY_MULTIPLIERS.get(self.priority, 1.0)
        base_cost = BASE_DELIVERY_COST + self.weight_kg * 0.15 + self.distance_km * 0.08
        return round(base_cost * multiplier, 2)


    def get_status_label(self):
        labels = {
            "pending":    "Awaiting dispatch",
            "in_transit": "On its way",
            "delivered":  "Successfully delivered",
            "failed":     "Delivery failed",
            "returned":   "Returned to depot",
        }
        return labels.get(self.status, "Unknown")

    def __repr__(self):
        return f"Shipment({self.shipment_id}, {self.status}, {self.weight_kg}kg, {self.distance_km}km)"

# Hint: add a __repr__ method that returns something like:
# "Shipment(S001, delivered, 50.0kg, 120.0km)"


# =============================================================================
# SECTION 2: Vehicle
# Hint: create a Vehicle class.
# __init__ should take: vehicle_id, vehicle_type, depot_code, active=True
# The functions below operate on a vehicle dict — make them methods.
# =============================================================================


class Vehicle:
    def __init__(self, vehicle_id, vehicle_type, depot_code, active=True):
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.depot_code = depot_code
        self.active = active

    def get_fuel_estimate(self, distance_km):
        rate = FUEL_RATES.get(self.vehicle_type, 0)
        return round(distance_km * rate, 2)


    def get_carbon_kg(self, distance_km):
        factor = CARBON_FACTORS.get(self.vehicle_type, 0)
        return round(distance_km * factor, 2)


    def is_active(self):
        return self.active


    def is_electric(self):
        return self.vehicle_type in ["cargo_bike", "drone"]


    def get_vehicle_label(self):
        labels = {
            "truck":      "Heavy Goods Vehicle",
            "van":        "Delivery Van",
            "cargo_bike": "Cargo Bicycle",
            "drone":      "Autonomous Drone",
        }
        return labels.get(self.vehicle_type, "Unknown Vehicle")


# Hint: add a __repr__ method that returns something like:
# "Vehicle(V01, truck, HAM)"


# =============================================================================
# SECTION 3: Depot
# Hint: create a Depot class.
# __init__ should take: depot_code, region, capacity
# The functions below operate on a depot dict and a list of shipments.
# Hint: store shipments as self.shipments = [] and add an add_shipment method.
# =============================================================================

class Depot:
    def __init__(self, depot_code, region, capacity):
        self.depot_code = depot_code
        self.region = region
        self.capacity = capacity
        self.shipments = []

    def add_shipment(self, shipment):
        self.shipments.append(shipment)
        
        
    def get_total_shipments(self):
        return len(self.shipments)


    def get_delivery_rate(self):
        if not self.shipments:
            return 0
        delivered = [s for s in self.shipments if s.is_delivered()]
        return round(len(delivered) / len(self.shipments) * 100, 2)


    def get_total_weight(self):
        return round(sum(s.weight_kg for s in self.shipments), 2)


    def get_total_distance(self):
        return round(sum(s.distance_km for s in self.shipments), 2)


    def is_over_capacity(self):
        total = self.get_total_shipments()
        return total > self.capacity

    def get_failed_shipments(self):
        return [s for s in self.shipments if s.is_failed()]

    def summary(self):
        return {
            "depot_code": self.depot_code,
            "region": self.region,
            "total_shipments": self.get_total_shipments(),
            "delivery_rate": self.get_delivery_rate(),
            "over_capacity": self.is_over_capacity(),
        }

# Hint: add a summary() method that returns a dict with:
# depot_code, region, total_shipments, delivery_rate, total_weight_kg, over_capacity


# =============================================================================
# SECTION 4: DeliveryRoute
# Hint: create a DeliveryRoute class.
# __init__ should take: route_id, vehicle_id, date, stops=None
# stops is a list of shipment dicts (or Shipment objects once you refactor).
# Hint: add an add_stop(shipment) method.
# The functions below operate on a route dict with a list of stops.
# =============================================================================
class DeliveryRoute:
    def __init__(self, route_id, vehicle_id, date, stops=None):
        self.route_id = route_id
        self.vehicle_id = vehicle_id
        self.date = date
        self.stops = stops if stops is not None else []
        

    def get_total_route_distance(self):
        return round(sum(s.distance_km for s in self.stops), 2)


    def get_total_route_weight(self):
        return round(sum(s.weight_kg for s in self.stops), 2)


    def get_route_completion_rate(self):
        if not self.stops:
            return 0
        delivered = [s for s in self.stops if s.is_delivered()]
        return round(len(delivered) / len(self.stops) * 100, 2)


    def has_failed_stop(self):
        return any(s.is_failed() for s in self.stops)


    def get_heaviest_stop(self):
        if not self.stops:
            return None
        return max(self.stops, key=lambda s: s.weight_kg)

    def get_route_carbon_estimate(self, vehicle_type):
        factor = CARBON_FACTORS.get(vehicle_type, 0)
        return round(self.get_total_route_distance() * factor, 2)

    def add_stop(self, shipment):
        self.stops.append(shipment)

    def __len__(self):
        return len(self.stops)

    def __repr__(self):
        return f"DeliveryRoute({self.route_id}, {self.vehicle_id}, {self.date}, {len(self.stops)} stops)"


# Hint: add a __len__ method that returns the number of stops
# Hint: add a __repr__ method that returns something like:
# "DeliveryRoute(R001, V01, 2024-06-01, 3 stops)"


# =============================================================================
# EXAMPLE USAGE (shows how the procedural code currently works)
# After refactoring, update this to use your new classes.
# =============================================================================

if __name__ == "__main__":
    import datetime

    s = Shipment(
        shipment_id="S001",
        weight_kg=50.0,
        distance_km=120.0,
        status="delivered",
        priority=2,
        depot_code="HAM",
        scheduled_date=datetime.date(2024, 6, 1),
        actual_date=datetime.date(2024, 6, 3),
    )

    v = Vehicle(vehicle_id="V01", vehicle_type="van", depot_code="HAM")

    d = Depot(depot_code="HAM", region="Hamburg", capacity=100)
    d.add_shipment(s)

    print(s.is_heavy())
    print(s.is_late())
    print(s.days_overdue())
    print(s.get_delivery_cost())
    print(s.get_status_label())
    print(v.get_fuel_estimate(120))
    print(v.get_carbon_kg(120))
    print(v.get_vehicle_label())
    print(d.get_delivery_rate())
    print(d.is_over_capacity())