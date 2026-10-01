# REPORT — MAT2-W08 verify commanded start, stop, speed, and heading

Generated from the receipts by `make_report.py` (no hand-transcribed
numbers; `lint_report_numbers.py` proves every numeric literal traces
to a bound artifact). Composed against CARD_STARTER v5; house
standards `IMPLEMENTER_CHECKLIST.md` (G1-G9) + `TOOLKIT.md` (P1-P9)
cited at the candidate commit.

## done_when verification (verbatim clause -> evidence)

done_when (verbatim): "Frozen command sequence satisfies tracking
and physical-stability limits"

| clause | outcome | evidence |
|---|---|---|
| frozen command sequence | MET | the frozen input script (prereg 4.1) ran through the PINNED U01 port: 403 CommandRecords v1, v in [0.000000, 0.763625] m/s, |yaw| <= 1.6 rad/s, interval diffs exactly [15] ticks, decay deadline honored, idle silent, sink only-emits (P2); the wrong-key probe script is a declared variant (prereg 4.4) |
| satisfies tracking limits | MET | start: onset 1 tick(s) (<= 15), segment-end v 0.745770 m/s within the derived range [0.726509, 0.803816], residual 0.017855 <= 0.040191 m/s (P4); turns: in-range yaw residual <= 1e-6 rad/s (measured max 0.000000011921), seam-max achieved 1.0 rad/s with named saturation, declared residual 0.6 (P5); decay step strictly decreasing (P6); stop: v at the settle end 0.313959 m/s inside the derived range [0.299320, 0.339577] (P7) |
| satisfies physical-stability limits | MET | every tick of the horizon: |v| <= 2.977443609 m/s (derived envelope), contact floor min 4 (bar >= 2), no non-finite state, intervention none, x never decreased, pad gaps all > 0 (P8); the state chain is continuous and the R1/R2 zero-control is bit-identical (no hidden reset) |
| without pose bypass | MET | the port's sink log contains only emit(CommandRecord) calls; the adapter projects records into the manifest limiter's 8-channel setpoints (all within bounds, every clipped channel named, 61 floor rows and 30 seam-max yaw rows carrying their named saturation); the scene's step(applied, saturation) is the only motion path |
| wrong command response (falsifier class MUST fire) | EXECUTED | R3's wrong-key script diverges from R1 at exactly tick 5431 (prefix identical through 5430), with physical separation 0.747213 vs 0.529942 m/s beyond the derived brackets [0.734785, 0.549869]; the R1/R2 zero-control is bit-identical (P9) |

The observation clause — "Existing 20 Hz speed/heading seam is
retained" — is executed, not asserted: the port's own pinned
InputMapper produced every command at its frozen interval
(exact [15]-tick spacing measured on the records), the yaw demand rode
the port's own rate law (counts*sens/interval), and the consumer-side
expiry contract (named for this card in the pinned mapper) is
implemented and bite-tested (FB10).

## Identity

- Card MAT2-W08 (planning id W08, wave 8, slot 2), agent
  `wk-w08b-arrival-1`, attempt `c38b22e505874601aa3f3a3ba9035e4d`.
- Criteria sha256 `f38c2c96ef22cca080accba4b71b3370ca5b0272b824975c650cd543db9821ea` (join == registry read-only re-read; card
  state at load time: REVIEW, registry revision 1667).
