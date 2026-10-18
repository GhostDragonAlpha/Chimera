# S4 — Composition and state transfer (mechanism factory)

Gate: GAME_PLAN_ACTION_RPG.md §13.1, row **S4 — composition and state
transfer**: "Two coupled pieces and a second assembly using the same
mechanism | Coupled response versus detailed reference, two-sided exchanges,
no duplicated inventory/DOFs, stable switching where implemented".

Written 2026-10-18 by Maya (mechanism_factory increment). **CPU only**; no
engine boot, no GPU, no published record file touched, nothing committed.
S3 is published (bedadbd3), so reduced composition claims are unlocked and
this increment consumes the S3 reduced response — with its validity query
gating every use, no silent extrapolation through composition.

**Preregistration frozen at 2026-10-18T09:30:46.383865+00:00** (sha256
`2ca2a808491cd5ad9cc33b3ea885116a0b4c20c795e29afac45734d62405886c`),
BEFORE any S4 validation solve. Three earlier prereg-run attempts crashed
on harness mechanics (float-noise Pi keys; sympy bool/string sympify; a
definition-order bug) and froze nothing; those runs are retained in
math-tools/results (`20261018-042428…042917`) and no comparison was run
before the freeze. Final check evidence: `D:/Chimera-Maintenance/Runtime/
local-ai/math-tools/results/20261018-045956-8570c204/result.json`
(scripts `checks_tmp/s4_preregister_check.py`,
`checks_tmp/s4_composition_check.py`, **PASS 48/48**). Receipt:
`s4_composition_receipt_20261018T100039.322493Z.json`.

---

## 1. Step-1 inventory: what already existed, what was added

**Already proven by existing machinery (all re-verified fresh this run):**

- `composed_patch.py` + checks — assembly 1: two qualified fan patches
  (A: n_rim=200, r=1.0, h=0.3, identity; B: n_rim=200, r=0.8, h=0.3,
  inverted) welded apex-to-apex into an hourglass; ONE fused
  `solve_equilibrium` as the reference. Checks (a)–(g): seam single-valued,
  coupled balance at the packet's 1e-6 law, reduction degenerating to the
  qualified piece (dE = 0), real (non-rigid, non-zero) B-port transfer,
  named seam refusals before any solve, supported scales 0.5/1.0/2.0, and
  the two topology witnesses (free rim ring: no equilibrium, residual ~1e0;
  grounded ring weld: bit-for-bit zero transfer).
- `composed_chain.py` + checks — assembly 2 (the second assembly): the k=2
  fan-out star; A and B reused BYTE-IDENTICALLY (sha256 of vertex+face
  blocks; falsifier = any re-derivation) plus new piece C (r=0.5, h=0.25)
  welded at the SAME seam apex (two welded joints, one seam vertex).
  Topology law (witnessed): one apex per piece + rim welds impossible under
  the constant-γ current-area law ⇒ every connected assembly is a
  single-seam star. Checks (a)–(f) including transfer through BOTH welds,
  the new 0.75x scale point, and the measured full scale window
  [0.5, 2.0] under the adopted solver v2.
- `port_solve.py` + checks — the 11.20.5 port-based assembly solve: the
  two pieces coupled through their PORT RESPONSE OPERATORS ONLY (Newton on
  the 3-DOF interface residual — the seam vertex's full displacement; the
  weld consumes every other DOF), validated against the fused-mesh
  reference, with named refusals whose fallback is the fused solve,
  already run and attached.
- `native_binding.py` — record → compile-transaction binding (§11.20
  stage 9): compile reproducible from the record byte-for-byte, domain
  refusals by name. Not exercised by S4 (no engine seam is touched);
  inventoried, unchanged.
- §11.20.5 constraints honored throughout: compatible motion + equal-and-
  opposite exchange in consistent frames at the interface; the assembly
  solve satisfies all pieces together (one-shot evaluation fails by a
  measured 8.2e-1 N vs the 1e-6 gate — the iteration is load-bearing);
  named fallbacks on refusal.

