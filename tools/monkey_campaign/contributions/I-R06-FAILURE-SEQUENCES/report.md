# REPORT — I-R06-FAILURE-SEQUENCES

```
card:     I-R06-FAILURE-SEQUENCES (planning id R06)
attempt:  c57fd6bb125142ee9d593f800eb32dd4
branch:   branch-7
base:     9afbddcd90164b5544a16fd0bc72278d985eb6e3
prereg:   PREREGISTRATION.md (frozen before any implementation edit)
ledger:   reference/EXTRACTION_LEDGER.json
```

## WHAT WAS BUILT

A deterministic, stdlib-only (Python 3.11+), headless failure-sequence
regression runner that drives the EXISTING pinned product components —
`SessionFlow` filtering `FocusPolicy` filtering `InputMapper`, plus the seam's
`CommandRecord` — through eight CROSS-component sequences no component's own
unit suite exercises, and checks three invariants on the observed command
stream: release-no-latch (a), pause-silence (b), teardown-exactly-once (c).

Files:
- `failure_sequences.py` — the runner: import binding, injected clock
  (`SteppedClock`), recording sink, session composer, invariant checkers, the
  eight sequences, CLI (`python failure_sequences.py [reference_root]`).
- `test_failure_sequences.py` — stdlib unittest suite: 8 sequence tests +
  binding/refusal tests + determinism + runtime budget + 2 deliberately-broken
  controls (see below).
- `reference/` — byte-exact extraction of the pinned sources (read-only after
  extraction), with `EXTRACTION_LEDGER.json` (path + sha256 + git blob per
  file).
- `PREREGISTRATION.md` — the Rule-0 freeze (statement / prediction /
  falsifiers FS-1..FS-3).

## IMPORT-BINDING MECHANISM (the rewrite falsifier's guard, how it works)

At runner init `bind_components()`:
1. locates the extraction (`FAILURE_SEQ_REFERENCE` env or argument honored
   EXACTLY — an invalid named root is refused, never silently substituted;
   otherwise `<runner dir>/reference`, then ancestors),
2. purges any stale `tools.*` / flat `input_mapper` modules from
   `sys.modules` so this bind can only resolve from THIS root, inserts the
   root at `sys.path[0]`, and imports the four pinned modules,
3. resolves each module's `__file__` and hashes the real bytes; REFUSES
   (`ImportBindingError`) unless: sha256 matches the ledger AND the git blob
   sha1 (`sha1("blob <len>\0" + bytes)`) re-derives to the ledger's
   `git_blob` recorded from revision `9afbddcd90164b5544a16fd0bc72278d985eb6e3`
   AND the file physically lives under the reference root (no shadowing),
4. verifies `focus_policy`'s flat `_im` resolves to the SAME FILE as the
   package `tools.monkey_campaign.product.input_mapper` (they are two module
   objects over one pinned file — session_flow imports the package path,
   focus_policy flat-imports; frozen constants stay identity-equal because
   both read them from the single `command_record` module object), and
5. asserts the frozen-constant object-identity law across the modules
   (`input_mapper.V_MAX_IN_BAND_M_S is command_record.V_MAX_IN_BAND_M_S`,
   `focus_policy.RELEASE_DECAY_MS is input_mapper.RELEASE_DECAY_MS`,
   `focus_policy.MAX_AGE_MS is input_mapper.VALID_MS`,
   `session_flow.INTERVAL_MS is input_mapper.INTERVAL_MS`, plus HOLD_TICKS).

Any mismatch raises and the runner does not run. A corrupted-copy test in the
suite mutates one byte of a copied extraction and proves the guard fires.

### Verified binding (real sha256, from the run + ledger)

