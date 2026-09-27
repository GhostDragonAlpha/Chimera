# ONT-U04 — report (input settings: sensitivity, inversion, bindings, persistence)

Card `ONT-U04` (planning id **U04**), attempt `caffa214d5c1429f87a145634f3dd373`,
arrival `arrival-784f5dbaf83343cd8bb1b925a2583364`, branch `branch-2` (isolated
sparse attempt checkout, HEAD `c525b82c`), criteria_sha256
`91ae72baefd10d8e670a4c715fa0fec8ef8bddd014fe5cb7b1a4bcfbbffd931b`,
publication branch `review/ONT-U04`, base `astra/gait-capture` (repo
`GhostDragonAlpha/Chimera`). Source pin
`9afbddcd90164b5544a16fd0bc72278d985eb6e3` (`E:/ChimeraWork/monkey-play-20260924`)
read via `git show <rev>:<path>` only. PREREGISTRATION.md frozen BEFORE the
battery was run (statement, prediction, falsifiers F1–F6, nonvisual
declaration, limits).

## 0. Reconciliation (why this candidate looks the way it does)

- **U04 is already implemented at the pin**: commit `4699b37d` on the
  monkey-play line ("monkey-play: U04 integrated — input settings …") added
  `product/input_settings.py` (504 lines) + `product/input_settings_tests.py`
  (830 lines) with its integration receipt in `agents/U04_settings/`. That
  history is NOT in the campaign branch: `astra/gait-capture` and this
  attempt's HEAD predate it and contain no `product/` tree at all.
- **Nine prior ONT-U04 attempts left no artifacts** (checkout skeletons at
  HEAD `c525b82c`, zero commits; one holds an untracked reference extraction
  with the four modules byte-identical to this attempt's — verified by
  byte-comparison — and two empty package `__init__` placeholders). No
  completed implementation was repeated; the missing step was delivering the
  already-integrated pin implementation as a reviewable campaign candidate.
- **Precedent followed**: merged PR #138 (`review/I-U07-TRACE`, merge
  `eaa2fa46`) delivered a pin-derived module in exactly this shape
  (`contributions/<TASK>/…` + `reference/` + ledger + `proposed.patch`).

## 1. What was built

- **`input_settings.py`** (504 lines, **byte-exact from the pin**, sha256
  `8d1a49d6…a2f1`, 22,608 B) — the complete U04 done_when surface:
  - settings vector `InputSettings(bindings, sensitivity, invert_yaw)`;
    per-axis yaw sensitivity over the DERIVED range
    `(0, OMEGA_MAX_RAD_S * INTERVAL_MS/1000]` (one count in one 50 ms
    interval exactly saturates U01's declared steer bound; default = U01's
    frozen `SENS_RAD_PER_COUNT = 0.002`, imported, never redeclared);
    inversion = sign of the yaw delta scale, never a key swap.
  - persistence: versioned `chimera.monkey_input.v1` JSON; canonical bytes
    (sorted keys, fixed separators, one trailing newline); atomic save
    (same-directory temp → flush + fsync → `os.replace`, temp removed on
    failure); total refusing load — absent file ⇒ `first_run` defaults and
    NOTHING created; corrupt JSON / duplicate keys anywhere / NaN+Infinity
    literals / unknown schema / missing+unknown keys / wrong types
    (booleans are not numbers) / unknown axes / out-of-range values /
    unknown actions / unbound selected controls EACH refuse BY NAME; every
    refusal falls back to U01's EXACT defaults, never a partial accept.
  - seam protection: the apply surface is only `mapper.bindings = dict(…)`
    and `mapper.sensitivity = ±sensitivity` — the mapper's own declared
    data inputs; no module attribute of input_mapper/command_record is ever
    assigned; the schema's fixed key set rejects seam-constant key names.
- **`input_settings_tests.py`** (830 lines, **byte-exact from the pin**,
  sha256 `5845178a…720f`) — the frozen F1–F6 falsifier battery (33 named
  checks, seed 20260924), run UNMODIFIED.
