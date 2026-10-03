# PREREG DRAFT — RUNTIME-SLICE-V1: player-controlled physics tick to same-tick render (product MembraneTick line)

Status: **DRAFT (CHAIN STOP 1).** Authored by wk-runtime-slice, 2026-10-02.
Phase 1 only (design + readiness audit + prereg DRAFT; ZERO runner jobs
launched by this lane). This draft awaits the Lieutenant's pin; FINALIZE-AT-
FREEZE slots are marked; any required prereg commits go through the
publication owner BEFORE any gated experiment. Nothing here is a run claim.

Authoritative task brief:
`E:/Chimera/parallel-budget-probe/orchestration_cycle2/PLAYER_CONTROLLED_RUNTIME_SLICE_TASK.md`
(coordination-only input; every factual claim in it re-verified against the
tree by this lane — see EVIDENCE.md).

## 0. READINESS VERDICT (the chain stop)

**THE NATIVE MembraneTick CUSTOM-RENDERER RUNTIME FAILS THE READINESS TEST.
0/5 required mechanisms present. The positive-run implementation is NOT
unlocked; this readiness report IS the chain stop.**

Per the task file: "If any required mechanism is absent, report the exact
missing owner/API/equation and stop that claim for an authority decision; do
not fabricate a force model." Every named-absent below is a named refusal,
evidence-backed at file:line in the pinned source (hashes in EVIDENCE.md).

### The named-refusal table (the readiness-test result)

