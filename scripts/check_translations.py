#!/usr/bin/env python3
"""Report each locale's key coverage against en.json (the source of truth).

Home Assistant falls back to the English string for any key a locale is missing,
so a gap is a warning, not a failure. This script always exits 0 and prints a
per-locale summary. It is used by the Translations workflow and is runnable
locally: python scripts/check_translations.py
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

TRANSLATIONS = pathlib.Path("custom_components/medication_reminder/translations")


def flatten(obj, prefix=""):
    """Every key path in a nested dict, e.g. 'options.step.init.title'."""
    keys = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            keys.add(path)
            keys |= flatten(value, path)
    return keys


def main() -> int:
    en = flatten(json.loads((TRANSLATIONS / "en.json").read_text(encoding="utf-8")))
    out = [f"# Translation coverage vs `en.json` ({len(en)} keys)", ""]
    for path in sorted(TRANSLATIONS.glob("*.json")):
        if path.name == "en.json":
            continue
        keys = flatten(json.loads(path.read_text(encoding="utf-8")))
        missing = sorted(en - keys)
        extra = sorted(keys - en)
        pct = round(100 * (len(en) - len(missing)) / len(en)) if en else 100
        state = "complete" if not missing else f"{len(missing)} missing"
        out.append(f"## `{path.stem}`: {pct}% ({state})")
        if missing:
            out.append("Missing (falls back to English):")
            out += [f"- `{k}`" for k in missing]
        if extra:
            out.append("Not in en.json (typo or removed key?):")
            out += [f"- `{k}`" for k in extra]
        out.append("")

    report = "\n".join(out)
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(report + "\n")
    # Gaps are fine (English fallback), so never fail the build.
    return 0


if __name__ == "__main__":
    sys.exit(main())
