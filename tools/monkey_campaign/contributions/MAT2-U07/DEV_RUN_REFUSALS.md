# DEV_RUN_REFUSALS — MAT2-U07 (preserved; honest development negatives)

- D1 (2026-10-01, pre-run development): the FIRST draft of the U07 pin table
  pinned the seam modules at in-tree paths
  (`tools/monkey_campaign/product/input_mapper.py`,
  `tools/science_funnel/typeb_export/command_record.py`) by ASSUMING the
  in-tree layout. `git cat-file` at the package base refused
  (`blob_read_refused`): the seam is NOT in-tree at base a07ac859 — it lives
  only under the contribution reference/pinned_seam trees, and the runtime
  resolves it through the W10 extraction's stripped namespace. Fixed BEFORE
  any run: the pins now target the FOLLOWUP reference copies (same
  pinned-lineage hashes). Lesson: never assume an in-tree layout; probe the
  base tree first.

- D2 (pre-run development): the prereg's first occluder box
  (`[0.6,0.9]x[0.0,1.2]x[-0.3,0.3]`) FAILED the pre-registered look-ray
  arithmetic (the C_V1 ray crosses z=0.3 at x=0 — outside the box's x range).
  Corrected in the prereg BEFORE any experiment to
  `[-0.35,0.35]x[0.5,1.0]x[0.4,0.8]` with the intersection arithmetic stated
  in the freeze. The falsifier would have bitten on my own probe.

- D3 (pre-run development): W10's `verify_inputs.verify_registry()` asserts
  profile `walking`; U07's profile is `controls`. This card therefore runs
  W10's pin/extract layer for the certified line but performs its OWN
  registry/profile check (G7) against the controls profile, read-only.

- D4 (dev run, 2026-10-01): prereg P1 AS ORIGINALLY FROZEN was REFUTED by
  the accepted adapter's own antecedent law (re-issued commands lawfully
  share one press; seg_input_to_command grew to 13950 ms over the hold).
  Fixed by AMENDMENT-A1 (first-response law) BEFORE any sealed run; no
  receipt existed against the refuted form.

- D5 (dev run, 2026-10-01): prereg R4 AS ORIGINALLY FROZEN (hold, never
  release) produced ZERO expiry reverts — the seam re-issues held keys every
  poll, so the consumer record age never exceeds the floor. Fixed by
  AMENDMENT-A2 (release-then-silence script). The follow-up dev run then
  showed the decay lands on an EXACT-ZERO record whose projection IS the
  inert path — a healthy arm never produces a revert EVENT. Fixed by
  AMENDMENT-A3 (the honest observable law; the expiry belt's bite is proven
  at the unit level in the named checks).

- D6 (dev run, 2026-10-01): the R5 focus policy's mapper tick source was
  wired to a holder the loop never advanced (every record dropped at the
  gate with age ~2000 "ticks"), and the policy was first built against the
  DRIVER's sink instead of the arm's (one-emission-path violation caught by
  the empty arm sink). Fixed: the policy is built inside run_arm against the
  arm's own sink; the tick holder rides the loop.

- D7 (dev run, 2026-10-01): the first capture encode piped 3-byte RGB into a
  declared bgr0 (4-byte) rawvideo format — the decode probe REFUSED
  (capture_codec_violation:decode_mismatch). Fixed with W10's exact 4-byte
  bgr0 packing law (vectorized); the decode probes are byte-exact now.

- D8 (dev run, 2026-10-01): the validator's pair law (diagnostic/clean rows
  of one view must carry IDENTICAL camera records) refused the first
  manifest (mode-dependent label fields inside the camera record). Fixed:
  the camera record is mode-independent; the per-mode visibility row carries
  the labels/layers.

- Dev-run outcome: all five stages green (controls verification P_all_green,
  11/11 named checks, capture 32 frames validated, report generated, lint
  GREEN). The sealed runner run below is the evidence-producing execution.


- D9 (correction-r1 sealed-dev run, 2026-10-02, job
  6f44d32b2bf3415388605e3e3f61f4e9, base 69772e91, seal
  5d5ba08c6bfa71cf39a85bccbd32bf8220ced6bc6d0d409bc965c46b6797c387): the
  NEW mechanical pixel gate REFUSED its first sealed run —
  `capture_pixel_gate_failed:pixel_gate:body_palette_missing:O_clean_t4500
  :0/30` — and the census also showed the declared 200 px side-view floor
  above the real render (137-144 px). This is the gate's designed bite,
  recorded as an honest negative. Two facts established by the retained
  frames.npy of that job: (1) the follow fix WORKS — every previously blank
  view now renders the body (C_V1 presentation 385-418 px per frame,
  close-target 6282-6385 px, side 137-144 px, frustum marker 112 px and
  body-label marker 21 px on every diagnostic frame); (2) the frozen
  occluder box FULLY conceals the body in the obstructed view (fill 17678
  px, body 0 px) exactly as P9's numerics predicted
  (target_inside_box_screen_footprint true). Corrected BEFORE the evidence
  run and re-frozen: obstructed frames require the occluder fill (>= 100
  px) with body_min_px 0 and a declared reason (demanding body pixels would
  demand concealing the declared obstruction); side floors lowered to 100
  px (census-justified). The planted-defect selftest and all 18 named
  checks were GREEN in the same run; stages 1-2 GREEN, stage 3 refused —
  the refusal is the pixel gate working as amended.
