"""Sensor platform: the next upcoming dose per patient.

`sensor.<patient>_next_dose` is a timestamp of the soonest dose still in the
future, computed from each dose's schedule (any schedule type) via is_due.
"""

from __future__ import annotations

from datetime import datetime, time as dtime, timedelta
from typing import Any

import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_DOSES,
    CONF_MEDS,
    CONF_PATIENT,
    CONF_TIME,
    DOMAIN,
    is_due,
)

# Re-evaluate this often so "next dose" rolls forward as time passes.
_SCAN = timedelta(seconds=60)
# How far ahead to look for the next due day (covers monthly/long cycles).
_HORIZON_DAYS = 366


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the next-dose sensor for this patient."""
    patient: str = entry.data[CONF_PATIENT]
    async_add_entities([MedicationNextDoseSensor(entry, patient)])


class MedicationNextDoseSensor(SensorEntity):
    """Timestamp of the patient's next upcoming dose."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-time-four-outline"

    def __init__(self, entry: ConfigEntry, patient: str) -> None:
        self._doses: list[dict[str, Any]] = entry.options.get(CONF_DOSES, [])
        self._patient = patient
        self._value: datetime | None = None
        self._meds: str | None = None
        self._attr_name = "Next dose"
        self._attr_unique_id = f"{entry.entry_id}_next_dose"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": patient,
            "manufacturer": "Medication Reminder",
        }

    def _compute(self) -> None:
        """Find the soonest dose datetime strictly after now."""
        now = dt_util.now()
        best: datetime | None = None
        best_meds: str | None = None
        for dose in self._doses:
            try:
                hour, minute = (int(p) for p in str(dose.get(CONF_TIME)).split(":")[:2])
            except (ValueError, AttributeError, TypeError):
                continue
            for offset in range(_HORIZON_DAYS):
                day = (now + timedelta(days=offset)).date()
                if not is_due(dose, day):
                    continue
                cand = datetime.combine(day, dtime(hour, minute), tzinfo=now.tzinfo)
                if cand > now:
                    if best is None or cand < best:
                        best, best_meds = cand, dose.get(CONF_MEDS)
                    break
        self._value, self._meds = best, best_meds

    @property
    def native_value(self) -> datetime | None:
        return self._value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"patient": self._patient, "medications": self._meds}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._compute()
        self.async_on_remove(
            async_track_time_interval(self.hass, self._tick, _SCAN)
        )

    @callback
    def _tick(self, _now: datetime) -> None:
        self._compute()
        self.async_write_ha_state()
