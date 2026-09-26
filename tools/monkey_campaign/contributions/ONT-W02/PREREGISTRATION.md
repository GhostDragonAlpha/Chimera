# ONT-W02 — Close transcendental parity defects (frozen before any probe run)

Task card: W02, kind=implementation, group="Walking foundation", calculation_ids=[C09],
verification_profile=records (offline, numerical_evidence_required=true), criteria_sha256
`bf9f89874ee4a7d0606c46215e843474331482444af556ac4f199a6bfcd087f2`.
done_when: **"Reference-math equivalence is demonstrated at the frozen sites without
tolerance relaxation."** Card observation (stale, to be reconciled): *"31/125 sites
reported; fdlibm equivalence must not be assumed."*

This preregistration is written and frozen BEFORE the probes below are built or run.
Attempt: `681e63e9e5d84eaa9702379faf347ac5`, arrival `arrival-535a6d99aaf94c78b3aed6a239885498`,
base revision of the attempt checkout (branch-8): `155a0f5c6ed14d6ce0c95572676eb03f14bc8a50`.
Constraints honored: no GPU work, no engine launches, no training, python -B CPU-only
drivers; a small MSVC host C compile of the pinned probe is the only native build.
Writes are confined to this attempt workspace.

## 1. Reconciliation (read-only git pins; what EXISTS already)

The 125 frozen sites and the whole parity lane live in archive ref
`refs/chimera-archive-source/20260925/agent/typeb-gpu-finish-20260922` (head `a62b286e`,
lane commits: `2c062c2c` closeout-3, `77023970`+`11df019c` closeout-5, `714eba2b`/`c7058a6f`/
`d0b5eda8`/`7b092267`/`9e2e5c41` closeout-7, `e3b591e1`/`ef3f3554` closeout-8).
None of it is an ancestor of the current production head, and the card still says
"31/125 sites reported" — the implementation_state=UNRECONCILED gap this card owns.

Verified history (commit-message records + preserved output records):
- closeout-3 (`2c062c2c`): the frozen probe `trig_probe.cu` vs `trig_probe_host.cxx` on
  `trig_inputs.txt` — **31/125** sampled evaluations differ in the final bit between CUDA
  libdevice and the MSVC CRT (SIN 5/25, COS 5/25, ATAN2 6/25, ACOS 4/25, HYPOT 11/25),
  always exactly 1 ulp.
- closeout-5 (`77023970`): a netlib fdlibm port probed the same 125 points — **115/125**
  bit-identical, 10 differ by exactly 1 ulp → the 125/125 adoption gate FAILED; fdlibm
  was NOT adopted ("fdlibm equivalence must not be assumed" is a measured fact, not an
  assumption).
- closeout-7 (`d0b5eda8`, `7b092267`, `9e2e5c41`): a bit-exact reconstruction of the actual
  UCRT objects (`ucrt_math.c` + generated tables/consts, transcribed from the extracted
  `libucrt.lib` disasms) reached **125/125** bit-match host-side and the dense sweep
  **55,517/55,517** bit-identical host-side (`co7_dense_full2.txt`), then the CUDA port of
  the same reconstruction passed the **on-device gate 55,517/55,517 bit-identical**
  (`co7_gate_out2.txt`, device vs host CRT).
- closeout-8 (`e3b591e1`): the reconstruction was adopted into the walker build
  (`#define`-redirect of sin/cos/atan2/acos/hypot, `-DUCRT_MATH_DEVICE`, `-fmad=false`).

## 2. The frozen sites (exact definition, pinned identities)

A frozen site is one (function, input) pair from the card's original probe: 25 pinned
inputs (12 exact tick-1 rot-axis angles + a synthetic IK grid; `trig_inputs.txt`,
25 one-per-line doubles) x 5 functions, with the exact argument derivations of
`trig_probe_host.cxx` / `trig_probe.cu` (git blobs `007c6f6a`, `8751479e`):

