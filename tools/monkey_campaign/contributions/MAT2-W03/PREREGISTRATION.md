# MAT2-W03 sergeant attempt - PREREGISTRATION (frozen before the replay runs)

Arrival: `arrival-db26712d6a264e4899c951f55b074d80`
Workspace: `E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-W03\sergeant-arrival-db26712d`
Card: MAT2-W03, criteria sha256 `1350a1431c5a42cbeb4e2f15ef3fd8d8f9d9474c1629984c2a466c58fcc60217`
Profile: `parity-replay`. Escalated implementation round (Captain try-correct-takeover);
scratch plan approved by the Lieutenant after the phantom attempt `8e07b67b` was parked.

Timeline note: predictions P1..P8 below were stated in the working transcript before the
corresponding runs. The P1 scene regeneration was executed before this file was written
(its prediction is quoted verbatim in the transcript); everything after this file's
commit runs only after the freeze.

## Training revisions (identity, no substitution)

- Walk-anchor lane: `17ba94b948ca217c1bbf8f7dee5b51b995b387bb` ("DELIVERABLE: the real CT
  body WALKING..."), statedump source git object `a7bfe15e...` (content sha256
  `dea2be78...`), scene generator `tools/science_funnel/gait_scene.py`.
- Walker binaries lane: `a62b286effa27ee2db7bbcb65507a2ac45ad0d0c` (SHUTDOWN CHECKPOINT
  2026-09-23), `tools/science_funnel/typeb_gpu/{walker_env.cu, walker_kernels.cuh,
  host_loop.cxx}` + `build_dll_v2.ps1` / `build_host_loop.ps1` recipes.
- The two lineages share ONE certified scene: content bytes hash
  `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342`.
- Old gait/anchor evidence (MAT2-P02 lead ACCEPTANCE tables, closeout-8 bars) is BASELINE
  evidence only; this attempt re-measures. No identity substitution: the 13824.5 kg
  membrane lineage, the 10.038 kg Oku training body and any other mass lineage stay
  distinct; no CPU result may be labeled a fresh device qualification.

## Frozen anchors to reproduce (from the card + MAT2-P02 records)

| id | anchor | value |
| --- | --- | --- |
| A1 | scene.json sha256 | `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342` |
| A2 | statedump stdout sha256 | `8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc` |
| A3 | statedump stderr sha256 | `c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481` |
| A4 | q-dump run1 sha256 | `b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93` |
| A5 | q-dump run2 == run1 (bit-identical) | true |
| A6 | ticks | 302 (0..301), refusal at 302 |
| A7 | base dx | 0.9131056683968011 (exact) |
| A8 | worst moving ledger | 30.970714 J |
| A9 | registry binaries | walker_env_v2.dll `51259178...`, host_loop.exe `a0509caf...`, walker_env_co8.dll `799ba5ff...`, walker_env_d41.dll `9489dcad...` (gitignored by design; anchored to source+script+rebuild) |
| A10 | closeout-8 frozen bars (baseline, walker_env_co8 build) | freefall g=9.806650000000689 err=6.892264536872972e-13 pass=true; stand max_scaled_diff=0.9511245759469239 pass=false; C1 horizon=40 class=5 hind=0 fore=0; C2 64 seeds pass_100=0 median=40.0 |

## Predictions (named before results)

- **P1 SCENE (run; prediction stated in transcript before execution).** Blob-identical
  extraction of the 17ba94b9 generator closure regenerates scene.json with sha256 A1
  EXACT. Basis: P02 P1 CONFIRMED on identical blobs; deterministic python+numpy.
  OBSERVED: CONFIRMED (f6844eea... exact; stdout printed scene_sha256 bundle digest
  e61ad386... which is the pre-anchor-field digest, the file itself hashes to A1).

- **P2 STATEDUMP REBUILD.** cl rebuild (pinned flags, /fp:precise) from the pinned blob
  in THIS workspace produces a working exe whose sha256 MAY DIFFER from the pinned
  2072a881... (MSVC embeds timestamps/paths); the pinned exe hash is a historical
  record, not a rebuild expectation. BUILD OK with only warning-class diagnostics.

- **P3 WALK ANCHOR REPLAY (the W03 bar).** Running the rebuilt statedump on the
  regenerated scene (no argv[2], GAIT_STATE_DUMP/2 set) reproduces A2..A8 ALL EXACT:
  stdout/stderr/dumps byte-identical, 302 ticks, base dx exact to the last digit,
  worst ledger 30.970714 J. Basis: P02 P2/P3 CONFIRMED on the same source+scene; the
  binary is /fp:precise deterministic CPU code; same inputs -> same bytes.

- **P4 G1-reachable-ref.** `a62b286e` is the HEAD of a real branch in the
  finish-agent checkout (reachable there); in E:/PythonChimera the object exists but
  NO ref contains it (recorded as the residual G1 gap for the lead, honest finding).

- **P5 G2-binary-rebuild.** nvcc rebuild of walker_env_v2.dll and cl rebuild of
  host_loop.exe from the a62b286e blobs SUCCEED in this workspace; fresh hashes MAY
  DIFFER from A9 (compiler timestamp embedding); predicted TRACE-equivalent to the
  on-disk A9 binaries for identical inputs (same sources, deterministic fp:precise
  host code; device code determinism for identical arch/flags).

- **P6 BARS (freefall/stand/C1/C2).** On walker_env_co8.dll (the binary the frozen
  closeout-8 receipt was measured with, hash-verified on disk): freefall g, stand
  max_scaled_diff, C1 horizon/class, C2 median reproduce A10; C3/C4 are
  throughput/memory bars whose exact eps values are hardware/contention-dependent
  (predicted same order of magnitude; recorded, not gated). On walker_env_v2.dll
  (on-disk AND my rebuild): C1 (refusal t=40, before the tick-41 tie engagement)
  EXPECTED identical horizon/class; freefall (100 ticks, latch t=52), stand (60 ticks)
  and C2 seeds with horizon>=41 MAY differ under the tie-v2 rule - each difference is
  the Option-B version bump's declared mechanism, recorded per-seed, never averaged
  away. A blank "v2 == co8" claim is NOT predicted.

- **P7 G3-fresh-gpu-device.** Fresh replay past tick 41 from the fixture state:
  device FULL state lines (walker_env_v2.dll) bit-identical to the host v2 replay
  lines for the compared window t=1..43 (historical parity co8_dll_v2b_120.txt vs
  co8_hl_v2.out). Requires an uncontended GPU window; any contention or driver
  difference is recorded as a named gate result, never inferred from memory.

- **P8 MATERIAL-FIRST.** Every reproduced number is tagged with the representation
  that produced it (statedump CPU harness / walker co8 dll / walker v2 dll / rebuilt
  v2). No old PASS table is cited as this attempt's reproduction.

## Falsifiers (any one fails the claim)

- Any of A2..A8 not reproduced exactly by the rebuilt statedump without a named,
  analyzed cause.
- The rebuilt walker binaries produce trace-level outputs different from the A9
  on-disk binaries on the same inputs (rebuild-not-trace-equivalent).
- A trained walking skill is used or implied to pass any leg (none exists; the
  motion driver is the engine's certified scripted gait harness).
- CPU evidence labeled as fresh device qualification; a missing GPU window silently
  skipped instead of recorded as a named gate.
- Any write outside this attempt workspace.
