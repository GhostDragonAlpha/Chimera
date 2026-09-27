# ONT-U02 — follow-camera qualification (reconciliation + controls profile)

**Verdict: the card's done_when is MEASURED GREEN on the pinned M-U02 camera
lineage — 15/15 frozen checks, byte-deterministic trace, the tested
obstruction cases OC1-OC8 re-measured live and by case matrix, the
never-moves-the-animal invariant proven on the recorded command stream, and
a gate-valid camera manifest with the three declared views. Three frozen
sub-clause mispredictions FIRED and are recorded as deviations — not
smoothed. Nothing was reimplemented; no pinned byte was edited.**

- Card `ONT-U02` (planning U02, verification profile `controls`, kind
  **motion**), attempt `2c724944121f4feb893f671504bbac00`, agent
  `arrival-286909b6a5744dd79beb1a4a52c75b78`, criteria
  `5fb0dee8d086f9fd638507058063dd7b7c138958ab7433e5f086da2bbc120b83`.
- Dependencies ONT-P01 (PR #127, merged 391f0ede) and ONT-P03 (PR #140,
  merged 736d12cc): both DONE with qualified winners; their frozen contracts
  are reused unchanged.
- `PREREGISTRATION.md` (18f1ffcaad155e35c4831c861483f53468fdca1b6806f2b29cd5402c823d379d)
  was committed at `cbea7790` BEFORE any probe ran; the open-loop geometry
  derivation (`scratch/derive_geometry.py`, attempt workspace) preceded the
  freeze. A contribution-local `.gitattributes` (`* -text`, commit
  `a8a1df91`) keeps the pinned reference bytes byte-exact on fresh checkouts.

## Subject identity (nothing edited, nothing reimplemented)

Pinned play commit `f30f2224663324e9374b076938c56672febf4082` recovered
READ-ONLY (`git -C E:/ChimeraWork/monkey-play-20260924 show …`) into
`reference/`, hash-asserted at import in the probe AND the test suite (play
worktree untouched at HEAD `8d16d3c1`):

| source | sha256 | role |
|---|---|---|
| product/follow_camera.py | `d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7` | THE QUALIFIED SUBJECT |
| product/focus_policy.py | `e0b23968bb8ee8e7c5449da464948d68cc67bf3cc62db40dd30a73ee8ef0f9d0` | focus loss / release (exercised live) |
| product/state_feedback.py | `74c0aad033eeafef971888809702a0d0f4f387c55ac9690ee5380edc02a189d1` | recovered + hash-pinned; NOT imported (its observation needs climb_intent + session_flow — other lanes) |
| product/input_mapper.py | `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` | walk command seam (exercised live) |
| product/follow_camera_tests.py | `4d75164ff6a16bf0d817332b7c5229513750782727ad1a23911025dc93d31b27` | pinned suite incl. OC1-OC8 (re-run 24/24) |
| science_funnel/typeb_export/command_record.py | `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` | command record v1 seam |

## Done-when, clause by clause (measured)

**"Player can see motion on ground and at trunk"** — trace
`97f9fbfcfafcfbeaa02ced70636231bd3935ee446b8a9b9c114d2f05ad8a3c8a`
(391 ticks, 50 ms grid, byte-identical on rerun):
- ground: C1 measures the base framing law (radius/theta/phi/target to
  1e-9 of the pinned laws), anchor subtend <= 1.11 deg, a ground patch 2 m
  ahead <= 6.84 deg (both << the 22.5 deg half-FOV), commanded phi <=
  PHI_MAX_GROUND (feet-in-frame law);
- trunk: C5 measures the declared two-point fit at entry (single
  ground->trunk transition at axis distance 2.706 <= 2.952 threshold, zero
  exits), anchor AND trunk-contact subtends <= 3.64 / 2.86 deg on every
  trunk tick — the close-target view;
- C2/C3 exercise controls, focus loss and release through the REAL pinned
  FocusPolicy + InputMapper: blur while walking releases, the decay lands
  on an EXACT 0.0 record then silence, a press during blur is dropped BY
  NAME, focus + fresh press re-arms a fresh grid, and the camera settles
  under the declared starvation/clamp laws.

