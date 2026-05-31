"""Constants for the Medication Reminder integration."""

import re

DOMAIN = "medication_reminder"

CONF_PATIENT = "patient"
CONF_PATIENT_TYPE = "patient_type"
CONF_DOSES = "doses"
CONF_TIME = "time"
CONF_MEDS = "meds"
CONF_DAYS = "days"
CONF_NOTIFY = "notify"
CONF_RESET_TIME = "reset_time"
CONF_NAG_MINUTES = "nag_minutes"
CONF_NAG_INTERVAL = "nag_interval"
CONF_TIME_FORMAT = "time_format"

# Supply / refill tracking (per medication).
CONF_SUPPLIES = "supplies"
CONF_SUPPLY_MED = "supply_med"
CONF_SUPPLY_UNITS = "supply_units"
CONF_SUPPLY_PER_DOSE = "supply_per_dose"
CONF_SUPPLY_THRESHOLD = "supply_threshold"
CONF_SUPPLY_REFILL_TO = "supply_refill_to"

# Weekday codes, indexed by Python datetime.weekday() (Mon=0 .. Sun=6).
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

DEFAULT_PATIENT_TYPE = "person"
DEFAULT_DAYS = WEEKDAYS  # every day = daily
DEFAULT_RESET_TIME = "00:01:00"
DEFAULT_NAG_MINUTES = 45
DEFAULT_NAG_INTERVAL = 15
DEFAULT_TIME_FORMAT = "12h"
DEFAULT_SUPPLY_UNITS = 30
DEFAULT_SUPPLY_PER_DOSE = 1
DEFAULT_SUPPLY_THRESHOLD = 10
DEFAULT_SUPPLY_REFILL_TO = 30

# Icon for the patient-level "all doses given" sensor, by patient type.
PATIENT_ICONS = {
    "person": "mdi:account",
    "dog": "mdi:dog",
    "cat": "mdi:cat",
    "bird": "mdi:bird",
    "rabbit": "mdi:rabbit",
    "other": "mdi:paw",
}


def split_medications(meds):
    """Split a dose 'meds' string into individual medication names.

    A single dose can list several meds at once (e.g. "Keppra & Phenobarbital").
    Recognised separators: & , + /.
    """
    if not meds:
        return []
    return [p.strip() for p in re.split(r"[&,+/]", str(meds)) if p.strip()]


def meds_contains(meds, med_name):
    """True if `med_name` is one of the medications in a dose's meds string."""
    target = (med_name or "").strip().lower()
    if not target:
        return False
    return any(part.lower() == target for part in split_medications(meds))