- SIN(i): sin(x)
- COS(i): cos(x)
- ATAN2(i): atan2(wy, wx), wy = sin(x*0.5)*0.2, wx = 0.3 + cos(x)*0.15
- ACOS(i): acos(clamp(1.0 - |x|*1e-6, -1.0, 1.0))
- HYPOT(i): hypot(wx, wy)

125 sites total. The reference math implementation under test is the adopted
`ucrt_math.c` reconstruction (blob `efd87d67`, sha256 `cde32a8d...8b01a0ea8b01`-family
below); its declared reference/oracle is the MSVC UCRT the C++ parity reference
(`gait_controller_ref.hpp`) links on this machine — the lane's pinned ground truth
("the lib on disk as ground truth", closeout-5 standing order).

Pinned input/source identities (byte copies under `frozen_sites/`, extracted with
`git -c core.autocrlf=false show` from `a62b286e`; sha256 at extraction):

| file | git blob (a62b286e) | sha256 | bytes |
|---|---|---|---|
| frozen_sites/trig_inputs.txt | 252366b2d1106a13f87bb3cf8380c0202f97f71c | a21467e5e5aeb09f23a6de39c16902c34d2a34ebaa83cbccaab01ba1a0ea8b01 | 349 |
| frozen_sites/ucrt_math.c | efd87d67b114c350c1a8e081183d3a139a35a3df | cde32a8d36c0fbf481d67fa0005ace7dab08f066971085e543f7909740900b97 | 28375 |
| frozen_sites/ucrt_math_tables.h | bf81305a13fa11437d31238ae2791b89a3d349e1 | cdae6a920bb38d517c11683e11fda0c2f15b6069ab5c1ee4d5bbdd9a62d437ed | 12970 |
| frozen_sites/ucrt_math_consts.h | 74e86ae2d55f7ca3eeccf6003b94f552bb05e229 | 106b7cc7cc9823d58092a0eddc4987df5a31f0e02d0705e905292b2759aec938 | 13101 |
| frozen_sites/preserved/trig_host.txt | 0a89550d6fe1aedc205c3b34835d83b8f8c85ca1 | ed48cf12865115dc8223c0e4ab03ca331144a7c6267ad5e25dda327a9b0a24f2 | 5463 |
| frozen_sites/preserved/trig_gpu.txt | 5ba31ec7a1f527ffa86ab4f5b7d08718a0abc6c5 | bb896746b5883a3cfd73acccd6b4373496da589aa61361fe58be83237fa9e733 | 5458 |
| frozen_sites/preserved/trig_fdlibm_out.txt | d9cf26eac0f65fdb7790820c056eed9866856b97 | 41e484b2bf5be5eba7d7607d029d3221880e1af236ea424d938570dd158c34ed | 5469 |
| frozen_sites/preserved/co7_gate_out2.txt | f7fbfb11258f6ec3fb24f048541c32cda10f1cfc | 54e72577920b1fb0a1cfe068ac482198929bfc208779738c2ddf9c7ab1c740a4 | 155 |
| frozen_sites/preserved/co7_dense_full2.txt | af66ec6a229738fa90c47498b40e1769ea092d2e | 2bc8d9bc9631d58f81cf5c1e1d5774455b40e4c30e50661d62351f49ce909f67 | 203 |
| frozen_sites/preserved/co6_trig_dense.txt | 23fed41a5e5a0986b0505afab709af433873f654 | c51cda41db828723bdfa3c9360709f2733927164be05cc21db92727c5d5db8d2 | 2419 |

## 3. Frozen probes (exact, before execution)

Probe A — `parity_gate_host.cxx` (new, task-owned, compiled `/O2 /fp:precise /EHsc` with
the pinned `ucrt_math.c` via MSVC vcvars64; contraction stays off on the host because the
reconstruction carries its own explicit `fma()`):
1. **frozen125 section**: recompute all 125 sites twice per site — once through the linked
   CRT (`sin/cos/atan2/acos/hypot` — the live oracle) and once through the pinned
   reconstruction (`ucrt_sin/ucrt_cos/ucrt_atan2/ucrt_acos/ucrt_hypot`) — printing IEEE-754
   hex bits for both. Zero tolerance: the gate is bit equality (`016llx` string equality).
