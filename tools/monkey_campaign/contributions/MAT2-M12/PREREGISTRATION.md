# MAT2-M12 PREREGISTRATION — qualify mechanical detail and render detail independently

Attempt 22954da7b9704483960b563273e77b4a, arrival arrival-glm53f-m12-w1,
criteria sha256
1e98a4f4465d4a50f21ce5c1d42b5ab51e9a7f96482f8f711d2c66ca4c53b5b7 (identical
across dispatch, registry card + attempt, this file, and the named-check
identity). Attempt branch branch-4 starts at the sealed line tip
eeae6540 (merge of PR #279, the MAT2-M11 winner), which carries the whole
M-tier law stack M01-M11 UNMODIFIED.

Composed against CARD_STARTER.md **v2** (2026-09-30, evidence-anchoring +
GPU-banking additions), house-standards/IMPLEMENTER_CHECKLIST.md (G1-G9) and
TOOLKIT.md (P1-P9), card-kit/ templates (generator trio + batch_gates
**12 gates** -- G10 pin-vs-disk, G11 agent-trailer, G12 skip-accounting are
LIVE for this card), format-spec/FORMAT_SPEC.md,
codec-benchmark/CODEC_STANDARD.md.

This file was frozen and committed BEFORE the implementation existed and
BEFORE any M12 experiment ran. Amendments are separate own commits on the
amendment chain (never squashed -- the M10/M11 lesson), each committed before
the receipts that cite it. Every window below is derived from declared
constants and pinned law inputs by the stated derivation (build-data
arithmetic recorded in section 3b); no window is tuned from an M12 dynamics
measurement. If a probe forces a window change, the amendment records the
triggering probe values and the derivation.

## 1. Frozen statement

ONE sealed rig (the M11 hanging bone-chain limb, `limb_world.py` imported
UNMODIFIED, sha-pinned in section 2) is exercised at TWO declared mechanical
resolutions that differ ONLY in builder data (tube ring/radial counts and the
declared belt-section remap below) -- there is NO resolution-conditional
dynamics code. The done_when (verbatim): "Compare at least two mechanical
resolutions while preserving declared mass/inertia, interfaces, force
response and control meaning within frozen tolerances; render mapping stays
attached under large motion. Select the least costly qualified detail for the
monkey and record frame-time/VRAM limits."

### The two resolutions (declared)

| id | rings x radials | vertices | triangles | edges | belt chords |
|---|---|---|---|---|---|
| `coarse` | 6 x 6 | 38 | 72 | 108 | 33 |
| `reference` | 12 x 12 | 146 | 288 | 432 | 150 |

The `reference` resolution IS the sealed M11 limb (TUBE_RINGS = TUBE_RADIALS
= 12); `coarse` is the least-costly candidate. Counts above are build-data
arithmetic from the pinned frame inputs (section 3b), recorded before any
dynamics run.

### Declared remapping rules (the LOD contract; the independence law)

Mechanical resolution changes ONLY through these declared rules; every other
law input is bitwise identical across resolutions:

1. MASS (declared invariant, bitwise): total declared tissue mass
   LIMB_TISSUE_MASS_KG = 2.0e-3 kg (M11 sealed) is split per vertex by the
   sealed module's own rule `vertex_mass = tissue_total / n_vertices`
   (limb_world.py line 724) -- the total is resolution-invariant BY
   CONSTRUCTION; the per-vertex split is derived, recorded, and never
   re-declared. Bone/foot/load masses are untouched (bitwise).
2. BELT SECTION (declared invariant): the sealed chord law gives each chord
   k = E_FIBER * A_CHORD / l0 with per-chord section A_CHORD = T_WALL^2 =
   9.0e-6 m^2 at 150 chords (the sealed 12x12 build). The declared invariant
   is the belt's total chord section A_CHORD_TOTAL = A_CHORD * 150 =
   1.35e-3 m^2; per-resolution chord section is the equal split
   A_CHORD(res) = A_CHORD_TOTAL / n_chords(res) (coarse: 4.090909090909091e-05
   m^2 over 33 chords -- the same equal-split rule as the mass inventory).
   The chord law FORM is the sealed module's; only the declared section
   constant differs, per this rule, before construction.
3. EDGE NETWORK: the sealed edge law k_edge = E_TRANS * T_WALL * a_dual / l0^2
   is already per-area (a_dual sums adjacent triangle areas): per-area
   stiffness is resolution-invariant by construction. Unchanged.
4. INTERFACES (bitwise-identical builder data): the chain spec (humerus ->
   ulna -> radius -> foot with real B03 masses, A06 tie-site records T1..T4,
   contact radii), the load surrogate (0.25 kg, K_TIE, rest 0.05 m), the
   clamp role (top pole + 1-ring pinned), the bottom-ring load introduction,
   the M05 ground law (K_CONTACT = 1.0e5) and the PASCAL schedule function
   are the same objects at both resolutions (interface digest gate Y3a).
5. ERECTION: the rig is erected at the declared chain statics plus a
   per-resolution offset compensating the scaffold's own compliance sag
   (M11 A2 pattern). The `reference` offset is the SEALED M11 value
   3.0312e-3 m (reused, not re-derived). The `coarse` offset is PROBE-DERIVED
   before the bank (probe: free-hang settle, offset := settled sag; values
   recorded in Amendment A1 with the triggering probe trail).

### What "mechanical detail and render detail qualify INDEPENDENTLY" means here

- A render-side change may not alter measured mechanics: the render pass is
  OFFLINE over recorded snapshots; the render layer can only READ world
  state. Gate Y7 + falsifier arms FB1/FB2 are the named checks (a render
  tamper can never write back -- the render module receives copies).
- A mechanical-side change may not alter the render mapping: the render mesh
  IS the mechanical membrane (vertex-for-vertex binding declared below);
  refinement remaps both together through the same builder, and the binding
  audit refuses any rendered vertex not bound to a live mechanical vertex.

## 2. Frozen input pins (verify_input_pins at every run; drift refuses)

| pin | sha256 |
|---|---|
| MAT2-M01/material_state.py | b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40 |
| MAT2-M03/pressure_membrane.py | 3dd64f6465430380f1c0a53a95523c700cd51a6b1115e60f0df8afde2239c96e |
| MAT2-M04/passive_response.py | 68a696e1728066a3dce93db7b6c98f8bb4826322a84bbad20eeadf38350e326b |
| MAT2-M05/interface_exchange.py | 295e6c898ada14918f09b2b0633f5926c1623c9e09cd37258e516ab57450b9b9 |
| MAT2-M11/limb_world.py | (recorded at first run; the sealed rig module sha is pinned and drift refuses) |
| MAT2-B03/material_volume_input.json | 6e8033f26c823f410eb5beb8fdaaefd4c0c37db61327a86221e087bc832b9ddc |
| MAT2-M02/monkey_arm_independent_meshes.json | 51d8231e0d1eacd7f0d4b558699f011e35ff765f5d0e07ef5889ded27216a834 |
| MAT2-B04/frame_forest.json | 156ef55722e1ecda3238f3733131eb707f209cb93531d0e133227b00ebba8203 |
| MAT2-A06/attachment_ownership.json | f1f0430772258e8449fc354841becf2f1869783399e63f3f145565b8d0b1041c |
| MAT2-B05/mechanical_port_requirements.json | ef69ee740262cc5783e763517e4d27e0306f31d059b8273bb125486ad7647f3d |

All law imports are UNMODIFIED upstream modules. The M12 module composes and
configures them (module-constant configuration declared in section 1); it
does not edit them.

## 3. Declared constants (authored; engineering, labeled)

All M11 sealed rig constants are carried UNMODIFIED (TUBE_RADIUS 0.012 m,
T_WALL 3.0e-3 m, E_FIBER 1.0e8 Pa, E_TRANS 1.0e6 Pa, XPBD_ITERS 8,
XPBD_RELAX 0.15, N_SUB 16, DT 1/300 s, damping c_v 2000 / c_load 4 /
c_foot 200 / c_bone 30, K_TIE 600, K_TIE_BONE 600, REST_GAP_CHAIN 0.01 m,
R_FOOT = R_BONE 5.0e-3 m, G_FOOT_TARGET_M 2.0e-4 m, K_CONTACT 1.0e5,
schedule level DP_WORK_PA 1000 Pa, source limits MAX_DELTA_P_PA 5000 Pa /
MAX_FLOW 1.0e-3 m3/s, surrogate load 0.25 kg, foot inertial mass 0.010 kg).
M12-declared additions:

- RESOLUTIONS = {coarse: (6, 6), reference: (12, 12)} (section 1 table).
- A_CHORD_TOTAL = 1.35e-3 m^2 (declared invariant, rule 2).
- Coarse erection offset: probe-derived (Amendment A1) -- the ONLY
  per-resolution constant not sealed today.
- COST LIMITS (the recorded frame-time/VRAM limits; declared from the
  campaign's real-time usage, not from any M12 measurement):
  - TICK_BUDGET_S = DT = 3.333e-3 s (300 Hz real-time: one tick of
    simulation must fit its own period),
  - FRAME_BUDGET_S = 1.0/60 = 1.667e-2 s (real-time render frame budget at
    the declared capture viewport),
  - VRAM payload bound (computed demand formula, DECLARED -- the lane is
    software-rendered and claims NO GPU allocation):
    vram_payload_bytes = n_vertices*3*8 (f64 positions)
                       + n_triangles*3*4 (u32 indices)
                       + W*H*3 (RGB8 framebuffer, 640x480 = 921600 B).
  - Peak process memory is MEASURED per run (ctypes
    GetProcessMemoryInfo peak_working_set) and recorded beside the formula.

## 3b. Build-data arithmetic (recorded BEFORE any dynamics run)

Derived from the pinned inputs at the line tip (no dynamics; build only):

- span (palm anchor -> humerus top) = 0.19206378038613958 m;
- W_chain = 0.5086442710637195 N; W_foot = 0.0980665 N;
  W(ulna)+W(radius) = 0.1898455088713045 N; W_chain_top_static =
  W_chain - W_foot = 0.41057777106371945 N; W_total = 2.9799200710637193 N
  (matches the sealed M11 A3 probe: bound-hold T1 0.4105 N);
- cap area fraction of the capsule surface = 2R / (span_cyl + 2R) with
  cylindrical band span - 2R = 0.16806378038613958 m: 0.12495849010026033;
- transverse inertia of the declared tissue about the erected axis at rest:
  I(coarse) = 2.7284210526315684e-07 kg m^2,
  I(reference) = 2.7880150785742027e-07 kg m^2 (rel diff 0.02138).

## 4. Schedule and runs (declared before any run)

The M11 PASCAL schedule at 1000 Pa is carried UNMODIFIED (P0 presettle
0-199, A_rampup 200-399, B_hold 400-1099, C_poweroff 1100-1299,
D_settled_off 1300-1499; TOTAL_TICKS 1500; RELEASE_TICK 450, RELEASE_TIE T2).
Per resolution r in {coarse, reference}, THREE full runs:

1. `loaded` -- the full schedule (the qualification run),
2. `off` -- never-pressurized (mode='off'; the activation-off control
   reference),
3. `released` -- T2 released at tick 450 (the connection-removal control).

SNAP_TICKS = (0, 450, 460, 700, 1100, 1350) (rest, release tick, +10 ticks
into the departure transient -- the largest-motion record, hold, power-off
end, settled). Windows: BASELINE_WINDOW (100,200), LOADED_WINDOW (1000,1100),
OFF_WINDOW (1400,1500), POST_RELEASE_WINDOW (550,650) -- all M11-sealed,
carried unmodified. Falsifier fixture runs (FB5/FB6) use the
DECLARED_FIXTURE_TICKS = 500 prefix (ramp + early hold) on the `coarse`
loaded schedule (FB5) and the `reference` loaded schedule (FB6); their
metrics are defined on pressurized ticks only, so the prefix discriminates.

## 5. Frozen windows (derived from declared constants; never from M12 runs)

Let k_c = K_CONTACT = 1.0e5 N/m, x_floor = 1.0e-7 m (integrator positional
identity floor), REL = 0.05 (ledger-class fractional allowance, M03/M10/M11
heritage). Error budget of every identity below: the contact-penalty term
k_c * x_floor = 1.0e-2 N plus the fractional allowance on the stated
statics scale.

- Y2c inertia agreement (declared mass/inertia preserved):
  |I(coarse) - I(reference)| / I(reference) <= I_LOD_REL = 0.10.
  Derivation: masses are bitwise invariant; I separates between resolutions
  only through cap-surface quadrature (every cylindrical-band surface point
  sits at distance R from the axis EXACTLY, so only the caps contribute);
  the cap mass fraction is 0.12496 (section 3b) and the cap r^2 values span
  [0, R^2], so the worst-case quadrature difference is the full cap term
  0.12496 of the band term. Window 0.10 covers the measured build-data
  difference 0.02138 with margin 4.7x while a declared-mass tamper (FB4)
  moves I by >= 1.7x and must bite.
- Y3b belt-section audit (declared strength preserved): for each
  resolution, sum_i A_CHORD(res) over i = 1..n_chords(res) equals
  A_CHORD_TOTAL bitwise (equality of decimals recorded, not compared by
  float accumulation); each chord k carries E_FIBER * A_CHORD(res) / l0
  bitwise (recomputed audit).
- Y4a per-resolution whole-system statics (both resolutions, every declared
  window): |F_clamp_z + sum(F_contacts) - W_total| <=
  REL * W_total + k_c * x_floor (bound 0.1590 N).
- Y4b per-resolution chain-top identity: |T1_hold - W_chain_top_static| <=
  REL * W_chain_top_static + k_c * x_floor (bound 0.03053 N).
- Y4c foot-gap sanity per resolution: at OFF the settled foot gap
  g_off(r) satisfies |g_off(r) - G_FOOT_TARGET_M| <= GAP_WINDOW_M = 1.0e-3
  (the M11 A2 recovery-window class; the erection targets exactly this
  gap), and the OFF-run foot contact is bitwise 0 (positive gap => no
  penalty engagement).
- Y5 cross-resolution force response (the comparison; frozen tolerances):
  - |T1_hold(coarse) - T1_hold(reference)| <= REL * W_chain_top_static
    + k_c * x_floor (bound 0.03053 N): the transmitted chain-top force is
    weight statics; resolution may not move it beyond the ledger-class
    allowance.
  - |contact_hold(coarse) - contact_hold(reference)| <= REL * W_foot
    + k_c * x_floor (bound 0.01490 N).
  - |g_off(coarse) - g_off(reference)| <= GAP_WINDOW_M = 1.0e-3 m.
  - Recovery: |g_off(loaded run) - g_off(dedicated off run)| <=
    RECOVERY_GAP_M = 1.0e-3 m per resolution (M11 A2 form).
- Y6 control meaning at BOTH resolutions (the same discriminators bite):
  - activation-off: OFF-window foot contact bitwise 0 AND hold contact
    > 0 at r; the p = 0 thrust identity is bitwise by law.
  - connection-removal: after the tick-450 T2 release,
    t1_drop := T1(bound hold) - T1(released settled) satisfies
    |t1_drop - W(ulna)+W(radius)| <= REL * W(ulna)+W(radius) + k_c * x_floor
    (bound 0.01948 N); released T2 tension bitwise 0; distal elements land
    within 1.0e-4 m of their own contact rest heights; the released
    trajectory departs the bound one by >= BITE_M = 1.0e-3 m within
    100 ticks; a double release refuses (release_of_unbound_bond).
- Y7 render mapping attached (the independence law, render side):
  the render mesh is bound vertex-for-vertex to the mechanical membrane;
  for EVERY rendered frame the binding audit asserts the rendered vertex
  array equals the mechanical snapshot bitwise (identity binding; the
  renderer receives copies). The audit runs over the `released` run's
  snapshots -- the largest-motion record (departure >= 1e-3 m by gate).
  Coverage: rendered vertex count == mechanical vertex count and rendered
  index set == mechanical triangle set (a dropped ring refuses;
  visible vertices can never be left behind).
- Y8 cost accounting and selection (the least-costly qualified detail):
  - measured per resolution: sim_seconds_per_tick (wall-clock around the
    tick loop of the `loaded` run, recorded with host load note; physics
    itself stays wall-clock-free and deterministic), render_seconds_per_frame
    (wall-clock around the capture frame renders), peak_process_bytes,
    vram_payload_bytes (declared formula, section 3).
  - declared limits: TICK_BUDGET_S, FRAME_BUDGET_S (section 3); each
    measured value records within_limit as a boolean beside it.
  - SELECTION RULE (declared): qualified(r) := every Y-gate green for r;
    selection := argmin over qualified of sim_seconds_per_tick (the
    dominant recurring cost; ties broken by vram_payload_bytes). The rule
    is frozen here; the OUTCOME is measured and derived by the report
    generator from receipts (zero hand-typed numbers).
- Ledger: per resolution, the settled-window cumulative no-source gate
  |sum R_settled| <= max(REL*|W_press| + REL*W_grav, X8_FLOOR_J = 2.0e-3 J)
  (M11 A2 form); the full-run residual is REPORTED, not gated.
- Determinism: two fresh `loaded` runs per resolution byte-identical on the
  scoped dynamic trace (M11 X7 form).

## 6. Falsifier arms (P1: clean control FIRST, named premature guard, receipt rows)

Every arm: clean control on the untampered fixture runs FIRST and must pass
its declared window; the arm carries guard `<short>_fb<n>_premature`; the
receipt row embeds clean_control {metric_scope, value, within_tolerance,
guard} beside the tampered value and bit. Fixtures preflighted on CPU to
discriminate BEFORE any further spend. Every arm must be able to FAIL.

- FB1 stale render / unbound media (card falsifier "overlay-driven motion"):
  the render layer publishes the REST geometry while the mechanics move
  (the released run's tick-460 snapshot is the reference motion). Clean:
  identity binding deviation bitwise 0 (window AUDIT_WINDOW_M = 1e-9 m).
  Bite: deviation >= BITE_M = 1e-3 m (the declared departure bite).
- FB2 dropped-ring render remap (card falsifier "leaves visible vertices
  behind" -- the task falsifier class): the render mesh omits the last
  ring's vertices. Clean: Y7 coverage passes (counts/index sets equal).
  Bite: render_vertex_coverage_refused fires.
- FB3 undeclared strength change (task falsifier "Triangle refinement
  changes material strength ... without declaration"): a coarse build whose
  chord section stays at the SEALED per-chord 9.0e-6 m^2 (i.e. the
  refinement remap silently skipped). Clean: Y3b belt audit exact.
  Bite: belt_section_audit_refused fires (A_total mismatch vs declaration).
- FB4 silent mass drift (task falsifier ".../mass without declaration"):
  the coarse per-vertex split computed with the REFERENCE vertex count
  (2.0e-3/146 per vertex over 38 vertices -- total mass drifts 3.84x).
  Clean: per-resolution totals bitwise equal to the declaration.
  Bite: assembly mass audit refuses (mass_total_mismatch:coarse_tissue).
- FB5 area-independent triangle forces (card falsifier): M11's
  constant_weighting tamper on the coarse fixture prefix. Clean: M03
  traction identity worst relative error <= 1e-9. Bite: >= 1e-6.
- FB6 unaccounted energy (card falsifier): M11's tie_boost x2.0 tamper on
  the reference fixture prefix. Clean: tie-law audit bitwise 0 (state-
  determined force law). Bite: law deviation >= 0.05 * W_chain_top_static.

## 7. Gate map (done_when clause -> named check)

| clause | gates |
|---|---|
| at least two mechanical resolutions | Y1a resolution registry (both configs built through the ONE configure_resolution path; AST audit: constant writes only in the declared config function), Y1b run-identity receipts (same sealed law sha + schedule id at every run), Y1c counts match the section-1 table |
| preserving declared mass/inertia | Y2a total masses bitwise across resolutions (tissue 2.0e-3, bones, foot, load), Y2b per-vertex split == total/n bitwise, Y2c inertia window, Y2d the Y3b belt audit (declared strength) |
| interfaces | Y3a interface digest equality on resolution-invariant fields (chain spec, tie sites, contact radii, load surrogate, ground law id, schedule id), Y3b belt-section audit |
| force response within frozen tolerances | Y4a/Y4b/Y4c per-resolution statics + Y5 cross-resolution windows |
| control meaning | Y6 activation-off + connection-removal discriminators at both resolutions (double-release refusal) |
| render mapping stays attached under large motion | Y7 binding + coverage audits over the released-run snapshots; FB1/FB2 arms |
| select the least costly qualified detail | Y8 selection rule applied to receipts (derived, disclosed outcome) |
| record frame-time/VRAM limits | Y8 cost table with declared limits + measured values + vram formula |
| ledger / determinism honesty | X8 settled cumulative gate per resolution; rerun+compare byte-identity per resolution |
| unbound media / capture | capture section (below) + validator refusals |

## 8. Capture plan (material/motion profile; frozen before execution)

- Registry verification profile read READ-ONLY from
  E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3 (mode=ro URI;
  kanban.cards.MAT2-M12.spec.ontology_qualification.task.verification_profile).
  Required keys asserted; CANONICAL_LAYERS tripwire present (loud, never
  value-supplying). task_id SHORT form "M12" in manifest AND context.
- Views (registry): whole experiment at fixed distance; orthogonal side and
  front; oblique close-up of the loaded interface. Diagnostic/clean pairs
  per view (clean_view_required = true): clean rows carry ZERO labels,
  layers, overlays. Frames: SNAP_TICKS x {coarse, reference} x
  {diagnostic, clean} = 24 sheet frames; ONE video.
- Diagnostic layers (registry, all five): stable membrane/triangle/port IDs;
  pressure and area-scaled force vectors; rest/current geometry and material
  directions; contact/bond state; energy/work and simulation tick.
  Per-layer pixel presence: each declared layer, rendered alone, >= 1 pixel
  of its layer color in the frame (probe receipt; zero presence fails).
- Codec: FFV1 -level 3 -g 1 -fflags +bitexact mkv via rawvideo pipe; ffmpeg
  version line recorded in the capture receipt; lossy fallback REMOVED
  (refuses, never falls back). Per-viewport offscreen renders + clipping;
  no cross-viewport leakage by construction; perspective depth sign
  conforms to the declared camera record (M10 F2 scar).
- Camera records: all 16 registry fields on every camera record (frame_id,
  coordinate_unit, position, orientation_convention_and_values, target,
  distance_to_target, projection, vertical_fov_or_orthographic_span,
  near_far_planes, aspect_ratio, viewport_resolution,
  camera_motion_or_bookmark_sequence, visibility_layers, label_ids,
  occlusion_or_xray_mode, state_or_tick_interval). Fixed bookmarks only.
- Camera-consistency gate (M10 permanent check): signed row-order check per
  perspective viewport, declared close-up content presence, zero tie-color
  leakage -- recomputed from the committed stills by the named check suite.
- Bindings (P8): ONE video artifact; disk sha256 == manifest == context ==
  determinism record; every view row carries the same state_binding.sha256
  as its source run's canonical trace (coarse rows bind the coarse trace,
  reference rows the reference trace) -- view toggles preserve the physical
  state hash. Committed stills BMP at declared frame indices; P4
  transform-list gate (identity 0 px; vflip/hflip/rot180 > 0) + stdlib
  row-order proof with sensitivity guard.
- State-hash uniformity law: the diagnostic/clean pair of a view row is
  rendered from the SAME snapshot; both rows carry the same
  state_or_tick_interval and the same state digest -- a view toggle may not
  change the physical state hash (named check asserts pair equality).
- Unbound media falsifier: a manifest bound to a WRONG trace sha must be
  refused by validate_manifest (named refusal recorded in the receipt).

## 9. Scope decision: CPU-only (declared)

No GPU submission is required by the done_when's physics: the mechanical
comparison, the render-mapping audit and the falsifier arms are all
CPU-measurable on the sealed M11 numpy stack (the M11 precedent: CPU-only
declared in prereg scope, sealed at review). Frame-time and VRAM limits are
RECORDED per section 3/5-Y8: render wall-clock is measured from the offline
render pass; the VRAM entry is the DECLARED payload formula plus the
measured peak process memory, with the honest disclosure that this lane
allocates no GPU surface (a GPU residency claim is refused). CPU-FIRST is
thereby satisfied: the full-trajectory CPU run with ALL gates armed is the
only physics run. Should any gate force GPU work, an amendment records the
reason BEFORE the first GPU job and the gpu-queue PROTOCOL applies
(forward-slash JSONs, new ids, sequential banking, sanitizer first).

## 10. Honesty limits (declared now)

- The tissue is the M11 engineering actuator bladder; its classification law
  carries over (engineering_actuator; no biological equivalence claimed).
- Bones remain declared point-mass elements with real masses; no per-bone
  inertia tensors are invented. The "inertia" gate Y2c is the declared
  transverse inertia of the assembled mass layout about the erected axis --
  a declared aggregate, disclosed as such.
- The elbow bond stays UNRESOLVED (B04); the foot/hand stays an
  explicitly-unresolved terminal (B03 shell + B04 unresolved body); the B05
  port ledger carries over verbatim; this card qualifies DETAIL SCALING of
  the sealed rig, not the unresolved ports.
- The coarse mesh's bending fidelity is NOT claimed to match the reference
  between gates -- only the declared force/control/render-mapping gates
  within their windows are claimed; any gate the coarse resolution fails is
  reported as a disqualification of `coarse` (the selection rule then picks
  the qualified reference), never hidden.
- The VRAM formula is an engineering bound on rasterization demand, not a
  measured GPU allocation (section 9).
- Independent visual judgment of imagery stays with review
  (visual_acceptance stays false in the validator receipt).

## 11. Execution order (frozen)

prereg commit (this file ONLY) -> coarse-erection probe + implementation ->
Amendment A1 (probe-recorded coarse offset + any probe-forced window
re-derivation, BEFORE the bank) -> falsifier preflight -> CPU bank (all
gates armed at the final commit; batch_gates 12/12 green before any spend;
none planned) -> named checks -> capture -> generated report + lint ->
anchors -> push review/MAT2-M12 -> PR (base astra/gait-capture) -> registry
submit (args: task_id MAT2-M12, attempt_id, agent_id =
arrival-glm53f-m12-w1, pr_url, head_sha, criteria_sha256; actor astra-codex)
-> STOP (the Lieutenant owns review/accept/merge).


## Amendment A1 (own commit; recorded BEFORE the bank)

Trigger: the declared coarse erection offset was PROBE-DERIVED (prereg
section 1 rule 5). Probes on this attempt, CPU, pre-bank, recorded verbatim.
All probes: coarse resolution, offset 0, free-hang (the probe_free_hang
probe-only tamper: ground contacts disabled), off schedule.

- P-A1.1 (first probe; metric REJECTED): foot-gap-based sag -- rows[0] foot
  gap 3.179237071208419e-2 m, settled -8.938402469002187e-4 m, "sag"
  3.2686210958984406e-2 m. Diagnosis: NOT vessel compliance. The sealed
  chain placement (limb_world.py line 876: per-element drop from the pole)
  starts the chain bunched within sum(drop) ~= 4.18e-2 m of the pole; the
  chain settles to its taut hang through the P0 presettle phase (measured
  T1 0.1922 -> 0.5086 N over 200 ticks; vessel pole settles
  0.0470032 -> 0.045910 m). The foot-gap start is not an erection datum;
  the metric was rejected and the probe re-issued in the sealed M11 A2 form.
- P-A1.2 (adopted metric -- the sealed M11 A2 pole-sag form): pole sag :=
  z_pole_target - settled pole z (lift-invariant; uncontaminated by the
  chain's bunched-start settling). 600-tick probe: 1.0940713067333074e-3 m
  (trail, 20-tick means ending at the listed tick: 200: 1.0743451109040889e-3,
  400: 1.095249954234996e-3, 600: 1.0940713067333074e-3). 1500-tick probe
  (the bank's history length): 1.0928872117499794e-3 m (trail: 900:
  1.0932639105317096e-3, 1200: 1.0929824686764025e-3, 1400:
  1.0929083423526845e-3, 1500: 1.0928872117499794e-3; drift 600->1500
  ~1.2e-6 m -- converged).
- DECLARED: ERECTION_OFFSET_M['coarse'] = 1.0928872117499794e-3 m (the
  1500-tick value; probe history length == bank history length). The
  reference resolution keeps the SEALED M11 offset 3.0312e-3 m (reused).
- P-A1.3 (verification probe; contacts ENABLED, full 1500-tick off run,
  coarse, with the declared offset): settled OFF-window (1400,1500) foot
  gap 1.9999168685494353e-4 m (declared target 2.0e-4 m; deviation 8.3e-9 m
  against the 1.0e-3 m window) and max OFF-window foot contact 0.0 bitwise.
  The reference offset's Y4c verification is a bank gate.
- No window of PREREGISTRATION section 5 required re-derivation: every
  probe landed inside its declared window with the declared constants.
