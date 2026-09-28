# ONT-W01 — report

- Card `ONT-W01` (planning `W01`), kind `implementation`, profile `records` (offline).
- Objective: close the tick-3 discrete forelimb parity defect — done_when
  **"Frozen entry-state and event traces satisfy the existing CPU/GPU acceptance bar"**
  (C09: CPU/GPU parity and time stepping).
- Attempt `01a01bf2759648f687e7eb7113998f23`, agent `arrival-195e6b7256e942988473e20a03dce315`,
  branch `branch-7`, base `c525b82c7c3ce0128565424764293a3c85811ab3`,
  criteria `c42bd4f9ce228ebddcb1be6c87b261979c8a38987ff3d5e74ad37536f397be24`.
- PREREGISTRATION frozen BEFORE any probe or implementation:
  commit `df0fd8f8d7bdad42d9476c232a506f9b7cba4c8a`, blob `6bd7e3c94e14897ffe0280ebe31f9322b1fc3a5d`.
- Deliverable: `implementation.py` (the records verifier, stdlib, read-only, CPU-only),
  `test_implementation.py` (fixtures + mutation controls), `parity_records_audit.json`
  (official probe output, rerunnable via `python -B implementation.py --out parity_records_audit.json`).

## Verdict

**done_when SATISFIED_BY_RECORDS** — official probe 2026-09-26, all predictions
P1..P9 PASS (zero falsifiers fired; predictions executed exactly as frozen; the two
instrument defects found while building the comparator are recorded in §5 — both were
fixed before the official run and are themselves record-backed).

## 1. Clause-to-evidence map (done_when -> records)

| Clause component | Pinned record(s) | Measured (probe P-check) |
|---|---|---|
| Frozen entry state (the tick-3 event class) | fixture `state_t40_host.txt` == `state_t40_gpu.txt` (byte-identical); `state_t39_cpp.txt` differs only by the tick label; cross-linked to walk-pair lines; scene `f6844eea…` | **P2 PASS** — host/GPU entry-state bytes equal; cpp label-only; bodies equal `hl FULL t=40` / `cp FULL t=39`; scene sha exact |
| Event traces (walk pair, incl. the tick-3 window) | `cp_walk45.txt` vs `hl_walk45.txt` | **P3 PASS** — bit-exact for every aligned state t=1..41 incl. tick-3 window t=1..4; first divergence at aligned t=42 (the already-named next defect) |
| The defect was real (event traces recorded it) | `csub_t5.txt` vs `ksub_t5.txt` @ `7a845267` (defect era) | **P4 PASS** — first diverging SUBPRE census record is exactly `t=3 sub=3` (q0..q15+ differ; records 0..14 bit-exact), the closeout-3 named forelimb event |
| Event traces satisfy the bar post-fix | `csub41L.err` vs `ksub41N.out` | **P5 PASS** — census 20/20 SUBPRE + 20/20 TAUFULL + 20/20 SUBFULL, zero physics-token divergences (SUBFULL sub-label drill convention measured, kernel = starting substep + 1, consistent across all 20) |
| Existing CPU/GPU acceptance bar: replay | `co8_hl_v2.out` | **P6 PASS** — walks past tick 41 to t=100, final line exactly `tick 100: y=0.215657301 vx=0.664807 rc=0 adv=7 refused=0 ticks=100`, no REFUSED line, 100 FULL states |
| Existing CPU/GPU acceptance bar: pre-v2 vs v2 | `co8_hl_full6.out` vs `co8_hl_v2.out` | **P7 PASS** — bit-identical t=1..40, first divergence at exactly t=41 |
| Existing CPU/GPU acceptance bar: host-GPU parity | `co8_dll_v2b_120.txt` vs `co8_hl_v2.out` | **P8 PASS** — bit-identical on every FULL state t=1..43 (0 differing ticks) |
| The bar's own measured outcomes, truthfully recorded | `bars_split_b32.json` | **P9 PASS** — freefall GREEN `g=9.806650000000689` err `6.89e-13` `parity_pass=true`; stand RED `0.9511245759469239` `parity_pass=false`; C1 horizon 40 class 5 hind=0 fore=0; C2 64 seeds median 40.0, max horizon < 100 |
| Identities of every claim | archive tag + commits | **P1 PASS** — tag → `a62b286e`; all 11 pinned commits resolve; pinned bar sentences present in `2dee187d`/`3ab21e5f`/`055d6c05` messages; P02P03 report @ `8feea42a` carries the W01 CLOSED ruling |

## 2. Reconciliation (the map's "residual open" is resolved by newer receipts)

