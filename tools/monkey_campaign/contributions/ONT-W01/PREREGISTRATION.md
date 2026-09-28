# ONT-W01 PREREGISTRATION — frozen before probes

- Card `ONT-W01` (planning `W01`), kind `implementation`, verification profile `records`
  (offline; subject "Pinned definitions, ledgers and numerical evidence"; numerical
  evidence required; falsifier: "Missing identities or a claimed pass unsupported by
  records fails; a screenshot is not a substitute").
- Attempt `01a01bf2759648f687e7eb7113998f23`, agent `arrival-195e6b7256e942988473e20a03dce315`,
  branch `branch-7` (base `c525b82c7c3ce0128565424764293a3c85811ab3`),
  criteria `c42bd4f9ce228ebddcb1be6c87b261979c8a38987ff3d5e74ad37536f397be24`,
  scope `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`.
- This file is committed BEFORE the verifier is written and BEFORE any probe runs.
  Amending after first measurement is forbidden; any amendment must be recorded here
  with its pre-measurement justification.

## Statement (what is being qualified)

done_when: **"Frozen entry-state and event traces satisfy the existing CPU/GPU
acceptance bar"** (C09: CPU/GPU parity and time stepping; verification inputs:
"frozen entry states, operation order, precision, event rules").

The qualification is records-class: the pinned acceptance records — the walk-trace
pairs, the substep census drill pairs, the tick-41 regression fixture, the tie-v2
replay captures and the frozen bars JSON — are re-verified against their claims by an
independent oracle (deterministic byte/token comparison of git-object-pinned bytes),
not by re-running physics. No GPU work, no training, no engine builds, no source
edits outside the contribution directory.

## Reconciliation state this qualification builds on (reused, not re-derived)

