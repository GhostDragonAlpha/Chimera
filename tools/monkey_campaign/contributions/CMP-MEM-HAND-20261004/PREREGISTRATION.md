# PREREG DRAFT (chain stop 1) — PKT-G3-MEMBRANE-HAND / membrane.hand.v1

Worker: wk-membrane-hand. Status: DRAFT, awaiting the Lieutenant's separate-first
pin. NOTHING below is a claim of an executed run; no seal, no receipt and no
acceptance exists yet. Implementation starts ONLY on the pin; the seal base is
the pin. Publication stays with the Lieutenant.

## 0. Packet and criteria identity (verified 2026-10-02, this session)

| item | value | verified how |
| --- | --- | --- |
| packet | PKT-G3-MEMBRANE-HAND (criteria_sha256 `f3dbf0935ca3029c2799a55374f760d652f4e2e8432495b206a20e00aa285a81`) | recomputed from the packet bytes (canonical json minus {criteria_sha256, emitted_utc}) — MATCH |
| input_set | `93d51baca8b68a40e085741a6d9852e7c4e900aade0d94d227049fbe00b3d72d` | recomputed over the 17 pinned inputs — MATCH |
| external contract | pc.hand_ground_contact.v1 sha256 `a54313760c766764fb95302ebe0bee1fbc65f343770a8b9930657f2a6a3f2104` | re-hashed — MATCH |
| all 17 pinned_inputs | roles: runner profile, kernel_dsl, decl.hand_ground.v1, membrane_schema, binding_extension, bind_resolution, scheduler blocker packet, port contract + schema, G04 experiment/falsifier receipts + REPORT, G05 experiment receipt + REPORT, G07 REPORT, A05 mutation structure, graph store | re-hashed this session — ALL MATCH their recorded/expected sha256 |
| resume_state | status OPEN, attempts_at_criteria 0, prior_artifacts [] | read from packet |

Work produced against any DIFFERENT criteria_sha256 will be declared stale, per
the packet resume_law.

## 1. Scope (the interior law)

Implement/verify the HAND side only of conn.hand_ground_contact.v1 against the
external contract: the press channel (armed/released state, owned by
membrane.hand.v1), the press release latch (contract timing.latches.press_release_latch),
and the 32-slot observation seam output. jn/jt are consumed READ-ONLY as seam
records (single writer: the pinned M06 solver at the contact; owner
membrane.ground.v1). membrane.ground.v1's interior stays HIDDEN: no read of any
ground-lane workspace, no authored ground section, no ground-side parameter.
The pair RUN (obligation pair_run) is the assembly task's debt, not mine; my
result claims the hand-side components only.

## 2. Frozen substrate (imported-not-forked; hash-asserted at every run; drift refuses by name)

| role | bytes | sha256 (verified this session) |
| --- | --- | --- |
| ABI of record | E:/ChimeraWork/monkey-coordination/mathspec/membrane_abi.py | `80c5b36574a442fa...` (full 64-hex in EVIDENCE.md) |
| spec grammar/validator | mathspec/spec_format.py, spec_lang.py, spec_runtime.py | `7e037792...`, `6ac52e65...`, `423fca70...` |
| contact solver (seam records jn/jt; B01/B02/B04 implementation) | MAT2-M06 local_contact.py (at package base) | `1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc` |
| grip fixture runner (12-case construction, press application path, closed forms; B03) | MAT2-G04 grip_contact.py (at package base) | `0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b4173d69245` |
| observation seam implementation (32-slot table + delivery gates; B05 mechanism) | MAT2-G05 contact_support_obs.py (at package base) | `3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e4f31c46bd3` |
| release account (recursion + exact energy identity) | MAT2-G07 release_fall_account.py (at package base) | `78b5cc66f7019fa181765eb0366fe6c98525941840f57723d0ae99cb55b2a8c5` |
| trunk fixture mesh | MAT2-F03 assets/trunk_01_mesh.json (at package base) | `3b17441764714c5e...` |
| mu placeholder block constants | MAT2-M06 contact_law.json (at package base) | `583962c29f18118a...` |
| W04 observation contract (G05 upstream) | E:/ChimeraWork/pass3-integ/repo/.../observation_interface_v2.json | `e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a4f1188b1c0671c` (host pin re-verified this session) |

