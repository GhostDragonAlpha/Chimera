# PREREGISTRATION — MAT2-F06 implement and qualify terrain-aware walking

Frozen BEFORE any implementation file, harness run, measurement or capture
frame of this card exists. This file is committed ALONE (separate-first; the
M03/P04 law). Every emitted receipt refuses any document whose
`preregistration_sha256` does not match these live bytes.

- Card MAT2-F06 (planning id F06, wave 11, slot 1), agent `wk-f06-arrival-1`,
  attempt `36d640396a624ee79056fef8c8a74cd9`, attempt workspace
  `E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-F06\36d640396a624ee79056fef8c8a74cd9`,
  file package `package` (NO_WORKTREES law: pinned file package, no clone, no
  worktree), publication branch `review/MAT2-F06`, PR base `astra/gait-capture`.
- Criteria sha256 `a1d7040a03bd15fc12797edbb11cf44e081712539de84e900e99b95478772779`
  (startup join == registry `kanban.cards[MAT2-F06].criteria_sha256`, re-read
  READ-ONLY (`file:...?mode=ro`) from
  `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3` at run time;
  mismatch = refusal `criteria_pin_mismatch`. Registry join verified at prereg
  freeze: card state OPEN, criteria equal, profile `walking`/`motion`.)
- done_when (verbatim, registry): "Player walks the declared uneven-ground
  cases with certified runtime/training agreement. Material-first addition:
  Qualify player-controlled walking between trees and on the declared
  uneven-ground envelope in the same build as W10, with actual contacts."
- Observation (verbatim, registry): "Any expanded training objective gets a new
  approved runbook".
- Card task falsifier (verbatim): "Sliding/penetration, unsupported
  propulsion, hidden reset, wrong command response or diagnostic/clean state
  divergence fails."
