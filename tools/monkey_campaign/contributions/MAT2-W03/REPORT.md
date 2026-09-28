# MAT2-W03 — sergeant escalated implementation report

- Arrival: `arrival-db26712d6a264e4899c951f55b074d80`
- Task: MAT2-W03 (criteria sha256 `1350a1431c5a42cbeb4e2f15ef3fd8d8f9d9474c1629984c2a466c58fcc60217`)
- Kind: verification, profile `parity-replay`; escalated implementation round
  (Captain try-correct-takeover; scratch workspace approved by the Lieutenant
  after phantom attempt `8e07b67b` was parked; registry publication handoff is
  executed by the Lieutenant).
- Workspace: `E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-W03\sergeant-arrival-db26712d`
- Preregistration: `PREREGISTRATION.md` (frozen before the replay runs).

## 1. What was actually run (no paper citations)

Every number below was produced in THIS attempt workspace from blob-identical
extractions of the pinned training revisions, with commands and outputs
captured as evidence files. Nothing is cited from a prior PASS table.

- Walk-anchor lane, training revision `17ba94b948ca217c1bbf8f7dee5b51b995b387bb`:
  scene generator + statedump source (git object `a7bfe15e...`, content sha256
  `dea2be78...`) extracted read-only from E:/PythonChimera's object store
  (`extract_pinned.py`, `extract_record.json`).
- Walker lane, training revision `a62b286effa27ee2db7bbcb65507a2ac45ad0d0c`
  (SHUTDOWN CHECKPOINT): `walker_env.cu`, `walker_kernels.cuh`,
  `host_loop.cxx`, `host_shim/*`, `bars_fullport.py` + python driver chain
  extracted read-only; binaries rebuilt with the pinned recipes
  (`build_walker_v2.ps1` = `build_dll_v2.ps1` + `build_host_loop.ps1` recipes,
  paths redirected into this workspace).

## 2. The W03 bar — walk anchor replay (G4): REPRODUCED EXACTLY

Command: rebuilt statedump on the regenerated scene (no argv[2],
`GAIT_STATE_DUMP`/`GAIT_STATE_DUMP2` set), raw byte capture, 26.3 s wall.

| Anchor | Frozen | This run | Verdict |
| --- | --- | --- | --- |
| scene.json sha256 | `f6844eea...a8db342` | `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342` | EXACT |
| stdout sha256 | `8c537cdb...` | `8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc` | EXACT |
| stderr sha256 | `c6f9b6c0...` | `c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481` | EXACT |
| q dump run1 | `b47b709c...` | `b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93` | EXACT |
| q dump run2 == run1 | bit-identical | bit-identical | EXACT |
| ticks | 302 (0..301) | 302 (0..301), exit 0 | EXACT |
| base dx | 0.9131056683968011 | 0.9131056683968011 | EXACT |
| base dy | -0.7178374101385098 | -0.7178374101385098 | EXACT |
| worst ledger | 30.970714 J | stdout prints 30.970714; raw balance_error_J 30.970713623726674 (store 30.970713623726652), tick 300 | EXACT |

Evidence: `scene_out/scene.json`, `viswalk_dump/{dump_stdout.txt,
dump_stderr.txt, states_run1.jsonl, states_run2.jsonl, dump_run_record.json,
walk_numbers_record.json, build_log.txt}`. The rebuilt statedump exe hash
differs from the pinned P02 build (`f3aa3062...` vs `2072a881...`; MSVC embeds
build paths) — predicted; outputs are byte-identical, which is the meaningful
identity.

## 3. G1-reachable-ref: CLOSED

`a62b286e` is HEAD of `agent/typeb-gpu-finish-20260922` in the finish-agent
checkout (clean worktree) and is referenced in E:/PythonChimera by
`refs/chimera-archive-source/20260925/agent/typeb-gpu-finish-20260922` and tag
`archive/20260925/agent/typeb-gpu-finish-20260922`. The pinned sources are
reachable; all extractions verified by blob identity.

## 4. G2-binary-rebuild: CLOSED (rebuild is trace-equivalent)

| Binary | Registry/on-disk | Sergeant rebuild | Trace equivalence |
| --- | --- | --- | --- |
| walker_env_v2.dll | `51259178...` | `9366d02d...` | 43-tick FULL replay line-identical (43/43); full bars battery behaviorally identical |
| host_loop.exe | `a0509caf...` | `65805557...` | stdout BYTE-IDENTICAL to pinned receipt `co8_hl_v2.out` sha `6ba8123b...` (HL_FULL=1) |
| gait_unit_viswalk_dump.exe | P02 record `2072a881...` | `f3aa3062...` | walk-anchor outputs byte-identical (section 2) |

