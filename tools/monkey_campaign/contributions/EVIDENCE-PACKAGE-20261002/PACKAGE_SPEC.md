# PACKAGE_SPEC.md — the single evidence-package format (chimera.evidence_package.v1)

- **Lane:** wk-evidence-package (chimera-worker under the main Lieutenant), 2026-10-02.
- **Write scope:** `E:/ChimeraWork/monkey-coordination/evidence-package/` only. NO_WORKTREES
  honored: no worktree, no clone; every tooling execution goes through
  `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py` (slots 2/3 for this
  lane); all validation replays EXISTING sealed store bytes, never new physics.
- **Served law (the GOAL's final deliverable, verbatim pins):** "one evidence package binds
  the build and inputs to continuous video, player inputs, and time-aligned state, contact,
  force, and energy records"; "Freeze the build, scene, body and mass ownership, control
  interface, parameters, and pass criteria before the final run"; "an independent reviewer
  must verify the physical claims and confirm that the visible behavior matches the trace."
- **Status of this document:** the format contract the FINAL run must drop into. It is
  TOOLING, not physics: nothing here qualifies a physical claim, and the validation package
  built under it is labeled VALIDATION-ONLY.

---

## 0. Package identity and the one-run law

One package = ONE uninterrupted run. The package is a canonical-JSON object, schema
`chimera.evidence_package.v1`, content-addressed (`package_sha256` over the canonical body,
the acceptance-chain convention: `json.dumps(sort_keys=True, separators=(',',':'))`).

- `package_class`: `FINAL_DEMONSTRATION` or `VALIDATION_ONLY`. A `VALIDATION_ONLY` package
  MUST carry `label` containing "VALIDATION-ONLY" and is NEVER the final deliverable; a
  builder that finds `package_class: VALIDATION_ONLY` without the label refuses
  (`validation_label_missing`).
- `run_identity`: `run_id`, producer card/task, `base_build_id`, the exact command +
  interpreter, `dt_s`, the tick domain `[t0, t1]`, and the sealed receipts that pin the run
  (runner receipt / sealed manifest when produced through task_package.py).
- The package binds artifacts BY REFERENCE + sha256 (store-homed paths). Large datasets
  stay in the evidence store and are referenced by hash (NO_WORKTREES storage law); the
  builder re-hashes every referenced file fresh at build, and `verify` re-hashes again.

## (a) FREEZE MANIFEST — every freezable hashed; post-freeze changes refuse

`freeze_manifest` is the pre-run freeze the GOAL requires, expressed as hashes. Required
sections; a missing section is `freeze_manifest_incomplete`:

| section | contents | source convention |
|---|---|---|
| `build` | build identity string + sha256 of the build artifact/pin (e.g. `cpu-walk-scene-build-N`, engine/pipeline sha) | trace `build_id`; capture manifest `subject_sha256` |
| `scene` | scene id + scene sha256 (the sealed scene file identity) | store-anchored scene bytes (e.g. W03 `scene.json` class) |
| `body_mass_ownership` | REFERENCE to the lineage table — the wk-lineage-verify lane's 10.038 kg composition/ownership/runtime-config verdict feeds this. CITE ONLY THE OWNING LANE'S CURRENT AUTHORITY: `lineage-verify/REPORT.md` sha256 `b7801ce08b53f9f16edbbf67607406e48cdd919d95b44fc6f7f5055e3fbe384f` (supersedes the prior-round `79aa4997...`; the owning lane's EVIDENCE line 94 names the supersession). The citation is BINDABLE, not prose: `reference_binding` names the frozen binding carrying the report and `reference_sha256` must equal that binding's observed sha — a stale citation refuses `freeze_citation_stale`, an unbound one refuses `freeze_citation_unbound`. Do not duplicate or re-derive the table. PLUS the LV-1 EMISSION RECEIPT (below). | lineage-verify lane (dispatch 2026-10-03); assembly-identity comparison ASSEMBLY_IDENTITY.md |
| `control_interface` | interface name, command vector dimension, per-slot command names, the mapping source (input-mapper identity + sha256) | W08 class: `u01_input_mapper` source records; command table in the command-verification receipt |
| `parameters` | dt, seed, declared scenario parameters (mu bands, ceilings — every freezable number) | trace header / prereg |
| `pass_criteria` | preregistration sha256 + criteria sha256 + the pass/fail receipts that operationalize them | frozen prereg bytes (the K01/K02 law: the Lieutenant's COMMITTED bytes are the freeze) |
| `bindings` | `name -> {reference, sha256, size_bytes}` for EVERY artifact the package depends on | acceptance-chain `evidence_files_hashed` gate class: re-hashed fresh at build |

**The LV-1 per-body EMISSION RECEIPT (the mechanical closure of "body and mass
ownership" freezing).** Finding LV-1 of `lineage-verify/REPORT.md` — the
owning lane's CURRENT authority, sha256
`b7801ce08b53f9f16edbbf67607406e48cdd919d95b44fc6f7f5055e3fbe384f`
(supersedes the prior round `79aa4997...`, named in the owning lane's EVIDENCE
line 94; every assembly re-checks the file bytes at build by binding it as
`lineage_report` — the stale 12:43 pin that survived into a 15:03 assembly is
the recorded precedent): the home checkout carries an UNTRACKED stray
`tools/science_funnel/gait_scene.py` (blob `95c8b457...`) building a DIFFERENT
10-body assembly (pelvis 8.184 vs the sealed 7.371998 kg), and the checkout
HEAD does not contain the producer commit — so a LIVE run could silently
consume a different assembly. THEREFORE: at final-run freeze, the BUILD ITSELF
must EMIT its per-body mass table AT LAUNCH — per part: body owner/name + mass
value + the source-artifact sha each part was loaded from — and that emitted,
hash-chained table (with the assembled total and the consumed-mass field) is
hashed INTO the package's freeze manifest as `body_mass_ownership.
emission_receipt = {reference, sha256, per_body_count, assembled_total_kg,
emitted_by_build_sha256}`. The sealed scene bytes ALONE are not sufficient
evidence of what the running build actually loaded. The builder enforces: a
`FINAL_DEMONSTRATION` package without a bound `emission_receipt` refuses
`freeze_emission_receipt_missing`; a `VALIDATION_ONLY` package may carry
`status: EMISSION_RECEIPT_PENDING` with the LV-1 citation (named gap, never
silent). This composes with the build-sha freeze: the emitting build is the
same frozen build that produced the video and the records.

**The citation-rehash law (durable lesson, SGT review F1).** A sha cited in a
spec freezes nothing: citation-only references escape every re-hash gate by
design. Any sha this format cites in a freeze section MUST be carried by a
frozen binding (`reference_binding` + `reference_sha256`), re-hashed fresh at
build and again at verify; a mismatched citation refuses
`freeze_citation_stale`, an unbound one `freeze_citation_unbound`. Assemblies
re-check the owning lane's CURRENT bytes at final-assembly time — never
forward a sha observed at authoring time without re-hashing it into a
binding.

**The freeze law:** `build` writes the manifest with every hash observed; `verify`
re-hashes every binding and refuses `freeze_violation: <name>` on ANY mismatch, and
`package_tampered` if the package JSON itself fails its own content address. A post-freeze
modification of any bound byte therefore cannot verify — demonstrated live in the
validation probes. Amending a freeze means building a NEW package; there is no in-place
amendment.

## (b) CONTINUOUS VIDEO — every frame bound to its tick

Built on the standing certified-capture + walkfilm tooling (cited, extended, never
rebuilt): `chimera.visual_capture_manifest.v1`
(`tools/monkey_campaign/visual_capture.py`; store examples `MAT2-G07/camera`,
`MAT2-W08/camera`) and the walkfilm sealed per-frame manifest law
(`live-viewer/build_walkfilm_playlist.py`: disk sha == sealed manifest sha == sidecar sha,
plan `(shot, tick)` triple-binding).

`video` section:

- `artifact`: the continuous media file `{reference, sha256, size_bytes}`. The sha MUST
  equal the capture manifest's `capture_sha256` (W08 convention: "sha256 of the mkv bytes
  (the media identity)").
- `capture_manifest`: `{reference, sha256}` of the `chimera.visual_capture_manifest.v1`
  (or walkfilm sealed per-frame manifest) that declares views, camera, tick_interval.
- `frame_binding`: the frame<->tick table. Source is either
  `sheet_layout.frame_files` (tick-keyed dict) or a walkfilm-style frame list. Builder law
  (the M09 lesson, worker-wk-m09-capturegate): sheet keys are TICKS, not frame indices —
  resolve them with `sorted(keys, key=int)`; naive index pairing "reports 1/12 and lies".
  Every frame entry resolves to `{frame_id, tick:int, sha256}`; ticks must be unique,
  strictly increasing, inside the records' tick domain, and EVERY tick must resolve to a
  records row. `frame_count` must equal the declared count.
- `binding_receipt`: the capture-validation receipt `{reference, sha256}` that binds
  video bytes <-> trace identity (`trace_sha256` == the bound trace's sha256;
  `video_sha256` == the bound media sha256). A mismatch is `video_trace_identity_mismatch`.
- When loose frame stills are not store-homed (media-embedded), `frame_binding` carries the
  declared tick->sha table from the sealed manifest and the package names
  `still_bytes: MEDIA_EMBEDDED_PINNED` — the binding table is still proven, and the gap is
  named, never silent. The FINAL package requires the stills or an extractable media
  inventory for the reviewer.

## (c) PLAYER INPUTS — the input-event log; prohibitions expressible as checks

`inputs` section binds the event log of record: `{reference, sha256, schema}` plus the
normalized event table. Event schema (superset; sources: W08 `trace.decisions[]` +
`sink_records[]` with `source: u01_input_mapper`; K02-class injection registers):

```
{event_index, command, issued_tick:int, issued_ms, source,
 requested, applied, saturation, wrong_script}
```

The three prohibitions are CHECKS over log+records, not prose — the builder evaluates
each and records `pass/violated` with measured detail. CLAUSE -> MECHANICAL
ENFORCEMENT (every clause below is enforced with a named refusal; a clause without a
named refusal may not appear in this list — recorded-but-not-enforced fields are named
explicitly as attested metadata):

- **no_teleport** (`input_assertion_violation`, class `teleport`):
  (1) every per-tick row's intervention field (`intervention_reason`, K02 class:
  `injections.teleport_at_tick`) must be in the declared-allowed set — the prohibited
  set is `{teleport, position_snap, animation_only}` and an intervention class outside
  the assembly's declared `allowed_interventions` refuses as class
  `undeclared_intervention`; (2) every event's `applied` vector must equal `requested`
  exactly when its declared saturation vector is all-zero (an applied command outside
  requested-plus-clamp is a teleport-class violation); (3) an event whose COMMAND name
  tokenizes to a prohibited token (`teleport`, `snap`, `animation`) refuses.
- **no_hidden_anchor** (`input_assertion_violation`, class `hidden_anchor`):
  (1) no per-tick row records an anchor/weld intervention (`intervention_reason:
  anchor`, K02 class: `injections.hidden_anchor != null`, `sticky_release_weld !=
  false`); (2) an event whose COMMAND name tokenizes to `anchor`/`weld` refuses.
  BOTH the per-tick rows AND the decision-event command names are scanned.
- **no_reset** (`input_assertion_violation`, classes `reset` / `multi_source_session`):
  (1) the records' tick domain is exactly contiguous `{t0..t1}` with no duplicate tick
  and no negative step (a reset shows as a counter restart or a duplicated tick);
  (2) an event whose COMMAND name tokenizes to `reset`/`respawn`/`restart` refuses;
  (3) the SESSION census is BYTE-DERIVED ONLY — identities recorded in the bound trace
  (`sink_records[].source` + decisions' own `source` fields) — and must be exactly ONE
  identity, unless the assembly declares `allowed_sources`, in which case every
  byte-derived source must be inside that declared set (the widening is then a frozen,
  reviewed decision carried in the package). The assembly's `source_default` is
  SELF-DECLARED: it is recorded as `declared_source_default` (attested metadata) and
  NEVER counts toward the session census.

An input log that cannot express these checks (missing tick, missing byte-derived
source identity, missing intervention surface) is refused:
`input_log_not_expressible`.

## (d) TIME-ALIGNED RECORDS — one row per tick, joinable on tick_key

`records` section binds `{reference, sha256, schema}` and declares:

- `tick_key`: the row tick field (convention: `t_tick`/`tick`). Row lookup is NUMERIC:
  keys are resolved as ints and sorted with `key=int` (the M09 lesson — string-keyed
  tick tables sort '0','10','2' naively; this builder never does).
- `tick_domain`: `[t0, t1]` with `contiguous: true` required.
- The four record classes, each `present` with its field map, or in `declared_absent`
  WITH a reason (an unnamed absence is `record_class_absent_unnamed`):
  - **state**: per-tick state identity (`state_sha256` per row — the frame<->state pin) +
    state channels (com, phase, yaw, gaps).
  - **contact**: the contact census in the G04/K01/K02 per-channel convention — per tick,
    per channel/site: `jn_Ns`, `jt_Ns`, mode `stick|slip|no_contact` (flags), surfaces
    pair, cumulative displacement; aggregates (`contact_count`).
  - **force**: force/impulse channels per tick (per-channel contact impulse, per-tick
    force sums; K02 class: `ledger.trunk_anchor/trunk_contact` reciprocity pairs).
  - **energy**: the per-tick energy ledger in the K02 `acct_rows` class — KE start/after,
    work terms (gravity, press, friction losses), residuals, with the G07/K02 identity law
    (gravity work == KE gain within the declared window; hold ledgers close within 1e-9 J).
    A run whose harness did not record per-tick energy must carry
    `declared_absent: [{class: energy, reason: ...}]`; the FINAL package requires this
    class PRESENT (the GOAL names energy explicitly).
- The join law: frame ticks, input event ticks, and record rows all join on the same
  integer tick key. `verify` re-proves the join.

## (e) THE SYNC LAW + reviewer-verification plan

**Sync law:** every frame's tick is resolved in the records; every input event's tick is
inside the domain and matches a records row; the media identity, trace identity and
per-frame tick table agree. ANY desync/unbound row is a package FAILURE — the builder
refuses (exit 2, named JSON refusal on stderr, appended to `refusals.jsonl`) and NO
package is produced. Checks, each recorded with measured values:

1. `sync_frames_resolved` — every frame tick exists in records (probe A fires this law).
2. `sync_frame_ticks_unique_monotonic` — no duplicate/reordered frame ticks.
3. `sync_events_in_domain` — every input event tick in `[t0,t1]`.
4. `sync_video_trace_identity` — capture manifest media sha == video bytes sha ==
   binding receipt's video sha; binding receipt's trace sha == bound trace sha.
5. `sync_input_application` — per-event applied == declared mapping of requested within
   saturation (teleport class).

**Reviewer-verification plan (what the independent reviewer checks to confirm
visible-behavior-matches-trace):** the package ships `review_plan` with:

- per-PHASE transition evidence: for every declared phase boundary (walk-uneven->stop->
  approach->grasp->climb->hold->descend->release->land->resume), the records rows at the
  boundary ticks and the frames nearest the boundary, so the reviewer sees the state
  discontinuity that IS a commanded transition and can check there is no discontinuity
  that is NOT commanded;
- the phase-continuity law stated with its mechanical proof: one tick sequence
  (no_reset check), one uninterrupted run (single session/receipts), no reset between
  phases — the reviewer re-runs `verify` rather than trusting this document;
- the no-teleport/no-hidden-anchor/no-reset check results with per-tick coverage counts;
- a bounded frame sample law for the final package: reviewer-sampled frames (>= the
  campaign's standing >=20-frame picture-review sample) re-checked against their bound
  records rows (state_sha256 + phase + contact census), with the Sergeant's independent
  picture review routed through the Lieutenant (this text-only lane claims no picture
  verification authority);
- the pass-criteria receipt set, so the reviewer verifies the physical CLAIMS against the
  frozen criteria, not against prose.

## Extension-point investigation (recorded per dispatch)

`acceptance-chain/acceptance_packet.py` was investigated FIRST as the candidate base. Its
packet class is a CARD-packet: it binds task_id/PR/criteria/evidence-manifest for the
acceptance DECISION workflow (registry + GitHub gates) and has no tick, frame, input or
freeze-of-run-artifact concept. Extending it would (1) edit another lane's owned tool
bytes (acceptance-chain owns that file; this lane's write scope is evidence-package/), and
(2) conflate the acceptance decision chain with package assembly. DECISION: a NEW
full-loop class `chimera.evidence_package.v1` in `build_package.py` (this lane), reusing
the acceptance-chain CONVENTIONS only (canonical JSON content addressing, named refusals
with `refusals.jsonl`, fresh re-hash gates, immutable artifact discipline) by citation,
not import. The final package routes through the existing acceptance/publication path;
this lane claims no merge authority.

## Falsifiers of the FORMAT itself (each demonstrated in validation)

1. A package that cannot bind video<->inputs<->records at any tick -> build refuses
   `sync_frame_tick_unresolved`/`sync_frame_outside_tick_domain`; no package written.
2. A freeze manifest that accepts a post-freeze modification -> `verify` refuses
   `freeze_violation` on any bound-byte change and `package_tampered` on package edit.
3. An input log that cannot express no-teleport/no-reset -> `input_log_not_expressible`;
   an injected teleport/reset/anchor event -> `input_assertion_violation: *`.
4. A FINAL package without the LV-1 per-body emission receipt -> `build` refuses
   `freeze_emission_receipt_missing`; a validation package must name
   `emission_status: EMISSION_RECEIPT_PENDING` or bind the receipt.
5. A stale or unbound lineage citation (SGT review F1) -> `build` refuses
   `freeze_citation_stale` / `freeze_citation_unbound`; every cited sha must be
   carried by a frozen binding and re-hashed at build and verify.
6. A mixed-source session log or a prohibited command name (SGT review F2) ->
   `build` refuses `input_assertion_violation` (class `multi_source_session`) or
   the matching prohibited class; the session census is byte-derived only, and
   every no-teleport/no-hidden-anchor/no-reset clause has its own mechanical
   refusal (see section (c)).