Package base candidate: `cdfaa8cc1535dbe723097aa1277385aeb2aa79d3` — verified
this session to carry ALL of the above repo-relative reads at exactly these
sealed hashes (the same base the K01 package used). FINAL base = the
Lieutenant's pin; if the pin is a commit, it must descend from (or record) a
tree containing these reads at these hashes; the receipt's CHIMERA_BASE_SHA
binds the actual base per run.

## 3. New artifacts (written ONLY in my scopes)

Task package: E:/PythonChimera/tools/monkey_campaign/contributions/CMP-MEM-HAND/
(created with task_package.py create at the pin; writes declared to that
directory only). Lane records: E:/ChimeraWork/monkey-coordination/membrane-hand/
(this draft, EVIDENCE.md, later the report + result copies). Packet workspace:
compiler-compile/packets/PKT-G3-MEMBRANE-HAND/workspace/ (generated result only).

1. `spec/hand_press_seam.spec.v1.json` — frozen ABI-context document in
   chimera.mathspec.spec.v1 grammar declaring:
   - membrane `membrane.hand.v1` (IMPLEMENTS_MEMBRANE_ID), owned_state:
     `press_channel_state` (unit N*s; domain [0.0, 0.3]; released = 0.0 exactly,
     armed = P) and `grasp_observation_table` (unit `unitless` in-spec — see
     section 8 mapping note; contract unit slot_f32);
   - ports: inputs `in.jn`, `in.jt` (unit N*s, connection_ref
     conn.hand_ground_contact.v1, READ-ONLY seam records); outputs
     `out.press_channel_state` (N*s) and `out.grasp_observation_table`
     (contract slot_f32 / in-spec unitless);
   - parameters: `press_channel_jn_ns_per_tick` 0.3 (AUTHORED_DECLARED fixture,
     actuator_qualified false — G04 receipt), `press_dt_s` 0.005 (M06 frozen),
     release bars `jn_bar` 6.341478508833337e-11, `jt_bar`
     2.5365914035333348e-11 N*s (G04 amendment a2 worsts, carried as bars, never
     re-derived);
   - numerics.admissibility: exactly [dt_s 0.005]; the dt gate refuses any
     other dt (spec_dt_not_admissible);
   - refusal_conditions: press state outside {0.0, P} (contract: "a record
     outside {armed, released} is a structural fault, not a value"); exact
     grammar forms iterated against the pinned validator at implementation.
2. `hand_membrane_v1.py` — THE ABI module (ABI_VERSION chimera.membrane_abi.v1):
   `build(context, dt)`, `verify_frozen_inputs()` (re-hashes EVERY pinned byte
   above + the context identity; refuses spec_pinned_input_drift by name). The
   built membrane: `ownership()` (exactly the spec owned_states under the ONE
   resolve_ids scheme), `ports()` (typed table above),
   `exchange_quantity(view)` (reads jn/jt from the window-start view),
   `contribution()` writing EXACTLY the owned states, and NO
   `exchange_contribution()` (the seam's exchange-record owner is
   membrane.ground.v1; the ONE-writer law forbids a writer here — asserted
   positively by test).
   Components:
   - PRESS CHANNEL: armed applies P = 0.3 N*s per channel per hold tick
     (declared fixture operating point; operating force 60 N by the DECLARED
     /dt conversion); released applies exactly 0. State values only {0.0, P};
     any other value is a structural fault refusal.
   - RELEASE LATCH (contract timing.latches.press_release_latch): once
     released, stays released until an EXPLICIT re-arm call; a silent re-arm
     (any armed value on a tick after release without the explicit call) is
     refused by name (`ref.hand.latch_silent_rearm`); every release tick
     records jn/jt at the share-scaled noise bars, never a partial press.
   - OBSERVATION SEAM: delivers the declared 32-slot float32 table with the
     mandatory timing block (t_tick, t_phase, t_dt_s, t_seconds), cadence one
     sample per solver tick post-solve, through the pinned G05
     ObservationSeam gates (undeclared_field, timing_unbound, timing_drift,
     named_absent_occupied, privileged_source, nonfinite_value, dim_mismatch);
     the x_* namespace and the 6-name privileged registry stay refused.
3. `test_hand_checks.py` — the acceptance battery (section 5 + 7), runnable
   `C:/Python314/python.exe -B CMP-MEM-HAND/test_hand_checks.py` inside a
   sealed run; emits `outputs/result.json` (chimera.compiler_packet_result.v1)
   and per-check evidence files, all declared with --keep.

## 4. Fixtures (never tuned to pass)

| fixture | value | class | law |
| --- | --- | --- | --- |
| fx.ground_mu_pair | mu_s 0.6 / mu_k 0.4 | NAMED_PLACEHOLDER | debt owner: G04 measured-volar acquisition; blockers NB-01/NB-02; consumed from the contract placeholders (M06 contact_law.json block constants, synthetic_authored). NEVER tuned; every capacity number inherits it linearly; the L1/L2 envelope stays falsifier-band context only |
| fx.ground_plane_height | 0.004 m | AUTHORED_DECLARED | walk plane (composition flatten plateau); single writer: the composition flatten |

fx.mu_placeholders stays a NAMED PLACEHOLDER for this whole task: results stay
fixture_based = true; NO integrated-qualification claim is made anywhere; the
fixture retires only when NB-01/NB-02 retire in a store-pinned artifact.

Honest-absent list (carried VERBATIM from the contract into result.json):
- x_press — measured grip-force actuator bound behind the normal press — ABSENT
  (debt: G04 successor actuator qualification A08-U1; blocker NB-03)
- x_share — per-port load partition across grip contacts — ABSENT (blocker NB-04)
- x_reach — the hand-to-ground placement transform (frame composition) — ABSENT
  (blocker NB-05)
- mu_s_mu_k_measured — measured volar-skin friction pins — NAMED_PLACEHOLDER
  (blockers NB-01/NB-02)
No synthetic constant occupies an absent slot; the seam refuses x_* keys.

## 5. Acceptance battery — preregistered predictions (the packet's own checks ARE the run-time falsifiers; each must fire on its constructed trigger)

Execution: sealed run per NO_WORKTREES (`task_package.py seal` then `run`,
absolute CLI paths, `--keep outputs/result.json` + evidence files). A passing
claim requires the ACTUAL receipt: state PASSED and cleanup_verified true.
BUSY/exit 75 = wait >= 10 s and retry; never a scientific failure. Failures are
preserved and reported, never retried into green.

| check | statement (packet, verbatim numbers) | preregistered prediction | constructed trigger that MUST fire (negative control, run and recorded) |
| --- | --- | --- | --- |
| ACC::T.X1_press_entry | worst abs(jn_pad - P) over all hold ticks of all 12 cases; window 1e-9 N*s; sealed ref 8.342154744767072e-11 (G04 X1) | reproduces the sealed worst 8.342154744767072e-11 N*s (deterministic pinned path) and PASSES the 1e-9 window | press tampered to P*1.001 on an instrumented re-run: worst leaves the 1e-9 window and the check FAILS on the tampered trace |
| ACC::T.X4_release_bars | every release tick jn <= 6.341478508833337e-11 and jt <= 2.5365914035333348e-11 N*s; window share_kg * 1e-10 per release tick; sealed ref G04 a2 worsts | holds on every release tick of every case; my latch state machine's decisions equal the pinned fixture's phase record tick-for-tick | latch disabled (silent re-arm at the first release tick): that release tick records jn ~ 0.3 >> bar and the bar predicate FIRES; the silent re-arm is also refused by name by the production latch |
| ACC::T.G07_accounted_release | free-fall recursion worst 1.747198913326642e-11 m/s (window 1e-9); exact energy identity worst 1.354472090042691e-14 J (exact identity) | both hold at the pinned inputs over the 13 scenarios (12 + band_mid\|n=3\|mu=0 control) with W_press == 0.0 J exactly on every release tick | hidden post-release support impulse (G07 FB2 class) injected on an instrumented re-run: energy identity residual breaks >> 1e-12 J and the account refuses |
| ACC::T.G05_observation_seam | declared-only 32-slot table, explicit timing, 0 refused; worst float32 delivery error <= 1e-6; sealed ref 1.2003610327937508e-08 | 390 accepted / 0 refused over 13 scenarios x 30 ticks (cadence 1 sample/tick post-solve); worst float32 delivery error reproduces 1.2003610327937508e-08 | (a) sample with extra solver-internal key refused undeclared_field; (b) t_dt_s = 0.0 refused timing_unbound; (c) key `x_press` refused named_absent_occupied — each refusal named and recorded |

Prediction of record: ALL FOUR clean checks PASS at the pinned inputs. If any
falsifies, the falsified prediction is itself the result — recorded FAIL with
the artifact, no tuning, no retry-into-green.

Also re-run UNMODIFIED as regression evidence (upstream sealed suites, exit 0):
test_local_contact.py, test_g04_checks.py, test_g05_checks.py (the G07 upstream
triple pattern), if present at the pin base; any absence is declared NOT_RUN in
result.json, never silent.

## 6. ABI conformance tests (preregistered)

1. validate_module(module) -> conformant; identity membrane.hand.v1.
2. validate_built(built, spec, membrane.hand.v1, conn.hand_ground_contact.v1)
   -> conformant; ownership rows == spec section under resolve_ids; typed ports
   equal the spec section; exchange accessor present.
3. ONE-writer law: the built membrane has NO exchange_contribution (owner is
   membrane.ground.v1) — the validator's abi_exchange_writer_violation path is
   asserted by a probe wrapper that ADDS the attribute and must be refused.
4. dt gate: build(context, dt=0.01) refuses spec_dt_not_admissible BEFORE any
   payload; refused window leaves state bitwise unchanged.
5. Frozen-input gate: context bound to tampered spec bytes refuses
   spec_pinned_input_drift; verify_frozen_inputs() returns the identity table.

## 7. Spec conformance — scoped, disclosed (the packet demands NO spec artifact)

The packet's deliverables demand no spec document. My frozen CONTEXT document
exists because the ABI's SpecContext requires one; it is authored in
chimera.mathspec.spec.v1 grammar so the pinned validators operate on it.
Full spec_format.validate_spec conformance is NOT claimed: the validator's
first-class connection rules (exactly 2 declared members; exchange expr;
transfer_law with EXACTLY ONE per-member entry targeting the member's own
state, applied_by assembly) are defined for the continuous ODE-exchange class.
My seam is the GENERATED contact class (per-tick records, single ground-side
writer); forcing it into a transfer_law would require authoring the hidden
neighbor's interior dynamics — prohibited by the interior law — or a synthetic
zero-transfer constant in the neighbor's slot — prohibited by the named-variable
law. My battery therefore (a) runs validate_spec on my document and RECORDS its
complete refusal list verbatim in the evidence, asserting every refusal is in
the enumerated connection-class set (E_SPEC_UNKNOWN_MEMBRANE /
E_SPEC_TRANSFER_MEMBER_INVALID / transfer-law rows) and NONE is in my hand-side
membrane section; (b) claims the packet-relevant conformance through the ABI
validators (section 6), which check ownership/ports/one-writer/dt/drift against
the same document. If the Lieutenant prefers a different resolution (e.g. a
validator extension owned by the mathspec lane), this draft flags it as an open
decision BEFORE the pin; it does not block the hand-side implementation.

## 8. Declared representation mapping (disclosed amendment-class note)

The pinned spec grammar's canonical-unit table has no slot dimension
(spec_unit_unknown for `slot_f32`; verified this session). The spec document
declares grasp_observation_table unit `unitless` with a conventions note mapping
it to the contract unit slot_f32 (dimensionless float32 delivered slots); N*s
parses canonically. The contract's unit rows are preserved verbatim in
result.json and the report; nothing is re-declared away.

## 9. Result and evidence laws (standing format)

- result.json: chimera.compiler_packet_result.v1 with ALL required keys
  (packet_id, criteria_sha256 = f3dbf093..., generated_utc,
  worker_arrival_id = wk-membrane-hand, per_test_results for the four test ids,
  receipts, fixture_based = true, named_debts_encountered = NB-01..NB-05 rows,
  deviations, claims, sergeant_review_required = true).
- per_test row verdicts PASS|FAIL|NOT_RUN; missing/skipped/unrun stated
  explicitly. A PASS row cites the runner receipt (job id, state PASSED,
  cleanup_verified true, artifact sha256 map).
- Every load-bearing artifact's sha256 recorded in membrane-hand/EVIDENCE.md.
- Required campaign evidence anchored through anchor.py into the sealed
  evidence store BEFORE registry reference.
- I never approve my own verification: Sergeant review is requested through the
  Lieutenant; publication stays with the Lieutenant.

## 10. Open items for the Lieutenant (blocking nothing else)

1. The pin itself (and whether it is a published commit; package base then =
   that commit; reads must carry the sealed hashes of section 2).
2. The section 7 scoped-spec-conformance resolution (accept as disclosed, or
   route a validator-class extension to the mathspec lane).
3. Registry claim/card materialization (R3) stays a lead action per the packet
   resume_state; I have not claimed anything in the registry.
