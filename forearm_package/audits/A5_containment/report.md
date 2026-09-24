# A5 — CONTAINMENT AUDIT REPORT (containment authority, signed distances, numerical uncertainty, four classes)

**Auditor:** A5 (audit agent) · **Date:** 2026-09-24 · **Scope:** `forearm_package/baseline_snapshot/` (READ-ONLY)
**Brief:** `brief.md` (verbatim copy of the task brief). **Preregistration (frozen):** classes reproduce exactly from recorded data; synthetic probes match the law at every boundary; the 41 µm shortfall is below the loop discretization scale. **Falsifier:** any class change on reproduction, or any synthetic probe violating the class law.

**Baseline integrity (criterion 6) — PASS.** `git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot` → empty, exit 0. Input bins hash-match the recorded meta (`550a5b3e…` mesh, `74b3ab04…` pack). Last commit touching the baseline: `0ad24b02`.

---

## VERDICT SUMMARY

| # | criterion | verdict |
|---|---|---|
| 1 | class-law quote + code-vs-docstring | **PASS** (3 minor documentation gaps, behavior lawful) |
| 2 | synthetic boundary matrix | **PASS** — 49/49 probes match the law |
| 3 | 32-site × 2-authority reproduction | **PASS** — exact, both from records and recomputed from inputs |
| 4 | uncertainty budget + 41 µm situating | **PASS as measurement** — with FINDING F4 (prose 41 µm vs recorded 67.15 µm) |
| 5 | authority-labeling audit | **PASS** |
| 6 | baseline integrity | **PASS** — porcelain empty |

**Falsifier status: NOT FIRED** — no class changed on reproduction; no synthetic probe violated the class law. No machinery defect found.

---

## 1. Class-law audit (criterion 1) — PASS

The session-05 §2 law and its implementation in `code/target_envelope.py`:

**Per-variant class (hull path), L264-269 (inside `containment()`):**
```python
def _cls(d: float) -> str:
    if d > 0.0:
        return "outside"
    if d <= -margin_m:
        return "inside"
    return "inside_tight"
```

**Variants + aggregation, L285-328:** `variants = [("nominal","hull_bc"), ("narrow","hull_bc_narrow"), ("wide","hull_bc_wide")]`; `setc = set(classes)`; `len(setc) > 1 → unresolved` ("radial_cap_sensitivity: class flips…"); `{"outside"} → outside`; `{"inside_tight"} → inside_insufficient_clearance` (reason: "inside the hull at every band-width variant but clearance never reaches the required margin"); `else → inside`. Missing/unusable variant geometry → unresolved "no_vertices" (L291-302). No sampled band within `half` of the site axial → unresolved "local_narrowing" (L276-282).

**Law-vs-code, row by row:**
| session-05 law | implementation | match |
|---|---|---|
| outside = d>0 at every variant | `_cls` row 1 + `setc == {"outside"}` | yes |
| inside_insufficient_clearance = d≤0 at every variant, clearance never reaches 1 mm | `_cls` row 3 (−margin < d ≤ 0) + `setc == {"inside_tight"}` | yes |
| inside = d≤−1 mm at every variant | `_cls` row 2 (d ≤ −margin, inclusive) + else-branch | yes |
| unresolved = class flips under band-width variation, or no sampled band near the axial position | `len(setc)>1`; `local_narrowing`; `no_vertices` | yes |

**Loop path (the authority), `section_loop_containment()` L527-533:** `d > 0 → outside`; `d <= -margin_m → inside`; `else → inside_insufficient_clearance`. Section ambiguity: `len(identified) != 1 → unresolved` "ambiguous_section … no bridging, no repair, no proximity choice" (L512-519). Docstring L463-465 matches the code exactly.

**Boundary inclusivity (probe-pinned):** d = −1 mm exactly → `inside` (inclusive `<=`); d = 0 exactly → `inside_insufficient_clearance`; d = +ε → `outside`.