| # | Mechanism (task-file name) | What actually exists in the pinned source | Verdict | Named refusal | Exact missing owner/API/equation |
|---|---|---|---|---|---|
| RT-1 | Body mass/inertia | ONE scalar `mass_kg_ = 13824.5` (membrane_tick.hpp:423), water-volume-derived (13.8245 m^3 x 1000 kg/m^3, header comment), used ONLY by the single root-Y DOF (membrane_tick.cpp:865). Limb-partition "mass table" = `LIMB_MASS_RHO * w` (water, hpp:330-341) — book values that drive no dynamics. `JointBinding` carries NO mass/inertia fields; its header line 3 states: "Geometry binding only: these operations do not supply actuator dynamics." | **ABSENT** | `body_mass_inertia_table_absent` | Per-body rigid mass + inertia tensor with expressed frame, owned by the assembly/mass packet. The packet is BLOCKED: `real_packet_readiness.json` counts 0.0 kg of component mass vs 17.039978509953905 kg uncounted; 9 undecided masses; 9 missing component frames; ambiguous root frame; 0/8 mechanically qualified attachments; BOTH required inputs (`material_volume_document.json`, `mechanical_requirements.json`) `exists:false`, and `tools/assembly_handoff/inputs/` is absent from the tree. **No existing lane owns it** — the sibling mass lanes (mass-reg, lineage-verify, assembly-identity) all concern the W03 sealed walk-scene lineage (10.038 kg), not this packet. A separate owner is REQUESTED. |
| RT-2 | Force/torque actuation | `intent(force_n, foot)` standing press (cpp:342-347) and `intent_joint` per-pin presses are consumed as the HYDRAULIC DIMPLE — surface offsets `delta = F/(4 pi sigma)` into `press_off_` (cpp:451-535). They enter no equation of motion. The ONLY integrated dynamics in the runtime: `root_vy_ += (g_contact_n_/mass_kg_ - G_EARTH)*dts` (cpp:865), gravity + one penalty spring on ONE DOF. | **ABSENT** | `generalized_actuation_absent` | A declared actuator interface mapping player commands to generalized force/torque through a mass matrix M(q), with a pinned actuator/sign map. No such model, API, or equation exists on this line. |
| RT-3 | Solved foot-ground contact | Penalty spring read at the single lowest vertex, Y-normal only: `F = k_ground_*depth + c_ground_*max(0,-root_vy_)`, capped 50*m*g (cpp:849-861). No friction, no contact manifold, no per-foot contacts, no impulse/LCP solve. The G1 gait machine MEASURES foot depth (`gait_depth_`) but drives joint pose pins kinematically with rate caps (hpp:114-128, 550-553). | **ABSENT** | `foot_ground_contact_solver_absent` | A frictional contact solver emitting per-contact receiver identity, gap/touch state, and normal+tangent impulses. |
| RT-4 | Signed reaction impulses | One scalar `g_contact_n_` (Y-normal force; hpp:427, cpp:861, reported at cpp:4697). No tangent component anywhere; no impulse records. The WALKPHYS P3 lesson (PR #328, merged 42614bac) — direction-free serialized friction scalars left 61/240 window ticks unattributed, failures clustered at impacts, 16/61 carried ZERO serialized friction despite loaded pads — applies a fortiori: this line does not even have a scalar tangent. | **ABSENT** | `signed_reaction_impulse_channel_absent` | Signed world-space (n, t1, t2) impulse components per contact with recorded basis vectors, application points, and degeneracy fallback, per `WALK_TELEMETRY_V2_CORRECTIONS.md` ("Close linear and angular impulse balances"). |
| RT-5 | Energy accounting | Kappa volume-pressure law + `conserve_pct_` volume conservation (seal machinery). NO mechanical energy ledger for any motion DOF (no work/heat/dissipation/projection accounts; the FALL DOF has none either). The W03 line's ledger carries the pre-accepted 30.970713623726674 J imbalance — engine debt, WALKPHYS P4. | **ABSENT** | `mechanical_energy_ledger_absent` | One nonduplicating ledger: mechanical storage, signed work, heat, solver projection under ONE declared gravity convention (WALK_TELEMETRY_V2_CORRECTIONS.md "Use one gravity convention per energy boundary"). |

**Named-present (does not unlock the milestone but is the lane's asset):**
the same-frame seam EXISTS — main.cpp:4473-4474
(`g_tick.step(g_tick_verts, tick_dt); engine.update_mesh(g_tick_verts, g_tick_vcount)`
on the render thread); `/tick_state` exposes `g_tick.state_json()`
(main.cpp:3139-3141) which self-reports `"body_actuation":"kinematic"`
(membrane_tick.cpp:4660); the GPU completed-readback primitive EXISTS
(`request_capture` / watermark / `capture_frame(rgba,w,h,&seq,&phases)`,
engine.hpp:47-79, exercised at main.cpp:783-793). The seam is plumbing, not
physics — the runtime says so itself.

**Build identity gap:** no executable matches the pinned source. The only
prebuilt `ChimeraEngine.exe` (sha256 `3cb959a2...`, mtime 2026-08-16) predates
this branch (HEAD 7222729e, 2026-09-29 line). `PLAYABLE_BUILD.json` is
UNQUALIFIED with all-null pins (verified). First executable work is the
walkphys pre-gated smoke-probe pattern: an MSVC build inside a runner slot;
`BLOCKED(toolchain)` is the honest smallest-missing-prerequisite outcome.

## 1. The readiness-test plan (what the test IS, so the refusal is falsifiable)

The readiness test is a STATIC-SOURCE + BUILD-PROBE instrument, preregistered
before any dynamic run. It re-executes on demand and must produce this exact
verdict format:

- For each RT-1..RT-5: PRESENT / ABSENT with the named-refusal code, the
  file:line evidence, and the constructed trigger that would flip the verdict.
- Constructed triggers (each refusal is falsifiable — these fire the flip or
  prove the audit blind):
  - T1 (mass): a sealed per-body mass/inertia table admitted by the assembly
    owner + a build-time LV-1-class emission receipt. If the audit still says
    ABSENT with such a table pinned, the AUDIT is falsified, not the runtime.
  - T2 (actuation): a compiled path applying force to a named generalized
    coordinate through M(q). Grep-level absence is checked against the symbol
    census (mass matrix / actuator / applied_generalized_force classes) in the
    built binary's translation units.
  - T3 (contact): a contact-solver symbol emitting per-contact impulses. The
    audit must name every contact-related symbol on the line
    (g_contact_n_, k_ground_, c_ground_, gait_depth_) and show none solves.
  - T4 (impulses): any signed (n,t1,t2) record anywhere in the tick path.
  - T5 (energy): any work/heat ledger accumulator in the tick path.
- The probe arm: inside one runner slot, configure+build the pinned source
  (engine/CMakeLists.txt, Vulkan SDK path pinned in it) and run the binary to
  `/tick_state` readiness. Outcomes OK / `BLOCKED(toolchain)`. A BLOCKED is
  reported as the smallest missing prerequisite, never worked around.

## 2. Entry-blocker resolution (the task file's ownership question, answered)

The task file: "First check whether the assembly/mass lane already owns the
missing material-volume, ownership, frame, and mechanical-requirements
evidence." **Answer: NO.** Verified 2026-10-02: `tools/assembly_handoff/inputs/`
does not exist in the checkout; both required inputs are `exists:false` in
`real_packet_readiness.json` (unchanged since 2026-09-24 13:59); the
monkey-coordination sibling lanes named for mass work (mass-reg, lineage-verify,
assembly-identity, pair-assembly) all address the W03 sealed walk-scene lineage
(10.038 kg, VERIFIED-AS-SEALED-DYNAMICS-MASS per lineage-verify/REPORT.md) —
none owns the assembly_handoff packet. **A separate owner is requested from the
Lieutenant for: the reconstructed material-volume document, the mechanical-
requirements document, component frames, and the root-frame decision.**

Mass-prerequisite carry rule (inherited): any later mass admission is carried
as its owning-lane identity (the W03 lineage precedent:
VERIFIED-AS-SEALED-DYNAMICS-MASS) PLUS the LV-1 live-runtime emission gate —
at any live-build claim, the BUILD ITSELF emits its per-body mass table at
launch (per part: body owner/name + mass value + source-artifact sha each
part loaded from) and that receipt is bound; a package without it refuses
`freeze_emission_receipt_missing`. This is the lawful path to the first
QUALIFIED PLAYABLE_BUILD row.

## 3. The positive-run design (CONDITIONAL — gated on RT-1..RT-5 flipping to PRESENT)

NOT DISPATCHED. This section activates only after: (a) the mass/contact/energy
prerequisites land through their owning lanes, (b) this prereg is re-pinned
with the landed identities, (c) the Lieutenant grants the run. Until then any
implementation or measurement run is prohibited by the task file's strict
order. The design skeleton is recorded now so the gate is pre-committed:

- **Command:** ONE bounded sequenced player command stream (e.g. a forward
  press at declared foot channels), consumed EXACTLY once per tick at the
  tick boundary inside `step()` via a new tick-boundary queue (today HTTP
  route handlers write `force_l_/force_r_` bare floats with no lock against
  the render-thread tick — the join adds the sequenced handoff).
- **dt policy (FINALIZE-AT-FREEZE):** fixed-step policy declared in the
  freeze. Today `tick_dt` is measured frame time clamped [0, 0.1] s
  (main.cpp:4466-4472); replay identity cannot be predicated on wall-clock
  jitter, so the fixed-step rule and its relation to render cadence are
  frozen constants with derivation.
- **Positive predicate:** whole-body COM translation over a frozen window
  caused by CONTACT FORCES from named actuators, exceeding a frozen
  uncertainty band; joint-motion-only or membrane-shape-only outcomes do not
  satisfy it.
- **Momentum reconciliation (the walkphys-corrected identity):**
  `|M*(x[t+2] - 2*x[t+1] + x[t])/dt| <= sum(|f|*dt)` in SIGNED vector form —
  per-contact world-space (n, t1, t2) with recorded basis vectors,
  application points, actuator/generalized sources, per-body COM
  states/masses/inertias; vector residual reported, never scalar proxies.
  Inherited lesson (PR #328 P3): scalar serialization is the known gap;
  impact-impulse records are part of the attribution set.
- **Energy ledger:** one gravity convention for the boundary; mechanical
  storage, signed work, heat/dissipation, solver projection, no
  double-counting; a missing term labels that evaluator NOT ASSESSABLE and
  the run diagnostic-only (fail closed, never zero-filled).
- **Prohibitions (structural, not prose):** the command/control path never
  assigns root position, body transforms, or posed vertices; solver/integrator
  updates to generalized state are the ONLY lawful writers. `set_gait` /
  pose / flex / mesh-pose routing called physics is refused by construction.

## 4. Falsifiers (each fires on its constructed trigger)

| ID | Falsifier | Fires when | Constructed trigger (how it is proven able to fire) |
|---|---|---|---|
| FB-A | Root-write scan | any player/controller-path write to root position, qpos, body pose, or renderer-only animation state outside the solver | an injected root-pose write mutant is caught by the scan (the certificate-gate I1 / TC-4 pose-authority class) |
| FB-B | Animation-routing scan | a command routed to set_gait/pose/flex/mesh-pose instead of the declared actuator channels | route-cut mutant: cutting the actuator channel must stop all player-caused motion (the C1 pressure_coupling nerve-cut class); a surviving response = routing bypass |
| FB-C | Signed momentum identity | per-tick vector residual of `M*dx_dot/dt` vs `sum J_external` beyond the frozen window | a sign-flip mutant on one tangent component must fire it; a passing sign-flip = the check is direction-blind (the exact WALKPHYS P3 failure mode) |
| FB-D | Determinism / replay | same frozen initial state + input stream fails to reproduce the preregistered physics + render payload bytes exactly (only named volatile metadata excluded) | any unmasked volatile field (e.g. `ts_us`) inside the hashed payload fires it on repeat run |
| FB-E | Neutral-input control | the neutral command stream diverges from the no-player baseline beyond noise | run both; divergence fires |
| FB-F | Actuator-disabled control | the player-specific response survives disabling the controlled actuator channels | channel-cut arm retains the response = an undeclared force source |
| FB-G | Contact-disabled control | contact-off arm retains support impulses or reacts inconsistently | support impulse present with contact disabled fires |
| FB-H | Snapshot freshness | snapshot tick/hash != the state submitted to splats/evidence; stale tick, mixed mutable state, missed or duplicated command | a reread-after-snapshot mutant (state mutated between snapshot and submission) must fire the hash equality check |
| FB-I | Energy-ledger closure | cumulative ledger imbalance beyond the frozen window | a dropped ledger term mutant must fire the closure check; a silent zero-fill fires the fail-closed check |
| FB-J | Command sequencing | a duplicated/late/replayed command is consumed twice or out of sequence | injected duplicate command at a declared tick must produce a visible refusal or sequence gap |

## 5. Honest-absent list (declared BEFORE any run; FINALIZE-AT-FREEZE items marked)

- Per-body mass/inertia table (product line): ABSENT (RT-1; assembly packet
  blocked; owner requested).
- Generalized force/torque actuation: ABSENT (RT-2).
- Solved frictional foot-ground contact: ABSENT (RT-3).
- Signed reaction-impulse channel: ABSENT (RT-4).
- Mechanical energy ledger: ABSENT (RT-5); W03-line ledger closure: KNOWN
  NEGATIVE (30.970713623726674 J, engine debt — carried, not this lane's
  repair).
- Build identity for the pinned source: ABSENT (no matching executable;
  PLAYABLE_BUILD.json UNQUALIFIED, all null).
- Fixed-step dt policy: UNDECLARED (FINALIZE-AT-FREEZE).
- Positive-run windows, tolerances, residual criteria, uncertainty bands:
  UNDECLARED (FINALIZE-AT-FREEZE — set once at freeze with derivation, never
  after seeing data; the WALKPHYS P5 frozen-window lesson requires early-
  refusal behavior stated at freeze time).
- Tick-boundary sequenced command queue: ABSENT (design section 3; a new
  implementation item requiring its own scoped patch).
- Mass-table emission receipt at build (LV-1 gate): ABSENT (required for the
  first QUALIFIED row).
- Uneven terrain, transition phases, continuous ten-phase run: OUT OF SCOPE
  (the task file scopes a controlled flat-ground stride at most).
- Interactive real-time guarantee: ABSENT (not claimed by this slice).
- Camera/focus-loss/start-stop behavior verification: NOT STARTED (PLAYABLE_
  BUILD.json remaining_blockers stand).

## 6. What this lane is NOT claiming

No locomotion milestone. No PLAYABLE_BUILD qualification. No physics claim of
any kind. The W03/walkphys results (PR #328) are evidence for the W03 line;
they are inherited here as METHOD (instrument patterns, momentum-change
identity, prereg law) and as NAMED DEBT (signed-tangent channel, energy
ledger), never as product-line evidence. The Python /walk and /sim viewers
are ruled out as evidence paths for this lane (verified: walker.py:311-363
integrates root x/y directly; live_viewer.py:880+ StandSimulator is a stand-
only MuJoCo policy receiving no player movement command).

## 7. Execution plan (phase 2, NOT STARTED; requires the Lieutenant's unlock)

1. Prerequisites through their owners (mass/inertia; contact solver; energy
   ledger; actuator interface — each a NEW prereg by its owning lane).
2. Re-pin this prereg to the landed identities; freeze FINALIZE-AT-FREEZE
   slots; publication owner commits the prereg BEFORE any gated experiment.
3. Independent pre-run approval/release.
4. Pre-gated smoke probe (build + /tick_state) in a runner slot;
   BLOCKED(toolchain) honest.
5. Smallest implementation patch + focused tests; seal via
   `task_package.py seal|run`; all receipts + traces declared with --keep;
   evidence anchored through anchor.py before any reference.
6. Independent review (Sergeant): rebuild/rerun the pinned package, verify
   negative controls, static no-root-write scan, measured latency.

Anti-tuning law (standing, inherited): no parameter may differ between the
pinned baseline and any clean arm; the only declared deltas are the control
arms (FB-E/F/G), each EXPECTED to lose the response. A gate that passes only
under a clean-arm parameter change is a tune_to_success refusal: record and
stop.
