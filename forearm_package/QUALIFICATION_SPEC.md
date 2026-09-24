# QUALIFICATION SPECIFICATION v1 (pass-2) — MECHANICAL GRASP QUALIFICATION (FOREARM PACKAGE)

**Status: DRAFT — NOT APPROVED.** Owner: Astra (external architect). v0 drafted by A10; pass-2 integration (this document) by the coordinator, 2026-09-24, folding in the verified A1–A10 audit results. v0 remains at `audits/A10_spec/qualification_spec_v0.md`.
**Input revision:** `baseline_snapshot/MANIFEST.json` (44 files, crosschecks 4/4 green) + all ten audit reports under `audits/` (every receipt coordinator-re-verified).
**Nothing in this document decides anything.** Numeric criteria remain `[ASTRA-APPROVES: …]` placeholders; statuses carry citations.

---

## 0. PASS-2 DELTA (what changed from v0)

All `[PENDING A<n>]` slots are resolved. Summary of the audit wave (details in §2–§4):

| audit | verdict | one-line result |
|---|---|---|
| A1/A2 wrist | PASS 4/4 each | ambiguity = unwelded seam; verdict-invariant OUTSIDE ≥4.83 mm — consolidated at `findings/I1_wrist_ambiguity.md` |
| A3 source | PASS (+falsifier on prose) | 32/32 exact float/units/roles/provenance; ERRATUM E-1 |
| A4 transforms | PASS 5/5 | reconstruction + bilateral verified; asymmetry is source-authored (S-1) |
| A5 containment | PASS 6/6 | four-class law verified 49/49 synthetically + full recompute; uncertainty budget measured; ERRATUM E-3 (the "~41 µm" number) |
| A6 evidence | PASS 6/6 | taxonomy exists: zero rows above the geometric tier; probative-claim scan clean |
| A7 paths | PASS 5/5 | 42/42 L₀ bit-identical; only BRD/BRD_l functional; 16 grasp tendons null on unresolved bodies |
| A8 arms | PASS 6/6 | FD 5.551e-11; zero-arm law 2.776e-17; transmission set EMPTY — wrist/elbow arms NaN (undefined); ERRATUM E-2 |
| A9 reproduction | PASS 6/6 | 49/49 green, 9/9 byte-identical, determinism ×2; H-1 confirmed at producer level; two package gaps |
| A10 spec | PASS 6/6 | the v0 you are reading the successor of |

**Errata established this wave (documentation-level; artifacts are the record):**
- **E-1** — report 05 §3 line 29 "8 last-endpoints per side": measured **4 per side** (8/0/24 are two-side totals). [A3; confirmed independently by A6, A10]
- **E-2** — report 05 §4-C explains zero arm-deltas by "straight tendon ⇒ zero arm": the paths bend 20–65° at elbow entries; the zeros hold because bends sit on **unresolved-owner** joints. Numbers unaffected. [A8]
- **E-3** — report 05 §4-C "~41 µm" candidate shortfall: **no artifact supports 41 µm**; the exact recorded violation is a single **67.147 µm** breach at ECRL-P3 @ t=0.35, each side (objective decomposed exactly, 2–3e-13 m²). The failure stands regardless — 67 µm also violates `≤ −1 mm`. [A5]

---

## 1. SCOPE & DEFINITIONS

Unchanged from v0 §1 (mission; evidence ladder anchored on report 05 §6 and DERIVATION §12; definitions of site/role/class/authority/comparable-chain/mechanical_qualification) with two verified updates:

- **Role counts (E-1 settled):** per body — 0 `first_endpoint`, **4 `last_endpoint`** (right: `BIClong-P11`, `BICshort-P8`, `BRD-P3`, `PT-P5`; left mirrored), 12 `waypoint`. The artifact is the record.
- **Candidate C shortfall (E-3 settled):** exactly one violated section per side at the optimum (`ECRL-P3`/`ECRL_l-P3` @ t=0.35, 67.147 µm each; `j` recomputed = recorded to 2–3e-13 m²). Any future prose citing the shortfall cites 67.147 µm, not 41 µm.

