# report.md — I-R05-RESOURCE-LEDGER-FOLLOWUP

- **Card:** I-R05-RESOURCE-LEDGER-FOLLOWUP (planning id R05, `bounded_implementation`)
- **Attempt:** a4592d4b796542a7ad657d8e2ad7d3ec · branch-3 · base `c525b82c7c3ce0128565424764293a3c85811ab3`
- **criteria_sha256:** `03d70278eca25c1b2f7450abaca7178f475aba038a76ff9e1ed3e5e35669f815`
- **Preregistration:** `PREREGISTRATION.md` (frozen BEFORE implementation, Rule 0; sha256 `a9757722502cb4529d282fc21de25f252b07cd20da846372bc2bc987cc1d800f`)
- **Depends on:** the ACCEPTED I-R05-RESOURCE-LEDGER module — PR #139 head `47c00f05169fa49ea770c274cfe7f280e6710e82`, merge `becdcb2716ee441cfb2832287a349c8f4b6c7090`
- **pr_destination:** `tools/monkey_campaign/contributions/I-R05-RESOURCE-LEDGER-FOLLOWUP/`

## What was built

A thin, production-untouched **adapter** that connects the ACCEPTED
`resource_ledger.py` (sha256 `05cf62184931d6443188cd9b72aa9e88821cc8a9063a351a
7e4d658d6690da6c`) to the EXISTING session teardown hooks and the EXISTING
session teardown tests, exactly as the card demands:

