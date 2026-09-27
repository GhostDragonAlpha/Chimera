# PREREGISTRATION — HAND_SOURCE_EVIDENCE (R2 Form A)

**Frozen:** 2026-09-24, BEFORE any STL was opened, parsed, or measured. The only actions taken
before this file: (i) reading `HAND_EVIDENCE_REQUEST.md` §R2 (the acceptance criteria this audit
works against), O1's report/script (the discipline precedent), O2's report (the failed prong);
(ii) reading the XML text of the hand body declarations (L628–667), the mesh asset declarations
(L855–911), and the arm-chain body lines — i.e. reading the frozen record, no geometry;
(iii) file listing + md5 spot-check of two vendor files (inventory, no geometry).
Everything below is frozen. Nothing may be re-declared after a measurement is seen. Fired rules
are reported as they fall, with their numbers kept (O1 discipline). No tuning anywhere.

---

## 1. QUESTION AND DESIGN

Close O2's SOURCE prong (handreq §R2.1): a **fan-independent signed palm normal in `hand_r`
local coordinates**, derived from identity-tested vendor hand-bone surfaces (Form A, §R2.3-A).
The 27-geom anchor plane is disqualified as a derivation input: its ~10.0° digital-fan tilt
mixed the compartment signs (O2 §2.1–2.2, FCR −1.99 mm wrong side; 1/27 jackknife). No phalange
enters this derivation (F-R2c).

## 2. IDENTITY TEST (frozen before any mesh is parsed)

### 2.1 Scope and inputs
- The 27 right-hand bones the XML declares at `Geometry/<name>.stl`, `scale="1 1 1"`
  (chimanoid.xml L855–881), geom pos anchors L635–661, sites L663–667.