- Profile: `walking`/`motion` (registry read-only at capture time; G7);
  numerical_evidence_required true; clean_view_required true; diagnostic
  layers ["skeleton", "foot contacts and normals", "support/COM markers",
  "command and tick overlay", "stable 3D labels"]; views ["full-body ground
  overview", "side view of stance/swing", "close-up of foot-ground contact"];
  profile procedure (verbatim): "Replay the frozen start/stop/turn/speed/fall
  sequence; inspect stance and swing over the full declared interval. Use the
  task-owned subset of layers/behaviors. Inventory absent or unresolved
  components explicitly; do not require downstream skills to accept an
  upstream interface. Freeze exact applicable probes and views before
  execution."
- Base: `a07ac859d4ef16bb34d4006a75c4de8dbee462b4` = the publisher-seeded
  `refs/remotes/origin/review/MAT2-F06` (the integrated tip: the W10 merge,
  PR #311 — F05's terrain envelope, W07, W08's corrected seam, W09, and W10's
  walking acceptance in the pinned clearing build). The file package is
  pinned to this base by worker_start preparation. (The first startup
  BLOCKED on the missing named ref; the publisher seeded it; no fallback
  base was ever used.)
- Composed against CARD_STARTER v5/v6 and the house standards:
  `IMPLEMENTER_CHECKLIST.md` (G1-G9) + `TOOLKIT.md` (P1-P9), cited at the
  candidate commit. Dispatch brief:
  `E:/ChimeraWork/monkey-coordination/gap-analysis/wave-11.md` (MAT2-F06
  section). Climb-derivation debt rows consumed:
  `E:/ChimeraWork/monkey-coordination/climb-derivation/DERIVATION.md` gap 10
  (step-over NAMED-ABSENT owner F06; trunk-approach placement laws).
- Calculations: this card declares NO new calculation. It consumes sealed
  upstream work read-only: C11 (walking tracking and stability, sealed by
  W08, re-executed on terrain by this card's arms), C14 (terrain
  geometry/consistency, sealed by F02/F04/F05/F07 — consumed through their
  pinned modules and declarations). Nothing sealed is recomputed or
  re-decided; every sealed number this card cites is re-verified against its
  pinned bytes at run time.

## 0. The governing frame (what "terrain-aware walking" means here)

THE CERTIFIED WALKING RUNTIME IS THE FROZEN CERTIFIED LINE — nothing else.
W04 froze the runtime/training contract and issued the certificate; W07
loaded the frozen line bit-for-bit; W08 commanded it through the actual
player command port; W09 wrapped the declared supervisor; W10 walked it in
the pinned clearing build. This card adds NO policy, NO reissue, NO retune,
and NO training run: it adds a DECLARED TERRAIN EXTENSION around the
certified scene so the same player commands walk the DECLARED uneven-ground
envelope of the same pinned clearing build, with actual contacts, and it
resolves the three F05-owned named-absent variables that belong to F06
(`x_max_qualified_slope`, `x_step_over_case`,
`x_slope_gait_qualification`) plus the climb derivation's gap-10
approach-to-grasp geometry, by MEASUREMENT, whatever the verdicts are.

- "THE SCENE" is the certified declared scene `cpu-walk-scene/1.0.0`, build
  `cpu-walk-scene-build-N` — the walking scene of record, pinned bytes,
  zero modification (the sealed lane bytes keep their recorded sha256s; a
  changed sha is refusal `input_pin_mismatch`). The claim class stays
  offline/trace at the 300 Hz tick (TC-11 COST-GAP carried; no real-time
  claim).
- "THE TERRAIN" is the pinned F02 clearing bundle — the ONE surface with
  render arrays == collision triangulation (seal F02/F04/F07) — queried
  through the PINNED F02 `terrain_query.py` (`height_at`, `gradient_at`,
  `classify`; a drifted bundle or module is refusal `input_pin_mismatch`).
  The declared obstacles are the pinned F07 declaration rows; the climbable
  trunk is the pinned F03/F02 analytic cylinder.
- "PLAYER" is the pinned U01/U03 command seam exactly as W08/W10 consumed it
  (`InputMapper` -> versioned `CommandRecord` v1, INTERVAL_MS=50, the pinned
  consumer-side expiry contract) over an injected integer-millisecond clock
  into a recording sink; commands are projected by the FROZEN W08 adapter
  law and applied OPEN-LOOP (`scene.step(applied, saturation)`). Nothing
  here closes a loop around position: the walk scripts are frozen event
  tables, and every arrival claim carries its derived open-loop band.
- "CERTIFIED RUNTIME/TRAINING AGREEMENT" is executed, not asserted: (i) the
  extension's flat-surface regression arm (A0) must reproduce the certified
  line's state chains BIT-IDENTICALLY (P1) — the certificate-bound build N
  laws are untouched on the certified surface; (ii) the terrain laws of
  section 3 are ONE declared implementation (this card's own module, sha
  recorded in every receipt) — the same declared scene definition a future
  approved training runbook would consume; (iii) this card runs NO training
  and expands NO training objective (the observation clause honored): the
  W06 sealed record stands (three seeds DEGRADED even on the flat certified
  line), flat-ground training transfer to ANY nonzero slope remains
  unevidenced (F05), and the trained bundle stays BLOCKED by the pinned
  deploy gate (W06/W07 heritage, re-proven at this card's pins by the
  section 2 gate steps).
- "THE DECLARED UNEVEN-GROUND CASES" are the sealed F07 routes and the F05
  declared envelope, consumed read-only: the F05 declared slope bound
  0.05 m/m with the F07 `terrain_slope_rule` (cells whose measured query
  slope exceeds 0.05 are not passable — declared, never an invisible stop),
  the F07 walkability mask (81x81 at 0.5 m, body envelope 0.25 m, obstacle
  footprints + the trunk's own 0.287 m blocking ring, extent rule 19.75 m),
  and the F07 sealed route receipts (re-derived at run time from the pinned
  modules; equality with the sealed receipt values is prediction P2).
- "BETWEEN TREES / SCENE FURNITURE" is honest about the declared scene: ONE
  climbable trunk (`trunk_01`), seven declared obstacles, the 80-post
  boundary ring. The route cases walk between the declared obstacle
  footprints and the trunk under the declared clearance rules; no second
  tree exists anywhere in the declared scene and none is invented here.
- Physics charter: commands choose actuator setpoints; nothing writes scene
  state. The pinned scene's public stepping API (`step(applied, saturation)`)
  is the only motion path in every arm; the extension reads the scene and
  the pinned surface, and writes ONLY its own declared extension channels
  (section 3). The render path consumes records only (FB6 proves a
  state-writing render diverges and refuses).
- The no-reissue law: the EXISTING certificate is deployed; nothing is
  re-issued, re-certified or amended; no trained bundle is loaded (the gate
  BLOCKs them; W07's executed discrimination is pinned and carried).

## 1. Input pins (verified byte-exact at attempt start; drift = refusal `input_pin_mismatch` / `input_pin_missing`)

Store pins (evidence-store `E:/ChimeraWork/monkey-coordination/evidence-store/`):
- `MAT2-W04/numerical/w04_certificate.json` `07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598`
- `MAT2-W04/numerical/checks_receipt.json` `05e28bbaffcf9d65db174ec9b83708d33705922ac506b1cee852a2f9790744c9`
- `MAT2-W09/numerical/out_of_envelope_receipt.json` `0880a18a46b99e9463cde8f64fafc6daff82a9b78f04ea5e2960abef963cb4c7`
- `MAT2-W09/numerical/checks_receipt.json` `e4cd94ae5c77a7dc9a5ecfba0e02ad4ae100ebabf1995132bbe9f41a3c2b4430`
- `MAT2-W09/numerical/falsifier_receipt.json` `3a61cdbf43f7b11b4b284c7be969c5f0a36208556942f0832f1022fe87b1204c`
- `MAT2-F07/numerical/checks.json` `0a7e94b545e4add955eb3f0315f8a783f00e2ebbcf4a2a44f43398b72916fb70`
  (the sealed route/obstacle receipt: route metric equality is P2)
- `MAT2-F05/source/TERRAIN_REPORT.md` `2b4d9905be1f9f888a3ff33cb4c22a23f009053471c4fd609280bc7b2cba4672`
  (the authored 10/20/30 deg walk-class context, section 8 item 6)

Base-blob pins (read from the shared repository's Git object database at the
package base `a07ac859d4ef16bb34d4006a75c4de8dbee462b4` through the DECLARED
read-only `git cat-file` access — W10's `source_access.py` pattern, pinned;
the blob identities were verified at prereg freeze):
- `tools/monkey_campaign/contributions/MAT2-F02/pins/terrain_bundle.json` `446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52`
- `tools/monkey_campaign/contributions/MAT2-F02/pins/terrain_query.py` `b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1`
- `tools/monkey_campaign/contributions/MAT2-F02/pins/terrain_bundle.py` `c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e`
- `tools/monkey_campaign/contributions/MAT2-F02/pins/clearing_recipe.py` `ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc`
- `tools/monkey_campaign/contributions/MAT2-F02/pins/clearing_declaration.json` `18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1`
- `tools/monkey_campaign/contributions/MAT2-F02/pins/trunk_declaration.json` `94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1`
  (the trunk solid: axis base [11.976783, 0, 2.471766], radius 0.037 m,
  height 1.158 m; `derivation.gravity_m_s2` 9.80665 — this card's pinned g)
- `tools/monkey_campaign/contributions/MAT2-F03/assets/trunk_01_mesh.json` `3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7`
- `tools/monkey_campaign/contributions/MAT2-F07/implementation.py` `49a975c7a1a14238eb79bd5edcb0e96bbd5231a2cdf329dccacd282f65b36a94`
  (THE ROUTE/MASK AUTHORITY: `build_mask`, `route_path`, `route_metrics`,
  `verify_routes`, `destination_table` are executed from these pinned bytes;
  the sealed F07 behaviors, including `contact_stop`, are consumed verbatim)
- `tools/monkey_campaign/contributions/MAT2-F07/assets/obstacle_declaration.json` `73525a3de022d5b8d9901ca90fde77124904471f33a67f2f79a94f7ad1636769`
  (the 7 declared obstacles with footprints, extents, matter and the declared
  `contact_stop` behavior)
- `tools/monkey_campaign/contributions/MAT2-F07/evidence/route_trace.json` `f159edd59fa2047326c130945a74d4451c164e38d7a8b371a5e6330c69d0b729`
- `tools/monkey_campaign/contributions/MAT2-F05/evidence/terrain_envelope_declaration.json` `3fa7e5f4d91936012716f44212cb05f853e8335a9e561c5a53fb7902a5624208`
  (THE ENVELOPE AUTHORITY: the F05 named-absent variables this card owns,
  the declared slope bound 0.05, the friction placeholder table)
- `tools/monkey_campaign/contributions/MAT2-F05/checks_receipt.json` `cdc00269b928fcdd858a618acc8a824e6ea0f7a332e8673a3d0492d65b87b1e5`
- `tools/monkey_campaign/contributions/MAT2-W08/PREREGISTRATION.md` `00a04e08411ed079aee9e0ef43f9221c69abc84612f66311e4db4822f6c8412a`
  (THE FROZEN COMMAND SCRIPT + ADAPTER LAW AUTHORITY: its section 4.1
  script, 4.2 adapter law and 4.4 wrong-command probe are replayed VERBATIM)
- `tools/monkey_campaign/contributions/MAT2-W08/receipts/command_verification_receipt.json` `bb9e014b160062d486002745571fd4485a50431cfdbc25038ebb9bed1171f787`
- `tools/monkey_campaign/contributions/MAT2-W09/PREREGISTRATION.md` `6a3e0f6f5e0a0d7cbad595e0d16285556608b93fa77ef77dc59c30ae962f9d7b`
- `tools/monkey_campaign/contributions/MAT2-W09/out_of_envelope.py` `7245739a746aaeb259a2720c97dbdfec4a88b77aed997cd0c9f961f5ca89d782`
  (the sealed supervisor: observation role on the clean terrain arms)
- `tools/monkey_campaign/contributions/MAT2-W10/PREREGISTRATION.md` `394463ab4172590af881194980460913dac751cde77ba32aab6111c497eda655`
- `tools/monkey_campaign/contributions/MAT2-W10/AMENDMENT-A1.md` `9c32048ce80a33f9b40d5f41ee9bd4111deb307ccb65f6d2bf2c5776b3aa42de`
- `tools/monkey_campaign/contributions/MAT2-W10/AMENDMENT-A2.md` `f47b30f0244954ee18a0cddd37af2e633fcbe791e940a3a858c8cb3ccd04e837`
- `tools/monkey_campaign/contributions/MAT2-W10/AMENDMENT-A3.md` `caca29ac7df93fa2e569349a1b28e05b64039401dc59f314bfd897917a0c4b10`
- `tools/monkey_campaign/contributions/MAT2-W10/command_model.py` `0f9fa1a37092760ab4de05bcd32a7b0c769202dddd4347ff54fbdb5c77d184aa`
  (THE FROZEN SCRIPT/ADAPTER MODULE: `feed_events`, `now_ms_of`,
  `derived_bounds`, `CommandAdapter` consumed byte-exact)
- `tools/monkey_campaign/contributions/MAT2-W10/verify_inputs.py` `25c5fc289a48f24886510d8849856044016e155c627b92c78c15a8781f18f4f6`
  (consumed as PATTERN source for the pin/registry/extraction machinery,
  re-authored for this card's pin table; never imported)
- `tools/monkey_campaign/contributions/MAT2-W10/source_access.py` `4eea1c5c9e10263b02f3a607a280d52f2a8f5862d651834e1794e22c80963ccc`
  (THE DECLARED read-only base-blob access module; pinned and imported
  byte-exact: the ONLY subprocess module in this contribution besides the
  declared capture tool calls)
- `tools/monkey_campaign/contributions/MAT2-W10/run_capture.py` `a078928fcdbe78b7982d20fc362f7f9e021c3360c47523fb2af6cc564af9bf2a`
  and `tools/monkey_campaign/contributions/MAT2-W10/visualization.py` `2e98e8d803f1fde383b00f648100bc8404eac41e3e27db9f6bc32a03de71fafb`
  and `tools/monkey_campaign/contributions/MAT2-W10/make_report.py` `b40b1f9ee349ee095e0b20a155d504f236f87e6177e96fdb15d17603eeb8a31d`
  and `tools/monkey_campaign/contributions/MAT2-W10/lint_report_numbers.py` `c2f046439ad330a1d748468b20fefdfc452f67deaa64272b931f0eb8ccfd1405`
  (consumed as PATTERN source for capture/report/lint tooling, adapted to
  this card's receipts; the adaptations are declared in the report)
- `tools/monkey_campaign/contributions/MAT2-W10/DEV_RUN_REFUSALS.md` `5c88d0d1061dcee8466b5683dbaa771d8dbd6b357aa6297ae8957f85c3b0e6f2`
  (the record-accuracy lesson source; this card keeps its own ledger)
- `tools/monkey_campaign/contributions/MAT2-U01/reconcile/pinned_seam/tools/monkey_campaign/product/input_mapper.py` `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44`
- `tools/monkey_campaign/contributions/MAT2-U01/reconcile/pinned_seam/tools/monkey_campaign/product/input_mapper_tests.py` `95f44e90998f9728802ff5f7cb8628f18f2026bef1fb2c4de681e5253381216e`
- `tools/monkey_campaign/contributions/MAT2-U01/reconcile/pinned_seam/tools/science_funnel/typeb_export/command_record.py` `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e`
- `tools/monkey_campaign/visual_capture.py` `5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05`
- `tools/monkey_campaign/contributions/MAT2-M06/local_contact.py` `1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc`
  and `tools/monkey_campaign/contributions/MAT2-M06/contact_law.json` `583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b`
  (the shared contact law declarations; constants cited, never retuned)

Sealed lane machinery (`E:/ChimeraWork/pass3-integ/repo`; consumed read-only,
pinned bytes, the identical 15-file table W07/W08/W09/W10 verified — full
64-hex values live in `verify_inputs.py` PINS and are re-verified every run):
`tools/policy_compat/` `__init__.py`, `__main__.py`, `certificate.py`,
`engine_cert.py`, `injections.py`, `runner.py`, `scene_cpu.py`,
`snapshot_api.py`; `tools/science_funnel/typeb_export/` `infer_numpy.py`,
`observation_schema.py`, `policy_manifest.py`; validation
`typeb_p3_20260921/policy_manifest.json`, `typeb_p3_20260921/dummy_actor.npz`,
`typeb_p3_20260921/trace_slice_wave38.json`,
`upgrade_gate_20260920/receipt.json`. PLUS W10's added lane pins carried:
`tools/creature_graph/data/authored/project_program.json`
`3e5182f5a8bd85995f3dd0dac1ae24a27cdc0a9539e4da9ec0aef17018b1555c` and
`tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json`
`013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd1514017a173`
(the declared skeleton geometry fallback for the visualization pose law).

Registry: criteria hash and the `walking`/`motion` profile read READ-ONLY at
run time (G7). A missing required profile key = refusal
`registry_profile_missing_key`.

## 2. The frozen protocol (order is law)

1. Verify every section-1 pin; re-read the registry READ-ONLY and require the
   criteria hash and the profile identity. Any drift is a named refusal
   BEFORE anything runs.
2. Pin-extract the machinery tree, the base-blob seam tree and the F02/F07
   terrain/route authority files under a slot-scratch directory and import
   ONLY pinned bytes (zero upstream files modified; the NO_WORKTREES
   source-access declaration).
3. Re-validate the pinned W04 certificate (machinery validator; the only
   authority): zero violations, else refusal `certificate_validator_violation`.
4. Build the deployment request from the certificate's OWN relation;
   `check_deploy` must return ALLOW for the frozen line BEFORE any load, else
   refusal `deploy_gate_sanity`; load the bundle through the FROZEN loader
   and require bit-for-bit identity, else refusal `load_identity_mismatch`;
   verify build N identity (params sha, scene module sha, timestep 1/300 s),
   else refusal `build_identity_mismatch`.
5. Load the pinned terrain surface: `terrain_query.TerrainSurface(bundle)`
   with its own validator ON (a bundle that fails validation is refusal
   `f06_terrain_bundle_invalid`), and the pinned F07 module: re-run
   `build_mask` + `verify_routes` from the pinned obstacle declaration and
   require the sealed route metrics to reproduce EXACTLY (P2), else refusal
   `f07_route_replay_drift`.
6. Re-derive the declared case geometry (section 4) from the pinned bytes at
   run time: route polylines, leg bearings/tick counts, the approach ring,
   the step-over crossing. Every derived number is re-derived live; the
   freeze-time values quoted in sections 4-5 are the pinned-constant
   evaluations recorded at freeze.
7. Execute the arms (section 4) — every arm a full re-execution from tick 0
   through the pinned port seam and the frozen adapter, with the extension's
   declared channels recorded per tick. The W09 supervisor rides the clean
   arms in its sealed OBSERVATION role (emits nothing on the certified line;
   the declared responses stay R-probe-only, W10 heritage).
8. Evaluate the frozen predictions (section 5) and the falsifier detectors
   (section 6); emit the receipts. Any failed prediction is a named refusal
   (`prediction_failed:<name>`), never a silent pass. Honest negative
   verdicts that are themSELVES frozen predictions (the crest stall A2, the
   step-over envelope A3) are evaluated as predictions about the negative,
   recorded with MEASURED beside nominal.
9. Render the visualization (section 7) from the arms' OWN recorded records
   inside the pinned clearing build; the render path is records-only.
10. Emit receipts, run the named checks, run the 12 card-kit gates through
    the runner, generate the report from the receipts (zero hand-transcribed
    numbers), lint, and stop at the publication handoff.

## 3. The declared terrain-aware extension (THE LAWS; every constant pinned or derived, none tuned)

The extension is THIS card's own module. It wraps — never modifies — the
pinned scene: per tick it reads the scene's observation record, advances its
own declared state, and hands the scene the adapter's applied vector exactly
as W10 did. The certified channels (v, x, phase_l/r, warm, contacts, trips,
draws, micro, pad gaps) remain the pinned scene's own outputs.

- E1 HEADING: `psi(t+1) = psi(t) + dt * yaw_rate(t)`, yaw_rate the pinned
  record's own channel (W08 P5: tracks the command within 1e-6 rad/s).
  Convention: forward = `(cos psi, sin psi)` in clearing (x, z); psi=0 = east
  (+x); positive psi = north (+z). Heading is an EXACT integral of the
  command stream (no plant) — closed form, and cross-track drift is
  exactly zero on constant heading (P5 heritage: "the lateral coordinate is
  constant exactly").
- E2 POSITION: arc-length integration of the record's `com_v_m_s` along the
  heading: `px(t+1) = px(t) + dt * v(t) * cos psi(t)`;
  `pz(t+1) = pz(t) + dt * v(t) * sin psi(t)`. On flat ground with psi=0 this
  is the certified `com_x` advance identically (P1).
- E3 TERRAIN SLOPE DRIVE TERM (the declared terrain-aware scene subclass):
  the extension implements a DECLARED SUBCLASS of the pinned scene's step:
  after the pinned scene's own update `v_scene(t+1) = v(t) + dt*(a -
  d_eff*v(t))`, the subclass applies the additive declared grade term
  `v(t+1) = v_scene(t+1) - dt * g * grade(t)`. This is EXACTLY the declared
  terrain drive law `v(t+1) = v(t) + dt*(a - d_eff*v(t) - g*grade(t))`
  (both parts explicit in v(t); no reordering). The scene's own update law,
  constants and every other channel are the pinned bytes' own outputs; the
  subclass is THIS card's module (sha recorded in every receipt). On the
  certified flat line grade == 0 so the term is exactly 0.0 and P1's
  bit-identity holds; on graded ground the term is the physics that slows
  and stalls the walk (P4/P5). The upstream fixed-point law
  `v* = (a - g*grade)/d_eff` (pinned constants) is the derived prediction
  form for every slope claim.
  - `g = 9.80665 m/s^2` (pinned: `trunk_declaration.json`
    `derivation.gravity_m_s2`; gait_scene assembly gravity heritage).
  - `grade(t) = gradient_at(px, pz) . forward` — the pinned bundle's
    piecewise-constant per-triangle gradient dotted with the heading.
    Declared restriction: the grade term uses the TERRAIN (bundle) gradient
    only; obstacle faces are CONTACT surfaces (E5/E6), not grade.
  - Declared envelope consistency: the F05 declared bound 0.05 m/m keeps the
    linear grade law's cos error below 0.125 %; the F07
    `terrain_slope_rule` refuses cells with measured slope > 0.05 (refusal
    `f06_slope_rule_exceeded`; declared, never an invisible stop).
- E4 SUPPORT HEIGHT: `s(t) = H(px(t), pz(t))` — the COMPOSITE declared
  surface height: the pinned bundle height PLUS the declared obstacle top
  profiles of E5. The body's rendered base height in the visualization is
  the recorded `s(t)` plus the declared clearance band (the P06-declared
  band W10 used; no vertical body dynamics exist — W10 honesty carried).
- E5 OBSTACLE TOP PROFILES (the step-over surface class): declared logs are
  capsule SDFs from the pinned declaration rows:
  `H_log(p) = terrain_height_at_site + sqrt(max(0, r^2 - d_perp(p)^2))`
  with `d_perp` the perpendicular distance to the capsule axis segment
  (yaw_index 0 rows: axis = x through `centre_m`), `r = log_radius_m`.
  Rocks and stands are DECLARED contact_stop solids WITHOUT top profiles
  (F07's own declared behavior; their ascent is not modeled anywhere —
  honest limitation, section 9).
- E6 CONTACT/STOP LAWS (all from pinned declarations):
  - TRUNK: the body's declared contact envelope (radius = F07's
    `BLOCK_INFLATION_M` = 0.25 m, the declared spawn body_radius_envelope_m)
    may not enter the trunk solid: the body centre stops at axis distance
    `R + 0.25 = 0.287 m` (EXACTLY the F07 mask's own trunk blocking ring —
    `TRUNK_RADIUS_M + BLOCK_INFLATION_M`). Contact_stop semantics: the
    position ceases to advance into the ring; the stop tick, the pre-stop
    position and the held distance are receipted (declared, never hidden;
    FB4 proves continuity enforcement).
  - ROCKS/STANDS: the same contact_stop at their pinned footprints inflated
    by 0.25 m (the mask's own `inside_footprint` law).
  - STEP-OVER ENVELOPE: `D_step = ground_clearance + lift_gain * lift_hi
    = 0.008 + 0.06 * 1.8 = 0.11599999999999999 m` (derived from pinned
    scene constants; the maximum support step a swing pad's apex can
    mount). Detector: if any declared support point's composite ground
    exceeds the body's current support height by more than D_step, the
    declared contact_stop fires and the case ends with refusal
    `f06_step_over_envelope_exceeded` carrying the measured spread, tick
    and position. Declared support points: the four front pads at
    `+0.257 m` along forward (the pinned forelimb chain 0.125 + 0.132,
    trunk declaration derivation) and the two hind pads at the contract's
    own contact points `-0.012 m` and `+0.074 m` (heel/mp, pinned); all
    inline (zero lateral offset — the surrogate is inline; declared, no
    lateral stance width exists in any pinned lane).
- E7 EXTENSION CHANNELS (per-tick receipt record): `px, pz, psi, s, grade,
  support_ground` (the 6 support-point heights), `support_spread
  (max-min)`, `stop_state (none|trunk|obstacle:<id>|step_over)`, plus the
  scene's own record verbatim. The extension's state is part of the arm's
  state chain (the per-tick hash input), declared order.

## 4. The declared walk cases (arms; full re-executions from tick 0)

Common form: the pinned `InputMapper` over the injected clock, the frozen
W08 `CommandAdapter`, the certified scene build N at seed 20260920, the
sealed W09 supervisor in observation role. THE SCRIPT DERIVATION LAW: every
case's event table is DERIVED at run time (protocol step 6) by replaying the
declared case plan through the pinned scene recursion + the sealed adapter +
the extension's declared laws — a deterministic function of pinned bytes
only (the W08 `derived_bounds` pattern). The derivation produces each leg's
tick count (targeting the declared geometric waypoint along the declared
bearing, including the sealed measured start-rise inside leg 1: the sealed
W08 receipt's own `onset_tick` 301 / `band_entry_tick_measured` 3175 are
the pinned rise anchors) and the predicted per-tick arc table. The arm
executes the derived script; the receipts compare the arm's measured arc
table against the derivation's predicted arc table (float-identity window
1e-9; any drift = refusal `f06_script_drift`). Because the derivation and
the arm are the same deterministic pinned recursion, the open-loop landing
claims are EQUALITY claims, and the falsifiable content lives in the
closed-form bounds (P4-P7) and the falsifier arms (section 6) — the
house pattern (W08 P9 zero-control, W10 P11 identity), not a substitute
for them. Declared leg structures (waypoints in clearing coordinates;
bearings exact; turn instants at the derived ticks):
- A0: the W08 frozen input script verbatim (its own event table; no
  derivation beyond the seam).
- A1 (D_rock_01): east-prime rise inside leg 1, west to (17.5, 0) —
  walked as bearing pi (west) for 17.5 m — then bearing -pi/2 (south)
  for 9.0 m. (Spawn-region ground: pinned height 0.0, slope 0.0.)
- A2 (crest): east 19.5 m, north 6.0 m (bearings 0, +pi/2).
- A3 (step-over): east 5.0 m, then bearing -pi/2 (south) across the
  capsule footprint (the declared step-over stop fires inside the leg).
- A4 (approach): east 10.5 m, then ONE declared turn to the bearing
  `beta = atan2(2.471766, 1.476783) = 1.0322460640521718 rad` — the exact
  bearing from the declared turn point (10.5, 0) to the trunk axis base
  (11.976783, 2.471766); diagonal distance 2.8793254744549115 m; ceiling
  hold until the E6 trunk contact stop, then the declared hold.
- Horizon caps (declared, with early exits): A1 15000 ticks; A2 16000;
  A3 9000; A4 9000. Early exits: the declared stall (A2), the declared
  step-over stop (A3), the trunk contact stop + 600 declared hold ticks
  (A4). An arm that reaches its cap without its declared terminal is
  refusal `f06_case_terminal_missing`.

- A0 FLAT REGRESSION (the agreement anchor; horizon 10500 = W08's sealed
  HORIZON): the W08 frozen input script verbatim at this card's pins on the
  bundle's flat spawn region (measured height 0.0, slope 0.0 — declared
  probes in the receipt). THE CERTIFIED LINE: the pinned scene alone.
  THE EXTENSION LINE: the same script through the extension wrapper.
  P1: the two state chains (certified channels + extension channels) are
  BIT-IDENTICAL, the extension's (px, pz) advance equals the certified
  `com_x` exactly (`psi=0`, grade 0), and the certified line's own
  `v_at_segment_end` (tick 5415) reproduces the sealed W08 receipt's
  measured `0.7457698018962889` exactly. This is the certified
  runtime/training agreement proof at the wrapper boundary.
- A1 UNEVEN-GROUND ROUTE (D_rock_01; the measured route slope class): the
  sealed route to rock_01's viewpoint: 35 hops west (17.5 m) then 18 hops
  south (9.0 m), 53 hops, 26.5 m, min footprint clearance 0.300054 m,
  max sampled slope 0.026054 (sealed F07 receipt values; P2 re-derives
  them from pinned bytes). The walked bearing sequence is the pinned
  polyline's (west then south); leg 1 carries the start-rise inside its
  derived ticks. The corridor's derived grade envelope peaks in m1's
  flank; the predicted speed floor is the uphill fixed-point bound (P4).
- A2 CREST ATTEMPT (the honest-negative slope case): the sealed route
  toward mound m3's crest neighbourhood (39 hops east 19.5 m, 12 hops
  north 6.0 m, 51 hops, 25.5 m; the nearest reachable mask cell to the
  crest centre (19.265584, 6.057064) is (19.5, 6.0) at 0.241262 m — the
  crest cell itself is mask-blocked, disclosed). The corridor's derived
  grade profile crosses the derived stall grade for one sustained 2.0 m
  stretch (sampled grades 0.033381, 0.035335, 0.031843, 0.033347), 2.5 m
  into the north leg. P5 freezes the stall prediction and its derived
  bounds. The arm ends at the declared stall marker: first tick with
  `v <= 0` while the command demands forward (refusal `f06_slope_stall`
  — the honest negative marker; the receipt records the stall tick,
  position, and the local measured grade).
- A3 STEP-OVER CASE (`x_step_over_case`; log_02, the smallest declared
  obstacle): the sealed D_log_02 route (10 hops east, 5.0 m, flat) to the
  capsule axis line at (5.0, 0.0), then a declared south turn and a
  ceiling hold across the capsule footprint (perpendicular crossing at
  x = 5.0, inside the capsule span [3.844404, 5.91447]). P6 freezes the
  step-over envelope prediction (the declared negative and its exact
  requirement band). The arm ends at the declared step-over stop.
- A4 APPROACH CASE (the climb-derivation gap-10 bridge): east 10.5 m on
  z = 0 (the spawn-region flat line), then the ONE declared turn to
  `beta = 1.0322460640521718 rad` and the ceiling hold to the ring. The
  declared catch bound: a residual along-track error `delta1` at the
  turn point leaves the walked line at perpendicular distance
  `|0.8584531418657813 * delta1|` from the axis (the direction cosine is
  the declared bearing's own); the derivation-vs-execution identity
  window puts `delta1` at float-identity scale, and even the declared
  conservative band `|delta1| <= 0.1365 m` (the sealed W08 measured
  ceiling spread ratio 1.0254487372612255 over 10.5 m) gives a maximum
  miss `0.11717885386467919 m < 0.287 m` — the ring is caught with
  margin 0.16982114613532081 m. The terminal receipt IS the declared
  approach-to-grasp terminal geometry (P7): standoff ring 0.287 m (exact,
  the E6 clamp), the walked heading == the declared bearing `beta`
  within the turn law's 1e-6 rad/s tracking, the bearing-to-trunk at the
  stop recorded beside it, speed in the velocity envelope, support
  contacts >= 4, every certified pad gap > 0, trunk penetration 0, no
  snap (FB4).
  This card declares the terminal GEOMETRY only; the attach/facing
  precondition is K06's and is NOT claimed here (U05's frozen walk contract
  unchanged; no climb intent is emitted).

## 5. Frozen predictions (registered BEFORE any run; disclosed either way)

All bounds re-derived live from the pinned constants at run time; the
values quoted here are the pinned-constant evaluations recorded at freeze.

- P1_flat_regression_bit_identity (A0): the certified-line state chain and
  the extension-line state chain are bit-identical over the whole 10500-tick
  horizon; the extension (px, pz) equals (com_x, 0) exactly; grade == 0.0
  at every tick; s == 0.0 at every tick (the flat spawn region's pinned
  height). Any divergence = refusal `prediction_failed:P1` (the wrapper is
  not identity and the runtime/training agreement claim fails).
- P2_f07_route_replay_exact (protocol step 5): the pinned F07 module
  re-derives the mask (6198 reachable / 363 blocked, 0 unattributed) and
  the sealed route metrics EXACTLY: D_rock_01 (53 hops, 26.5 m,
  0.300054 m, 0.026054), D_trunk (25 hops, 12.5 m, 0.280824 m, 0.0),
  D_log_02 (10 hops, 5.0 m, 0.280824 m, 0.0), D-crest route (51 hops,
  25.5 m, 0.280824 m, 0.035335). Any drift = refusal
  `f07_route_replay_drift`.
- P3_command_seam_laws (every arm): W08's sealed seam laws re-executed
  (record_version 1; v_forward in [0, 0.763625]; |yaw_rate| <= 1.6; the
  15-tick interval law on held keys; idle emits nothing; sink = only
  emit(CommandRecord)).
- P4_route_slope_floor (A1): the walked path is the pinned polyline
  (cross-track exactly 0; along-track per the script derivation identity),
  and the corridor's derived grade envelope at 1 cm sampling is
  `max |grade| = 0.026054` (equal to the sealed route max; no corridor
  sample exceeds it). At every tick, with grade(t) <= 0.026054 and
  `a_ceiling = 0.763625 * 0.35 = 0.26726875 m/s^2`, `d_hi = 0.3675 1/s`:
  `v(t) >= (a_ceiling - g * 0.026054) / d_hi = 0.03201711809523818 m/s`
  (the uphill fixed-point invariant; the recursion never crosses its
  fixed point from above). MEASURED beside: the per-tick minimum speed,
  the grade profile along the walked path, the terminal arc inside the
  derivation's predicted arc (identity window 1e-9), and the measured min
  footprint clearance >= 0.25 m on the walked path. Zero
  `f06_slope_rule_exceeded` events.
- P5_crest_stall_MUST_FIRE (A2; the honest negative is the prediction):
  the walked corridor's derived grade profile (1 cm sampling) contains
  EXACTLY ONE sustained over-stall stretch: 2.0 m at sampled grades
  0.033381 -> 0.035335 -> 0.031843 -> 0.033347 (all above gamma_stall
  `= 0.26726875 / 9.80665 = 0.027253827759734468`), entered at ~24.0 m of
  the 25.5 m route. Rigorous stall bound (worst case: entry speed at the
  ceiling-band top 0.8038157894736843 m/s, weakest damping
  d_lo = 0.33249999999999996): the declared law's fixed point in the
  stretch is `v* = (a - g*0.033381)/d_lo = -0.1807128831578948 m/s` (using
  the stretch's LOWEST sampled grade for the weakest deceleration;
  `g*0.033381 - a_ceiling = 0.06008703365000001 m/s^2`), and the speed
  reaches 0 after `1.496636 m` of travel (the discrete-tick recursion
  bound at dt = 1/300; the continuous form gives 1.496125 m) — INSIDE the
  2.0 m stretch. P5: the arm stalls (v <= 0 under forward command) before
  leaving the over-stall stretch, i.e. before the saddle at the stretch's
  end. MEASURED beside: the stall tick, the stall position, the local
  grade at the stall (must be >= gamma_stall), the distance travelled
  into the stretch (bound: <= 1.496636 m), and x_max_qualified_slope's
  measured band: traversed
  with positive progress on A1 up to its corridor max 0.026054, stalled
  below the crest (the crest grade 0.03795552514626025 has drive margin
  `0.26726875 - 9.80665*0.03795552514626025 = -0.10494780067557308`).
- P6_step_over_envelope (A3; the declared negative is the prediction):
  the E6 step-over detector fires (`f06_step_over_envelope_exceeded`)
  with the measured support spread at the firing tick inside the derived
  band `(0.11599999999999999, 0.117275]` m — the envelope D_step plus at
  most one tick's ceiling advance along the capsule dome
  (the dome slope at the firing point
  `sqrt(0.128476^2 - 0.116^2)/0.116 = 0.4761` times
  `0.8038157894736843/300 = 0.001275 m`); the full log_02 top
  `0.128476 m` above the flat approach is the required mount height, the
  deficit
  `0.128476 - 0.11599999999999999 = 0.012476000000000015 m`, and the
  requirement band: a passing step-over of log_02 needs
  `lift_command >= (0.128476 - 0.008)/0.06 = 2.0079333333333333` —
  OUTSIDE the certified action bounds_hi 1.8 (log_01:
  `0.141408 m`, deficit `0.025408000000000014 m`, required
  `2.223466666666667`; rocks 0.374513-0.557057 m; stands 1.6 m — every
  declared obstacle is outside the certified envelope). The envelope table
  for all 7 obstacles is receipted. x_step_over_case is delivered as the
  EXECUTED case with its measured verdict; a PASSING step-over of any
  declared obstacle is outside the certified command envelope and needs a
  new approved runbook (the observation clause) — declared, not claimed.
- P7_approach_terminal_geometry (A4; the gap-10 bridge): the terminal
  receipt at the declared hold records: axis distance == 0.287 m exactly
  (the E6 clamp; the pre-stop tick's distance in [0.287, 0.287 +
  0.009924812030075191] — one tick's advance at the velocity envelope
  2.977443609022557 m/s); walked heading == the declared segment bearing
  within 1e-6 rad/s tracking (plus the exact closed-form integral of the
  whole script's yaw commands); speed within the velocity envelope;
  contact_count >= 4 at every tick; every certified pad gap > 0 at every
  tick; trunk penetration events 0 (no tick with axis distance < 0.287);
  stop_state transitions declared (approach -> trunk at the stop tick).
  The declared terminal geometry block (for K06's consumption): ring
  radius 0.287 m (pinned R 0.037 + declared body envelope 0.25), inside
  the sealed 0.5 m reach envelope (0.287 < 0.5 — the grasp reach class
  can be evaluated at this terminal; declared, not claimed).
- P8_stability_bars (every tick of every clean arm; W10 P8 heritage):
  |v| <= 2.977443609022557 m/s; contact_count >= 2 (observed floor 4
  recorded); no NaN/Inf in any channel; intervention_reason == "none";
  every certified pad gap > 0; x never decreases; com_x advances exactly
  by dt*v per tick; extension channels finite; the extension position
  never leaves the declared extent (|px| <= 19.75 and |pz| <= 19.75) and
  never enters a blocked footprint (the E6 laws hold). On A1 the
  position-corridor claim: the walked path stays inside the derived
  along-track band around the pinned polyline (cross-track exactly 0).
- P9_no_sliding_no_penetration_terrain (A1/A3/A4; W10 P11 heritage): the
  arc-length identity — the extension's travelled distance advances
  exactly by dt*v per tick (window 1e-9); the support-point ground
  heights satisfy the E6 step law at every tick (no support point above
  s + D_step without the declared stop having fired); no certified pad
  gap <= 0.
- P10_command_response (A0; W08/W10 P9 heritage re-executed at this
  card's pins): the wrong-command divergence at the declared inject tick
  with the physical separation beyond the derived brackets; R-arms'
  bit-identity zero-controls hold (A0's two lines are the R1/R2
  equivalent; the wrong-command arm runs on the extension line).

## 6. Falsifier arms (G1: clean control FIRST, named guard, receipt row; every arm can fail)

| arm | clean control | tampered | detector | discriminator |
|---|---|---|---|---|
| FB1_terrain_decouple | A1's height/grade channels match the pinned surface at the recorded positions (worst residual 0) | 6 bundle vertices within 0.5 m of the A1 path lifted by 0.01 m in a scratch bundle copy (F05 FB6 heritage) | height/grade residual fires at the lifted cells | render/query decouple class |
| FB2_slope_term_mute | A1's measured speed floor >= the P4 bound under the declared law | the grade channel forced to 0 on the m1 flank stretch in a scratch run (the declared law muted) | the muted run's speed exceeds the declared law's fixed-point bound on the flank (>= the bound + the derived separation) | unsupported-propulsion-on-slope class: motion beyond the declared terrain law |
| FB3_step_envelope_discriminates | A3 fires on the pinned log (P6) | a scratch log copy with r = 0.10 m (< D_step) — the declared crossing must CROSS without the stop | the stop does NOT fire on the lowered log (and the crossing receipt shows the mounted top at 0.10) | the envelope detector discriminates (not a always-fire tripwire) |
| FB4_trunk_snap | A4's walked terminal path (arc-length continuity) | the body position set to the ring terminal at a declared tick (a hidden snap) | the arc-length identity residual fires (jump without velocity) | teleportation/hidden-support class |
| FB5_sliding | P9's exact arc-length identity on A1 | the extension position advanced by 2x dt*v at one declared tick (W10 FB4 heritage, record-level, declared) | the identity residual fires | the sliding class |
| FB6_hidden_reset | A1's detectors green (W09's battery: draw chain, phase recursion, velocity identity) | tick-60 snapshot restored at tick 100 inside A1's produced window (W09 FB1 form) | the fresh-seed draw chain breaks at the restore tick | the concealed-reset class |

Guard naming: `f06_fb<n>_premature`. A non-biting arm, or an arm that
fires on its clean control, fails the whole build.

## 7. Capture plan (profile check BEFORE capture; G7/G8/G4)

- The registry profile is read READ-ONLY (`file:...?mode=ro`) BEFORE any
  capture; required keys asserted; `CANONICAL_LAYERS` tripwire present;
  `task_id` SHORT form (`F06`) in manifest AND context; the registry
  profile snapshot + provenance written to evidence; `criteria_sha256`
  identical across dispatch / registry / prereg / checks identity.
- Views (profile verbatim, each x diagnostic/clean): full-body ground
  overview; side view of stance/swing (bookends sample one declared stance
  tick and one declared swing tick of A1, keyed per phase, G6); close-up
  of foot-ground contact (A3's step-over stop and A4's trunk terminal are
  the declared close-up subjects). `state_or_tick_interval` carries the
  real tick axis; one tick = 1/300 s.
- Camera record: ALL 17 registry fields per view (the F04/W10
  camera-manifest schema); `visibility_layers` and `label_ids` name the
  diagnostic layers actually drawn (skeleton; foot contacts and normals;
  support/COM markers; command and tick overlay; stable 3D labels — the
  terrain arms add the declared terrain support markers to the support
  layer, disclosed); `occlusion_or_xray_mode` recorded.
- The rendered base height is the recorded `s(t)`; the diagnostic frames
  carry the terrain support points and the recorded grade at the body.
  Every frame records the state hash of the run record at its tick; each
  diagnostic/clean view pair is state-hash IDENTICAL (G8).
- Codec: FFV1 `-level 3 -g 1 -fflags +bitexact` mkv (the codec standard);
  the ffmpeg version string recorded; frames are the determinism unit;
  decode == committed stills at independently recomputable indices under
  identity ONLY (G4); ONE gate-bound capture identity per arm (G8).

## 8. Named checks, gates and refusal codes

- Suite: `test_f06_terrain_walking.py` (unittest; zero skips by design;
  KNOWN_SKIPS: none). Receipt-semantics changes land TOGETHER with the
  named check that asserts them.
- The 12 card-kit gates run through the runner on the card directory
  (py_compile, ast checks, receipt schema, named-check suite, prereg
  exists, gitattributes text flag, CRLF byte stability, job-JSON
  forward-slash, G10 pin-vs-disk, G11 agent trailer, G12 skip accounting);
  red gates block submission.
- Refusal codes (frozen): `criteria_pin_mismatch`, `input_pin_missing`,
  `input_pin_mismatch`, `certificate_validator_violation`,
  `deploy_gate_sanity`, `load_identity_mismatch`,
  `build_identity_mismatch`, `port_record_version`, `port_v_out_of_band`,
  `port_yaw_out_of_band`, `prediction_failed:<name>`,
  `f06_terrain_bundle_invalid`, `f07_route_replay_drift`,
  `f06_script_drift`, `f06_slope_rule_exceeded`, `f06_slope_stall`,
  `f06_step_over_envelope_exceeded`, `f06_trunk_penetration`,
  `f06_case_terminal_missing`, `f06_extent_violation`,
  `f06_fb<n>_premature`, `registry_profile_missing_key`,
  `profile_read_failure`, `capture_codec_violation`,
  `vacuous_comparison:<name>`.
- The report is GENERATED from the bound receipts (zero hand-transcribed
  numbers; `lint_report_numbers.py` exits 0 with the selftest proving the
  detectors); receipts report MEASURED values BESIDE nominals with
  deviation flags; no format placeholders. Every refusal that fires in
  development is recorded verbatim in `DEV_RUN_REFUSALS.md` (the W08/W10
  record-accuracy law).

## 9. Honest limitations and absent inventory (declared, never imputed)

- The certified execution vehicle is the DECLARED SURROGATE scene; the
  product engine has no live control path for the certified policy (W07
  N1/N2/N3 carried). Real-time 300 Hz interactive execution is NOT claimed
  (TC-11 COST-GAP); the claim class is offline/trace qualification at the
  300 Hz tick.
- NO TRAINING runs on this card and NO training objective is expanded (the
  observation clause): the W06 sealed record stands (three seeds DEGRADED
  on the FLAT certified line); flat-ground training transfer to ANY
  nonzero slope remains unevidenced (F05); the trained bundle stays
  BLOCKED at the pinned deploy gate. The terrain laws of section 3 are the
  declared scene definition for runtime; a future training runbook against
  them requires its own approval.
- The declared negatives (frozen as predictions, disclosed either way):
  the crest case A2 is predicted to STALL (the walker cannot sustain the
  m3 flank grades); the step-over case A3 is predicted to be STOPPED by
  the step-over envelope (no declared obstacle is step-over-able within
  the certified command envelope). If these predictions fail, the
  measured result replaces them and the F05 named-absent variables take
  the measured values — either way they are resolved by measurement, not
  assertion.
- x_slope_gait_qualification: the authored 10/20/30 deg walk classes
  (grades 0.17632698070846498 / 0.36397023426620234 / 0.5773502691896257)
  are ALL far above the derived stall grade 0.027253827759734468 — none
  is walker-qualified at the certified envelope; the honest verdict and
  its numbers are receipted (thresholds are authored for a reference
  earth-contract biped; F05 TERRAIN_REPORT 8.6 heritage).
- The surrogate has NO vertical body dynamics (W10 heritage): support
  height s(t) is kinematic; the step-over envelope is a swing-apex
  envelope, not a vertical-dynamics result; no impact/landing accounting
  exists beyond W09's sealed records.
- The declared scene has ONE climbable trunk; "between trees" is walked
  as between the declared obstacle footprints and the trunk under the
  declared clearance rules; no second tree exists and none is invented.
- Rocks and stands are contact_stop solids without top profiles; their
  ascent is unmodeled. The trunk is never added to a dynamic solve with
  the ground (F04's measured both-pinned refusal heritage); the approach
  stop is the declared analytic ring.
- The approach terminal declares GEOMETRY only; the attach/facing
  precondition, climb intent and skill arbitration are K-lane work (U05's
  frozen walk contract unchanged).
- This text-only worker will inspect no pictures: pixel claims stay
  MEASURED decode checks and image review is owned by the Sergeant/
  Lieutenant.
