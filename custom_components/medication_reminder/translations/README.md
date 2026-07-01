# Translations

`en.json` is the source of truth. Every other `<lang>.json` mirrors its key
structure. Home Assistant falls back to the English string for any key a locale
is missing, so a partial translation never breaks anything; it just shows some
labels in English.

## Add a language

1. Copy `en.json` to `<lang>.json` (for example `fr.json`) and translate the
   values. Keep the keys and any `{placeholders}` (like `{medication}`) exactly
   as they are.
2. Open a PR that adds just that one file.
3. The **Translations** workflow reports the file's coverage against `en.json`
   on your PR, so you can see whether anything is missing.

## Keep a language current

When a release adds new keys to `en.json`, existing locales fall back to English
for them until they are updated. Run the coverage check to see exactly which
keys each locale is missing:

```
python scripts/check_translations.py
```
