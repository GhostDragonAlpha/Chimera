# ONT-W02 report — Close transcendental parity defects

Task W02 (implementation, group "Walking foundation", calculation C09, profile
`records` offline, numerical evidence required). Attempt `681e63e9e5d84eaa9702379faf347ac5`,
arrival `arrival-535a6d99aaf94c78b3aed6a239885498`, criteria_sha256
`bf9f89874ee4a7d0606c46215e843474331482444af556ac4f199a6bfcd087f2`.
Attempt checkout base: branch-8 @ `155a0f5c6ed14d6ce0c95572676eb03f14bc8a50`.
done_when: **"Reference-math equivalence is demonstrated at the frozen sites without
tolerance relaxation."**

VERDICT: **done_when demonstrated** — fresh, independently observed, zero-tolerance
(bit-exact) host evidence at all 125 frozen sites, on top of the reconciled lane history;
`RESULT PASS_NO_TOLERANCE` in `parity_gate_result.json`.

## 1. Existed vs built

**Existed (reconciled, read-only git pins; reused, not rebuilt):** the entire parity lane
in archive ref `refs/chimera-archive-source/20260925/agent/typeb-gpu-finish-20260922`
(head `a62b286e`): the frozen-site probe definition (`trig_probe_host.cxx` blob
`007c6f6a` / `trig_probe.cu` blob `8751479e` / `trig_inputs.txt` blob `252366b2`),
the libdevice-vs-CRT measurement (closeout-3 `2c062c2c`, records `trig_host.txt`
blob `0a89550d`, `trig_gpu.txt` blob `5ba31ec7`), the fdlibm rejection (closeout-5
`77023970`, `trig_fdlibm_out.txt` blob `d9cf26ea`), the UCRT reconstruction
(`ucrt_math.c` blob `efd87d67` + generated `ucrt_math_tables.h` blob `bf81305a` /
`ucrt_math_consts.h` blob `74e86ae2`; closeout-7 `d0b5eda8`/`7b092267`/`9e2e5c41`),
the on-device gate record (`co7_gate_out2.txt` blob `f7fbfb11`: 55,517/55,517
bit-identical), and the adoption into the walker build (closeout-8 `e3b591e1`).
None of these artifacts exist on the current production head; the card observation
("31/125 sites reported; fdlibm equivalence must not be assumed") was stale — that is
the UNRECONCILED state this card owns.

**Built (this attempt, task-owned):**
- `frozen_sites/` — byte-identical pinned copies of the lane artifacts above
  (extracted with `git -c core.autocrlf=false show`; sha256+git-blob table in
  PREREGISTRATION.md section 2, verified by the driver at 10/10 before any run).
- `frozen_sites/parity_gate_host.cxx` — the new frozen zero-tolerance gate probe:
  the 125 frozen sites (25 pinned inputs x 5 functions with the exact
  `trig_probe_host.cxx` argument derivations) plus the dense sweep ported verbatim
  from `trig_probe2_host.cxx` (blob `5bfe2c46`), reconstruction-vs-live-CRT, IEEE-754
  bit equality as the only pass condition.
- `frozen_sites/host_qual_shim.h` — compile-time neutralizer for the nvcc
  `__host__/__device__` markers in the pinned source (the lane's own host_shim
  precedent, closeout-8); no pinned byte is modified.
- `run_gate.py` — python -B driver: pin verification, MSVC host build
  (vcvars64.bat, `cl /nologo /O2 /fp:precise /EHsc /FI host_qual_shim.h`), probe
  execution (twice, for a determinism check), preserved-record cross-checks,
  machine-readable result.
- `parity_gate_result.json` — the evidence ledger (pins, per-site oracle/recon bits,
  dense census, preserved-record recounts, predictions, verdict).
- `PREREGISTRATION.md`, `report.md`, `qualification_receipt.json`.

## 2. Frozen predictions — outcomes

Frozen in `PREREGISTRATION.md` BEFORE the probe was built or run.

| id | prediction | outcome |
|---|---|---|
| P1 | reconstruction vs live CRT bit-identical at 125/125 frozen sites | **CONFIRMED** — `FROZEN125 125/125`, zero differing bits |
| P2 | live CRT oracle bits equal preserved `trig_host.txt` bits at all 125 sites (plus pinned-input identity) | **CONFIRMED** — 0 oracle-drift sites; input bits match |
| P3 | dense sweep: 0 differing bits; census sin 6396, cos 6396, atan2 40400, acos 1000, hypot 1200 | **CONFIRMED with one prereg-text correction** — measured 55,392/55,392 bit-identical and the per-function census matched exactly; the prereg's grand-total line said 53,392, an author addition slip (its own per-function numbers sum to 55,392). Prereg file left frozen; correction recorded here and as `PREDICTED_DENSE_TOTAL=55392` in the driver. Finding id F-ONTW02-CENSUS. |
| P4 | preserved fdlibm record: 115/125 identical, 10 diffs all exactly 1 ulp | **CONFIRMED** — fdlibm is NOT reference-equivalent at the frozen sites |
| P5 | preserved libdevice-vs-CRT: 31 diffs, distribution SIN 5, COS 5, ATAN2 6, ACOS 4, HYPOT 11, "every difference exactly 1 ulp" | **PARTIALLY REFUTED (finding F-ONTW02-ULPCLASS)** — count and distribution CONFIRMED (31 diffs, exact distribution); the all-1-ulp sub-claim is corrected by the records themselves: 30 diffs are exactly 1 ulp, 1 site (HYPOT input 16) differs by exactly 2 ulps (`3fdc335371774ecf` vs `3fdc335371774ecd`). The closeout-3 commit-message wording "always exactly 1 ulp" overstates precision. This strengthens, not weakens, the non-equivalence of libdevice. |
| P6 | preserved on-device gate record present and consistent | **CONFIRMED** — `ON-DEVICE GATE: 55517/55517 bit-identical -- PASS` (`co7_gate_out2.txt`), historical, not re-measured |

