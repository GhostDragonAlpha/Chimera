# chimera-construction-v0.1.0-rc.1 — construction release candidate (draft)

Status: **release candidate draft**, not a release. Naming and location are
the proposed convention (referenced from plan §13 — see "Applying the §13
reference" below).

- **Pinned source commit:** `27314746`
  ("B9: material-geometry-solver qualification envelope on the resident
  runtime"). A moving branch tip is insufficient; everything below describes
  exactly this commit. (The draft originally pinned `def4d82d` (B8); the pin
  advanced when B9 landed, and the receipt was rerun against the new
  candidate binary — see §3 and `recipe_comparison_rc1_27314746/INDEX.md`.)
- **Candidate executable:** built from a clean detached worktree at the pin —
  `cmake -S ChimeraEngine/engine -B .tmp/body-engine` then
  `cmake --build .tmp/body-engine --config Release` — SHA-256
  `6c2f97d80666fc999105a564c6bff01d0f5fa886edb855d3d1f1c4870de9906f`.
  Shader identities: `shader_sha256` in
  `docs/evidence/recipe_comparison_rc1_27314746/receipt.json`.
- **Launch:** `chimera_engine.exe <port> --hidden 1600 900 --no-restore`.

## 1. Scope — what this candidate does and does not qualify

This candidate freezes the **construction packet** interfaces and evidence
(B0–B9 of the plan §13 gate table and acceptance gallery). It does **not**
satisfy the graph's full engine-release gate: `req.engine_game_release`
explicitly requires an objective, success/failure/recovery, operation without
an agent, and operator/player confirmation. Those remain open (§6). The
separate game repository stays deferred until a qualified player-driven loop
exists.

## 2. Frozen contracts

1. **Route surface.** The supported construction routes and their
   request/response JSON schemas: `/tick_b2_admit`, `/tick_b2_state`,
   `/tick_b2_place`, `/tick_b2_remove`, `/tick_b2_parts`, `/tick_b2_clear`,
   `/tick_b2_pause`, `/tick_b2_load`, `/tick_b2_support`,
   `/tick_b2_gravity`, `/tick_b2_pick`, `/tick_b2_inspect`,
   `/tick_b2_weld`, `/tick_b2_weld_remove`, `/tick_b2_patch`,
   `/tick_b2_save`, `/tick_b2_restore`, `/tick_b2_hash`,
   `/tick_b2_render_lod`, `/tick_b2_clock`, `/tick_b2_chamber`,
   `/tick_b2_valve`, `/tick_b2_valve_set`, `/tick_b2_valve_patch`,
   `/tick_b2_valve_remove`, `/tick_b2_heat`, `/tick_b2_heat_remove`,
   `/tick_b2_piston`, `/tick_b2_piston_remove`, `/tick_b2_process`,
   `/tick_b2_process_clear`, plus the evidence-chain auxiliaries the
   batteries and recipe runner depend on (`/frame`, `/log`, `/reel`,
   `/compare`, `/glass`, `/cameras`).
2. **Units and coordinates.** SI throughout: metres, kilograms, newtons,
   m/s, rad/s, joules. Y-up world frame; `com_m` and `point_world` are
   world-frame metres; `pose_R_rowmajor` is a row-major 3×3 rotation;
   weld `anchors_world` are `[ax,ay,az,bx,by,bz]` world pairs; loads are
   world-frame newtons applied at a world point.
3. **Transaction and refusal behavior.** Every mutating route is a
   transaction: it either commits fully or refuses with a self-named error
   and leaves the live world byte-identical (state hash invariant across
   refusals). Over-cap and invalid-geometry transactions refuse before
   mutation. Pool-cap refusals name the cap and the remedy.
4. **Save/restore format.** `/tick_b2_save` returns the complete scene
   document; `/tick_b2_restore` accepts exactly that document and is
   hash-verified (`/tick_b2_hash` equality after restore). The document is
   the save format; no side files.
5. **State-hash semantics.** Hashing happens only on the explicit
   `/tick_b2_hash` route — never on routine reads (no full-state CPU round
   trip on `/tick_b2_state`). Instrumentation counters (round trips,
   backstop engagements) are never serialized, so the hash is invariant
   across saves/reads/instrumentation.
6. **Clock behavior.** Independent physical clock: dedicated
   `steady_clock` thread, 2 ms wake, 50 ms catch-up clamp per wake,
   self-reporting counters (`catchup_clamps`, `slow_ticks`, `max_gap_ms`)
   on `/tick_b2_clock`. Physical outcomes do not depend on display cadence;
   render LOD never touches physics, the save document, or the hash.
7. **Pool caps.** parts 6 / welds 15 / chambers 6 / valves 12 / heat 12 /
   pistons 6, reported every tick as `state.pools = [used, cap]`.
8. **Declared numerical approximations** (b2_scene, all measured):
   resting-contact penalty rung (10 mm rest sink); declared impact
   backstop — ordinary rung to `B8_STOP_M = 15 mm`, then a one-way,
   velocity-gated (`0.1 m/s` approach) stiff catch (200× rung, ζ = 0.7),
   energy-booked and engagement-counted; pair-contact candidacy requires
   penetration past the `B2_FACE_TOL = 1e-4` coplanar noise floor and
   half-space containment (max gap over all face planes < −tol);
   regularised Coulomb friction with per-site impulse caps
   (`mass/(nv·h)` ground, reduced-mass pair); fixed substep with explicit
   stability margins ω·h = 0.11, c·h/m = 0.16.
9. **Measured envelopes.** `B7_declared_envelope.json` (4090-class host:
   working set, frame-time window, plateau under repeated construction);
   the B2 numerical envelope report; the recipe-comparison receipt
   (`recipe_comparison_rc1_27314746`, equilibrium fixture only — this
   qualifies the equilibrium comparison, not fracture strength or transient
   behavior).
10. **Qualification envelope (B9).** Admission, place and restore refuse
    named bands **before mutation** (state hash invariant across refusals):
    rest sink ≥ `B9_SINK_MIN_M = 10 mm`; sliding-role parts ≥
    `B9_SLIDE_MIN_H_M = 50 mm` tall; declared sustained lateral load must
    satisfy `F·H/(m·g) ≤ B − sink − 2 mm` (`B` = smaller base half-extent).
    The optional part-document `envelope` block
    (`max_lateral_load_n`, `max_approach_speed_m_s`,
    `role: stand|slide|impinge`) travels with the part: echoed in the save
    document, revalidated on restore. Post-admission exits are **visible
    telemetry, never physics mutation**: `/tick_b2_state` reports
    `out_of_envelope_events` (cumulative), `out_of_envelope_last`
    (part/limit/measured/declared) and `out_of_envelope_limits`
    (per-limit counts) for `max_approach_speed_m_s`, `backstop_stop_m` and
    `stand_tilt_rad` (10°). Bands are calibrated on the measured B8
    failures; geometries between the largest measured failure and the
    smallest measured pass are **unqualified**, not silently allowed.
    Evidence: `B9_envelope_evidence.md`, `test_b9_envelope.py`.

## 3. Format compatibility vs physical-result compatibility

These are different claims and this candidate keeps them separate:

- **Format compatibility:** a save document produced by an older qualified
  binary loads and restores on the candidate with hash-verified equality of
  the restored state.
- **Physical-result compatibility:** NOT claimed across solver changes. The
  B8 contact-model change is the demonstration: the same cradle fixture
  restores fine (format-compatible) yet its baseline state hash changed
  (`c2336e9a…` → `805af3e4…`) and equilibrium forces shifted ≈ −0.9 %
  (soft 0.368730 → 0.365492 N; stiff 0.398294 → 0.394519 N). Old
  measurements are therefore **not valid** against the new binary; each
  solver change requires re-measurement, and receipts carry predecessor
  references (`recipe_comparison_rc1_def4d82d/INDEX.md`).
- The B9 receipt rerun demonstrates the **converse**, which is the sharper
  lesson: the B9 candidate reproduced the equilibrium numbers exactly
  (0.365492 / 0.394519 N) and its rendered captures are **byte-identical**
  to the predecessor's deleted originals (SHA-256 match in both
  `CAPTURE_DIGEST.json` files) — yet the baseline state hash still differs
  (`805af3e4…` → `fc956d5c…`). Field-by-field, only the step counter
  (8681 → 8480, the settling loop lands on a different step under
  wall-clock polling) and machine-epsilon residuals (1e-17…1e-33) moved.
  The state hash is a format/serialization identity over the save document
  — which includes the step counter — so it is not a cross-run physical
  comparator; the measured quantities are. See
  `recipe_comparison_rc1_27314746/INDEX.md`.

## 4. Evidence index

- Gate evidence: `docs/evidence/construction_packet_20261012/`
  (`B0_baseline_and_ownership_map.md` … `B7_bounds_evidence.md`,
  `B8_gallery_evidence.md`, `B9_envelope_scope.md`,
  `B9_envelope_evidence.md`, `FULL_PLAN_AUDIT.md`, frames, envelope JSON).
- Batteries: `tools/construction_packet/test_b*.py` +
  `test_construction_packet.py` — **84 passed** full regression at this
  commit (133.20 s, sequential; disjoint engine ports).
- Recipe comparison: `docs/evidence/recipe_comparison_rc1_27314746/`
  (4 reversed-order trials, contract checks green, exact reproduction of
  the `def4d82d` candidate's equilibrium; predecessor receipt preserved
  and marked stale at `recipe_comparison_rc1_def4d82d/`).
- Capture retention: raw image captures are digested (SHA-256 + the
  physics they demonstrated) and deleted per
  `docs/evidence/CAPTURE_RETENTION.md`; committed evidence in this chain is
  JSON-only, and the receipts' `artifacts_sha256` preserve the byte-identity
  audit of everything deleted.
- Caveat, stated plainly: the 84-test regression was measured on the shared
  checkout's build, which differs from the candidate binary only by three
  uncommitted UI-only lines in `ui.cpp` (another agent's work, not in the
  pin). The recipe comparison was measured on the candidate binary itself.

## 5. Applying the §13 reference

The plan file `docs/GAME_PLAN_ACTION_RPG.md` is dirty with another agent's
uncommitted edits in the shared checkout, so this document cannot add its
own §13 reference line without committing that agent's work. The line to
apply when the plan file is next clean, after the B7 gate-table row:

> | B8 / gallery — acceptance gallery + §11.3 swept contact | (see gallery items 1–17) | Closed by `docs/evidence/construction_packet_20261012/B8_gallery_evidence.md`; construction release candidate `docs/releases/chimera-construction-v0.1.0-rc.1.md` |
> | B9 — material–geometry–solver qualification envelope | named refusals before mutation; unchanged state after rejection; boundary cases; known-failure reproductions; visible runtime response to post-admission exits | Closed by `docs/evidence/construction_packet_20261012/B9_envelope_evidence.md` (battery `test_b9_envelope.py`, 7 tests; envelope contract frozen in the release candidate §2.10) |

## 6. Open blockers — visible, not hidden

1. **Human observation (release blocker).** No designated player-observation
   workflow exists in the inspected contract. Automated tests establish
   mechanical behavior; they cannot establish that an unfamiliar player
   understands it. Operator observation can satisfy the operator-confirmation
   clause of `req.engine_game_release`; unfamiliar-player claims require
   actual unfamiliar participants. Encounter packets remain proposals.
2. **Transient comparisons are unqualified.** The recipe chain qualifies the
   equilibrium fixture only. Exact transient comparison needs its own gate:
   exact native step counts, exclusive clock ownership during trials,
   observation boundaries, state restoration, repeatability, and preserving
   every physical substep. An independent clock does not establish
   deterministic advancement or synchronized samples.
3. **Python chain provenance.** The recipe-experiment chain
   (`tools/recipe_experiments/`, `cradle_recipe.py`, `python_control/`) is
   untracked working code, byte-verified against the predecessor run but
   not yet committed by its author; the candidate's reproducibility from the
   pin alone therefore covers the native binary, not the experiment driver.

**Closed since draft:** the qualification-envelope blocker (B9) was closed
at the pin commit itself — bands declared, refusals enforced, runtime exits
visible (`B9_envelope_evidence.md`; contract frozen in §2.10). The measured
B8 failure modes it existed to cover — slender-wall topple, material-
dependent catch stability, thin sliding block — are now refused at admission
or reported as named out-of-envelope events.
