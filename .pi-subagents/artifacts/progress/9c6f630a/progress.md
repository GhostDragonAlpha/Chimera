# Progress: educational_catalog.py

## Status
Created `Chimera/core/educational_catalog.py` — complete catalog module.

## What was done
- Defined 49 educational topic records (20 geology, 13 meteorology, 16 astronomy)
- Each record has: id, subject, title, description, item_asset_name, text_level_name, source
- Added `get_all_topics()`, `get_topic()`, `get_topics_by_subject()`, `count_by_subject()`
- Added `generate_catalog()` — prints formatted markdown
- Added `generate_json()` — returns JSON string
- CLI supports `--json` flag

## Verification
- `python -m core.educational_catalog` — prints markdown
- `python -m core.educational_catalog --json` — prints JSON
- `count_by_subject()` returns `{'geology': 20, 'meteorology': 13, 'astronomy': 16}`
- Total: 49 topics
