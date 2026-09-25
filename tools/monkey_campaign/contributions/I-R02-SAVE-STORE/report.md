# Report — I-R02-SAVE-STORE (bounded implementation)

**Task ID:** I-R02-SAVE-STORE (planning id R02)
**Attempt:** ee0799d3f9d445928350c932be0c6805
**Arrival:** arrival-cba7b89cb6734050a3c4fe5fff7e98f4
**Base revision:** 9afbddcd90164b5544a16fd0bc72278d985eb6e3
**Card criteria sha256:** 0f60830b82c0ed0fe52a693384d5b73c976a8fea2cb671390eed49529b7b087d
**Branch:** codex/monkey-i-r02-save-store-ee0799d3f9
**pr_destination:** tools/monkey_campaign/contributions/I-R02-SAVE-STORE/

## Objective
Wrap opaque existing engine snapshot bytes in a durable, self-verifying *envelope*
and expose `save` / `load` / `list` over named slots — **without inventing any
physics serialization**. The payload is treated as opaque bytes; this store records
*what* was saved (identities + payload hash) and guarantees the bytes return
byte-exact. The engine owns how snapshot bytes are produced/consumed; this module
owns durability and identity refusal.

## Deliverables (real sha256, verified on disk)
| artifact | sha256 |
| --- | --- |
| `save_store.py` | `cf175ea73508927697905cb9faa96737bb454ce7e946caa1ccc247338e4f9347` |
| `test_save_store.py` | `c61fe4173270ac98ebcad3abc269970c250956b6341e51fb804a312666df3261` |

Both live in the attempt workspace:
`E:/ChimeraWork/monkey-coordination/kanban-attempts/I-R02-SAVE-STORE/ee0799d3f9d445928350c932be0c6805/`

## Verification (commands + observed results)
```
cd .../I-R02-SAVE-STORE/ee0799d3f9d445928350c932be0c6805
python -B test_save_store.py
```
Observed: `Ran 26 tests in ~0.13s` — **OK**, zero failures (reproduced this run:
26/26 passing).

Falsifier + scenario coverage:
- **Falsifier 1 (interrupted write must not destroy a prior save):**
  `test_interrupted_write_preserves_previous_save` — `os.replace` raised after the
  temp existed; the earlier payload loads byte-exact, no partial file under a real
  slot name, stray `.B.save.tmp-<pid>` cleaned and excluded by `list()`.
