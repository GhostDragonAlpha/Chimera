# MAT2-W02 — Close transcendental parity defects (frozen before any probe run)

Task card: **MAT2-W02**, kind=implementation, group="Walking foundation",
calculation_ids=[C09], verification_profile=`records` (offline,
numerical_evidence_required=true), criteria_sha256
`a9014f57b2cd9b88425fe1a92e26031e4cb7d2fb0884787de385f33736385e19`, scope_sha256
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097` (95-item material
catalog, instruction revision astra-0031).
done_when: **"Reference-math equivalence is demonstrated at the frozen sites without
tolerance relaxation."** Card observation (to be reconciled): *"31/125 sites reported;
fdlibm equivalence must not be assumed."* depends_on: `MAT2-P02`, `MAT2-P03`.

Attempt `296a4a34840e4c81a3a65f95ec491d11`, arrival `arrival-f2170bddbe024617aae68cfdfd9d7b0e`,
isolated checkout `branch-4` @ `9ba1be77228e181f55ed2e4d2eb3e73e2f09685f`; publication base
`astra/gait-capture` @ `8ec90f13e76954596af3711c241c08b843ff78bf`. Sparse contribution path:
`tools/monkey_campaign/contributions/MAT2-W02`.

This preregistration is written and frozen BEFORE any probe in this attempt is built or run.
Constraints honored: no GPU work, no engine launches, no training, `python -B` CPU-only
drivers; a small MSVC host C/C++ compile of the pinned probe is the only native build.
Writes are confined to this attempt workspace; the source repository is read through
read-only `git show`/`git cat-file` only.

## 1. Reconciliation inputs (what already EXISTS, verified read-only)

The material-first adoption says old DONE does not automatically become MAT2-DONE, but
old evidence may satisfy unchanged clauses after checking exact inputs, dependencies and
validity — so this card's contribution is a **re-verification at the current lineage plus
an identity re-binding**, not a new parity implementation.

Historical card `ONT-W02` (read-only scope archive, `kanban_cli.py inbox --task ONT-W02`):
state DONE, winner PR #184 head `531b99354ef241ced711abbaa137105afb28ca5b`, merge commit
`6348533e4c0e25d8968b50e312151f6105146ae4` (merged 2026-09-27T05:40:18Z), criteria
`bf9f89874ee4a7d0606c46215e843474331482444af556ac4f199a6bfcd087f2`, verdict PASS_NO_TOLERANCE
(125/125 frozen sites + 55,392/55,392 dense). Its recorded evidence references:

| class | reference | raw_sha256 |
|---|---|---|
| numerical | `kanban-reviews/ONT-W02/af47151d04f1452a9af24cb95b193700/review_scratch/independent_stdout_run1.txt` | `517096e569b6bc7bbeb3e581ab590c5f84fa8e1da9e97962ab2d34f61291d935` |
| source | `kanban-reviews/ONT-W02/af47151d04f1452a9af24cb95b193700/accept_evidence/run_gate_at_head.py` | `7cd46a8245ed09c3e54cc702b8556c14e7fde66b03d7cd20d2d3384753a03e87` |
| independent_review | `kanban-reviews/ONT-W02/af47151d04f1452a9af24cb95b193700/REVIEW.md` | `f0059b7d8027f18207b2a1ffd4fe4a7dcce78b6950eb7313aa6715950c9fdd29` |

The unchanged clauses are identical between the archived and current card: same
done_when text, same calculation C09, same `records` profile, same falsifier. What changed
is identity (MAT2- namespace, new criteria hash, new scope digest) and dependencies
(`ONT-P02/ONT-P03` → `MAT2-P02/MAT2-P03`).

Dependency receipts read from the live registry:

| dependency | state | PR | head_sha | merge_commit_sha |
|---|---|---|---|---|
| MAT2-P02 | DONE | #196 | `e1606b934f37f057abc6b09e8688eb76afb0f81f` | `8ec90f13e76954596af3711c241c08b843ff78bf` |
| MAT2-P03 | DONE | #194 | `250d6b243947eceb0abd93c6ffadea099a612bd7` | `13a943911da711a4dd24a450055ba0d1b1fe1d04` |

## 2. Frozen pinned inputs (extracted byte-identically, never re-typed)

Extracted with `git -C E:/PythonChimera -c core.autocrlf=false show <ref>:<path>` from BOTH
the historical winner head `531b9935…` and the publication base `8ec90f13…`; the two
extractions must be byte-identical, and each sha256+size must equal the value frozen by the
historical lane (`ONT-W02/run_gate.py` PINS table).

| file | sha256 | bytes |
|---|---|---|
| `frozen_sites/trig_inputs.txt` | `a21467e5e5aeb09f23a6de39c16902c34d2a34ebaa83cbccaab01ba1a0ea8b01` | 349 |
| `frozen_sites/ucrt_math.c` | `cde32a8d36c0fbf481d67fa0005ace7dab08f066971085e543f7909740900b97` | 28375 |
| `frozen_sites/ucrt_math_tables.h` | `cdae6a920bb38d517c11683e11fda0c2f15b6069ab5c1ee4d5bbdd9a62d437ed` | 12970 |
| `frozen_sites/ucrt_math_consts.h` | `106b7cc7cc9823d58092a0eddc4987df5a31f0e02d0705e905292b2759aec938` | 13101 |
| `frozen_sites/preserved/trig_host.txt` | `ed48cf12865115dc8223c0e4ab03ca331144a7c6267ad5e25dda327a9b0a24f2` | 5463 |
| `frozen_sites/preserved/trig_gpu.txt` | `bb896746b5883a3cfd73acccd6b4373496da589aa61361fe58be83237fa9e733` | 5458 |
| `frozen_sites/preserved/trig_fdlibm_out.txt` | `41e484b2bf5be5eba7d7607d029d3221880e1af236ea424d938570dd158c34ed` | 5469 |
| `frozen_sites/preserved/co7_gate_out2.txt` | `54e72577920b1fb0a1cfe068ac482198929bfc208779738c2ddf9c7ab1c740a4` | 155 |
| `frozen_sites/preserved/co7_dense_full2.txt` | `2bc8d9bc9631d58f81cf5c1e1d5774455b40e4c30e50661d62351f49ce909f67` | 203 |
| `frozen_sites/preserved/co6_trig_dense.txt` | `c51cda41db828723bdfa3c9360709f2733927164be05cc21db92727c5d5db8d2` | 2419 |
| `frozen_sites/parity_gate_host.cxx` (gate probe, reused unchanged) | `9cdc67df81b7fd358d7eef83634ba294a4f9ac310500f5d452fe74b51b17c683` | 8766 |
| `frozen_sites/host_qual_shim.h` (reused unchanged) | `39ebeeb939d85345c28dcea41f4ab4e4443f168b4c2a4b3a0e0ac33772c1250a` | 1010 |

The gate driver `run_gate.py` is reused from the merged lane
(`ONT-W02/run_gate.py`, sha256 `7cd46a8245ed09c3e54cc702b8556c14e7fde66b03d7cd20d2d3384753a03e87`)
with **only** its identity header changed (task/attempt/criteria/scope/base fields). No gate
condition, tolerance, site list, input file, oracle or reconstruction byte is altered. Any
change to a pass condition would be a tolerance relaxation and is therefore forbidden here.

## 3. Frozen probes

1. **frozen125** (fresh): all 125 frozen sites (25 pinned inputs × 5 functions SIN/COS/
   ATAN2/ACOS/HYPOT with the exact `trig_probe_host.cxx` argument derivations), computed
   twice per site — once through the linked MSVC UCRT (`sin/cos/atan2/acos/hypot`, the live
   oracle) and once through the pinned reconstruction in `ucrt_math.c`. Pass condition is
   IEEE-754 bit equality of the two hex renderings. **No tolerance parameter exists.**
2. **dense** (fresh): the dense sweep ported verbatim from `trig_probe2_host.cxx`
   (xorshift64* seed `0x243F6A8885A308D3`, same class generators and iteration counts),
   reconstruction vs live CRT, bit equality.
3. **determinism**: run the compiled probe twice; stdout must be byte-identical.
4. **records derivations** (no measurement): recount preserved `trig_gpu.txt` vs
   `trig_host.txt` (libdevice-vs-CRT) and `trig_fdlibm_out.txt` vs `trig_host.txt`
   (fdlibm-vs-CRT); cite the on-device leg from `co7_gate_out2.txt` as preserved history.
5. **lineage reconciliation** (`reconcile_lineage.py`, read-only git + registry): pin
   identity at both refs, ancestry of the historical merge and of both dependency merges
   relative to the publication base, presence of the adopted UCRT transcription in the
   walker kernel at the publication base, and hash verification of the archived evidence
   files named in section 1.

## 4. Predictions (named before any run; each marked CONFIRMED/REFUTED afterwards)

- **P1** frozen125: reconstruction vs live CRT bit-identical at **125/125** sites, zero
  differing bits.
- **P2** oracle stability: fresh live-CRT oracle bits equal the preserved `trig_host.txt`
  bits at all 125 sites (pinned inputs unchanged).
- **P3** dense: zero differing pairs and per-function census summing to 55,392.
- **P4** fdlibm is NOT reference-equivalent: exactly 115/125 bit-identical, 10 differences.
- **P5** libdevice-vs-CRT preserved recount: exactly 31 differing sites distributed
  SIN 5 / COS 5 / ATAN2 6 / ACOS 4 / HYPOT 11; the "always exactly 1 ulp" subclaim is
  expected REFUTED (30 × 1 ulp + HYPOT input 16 at 2 ulps), matching finding F-ONTW02-ULPCLASS.
- **P6** preserved on-device leg record present and internally consistent
  (`55517/55517 bit-identical -- PASS`); it is cited, not re-measured (no GPU here).
- **P7** determinism: two probe runs produce byte-identical stdout.
- **R1** pins: every extracted file matches the frozen sha256+size table at BOTH refs, and
  the two extractions are identical.
- **R2** lineage: historical merge `6348533e…` (ONT-W02 PR #184) is an ancestor of the
  publication base `8ec90f13…`; so are dependency merges `8ec90f13…` (MAT2-P02) and
  `13a94391…` (MAT2-P03).
- **R3** adoption: the walker kernel at the publication base carries the UCRT transcription
  ("THE TRANSCENDENTAL LAW" / explicit-fma precise arithmetic), i.e. the reference math is
  in the production lineage rather than only in a contributions folder.
- **R4** archived evidence integrity: the three ONT-W02 winner evidence files hash to the
  recorded raw_sha256 values, and `ONT-W02/parity_gate_result.json` records
  `gate_stdout_sha256 = 517096e5…` equal to the independent reviewer's run stdout.

## 5. Falsifier (from the card)

"Missing identities or a claimed pass unsupported by records fails; a screenshot is not a
substitute." Concretely, this attempt fails if: any pin mismatches; any frozen site differs
in its final bit; the dense sweep shows any differing pair; the gate reports fewer than
125/125; the driver's tolerance semantics were altered; the historical merge or either
dependency merge is not an ancestor of the publication base; or a claim in the report is not
backed by a named, hashed artifact produced here.

## 6. What this card does NOT claim

No fresh GPU/on-device re-qualification, no engine launch, no walker-runtime or training
claim (GPU/engine work belongs to other lanes and their gates). `records` profile: numerical
evidence only; no camera capture is required by the profile (`clean_view_required=false`,
`camera_required_fields=[]`). Independent review of this candidate and lead-serialized
publication remain open gates; nothing here merges or self-approves.