## 2. REQUIRED TEST CATEGORIES T1–T8 (pass-2 statuses)

### T1 — Containment resolution — **NOT SATISFIED; BLOCKER NOW DECISION-READY**
Artifacts/laws as v0. **A5 verified the machinery end-to-end**: four-class law implemented law-for-law (`target_envelope.py` L264–269, L285–328, L527–533); boundary semantics probe-pinned (d = −1 mm exactly → inside, inclusive; d = 0 → tight; +ε → outside); 49/49 synthetic boundary matrix; **full recompute from mesh+pack reproduces every per-site verdict on both authorities** (loop 6/1/7/2, hull 3/0/5/8 per side).
**A1+A2 (consolidated, `findings/I1_wrist_ambiguity.md`):** all four `unresolved` sites are **OUTSIDE by ≥ 4.83 mm under BOTH identified loops** (skin +4.826/+5.511 mm; sliver +4.872/+5.511 mm; verdict-invariant Δ ≤ 0.077 mm; bilateral mirror-consistency to sub-µm). Mechanism: unwelded seam (exactly-duplicated vertices at the wrist crease — 1,255 duplicated-coordinate vertices mesh-wide) makes the section a self-touching figure-eight; the no-bridging law necessarily yields two 100 %-owned loops.
**Uncertainty budget (A5, measured):** hull band variants 6/8/10 mm halves; hull chord sagitta 187–256 µm; loop edge median 1.11–1.37 mm → sagitta 29–45 µm (median) / 92–220 µm (max); float32 coords ~50 nm; export rounding 1e-9 m. The 67.147 µm candidate breach sits at the loop median-edge scale, ~3× below hull chord scale.
**Remaining for T1:** Astra's resolution rule (see §6-P1/P2/P3 and I1's decision request). Projection under any loop-agreement/degenerate-exclusion rule: 6 inside / 1 tight / **9 outside / 0 unresolved** per side — recorded as a projection, NOT a reclassification; Candidate C's 0/14/0/2 stays dead.

### T2 — Attachment evidence classes — **EVIDENCE COMPLETE; ADOPTION = ASTRA**
A6 delivered the taxonomy: `audits/A6_evidence/table.md` (+csv) — all 32 rows resolve to source(coordinates+membership+role) ⊕ fit(transform+scale+landmarks) ⊕ containment(geometric-only). **Zero rows carry measured-anatomy attachment evidence**; the probative-claim scan over all artifacts returned zero hits (every "qualification" occurrence is negated). Special-site notes cover all 18 non-inside sites with report-05-§6 anchors. `[ASTRA-APPROVES: taxonomy adoption]`.

### T3 — Source fidelity — **SATISFIED (audit-verified)**
A3: 32/32 exact float identity vs raw XML; units verbatim with 0.065 non-application provable per site (min detectability delta 0.0112); roles re-derived; provenance uniform; canonical-hash recipe (`intake.py:57-65`) reproduced exactly. Residual: E-1 prose correction (§0).

### T4 — Transform + bilateral integrity — **SATISFIED (audit-verified)**
A4: reconstruction max 1.15e-9 m export / 5.6e-17 m full precision; `R` verified as scale×rotation by construction (s ≈ 0.2217, det(R) = s³, Q = R/s proper); bilateral mirror max 0.6306 mm (BICshort-P6), mean 0.0547 mm, zero pairs over the 20 mm bound; mode `preserve` recorded (`actual_monkey_fit.json:119-120`, chirality_det +1). **S-1:** the only two real asymmetries (BICshort-P6, FCU-P2) are authored in the source XML (non-mirrored there) — the fit inherits, not creates. Caveat: `runs/mirror_read.json` is the synthetic-twin read (stale, session-4) — never cite as the actual-monkey policy record.