Fresh binary hashes differing from registry values is the PREDICTED outcome
(compiler embeds timestamps/paths; the registry anchors binaries to
source+script+rebuild by design — .gitignore banks `*.dll`/`*.exe`, "source is
the truth"). The meaningful identity is trace-level, and it holds everywhere it
was measured.

## 5. G3-fresh-gpu-device: CLOSED (with an honesty note)

Fresh 43-tick tie-v2 replay on the RTX 4090 (`dev_replay.py`, pinned
co8_dev41.py protocol: WalkerEnvDLL(spec,1,reflex_level=1,block=32), FULL t
lines %.17g), re-run inside the Lieutenant-certified uncontended window
(22468 MiB free at start; `gpu_clean_window_start.txt`/`_end.txt`):

- device (original `51259178` dll) == historical `co8_dll_v2b_120.txt` — line-identical (43/43)
- device (rebuilt `9366d02d` dll) == device (original) — line-identical (43/43)
- device == host FULL window t=1..43 — line-identical (43/43), host leg itself
  byte-identical to the pinned `6ba8123b` receipt.

Fresh host-vs-device parity t=1..43 reproduced NOW. Honesty note: the first
device replays ran on a shared desktop GPU (VRAM ~23.4-23.7/24 GiB in use by
desktop processes, utilization 2-41%); they were REPEATED in the certified
clean window with byte-identical results. Both runs are preserved
(`dev_original_v2.out` vs `dev_original_v2_clean.out`).

## 6. Freefall/stand/C1/C2 bars (P6): measured on three binaries

Protocol: pinned `bars_fullport.py --env dll 32` (frozen falsifier
definitions; PCG64(s) seeds; frozen `cpu_stand.txt` baseline copied
byte-identical). Results JSONs: `typeb_run/tools/science_funnel/validation/
typeb_gpu_fullport_20260921/bars_split_b32_{co8,v2original,v2rebuilt}.json`.

| Measure | Frozen closeout-8 (co8, baseline) | This run: co8 `799ba5ff` | This run: v2 `51259178` | This run: v2 rebuild `9366d02d` |
| --- | --- | --- | --- | --- |
| freefall g | 9.806650000000689 (err 6.892265e-13, latch 52, GREEN) | 9.806650000000689, err 6.892265e-13, latch 52, GREEN — IDENTICAL | 9.806650000000689, latch 52, GREEN — IDENTICAL | IDENTICAL |
| stand max_scaled_diff | 0.9511245759469239 RED | 0.951124575946924 RED — IDENTICAL | 0.086511750196834 RED — changed | IDENTICAL to v2 |
| C1 nominal | horizon 40, class 5, hind 0, fore 0 | 40/5/0/0 — IDENTICAL | horizon 55, class 3 — CHANGED | IDENTICAL to v2 |
| C2 survival | 64 seeds, pass_100 0, median 40.0 (40/41/55/66/70 mix, classes 5/3) | 0, 40.0, all 64 horizons AND classes IDENTICAL | 0, 55.0, all 64 horizons/classes CHANGED (41..77, class 3) | IDENTICAL to v2 (only wall_s timing differs) |

Mismatch analysis (honest, with the mechanism named):
- The frozen closeout-8 receipt reproduces EXACTLY on the binary that recorded
  it (`walker_env_co8.dll`), uncontended, including every one of the 64 C2
  seeds and classes. The A10 baseline is real and stable.
- walker_env_v2.dll differs from the co8 baseline at exactly the declared
  Option-B version-bump sites: nothing before the tick-41 tie engagement moved
  (freefall identical to the last digit; my G3 replay shows t=1..40 states
  bit-identical to pre-v2 host and t=41..43 equal to the v2 historical
  receipt), while post-engagement outcomes moved (stand residual, C1 40->55
  with class 5->3 — the walk now demonstrably passes tick 41, which is the
  tie-v2 registration's own purpose per `PREREG_RESIDUAL_TIE_V2.md`, commit
  `9376c3d8`), and C2's horizon/class distribution follows the same mechanism.
  The stand bar remains RED on every build (threshold <1e-2 unchanged and
  untouched); C2 remains pass_100=0 on every build.
- The sergeant's v2 rebuild is behaviorally identical to the registry-hash v2
  binary across the whole battery.

## 7. D-W03 verifier + material-first clause

`implementation.py` / `test_implementation.py` hash-match the pinned records
(`F21180BC...` / `5A605ED3...`) and run `16 passed, 0 failed, 16 total`.

Material-first: every number in this report is tagged with the representation
that produced it (statedump CPU harness / walker co8 dll / walker v2 dll /
sergeant v2 rebuild). Old evidence was treated as baseline only; it was RERUN,
not cited. No identity substitution: the 13824.5 kg membrane lineage, the
10.038 kg Oku training body (mass 10.037998000000004 kg in the regenerated
scene's seating scan, weight 98.43913308670002 N) and all other mass lineages
stay distinct. No trained walking skill exists or was used; the motion driver
is the engine's certified scripted gait harness.

## 8. Gates and standing gaps (named, none invented)

- G1 CLOSED, G2 CLOSED, G3 CLOSED (clean-window re-run), G4 CLOSED (section 2),
  D-W03 verifier suite PASS.
- Named gate condition, recorded honestly: no exclusive broker window existed
  for the FIRST device replays (shared desktop GPU); the Lieutenant then
  certified an uncontended window and the runs were repeated byte-identically.
- G5 (tick-41 row-0 sign knife registration) and G6 (non-author manifest
  review + coordinator compatibility certificate) are downstream lead/reviewer
  actions from the D-W03 lineage; not claims of this attempt.
- No visual gate is specified by the W03 done_when or the parity-replay
  profile; no visual evidence is claimed. (The P02 movie lane is a different
  card's deliverable.)
- Registry publication handoff for this attempt is executed by the
  Lieutenant (the live harness's worker_start.py has no --request-pr flag;
  recorded in the task inbox note).

## 9. Falsifier self-check

- Changed old anchors? No — the frozen receipt and the P02 anchor bytes were
  used read-only and reproduced, never modified.
- Unexplained out-of-band change? The only behavioral differences (v2 vs co8)
  are at the declared tie-v2 sites, analyzed in section 6.
- CPU labeled as fresh device qualification? No — device legs ran on the RTX
  4090 and are reported as such.
- Writes outside this workspace? None; prior attempt workspaces and both
  source repositories were used read-only.