1. **`LedgeredSessionFlow(session_flow.SessionFlow)`** — hook-up proposal A
   (accepted in the parent's report), realized as a SUBCLASS instead of an
   edit (`production_edit_allowed: false`).  It owns the SESSION GENERATION
   integer (mirroring `World.boot_count`, slice_server.py:128); a successful
   restart closes exactly the generation that ended (AFTER the declared
   `World.boot` referent returned) and bumps the generation; a successful
   exit records the session-owned release claims (reverse-acquire order) and
   closes the final generation.  Every close leaves a named receipt in
   `last_trace` (`restart_leaks` / `exit_leaks`) in the exact style of the
   existing `restart_failed` / `exit_failed` records.  The frozen transition
   table, the gating, the quiesce and the one-real-teardown law are the
   pinned flow's own, untouched.
2. **`LedgeredForestScene(forest_loader.ForestScene)`** — hook-up proposal B
   as a subclass: every name the scene registers in `self._resources`
   (including `attach_engine_shutdown`) is mirrored as a
   `(generation, owner="session", "forest:<name>")` ledger record; each
   successful teardown release is mirrored; on the `f08_teardown_leak` path
   the record stays live, so the next close names the leak by exact id.  The
   scene's zero-live audit (`live_after`) and the ledger's live ids are two
   independent counts of one truth, and the tests prove they agree.
3. **A source-pinning import** — the falsifier F1 guard.  The adapter loads
   the accepted ledger bytes (preferring the merged sibling contribution
   `contributions/I-R05-RESOURCE-LEDGER/resource_ledger.py`, falling back to
   the pinned `reference/resource_ledger.py` extraction) and REFUSES BY NAME
   (`adapter_accepted_source_drift`) unless the file hashes exactly to
   `05cf6218…`.  The same guard covers every pinned hook byte
   (`adapter_reference_drift`), including a post-import verification of what
   `session_flow` actually resolved for `input_mapper` / `command_record`.
   A duck-typed ledger stand-in is refused at both adapter constructors
   (`adapter_ledger_type`): the accounting law can only be the accepted
   module's.

## Source identities (exact)

| File | SHA-256 | Lines | Notes |
| --- | --- | --- | --- |
| `adapter.py` | `f1c20f06256f50c8657de17bc7b3245424a5957798a008bfccd3c0a586bcfe9f` | 488 | stdlib only (`hashlib`, `importlib.util`, `sys`, `pathlib`) |
| `test_adapter.py` | `73a1cd832f304f7fac6d9a94acdcf78497fc75e1f512edb6a7ebcd9da4228056` | 513 | stdlib only; imports `adapter` |
| accepted `resource_ledger.py` | `05cf62184931d6443188cd9b72aa9e88821cc8a9063a351a7e4d658d6690da6c` | 504 | byte-identical at PR #139 head 47c00f05 (in `reference/`) |
| pinned `session_flow.py` | `30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf` | 357 | 9afbddcd (`reference/tools/monkey_campaign/product/`) |
| pinned `input_mapper.py` | `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` | — | 9afbddcd |
| pinned `command_record.py` | `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` | — | 9afbddcd |
| pinned `forest_loader.py` | `53d7fdde7deb6223f6760f4d9d6d8f378f3c4bf3cc5513381bf83e68d8cfbb95` | 508 | 9afbddcd (`reference/tools/monkey_campaign/data/monkey_forest/`) |
| pinned `session_flow_tests.py` | `b6ce2bba598fcb8119de82f9a06639ee6d2744c1605ac82c8d699b8df75ef49a` | — | 9afbddcd, the EXISTING teardown suite |

All extraction identities are recorded in `reference/EXTRACTION_LEDGER.json`
(sha256 `401f85f86c09a4e8400d83a7ced76097c9cebe3cf9012a118fdb3a0cfdeae3c0`)
and re-verified at every `import adapter`.  The pinned hooks at the
monkey-play tip are byte-identical to the 9afbddcd blobs (git blob ids
compared), so "current hooks" == "pinned hooks".

## The claim-timing law (deliberate, documented deviation)

Parent proposal A orders exit as release-before-teardown.  This adapter
records the session's release claims AFTER the one real teardown returned.
Reason: a claim must never precede the observable completion of what it
claims — a failed teardown records NOTHING, the generation stays open, and
the eventual close names every still-live record (proven by
`test_raising_teardown_records_nothing_and_closes_nothing`).  Restart does
NOT auto-release either: the old scene's owner tears the scene down (the
mirror records each release) or the close names the leaks — a resource
nobody released can never pass a cycle (the accepted ledger's own law).

## Verification (commands, outputs and hashes in `verification/`)

| # | Command (cwd = this directory) | Result | Wall |
| --- | --- | --- | --- |
| 1 | `python -B -m unittest -v test_adapter` (run 1) | **Ran 26 tests — OK** | 0.186 s |
| 2 | `python -B -m unittest test_adapter` (run 2, determinism) | **Ran 26 tests — OK** | 0.133 s |
| 3 | `python -B adapter.py selftest` | `{"adapter_selftest":"pass",…}` | — |
| 4 | `python -B reference/resource_ledger.py selftest` | `{"selftest":"pass",…}` (the ACCEPTED bytes, via reference) | — |
| 5 | `python -B reference/tools/monkey_campaign/product/session_flow_tests.py` | **RESULT: ALL CHECKS PASS — checks_total 74** | 0.125 s |

Check 5 is the EXISTING session teardown suite (X02 falsifiers F1–F5)
running UNMODIFIED against the exact pinned bytes the adapter imports; its
own receipt (moved to `verification/session_flow_tests_receipt.json` to keep
`reference/` frozen) independently pins the same module hashes as
`EXTRACTION_LEDGER.json`.  First recorded run (run 1 in
`verification/unittest_run1.txt`) is the FINAL code state; the honest first
development run is recorded below.

### First development run (recorded honestly, before the fixes)

`Ran 26 tests: FAILED (failures=4, errors=1)` plus an adapter-selftest FAIL:

1. ERROR `test_imported_ledger_is_the_accepted_module` — real API gap:
   `adapter.RESOURCE_LEDGER_SHA256` (in `__all__`) did not exist yet.  Fixed
   by publishing the verified constant.
2. FAIL `test_adapter_source_has_no_governor_tokens` — a TEST bug: the
   substring `"import time"` appears in adapter PROSE ("verified by sha256
   at import time").  Replaced with a stronger AST check: the adapter's
   complete import set must equal `{__future__, hashlib, importlib.util,
   sys, pathlib}`.
3. FAIL `test_ceilings_flow_through_adapter_closes` — TEST bug: asserted
   ceiling violations on `summary()` (no ceilings) instead of the close-time
   summary that carried them.  Fixed to read `restart_summaries[0]`.
4. FAIL `test_wrong_owner_keeps_record_live_until_close` — wrong TEST
   expectation: the ledger's law is that a RECORDED wrong-owner refusal
   fails the default (zero-budget) cycle even after the owner releases.
   Test corrected to assert exactly that; the module was never changed.
5. FAIL `test_stale_claim_leaves_a_named_failure_not_a_close` — scope fact:
   a release failure event carries the CLAIMED generation (5, not the live
   record's 0), so the evidence lives at whole-ledger scope.  Test asserts
   the whole-ledger summary fails.
6. Adapter selftest FAIL — the same fixture-bug class the parent recorded:
   the selftest session never released `engine:9347` before restart, so the
   ledger correctly named the leak (`ledger_live_at_close`) — falsifier
   detection firing on my own fixture.  Fixed the fixture, not the law.

Second invocation: **26/26 OK**, twice, deterministic (0.006 s of test time,
0.13–0.19 s wall, bound 120 s).

## Card-clause verification

- "Read the winning ledger module and current SessionFlow/forest_loader
  ownership hooks" — done read-only (`git show` at 47c00f05 / 9afbddcd);
  identities pinned above and in `EXTRACTION_LEDGER.json`.
- "a real adapter … around these Python hooks" — both adapters are
  subclasses of the pinned hook classes; the hooks' own doubles
  (`RecordingRestart`, `TeardownDouble`, `CountingMapper`) drive the tests.
- "including a deliberate unreleased resource" — two flavors, both named and
  both FAILING their cycle: an unreleased session resource across restart
  (`test_restart_leak_named_when_session_resource_unreleased`) and an
  operator-owned resource at exit, also proven NOT launderable by
  `max_failures=1000` (`test_exit_deliberate_unreleased_operator_resource_
  fails_cycle`, `test_leak_not_launderable_by_ceiling`), plus the
  `f08_teardown_leak` scene leak
  (`test_raising_release_stays_live_and_close_names_exact_id`).
- "and wrong-generation release" —
  `test_stale_claim_refused_and_current_record_untouched` (refused by name,
  record untouched, releasable by its true generation) and
  `test_stale_claim_leaves_a_named_failure_not_a_close` (the ledger FAILS at
  whole-ledger scope).
- "Publish actual source imports" — the report publishes the exact sha256 of
  every imported source; the import re-verifies them at load time.
- "Never enumerate or terminate operator processes" — the adapter's complete
  import set is `{__future__, hashlib, importlib.util, sys, pathlib}`
  (AST-checked by the suite); no process discovery, termination, launch,
  memory probe, wall clock or network exists anywhere in it.  All engine
  references in tests are recorded doubles of the declared referents.

## Falsifier self-check (PREREGISTRATION.md)

- **F1 rewritten stand-in?** NO — imported file re-hashed to `05cf6218…` at
  import; duck-typed stand-ins refused (`adapter_ledger_type`); suite proves
  the identity (`TestAcceptedSourceIdentity`). GREEN.
- **F2 a leak passes?** NO — three unreleased-resource flavors all FAIL
  their cycle; `max_failures=1000` cannot launder. GREEN.
- **F3 a wrong-generation claim mutates the current record?** NO — refused by
  name, record untouched and releasable by its true generation. GREEN.
- **F4 a production edit?** NONE — the diff touches only
  `contributions/I-R05-RESOURCE-LEDGER-FOLLOWUP/`; `reference/` is a
  read-only extraction (the existing suite's receipt artifact was moved out
  and the tree restored; `reference/` is exactly the 7 pinned files).
  GREEN.
- **F5 native qualification claimed from a fixture?** NOT CLAIMED — see
  Remaining gates. GREEN.

## Remaining gates (open, deliberately)

- **Native engine-process qualification:** the declared teardown referent
  (`World.shutdown_engine`, terminate → wait(10 s) → kill) and the restart
  referent (`World.boot`) are exercised here only as recorded doubles of the
  pinned slice_server paths.  The REAL engine-process soak — actual child
  process closure across repeated restarts, OS handle counts — is a native
  runtime gate this fixture work cannot satisfy.
- **VRAM / device-memory soak:** completely open.  No GPU work was done, no
  VRAM figure exists, and none is inferable from these CPU fixtures.
- **`slice_server.py` wiring (proposal C):** reference only, zero edits —
  the generation mirror rides `World.boot_count` only when the live server
  adopts `LedgeredSessionFlow`.
- **Operator-side adoption:** `owner="operator"` records exist ledger-level;
  no operator flow emits them yet.
- **Parent R05 runtime gates** remain exactly where they were; this card
  closes only the FOLLOWUP objective (connect the accepted module to the
  existing hooks/tests).

## Constraints honored

Code only inside the attempt workspace · no network, installs, GUI, GPU,
training, process control · test invocations bounded (0.19 s worst wall vs
120 s bound) · production checkouts touched read-only (`git show` /
`ls-tree` / `rev-parse` only) · `reference/` frozen after extraction ·
total new output well under 16 MiB.
