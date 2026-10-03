# DEV RUN REFUSALS — SUPPORTED-LANDING-IMPL-20261002 (preserved, never deleted)

Every dev-run refusal and every failed arm of this card is recorded here
with its runner receipt identity (honest negatives; failure captures use
the same declared views as success captures). Format per entry: runner job
id, slot, exit code, receipt sha256, what fired, and the disposition.

## Entries

(dev calibration pending — entries are appended as dev runs execute)

## 1. Dev run e662d53d583d4a589224ba7279db056a (2026-10-02)

- Command: `C:/Python314/python.exe -B
  tools/monkey_campaign/contributions/SUPPORTED-LANDING-IMPL-20261002/run_battery.py`
  through the sealed runner (package base 10b05f9f, dev snapshot
  `272178eb1c314954840f4049b5a26164`).
- Exit 4, state REFUSED_HARNESS, runner receipt sha256
  `6c88df061caedeb14ff8fcf0a823699770ee52355e472cdf17b6796160b4ddc7`
  (log tail), refusal receipt
  `outputs/landing_experiment_receipt.json` sha256
  `480a9718e8acd6eecb0e238094c87bcd56f4bcb0680b364941c1e0b85e48193c`.
- Refusal: `threshold_pin_mismatch:impact_jn_scene_ns,release_bar_ns` —
  the pin gate refused two presence entries whose float literals do NOT
  exist in the pinned bytes (the committed prereg carries the FORMS
  'share*|vn_pre|' and 'share_kg * 1e-10', never the products
  9.847276038 / 3.3459993333333336e-10). THE GATE CAUGHT A REAL AUTHORING
  DEFECT (an over-broad presence list). Disposition: the presence list
  corrected to the prereg's own refinement law (presence applies ONLY
  where the value exists in pinned bytes); both values remain DECLARED
  DERIVATIONS recorded in every receipt; this entry preserved.

## 2. Dev run 1b74161fba6d4dafac3aa81bc2f14335 (2026-10-02)

- Same command; dev snapshot `6005bc1fb1e74205915a94903f9c680a` (manifest
  `30321d52c014cb98889a6650621c2951c2848b1a1c170bf06ff1d28e1201eaab`).
- Exit 4 (unhandled observer_drift:header). THE PHYSICS RAN CLEAN through
  both observed runs (the 141-tick floor scene included); the prefix
  cross-check refused because cross_check_rows requires FULL header
  equality while the two runs' headers legitimately differ in the declared
  scaffold field release_ticks (reference 59 vs landing scene 121).
- Disposition: the prefix comparison now asserts header equality
  field-by-field with the ONE declared exception 'release_ticks' and
  keeps the row-level key law of cross_check_rows verbatim; any other
  header difference still refuses (observer_drift). Preserved.

## 3. Dev runs 279f3818ab18412a8ad933268e568dd6 and 3ac03b1cfb554ffc8b070fd3d14b45d5 (2026-10-02)

- Exit 1, KeyError 'observer_cross_check' in P1 evidence assembly: the
  landing arm record did not carry the field its own check read. Fixed by
  declaring the field on the arm record at construction. job 279f3818 also
  documents a dispatch defect on MY side: the runner was invoked with a
  stale sealed snapshot (name-sorted instead of newest) — the run was
  repeated with the newest snapshot. Preserved.

## 4. Dev run 7dc2e6ddb181456d809328b0eb136bcc (2026-10-02)

- Exit 1, ValueError 'Out of range float values are not JSON compliant:
  inf' serializing P3 evidence 'worst_floor_gap_m'. ROOT CAUSE (real
  authoring defect caught by the checks): run_landing passed the
  scene-extension shim to the sealed observer as the cso (observation
  seam) argument and the REAL solver as the lc argument, so the declared
  floor body never entered any solve_tick — the pads fell through the
  declared floor plane with zero floor records (the shim's captured
  side channel held 0 ticks). A local authoring probe reproduced the
  scene and confirmed the correct wiring: with the shim passed as the
  observer's lc argument, the impact fires at release tick 60 (jn
  9.847276037952213 N*s == the derived share*v(60) class), the trailing
  pads at release tick 61 (inside the declared window {59, 60, 61}), the
  steady support is the weight-share impulse per channel, and the rest
  velocities are exactly zero. Fixed in run_landing; this entry preserves
  the tunnel-through signature that the wiring defect produced.

## 5. Dev run 405ab2c310c2444fa630fb86e2915d1e (2026-10-02)

- Exit 1, IndexError inside the SEALED rfa.release_account (acct_rows
  indexed by absolute tick). THE SEALED LAW IS NEVER PATCHED: the caller
  must hand it rows/acct_rows from tick 1 (its own indexing law, the K02
  invocation pattern). Fixed the slice to arm['rows'][:fall_end].
  Preserved.
