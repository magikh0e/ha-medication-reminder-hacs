"""Config and options flow for the Medication Reminder integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, selector
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ANCHOR_DATE,
    CONF_DAYS,
    CONF_DOSES,
    CONF_INTERVAL_DAYS,
    CONF_MEDS,
    CONF_NAG_INTERVAL,
    CONF_NAG_MINUTES,
    CONF_NOTIFY,
    CONF_PATIENT,
    CONF_PATIENT_TYPE,
    CONF_RESET_TIME,
    CONF_SCHEDULE_TYPE,
    CONF_SUPPLIES,
    CONF_SUPPLY_MED,
    CONF_SUPPLY_PER_DOSE,
    CONF_SUPPLY_REFILL_TO,
    CONF_SUPPLY_THRESHOLD,
    CONF_SUPPLY_UNITS,
    CONF_TIME,
    CONF_TIME_FORMAT,
    DEFAULT_DAYS,
    DEFAULT_INTERVAL_DAYS,
    DEFAULT_NAG_INTERVAL,
    DEFAULT_NAG_MINUTES,
    DEFAULT_PATIENT_TYPE,
    DEFAULT_RESET_TIME,
    DEFAULT_SCHEDULE_TYPE,
    DEFAULT_SUPPLY_PER_DOSE,
    DEFAULT_SUPPLY_REFILL_TO,
    DEFAULT_SUPPLY_THRESHOLD,
    DEFAULT_SUPPLY_UNITS,
    DEFAULT_TIME_FORMAT,
    DOMAIN,
    SCHEDULE_INTERVAL,
)


def _notify_selector(hass: HomeAssistant) -> selector.SelectSelector:
    """Dropdown of available notify services (groups + per-device)."""
    services = sorted(hass.services.async_services().get("notify", {}))
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=services,
            mode=selector.SelectSelectorMode.DROPDOWN,
            custom_value=True,
        )
    )


def _type_selector() -> selector.SelectSelector:
    """Dropdown of patient types (drives the patient icon)."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": "person", "label": "Person"},
                {"value": "dog", "label": "Dog"},
                {"value": "cat", "label": "Cat"},
                {"value": "bird", "label": "Bird"},
                {"value": "rabbit", "label": "Rabbit"},
                {"value": "other", "label": "Other"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _time_format_selector() -> selector.SelectSelector:
    """12-hour vs 24-hour display for dose times in entity names."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": "12h", "label": "12-hour (2:00 PM)"},
                {"value": "24h", "label": "24-hour (14:00)"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _days_selector() -> selector.SelectSelector:
    """Multi-select of the days of the week a dose applies to."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": "mon", "label": "Monday"},
                {"value": "tue", "label": "Tuesday"},
                {"value": "wed", "label": "Wednesday"},
                {"value": "thu", "label": "Thursday"},
                {"value": "fri", "label": "Friday"},
                {"value": "sat", "label": "Saturday"},
                {"value": "sun", "label": "Sunday"},
            ],
            multiple=True,
            mode=selector.SelectSelectorMode.LIST,
        )
    )


def _schedule_type_selector() -> selector.SelectSelector:
    """Dropdown: day-of-week schedule vs every-N-days."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": "weekdays", "label": "On chosen days of the week"},
                {"value": "interval", "label": "Every N days"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _interval_selector() -> selector.NumberSelector:
    """Whole-number box for the every-N-days interval."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            max=60,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="days",
        )
    )


def _minutes_selector(low: int, high: int) -> selector.NumberSelector:
    """A minutes number box in steps of 5."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=low,
            max=high,
            step=5,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="min",
        )
    )


def _count_selector() -> selector.NumberSelector:
    """A whole-number box for supply counts (pills/doses on hand)."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=9999,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


class MedicationReminderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Initial flow: one config entry per patient (pet or person)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Ask for the patient's name, type, and who to notify."""
        errors: dict[str, str] = {}
        if user_input is not None:
            patient = user_input[CONF_PATIENT].strip()
            await self.async_set_unique_id(patient.lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=patient,
                data={CONF_PATIENT: patient},
                options={
                    CONF_DOSES: [],
                    CONF_PATIENT_TYPE: user_input[CONF_PATIENT_TYPE],
                    CONF_NOTIFY: user_input[CONF_NOTIFY],
                    CONF_RESET_TIME: DEFAULT_RESET_TIME,
                    CONF_NAG_MINUTES: DEFAULT_NAG_MINUTES,
                    CONF_NAG_INTERVAL: DEFAULT_NAG_INTERVAL,
                    CONF_TIME_FORMAT: DEFAULT_TIME_FORMAT,
                },
            )
        schema = vol.Schema(
            {
                vol.Required(CONF_PATIENT): str,
                vol.Required(
                    CONF_PATIENT_TYPE, default=DEFAULT_PATIENT_TYPE
                ): _type_selector(),
                vol.Required(CONF_NOTIFY): _notify_selector(self.hass),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "MedicationReminderOptionsFlow":
        return MedicationReminderOptionsFlow(config_entry)


class MedicationReminderOptionsFlow(config_entries.OptionsFlow):
    """Add or remove doses, and change reminder settings."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "add_dose",
                "remove_dose",
                "add_supply",
                "remove_supply",
                "settings",
            ],
        )

    async def async_step_add_dose(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Add one dose: a time, the medications, and how it repeats.

        Schedule type "weekdays" uses the days picker (the default, unchanged
        behaviour); "interval" uses every-N-days from a start date. The fields
        for the other type are simply ignored on save.
        """
        if user_input is not None:
            options = dict(self._entry.options)
            doses = list(options.get(CONF_DOSES, []))
            stype = user_input.get(CONF_SCHEDULE_TYPE, DEFAULT_SCHEDULE_TYPE)
            dose = {
                CONF_TIME: str(user_input[CONF_TIME])[:5],
                CONF_MEDS: user_input[CONF_MEDS],
                CONF_SCHEDULE_TYPE: stype,
            }
            if stype == SCHEDULE_INTERVAL:
                dose[CONF_INTERVAL_DAYS] = int(
                    user_input.get(CONF_INTERVAL_DAYS, DEFAULT_INTERVAL_DAYS)
                )
                dose[CONF_ANCHOR_DATE] = str(
                    user_input.get(CONF_ANCHOR_DATE)
                    or dt_util.now().date().isoformat()
                )[:10]
                dose[CONF_DAYS] = list(DEFAULT_DAYS)
            else:
                dose[CONF_DAYS] = user_input.get(CONF_DAYS) or list(DEFAULT_DAYS)
            doses.append(dose)
            options[CONF_DOSES] = doses
            return self.async_create_entry(title="", data=options)
        schema = vol.Schema(
            {
                vol.Required(CONF_TIME): selector.TimeSelector(),
                vol.Required(CONF_MEDS): selector.TextSelector(),
                vol.Required(
                    CONF_SCHEDULE_TYPE, default=DEFAULT_SCHEDULE_TYPE
                ): _schedule_type_selector(),
                vol.Required(CONF_DAYS, default=list(DEFAULT_DAYS)): _days_selector(),
                vol.Optional(
                    CONF_INTERVAL_DAYS, default=DEFAULT_INTERVAL_DAYS
                ): _interval_selector(),
                vol.Optional(
                    CONF_ANCHOR_DATE, default=dt_util.now().date().isoformat()
                ): selector.DateSelector(),
            }
        )
        return self.async_show_form(step_id="add_dose", data_schema=schema)

    async def async_step_remove_dose(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Pick existing doses to remove."""
        doses = list(self._entry.options.get(CONF_DOSES, []))
        if user_input is not None:
            remove = set(user_input.get("remove", []))
            options = dict(self._entry.options)
            options[CONF_DOSES] = [
                d for i, d in enumerate(doses) if str(i) not in remove
            ]
            return self.async_create_entry(title="", data=options)
        choices = {
            str(i): f"{d[CONF_TIME]} - {d[CONF_MEDS]}" for i, d in enumerate(doses)
        }
        schema = vol.Schema(
            {vol.Optional("remove", default=[]): cv.multi_select(choices)}
        )
        return self.async_show_form(step_id="remove_dose", data_schema=schema)

    async def async_step_add_supply(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Track supply for one medication: units on hand, per-dose, threshold."""
        if user_input is not None:
            options = dict(self._entry.options)
            supplies = list(options.get(CONF_SUPPLIES, []))
            supplies.append(
                {
                    CONF_SUPPLY_MED: user_input[CONF_SUPPLY_MED].strip(),
                    CONF_SUPPLY_UNITS: int(user_input[CONF_SUPPLY_UNITS]),
                    CONF_SUPPLY_PER_DOSE: int(user_input[CONF_SUPPLY_PER_DOSE]),
                    CONF_SUPPLY_THRESHOLD: int(user_input[CONF_SUPPLY_THRESHOLD]),
                    CONF_SUPPLY_REFILL_TO: int(user_input[CONF_SUPPLY_REFILL_TO]),
                }
            )
            options[CONF_SUPPLIES] = supplies
            return self.async_create_entry(title="", data=options)
        schema = vol.Schema(
            {
                vol.Required(CONF_SUPPLY_MED): selector.TextSelector(),
                vol.Required(
                    CONF_SUPPLY_UNITS, default=DEFAULT_SUPPLY_UNITS
                ): _count_selector(),
                vol.Required(
                    CONF_SUPPLY_PER_DOSE, default=DEFAULT_SUPPLY_PER_DOSE
                ): _count_selector(),
                vol.Required(
                    CONF_SUPPLY_THRESHOLD, default=DEFAULT_SUPPLY_THRESHOLD
                ): _count_selector(),
                vol.Required(
                    CONF_SUPPLY_REFILL_TO, default=DEFAULT_SUPPLY_REFILL_TO
                ): _count_selector(),
            }
        )
        return self.async_show_form(step_id="add_supply", data_schema=schema)

    async def async_step_remove_supply(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Pick tracked medications to stop tracking supply for."""
        supplies = list(self._entry.options.get(CONF_SUPPLIES, []))
        if user_input is not None:
            remove = set(user_input.get("remove", []))
            options = dict(self._entry.options)
            options[CONF_SUPPLIES] = [
                s for i, s in enumerate(supplies) if str(i) not in remove
            ]
            return self.async_create_entry(title="", data=options)
        choices = {
            str(i): f"{s[CONF_SUPPLY_MED]} ({s.get(CONF_SUPPLY_UNITS, 0)} on hand)"
            for i, s in enumerate(supplies)
        }
        schema = vol.Schema(
            {vol.Optional("remove", default=[]): cv.multi_select(choices)}
        )
        return self.async_show_form(step_id="remove_supply", data_schema=schema)

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Patient type, notify target, reset time, nag window, and time format."""
        if user_input is not None:
            options = dict(self._entry.options)
            options[CONF_PATIENT_TYPE] = user_input[CONF_PATIENT_TYPE]
            options[CONF_NOTIFY] = user_input[CONF_NOTIFY]
            options[CONF_RESET_TIME] = str(user_input[CONF_RESET_TIME])
            options[CONF_NAG_MINUTES] = int(user_input[CONF_NAG_MINUTES])
            options[CONF_NAG_INTERVAL] = int(user_input[CONF_NAG_INTERVAL])
            options[CONF_TIME_FORMAT] = user_input[CONF_TIME_FORMAT]
            return self.async_create_entry(title="", data=options)
        opts = self._entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PATIENT_TYPE,
                    default=opts.get(CONF_PATIENT_TYPE, DEFAULT_PATIENT_TYPE),
                ): _type_selector(),
                vol.Required(
                    CONF_NOTIFY, default=opts.get(CONF_NOTIFY, "")
                ): _notify_selector(self.hass),
                vol.Required(
                    CONF_TIME_FORMAT,
                    default=opts.get(CONF_TIME_FORMAT, DEFAULT_TIME_FORMAT),
                ): _time_format_selector(),
                vol.Required(
                    CONF_RESET_TIME,
                    default=opts.get(CONF_RESET_TIME, DEFAULT_RESET_TIME),
                ): selector.TimeSelector(),
                vol.Required(
                    CONF_NAG_MINUTES,
                    default=opts.get(CONF_NAG_MINUTES, DEFAULT_NAG_MINUTES),
                ): _minutes_selector(5, 240),
                vol.Required(
                    CONF_NAG_INTERVAL,
                    default=opts.get(CONF_NAG_INTERVAL, DEFAULT_NAG_INTERVAL),
                ): _minutes_selector(5, 120),
            }
        )
        return self.async_show_form(step_id="settings", data_schema=schema)