2. **dense section**: the dense sweep generator ported VERBATIM from
   `trig_probe2_host.cxx` (git blob `5bfe2c46`): xorshift64* seed `0x243F6A8885A308D3`,
   the same class generators and iteration counts, reconstruction vs live CRT, bit equality.

Driver — `run_gate.py` (python -B): verifies pinned sha256s BEFORE building, builds in a
scratch dir under the attempt workspace, runs the probe, then cross-checks against the
preserved records (below) and writes `parity_gate_result.json` plus a per-site ledger.

Records derivations (no run, pure record analysis):
3. Recount the **31/125** class by text-comparing preserved `trig_gpu.txt` (libdevice)
   against preserved `trig_host.txt` (CRT) bit columns; assert every differing pair is
   exactly 1 ulp (adjacent doubles).
4. Parse preserved `trig_fdlibm_out.txt` vs `trig_host.txt` → expect 115/125 with the 10
   differences at exactly 1 ulp.
5. Parse preserved `co7_gate_out2.txt` and `co7_dense_full2.txt` → cite the lane's
   on-device gate (55,517/55,517) and host dense totals (6421/6421, 40425/40425, 1025/1025,
   1225/1225) as preserved device/history evidence — NOT re-measured here.

## 4. Predictions (named before the run; each marked CONFIRMED/REFUTED in report.md)

- **P1**: Fresh host gate, frozen125 section: reconstruction vs live CRT bit-identical at
  **125/125** sites; zero differing bits.
- **P2**: The live CRT oracle bits equal the preserved `trig_host.txt` bits at all 125
  sites (no oracle drift on this machine since the record was made).
- **P3**: Fresh host gate, dense section: **0** differing bits. Predicted totals from the
  frozen generator's arithmetic (counted from the source BEFORE the run): sin 6396,
  cos 6396, atan2 40400, acos 1000, hypot 1200; grand total 53,392 evaluations.
  (This is my probe's own census; the lane's preserved 55,517 total came from the lane's
  own final probe build and is cited as history, not re-claimed.)
- **P4**: Preserved fdlibm record vs preserved CRT record: 115/125 identical; 10 differing
  pairs all exactly 1 ulp → fdlibm is NOT reference-equivalent; the substitution used is
  the UCRT reconstruction, not fdlibm.
- **P5**: Preserved libdevice-vs-CRT recount: **31** differing sites, every difference
  exactly 1 ulp, distribution SIN 5, COS 5, ATAN2 6, ACOS 4, HYPOT 11.
- **P6**: Preserved device record `co7_gate_out2.txt` states 55,517/55,517 bit-identical
  ON-DEVICE (historical; GPU work is barred for this attempt, so this stays a preserved
  record with its hash, never a fresh claim).

## 5. Falsifiers (any one fails the card)

- F1: any differing bit in Probe A frozen125 (reconstruction vs live CRT) — equivalence
  with any tolerance (1 ulp, relative eps, "close enough") is a FAIL by definition.
- F2: any differing bit in Probe A dense section.
- F3: oracle drift (P2 refuted) without an explicit recorded finding and re-pin.
- F4: any claim that fdlibm equivalence, libdevice parity, or a fresh GPU qualification
  was demonstrated here (they are not; each is labeled preserved-record evidence).
- F5: a missing identity (any pinned file whose sha256 differs at verification time), or
  a claimed pass unsupported by the actual run outputs.

## 6. Evidence classes (labeled honestly)

- Fresh evidence (this attempt, CPU-only host): bit-equality of the pinned UCRT
  reconstruction against the live MSVC UCRT at the 125 frozen sites and over the dense
  sweep. This is component/records-subject evidence about pinned math implementations —
  it does NOT by itself re-qualify the GPU runtime or the engine.
- Preserved evidence (hash-pinned, cited, not re-measured): libdevice 31/125 class,
  fdlibm 115/125 failure, on-device gate 55,517/55,517, lane dense totals.
- Not claimed anywhere: fresh GPU runs, engine launches, training, walker runtime bars.
