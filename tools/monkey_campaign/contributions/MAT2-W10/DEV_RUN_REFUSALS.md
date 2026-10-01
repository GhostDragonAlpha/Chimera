# DEV_RUN_REFUSALS — MAT2-W10

The W08 lesson: development-run refusal codes live in a frozen prereg file
or here. Recorded BEFORE any sealed run; the sealed runs are the receipted
arms of `run_all.py` at the final candidate commit.

As of this file's writing (the implementation commit, BEFORE any gated run):

- No development harness run of walking_demo.py has happened yet. The
  implementation was written against the pinned bytes and compile-checked;
  the first execution of every arm is the runner-gated sealed run. Any
  pre-seal development refusal will be APPENDED here verbatim with its named
  code, the exact command and the correction — never silently discarded,
  never cited as final-run evidence.
- Anticipated refusal codes are frozen in PREREGISTRATION.md section 9
  (`criteria_pin_mismatch`, `input_pin_missing`, `input_pin_drift`,
  `certificate_validator_violation`, `deploy_gate_sanity`,
  `load_identity_mismatch`, `build_identity_mismatch`,
  `prediction_failed:<name>`, `walk_unsupported_tick:<tick>`,
  `w09_replay_drift`, `asset_geometry_absent`,
  `registry_profile_missing_key`, `capture_codec_violation`,
  `w10_fb<n>_premature`, `falsifier_did_not_bite:<arm>`,
  `fb1_window_precondition_unmet`, `vacuous_comparison:<name>`).

Known pre-prereg dev notes (disclosed for completeness):

- The segment lengths (thigh 0.163 m, shank 0.182 m) were located in the
  derivation lane's derived_numbers.json during implementation; that became
  Amendment A2 (pin added BEFORE any run) rather than an inline constant —
  the refusal law (`asset_geometry_absent`) worked as designed.
- The W09 supervisor module needed an explicit pin for the replay arm; that
  became Amendment A1 (BEFORE any run).