**Documentation gaps (findings, minor — behavior lawful in all three):**
- **F1.** `containment()` docstring L243 still carries the session-4 vocabulary: "Verdict per site: ok | outside | unresolved(narrowing | no_vertices)". The code's per-site verdicts are inside | inside_insufficient_clearance | outside | unresolved; `ok` is a summary flag (L338), not a verdict; the tight class is absent from that line. The session-5 law lives in the inline comment L261-263 and the returned `claim` (L348-355).
- **F2.** The flip reason string (L315-317) says "class flips between inside and outside", but the code flags ANY class mix across variants — including an inside ↔ inside_tight flip (probe-verified, Part 2). The string is narrower than the behavior; the behavior matches the law ("class flips").
- **F3.** `_dist_to_poly` docstring L187-188 says "measured to the nearest polygon point"; the code measures to the nearest point on the boundary EDGES (point-to-segment min, L193-198) — the standard boundary distance, and it agrees with my independent reference implementation to <1e-9 on every probe. Loose wording, correct behavior.

---

## 2. Synthetic boundary probes (criterion 2) — PASS, 49/49

Own geometry only (96-gons, squares, chamfered-square and circular tube meshes; no baseline data). Expected classes derived from an independent distance implementation written in the probe script; exact float boundaries pinned with axis-aligned squares. Full matrix: `receipts/synthetic_probes.json`.

**Exact boundary semantics (square; floats exact):**
| probe | expected | observed |
|---|---|---|
| d = 0 exactly (on edge) | inside_insufficient_clearance | inside_insufficient_clearance |
| d = +1e-12 / −1e-12 | outside / tight | outside / tight |
| d = −1 mm exactly (AT margin) | inside (inclusive) | inside |
| d = −1 mm − 1e-15 / + 1e-15 | inside / tight | inside / tight |
| d = −0.5 mm (tight zone) | tight | tight |
| d = +4.6 mm (report-05 magnitude) | outside | outside |

**Hull path (`containment()`) with synthetic band variants:** all-tight → `inside_insufficient_clearance`; all-outside → `outside`; all-inside → `inside`; three-way flip → `unresolved` (radial_cap_sensitivity); **inside↔inside_tight flip only → `unresolved`** (law: any flip); axial 50 mm vs half 8 mm → `unresolved` (local_narrowing); one variant hull empty → `unresolved` (no_vertices); square hulls driven through `containment()`: d=−1 mm exactly → `inside`, d=0 → tight. 11/11.

**Loop path (`section_loop_containment()`) on synthetic tube meshes:** exactly 1 identified loop (64-point cut of a 64-gon prism, adjacent duplicated points — zero-length edges guarded); center → inside; nominal −0.5 mm → tight; nominal −1 mm (chord −0.9988 mm at this tessellation) → tight; +0.5/+5 mm → outside; square tube: d=0 → tight, −2 mm → inside, −0.5 mm → tight, +1 mm → outside; module distances agree with the independent reference at the recorded 1e-9 rounding; **two pack-owned loops → unresolved** (n_identified=2, no choosing by size); **foreign-owned second loop ignored → inside** (n_identified=1); axial beyond the mesh → unresolved (0 loops). 21/21.

**Chaining (open never closes):** stray segments (0 loops, 2 open); open V (0,1); closed quad (1 loop, 4 pts, closing point dropped); 10 nm gap closes (below the 1e-7 m tol); **1 µm gap never bridges** — decomposes into 2 open chains, 0 loops. 6/6.

**Concave polygon (loop path claims ray-cast concavity support):** L-shape, 6 probes incl. reflex vertex (d=0 → tight) and notch geometry — all agree with the reference. 6/6.

---

## 3. 32-site × 2-authority reproduction (criterion 3) — PASS

Records were SUFFICIENT to re-derive all 32 sites × 2 authorities (every judged site carries distances; every unresolved site carries identification diagnostics), so recomputation from inputs was not required for re-derivation — it was performed anyway as the stronger test. Scripts: `scripts/reproduce.py`, `scripts/candidate41.py`; receipts: `receipts/reproduction.json`, `receipts/candidate41.json`.