- **`run_falsifiers.py`** — this attempt's bounded verification bootstrap
  (the only new logic here). It (1) aborts before running on any hash drift
  between candidate, reference and ledger; (2) runs the pinned battery
  UNMODIFIED with `reference/` as its expected repo-root (`parents[3]`, same
  implicit-namespace package shape as the pin — verified: the pin has no
  `tools/monkey_campaign/__init__.py` and no
  `tools/monkey_campaign/product/__init__.py`); (3) enforces the attempt
  limits (120 s, 16 MiB output); (4) emits a machine-checkable JSON summary
  (hashes, limits, elapsed, PASS/FAIL counts, verdict line).
- **`reference/` + `EXTRACTION_LEDGER.json`** — byte-exact pinned
  extractions with per-file path/revision/sha256/bytes:
  `input_settings.py` `8d1a49d6…a2f1` (22,608 B), `input_settings_tests.py`
  `5845178a…720f` (41,221 B), `input_mapper.py` `7a36a45e…6b44` (18,349 B),
  `command_record.py` `67711759…4355e` (12,095 B),
  `science_funnel/__init__.py` `c5a9f9b1…8b19` (86 B),
  `typeb_export/__init__.py` `e3b0c442…855` (0 B). Files are read-only
  after extraction. Identity cross-check: the `input_mapper` and
  `command_record` hashes match the independent extraction identities
  recorded in merged PR #138's report (different worker, same pin).
- **`proposed.patch`** — the INTEGRATION PROPOSAL ONLY (lead-serialized):
  adds the two product modules at their canonical paths
  (`tools/monkey_campaign/product/input_settings.py`,
  `…/input_mapper.py`) plus the pin-required dependency subtree
  (`tools/science_funnel/__init__.py` 86 B byte-exact,
  `typeb_export/__init__.py` 0 B byte-exact,
  `typeb_export/command_record.py` byte-exact). The campaign base contains
  none of these (verified absent at `c525b82c` and at `astra/gait-capture`,
  so no identical-blob dedup applies). `git apply --check` verified OK.
  Application places the modules byte-identical to the reference copies;
  it is the publisher's action, not this worker's.

## 2. Verification (exact command, observed results, limits)

```
python -B tools/monkey_campaign/contributions/ONT-U04/run_falsifiers.py
```
(from the attempt checkout root; exit 0; full captured battery output in
`evidence/run_falsifiers_output.txt`, machine summary in
`evidence/run_falsifiers_summary.json`)

- **Result: VERDICT GREEN — 33/33 checks PASS, 0 FAIL.**
- F1 (silent accept): 36/36 adversarial files refuse BY NAME with exact
  defaults; every refusal carries machine code + human detail; the
  multi-offense file reports all three; the corpus exercises all 19 declared
  refusal codes.
- F2 (seam poison): 171 named poison payloads leave all 18 seam constants
  bit-identical; 2000-payload fuzz (frozen seed): 685 loaded / 1315 refused,
  13,909 emitted records, 0 bounds violations; bindings-table copy verified;
  direct extreme-vector probe 0 violations.
- F3 (round-trip): first_run creates nothing; exact save→load; byte-identical
  resave (194 B canonical form); atomic same-directory temp → os.replace
  (temp `.{name}.tmp-<pid>` observed, no residue); stale temp ignored;
  bit-flipped files refuse by name.
- F4 (sensitivity): exact `clamp(counts*s/interval, ±OMEGA)` across 98
  (sensitivity, inversion, counts) triples incl. the derived ceiling; exact
  doubling linearity pre-clamp; 100x + 100k-count flick lands exactly AT the
  bound (1.6 rad/s == OMEGA); 100x unreachable through a file; inversion
  negates mouse yaw exactly (+0.8/−0.8) without touching key semantics.
- F5 (bindings): duplicate key refuses (`key_duplicate`); aliases legal and
  both drive at the band ceiling; sprint/jump bindable, refuse by name at
  runtime; remap values-only (same record type/version, same adapter
  projection); collision resolves by U01 precedence and is named in the
  trace; unbound selected control and unknown action refuse at the file
  boundary.
- F6 (first run): absent file → `first_run` with U01's exact baseline
  (bindings, 0.002, no inversion); defaults drive a plain U01 mapper
  record-for-record (7 records identical); explicit save ⇒ `loaded`
  identical; declared default path never created by import or tests
  (resolved inside `reference/…` in this layout — creation outside the
  attempt workspace is structurally impossible here).
