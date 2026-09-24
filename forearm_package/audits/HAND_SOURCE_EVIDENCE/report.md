# R2 Form A — HAND_SOURCE_EVIDENCE: the 27 vendor hand STLs identity-tested, a fan-independent signed palm normal derived

**Agent:** M-handsrc (R2 evidence acquisition) · **Date:** 2026-09-24
**Governing spec:** `audits/HAND_EVIDENCE_REQUEST/HAND_EVIDENCE_REQUEST.md` §R2 (read first; its
acceptance criteria and falsifiers govern). **Precedent followed exactly:** O1
(`audits/O1_ulna_orientation/` — anchor-class identity, fired rules preserved, Agg figures,
integrity receipt). **Prereg frozen before any measurement:** `prereg.md` (its header records
the exact pre-measurement state; no rule edited after any number was seen).
**Scope:** source-side orientation evidence ONLY — no mapping choice (a passing normal is
evidence for Astra's A04 decision, not a mapping), no scale/dimension number, no
assembly-correspondence claim, no utility quantity, no target-side claim. CPU-only
(stdlib+numpy STL parsing); figures matplotlib Agg before pyplot import; writes confined to
`forearm_package/audits/HAND_SOURCE_EVIDENCE/`.

**HEADLINE: SOURCE-PRONG-CLOSED (with one documented deviation, O1-style).**
The on-disk vendor hand set passed identity at the R2-A3 anchor class, and the frozen
pisiform-signed palm-plate method produced a fan-independent signed palm normal that splits
the frozen site table **5/5 clean on both hands**:

> **n_palm (hand_r local, unit) = (+0.128427, −0.168691, −0.977266)** — 12.24° from local −ẑ;
> left hand exact mirror (+0.128427, −0.168691, +0.977266).

---

## 0. ACCEPTANCE-CRITERION VERDICTS (the brief's six)

| # | criterion | verdict |
|---|---|---|
| 1 | frozen prereg | **PASS** — `prereg.md` written before any STL was opened; thresholds, chain-link set, palm method, sign rule, gate, and verdict mapping all frozen; nothing re-declared post hoc; the fired rule preserved with numbers (§3.2). |
| 2 | 27-bone identity table with hashes + anchor classes | **PASS WITH ONE DOCUMENTED DEVIATION** (§3) — table complete (`receipts/identity_table.md`, per-bone sha256/tri-count/d_own/links/site anchors); the frozen 19-link rule **FIRED on 9 links and is preserved verbatim**; the governing R2-A3 anchor class is met with margins (sites 0.06–0.80 mm; ray links 1.35–2.55 mm; CMC/MCP surface interlock 0.00 mm; extent record < 0.05 mm). The deviation is flagged, both readings preserved (§3.4). |
| 3 | derived normal with method documentation | **PASS** — one method frozen before computing (pisiform-signed palm-plate plane; 12 carpal+metacarpal bones, zero phalanges, zero thumb, zero sites); signed, fan-independent, feature-named (pisiform = the palmar sesamoid; Gray's-anatomy fact), recorded in `hand_r` local coordinates (§4). |
| 4 | acceptance-check results | **PASS — CLEAN 5/5 both hands** (§5): flexors FCR-P3 +5.29 mm, FCU-P4 +4.36 mm on the palm side; extensors ECRL-P4 −3.26 mm, ECRB-P4 −9.10 mm, ECU-P6 −2.63 mm dorsal. Falsifier (b): NOT fired. Falsifier (c) mirror: XML z-mirror exact (max |Δ| = 0.0 mm over 27 anchors + 5 sites); left normal exact mirror; left split 5/5 clean. Left STL identity NOT testable (files absent from vendor) — recorded limitation, not a failure (§5.3). |
| 5 | verdict | **SOURCE-PRONG-CLOSED** (§6): normal + evidence chain delivered per R2.4-1/2/3 (hash-pinned files with upstream revisions; scale declared `1 1 1` as the XML attribute states; anchor-class pass with per-point numbers; clean compartment split on the frozen site table; normal in hand_r local for the future roll-sign mapping). |
| 6 | integrity: baseline porcelain empty | **PASS** — pasted in §8 (start and end, HEAD `768f3de0`); `PYTHONDONTWRITEBYTECODE=1`; no git writes; all writes in this audit dir. |

## 0.1 PREREGISTRATION VERDICT

| prong | outcome | numbers |
|---|---|---|
| 27 vendor files match the XML's 27 declared hand bones by name at scale (1,1,1) | **CONFIRMED** | 27/27 names, 27/27 mesh-asset declarations `scale 1 1 1`; hand_r world origin (−0.0731, 0.532647, 0.202699) == R2-A4 pin exactly |
| chain links anchor class ≤ 3.5 mm (my frozen primary rule) | **FALSIFIED — PRESERVED** | 10/19 pass; 9 fail: 4 gross CMC (26.65–31.34 mm), 4 marginal MCP (3.62–4.48 mm), 1 CMC-thumb (4.53 mm). Fired numbers kept in `receipts/s2_identity.json`; per-bone verdicts in the table kept as they fell |
| refined-rule diagnosis: the failures are convention-form, not asset mismatch | **CONFIRMED** | all 5 CMC + 5 MCP surface–surface gaps **0.00 mm**; MC proximal poles reach 26.8–35.0 mm past their anchors, bridging the 26.7–31.3 mm CMC anchor gaps exactly; ray-internal links 9/9 pass (1.35–2.55 mm) |
| governing R2-A3 anchor class (sites + geom-anchor skeleton extents) | **CONFIRMED** | ECRL-P4→2mc 0.80, ECRB-P4→3mc 0.51, ECU-P6→5mc 0.06, FCR-P3→2mc 0.69 mm (anchor class); FCU-P4→pisiform 16.83 mm (course class, enumerated per O1 discipline); extents: 155.285 vs 155.29 mm, rays 66.99/96.42/100.17/89.10/78.61 vs 67.0/96.4/100.2/89.1/78.6 mm |
| FALSIFIER (a): any STL failing identity (name/scale/anchor class) | **NOT FIRED at the R2-A3 bar** | no name mismatch; scale resolvable (= the declared 1 1 1, verified by the passing assembly); anchor class met on the spec's instruments. My stricter frozen link rule DID fire — preserved, diagnosed as hypothesis-form error (§3.3–3.4) |
| FALSIFIER (b): derived normal's sign disagrees with the site split (FCR/FCU must sit palm-side) | **NOT FIRED** | split 5/5 clean; smallest flexor margin +4.36 mm, smallest extensor margin −2.63 mm (ECU — the ulnar-border extensor rides the plane, anatomically expected; same behavior in O2's recorded 13-geom diagnostic +0.02 mm) |
| FALSIFIER (c): left/right mirror inconsistency | **NOT FIRED** | anchor + site z-mirror exact (max |Δ| = 0.0 mm); left derivation returns the exact mirror normal (max |Δ| < 1e-9); left split 5/5 clean |

## 1. INPUTS AND FRAMES

- XML: `baseline_snapshot/source_xml/chimanoid.xml` — hand_r body L629 (pos (0.018, −0.2904,
  0.025), quat identity → **hand_r local axes are world axes at rest**), 27 mesh geoms L635–661,
  5 sites L663–667; mesh assets L855–881 all `Geometry/<name>.stl`, `scale="1 1 1"`; hand_l
  L769–799 + L885–911 (exact z-mirrors).
- Vendor: `E:/PythonChimera/vendor/myo_sim/meshes/` — provenance pinned: **MyoHub/myo_sim,
  VERSION 0.1.0, Apache-2.0, own git HEAD `33f3ded946f55adbdcf963c99999587aadaf975f`**. The
  chimanoid XML itself is FreeMusco rev `e021d5d9d1698dafea93c0dcf34b4bc8ce1530e7` (handreq
  R3.4). Per R2-A1/A2 the tie between the two is exactly what the identity test establishes
  (it does not rest on naming — the vendor dir also contains other hand families: `arm_r_*`,
  `hand_2*`, `*_lvs/_rvs`, `fingers*`; all excluded as non-name-matched, and `arm_r_1mc.stl`
  is byte-different from `1mc.stl`).
- Vendor scale convention (derived from the XML attribute, not fitted): place STL vertices
  unscaled, translated by the geom pos anchor; lunate's geom has no pos → origin. The
  convention's resolvability is verified by the passing assembly itself (§3).
- `hand_r` world origin reproduced from the parsed body chain: **(−0.0731, 0.532647,
  0.202699) m — equal to the R2-A4 pin** (S1 receipt).

## 2. S1 — ENUMERATION AND HASHES

27 right-hand geoms parsed, 27 left; all 27 vendor `<name>.stl` present; all mesh-asset
scales `[1.0, 1.0, 1.0]`; every file binary STL, 1566–8360 triangles. Full per-bone table:
`receipts/s1_inventory.json` (sha256, bytes, tri count, local bbox); the identity table in
§3.5 carries the sha256 prefixes. Left `<name>_l.stl`: **absent from the vendor set (0/27)**.

## 3. IDENTITY (O1-class)

### 3.1 Design (frozen in `prereg.md` §2)
Per-bone records (d_own, inside flag, bbox); the DECISIVE frozen rule = 19 chain links
(14 ray + 5 CMC), child anchor → parent surface ≤ 3.5 mm; assembly reproduction of C2's
anchor record; carpal adjacency descriptive; the 5 tendon sites recorded (course-class
discipline), NOT identity-decisive, used only in §5.

### 3.2 The frozen primary rule — FIRED, PRESERVED
`d_link ≤ 3.5 mm` failed on 9/19 links: gross CMC failures (trapezoid→2mc 28.85, capitate→3mc
30.40, hamate→4mc 31.34, hamate→5mc 26.65 mm), thumb CMC (trapezium→1mc 4.53), marginal MCP
(1mc 4.48, 2mc 4.07, 3mc 4.15, 5mc 3.62 mm). The per-bone verdict column in
`receipts/identity_table.md` records `OUT(link-fail)` for the 8 failing parents **exactly as
the frozen rule produced them** — not overwritten. Had anything else in this audit depended
on hiding these numbers, the verdict would be BLOCKED.

### 3.3 The preregistered refined-rule diagnosis (run because the primary fired)
The prereg froze the response: record the child-anchor position relative to the parent
surface and the gap geometry. Measured (`receipts/s2b_cmc_diagnosis.json`):
- **Every CMC and MCP bone pair's surfaces touch: surface–surface gap 0.00 mm (all 10 pairs).**
- Each metacarpal surface extends **26.8–35.0 mm proximal of its own anchor** — precisely the
  26.7–31.3 mm CMC anchor gaps. The MC meshes grow backward over the carpometacarpal row;
  the CMC articulation in this rig is surface-to-surface, NOT "MC anchor on carpal surface".
- The marginal MCP failures have the child anchor **inside** the parent head (knuckle center
  within the condylar envelope, 3.5–4.5 mm from the cartilage surface).
- Ray-internal links pass everywhere: 9/9 at **1.35–2.55 mm** (14 bones mutually coherent).
- Carpal row adjacency matches anatomy: the 6 anatomically adjacent carpal pairs touch at
  0.16–0.60 mm (pisiform–triquetrum 0.16, lunate–triquetrum 0.40, capitate–trapezoid 0.46,
  lunate–capitate 0.52, trapezoid–trapezium 0.53, triquetrum–hamate 0.60) while
  non-adjacent pairs sit 17–21 mm apart — a correctly assembled carpal row.

So the failures are a hypothesis-form error in MY link construction (it assumed the child's
placement origin sits at the parent's articular surface), not evidence about the assets.

### 3.4 The deviation, flagged (O1 §2.2 pattern — both readings preserved)
My prereg's letter said a fired primary makes failing parents OUT, which would gate the
derivation BLOCKED. The governing R2 spec defines the hand's anchor class differently and did
so before this audit existed: *"anchor-class landmarks within 3.5 mm of the tested surface,
with tendon-course-type deviations separately enumerated … For the hand, the anchor class is
the geom-anchor skeleton itself: assembled chain extents must reproduce the anchor-derived
record."* On that bar the identity evidence is:

1. **Four independent authored tendon anchors land on their cited bones at 0.06–0.80 mm**
   (ECRL-P4→2mc dorsal face, FCR-P3→2mc palmar face, ECRB-P4→3mc dorsal face, ECU-P6→5mc
   ulnar face) — the exact O1 instrument that accepted `ulna.stl` at 0.04–2.88 mm. A wrong
   family's geometry cannot pass four landmarks on three bones across both compartment faces.
2. **FCU-P4→pisiform 16.83 mm — course class, enumerated** (the FCU insertion spreads through
   the pisohamate/pisometacarpal ligaments; the site sits on that course, exactly like O1's
   off-surface PT-P2/ECU waypoints).
3. **The geom-anchor skeleton record reproduces**: 155.285 vs 155.29 mm; rays
   66.99/96.42/100.17/89.10/78.61 vs 67.0/96.4/100.2/89.1/78.6 mm (all < 0.05 mm).
4. Ray links 9/9 ≤ 2.55 mm; CMC/MCP interlock 0.00 mm; carpal adjacency anatomical (§3.3).

**Identity verdict: PASS at the R2-A3 anchor class, with my stricter frozen link rule reported
FIRED and preserved.** This deviation from my prereg's letter is deliberate and explicit: the
tasking states the handreq spec *"defines the acceptance criteria and falsifiers you work
against"*, and F-R2a's failure modes (inconsistent with the pos anchors beyond the anchor-class
rule; a different family's geometry) are measured FALSE with large margins on the spec's own
instruments. What would have changed the verdict: sites at course-class distances, non-zero
CMC/MCP gaps, or a failing extent record — none observed. The pisiform (sign-critical) carries
name match, d_own 1.22 mm inside its surface, the tightest carpal adjacency in the row
(pisiform–triquetrum 0.16 mm — its anatomical seat on the triquetrum's palmar surface), and
its protrusion geometry is what §4 consumes.

### 3.5 The 27-bone identity table
Full table with sha256 prefixes, triangle counts, d_own (inside flag), chain-link distances
(P/F at 3.5 mm), site anchors, and the preserved frozen-rule verdicts:
`receipts/identity_table.md` (also `receipts/s1_inventory.json` for full hashes, and
`receipts/s2_identity.json` for every link and adjacency pair).

## 4. THE PALM NORMAL (frozen method, run once)

**Method (frozen in `prereg.md` §3 before computing): pisiform-signed palm-plate plane.**
Plate = 12 bones (pisiform, lunate, scaphoid, triquetrum, hamate, capitate, trapezoid,
trapezium, 2mc, 3mc, 4mc, 5mc) placed at their XML anchors, identity scale. Unsigned normal =
smallest-eigenvalue eigenvector of the union vertex covariance. Sign rule: the pisiform is
the **palmar sesamoid bone of the wrist** (it rides the palmar surface of the triquetrum and
is the palpable protuberance at the ulnar base of the palm — standard carpal anatomy), so the
palm side is the side its surface protrudes toward:
`n_palm = n_hat · sign((c_pisi − c_rest) · n_hat)`.
Fan-independence by construction: no phalanx enters any step (F-R2c), no thumb-ray bone, no
site coordinate, no author choice; the L/R mirror law and the XML z-mirror are the only other
inputs. The thumb ray was excluded in the prereg (divergent radial ray) — recorded before
measurement, not after seeing its geometry.

Measured (right):
- `n_hat` (unsigned, display-oriented) = (−0.128427, +0.168691, +0.977266); covariance
  eigenvalues 3.46e-05 / 1.56e-04 / 5.84e-04 m² (out-of-plane variance 4.5× below the middle
  axis — a plate); plate rms residual 5.88 mm (the palm plate is a curved band; the plane is
  the frozen construction, and §5's acceptance prices the curvature in).
- **Sign rule margin: (c_pisi − c_rest)·n_hat = −6.97 mm** — a healthy margin, not a coin flip.
  c_pisi = (−11.32, −11.04, −10.13) mm: the pisiform is the palmar-most plate member measured.
- **n_palm = (+0.128427, −0.168691, −0.977266)** in hand_r local coordinates (== world
  direction at rest), 12.24° from local −ẑ, i.e. the palm faces the −z side with a slight
  radial-distal lean inherited from the plate's curvature.

## 5. ACCEPTANCE CHECKS (frozen, run once, margins recorded whatever they fell)

### 5.1 Compartment split on the frozen site table (R2 closure test, falsifier (b))
Plane through c_all = (1.25, −28.94, 0.94) mm with normal n_palm; palm side positive:

| site | compartment | offset along n_palm | expect | agree |
|---|---|---:|---|---|
| FCR-P3 | flexor | **+5.29 mm** | palm | OK |
| FCU-P4 | flexor | **+4.36 mm** | palm | OK |
| ECRL-P4 | extensor | **−3.26 mm** | dorsal | OK |
| ECRB-P4 | extensor | **−9.10 mm** | dorsal | OK |
| ECU-P6 | extensor | **−2.63 mm** | dorsal | OK |

**CLEAN 5/5.** Falsifier (b) NOT fired. O2's mixed-sign failure (FCR −1.99 mm on the wrong
side of the 27-geom plane; jackknife 1/27) does not survive the fan-independent boundary —
consistent with O2 §2.2's tilt diagnosis (the sites carry −1.0…−5.6 mm tilt terms on n27).

### 5.2 Post-hoc consistency note (documentation only, no decision input)
The derived palm side (−z-dominant) agrees in direction with O2's recorded raw local-z
diagnostic (extensors +8.16/+10.82/+1.05, flexors −1.85/−5.19) — recorded there as diagnosis
only. This audit's derivation never reads that diagnostic; the agreement is corroboration
after the fact.

### 5.3 Sign consistency L/R (falsifier (c))
- XML mirror: all 27 left anchors and all 5 left sites equal the right with z negated,
  **max |Δ| = 0.0 mm** (exact to the last printed digit).
- Left derivation (same frozen method on z-mirrored geometry at left anchors):
  **n_palm_L = (+0.128427, −0.168691, +0.977266) = exact z-mirror of the right** (max |Δ| <
  1e-9); left split 5/5 clean (same margins to 0.01 mm).
- **Recorded limitation:** the vendor set contains no `<name>_l.stl` (0/27), so left ASSET
  identity is not testable on disk; the mirror check is at the XML-mirror + construction
  level, exactly as preregistered (§2.6c). A limitation, not a failure.

## 6. VERDICT

> **SOURCE-PRONG-CLOSED (R2 Form A).** The vendor hand set at
> `E:/PythonChimera/vendor/myo_sim/meshes/` (MyoHub/myo_sim v0.1.0 @ `33f3ded9…`) is the
> chimanoid's `Geometry/*.stl` hand at the R2-A3 anchor class (falsifier F-R2a not fired),
> and the fan-independent signed palm normal exists:
> **n_palm = (+0.128427, −0.168691, −0.977266) hand_r local** (left: z-mirror), derived from
> identity-tested bone surfaces by the preregistered pisiform-signed palm-plate method,
> splitting the frozen site table 5/5 clean on both hands (falsifiers F-R2b, F-R2c not
> fired). With O2's source-side diagnostic recorded and this normal's evidence chain, the
> source prong's blocker condition (no fan-independent palm identifier) is met by exactly
> the artifact USTR §1 O2 named.
>
> **Preserved negative:** my stricter frozen 19-link identity rule fired (9 links) and is
> reported with all numbers and per-bone verdicts intact (§3.2, §3.5); the identity verdict
> rests on the governing spec's anchor class, and the deviation is flagged in §3.4. The left
> STL identity remains untestable on disk (§5.3). No mapping is stated here — by scope, the
> roll-sign mapping to §R1's target face is the architect's/A04's statement to make from this
> evidence.

## 7. SCOPE DISCIPLINE

No scale/dimension/proportion number (hand or paddle) computed or consumed; no
same-assembly claim (§R3 untouched); no target-side claim (§R1 untouched); no production
mapping stated; no utility/moment-arm/path-length quantity anywhere. Every number above is a
hash, a placement distance, a plane-fit component, or a signed site offset used only for the
orientation sign. CPU-only: STL parsing stdlib+numpy; no trimesh; no GPU/OpenGL/Vulkan
context; the single figure is matplotlib Agg set before pyplot import.

## 8. INTEGRITY RECEIPT

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty)          # start of work (pre-prereg) AND end of work; HEAD 768f3de04a3b5539a80cf85d9a4587505da8385d
```
All writes confined to `forearm_package/audits/HAND_SOURCE_EVIDENCE/`
(brief.md, prereg.md, report.md, scripts/, receipts/, figures/). Baseline read-only; input
hashes pinned per bone in `receipts/s1_inventory.json`; vendor provenance pinned (myo_sim
v0.1.0 @ 33f3ded946f55adbdcf963c99999587aadaf975f). `PYTHONDONTWRITEBYTECODE=1` throughout;
no git writes. Commands verbatim: `receipts/commands.md`.

## 9. RECEIPTS INDEX

| receipt | content |
|---|---|
| `prereg.md` | frozen preregistration (identity design, thresholds, method, gate, verdict mapping) |
| `receipts/s1_inventory.json` (+`_run.log`) | 27-bone inventory: anchors, scales, sha256, bytes, tri counts, bboxes, left-file absence, family spot-checks, hand_r origin pin |
| `receipts/s2_identity.json` (+`_run.log`) | per-bone d_own/inside, 19 links (fired rule numbers), extent-record reproduction, 28-pair carpal adjacency, site distances, frozen verdicts |
| `receipts/s2b_cmc_diagnosis.json` (+`_run.log`) | CMC/MCP surface gaps (0.00 mm ×10), MC proximal reach 26.8–35.0 mm, per-link gap vectors |
| `receipts/identity_table.md` | the 27-bone table (hash prefixes, d_own, links, sites, preserved verdicts) |
| `receipts/s3_palm_normal.json` (+`_run.log`) | derivation (n_hat, eigenvalues, pisiform dot −6.97 mm), acceptance split R+L, mirror exactness, falsifier states |
| `receipts/commands.md` | every command verbatim |
| `figures/hand_source_assembly_normal.png` | Agg-only: assembled skeleton, 3 declared views, palm plate + pisiform + n_palm + sites |
| `brief.md` | the task brief, copied verbatim as the first action |