**"camera avoids tested obstruction cases"** — the tested cases are the
pinned preregistration's OC1-OC8:
- OC1 live (C4): the pole crosses the base sight-line for the derived
  window; avoidance onset EXACTLY at the first blocked tick of the module's
  actual (smoothed-aim) sight-line (4200 == 4200); every non-degraded
  solution eye-clear by 0.25 m, ray-clear by 0.02 m, anchor framed; the
  measured orders are exact prefixes of the frozen order
  (steepen -> height_radius -> orbit);
- OC6 live (C4): the solution is retained across the halt (shape bitwise
  constant), and when the converging aim point exits the optical margin the
  module flips degraded -> resolved within ONE tick;
- OC2/OC7 case matrix (C9): pull_in resolves at R' = 3.7553, strictly
  inside [pull_floor 2.5349, pre-avoidance base 4.348), eye+ray clear,
  framed, bit-identical on a fresh camera (determinism); monotonicity is
  additionally owned by the re-run pinned suite;
- OC3b case matrix (C8): an anchor inside an unreachable blocker's optical
  margin ends degraded=True with the declared reason — honest degradation;
- OC4 (C6): clean static scene = one write, bitwise no-op;
- OC5 (C7): a sub-ray curb whose footprint IS crossed (module's own 2D
  segment test) leaves the height-aware ray clear with the command equal to
  the clean-scene base command;
- OC8 live (C10): the WHOLE run's command stream (both cameras, 500 writes)
  has zero allowlist violations, zero forbidden routes, pan 0.0 and exactly
  8 camera fields on every write; the engine doubles expose no body surface.

**"never moves the animal"** (C10/C12): the anchor stream is
harness-owned (the REAL mapper's records integrated by the harness); camera
code never writes body state; every write is POST /camera (allowlist,
8 fields, pan 0); the strict doubles record zero undeclared attempts; the
pinned verify_apply echo equals the last commanded v within 1e-3 on both
cameras (FG).

## Falsifier scorecard (honest)

- **P3-sub "writes CEASE within 1.5 s" / "ZERO writes over the final idle"
  FIRED**: the pinned starvation law deadbands sub-deadband STEPS; it does
  not hard-stop the converging settle tail. Measured laws that hold instead:
  per-tick applied steps within deadband + settling floor, path length
  within the 0.05 m/s settle budget, tapering writes, residual under the
  deadbands (C3/C6). Recorded in `numerical_receipt.prediction_deviations`.
- **P-sub "the continuous run has ZERO degraded ticks" FIRED**: 85 degraded
  ticks. The frozen open-loop derivation evaluated the sight-line at the RAW
  anchor; the module aims at the SMOOTHED anchor (EMA tau=0.3 s), which
  trails ~0.21 m on this path and converges after the halt. Wherever that
  aim point sits inside a declared obstacle's optical margin (r + m_ray) no
  pose can clear the look-ray. The measured LAW is an exact biconditional:
  degraded(t) IFF smoothed-anchor(t) inside an obstacle optical margin —
  the flag never conceals and never fakes (C8). Recorded FIRED.
- **P-sub "no avoidance before the first derived blocked tick (+-2)" FIRED**:
  avoidance onset lags the raw-anchored window by the declared smoothing.
  On the module's ACTUAL sight-line the law is exact (avoidance order
  non-empty IFF the smoothed-aim base sight-line is blocked/eye-unclear,
  C4). Recorded FIRED.
- No other falsifier fired: no stuck command, no camera-induced body
  movement, no unreadable required target (max non-degraded subtend
  3.64 deg), no concealed obstruction, no unbound timing (trace times are
  injected; wall-clock latency reported separately, max 0.552 ms vs the
  50 ms test-level budget), no pinned-source drift.

## Camera + visual evidence (per visual_gate, honest boundary stated)

`evidence/capture.mp4` (sha `e31290998b65b12886381523842c3d6c132421baefab3cdcf4ebe333d37c373e`,
2,343,224 bytes, 640x360, 2346 frames @ 20 fps = 117.3 s, h264 bitexact)
rendered from the SAME trace by `capture_build_camera.py`:

- `normal follow-camera distance` — the BASELINE camera (clean scene),
  recorded each tick — the normal-distance framing law, motion on ground
  visible;
- `obstructed and close-target views` — the SUBJECT camera (trunk + pole +
  curb), recorded each tick — the avoidance episode, latch retain/release,
  and the trunk-mode close-target framing, with the DEGRADED flag drawn in
  the diagnostic rows;
- `repeatable inspection side view` — fixed bookmark (radius 14, theta
  pi/2, phi 0.3, target (3,0,-2), pinned engine eye law), identical pose
  all 391 samples;
- each view a diagnostic+clean pair binding the same trace sha; camera
  fields complete (frame `monkey_u02_world_yup_m`, right-handed metres,
  quaternion wxyz camera->frame NUMERICALLY VERIFIED axis-mapped — camera
  +Z lands on the eye->target forward, +X on right, +Y on up (unit test);
  forward +Z / up +Y, near/far 0.1/200, 640x360, aspect 16:9, perspective
  45 deg vertical FOV, 391 samples covering tick_interval [0, 390] exactly);
- diagnostic rows carry exactly the three declared profile layers
  ("input/state/tick display", "camera target and frustum diagnostics",
  "selected creature labels") with stable tag bindings; clean rows are
  scene-only, depth-tested.

`evidence/capture_manifest.json`
(sha `103b93ed6d02964c42f7cabb76346618e1d02c2519d54249c868d1a5eae0f5dd`)
validates in-process through the campaign's own `visual_capture.
validate_manifest` AND `visual_gate.verify` against `card_task.json`
(structurally_valid: true, profile controls, 6 views, video). The exact
receipt-as-submitted (`qualification_receipt.json`) also re-validates
through `visual_gate.verify` — verified before submission.

**HONEST BOUNDARY (unchanged from the frozen preregistration)**: the pixels
are a deterministic CPU visualization of the recorded headless trace of the
pinned camera subject — they are NOT native engine frames and make no
V03/V08 native-rendering claim; the integrated native checkpoints remain
with the integration lane. An unmodeled obstacle can still occlude (the
declared cylinder model is INJECTED, never discovered) — the pinned C23
coverage boundary, unchanged. Human follow-feel acceptance and tau
re-derivation remain U07's declared follow-ups exactly as the pinned
verdict recorded.

## Observation for the lead (non-blocking)

The ONT-X02 candidate (PUBLICATION_PENDING) ships manifest orientations from
the same `quat_wxyz_camera_to_frame` construction this candidate inherited
as the pattern; structural validation checks unit-norm only. A numeric
axis-mapping check (camera +Z -> forward) shows that construction yields the
transposed convention. This card's own orientations are regenerated with the
verified convention and unit-tested; the lead may wish to note the same for
X02's manifest before its publication.

## Candidate suite and how to reproduce

```
python -B tools/monkey_campaign/contributions/ONT-U02/camera_profile_probe.py
python -B tools/monkey_campaign/contributions/ONT-U02/capture_build_camera.py
python -B -m unittest test_camera_profile_probe -v     # 8/8 OK
```
CPU-only (stdlib + Pillow + ffmpeg on rendered frames), no GPU, no engine
process, no browser, no network. Trace + receipts byte-identical on rerun;
the video rebuilds bit-exact. Total new output ≈ 3.4 MiB (< the 16 MiB cap).

Note: `reference/tools/monkey_campaign/agents/U02_camera/receipts/
latency_run.json` is the PINNED suite's own declared receipt output
(`follow_camera_tests.py` TestLatencyBudgets writes there on every run); the
committed copy is this environment's re-run record (wall-clock latency of
the pinned suite here: max chain 0.0603 ms vs the 50 ms budget). The pinned
test file itself is byte-unmodified.

## Submission note

`qualification_receipt.json` ships `head_sha: null` with an explicit binding
note: the ACCEPTED review must pass this receipt with `head_sha` set to the
exact reviewed head (an in-tree file cannot contain its own commit hash; the
same pattern as the ONT-P01 winner record and the ONT-X02 candidate).
Writes stop at this candidate's commit; the independent review is queued by
the publication request.