- **Limits honored**: battery wall time 13.315 s (bound 120 s); captured
  output ~7 KB (bound 16 MiB); headless, CPU-only, no network/GPU/engine
  imports (import scan below); no writes outside `tempfile` directories,
  the attempt workspace, and one explicit `save_settings` to a temporary
  directory under the test's own `TemporaryDirectory`.

## 3. Failures, corrections, and what this does NOT claim

- One runner defect was found and fixed during verification (before the
  final GREEN run): the hash-proof compared POSIX ledger keys against
  Windows-style `relative_to()` keys and aborted with
  `ABORTED_HASH_DRIFT` (hashes were in fact equal). Fixed by `.as_posix()`
  normalization; the abort behavior itself was thereby demonstrated to
  work. Recorded as an honest intermediate run in this history, not hidden.
- Git note for the publisher: the temp-index patch generation logged
  `warning: LF will be replaced by CRLF` for two extracted files
  (`core.autocrlf` display warning only; index blobs are the exact pin
  bytes — verified by re-hash after `git add`).
- This candidate is the **settings data layer**: it does NOT close the
  `controls` motion profile, the parent runtime phase, or any human
  acceptance. No game acceptance is claimed. Only the lead/publisher may
  integrate via `proposed.patch` (or their own preferred path) into
  `astra/gait-capture`.

## 4. Source/artifact identities (raw SHA-256, bytes)

| artifact | sha256 | bytes |
|---|---|---|
| contributions/ONT-U04/PREREGISTRATION.md | (recorded in receipt.json) | |
| contributions/ONT-U04/run_falsifiers.py | (recorded in receipt.json) | |
| contributions/ONT-U04/proposed.patch | (recorded in receipt.json) | |
| contributions/ONT-U04/EXTRACTION_LEDGER.json | (recorded in receipt.json) | |
| contributions/ONT-U04/evidence/run_falsifiers_summary.json | (recorded in receipt.json) | |
| contributions/ONT-U04/evidence/run_falsifiers_output.txt | (recorded in receipt.json) | |
| reference/tools/monkey_campaign/product/input_settings.py | 8d1a49d63f85164f3b9ac27f3387237d0a0790f68075e2455a74e2caa485a2f1 | 22,608 |
| reference/tools/monkey_campaign/product/input_settings_tests.py | 5845178ab12a69773e6b4bcdf2e8aa0b9fd144cddff7ee1e89204e0c5dd3720f | 41,221 |
| reference/tools/monkey_campaign/product/input_mapper.py | 7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44 | 18,349 |
| reference/tools/science_funnel/typeb_export/command_record.py | 6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e | 12,095 |
| reference/tools/science_funnel/__init__.py | c5a9f9b162177ec18d127edb799bbfe1ba08442ed95c72f8f0947f9d64618b19 | 86 |
| reference/tools/science_funnel/typeb_export/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | 0 |

(`receipt.json` records the exact hash of every file in this candidate
directory at submission time.)

## 5. Headless law check (import scan of every shipped Python file)

- `input_settings.py`: `json, math, os, sys, dataclasses, pathlib` + local
  `input_mapper` — all stdlib/local.
- `input_mapper.py`: `sys, pathlib` + `tools.science_funnel.typeb_export.command_record` — stdlib/local.
- `command_record.py`: `hashlib, json, struct, dataclasses, typing` — stdlib.
- `input_settings_tests.py`: `copy, json, random, sys, tempfile, pathlib` — stdlib.
- `run_falsifiers.py`: `hashlib, io, json, sys, time, contextlib, pathlib` — stdlib.

No clock/wall-time, window, GUI, network, numpy, engine or GPU import exists
anywhere in the candidate. Deterministic: the battery uses a frozen seed
(20260924) and fixed vectors; re-runs reproduce byte-identically.

## 6. Next implementation step (for the lead/publisher)

1. Independent review of this candidate on `review/ONT-U04` (exact head,
   criteria hash `91ae72ba…d931b`); re-run
   `run_falsifiers.py` (bounded 120 s) and re-hash the reference files.
2. On approval, apply `proposed.patch` to `astra/gait-capture` — the modules
   land byte-identical to `reference/`; SessionFlow/U01 wiring (adapter
   call sites) is subsequent integration work and stays with the publisher.
3. Runtime/visual `controls` qualification (the motion profile) remains with
   the parent runtime tasks; this card's data-layer contract is reviewable
   and integrable independently of them.