### T5 — Reproducibility / determinism — **SATISFIED (audit-verified; two package gaps → §6-P7)**
A9: `run_tests.py` 49/49 green, exit 0, 8.2 s (Python 3.14.3, numpy 2.2.6, matplotlib 3.10.8); all 9 session-5 run artifacts regenerate byte-identical; two consecutive regenerations agree 12/12; H-1 confirmed at producer level (`actual_target_fit.py:648-649` hashes written bytes after `write_json`). Gaps: S6 assumes `runs/` exists (first pristine run fails until created); scripts hardcode absolute paths (reproduction required a junction). Three stale session-4 side artifacts in `runs/` are labeled (`grounded_chimanoid.json`, `mirror_read.json`, `synthetic_twin.json`) — cite as history only.

### T6 — Path / excursion consistency — **VERIFIED WHERE DEFINED; STRUCTURALLY BLOCKED FOR 16/18 TENDONS**
A7: all 42 defined rest lengths bit-identical to recomputation (max rel dev exactly 0.0); λ rebaseline consistent to 1.2e-16; only BRD/BRD_l possess L₀ and lengthrange′ (margins **+0.986 / +0.975 mm**). The other 16 grasp tendons (ECRB, ECRL, ECU, FCR, FCU per side; PT on ulna) are `path_incomplete: unresolved_bodies` — **T6 for them requires hand/ulna body resolution** (§4-f). Comparability census verified: 42/120; 78 non-comparable enumerated (thorax-only 40, ulna-only 10, hand-only 8, hand+ulna 2, thorax+ulna 2, talus-only 10, talus+toes 6).

### T7 — Transmission non-degeneracy — **MACHINERY VERIFIED; RESULT SET EMPTY — STRUCTURALLY BLOCKED**
A8: analytic arms match the packet bit-exactly; FD crosscheck max 5.551e-11 < 1e-9 (140 finite pairs); candidate zero-arm law holds at 2.776e-17 m. **The nonzero-arm census is EMPTY** — all finite arms are 0.0 or ≤ 1.4e-17 noise; **562/702 pairs are NaN** (elbow_flexion owned by unresolved ulna; wrist triples by unresolved hand_r/l). Grasp transmission at wrist/elbow is **UNDEFINED, not dead** (E-2). T7 is unsatisfiable until hand/ulna bodies resolve (§4-f).

### T8 — Package integrity — **PARTIAL → NEARLY SATISFIED**
A9 confirmed all hash invariants (manifest crosschecks 4/4; H-1 at producer level; regeneration preserves them). Remaining: the candidates-packet self-hash rule and MANIFEST self-coverage — `[ASTRA-APPROVES: …]` as v0 §2-T8.

## 3. CURRENT-STATE TABLE (pass-2)

| Category | Status | Key receipts |
|---|---|---|
| T1 containment | NOT SATISFIED — decision-ready | I1 finding; A5 recompute + uncertainty budget |
| T2 evidence classes | EVIDENCE COMPLETE — adoption pending | A6 table (32 rows, zero above geometric tier) |
| T3 source fidelity | **SATISFIED** | A3 (32/32; canonical recipe reproduced) |
| T4 transforms + bilateral | **SATISFIED** | A4 (+S-1 source-authored asymmetry) |
| T5 reproducibility | **SATISFIED** (two mechanical gaps → P7) | A9 (49/49; byte-identical ×2) |
| T6 path/excursion | verified where defined; **BLOCKED 16/18** on hand/ulna | A7 |
| T7 transmission | machinery verified; **BLOCKED** (empty set, NaN coverage) | A8 |
| T8 package integrity | nearly satisfied; self-hash rule pending | A9; MANIFEST |
| Candidate C | **FAILED — stands** (exact breach 67.147 µm/side, E-3) | experiment record; A5 decomposition |
| `mechanical_qualification` | **FALSE — all 32 sites** | packet per-site flags |
| Mass admission | 0 physically admitted; density validation open | admission ledger (unchanged) |

## 4. EXACT UNRESOLVED BLOCKERS (pass-2)

