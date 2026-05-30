"""Binary sensor: all of a patient's doses given today."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_PATIENT,
    CONF_PATIENT_TYPE,
    DEFAULT_PATIENT_TYPE,
    DOMAIN,
    PATIENT_ICONS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the per-patient 'all doses given' sensor."""
    patient_type = entry.options.get(CONF_PATIENT_TYPE, DEFAULT_PATIENT_TYPE)
    async_add_entities(
        [AllDosesGivenBinarySensor(entry, entry.data[CONF_PATIENT], patient_type)]
    )


class AllDosesGivenBinarySensor(BinarySensorEntity):
    """On when every dose for this patient is marked given today."""

    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, patient: str, patient_type: str) -> None:
        self._patient = patient
        self._patient_type = patient_type
        self._attr_name = f"{patient} all doses given"
        self._attr_unique_id = f"{entry.entry_id}_all_doses_given"
        # The patient-level entity carries the patient icon (dog/person/etc.).
        self._attr_icon = PATIENT_ICONS.get(patient_type, "mdi:check-all")
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": patient,
            "manufacturer": "Medication Reminder",
        }

    def _doses(self) -> list:
        """This patient's dose switches (matched by attributes)."""
        return [
            s
            for s in self.hass.states.async_all("switch")
            if s.attributes.get("medications") is not None
            and s.attributes.get("patient") == self._patient
        ]

    @property
    def is_on(self) -> bool | None:
        doses = self._doses()
        if not doses:
            return None
        return all(s.state == "on" for s in doses)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        doses = self._doses()
        total = len(doses)
        given = sum(1 for s in doses if s.state == "on")
        return {
            "patient_type": self._patient_type,
            "total": total,
            "given": given,
            "remaining": total - given,
            "pending": [s.name for s in doses if s.state != "on"],
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def _on_state_changed(event: Event) -> None:
            if not event.data.get("entity_id", "").startswith("switch."):
                return
            new = event.data.get("new_state")
            if new is None or (
                new.attributes.get("patient") == self._patient
                and new.attributes.get("medications") is not None
            ):
                self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen("state_changed", _on_state_changed)
        )