**Count tables (both sides identical; known state CONFIRMED):**

| side | authority | inside | tight | outside | unresolved |
|---|---|---|---|---|---|
| radius | loop | **6** | **1** (PT-P3) | **7** | **2** (ECRB-P3, ECRL-P3) |
| radius | hull | **3** | **0** | **5** | **8** |
| radius_l | loop | **6** | **1** (PT_l-P3) | **7** | **2** |
| radius_l | hull | **3** | **0** | **5** | **8** |

Loop inside (radius): BIClong-P11, BICshort-P8, ECU-P5, FCR-P2, FCU-P2, FCU-P3. Loop outside: BIClong-P9, BICshort-P6, BRD-P2, BRD-P3, ECRB-P2, ECRL-P2, PT-P5. Matches session-05 §4-B and admission lists exactly (BIClong-P9 + BICshort-P6 are the two sites the loop authority SHARPENS from hull-unresolved to outside; PT-P3 the reclassification to tight).

**Per-site re-derivation from records:** every recorded verdict re-derived per the law from its recorded distance(s) — 28 judged loop sites (14/side) and 20 judged hull sites (10/side) all match; 4 loop-unresolved sites carry `n_identified_loops = 2` with `ambiguous_section` reason; all 16 hull-unresolved records (8/side) are `local_narrowing` (no band coverage) — the flip and no_vertices paths never fired on real data.

**Crosschecks, all exact:** fit-json ↔ `attachment_candidates.json` (32 candidates: verdict + distances + `authority` label); reproduced lists ↔ `admission_actual_monkey.json` envelope lists (loop_outside/loop_tight/loop_ambiguous/containment_outside/containment_unresolved per side); residual flags ↔ counts (`envelope_containment_loop.{outside,tight,ambiguous_section}.{radius,radius_l}` all consistent).

**Path B — full recompute from inputs (mesh + pack, code copies in `work/`):** `MonkeyTarget` hashes match recorded meta; frame rebuilt verbatim (`_band_roll` with the UNNORMALIZED axis, `onb_from_points`) deviates from the recorded frame by 2.9e-10–4.7e-10 m (consistent with the recorded 1e-9 export rounding); recomputed loop verdicts **6/1/7/2** and hull verdicts **3/0/5/8** per side; **all 32 × 2 per-site verdicts identical** to the packet.

