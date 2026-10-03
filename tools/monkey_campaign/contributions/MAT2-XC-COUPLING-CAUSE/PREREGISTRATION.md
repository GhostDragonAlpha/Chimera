# PREREGISTRATION (DRAFT) — card MAT2-XC-COUPLING-CAUSE / lane coupling-cause: the controlled comparison isolating the gait-phase divergence cause

STATUS: DRAFT for Lieutenant commit (separate-first law; the x05 lane
precedent). These bytes are NOT frozen until the Lieutenant commits them
ALONE on the lineage through the publication owner and hands back the
commit sha (the pin). Phase B (the gated run) starts ONLY after that
handoff. Every receipt of this card will embed `preregistration_sha256`
of the COMMITTED bytes and refuse any mismatch.

- Card MAT2-XC-COUPLING-CAUSE (the named follow-up to the frozen X05
  finding), worker `wk-coupling-cause`, session under the main Lieutenant.
- Write scope: the NEW lane dir
  `E:\ChimeraWork\monkey-coordination\coupling-cause\`; the Phase B
  contribution dir `tools/monkey_campaign/contributions/MAT2-XC-COUPLING-CAUSE/`
  in a pinned file package.
- NO_WORKTREES law: pinned file packages only; CPU runs only through
  `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`;
  no Git clone, worktree, ref or index mutation by this lane. A package
  seal does not substitute for the required prereg commit.
- GOVERNING RULING (Captain, carried in the merged record): "Do not claim
  that gait responds to speed until a controlled comparison isolates that
  causal relationship." Every determination of this card is at
  isolated-cause strength only; the phrase "responds to speed" is
  forbidden output short of the ISOLATED_VELOCITY_COUPLING verdict.

## 0. The frozen basis this prereg is computed from

The following identities were byte-verified at design time by this lane
(sha256 recomputed from the sealed job and the anchored store; the a12
job receipt and P01/P02 driver records match the `verify_inputs_x05.py`
pin constants exactly):

- a12 (WK-LATENCY-20261002 attempt 12): job `ca111cdc917e420eb78c41339d88c41b`,
  receipt sha256 `f85c0447ce0ff8cf9b27840dca31dd2dc4b309212171724d96c20359a761ef24`,
  sealed manifest `4d7bb0ae26a063a7f0a16823d6332de7f8e7d01176d4b0be2c15dc89d9b09fd9`,
  base `45fc250582785bdcf125d9a09c74a39092a57c15` (amendment A3);
  driver_pair_P01_BRAKE-SHORT.json sha256
  `5a3ca1be4778a60d9c99ec424b3047c503f473fe665ebb1e8df079f7f77f14fb`;
  driver_pair_P02_BRAKE-LONG.json sha256
  `d63301e76da53a2ec3ae6d368a3439dbca2b78ed65281a347f58f12c90dcbc48`.
- X05 (MAT2-X05, merged `ea1b7e7e`): job `2c452aeed4d54ce6a04f5de13ceade2a`,
  sealed manifest `5f8b05e841e5f7d5bd7a98772c21102e74d3483e0e30df340f32da0bc26b27db`;
  anchored store driver_pair_P01_BRAKE-SHORT.json sha256
  `31e4d11eec3f867ab044ddd97b6de1c54a5e82daf4fd055ecad696913eb3e918`;
  pins_x05.json sha256 `bdaeb0bd254d0f562ac8a64b1bcd9a4a6eb64f4877f81d36889fa3ee81f16920`.
- a9 (attempt 9, the A2 S-press inertness proof): driver_pair_P01
  sha256 `43d659afc354cb6e16df7ea92c9a3db6e7e3c843d12804e7a5f908c2b45d36ad`.

Verified facts (reproducible from those bytes):

1. Both lines pin SEED 20260920 and the SAME window (presented ticks
   4365..4665 step 15; 21 rows) and the SAME sealed probe classes
   verbatim (release W at T_in(n)=4351+(n-1); re-press +150 ticks SHORT /
   +300 ticks LONG on the 300 Hz injected clock; the +150 ms/+300 ms
   unit reconciliation rides the seal as in X05).
2. a12 P01: phase identity 21/21, com_v divergence 20/21 (P02 mirrors:
   42/42 and 40/42 over the two records). x05 P01: phase identity 4/21,
   first divergent row t4425, com_v divergence 20/21.
3. Row 0 state identical across all four arms
   (`79e3aaa7...`); from row 1 the CONTROL arms differ ACROSS lines by the
   constant symmetric offset (x05 B minus a12 B: left +0.200000,
   right -0.200000) with control com_v differing ~4.3e-4 m/s.
4. Both lines internally deterministic (per-tick/state-chain receipts;
   X-P1a).

Fact 3 elevates HARNESS/SCENE IDENTITY to a named fifth candidate (the
frozen candidate list named regime/seed/window/mechanism only). The
correction that the "brake vs release" class framing dissolves at the
record level (both cited lines ran release classes; the S-press class was
the attempt-9 probe, proven inert) is recorded; the candidates are
retained with the regime arm defined by the MEASURED velocity band.

## 1. The arms (one sealed package; ONE scene-module identity, ONE build id, ONE seed, ONE harness form per arm; one manipulated candidate each)

Group A — harness/scene identity (runs FIRST; gates interpretation):
- A1a: the WK-LATENCY Phase B harness configuration (U07
  `controls_harness` import form) over THIS package's pinned scene bytes,
  control arm only, sealed window.
- A1b: the MAT2-X05 harness configuration (W10 `run_commanded` loop form)
  over the SAME pinned scene bytes, control arm only, sealed window.
- A1 pass law: A1a and A1b control arms bit-identical (all 21 rows:
  state_sha256, phases, com_v, com_x). On failure: record
  `xc_harness_form_offset` with the per-row detector below; the within-line
  instruments remain the only interpretable comparisons; arm groups D/E
  still run but the determination caps at CAUSE_NOT_ISOLATED unless the
  offset pattern is itself the isolated cause (see the matrix).
- A2 (no new physics): the ±0.2 offset detector on the EXISTING sealed
  records: for each row i, `d_left(i) = phase_left_x05B(i) -
  phase_left_a12B(i)` and `d_right(i)` likewise; the offset pattern is
  `EXACT_SYMMETRIC_020` iff `d_left == +0.2` and `d_right == -0.2`
  (exact float equality, tolerance 0) on every compared row; any other
  value is recorded as a finding (`xc_offset_pattern_deviation`).

Group B — seed held constant:
- SEED = 20260920 in every arm of every group (identical seeds across
  both lines' configurations). Each arm is re-executed once in the same
  package; bit-identity is REQUIRED (the sealed X-P1a form; receipt
  per arm). Any mismatch: finding `xc_determinism_breach`; lane stops
  as a preserved failure; no determination.

Group C — window held constant; robustness scan analysis-only:
- The sealed window in every arm. The robustness scan recomputes every
  statistic over window starts {4365, 4380, 4395} on the SAME recorded
  rows (no new physics). Report all three; the determination uses the
  sealed window; a determination that flips between window starts is
  itself the finding `xc_window_sensitive` (window not excluded).

Group D — regime (the measured speed band; the release-decay channel):
- D1 SHORT: re-press +150 ticks (the sealed class, verbatim).
- D2 LONG: re-press +300 ticks (the sealed class, verbatim).
- D3 DEEP: re-press +600 ticks (NEW; declared here first).
- D0 control: holds W (no release). N pairs: 5 per class (odd n SHORT,
  even n LONG per the sealed interleaving; DEEP on n in {11..14} + 1
  control replication), T_in(n) = 4351 + (n-1), horizon 4800 ticks.
- Measured band per class: the minimum com_v over the window rows and
  the com_v time series (recorded per arm).

Group E — mechanism (the command channel at matched velocity):
- E1: the W-release channel (= D1 SHORT, shared; no duplicate run).
- E2: S-press under held W (the sealed A2 class verbatim: press S at
  T_in, release S at T_in + 150 ticks), 5 pairs, same harness.
- E3 matched-band pair: the S-press hold duration is declared at run
  configuration time as the smallest value in {50, 100, 150, 200, 300,
  450} ticks whose achieved min com_v over the window is within
  +/-0.01 m/s of E1's achieved min com_v (the band-match tolerance
  frozen here; chosen from the recorded E2/D1 rows BEFORE any E3
  physics runs — the selection step is itself recorded with its inputs).
  If no listed duration matches the band, E3 is recorded NOT_ACHIEVABLE
  and the E determination degrades to `xc_band_match_unachievable`
  (a finding; the matrix row is then not claimable).

## 2. The predictions (which pattern of results isolates WHICH cause)

- P-HARNESS (A1 fails bit-identity AND A2's offset pattern replicates
  between the two harness configurations over the same scene bytes):
  the cross-line discrepancy is the harness/scene class. If additionally
  D/E show within-line phase identity at every depth in both channels
  (identity 21/21 per pair), the determination is
  ISOLATED_HARNESS_SCENE: the X05 divergence was the scene/harness
  version class; the a12 inert-phase result describes the certified
  scene; the coupling card closes ABSENT-WITH-CAUSE (the cause named and
  pinned).
- P-COMMAND (A1 passes; E2/E3 show NO phase divergence at any row while
  E1/D arms show the divergence; bands matched within tolerance):
  ISOLATED_COMMAND_CHANNEL — the phase law consumes the W-key/command
  record channel (the release event / its decay law), not the measured
  speed. The coupling follow-up stays closed; the finding names the
  channel.
- P-VELOCITY (A1 passes; in D, the first divergent phase row tracks the
  last row where com_v is inside the cruise band, monotone in depth
  ordering (SHORT < LONG < DEEP first-divergence tick), replicated in
  E2/E3's channel at matched bands):
  ISOLATED_VELOCITY_COUPLING — the only verdict that licenses the
  certified-line coupling follow-up card (visible motion beyond the
  landmarks through a phase law consuming measured speed). Even then,
  the implementation is a NEW prereg-first card; this card renders
  nothing.
- P-NONE (any other pattern, including mixed, band-unmatched, or
  window-sensitive outcomes): CAUSE_NOT_ISOLATED — the frozen X05
  observational finding stands unchanged; the coupling card closes
  ABSENT-UNVERIFIED with this prereg's arms recorded as the named
  follow-up; no velocity-coupling phrasing anywhere.

## 3. The falsifiers (declared before any run)

- F1 (determinism): any same-configuration re-execution mismatch
  (bit-level) falsifies the seed-constant premise; lane stops.
- F2 (control invariance): any probe arm whose CONTROL counterpart shows
  a phase change falsifies the within-line isolation premise for that
  pair (finding; the pair is discarded from determination inputs,
  never tuned).
- F3 (band match): an E3 arm whose achieved band violates the +/-0.01
  m/s match falsifies the matched-band premise for the P-COMMAND row
  (the row degrades to CAUSE_NOT_ISOLATED; recorded, never re-tuned).
- F4 (onset law): a P-VELOCITY claim where any pair's first divergent
  phase row precedes its first out-of-band com_v row falsifies the onset
  law (the claim is refused; CAUSE_NOT_ISOLATED stands).
- F5 (instrument reuse): any statistic not computable from the sealed
  row schema (tick, phase_left, phase_right, com_v_m_s, com_x_m,
  state_sha256) is out of scope; adding channels mid-lane requires a
  prereg amendment through the publication owner BEFORE the affected
  runs.

## 4. The measurement (reuse, do not rebuild)

- The per-frame phase records: the window rows exactly as both sealed
  instruments produce them — `tick`, `phase_left`, `phase_right`,
  `com_v_m_s`, `com_x_m`, `state_sha256` — 21 rows per arm, no new
  channel, no re-derivation of the phase law.
- Statistics (exact definitions, frozen):
  - `phase_identity_count(pair)` = number of window rows i where
    `phase_left_A(i) == phase_left_B(i)` AND `phase_right_A(i) ==
    phase_right_B(i)` (exact float equality, tolerance 0);
  - `v_divergence_count(pair)` = rows where
    `com_v_m_s_A(i) != com_v_m_s_B(i)`;
  - `first_divergence_tick(pair)` = the first window tick failing phase
    identity;
  - `control_offset(a,b)` = per-row phase differences between the named
    control arms (the A2 detector above);
  - `band(arm)` = (min com_v over window rows, the com_v series);
  - determinism: per-arm re-execution bit-identity receipts.
- Every receipt embeds: the base identity, the preregistration_sha256,
  the sealed manifest, the per-arm input record shas, the row tables,
  the statistics, the findings, and the determination or its refusal.

## 5. The determination law

Determinations are ONLY the four named verdicts (ISOLATED_HARNESS_SCENE,
ISOLATED_COMMAND_CHANNEL, ISOLATED_VELOCITY_COUPLING, CAUSE_NOT_ISOLATED)
under the matrix in DESIGN.md section 4 and the predictions in section 2.
The phrases "responds to speed", "gait consumes velocity", and every
other causal phrasing are forbidden in any receipt, report or commit
message short of ISOLATED_VELOCITY_COUPLING (the X05 r1 reviewer-grep
law carries over). The frozen a12/X05 records are CITED, never
re-claimed; X04/X05 verdicts are not re-opened; no byte of any other
contribution changes.

## 6. Run discipline (Phase B, after the pin handoff only)

- One sealed package pinned to the COMMITTED prereg commit; ONE sealed
  command runs the arms in the declared order (A, then B determinism
  receipts interleaved per arm, then D, then E with the E3 selection
  step recorded before its physics); findings recorded as findings;
  failures preserved; refusal on any pin mismatch; evidence anchored
  through anchor.py before registry reference.
- Budget: bounded by the X05 sealed-run precedent (one CPU job class,
  the four-slot runner, declared outputs only).