- **(a) Wrist resolution rule — DECISION READY.** All evidence at `findings/I1_wrist_ambiguity.md`: P1 axial-sweep, P2 ownership (resolves negatively), P3 seam forensics, P5 verdict-invariance are COMPLETE; **P4 (hull SECTION_T band extension past 50.084 mm) is the one baseline change requiring authorization** (pure measurement, no fit change, no margin change). Options (a) degenerate-loop exclusion, (b) loop-agreement verdict, (c) authorize P4, (d) permanent documented uncertainty.
- **(b) Qualification gate.** Unchanged: the flag flips only through the approved, passing T-set.
- **(c) Candidates-packet self-hash.** Confirmed gap; rule = `[ASTRA-APPROVES]` (§6-P4).
- **(d) Environment/reproducibility — RESOLVED** by A9 (T5 satisfied); residual mechanical gaps moved to §6-P7.
- **(e) Item-level:** e1 RESOLVED (E-1); e2 mass admission open (as v0); e3 scope ruling — now sharpened by A7/A8 into (f); e4 RESOLVED (A5 re-measured the full inventory + budget); e5 MANIFEST self-coverage (T8 rule); e6 tendon-less muscle treatment (T6/T7 census wording) — unchanged.
- **(f) NEW — HEAD BLOCKER: hand/ulna body resolution.** 16 of the 18 grasp-relevant tendons have null lengths and null arms because their chains cross `hand_r/hand_l` (8 tendons) or `ulna/ulna_l` (PT + others); wrist and elbow transmission is NaN-undefined (562/702 pairs). No T6/T7 satisfaction, and therefore no mechanical grasp qualification, is possible for those paths until those bodies resolve. Resolution requires new correspondence/landmark evidence and a new fitting session — **architecture and scope belong to Astra** (§6-P6).

## 5. NON-GOALS

Unchanged, verbatim from v0 §5 (baseline frozen; Candidate C's failure stands — citing 67.147 µm, not 41 µm; no second candidate; no displacement; no relaxation; evidence ladder uncrossable; no physics/semantics/muscle-limit/architecture changes without Astra).

## 6. PROPOSALS-FOR-ASTRA (options only — smallest change first)

- **P1 — Wrist resolution by ruling over existing evidence** (no new measurement): loop-agreement verdict or degenerate-loop exclusion; both yield OUTSIDE ≥ 4.83 mm for all four sites on current evidence (I1). Changes: classification records only, append-only; no placement/margin/candidate change.
- **P2 — Authorize hull SECTION_T extension (I1-P4)**: adds the hull diagnostic's independent voice at wrist axials (current coverage ends 50.084 mm < 51.51 mm). Pure measurement; baseline change → needs authorization.
- **P3 — Permanent documented uncertainty at the wrist sites** (if neither P1 nor P2): T1.2 amended by Astra to a stated maximum; those sites' claims capped at "not measured".
- **P4 — Packet self-hash rule** (v0-P4, unchanged; S12 revision-safety applies).
- **P5 — Scope ruling on mass admission** (v0-P5, unchanged; A8 confirms transmission claims at climbing loads would depend on it).
- **P6 — NEW: authorize a hand/ulna body-resolution evidence session** (blocker §4-f). What it needs: correspondence landmarks for `hand_r/hand_l`, `ulna/ulna_l` in the same authored-landmark discipline (DERIVATION §1 — landmarks are the only taste axis), then a new fit session under the same falsifier regime. What it unlocks: T6/T7 for 16 tendons, wrist/elbow moment arms, the actual grasp transmission set. What it does NOT change: the frozen session-5 baseline (new revision chain, own hashes); Candidate C; containment classes.
- **P7 — NEW: package self-containment** (mechanical, from A9): S6 `runs/` auto-creation; path relativization of `run_tests.py:16`, `actual_target_fit.py:58`, `synthetic_fixtures.py:28`, `mesh_target.py:31-32`; ship a one-command reproduce script. No measured values change; touches frozen code → authorization required.
- **P8 — NEW: errata sheet for session reports** (documentation only): E-1 (role counts), E-2 (zero-arm causality), E-3 (41 µm → 67.147 µm), plus the stale-artifact labels. Propose an `ERRATA.md` in the package rather than editing frozen reports.

---

*v1 pass-2 ends here. This document is NOT APPROVED. The decision queue it feeds is `BLOCKER_REPORT.md` (I3).*