## 3. Actual verification (commands and identities)

All steps are re-runnable: `python -B run_gate.py` (in this directory). Executed
2026-09-26 (UTC timestamps inside `parity_gate_result.json`):

1. Pin check: 10/10 pinned files match sha256+size (PREREGISTRATION.md table).
2. Build: `vcvars64.bat` (the lane's path) + `cl /nologo /O2 /fp:precise /EHsc /FI
   host_qual_shim.h ucrt_math.c parity_gate_host.cxx /Fe:parity_gate.exe` — exit 0.
   Compiler: Microsoft (R) C/C++ Optimizing Compiler Version 19.44.35228 for x64
   (MSVC toolset 14.44.35207). `/fp:precise` keeps host contraction off; the
   reconstruction carries explicit `fma()` — the same recipe the lane used for the
   adoption probe (`build_trig_probe2.ps1`).
3. Run probe twice: outputs byte-identical
   (`stdout_sha256_first == stdout_sha256_second ==
   517096e569b6bc7bbeb3e581ab590c5f84fa8e1da9e97962ab2d34f61291d935`).
4. Gates: `FROZEN125 125/125` (bit equality), `DENSE-TOTAL 55392/55392` (bit
   equality, census-exact), fdlibm recount 115/125 (10 diffs all 1 ulp),
   libdevice recount 31/125 (count+distribution), on-device record parsed.

The independent oracle is the MSVC UCRT this probe links (the lane's pinned ground
truth: "the lib on disk as ground truth", closeout-5) — not the reconstruction, not a
fixture, not a reconstruction-of-the-reconstruction.

## 4. Evidence classes (honest labeling)

- **Fresh real runs (this attempt)**: compile + two executions of the frozen probe on
  this machine's CPU; component/records-subject evidence about the pinned math
  implementations (`ucrt_math.c` vs the linked UCRT). NOT an engine run, NOT a fresh
  GPU qualification, NOT a training or walker-runtime claim.
- **Preserved records (hash-pinned, cited, not re-measured)**: `trig_gpu.txt`
  (libdevice class), `trig_fdlibm_out.txt` (fdlibm failure), `co7_gate_out2.txt`
  (on-device gate), `co7_dense_full2.txt`, `co6_trig_dense.txt`, `trig_host.txt`.
- **Records derivations**: the 31/125 and 115/125 recounts are pure text comparisons
  of the preserved records (values shown site-by-site in `parity_gate_result.json`).

## 5. done_when mapping

"Reference-math equivalence is demonstrated at the frozen sites without tolerance
relaxation": the frozen sites are the card's original 125 (probe definitions pinned);
"reference-math equivalence" is bit equality between the adopted reference-math
implementation (the UCRT reconstruction the walker kernels `#define`-redirect to since
closeout-8) and its declared reference (the MSVC UCRT of the C++ parity reference);
"without tolerance relaxation" holds because the pass condition is IEEE-754 bit
equality — any 1-ulp tolerance would fail this gate. Demonstrated fresh (125/125 +
55,392/55,392 dense) and reconciled with the lane's historical legs (fdlibm rejected;
libdevice non-equivalent; on-device gate PASS as a preserved record).

## 6. Remaining gates (stayed open, honestly)

- Fresh GPU/on-device re-qualification and walker-runtime bars are NOT claimed here
  (GPU and engine work are barred for this attempt); they remain with the owning
  runtime lanes. The preserved closeout-7 device record stands as history.
- Independent review of this candidate (queued automatically on publication request).
- Lead-serialized publication; this attempt does not merge anything.

## 7. Containment

All writes stayed inside
`E:\ChimeraWork\monkey-coordination\kanban-attempts\ONT-W02\681e63e9e5d84eaa9702379faf347ac5`
(checkout contribution dir + `build_gate\` scratch). One early driver revision computed
its build dir one level too high; the stray `kanban-attempts/ONT-W02/build_gate`
directory was deleted in the same session before any further writes (nothing else was
created outside the attempt workspace). No GPU, no engine launches, no training,
python -B CPU-only drivers throughout.