- Base: `8b285ee4301a8ed42be54a1924af5db019f9fb20` (the file package's base; the MAT2-W07 merge, PR #301).
- Preregistration sha256 `00a04e08411ed079aee9e0ef43f9221c69abc84612f66311e4db4822f6c8412a` (committed separate-first BEFORE any
  sealed run — the M03/P04 law; the dev-run refusal codes are
  recorded in `DEV_RUN_REFUSALS.md` (the frozen prereg narrates the
  amendments and names the P4 segment-range refusal).
- Certificate: the pinned W04 certificate re-validated by the
  machinery's own validator: VALID; deploy gate ALLOW.
- Physics build: `cpu-walk-scene-build-N`, params sha `3e770bef8b8707c9`, timestep 0.0033333333333333 s.

## The gate path (the frozen line runs through the certificate machinery)

| stage | outcome |
|---|---|
| validator | VALID (violations: 0) |
| deploy gate on the certified tuple | ALLOW |
| frozen loader identity | manifest_hash `9ca7e976dfb0dedd`, weights `5fb2b7857d872fcc` bit-for-bit |
| build identity | `cpu-walk-scene-build-N`, scene module sha `ab4257024df63d97` |
| trained bundles loaded | none (the gate BLOCKs them; W07's executed
|  discrimination is pinned and carried) |

## The command-verification table (C11/C12; named variables)

| command | issued (tick) | tracking | stability | wrong-command probe |
|---|---|---|---|---|
| start / ceiling hold | 300 | onset 1 tick(s); residual 0.017855 <= 0.040191 m/s; band entry measured at tick 3175 (recorded informationally) | P8 bars green every tick | onset <= the 15-tick hold |
| turn left in-range | 3600..4035 | yaw residual max 0.000000011921 rad/s (bound 1e-6) | P8 bars green | FB7 bite fires on mirrored sign |
| turn right in-range | 4050..4485 | yaw residual max 0.000000011921 rad/s (bound 1e-6) | P8 bars green | FB7 bite fires on mirrored sign |
| turn left seam-max (+1.6) | 4500..4935 | achieved 1.0 rad/s, residual 0.0 (the declared saturation residual 0.6; limiter clip NAMED on channels 0,4 at every tick) | P8 bars green | the saturating row is itself the named clip |
| speed step (decay mid sample) | 5415 (one block) | MEASURED demand 0.55744625 m/s at tick 5415 (prereg nominal 0.57271875 m/s; deviation flagged — see the receipt's deviation_cause); v 0.745540 -> 0.742367 m/s, strictly decreasing above the measured band top 0.586786 | P8 bars green | P9 class at the stop boundary |
| stop / zero-advance floor | 5430 (+ live zero 6000..6885) | v at the settle end 0.313959 m/s in [0.299320, 0.339577]; entry measured at tick 7910 (recorded informationally) | P8 bars green; stride saturation NAMED on channels 1,5 at every zero/floor row | P9 MUST-FIRE injected at this boundary |
| wrong-command probe (R3) | injected 5430 | clean 0.529942 vs wrong 0.747213 m/s at tick 5999 (brackets 0.734785 / 0.549869) | zero-control bit-identical | FIRED at 5431 |

## Seam laws retained (C12, the port's own frozen semantics)

| law | measured |
|---|---|
| interval (50 ms = 15 ticks) | contiguous record diffs exactly [15] |
| command domain | v in [0.000000, 0.763625] m/s; |yaw| <= 1.6 rad/s |
| release decay deadline | zero demand at tick 5430 <= bound 5437 |
| idle silence | decay->S gap records: 0; post-S records: 0 |
| no-teleport | sink calls only emit: True |

## Falsifier outcomes (each class -> executed detector)

| class | outcome |
|---|---|
| sliding/penetration | no x decrease, no nonpositive gap on any tick |
| unsupported propulsion | envelope max |v| <= 2.977443609 m/s on every tick |
| hidden reset | continuous state chain; R1/R2 zero-control bit-identical |
| wrong command response | FIRED (P9, table above) |
| diagnostic/clean state divergence | both capture bands render from ONE recorded state per frame (state_sha256 identical per row-pair); the validator's clean-view check passes |

## Named missing (recorded, never fabricated)

- **N1_vertical_fall_channel**: NAMED_MISSING (surrogate scope; trip channels measured: True)
- **N2_c09_ledger_and_settle_limits**: NAMED_MISSING for the C09 ledger/episode caps; P06 stability-settle-vy-ms 0.05 m/s quoted and NOT applicable to the declared bounded floor band (the plant's minimum advance exceeds it by declaration); P06 simulation-tick-hz 300 == the scene dt (verified)
- **N3_product_engine_live_control_path**: carried NAMED_MISSING from the pinned spike evidence
- **N4_trained_bundles**: BLOCK at the gate; nothing trained loaded

## The capture (profile walking/motion)

- 60 frames at the declared command-sequence ticks (8 event anchors +
  52 uniform samples; the real per-frame tick list is in the
  manifest), each a sheet of the three profile views, diagnostic band
  over clean band, rendered from the SAME recorded state; FFV1
  lossless (`-c:v ffv1 -level 3 -g 1 -fflags +bitexact`), G4 decode
  pixel-exact on all 60 frames, order-sensitivity pass; validator CAMERA_METADATA_STRUCTURE_ONLY
  (True; visual_acceptance stays False — independent visual review is
  the Sergeant's).
- Capture sha256 `3d991a8b7a0af276`; trace sha256 `239624319fc0dda8`; subject receipt
  `capture/capture_receipt.json` sha256 `c5e23720d9434750`.

## Accounting

- Named checks: 19 executed, 0 skipped (test_w08_commands.py (unittest discover -p test_*.py)).
- Runs: R1/R2 at 10500 ticks (zero-control bit-identical: True), R3 at 6000
  ticks; R1 final state `2ade03d79d565ff9`; 403 port records, 404 adapter decisions.
- Dev-run disclosure: the prereg was amended in five recorded editing
  rounds BEFORE any sealed run; all refusal codes with their
  derivations are recorded in `DEV_RUN_REFUSALS.md` (the frozen
  prereg narrates the amendments and names the P4 segment-range
  refusal; it does not repeat the other three codes).