**Untracked receipts at 2026-10-17T03:45–03:55Z — provenance established:**
all eight (composed_patch_receipt ×2, composed_qualification_receipt ×2,
composed_chain_checks ×2, composed_chain_qualification_receipt ×2, plus
piece_record_checks ×2 in the same window) carry
`source_commit = eaf6a9e9` ("step37 independent review of solver v2
adoption + C3 reconciliation"), which POSTDATES the solver-v2 adoption
commit `7d99bdeb`. Every hashed composition source is byte-identical to
the current tree (re-verified this session), all checks PASS, and the
adapter independently verified each qualification receipt. They are the
two consecutive full runs of each battery (a determinism/idempotency
precedent). **Disposition: valid current-machinery evidence, incorporated
as corroboration**; the S4 battery additionally re-derives all 19 checks
fresh at the S3-published HEAD (bedadbd3), which is the primary S4
evidence. Nothing was deleted or silently ignored.

**Added by S4** (checks_tmp scripts + receipt; no repo module edited):
(a) a fresh current-HEAD re-run of all 19 battery checks; (b) reduced
composition on the S3 table with per-use validity gating and named
per-cell fallbacks; (c) per-film two-sided exchange measurement at the
star's TWO welded joints; (d) mechanical ownership maps for both
assemblies; (e) the implemented switching surface (detailed ↔ S3 reduced,
star apex response) with stability checks.

## 2. Column verdicts

### Column 1 — two coupled pieces and a second assembly using the same mechanism: **PASS**

Fresh under bedadbd3, 19/19 battery checks PASS
(composed_patch_checks 7, composed_chain_checks 6, port_solve_checks 6).
Reuse is byte-identical under the CURRENT machinery: A block sha
`5bb740cc29d92102…`, B block sha `7857974be40d3eaf…` — both equal to
assembly 1's; C is a genuinely new piece. The second assembly is a
different topology (k=2 star vs hourglass) built from the same pieces and
the same seam law.

### Column 2 — coupled response versus detailed reference: **PASS**

Two layers, both against the ONE fused-solve detailed reference:

- **Piece-by-piece detailed path (assembly 1):** the port-based solve
  reproduces the fused-mesh reference to A-rim-net diff **3.17e-08 N**,
  B-rim-net diff **2.14e-08 N**, seam position **1.04e-08 wu** (bounds
  1e-6 N / 1e-5 wu, quoted from port_solve.py's frozen prereg), stored
  energy diff **8.33e-09 J** (≤ 1e-6 J), interface residual
  **3.45e-12 N**.
- **Reduced composition (assembly 2):** the S3 η(Π) table
  (`s3_star_eta_pi_table_v1.json`, sha-pinned to its S3 receipt) predicts
  the star's coupled apex response; the validity query returns code 0 for
  EVERY use before any prediction. Worst |Δη| over the four measured
  scales at F = 0.8 N = **5.609e-06** (at s = 1.5, Π = 0.5333;
  stationary, residual 4.2e-14 N) — **56× under T_S4 = 1e-4** (= S3's
  T_S3, quoted, never widened):

  | s | Π | η_pred | η_meas (fresh detailed solve) | \|Δη\| | status |
  |---|---|--------|--------|--------|--------|
  | 0.75 | 1.066667 | 0.248206644295914 | 0.248204695790847 | 1.949e-06 | stagnated, 3.4e-07 N |
  | 1.0 | 0.8 (node) | 0.284380487039174 | 0.284380487039174 | **0 (digit-for-digit)** | stagnated, 7.3e-07 N |
  | 1.5 | 0.533333 | 0.319465273465017 | 0.319470881996502 | 5.609e-06 | stationary, 4.2e-14 N |
  | 2.0 | 0.4 (node) | 0.336652356168765 | 0.336652356168765 | **0 (digit-for-digit)** | stationary, 1.1e-13 N |

  The predictor is pinned to the published S3 receipt: it reproduces the
  recorded η_predicted at Π ∈ {0.6, 1.0, 1.4, 1.8} to ≤ 1e-15 and every
  node digit-for-digit.
- **No silent extrapolation through composition:** a reduced WORKLOAD
  containing a refused cell is refused for that cell and falls back per
  cell, by name: (s=1.0, F=2.5 N) → code 4 (packet cap max_force_N=2.0);
  the named detailed fallback solves in-gate (residual **1.49e-07 N**).
  (s=1.0, F=0.2 N) → code 6 (unmeasured Π gap (0, 0.4)); fallback
  in-gate (**3.95e-13 N**). (s=3.0, F=0.8 N) → code 3 (scale window), AND
  the detailed path is refused by the SAME packet scale law
  (`unsupported_scale`) — both refusals named, no solve invented.

### Column 3 — two-sided exchanges: **PASS**

- **Hourglass (existing, fresh):** at convergence the interface exchange
  is closed — F_A + F_B + f = 0 to **3.45e-12 N**, both pieces at
  BIT-IDENTICAL seam positions, the massless joint creates no net work
  (**5.40e-13 J** ≤ 1e-7 J) over the solved displacement.
- **Star, both welded joints (new):** the three films' seam forces are
  measured INDEPENDENTLY — each piece's qualified pinned-response
  operator evaluated at the converged shared seam position — at s=1.0 and
  s=2.0 (F = 0.8 N):
  - s=1.0: closure |F_A + F_B + F_C + f| = **7.32e-07 N** ≤ 1e-6 N;
    Newton's third law at each weld, measured on both sides (A's own
    measured film force vs −(F_B + F_C + f) from the B/C sides):
    **7.32e-07 N**; frames bit-identical; transfer real through BOTH
    welds: |F_B| = **0.9224 N**, |F_C| = **0.7370 N** (margin ≥ 0.1·max(1,|f|)).
  - s=2.0: closure and third-law residual **1.06e-13 N**; |F_B| = **1.572 N**,
    |F_C| = **1.233 N**.
  - Honest framing: because A's share is measured independently while the
    B/C side sum is defined by the same vertex balance, the third-law
    residual coincides with the seam vertex's force-balance residual —
    which is exactly the quantity the packet's 1e-6 law bounds (at s=1.0
    it equals the fused solve's measured seam residual 7.32e-07 N, the
    same number composed_chain check (c) measures on the joined mesh).
    The two-sided content is that BOTH sides' forces come from
    independent piece solves that agree to the packet law.