Auditor note (for the next agent's pathway): rebuilding the frame requires `_band_roll(mt, prox, P, P_d - P)` with the unnormalized axis (actual_target_fit.py L523). With a normalized axis the roll witness argmax changes, the (b,c) frame rotates, and hull-path distances move by millimetres while loop-path distances stay invariant (frame rotation is distance-invariant). My first reproduction attempt made exactly this mistake; the mismatch it produced was a script bug, not a baseline defect.

**Ambiguity mechanism (measured, not prose):** at the two wrist-level axials (0.051510357 m and 0.053482959 m) the cut yields 4 closed loops, of which TWO reach owner_fraction ≥ 0.5: the 50-point skin loop (frac 1.0) and a 3-point fragment (frac 1.0). The ownership rule cannot distinguish them; the machinery stays unresolved. At all 13 other axials exactly one loop identifies.

---

## 4. Uncertainty budget (criterion 4) — numbers

**Hull band-width variant set** (read from code): nominal half **8 mm**; narrow **6 mm**; wide **10 mm** (`BAND_SWEEP_FRAC = 0.25`, `BAND_HALF_M = 0.008`). Sections t = 0.35/0.50/0.65 of axis_len 64.744899 mm → axis positions 22.66/32.37/42.08 mm. `SECTION_TOL = 0.05` (±5 % section placement) feeds only the sensitivity block, not containment.

**Hull polyline discretization** (from the recorded hulls, both sides): 24–26 hull points; edge median 2.80–2.84 mm, max 3.07–3.32 mm; polygon effective radius r_eff = A/p = 5.17–5.37 mm; chord sagitta s²/(8R): **187–227 µm** (median edge), **227–256 µm** (max edge).

**Loop discretization** (recomputed cuts): 152–300 cut segments per section (all bodies at that plane); identified-loop points 48–52; edge median 1.11–1.37 mm, max 1.94–3.05 mm; r_eff 4.56–5.32 mm; chord sagitta **29–45 µm** (median edge), **92–220 µm** (max edge). Endpoint chaining tolerance 1e-7 m = 100 nm (probe-pinned: 10 nm gaps close, 1 µm gaps never bridge).

**Mesh resolution:** 18,459 verts / 36,630 tris total; band vertex counts at the three sections **75/66/56** (recorded, confirmed); source coordinates are float32 → absolute coordinate quantization ≈ 30–60 nm (float32 spacing at |coord| ≈ 2–4 mesh units × 0.065 m/unit).

**Export rounding:** every recorded distance, position and hull point is rounded at 1e-9 m (`round(…, 9)`); measured consequences: frame rebuild deviation ≤ 4.7e-10 m; step-A recorded reconstruction error 1.15e-9 m (report 05 §4-A). Zero-length guard makes duplicated loop points harmless.

**Caveat on interpretation:** the mesh IS the defined surface — recorded distances are exact w.r.t. the mesh (up to float32 coords ~50 nm and 1e-9 export). The sagittas above quantify faceted-polyline vs ideal-smooth-skin, i.e. the resolution floor for comparing the model to reality, not measurement noise.

**The shortfall, situated (measurement only):** the recorded optimum (db = ±6.24 mm, dc = ±2.02 mm, objective 4.346890e-07 m²) decomposes EXACTLY as ridge 4.301800e-07 + ONE violation² — recomputed objective 4.346888e-07 m², delta 2–3e-13 m². The violation is a **single site-section at 67.15 µm** below the ≤ −1 mm law: ECRL-P3 at t = 0.35 (and mirror ECRL_l-P3), robust across narrow/nominal variants (wide clears at −324 µm). Report 05 §4-C's prose says "fitting sections violated by ~41 µm total"; **no artifact supports 41 µm — the recorded numbers encode 67.15 µm** (FINDING F4). Situating:

| scale | magnitude | 67.15 µm vs scale |
|---|---|---|
| hull-path chord sagitta (the judging polyline for the fitting-section criterion) | 187–256 µm | **below, ~3×** |
| loop max-edge sagitta (nearby sections) | 92–220 µm | **below** |
| loop median-edge sagitta | 29–45 µm | **same order (1.5–2.3× above)** |
| export rounding / float32 coords / chaining tol | 1e-9 m / 30–60 nm / 100 nm | far above (negligible) |

Preregistered prediction "the 41 µm shortfall is below the loop discretization scale": **as measured, PARTIAL — it depends which statistic names the scale.** Below the hull polyline's own chord scale and the loop's max-edge scale; of the same order as the loop's median-edge scale; and the recorded magnitude is 67.15 µm, not 41 µm. The falsifier (machinery defect) did NOT fire: this is a prose-vs-record magnitude discrepancy and a resolution-floor observation, not a classification defect. **The criterion stands regardless** (report 05 §4-C: "a hair, but the criterion is the criterion"; §6: "a ~41 µm shortfall is still a fail").

**Related scope observation (F5, declared, not a defect):** the experiment objective judges EVERY site against ALL THREE fitting hulls regardless of band coverage (`experiment_transverse_fit.py` L268-272), so the sole violation arises at a site (ECRL-P3) whose axial position the hull containment itself leaves unresolved (no sampled band) and the loop authority leaves unresolved (ambiguous section). The containment machinery never judges those pairs; the experiment's preregistration declares the stricter "every site inside every fitting-section hull".

---

## 5. Authority consistency (criterion 5) — PASS

- `attachment_candidates.json`: **32/32** candidates carry `skin_containment.authority == "local_triangle_plane_loop"` plus a `hull_sampling_diagnostic` block; the hull is nowhere labeled authority (0 regex hits for hull↔authority adjacency in both run records).
- `actual_monkey_fit.json`: `measurements.containment_authority = "local_triangle_plane_loop (hull sampling retained as diagnostic)"`; loop records carry `"authority": "local_triangle_plane_loop"` with the hull findings retained verbatim beside them.
- Code: `actual_target_fit.py` L552-557 ("session-5 FINAL authority … RETAINED verbatim as a diagnostic"), `target_envelope.py` L447+ ("FINAL skin-containment authority … replacing the band-vertex convex hull (kept as a diagnostic by the caller)"), `experiment_transverse_fit.py` ("authority (triangle-plane section …)"). Consistent everywhere.
- `admission_actual_monkey.json` `loop_authority_ok: false` is defined at `actual_target_fit.py` L632 as `confirm_loop[side]["ok"]`, and `ok` is the containment pass flag at `target_envelope.py` L548: `bool(not outside and not unresolved and not tight and inside)`. It is false because the BASELINE SITES FAIL containment (7 outside + 1 tight + 2 unresolved per side) — **not** a machinery flag. The machinery demonstrably works: this audit recomputed it from inputs and reproduced every verdict. (The candidate record reuses the same field name for the candidate's containment pass — same semantics, same cause there: the 2 ambiguous sections.)

---

## FINDINGS (discrepancies are findings; baseline untouched)

- **F1 (doc drift).** `target_envelope.py` L243: stale session-4 verdict list in `containment()` docstring (see §1). Suggested owner: docstring update by the architect; behavior lawful.
- **F2 (wording).** Flip reason string says "between inside and outside"; the code (lawfully) flags any class mix. `target_envelope.py` L315-317.
- **F3 (wording).** `_dist_to_poly` docstring "nearest polygon point" vs nearest point on boundary edges. L187-188.
- **F4 (prose vs record).** Report 05 §4-C "~41 µm total" vs the recorded optimum encoding a single **67.15 µm** violation (ECRL-P3 @ t=0.35, each side; objective decomposition exact to 2-3e-13 m²). Failure verdict unaffected — the criterion fails either way (and the candidate also fails `loop_authority_ok` via the 2 ambiguous sections). Magnitude in prose should be corrected to 67 µm (or the 41 µm source identified) by the architect.
- **F5 (scope, declared).** The candidate objective judges all sites × all fitting hulls regardless of band coverage; containment authority judges only band-covered (hull) or single-identified-section (loop) pairs. Declared in the experiment module's preregistration; noted because it is where the sole violation lives.
- **F6 (observation).** All 16 hull-unresolved records are `local_narrowing`; flip/no_vertices paths are real (probe-verified) but never fired on the baseline. Loop ambiguity at the wrist sites is caused by a 3-point pack-owned fragment loop reaching owner_fraction 1.0 alongside the 50-point skin loop — recorded in the packet's section diagnostics.

## Explicit uncertainty / limits of this audit

- The 41 µm prose figure could not be reproduced from any artifact; if it was computed by a method not recorded in the packet, that method is outside this audit's visibility.
- Sagitta numbers use r_eff = A/p (isoperimetric radius) as the local curvature scale; a true curvature-by-arc estimate would shift them tens of percent, not orders.
- The candidate optimum was evaluated at its recorded (1e-6-rounded, on-grid) values; the exact pre-record optimum could differ by < 1 µm of shortfall, far below the F4 gap (26 µm).
- No Edgeworth-level shape statistics were computed; "discretization scale" here means chord-vs-smooth-skin deviation of the judging polylines.

## Artifacts

`E:/PythonChimera/forearm_package/audits/A5_containment/`
- `brief.md` — verbatim brief
- `report.md` — this report
- `scripts/synthetic_probes.py`, `scripts/reproduce.py`, `scripts/candidate41.py`
- `receipts/synthetic_probes.json`, `receipts/reproduction.json`, `receipts/candidate41.json`, `receipts/hull_discretization.json`, `receipts/work_copy_hashes.txt`, `receipts/commands.md`
- `work/target_envelope.py`, `work/mesh_target.py`, `work/compiler.py` — verbatim baseline copies (read-only use)
