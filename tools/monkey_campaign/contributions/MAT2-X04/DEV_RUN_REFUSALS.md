# DEV_RUN_REFUSALS — MAT2-X04 (honest negatives; never deleted)

Prereg section 9 law: dev-run failures and refusals are preserved here,
never deleted. Unsealed dev states are development history, not evidence;
only the sealed gated run and its receipts carry evidential weight.

## Resume context (wk-x45-impl, 2026-10-02)

The predecessor attempt died with the host at 18:03 Oct 1 (power failure),
leaving dev checks RED at "20 executed, 8 failures, 0 skipped" and NO sealed
run, no sealed directory, nothing published. That RED state was never
sealed: it is not evidence of anything and is not preserved as a record.
Diagnosis at resume found five work-in-progress defects, all repaired before
any sealed run:

1. `scene_source_bytes` pointed at this card's own extraction root, which
   never materializes the scene (the scene is a W10 certified-line pin,
   extracted by the W10 layer). Six unit checks errored on
   `input_pin_missing:scene_cpu_extraction`. Fixed: the bytes are read from
   the W10 layer's byte-verified extraction (order is law; loud refusal if
   the layer has not run).
2. The climb-audit form mismatch: the driver passes the receipt wrapper
   (clean + scratch_flipped + law) where `derive_state`/`binding_audit`
   expected the flat clean audit. Fixed in the derivation module (both
   forms normalized, nothing else accepted).
3. The diagnostic-probe consumer read `l1_bg_px_expected`-style keys; the
   probe's schema is `l1_bg_expected`-style. Fixed the consumer to the
   probe's schema.
4. The camera-field unit check hardcoded the prereg's freeze-time count
   (15) against the live registry profile (16 fields; G7 consume-live law).
   Fixed: the check asserts ALL live profile fields carried and pins the
   live count; the drift is disclosed in the P6 receipt evidence and the
   report, never silently reconciled.
5. The clean-diagnostics validator fixture violated the tag-binding
   identity law (checked first by the pinned validator), so the intended
   clean-law refusal never fired. Fixed the fixture to violate ONLY the
   clean law.

## Dev-run refusals of the sealed-order pipeline (devcheck scratch copies)

- 2026-10-02 dev run 1: stage `presentation_verification` RED —
  KeyError `climb_state` at the first rendered frame (defect 2 above).
- 2026-10-02 dev run 2: stage `presentation_verification` RED —
  KeyError `l1_bg_px_expected` (defect 3 above).
- 2026-10-02 dev run 3: stage `report_lint` RED —
  `LINT:missing_honesty_marker:by design` (the report lacked the marker the
  lint requires; fixed in the verdict paragraph where it is true: visual
  acceptance false by design).
- 2026-10-02 dev run 4: all stages GREEN (20/20 checks, 39 frames,
  29 distinct poses, 5 bites, capture validator valid, lint GREEN).

## Standing capture gate (assigned at resume; disclosed, see card_prereg)

The two-stage capture-gate template (capture_card/) was integrated after
the dev GREEN run as the capture acceptance gate: 3 production cases over
the 39 committed frames + 4 declared defect cases that must be REJECTED.
Dev calibration of the frozen view-spec floors used the dev frames'
measured palette minima (body 386/400/6249/6230/136/136; layers
45323/9537/44927); floors pinned BELOW minima; no threshold was ever
adjusted to pass an observed frame. Card-kit batch gates re-run after
integration; the previously-red `receipt_json_schema` gate is satisfied by
card_prereg.json + view_spec.json.
