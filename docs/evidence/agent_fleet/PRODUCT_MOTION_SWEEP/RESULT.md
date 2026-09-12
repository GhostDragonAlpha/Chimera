# RESULT — product-motion-sweep-01

Task packet: the PR #97 blind judge found that "only the right arm visibly
moves … the other 20+ joints never do, so the 'all joints exercised' claim is
carried by UI text and reel thumbnails, not observable motion." Deliverable:
one continuous scripted interaction, public HTTP API only, visibly exercising
>= 8 distinct joints across >= 3 body regions, captured on /glass and judged
BLIND by the ordered-frames protocol.

Chain: prereg `ec26f5df` (RULE 0, zero actuals) -> driver `f001a416` ->
take + blind spec `6a7a406a`. Base `cb874a3a`, branch
`astra/tasks/product-motion-sweep-01`, slot-04, claim generation 1.

## The take (measured 2026-09-11, MY private build)

- Engine: `.tmp/engine_build/motionsweep/Release/chimera_engine.exe`
  sha256 `1424d8653feea5f0ebc0579c49407d151c393bb00c2a6a2287b3fdb88dcac1d0`,
  port 8104, runtime CWD `.tmp/engine_runtime/product-motion-sweep-01/`,
  `--no-restore`; pid 73400; rtx4090 + engine_demo held via the controller
  for the whole run (granted rev 1089, released rev 1097/1098 with drain
  evidence after the run). `ChimeraEngine/engine/build/` untouched; zero
  engine-source edits (the falsifier's structural half).
- Rig verification (public GET /joints): 28/28 declared names present,
  0 ROM mismatches at 0.5 deg tolerance, all rest thetas zero. The rig is the
  PR #97 pair, byte-committed (`monkey_birth.bin` + `monkey_joints.bin`).
- Script: 13 joints / 4 regions exactly as preregistered (arms 36/75 deg,
  legs 71.4/88.2 deg, spine 37.85/35.75 deg, tail 52.28/83.24/27.0 deg);
  70 frames at 10 fps; phases REST -> ARMS-RISE -> LEGS-STEP -> SPINE-TAIL-
  WAVE -> FULL-HOLD -> RESPONSE; fixed camera 3.4x extent (the PR #97
  head-crop fix — the whole creature including head and tail is in frame in
  every keyframe).
- **Engine-truth gate: 13/13 PASS** — at full hold (f049) every scripted
  joint's GET /joints readback equals its declared peak (36.0, 75.0, 71.4,
  88.2, 37.85, 35.75, 52.28, 83.24, 27.0 deg), >= 50% gate. The readback
  table for all 6 keyframes x 28 joints: `joint_thetas_keyframes.txt`.
  This is engine-side truth, not UI text — the exact failure mode the PR #97
  judge named.
- Judge artifact: `product_motion_sweep.mp4` (the /glass product surface, 70
  frames, sha256 `bb8a6d4cd10103691e303dac2f7f98dfbbc63e4ac37c1363fe0dab68df003fa6`);
  the /frame twin encoded separately; 140-frame sha256 manifest retained
  (`frames/MANIFEST_sha256.txt`); the 6 judge keyframes committed as PNGs.
- Recorded observations from the keyframes (cosmetic findings, none gate-
  bearing): at full hold the composed spine bend folds the torso forward ~74
  deg as derived; the curled tail's silhouette spikes read slightly dark
  against the floor grid; the studio show clock continues its own course
  during the take (the PR #97 timing-untruth defect 4 — NOT this lane's
  scope; product-hud-truth territory; the take's timing truth is carried by
  the declared 10 fps schedule and the engine readback).

## Script API surface (falsifier check)

POST /joint, POST /camera, POST /joints_bin, GET /joints, GET /scene,
GET /glass, GET /frame, POST /mesh_bin (via cpp_bridge.load_mesh_bin, the
PR #97-accepted wrapper) + tools/engine_demo.py launch/stop. No engine-source
edit exists on this branch (`git diff cb874a3a..HEAD --stat` touches only
`docs/evidence/agent_fleet/PRODUCT_MOTION_SWEEP/`). The engine-source half of
the falsifier is NOT fired by construction and by diff.

## The blind dyad (ordered-frames, PR #97 protocol)

Spec: `dyad_orderedframes_spec.json`; exact prompt:
`dyad_plan/exact_prompt_product-motion-sweep-orderedframes-v1.txt`; the judge
is told nothing about the joints, the regions scripted, or the defect under
exam. Spawn request posted to glm53-lead-02's mailbox (the lead owns the
judge spawn per the lane contract).

### Verdict

PENDING — appended below when the lead-executed judge returns.

---

## Dyad verdict (appended)

See DYAD_REPORT.txt (verbatim) and DYAD_ASSEMBLY.md (rubric scoring).

## Lead completion note (2026-09-11)

The owner host died to the provider outage before the judge spawn; the
lead executed it, assembled (DYAD_ASSEMBLY.md above), and pushed.
PREDICTION: 4 regions named unprompted (>=3 required) — the PR #97
one-arm defect is visually verified fixed. FALSIFIER: held (zero
engine-source edits). Visual proof delivered to the operator desktop
(CHIMERA_PROOF/motion_sweep_keyframes + MOTION_SWEEP_13joints_4regions.mp4).
Agent: glm53-lead-02
