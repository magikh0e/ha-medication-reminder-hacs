# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.11.2] - 2026-06-01
### Fixed
- Doses marked given before 0.11.1 (which have no stored give-time) no longer drift to the restart time on every reboot. On restore, a given dose with no recorded `given_at` now adopts its last known change time and keeps it, so the dashboard's "Already given at ..." freezes instead of changing each restart. Doses marked given from 0.11.1 onward already keep their exact give-time.

## [0.11.1] - 2026-06-01
### Fixed
- The dashboard's "Already given at ..." time no longer resets after a Home Assistant restart. Each dose now records a `given_at` timestamp when it is marked given and persists it across restarts (the on/off state was already restart-safe; only the displayed give-time was resetting to the startup time). The dashboard reads `given_at`, falling back to `last_changed` for doses that were already given before upgrading.

## [0.11.0] - 2026-06-01
### Added
- Every-N-days dose schedules (e.g. every other day, every third day). When adding a dose you can now choose the schedule type "Every N days" with an interval and a start date; the dose is due on the start date and every N days after. Day-of-week scheduling is still the default, and existing doses are unchanged (they default to the day-of-week behaviour). Each dose switch now also carries `schedule_type`, `interval_days`, `anchor_date`, and a computed `scheduled_today` attribute, and a single `is_due` rule decides "due today" for the status sensors, the supply run-out estimate, the companion automations, and the dashboard. Suggested by a community member.

## [0.10.0] - 2026-06-01
### Added
- Early-dose warning, a soft over-dose guard. The dose switch now fires a `medication_reminder_dose_given` event when a dose is marked given, carrying `patient`, `dose_time`, `medications`, `days`, `notify_service`, `scheduled_today`, and `minutes_early`. The new `med_early_given` companion automation listens for it and notifies the caretaker when a dose is marked given well before its scheduled time (default 30 minutes early; set `early_grace_minutes: 0` to warn on any early marking). It warns rather than blocks, so you keep control, and the warning carries two action buttons (Companion app): "undo" un-marks the dose if it was a mistake, "intended" dismisses. Un-marking a dose (the undo, or a manual toggle-off) now restores that dose's supply count via a new `medication_reminder_dose_undone` event; the daily reset does not restore, since a given dose was actually taken. Idea from community member IOT7712.
- Importable blueprints for every companion automation (reminders and missed-dose escalation, mark given from notification, low-supply refill, early-dose warning), under `blueprints/automation/medication_reminder/`. Add them with a one-click import and update them by re-importing, instead of copy-pasting YAML. Copying `companion-automations.yaml` still works as the alternative.

## [0.9.0] - 2026-05-31
### Added
- Supply and refill tracking, per medication. In Configure you can now "Track a medication supply" with the units on hand, units consumed per dose, a low-stock threshold, and a refill amount. Each tracked medication gets a settable `number` entity that decrements when a dose containing that medication is marked given today (once per dose per day, restart-safe, and never on the daily reset). It exposes `doses_left` and an `est_runout_date` computed from the schedule. A per-patient "supplies low" `binary_sensor` (device class `problem`) goes red when any supply reaches its threshold, and a new companion automation sends a refill reminder. Idea from Home Assistant Community member Tadies, who built it on a dashboard with counter helpers.

## [0.8.0] - 2026-05-30
### Added
- Day-of-week scheduling per dose. When adding a dose you can pick which days it applies to (Monday through Sunday); defaults to every day. A dose is only reminded, counted as pending, or flagged overdue on its scheduled days. Exposed as a `days` attribute, which the companion automations and the status sensors respect. Existing doses default to every day, so nothing changes for them.

## [0.7.0] - 2026-05-30
### Added
- Time format option (12-hour or 24-hour) in Reminder settings. Dose entity names show the time in the chosen format (e.g. `2:00 PM` or `14:00`). Exposed as a `time_format` attribute. Defaults to 12-hour, so existing setups are unchanged.

## [0.6.0] - 2026-05-30
### Added
- Per-patient "needs attention" sensor (`binary_sensor`, device class `problem`): red when a dose is overdue (past its time by the nag window and still not given), green when all is well. It re-evaluates on a 60-second timer so it trips on elapsed time alone, with no interaction, and fails safe toward "problem" rather than a false "all clear". Drives a simple red/green status panel and any light, siren, or notification you wire to it.

## [0.5.0] - 2026-05-30
### Added
- Patient type (Person, Dog, Cat, Bird, Rabbit, Other), chosen in the config flow and editable in Reminder settings. It sets the icon on the patient's "all doses given" sensor and is exposed as a `patient_type` attribute. Dose switches keep the pill icon.

## [0.4.0] - 2026-05-30
### Added
- Per-patient `binary_sensor` that is on when all of that patient's doses are given today, with `total`, `given`, `remaining`, and `pending` attributes. Useful for automations and dashboards.

## [0.3.0] - 2026-05-30
### Added
- Per-patient reminder settings in the UI (Configure, Reminder settings): daily reset time, nag window, and re-nag interval. These are exposed as switch attributes (`nag_minutes`, `nag_interval`) that the companion automations read, so changes take effect with no YAML edits.

## [0.2.2] - 2026-05-30
### Changed
- Dose entity names now show the medications inline, e.g. `Buddy 2:00 PM (Trazodone)`, so the toggle list matches the summary card.

## [0.2.1] - 2026-05-30
### Changed
- Dose entity names now display the time in 12-hour format (e.g. `2:00 PM` instead of `14:00`).

## [0.2.0] - 2026-05-29
### Added
- Per-patient notify target, selectable in the config flow and editable via the options flow.
- `notify_service` attribute on each dose switch, so the companion automations route reminders to the right person or group per patient.

## [0.1.0] - 2026-05-29
### Added
- Initial alpha release.
- UI config flow: add a patient, then add or remove doses (time + medications).
- One switch per dose (on = given today), grouped under a device per patient.
- Daily reset of all doses at 00:01; given/not-given state survives restarts.
- Companion automations for actionable, nagging, missed-dose reminders.
- Bundled dashboard card (12-hour summary + auto-entities).