### Column 4 — no duplicated inventory/DOFs: **PASS**

Mechanical ownership maps, asserted structurally (any violation raises;
fails loudly):

- assembly 1 (401 vertices, 400 faces): A rim+seam-owner block (201) + B
  far rim (200) = EXACT vertex partition; face blocks {200, 200} exact;
  400 pins unique; free-DOF count = **3** (the single seam vertex's
  displacement — the weld consumes every other DOF, counted once).
- assembly 2 (601 vertices, 600 faces): A (201) + B far rim reused (200)
  + C far rim new (200) exact partition; face blocks {200, 200, 200}
  exact; 600 pins unique; free-DOF count = **3**.
- no duplicated coordinates anywhere (min vertex distance 0.0251 wu /
  0.0157 wu > 1e-9 wu); the falsifier fires: an injected duplicate seam
  vertex trips the uniqueness probe (measured delta 0.0 ≤ 1e-9 wu).

### Column 5 — stable switching where implemented: **PASS (implemented; named surface)**

Switching IS implemented for ONE named surface: the k=2 star's apex
response between the detailed fused solve and the S3 reduced η(Π) map.
The hourglass has NO reduced representation (the S3 table is
assembly-level and star-only) — it is served by the port-based detailed
path; this is stated, not hidden.

- **Idempotence:** the reduced query on the same state is bit-identical
  over 100 repeats (pure function).
