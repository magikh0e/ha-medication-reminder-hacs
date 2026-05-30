"""Switch platform: one toggle per medication dose (on = given today)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify

from .const import (
    CONF_DOSES,
    CONF_MEDS,
    CONF_NOTIFY,
    CONF_PATIENT,
    CONF_TIME,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create a switch per dose and wire up the daily reset."""
    patient: str = entry.data[CONF_PATIENT]
    notify_target: str = entry.options.get(CONF_NOTIFY, "")
    doses: list[dict[str, Any]] = entry.options.get(CONF_DOSES, [])
    entities = [
        MedicationDoseSwitch(entry, patient, notify_target, dose) for dose in doses
    ]
    async_add_entities(entities)

    @callback
    def _reset_all(_now) -> None:
        for entity in entities:
            entity.reset_given()

    # Clear every dose's "given" flag at the start of each day.
    entry.async_on_unload(
        async_track_time_change(hass, _reset_all, hour=0, minute=1, second=0)
    )


class MedicationDoseSwitch(SwitchEntity, RestoreEntity):
    """A single scheduled dose. on = given today, off = not yet given."""

    _attr_should_poll = False
    _attr_icon = "mdi:pill"

    def __init__(
        self,
        entry: ConfigEntry,
        patient: str,
        notify_target: str,
        dose: dict[str, Any],
    ) -> None:
        self._patient = patient
        self._notify = notify_target
        self._time = str(dose[CONF_TIME])[:5]  # 24h "HH:MM" (used by automations)
        self._meds = dose[CONF_MEDS]
        self._attr_name = f"{patient} {self._format_time(self._time)}"  # 12h display
        self._attr_unique_id = (
            f"{entry.entry_id}_{slugify(self._time + '_' + self._meds)}"
        )
        self._attr_is_on = False
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": patient,
            "manufacturer": "Medication Reminder",
        }

    @staticmethod
    def _format_time(hhmm: str) -> str:
        """Convert 24h 'HH:MM' to 12h 'H:MM AM/PM' for the entity name."""
        try:
            hour_str, minute = hhmm.split(":")
            hour = int(hour_str)
            suffix = "AM" if hour < 12 else "PM"
            hour12 = hour % 12 or 12
            return f"{hour12}:{minute} {suffix}"
        except (ValueError, AttributeError):
            return hhmm

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Metadata the companion automations read to build reminders."""
        return {
            "patient": self._patient,
            "dose_time": self._time,
            "medications": self._meds,
            "notify_service": self._notify,
        }

    async def async_added_to_hass(self) -> None:
        """Restore the given/not-given state across restarts."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == "on"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Mark this dose given."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Mark this dose not given."""
        self._attr_is_on = False
        self.async_write_ha_state()

    @callback
    def reset_given(self) -> None:
        """Daily reset: clear the given flag."""
        self._attr_is_on = False
        self.async_write_ha_state()