The completion map's observation ("Last user status: residual open; reconcile newer
receipts") is reconciled, reusing verified work per the card's steps:

1. **Defect named** — closeout-3 `7a845267`: forelimb discrete event inside tick-3's
   substep-2→3 advance with a bit-exact entry state; first diverging census record
   SUBPRE t=3 sub=3 (re-measured here from the defect-era records, P4).
2. **Defect fixed** — closeout-4 pairs 4-8 `2dee187d`/`3ab21e5f` (crossing-bisection
   end-state evaluate; end-state save vs scan clobber; per-point friction row;
   swallowed-require guards; poscorr gram stride+operands): bit-exact through 41
   aligned walk states, tick-3 and tick-41 interiors line-identical, census 20/20
   (re-measured here from the post-fix records, P3/P5).
3. **Ruled closed** — P02P03 lineage reconciliation `8feea42a` §2: W01 **CLOSED** by
   those receipts; frontier later strengthened (60 states `77023970`, 66->71
   `37ab0c8f`, 73->74 `2c1dc8f2`, bit-exact through aligned state 74 with a named
   cpp-vs-host 1-ulp FK class at `b643a850`).
4. **Tie-v2 battery** — prereg `9376c3d8`, executed per TIE2 `055d6c05`: host replay
   past tick 41 to t=100 rc=0 (P6), host-GPU v2 parity t=1..43 (P8), edge-split on
   the ulp, outside-band byte-identical.

This card's implementation is the missing **task-owned artifact**: W01 previously had
no owned records verification anywhere — the closure evidence lived only inside commit
messages and branch-only worktrees. The verifier binds each done_when component to the
pinned record bytes and re-derives the verdict with an independent oracle, so the
closure is now checkable without trusting any prose.

## 3. Evidence classes (labeled honestly)

- **Records/offline** (the card's declared profile): every check compares
  git-object-pinned bytes (raw sha256 + blob oid recorded in
  `parity_records_audit.json.identities`), via exact token equality; the comparator
  has no tolerance parameter (F4 cannot fire by construction).
- **Numerical**: required and present — alignment indices, first-divergence
  identities (t=3 sub=3; t=41; t=42), census counts (20/20/20), bars numbers.
- **Not claimed**: no live GPU re-run (TIE2 Q1/Q2 queued — W03 scope), no engine
  rebuild, no screenshot or visual artifact (records profile nonvisual reason
  recorded), no trained-walking acceptance (W05+), and the walk-level GPU bars beyond
  the recorded freefall GREEN.

## 4. Boundaries (named, not silent)

- The walk-level acceptance bar is **not** fully green and this report does not claim
  it: stand/C1/C2 RED residuals in `bars_split_b32.json` are the class-41
  contact-residual knife (`g0=-6.9e-18`) plus scene-design knife edges, **charged to
  W03** by the P02P03 ruling (tie-v2 + anchor-version decision + C3 clean window).
  They are recorded as measured (P9), not tuned and not absorbed.
- The tick-3 defect's own subject — the frozen entry state and event traces under the
  existing bar — is closed by the records above.
- Out-of-scope items already owned elsewhere: anchor-version A/B (Astra/W03), C++
  reference leg of the tie (W03 gap #4), W04 mass-denominator binding
  (`first_skill/acceptance.py` M_BODY_KG — named in the P02P03 reconciliation).

## 5. Instrument honesty record

Two comparator defects were found and fixed while building the verifier, both before
the official probe run and both resolved against the records themselves:

1. The kernel-side drill labels SUBFULL records with the **ending** substep while the
   C++ side uses the starting substep — a naive positional comparison reported a false
   identity mismatch at the first SUBFULL. Fixed by kind-wise comparison on physics
   tokens; the convention is now a measured audit field
   (`subfull_sublabel_convention_measured: true` for all 20 records).
2. The P6 expected-summary string initially included the `tick 100:` prefix that the
   parser itself strips — an instrument artifact, fixed; the measured summary line is
   byte-exact against the pinned claim.

No prediction was amended after measurement; the frozen predictions P1..P10 and the
frozen done_when decision rule in `PREREGISTRATION.md` are the ones executed.

## 6. How to re-run

```bash
cd tools/monkey_campaign/contributions/ONT-W01
python -B -m unittest test_implementation -v          # 23 tests, fixtures + mutation controls
python -B implementation.py --out parity_records_audit.json   # official probe; exit 0 iff SATISFIED
```

Requires only the git object database (tag `archive/20260925/agent/typeb-gpu-finish-20260922`),
Python 3 stdlib, CPU. No GPU, no network, no writes outside `--out`.
