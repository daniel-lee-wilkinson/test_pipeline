# water_treatment.py
# Procedural pipeline for a water treatment plant.
# Goal: refactor into classes — Sensor, TreatmentStage, WaterSample, TreatmentPlant
# No hints on which refactoring type — identify issues yourself.
# After refactoring, fill in the test file.

import statistics
import datetime

# --- Constants ---
PH_MIN = 6.5
PH_MAX = 8.5
TURBIDITY_MAX = 4.0       # NTU
CHLORINE_MIN = 0.2        # mg/L
CHLORINE_MAX = 4.0        # mg/L
CONDUCTIVITY_MAX = 2500   # µS/cm
TEMP_MAX = 25.0           # °C
ALERT_CONSECUTIVE_DAYS = 3
DAILY_CAPACITY_LITRES = 50000

VALID_SENSOR_TYPES = ["ph", "turbidity", "chlorine", "conductivity", "temperature"]
VALID_STAGES = ["intake", "screening", "coagulation", "filtration", "disinfection", "distribution"]

STAGE_LABELS = {
    "intake":        "Raw Water Intake",
    "screening":     "Screening & Grit Removal",
    "coagulation":   "Coagulation & Flocculation",
    "filtration":    "Sand & Carbon Filtration",
    "disinfection":  "Chlorination & UV",
    "distribution":  "Distribution Network",
}

SENSOR_UNITS = {
    "ph":            "pH",
    "turbidity":     "NTU",
    "chlorine":      "mg/L",
    "conductivity":  "µS/cm",
    "temperature":   "°C",
}

ALERT_LEVELS = {
    "ph":           "Critical",
    "turbidity":    "High",
    "chlorine":     "Critical",
    "conductivity": "Medium",
    "temperature":  "Low",
}


# =============================================================================
# GROUP 1: Sensor functions
# Hint: these all operate on a sensor dict — make them a Sensor class.
# __init__ should take: sensor_id, sensor_type, stage, location, active=True
# =============================================================================

class Sensor:
    def __init__(self, sensor_type, location, sensor_id, stage, active=True):
        self.sensor_type = sensor_type
        self.active = active
        self.location = location
        self.sensor_id = sensor_id
        self.stage = stage
        

    def get_sensor_unit(self):
        return SENSOR_UNITS.get(self.sensor_type, "unknown")


    def get_alert_level(self):
        return ALERT_LEVELS.get(self.sensor_type, "Unknown")


    def is_sensor_active(self):
        return bool(self.active)


    def get_sensor_label(self):
        unit = SENSOR_UNITS.get(self.sensor_type, "unknown")
        return f"{self.sensor_type.upper()} Sensor [{unit}] @ {self.location}"


    def is_valid_sensor_type(self):
        return bool(self.sensor_type in VALID_SENSOR_TYPES)


    def deactivate(self):
        self.active = False

    def __repr__(self):
        return f"Sensor({self.sensor_id}, {self.sensor_type}, {self.stage})"
        # Hint: add __repr__ returning e.g. "Sensor(S01, ph, filtration)"


# =============================================================================
# GROUP 2: WaterSample functions
# Hint: these all operate on a sample dict — make them a WaterSample class.
# __init__ should take: sample_id, stage, date, ph, turbidity, chlorine,
#                       conductivity, temperature
# =============================================================================
class WaterSample:
    def __init__(self,sample_id, stage, date, ph, turbidity, chlorine, conductivity, temperature):
        self.ph = ph
        self.turbidity=turbidity
        self.chlorine=chlorine
        self.conductivity=conductivity
        self.temperature=temperature
        self.sample_id=sample_id
        self.stage=stage
        self.date=date


    def is_ph_safe(self):
        return PH_MIN <= self.ph <= PH_MAX


    def is_turbidity_safe(self):
        return self.turbidity <= TURBIDITY_MAX


    def is_chlorine_safe(self):
        return CHLORINE_MIN <= self.chlorine <= CHLORINE_MAX


    def is_conductivity_safe(self):
        return self.conductivity <= CONDUCTIVITY_MAX


    def is_temperature_safe(self):
        return self.temperature <= TEMP_MAX


    def is_sample_safe(self):
        return (
            self.is_ph_safe() and
            self.is_turbidity_safe() and
            self.is_chlorine_safe() and
            self.is_conductivity_safe() and
            self.is_temperature_safe()
        )


    def get_failed_parameters(self):
        """Return list of parameter names that are out of safe range."""
        failed = []
        if not self.is_ph_safe():
            failed.append("ph")
        if not self.is_turbidity_safe():
            failed.append("turbidity")
        if not self.is_chlorine_safe():
            failed.append("chlorine")
        if not self.is_conductivity_safe():
            failed.append("conductivity")
        if not self.is_temperature_safe():
            failed.append("temperature")
        return failed


    def get_sample_summary(self):
        safe = self.is_sample_safe()
        failed = self.get_failed_parameters()
        return {
            "sample_id": self.sample_id,
            "stage": self.stage,
            "date": self.date,
            "safe": safe,
            "failed_parameters": failed,
            "ph": self.ph,
            "turbidity": self.turbidity,
            "chlorine": self.chlorine,
        }

    def __repr__(self):
        status = "SAFE" if self.is_sample_safe() else "UNSAFE"
        return f"WaterSample({self.sample_id}, {self.stage}, {self.date}, {status})"

