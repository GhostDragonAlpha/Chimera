# I-R02-SAVE-STORE-FOLLOWUP — report

**Verdict: PASS — every preregistered prediction held; no falsifier clause fired.**
A minimal regression patch was NOT needed: the merged implementation survived all
real process-death injections and refused all corruptions by name. This card adds
fault-injection EVIDENCE, not a source fix.

## Scope and subject under test

Card: `I-R02-SAVE-STORE-FOLLOWUP` (planning ID R02, profile: recovery).
Attempt `21e3724ba8f84dd2bce9ed079c59979a`, agent `c95e1722350849bca846b237c1f60997`,
criteria sha256 `e6011f9304d14799c953cd323881d28674a5491b1eb702625082085f0f1fce5d`.

The fault-injected module is the MERGED parent card source — not a stand-in:

- Parent card: `I-R02-SAVE-STORE`, winning PR
  https://github.com/GhostDragonAlpha/Chimera/pull/117, merged head
  `9ba1be77228e181f55ed2e4d2eb3e73e2f09685f` (= branch-4; merge recorded
  2026-09-25T16:03:36Z).
- Tree path: `tools/monkey_campaign/contributions/I-R02-SAVE-STORE/save_store.py`
- Raw SHA-256 of the exact bytes under test:
  `cf175ea73508927697905cb9faa96737bb454ce7e946caa1ccc247338e4f9347`
  (verified against `git show 9ba1be77:tools/monkey_campaign/contributions/I-R02-SAVE-STORE/save_store.py`
  from this attempt's checkout; byte-identical).
- `adapter.load_accepted_module()` re-verifies this hash at every load — parent
  process AND child process — and refuses with named refusal `stand_in_module`
  otherwise. A stand-in cannot enter.

## Harness design (adapter.py)

Real writer subprocesses (`python -B adapter.py child ...`) load the accepted
module in their own process, arm exactly one injection by patching
`builtins.open` / `os.fsync` / `os.replace` in-process, then call the real
`SaveStore.save` and die with `os._exit` at the armed point — hard death, no
exception unwinding, no temp cleanup. Stdout marker lines prove where each child
died (`armed`, `died_at`, `saved`, `refused`).

| injection point | where it dies | exit code |
|---|---|---|
| `before_open`    | before the temp file exists | 10 |
| `mid_write`      | after HALF the envelope bytes are written (partial temp file on disk) | 9 |
| `before_fsync`   | envelope fully written, not fsynced | 8 |
| `before_replace` | fully written + flushed + fsynced, immediately before `os.replace` — the card's targeted point | 7 |

Corruption scenarios tamper the stored envelope BYTES on disk (bypassing the
module): raw truncation, payload_b64 character flip, stored-hash overwrite,
payload_size tamper, invalid UTF-8 insertion, textual duplicate key, NaN literal,
wrong schema, `format_version=0`, deleted identity. Payloads are deterministic
(chained/counter SHA-256 blocks; no randomness) so every rerun is byte-identical.

## Exact reproduction commands

Run from this attempt workspace (CPU-only, stdlib-only, temp dirs only):

```
python -B test_adapter.py -v                      # targeted suite, 14 tests
python -B adapter.py verify --save-store-path reference/I-R02-SAVE-STORE/save_store.py
```

Environment measured: Windows 10.0.26200 x64, CPython 3.14.3
(`MSC v.1944 64 bit (AMD64)`). Suite runtime 3.85 s; verify runtime 1.79 s —
inside the 120 s per-invocation bound (also asserted by the suite itself).

## Measured outcomes (verify run, `pass: true`)

Interrupted overwrite of a pre-existing valid save — per injection point:

| point | child rc | died-at marker | slot bytes unchanged | load status | payload == prior (byte-exact) | listed slots |
|---|---|---|---|---|---|---|
| before_open    | 10 | yes | yes (sha256 equal) | loaded | yes | 1, all ok |
| mid_write      |  9 | yes | yes (sha256 equal) | loaded | yes | 1, all ok |
| before_fsync   |  8 | yes | yes (sha256 equal) | loaded | yes | 1, all ok |
| before_replace |  7 | yes | yes (sha256 equal) | loaded | yes | 1, all ok |

Interrupted FIRST save (point `before_replace`): load → `first_run`, `list()` →
0 slots, no real `*.save.json` file exists; crash debris survives only as
`.clearing_1.tmp-<pid>` (no `.save.json` suffix → never listed).

Corrupted/truncated stored saves — 10/10 refuse with the EXACT named code:
`json_corrupt` (raw truncation), `payload_hash_mismatch` (b64 flip; stored-hash
tamper), `payload_size_mismatch`, `not_utf8`, `key_duplicate`, `not_finite_json`
(NaN), `schema_unknown`, `format_version_type` (0), `scene_id_missing`; payload
returned empty in every refusal. Identity mismatches on an intact envelope:
4/4 refuse as `format_version_mismatch` / `build_id_mismatch` /
`scene_id_mismatch` / `policy_id_mismatch`.

Crash loop (5 interrupted overwrites, rotating points): prior save intact after
every trial (bytes sha256-equal, loads byte-exact); first clean save afterwards
loads byte-exact (rc 0, `status=loaded`, payload equal to the deterministic
48 KiB expected payload).

Refusal law inside the child process path: traversal slot name `../escape`
refused with code `slot_traversal` (child rc 3), nothing written outside the
user directory.

Independent checks: `test_adapter.py` recomputes expected SHA-256 values and
byte equality in the test process from its own expected bytes, decodes the
stored envelope's `payload_b64` directly, and asserts the real-slot directory
listing contains exactly one `.save.json` after every interruption — none of
these rely on the adapter's own verdict.

## Falsifier scorecard (from PREREGISTRATION.md)

- **F1** (interruption changes slot bytes / load fails / listing changes): NOT
  FIRED — 4/4 points + 5/5 crash-loop trials preserve the prior save byte-exact.
- **F2** (corruption loads, or refuses without a named code): NOT FIRED —
  10/10 + 4/4 refuse with the exact named code, empty payload.
- **F3** (partial/new content observable under a real `*.save.json` name): NOT
  FIRED — debris exists only under temp names that `list()` never reports.
- **F4** (stand-in module, or physics-state-restore claims): NOT FIRED — the
  hash pin refuses any other bytes; payloads stay opaque end to end. **No
  physics/engine snapshot semantics are tested or claimed by this card.**

## Bounds honored

CPU-only; stdlib only; no network; no GPU; no production/source-checkout edits
(the merged source file is read-only under `reference/` in this attempt
workspace); every subprocess capped at 30 s; test invocation 3.85 s < 120 s;
new output well under the 16 MiB card bound.

## Artifacts (this attempt workspace)

| file | raw SHA-256 |
|---|---|
| `adapter.py` | `a7ca62175a36013240ad8ceba1abe7546f7c38150701e78380527840234bb982` |
| `test_adapter.py` | `de98f955b9be1e49a31585fd8d5747470b314abfb3f82c1125941ef314dfd4a6` |
| `PREREGISTRATION.md` | `04421a0b5f264d4adf701f21930f7a6dbf0cb955440b6d2efa84fe25266886c2` |
| `report.md` | this file |

Published `verify` JSON (full output of the command above, `pass: true`,
elapsed 1.79 s): see `verify_output.json` in this workspace; identical content
is regenerable via the published command (only `elapsed_seconds` and the temp
`save_store_path` absolute prefix vary between runs).