- **Falsifier 2 (traversal escapes the caller directory):**
  `test_load_traversal_names_refuse_without_escaping`,
  `test_save_traversal_names_raise` — names with `/`, `\`, `..`, absolute paths, or
  drive letters refuse; containment is a realpath defense-in-depth check.
- **Falsifier 3 (mismatched identities accepted / tamper/truncation passes):**
  `test_version_mismatch_refuses`, `test_identity_mismatch_refuses`,
  `test_missing_identity_in_envelope_refuses`, `test_tampered_payload_hash_mismatch`,
  `test_truncated_file_refuses` — every offense refuses by named code; a missing
  expected identity is refused, never silently defaulted.
- **Step-5 scenarios:** byte-exact round-trip incl. binary payload, deterministic
  byte-identical saves, overwrite replaces content, list returns metadata only and
  sorted, empty-payload round-trip, save coerces bytearray/memoryview, rejects
  non-bytes, enforces max payload bound, requires all identities.
- **Reused convention:** `test_atomic_write_uses_temp_fsync_replace`,
  `test_list_excludes_temp_and_reports_unreadable`,
  `test_absent_file_is_first_run_and_creates_nothing`.
- **Bounded / no execution:** `test_source_uses_no_pickle_or_exec` — module imports
  only `base64, hashlib, json, os, pathlib, dataclasses`; no `pickle`, no `eval`/`exec`.

## Reused convention (not duplicated)
The atomic-write law and the refusing-load parser shape are reused verbatim from
`input_settings.py` at base revision — **extracted read-only** under `reference/`
with hashes preserved. No import of, or copy into, the production module:

| reference path | sha256 |
| --- | --- |
| `tools/monkey_campaign/product/input_settings.py` | `8d1a49d63f85164f3b9ac27f3387237d0a0790f68075e2455a74e2caa485a2f1` |
| `tools/monkey_campaign/product/session_flow.py` | `30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf` |
| `tools/monkey_campaign/product/input_mapper.py` | `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` |

Atomic-write law (verbatim reuse): canonical deterministic UTF-8 bytes → temp file
in the **destination directory** → `flush()` + `os.fsync()` → `os.replace`; temp
removed on any failure so no partial document is ever observable under a real slot
name. Refusing-load shape (reuse): duplicate JSON keys, NaN/Infinity literals,
unknown schema, wrong types each refuse by name; payload hash recomputed on load.

## Design summary
- **Envelope** = one self-contained JSON doc: `schema` (`chimera.monkey_save_envelope.v1`),
  `format_version`, `build_id`, `scene_id`, `policy_id`, `payload_sha256`,
  `payload_size`, `payload_b64`. Serialized deterministically (sorted keys, fixed
  separators, one trailing newline) so equal inputs are byte-identical. The whole
  document is the atomic unit of durability.
- **Opaque payload:** base64 *inside* the document; no separate header+body to
  truncate across; nothing stored is ever executed or unpickled — only decoded and
  hash-checked.
- **Refusing read:** absent file → `first_run` (nothing created); any content or
  identity problem → `refused` with every named refusal; identities matched against
  caller-supplied expected values, mismatch or missing expected refuses.
- **Flat slot names:** `<slot>.save.json`; no separator, no `..`, cannot escape the
  supplied user directory. Default payload bound 8 MiB, overridable via
  `max_payload_bytes`.
## Adapter proposal for production (`session_flow.py`) — NOT edited here
`session_flow.py` is a four-state machine (attract → playing ⇄ paused → exited) that
touches the world only through injected `World.boot()` / teardown callables and drives
U01's mapper solely via key bindings while `playing`. The save store integrates as an
**injected dependency**, mirroring how `World` is already injected, with no change to
the frozen state table:

- Construct `SaveStore(user_dir)` from the run's user directory (injected like `World`).
- **PLAYING → PAUSED (quiesce):** before leaving `playing`, capture the session
  snapshot bytes and call
  `store.save("session_<id>", format_version=3, build_id=<build>, scene_id=<scene>,
    policy_id=<policy>, payload=snapshot_bytes)`. Identities come from the injected
  run identity; the envelope stores *what* was saved and hashes the opaque bytes.
- **PAUSED → PLAYING (resume / `confirm`):** `load("session_<id>")`; on status
  `"loaded"` restore the captured state, on `"refused"` fall back to a fresh grid
  (consistent with the existing RESUME TAIL — no phantom replay of a tampered save).
- **→ EXITED (teardown):** persist a final `exit` snapshot alongside the running one.
- The envelope never serializes physics: pass engine snapshot bytes as an opaque
  `payload`; the engine owns serialization. Headless by construction — same injection
  discipline already used for `World`, so no window/process/HTTP enters this module.

## PR / handoff
- Isolated git repo staged at `tools/monkey_campaign/contributions/I-R02-SAVE-STORE/`
  (task's `pr_destination`), built on base `astra/gait-capture`, branch
  `codex/monkey-i-r02-save-store-ee0799d3f9`. Contents: `save_store.py`,
  `test_save_store.py`, `PREREGISTRATION.md`, this report, `receipt.json`, and the
  read-only `reference/` tree with recorded hashes.
- Pushed via SSH using the fleetdeploy deploy key (`E:/ChimeraWork/control/deploy_key`).
- **head_sha:** final 40-hex SHA recorded in `submission.json` after this commit is
  amended (to fold in `receipt.json`) and force-pushed to
  `codex/monkey-i-r02-save-store-ee0799d3f9`; the PR *entry* is opened/merged by the
  lead/publisher from that head via their GitHub API access.
- **provisional PR number:** 117 (next after current max #116). The PR *entry* is
  opened/merged by the lead/publisher via their GitHub API access; see blocker note.

## Blocker (recorded, per KANBAN guidance)
GitHub REST API auth is unavailable on this host (`supervisor_token` / `enrollment_token`
return 401 Bad credentials; no PAT at `E:/ChimeraWork/control/.github_token`; `gh` CLI
absent). SSH deploy key works, so the branch and its head commit are pushed to
`GhostDragonAlpha/Chimera`. The PR page (`/pull/N`) must be opened from the pushed head
by an account with API access. **Smallest unblock:** place a repo-scoped PAT on one line
at `E:/ChimeraWork/control/.github_token`, then open the PR from branch
`codex/monkey-i-r02-save-store-ee0799d3f9`; nothing else is missing. Original attempt
artifacts are preserved untouched in the attempt workspace.