# Hint: add __repr__ returning e.g. "WaterSample(W01, filtration, 2024-06-01, SAFE)"
# where SAFE/UNSAFE reflects is_sample_safe()


# =============================================================================
# GROUP 3: TreatmentStage functions
# Hint: these operate on a stage dict and a list of samples.
# __init__ should take: stage_id, stage_type, capacity_litres
# Hint: store samples as self.samples = [] with an add_sample method.
# =============================================================================

class TreatmentStage:
    def __init__(self, stage_id, stage_type,capacity_litres):
        self.stage_type=stage_type
        self.stage=stage_id
        self.capacity_litres=capacity_litres
        self.samples=[]
        
    def add_sample(self, sample):
        self.samples.append(sample)
    
    def get_stage_label(self):
        return STAGE_LABELS.get(self.stage_type, "Unknown Stage")
    
    
    def get_stage_pass_rate(self):
        if not self.samples:
            return 0
        safe = [s for s in self.samples if s.is_sample_safe()]
        return round(len(safe) / len(self.samples) * 100, 2)
    
    
    def is_stage_at_capacity(self):
        return len(self.samples) >= self.capacity_litres
    
    
    def get_recent_failures(self, days=7):
        cutoff = datetime.date.today() - datetime.timedelta(days=days)
        return [s for s in self.samples if not s.is_sample_safe() and s.date >= str(cutoff)]
    
    
    def get_average_ph(self):
        if not self.samples:
            return None
        return round(statistics.mean(s.ph for s in self.samples), 3)
    
    
    def get_average_turbidity(self):
        if not self.samples:
            return None
        return round(statistics.mean(s.turbidity for s in self.samples), 3)


    # Hint: add a summary() method returning a dict with stage_type, label,
    # total_samples, pass_rate, avg_ph, avg_turbidity

    def summary(self):
        return {
            "total_samples": len(self.samples),
            "pass_rate": self.get_stage_pass_rate(),
            "avg_ph": self.get_average_ph(),
            "avg_turbidity": self.get_average_turbidity(),
            "stage_type": self.stage_type,
            "label":self.get_stage_label()
        }

# =============================================================================
# GROUP 4: TreatmentPlant functions
# Hint: these operate on a plant dict and collections of stages and samples.
# __init__ should take: plant_id, name, location, daily_capacity_litres
# Hint: store stages as self.stages = [] with add_stage / get_stage methods.
# Hint: store samples as self.samples = [] with add_sample method.
# =============================================================================

class TreatmentPlant:

    def __init__(self, plant_id, name, location, daily_capacity_litres):
        self.plant_id = plant_id
        self.name = name
        self.location = location
        self.daily_capacity_litres = daily_capacity_litres
        self.stages = []
        self.samples = []

    def add_sample(self, sample):
        self.samples.append(sample)
        

    
    def get_plant_pass_rate(self):
        if not self.samples:
            return 0
        safe = [s for s in self.samples if s.is_sample_safe()]
        return round(len(safe) / len(self.samples) * 100, 2)


    def is_plant_compliant(self):
        """Return True if overall pass rate is >= 95%."""
        return self.get_plant_pass_rate() >= 95.0

    def get_worst_stage(self):
        rates = {}
        for stage_type in VALID_STAGES:
            stage_samples = [s for s in self.samples if s.stage == stage_type]
            if not stage_samples:
                continue
            safe = [s for s in stage_samples if s.is_sample_safe()]
            rates[stage_type] = len(safe) / len(stage_samples) * 100
        if not rates:
            return None
        return min(rates, key=lambda k: rates[k])


    def get_daily_sample_count(self, date):
        return len([s for s in self.samples if s.date == date])

    def has_critical_failure(self):
        for s in self.samples:
            if "ph" in s.get_failed_parameters() or "chlorine" in s.get_failed_parameters():
                return True
        return False

    def get_plant_summary(self):
        return {
            "plant_id": self.plant_id,
            "name": self.name,
            "location": self.location,
            "total_samples": len(self.samples),
            "pass_rate": self.get_plant_pass_rate(),
            "compliant": self.is_plant_compliant(),
            "worst_stage": self.get_worst_stage(),
            "critical_failure": self.has_critical_failure(),
        }

    def __repr__(self):
        status = "COMPLIANT" if self.is_plant_compliant() else "NON-COMPLIANT"
        return f"TreatmentPlant({self.plant_id}, {self.name}, {status})"


# =============================================================================
# EXAMPLE USAGE — update this to use your new classes after refactoring
# =============================================================================

if __name__ == "__main__":
    sensor = {
        "sensor_id": "S01",
        "sensor_type": "ph",
        "stage": "filtration",
        "location": "Tank A",
        "active": True,
    }

    sample = {
        "sample_id": "W01",
        "stage": "filtration",
        "date": "2024-06-01",
        "ph": 7.2,
        "turbidity": 1.5,
        "chlorine": 0.8,
        "conductivity": 450,
        "temperature": 18.0,
    }

    stage = {
        "stage_id": "ST01",
        "stage_type": "filtration",
        "capacity_litres": 10000,
    }

    plant = {
        "plant_id": "P01",
        "name": "Hamburg North",
        "location": "Hamburg",
        "daily_capacity_litres": DAILY_CAPACITY_LITRES,
    }

    samples = [sample]