The tick-3 discrete forelimb parity defect was named by closeout-3 (`7a845267`:
"a fore-limb discrete event ... inside tick-3's substep-2->3 advance with a BIT-EXACT
entry state ... SUBPRE t=3 sub=3 is the first diverging census record") and fixed by
closeout-4 pairs 4-8 (`2dee187d`, `3ab21e5f`: crossing-bisection end-state evaluate;
end-state save vs scan clobber; per-point friction row; swallowed-require guards;
poscorr gram stride+operands). The P02P03 lineage reconciliation (`8feea42a`,
`tools/monkey_campaign/agents/P02P03/report.md` §2) rules W01 **CLOSED** by those
receipts with the frontier later strengthened (60 states `77023970`, 66->71
`37ab0c8f`, 73->74 `2c1dc8f2`; bit-exact through aligned state 74 with a named
cpp-vs-host 1-ulp FK class at `b643a850`). The tie-v2 battery (`9376c3d8` prereg,
executed per TIE2 report `055d6c05`) adds: host replay walks past tick 41 to t=100
rc=0; host-vs-GPU v2 parity on every FULL state t=1..43. The class-41 contact-residual
knife (`g0=-6.9e-18`), the GPU legs (Q1/Q2) and the anchor-version decision are
**charged to W03** by that same reconciliation — this card inherits them as named
boundaries, not as its own open work.

## Pinned records (single evidence source)

Git tag `archive/20260925/agent/typeb-gpu-finish-20260922`, commit
`a62b286effa27ee2db7bbcb65507a2ac45ad0d0c` (SHUTDOWN CHECKPOINT), plus defect-era
commit `7a845267` (closeout-3). All paths relative to that commit:

| id | path | role |
|---|---|---|
| R-state-host | `tools/science_funnel/typeb_gpu/co8_t41_fixture/state_t40_host.txt` | frozen host entry state (FULL t=40) |
| R-state-gpu | `tools/science_funnel/typeb_gpu/co8_t41_fixture/state_t40_gpu.txt` | frozen GPU entry state (FULL t=40) |
| R-state-cpp | `tools/science_funnel/typeb_gpu/co8_t41_fixture/state_t39_cpp.txt` | frozen C++ aligned state (FULL t=39) |
| R-scene | `tools/science_funnel/typeb_gpu/co8_t41_fixture/scene_sha256.txt` | pinned scene identity |
| R-cp45 | `tools/science_funnel/typeb_gpu/cp_walk45.txt` | C++ reference walk, FULL t=0..44 |
| R-hl45 | `tools/science_funnel/typeb_gpu/hl_walk45.txt` | host replay walk, FULL t=1..48 |
| R-csub5 | `tools/science_funnel/typeb_gpu/csub_t5.txt` @ `7a845267` | C++ substep census, ticks 0..4, defect era |
| R-ksub5 | `tools/science_funnel/typeb_gpu/ksub_t5.txt` @ `7a845267` | kernel substep census, ticks 0..4, defect era |
| R-csub41 | `tools/science_funnel/typeb_gpu/csub41L.err` | C++ census, post-fix (regenerated at `3ab21e5f`) |
| R-ksub41 | `tools/science_funnel/typeb_gpu/ksub41N.out` | kernel census, post-fix |
| R-hlv2 | `tools/science_funnel/typeb_gpu/co8_hl_v2.out` | host replay under tie-v2, to t=100 |
| R-hlpre | `tools/science_funnel/typeb_gpu/co8_hl_full6.out` | host replay pre-v2 |
| R-gpuv2 | `tools/science_funnel/typeb_gpu/co8_dll_v2b_120.txt` | GPU v2b capture, FULL t=1..43 |
| R-bars | `tools/science_funnel/validation/typeb_gpu_fullport_20260921/bars_split_b32.json` | frozen bars measurement |

Comparison law (frozen): state records are compared as ordered `key=value` token
streams after the `FULL t=N` prefix; census records are compared positionally on the
physics keys only (`q\d+`, `v\d+` for SUBPRE/SUBFULL; `tau\d+` for TAUFULL) plus the
`sub` ordinal, because the kernel-side drill prints extra instrument keys
(`batpost`, `w2`) the C++ side does not have. Equality is exact string equality of the
tokens (bit-level for the printed doubles); no tolerance is introduced anywhere.

## Predictions (each from a pinned claim; the probe verifies the claim against bytes)

- **P1 identities.** The tag resolves to `a62b286e`; commits `7a845267`, `2dee187d`,
  `3ab21e5f`, `77023970`, `37ab0c8f`, `2c1dc8f2`, `b643a850`, `9376c3d8`, `ef3f3554`,
  `055d6c05`, `8feea42a` resolve; the pinned bar sentences are present in their
  messages: `2dee187d` contains "BIT-EXACT THROUGH 41 ALIGNED WALK STATES";
  `3ab21e5f` contains "census 20/20 SUBPRE + 20/20 TAUFULL + 20/20 SUBFULL" and "the
  entire tick-3 and tick-41 interiors line-identical"; `055d6c05` contains "HOST
  REPLAY WALKS PAST TICK 41 to t=100 rc=0" and "host-GPU v2 parity t=1..43";
  `8feea42a:tools/monkey_campaign/agents/P02P03/report.md` contains the W01 verdict
  section ruling CLOSED.
- **P2 frozen entry states.** sha256(R-state-host bytes) == sha256(R-state-gpu bytes);
  R-state-cpp equals R-state-host except the tick label (39 vs 40); the state bodies
  equal the corresponding walk-pair lines (R-cp45 FULL t=39, R-hl45 FULL t=40);
  R-scene == `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342`.
- **P3 walk-pair parity incl. the tick-3 window.** R-hl45 FULL t=N equals R-cp45
  FULL t=N-1 exactly for every N=1..41 (41 aligned states); the tick-3 window
  (N=1..4) is inside the equal set; the first divergence, if any, is at N>=42.
- **P4 defect-era record (the named tick-3 defect is real in records).** At
  `7a845267`, the first positionally-diverging census record between R-csub5 and
  R-ksub5 is `SUBPRE t=3 sub=3`, with all earlier census records bit-exact on physics
  tokens.
- **P5 post-fix census.** R-csub41 and R-ksub41 each carry exactly 20 SUBPRE + 20
  TAUFULL + 20 SUBFULL records; pairwise physics-token equality holds for all of them
  (the "census 20/20" claim); 0 divergences.
- **P6 v2 host replay.** R-hlv2 ends with exactly
  "tick 100: y=0.215657301 vx=0.664807 rc=0 adv=7 refused=0 ticks=100", contains no
  `REFUSED` line, and carries FULL states t=1..100.
- **P7 pre-v2 vs v2 host.** R-hlpre and R-hlv2 FULL states are identical for t=1..40
  and the first divergence is at t=41.
- **P8 host-GPU v2 parity.** R-gpuv2 FULL states equal R-hlv2 FULL states for
  t=1..43 after CR normalization (the capture's documented `\r` artifact), 0 differing
  ticks.
- **P9 frozen bars record.** R-bars parses and reports: freefall `parity_pass==true`
  with `measured_g==9.806650000000689` and `err<=1e-9`; stand `parity_pass==false`
  with `max_scaled_diff==0.9511245759469239`; nominal `horizon==40`,
  `refused_class==5`; survival `seeds==64`, median(horizons)==40.0. The RED bars are
  recorded as measured and attributed per the pinned reconciliation (W03's charged
  residual), never silenced.
- **P10 mutation controls.** In synthetic fixtures (never the real repo objects),
  flipping any single compared byte flips the corresponding check to REJECT; the
  verifier also REJECTS when a pinned record is absent (missing-identity falsifier).

## Falsifiers (frozen decision rule)

- **F1 missing identity:** any record or commit the claims depend on fails to resolve
  and is not named as a finding -> qualification REJECTED.
- **F2 unsupported pass:** any prediction P1..P9 whose check cannot be re-derived from
  the pinned bytes fails -> qualification REJECTED for that clause; the done_when is
  only claimed for clauses whose checks PASS.
- **F3 screenshot substitute:** no visual artifact is offered as evidence; the
  profile is records and the receipt labels the evidence class accordingly.
- **F4 tolerance creep:** any comparison introducing a numeric tolerance instead of
  exact token equality -> REJECTED by construction (the comparator has no tolerance
  parameter).

## done_when decision rule (frozen before probes)

The done_when clause is declared **satisfied-by-records** iff P1, P2, P3, P5, P6, P7,
P8, P9 PASS and P4 confirms the defect-era record; the clause's subject is the scoped
tick-3 forelimb event and its event traces under the existing acceptance bar, NOT the
walk-level GPU bars beyond the recorded measurements (stand/C1/C2 RED residuals are
W03's charged scope; the live GPU qualification runs Q1/Q2 remain queued there). Any
failed check is reported as a finding, never tuned, retried with a changed rule, or
absorbed.

## Out of scope (named, not silently missing)

Live GPU re-runs (TIE2 Q1/Q2), the C3 clean-window re-measure, the anchor-version A/B
decision, the C++-reference leg carrying the tie, trained-walking acceptance (W05+),
and the W04 mass-denominator binding. Each is already owned by a named card/receipt
per the P02P03 reconciliation and the TIE2 report.