| file (under reference/) | sha256 | git blob @ 9afbddcd |
|---|---|---|
| tools/science_funnel/typeb_export/command_record.py | 6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e | a9e0444fb495be213faf2023378fca11c43c5611 |
| tools/monkey_campaign/product/input_mapper.py | 7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44 | b872859dfc80942125d75552983e81675dd93d64 |
| tools/monkey_campaign/product/session_flow.py | 30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf | 3ff34527d5d1b07da98b88a00c0af92c6191afac |
| tools/monkey_campaign/product/focus_policy.py | e0b23968bb8ee8e7c5449da464948d68cc67bf3cc62db40dd30a73ee8ef0f9d0 | 90843c73f446e0a16297d006eb03b18e30df783c |
| tools/monkey_campaign/product/focus_policy_tests.py | f1d7a2fd39dca37729532c41a74f2d061e6d7fc95dedb3da564d13b2b4304fa9 | f4d580289fb22cdb8b5ae612c768ea8049ff5cb8 |
| tools/science_funnel/__init__.py | c5a9f9b162177ec18d127edb799bbfe1ba08442ed95c72f8f0947f9d64618b19 | 2b8eadef87ac58c4dea52236d59a1e91f15639ac |
| tools/science_funnel/typeb_export/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | e69de29bb2d1d6434b8b29ae775ad8c2e48c5391 |

Extraction identity was proven at extraction time by `git hash-object` equal
to the pinned blob id for every file. Import mechanism: `tools`,
`tools.monkey_campaign`, `tools.monkey_campaign.product` are PEP 420 implicit
namespace packages (NO `__init__.py` for them exists at the pinned revision —
a fact of the source tree, not an omission); `science_funnel` and
`typeb_export` are regular packages whose `__init__.py` files are extracted.

## SEQUENCE INVENTORY (each cross-component sequence + the invariant it protects)

| id | sequence | components crossed | invariant |
|----|----------|--------------------|-----------|
| SEQ-01 | release-stops-emission: W held through 5 boundaries, released between boundaries, 5 further ticks | flow→mapper→gate→sink | (a) release decays ≤ 2 samples within RELEASE_DECAY_MS=100, lands on exact 0.0, then silence; held empties |
| SEQ-02 | pause-silences-locomotion: W emitting, Escape pauses mid-emission, 9 ticks while paused | flow quiesce→mapper→sink | (b) zero records after pause; quiesce receipt held=[]; 9 named decision_tick drops |
| SEQ-03 | resume-fresh-grid-no-phantom: pause 1.9 s, resume, ticks, NEW press | flow resume→mapper tail logic | (b)+(a) exactly ONE exact-0.0 resume-tail record (no phantom positive), then a fresh full-speed grid from the new press |
| SEQ-04 | restart-through-pause boots once; exit tears down once; repeated close + post-exit keys | flow→World.boot / World.shutdown_engine→mapper | (c) boot==1, teardown==terminate→wait→kill exactly once, terminal state, post-exit silence + named drops; (a) resume tail |
| SEQ-05 | blur-mid-emission decays to silence; blurred press dropped; focus recovery arms fresh grid | focus policy→mapper→gate→sink, flow gating | (a) post-blur decay ≤ deadline ending exact 0.0; probe: held empty AT the blur instant; dropped_blurred named |
| SEQ-06 | disconnect/reconnect no-zombie: W + pending mouse counts at disconnect, dropped press+mouse while disconnected, reconnect, fresh press | focus(disconnect)→mapper→flow | (a)+(b) ≤2 decay records ≤ deadline, silence while disconnected, named drops, named disconnect/reconnect events, fresh grid after reconnect |
| SEQ-07 | mid-play restart key is a named no-op | flow table→world (NO boot)→mapper | (c) state stays playing, boot==0, no quiesce, W keeps re-issuing bounded records, R named-dropped |
| SEQ-08 | exit from attract: teardown before anything ever played; repeated Q | flow→World.shutdown_engine | (c) teardown exactly once from attract, sink empty forever, terminal, all post-exit events named-dropped |

No duplication of the existing unit suites: `focus_policy_tests.py`,
`input_mapper_tests.py`, `session_flow_tests.py` each test one component; this
card's value is the composed seams (flow×focus×mapper×sink×world doubles).

## MOCKED-vs-REAL BOUNDARY STATEMENT

**All boundaries in this card are MOCKED.** The clock is an injected
integer-millisecond stepper (no wall time anywhere); the command sink is a
recording list; boot/teardown are the pinned session_flow module's own
`RecordingRestart` / `TeardownDouble` doubles; blur/disconnect/reconnect are
plain method calls on the policy surface. No window, process, device,
transport, engine, or operator input is touched. **No real Windows/device-loss
testing was performed and NONE is certified or implied** — these are
regression fences over the pinned headless logic only.

## BROKEN CONTROLS (FS-3 — the runner must fail bad behavior)

