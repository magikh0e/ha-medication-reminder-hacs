"""Button platform: a one-tap "refill to full" per tracked medication supply.

Pressing the button fires EVENT_SUPPLY_REFILL; the matching supply number
restocks itself to its configured refill-to amount.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import (
    CONF_PATIENT,
    CONF_SUPPLIES,
    CONF_SUPPLY_MED,
    DOMAIN,
    EVENT_SUPPLY_REFILL,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create a refill button per configured medication supply."""
    patient: str = entry.data[CONF_PATIENT]
    supplies: list[dict[str, Any]] = entry.options.get(CONF_SUPPLIES, [])
    async_add_entities(
        MedicationRefillButton(entry, patient, str(supply[CONF_SUPPLY_MED]).strip())
        for supply in supplies
    )


class MedicationRefillButton(ButtonEntity):
    """One-tap restock of a medication supply to its refill-to amount."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_icon = "mdi:package-variant-plus"

    def __init__(self, entry: ConfigEntry, patient: str, med: str) -> None:
        self._patient = patient
        self._med = med
        self._attr_name = f"{med} refill"
        self._attr_unique_id = f"{entry.entry_id}_refill_{slugify(med)}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": patient,
            "manufacturer": "Medication Reminder",
        }

    async def async_press(self) -> None:
        """Tell the matching supply to restock to full."""
        self.hass.bus.async_fire(
            EVENT_SUPPLY_REFILL,
            {"patient": self._patient, "medication": self._med},
        )