- **Detailed → reduced:** on every measured cell the state's own
  (Π, η = z/s) re-queries valid (code 0) and |η_pred − η_state| ≤ T_S4
  (same numbers as column 2).
- **Reduced → detailed round trip:** a fresh fused solve with the seam
  rest position pre-set to the reduced prediction (z = 0.284380487039174
  wu, the Π = 0.8 node) converges to z = 0.284380303981340 wu —
  |z_rt − z_detailed| = **1.831e-07 wu** (bound 1e-6 wu), exactly the
  S1/S3 solver noise floor 1.831e-07 — in-gate (stagnated, 6.39e-07 N);
  the switched-back state re-queries valid and within T_S4.
- **Out of domain:** the switch to the reduced map at (s=3.0, F=0.8) is
  refused by name (code 3) and the named detailed fallback is likewise
  refused by the packet scale law — switching never silently extrapolates.

## 3. Verdict

**S4 PASS, scoped exactly to the gate row.** Two coupled pieces (A+B) and
a second assembly (k=2 star) using the same mechanism, A and B reused
byte-identically under current machinery; coupled response verified
against the detailed fused reference both piece-by-piece (port operators,
~3e-8 N agreement) and via the S3 reduced composition (worst |Δη|
5.609e-06 ≤ T_S4, validity query gating every use, refusals named per
cell); two-sided exchanges closed at the hourglass interface and at BOTH
star welds with real, distinct transfer; inventory/DOF ownership exact in
both assemblies with free-DOF count 3 and a firing duplicate probe;
switching implemented for the named star-apex surface and stable
(idempotent, bounded, round-trips to the noise floor, refuses out of
domain).

**Named explicitly (not hidden):**
(a) the S3 reduced response is ASSEMBLY-level (the star's apex response)
and the only published reduced representation consumed; "piece-level"
validity gating maps to per-assembly-use gating here; the γ axis is
degenerate (γ = 1.0 only, S0 gap 6) and the query refuses elsewhere;
(b) the hourglass has no reduced representation — column 5's switching is
implemented only for the named star surface;
(c) the s=1.0 star closure (7.32e-07 N) sits at 73% of the preregistered
1e-6 bound — it IS the fused solve's own seam-vertex residual under the
packet law (the same number check (c) of composed_chain measures), not a
film-measurement artifact; at s=2.0 it is 1e-13;
(d) the solve budget: 258 `solve_equilibrium` calls total — the ~40 full
coupled solves this report's numbers come from, plus the port battery's
pinned response evaluations (each a tiny all-vertices-pinned stationary
evaluation at max_steps=10, the machinery's qualified port pattern);
wall ~34 s battery + ~8 s S4-specific;
(e) the three crashed pre-freeze prereg runs are retained in
math-tools/results and froze nothing;
(f) no piece-record claim is made or amended; all composition claims live
in the S4 composition receipt.

## 4. Reproduction

```
# prereg (freezes before any solve; already frozen)
math_check.py checks_tmp/s4_preregister_check.py
# main (19 battery checks + reduced composition + refusals + two-sided
#  + ownership + switching; ~40 s)
math_check.py checks_tmp/s4_composition_check.py
```

Scripts: `D:/Chimera-Maintenance/Runtime/local-ai/math-tools/checks_tmp/
s4_preregister_check.py`, `…/s4_composition_check.py`. Evidence dirs:
`…/results/20261018-045956-8570c204` (final; earlier crashed prereg runs
retained alongside). Artifacts: `s4_preregistration_
20261018T093046.383865Z.json`, `s4_composition_receipt_
20261018T100039.322493Z.json`, both under
`docs/evidence/mechanism_factory/`. Every number in this report is
present in the receipt.