- CTRL-01 `LatchingMapper` (subclasses the REAL pinned InputMapper, swallows
  speed-key releases) replayed through the IDENTICAL SEQ-01 steps+checks:
  **FAIL** with `zombie[seq01-key-release]: positive speed 0.763625 still
  emitted at 1350 ms, later than release 1210 + decay 100 = 1310 (released
  input remained latched)` (+2 more zombie violations, held-set and no-land
  violations). The failure preserves the minimal event log (13 events from
  `key_down Return@995`) + full component identity (module files + hashes).
- CTRL-02 `QuiesceIgnoringMapper` (swallows `release_all`) through the
  IDENTICAL SEQ-02 script: **FAIL** with `quiesce: mapper still holds ['W']
  after the pause quiesce` + the flow's own quiesce receipt showing held
  `['W']`.
- A guard test asserts the controls are NEVER used in any sequence under test
  (`used_control_mapper` is None for all 8 green runs).

## FALSIFIER SELF-CHECK

- **FS-1 (rewrite falsifier): NOT TRIGGERED.** Every sequence under test ran
  against the hash-verified pinned modules (table above); the runner refuses
  on any mismatch — proven by the corrupted-extraction test (`IMPORT BINDING
  FAILED ... input_mapper.py`), the foreign-root refusal test, and the
  under-reference-root check. The runner declares zero numeric constants and
  zero mapping/flow logic of its own; all numbers are read from the verified
  modules.
- **FS-2 (certification falsifier): NOT TRIGGERED.** Mocked boundary statement
  above; no device-loss certification claimed anywhere in this card.
- **FS-3 (rubber-stamp falsifier): NOT TRIGGERED.** Both broken controls were
  caught with the expected violation classes (evidence above).

## FIRST-RUN FAILURES (honest record, in order)

1. `NameError: im` in `bind_components`'s identity-check block (alias defined
   in a later scope). Fixed by defining the alias.
2. `ImportBindingError: focus_policy._im is package input_mapper` — a WRONG
   check I wrote: flat and package imports are legitimately two module objects
   over the same pinned file. Replaced with the `__file__` equality check
   (recorded in the ledger's import_mechanism note).
3. Runner first functional run: 1/8 — all flow sequences failed because
   `SessionFlow` boots in `attract` and no sequence sent the start key. Fixed:
   `Return`@995 (confirm → playing) added to SEQ-01..07.
4. SEQ-05/06 failed with "mapper holds ['W'] while blurred/disconnected": the
   checks read END-of-sequence state where a legitimate recovery press had
   re-armed W. Fixed with mid-sequence `probe()` snapshots taken AT the
   blur/disconnect instant.
5. Test file: `component_identity` (a dict attribute) called as a method — 9
   errors. Fixed.
6. Test file: an explicitly-passed invalid extraction root silently fell
   through to the relative search. Fixed: named roots are honored exactly,
   refused if invalid (fail-closed).

## MEASURED RESULTS

- Runner CLI: **8/8 sequences PASS**, wall 0.212 s (exit 0).
- Unittest suite: **17/17 OK**, 0.085–0.090 s (suite-internal), wall 0.372 s.
  Limits: each invocation < 120 s (prereg predicted < 5 s — held).
- Determinism: two full `run_all()` passes produce identical verdicts and
  identical violation lists (asserted in-suite); no wall clock, no randomness.
- Total new output: ~218 KB (reference extraction 158 KB + runner 41 KB +
  tests 10 KB + docs) << 16 MiB budget.

## REMAINING GATES

- Parent R06 gates remain OPEN — this card is one bounded implementation, not
  the row's completion.
- No device-loss certification (see boundary statement): real Windows alt-tab,
  real device disconnect, real process teardown behavior are OUT OF SCOPE here
  and remain with the integration lanes that own those surfaces.
- The checkout copy of `failure_sequences.py` intentionally ships without
  `reference/`; point it at an extraction via `FAILURE_SEQ_REFERENCE` or the
  positional argument (it fails closed with instructions otherwise).

## EQUIVALENT-CODE CHECK (mandated)

`git grep` at the pinned revision found NO existing input/focus/session
failure-sequence runner. `tools/thin_client_pilot/replay_runner.py` matched
"replay_runner" but is a different domain (replays recorded engine frames over
a loopback HTTP server for the thin-client pilot; numpy + http.server) — not
extendable for this card's headless component sequences, and not imported.
Nothing was duplicated from it.