- Vendor candidates: `E:/PythonChimera/vendor/myo_sim/meshes/<name>.stl` (name-matched).
  The `arm_r_*`, `*_lvs/*_rvs`, `hand_2*`, `fingers*` families are NOT candidates (different
  family names; F-R2a's "different family" clause). Left-hand `<name>_l.stl` files: PRESENT in
  the XML (L885–911), ABSENT from the vendor dir (verified by listing before this prereg) —
  the left side is handled in §2.6.

### 2.2 Scale convention (declared, and how it is derived)
The XML scale attribute is `1 1 1` for every hand mesh (vs the arm bones' `1 1.2 1`). Frozen
convention: **place STL vertices unscaled, translated by the geom pos anchor**
(`bone_local = STL_vertex * (1,1,1) + anchor`), lunate at the origin (its geom has no pos attr,
L636). The convention is DERIVED from the XML attribute, not fitted. The identity test itself is
the check that this convention is resolvable: if the bones do not assemble coherently at
scale (1,1,1) (systematic link failures, §2.4), the convention is UNRESOLVED → falsifier (a).

### 2.3 Per-bone tests (recorded for all 27)
For each bone: sha256 + byte size + STL format (binary/ASCII) + triangle count + local bbox;
`d_own` = distance from its own geom pos anchor to its own placed surface + inside/outside flag
(ray-cast parity along the anchor→surface direction, reported descriptively).

### 2.4 DECISIVE test — the 19 chain links (anchor class ≤ 3.5 mm)
The bone skeleton's anchor graph (parent bone → child bone whose anchor should land on the
parent's distal articular surface; MuJoCo convention hypothesis: mesh origin at the joint
center):
- Ray links (14): `1mc→thumbprox`, `thumbprox→thumbdist`;
  `2mc→2proxph→2midph→2distph`; `3mc→3proxph→3midph→3distph`;
  `4mc→4proxph→4midph→4distph`; `5mc→5proxph→5midph→5distph`.
- CMC links (5): `trapezium→1mc`, `trapezoid→2mc`, `capitate→3mc`, `hamate→4mc`,
  `hamate→5mc` (standard carpal-to-metacarpal articulations).
For each link: `d_link` = distance from the CHILD's geom pos anchor to the PARENT's placed
SURFACE (closest triangle, exact point-triangle, O1's method).
- **FROZEN RULE (primary, decided before running): every `d_link` ≤ 3.5 mm → identity PASS**
  (anchor class, R2 A3 bar = O1's refined rule).
- **FROZEN REFINED RULE (predeclared, applied only if the primary fires, with the fired
  numbers kept):** the primary hypothesis (origin at joint center) is refined to the
  origin-convention diagnosis: for each failing link, record the child anchor's position
  relative to the parent surface (inside / off which end) and the per-bone translation that
  would be needed. Identity may be re-verdicted PASS only on a rule nameable BEFORE seeing the
  per-link numbers that would use it — there is none preregistered beyond the primary; so if
  the primary fires, the failing parent bones are **OUT** (falsifier (a)), reported by name.
- Bones that parent no link (`scaphoid, lunate, triquetrum, pisiform`): identity verdict
  `ADJACENCY-SUPPORTED` (name match + carpal-row adjacency matrix recorded; not decisive).
  No subset substitution is allowed in the derivation on their account (§3.1).

### 2.5 Assembly-level reproduction (R2 A3's stated anchor class)
The assembled anchor skeleton must reproduce C2's frozen anchor-derived record: distalmost
`3distph` = **155.29 mm** (|anchor| from hand origin), ray chains (MC base → distal anchor,
sum of consecutive anchor gaps) = **67.0 / 96.4 / 100.2 / 89.1 / 78.6 mm** (rays 1–5).
Reproduction tolerance: < 0.05 mm (pure arithmetic on the same anchors — a transcription check).
Additionally recorded: the distalmost placed-SURFACE point (bones extend past the distal
anchor — descriptive) and pairwise min surface distances among the 8 carpals (descriptive
adjacency; no threshold).

### 2.6 Left/right mirror (falsifier (c))
(a) XML mirror exactness: all 27 left anchors + 5 left sites (L773–799 + left site block)
must equal the right with z negated (exact, < 1e-12). (b) The frozen method (§3) re-run on the
left assembly (right STLs z-mirrored, placed at left anchors) must give
`n_L = (n_Rx, n_Ry, −n_Rz)` exactly. (c) RECORDED LIMITATION: no left STL exists in the vendor
set, so left ASSET identity is not testable on disk; the mirror check is at the XML-mirror +
construction level. This is a limitation, not a failure; it is stated in the report.

### 2.7 Site-anchor distances (supporting, O1 course-point discipline)
The 5 hand sites (ECRL-P4, ECRB-P4, ECU-P6, FCR-P3, FCU-P4, XML L663–667) are soft-tissue
attachment/course points around the carpus (O2's citations: MC bases / pisiform course);
they are RECORDED as distances to their cited bones (`2mc, 3mc, 5mc, 2mc, pisiform`)
with a course-class caveat, and are NOT identity-decisive. Their ONLY decisive use is §4
(the acceptance split) — the independence line R2 Form B demands for landmarks holds for the
normal derivation (§3 uses no site coordinate).

## 3. PALM-NORMAL DERIVATION (frozen — ONE method)

**Method: pisiform-signed palm-plate plane (carpal row + metacarpal shafts; zero phalanges).**
1. Bones (12): `pisiform, lunate, scaphoid, triquetrum, hamate, capitate, trapezoid,
   trapezium, 2mc, 3mc, 4mc, 5mc`. EXCLUDED: `1mc, thumbprox, thumbdist` (the thumb is the
   divergent radial ray — excluded for fan-independence) and ALL 14 phalanges (F-R2c: no
   phalangeal/fan member may build the palm definition).
2. Placement: identity scale + XML anchor translation (right hand), all placed surfaces unioned.
3. Unsigned normal n̂: smallest-eigenvalue eigenvector of the covariance of the union vertex set
   (PCA plane of the palm plate).
4. SIGN rule: `n_palm = n̂ · sign((c_pisi − c_rest) · n̂)`, where `c_pisi` = vertex centroid of
   the placed pisiform surface, `c_rest` = vertex centroid of the other 11 plate bones.
   **Anatomical justification (frozen):** the pisiform is the palmar sesamoid bone of the
   wrist — it rides the PALMAR surface of the triquetrum and is the palpable bony protuberance
   at the ulnar base of the palm (Gray's anatomy; standard carpal anatomy). Its protrusion
   side IS the palm side. Fan-independent by construction: no phalanx, no site, no author
   choice enters; the sign comes from a named bone feature with external-anatomy status.
5. Palm plane (for the acceptance test only): through `c_all` (union centroid of all 12
   plate bones' vertices), normal `n_palm`. Palm side = positive offsets.
6. Derivation gate: the method runs ONLY if all 12 plate bones clear §2.4/§2.5. If any plate
   bone is OUT, the derivation does NOT run on a subset (subset substitution = re-authoring)
   → verdict BLOCKED with the named bones. Phalanx/thumb failures do NOT gate the derivation
   (they enter no step) but are reported OUT in the identity table.

## 4. ACCEPTANCE CHECKS (run once, after derivation; margins recorded whatever they are)

1. **Compartment split on the frozen site table** (R2 closure test / falsifier (b)):
   `s_i = (site_i − c_all) · n_palm`. Flexors FCR-P3, FCU-P4 must have `s_i > 0` (palm side);
   extensors ECRL-P4, ECRB-P4, ECU-P6 must have `s_i < 0` (dorsal). CLEAN = all five agree.
   Any flexor on the dorsal side or extensor on the palm side → **falsifier (b) FIRED** →
   escalate per R2 F-R2b (the failure is recorded, not resolved here).
2. **Sign consistency L/R** (falsifier (c)): left derivation exact-mirrors right (§2.6).
3. Anchor-class reproduction (§2.5) recorded as the identity backbone.

## 5. VERDICT MAPPING (frozen)
- **SOURCE-PRONG-CLOSED**: identity PASS (all 19 links ≤ 3.5 mm; record reproduced) AND the
  12 plate bones clear AND the acceptance split CLEAN AND mirror exact. Output: the signed
  unit `n_palm` in hand_r local coordinates + evidence chain.
- **BLOCKED**: any frozen acceptance failing → report WHICH criterion/falsifier failed, with
  numbers, preserved (no reinterpretation, no subset substitution, no re-derivation).
- No utility numbers, no mapping choice, no target-side claim anywhere (the passing normal is
  evidence for Astra's A04 decision, not a mapping).

## 6. DISCIPLINE (frozen)
CPU-only; STL parsing stdlib+numpy (O1's binary loader; ASCII fallback added for inventory);
figures matplotlib Agg backend set before pyplot import; `PYTHONDONTWRITEBYTECODE=1`; no git
writes; writes ONLY in `forearm_package/audits/HAND_SOURCE_EVIDENCE/`; baseline read-only;
hashes re-asserted at load; stop rule: identity table + normal + acceptance checks verdicted,
or a named failure.
