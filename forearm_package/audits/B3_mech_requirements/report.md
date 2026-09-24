# B3 REPORT — mechanical requirements for wrist/elbow/digit transmission (ulna, ulna_l, hand_r, hand_l)

**Agent:** B3 (requirements) · **Date:** 2026-09-24 · **Deliverable:** `requirements_sheet.md` (full sheets, matrix, flags) + this verdict summary.
**Scope honored:** read-only + spec writing; no fitting searches, no ownership decisions, no mechanical qualification; every deviation candidate flagged, none chosen.

---

## ACCEPTANCE-CRITERIA VERDICTS

| # | criterion | verdict |
|---|---|---|
| 1 | Four complete requirements sheets, every requirement cited to a contract line (DERIVATION §/line + code file:line + XML line) | **PASS** — requirements_sheet.md §3.1-3.4: 8 requirement rows (ulna), 8 (ulna_l via mirror §3.2), 9 (hand_r), 9 (hand_l via §3.4); every row carries a citation |
| 2 | Existence mapping with quotes: target joints, mesh extent assumption, schema capacity | **PASS** — §2.1 source tree (XML lines), §2.2 pack (my receipt: 28 joints, FK children of wrist NONE, digit names NONE, spans 79.868/64.745 mm, bands 318/263 verts, mesh 18 459 verts), §2.3 recorded fit state (origins==target joints, axes null, 30 unplaced sites, per-tendon blockers), §2.4 schema capacity = YES (demonstrated by the shipped baseline's own anchor-authored segments), §2.5 assumptions A-1..A-3 stated |
| 3 | Classification matrix complete (requirement × body × classification) | **PASS** — §5 matrix: every cell classed SWEC / NNE (no cell is ARCH; the two ARCH items live in §6 flags, they are not per-body requirements) |
| 4 | Architectural-flags list explicit (digits at minimum) | **PASS** — §6: F-1 digit transmission ARCH out-of-scope; F-2 elbow/wrist anchor partition needs architect ruling (ulna distal anchor forces radius re-anchor; A4 radius record supersession); F-3 hand-region evidence dependency on B1 (crease seam); F-4 baseline-record supersession discipline |
| 5 | Baseline integrity: `git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot` empty | **PASS** — output pasted below (empty, exit 0) |

**Preregistration:** all three predictions CONFIRMED; falsifier ("a forced contract change") NOT FIRED — details in requirements_sheet.md §7.

## BASELINE INTEGRITY (criterion 5, run at audit end)

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty; exit 0)
```

## 10-LINE SUMMARY

1. Coordinate ownership is FIXED by the source and cannot be re-authored: `elbow_flexion(_l)` rides ulna/ulna_l, wrist triples ride hand_r/hand_l (direct-children intake `schema.py:68`; `chain_conflict` `correspondence.py:113-117`).
2. Both elbow and wrist transmission are UNDEFINED today purely because their owner bodies are unresolved: joint origins already equal the target joints (elbow_R/L, wrist_R/L) while all axes are null and 30 sites (10 ulna + 5 hand per side) are NaN — the 562/702 NaN census (A8).
3. Every GEOMETRY requirement of all four bodies is fillable by authored landmarks under the existing schema (NEEDS-NEW-EVIDENCE, none ARCHITECTURAL): the schema already carries these bodies as anchor-only segments.
4. Hand edges are closure-clean: hand P = wrist_R/L already equals the recorded `radius(_l).P_d`, so resolving a hand forces no re-anchoring of anything proximal.
5. Ulna edges carry the single structural tension (preregistered, measured): with radius the resolved first child of ulna, authoring ulna's distal landmark X (the ulna/radius shared joint, no pack landmark exists there) forces `radius.P` to re-anchor from elbow to X — the closure law (`compiler.py:399-423`, 1e-9) enforces a PARTITION of the elbow→wrist span between the two serial edges.
6. Consequence flagged, not chosen (F-2): resolving ulna supersedes the A4-verified radius/radius_l records (s = 0.22170679566544982, elbow→wrist anchored); the architect's D2 ruling is between the two-edge partition (new landmark evidence) and permanent ulna-unresolved (today's state, transmission stays UNDEFINED).
7. New evidence needed, per side: an ulna/radius shared-point landmark X + off-axis roll witnesses (elbow band 318 verts, wrist band 263 verts; machinery `_band_roll` exists) and a hand distal reference (machinery `hand_tip` exists, `mesh_target.py:156`) — no new schema fields, refusals, or validation rules.
8. Measured transmission thresholds once bodies resolve: elbow arms ⇔ ulna resolved (BRD's path is already complete); wrist arms for ECRL/ECRB/FCR/FCU ⇔ hand resolved alone; ECU needs BOTH; PT needs only ulna; wrist arms move only the 5 hand-owned sites per side (subtree(hand) = {hand}).
9. DIGIT transmission is ARCHITECTURALLY out of scope: articulated fingers are `absent_in_source` (DER §12) and the 28-joint pack has nothing distal of the wrist (FK children: NONE; digit names: NONE); only wrist/elbow transmission and static finger-geometry carriage (with the hand frame) are evaluatable.
10. Integrity: baseline untouched (git status empty); all writes under `forearm_package/audits/B3_mech_requirements/`; receipts `receipts/b3_pack_read.txt`, `receipts/b3_fit_packet_extract.txt`; assumptions A-1..A-3 (incl. hand-region skin evidence pending B1) recorded in requirements_sheet.md §2.5.

## FILES

- `E:/PythonChimera/forearm_package/audits/B3_mech_requirements/brief.md` (verbatim brief)
- `E:/PythonChimera/forearm_package/audits/B3_mech_requirements/requirements_sheet.md` (the deliverable)
- `E:/PythonChimera/forearm_package/audits/B3_mech_requirements/report.md` (this file)
- `E:/PythonChimera/forearm_package/audits/B3_mech_requirements/receipts/b3_pack_read.txt`, `receipts/b3_fit_packet_extract.txt`
- `E:/PythonChimera/forearm_package/audits/B3_mech_requirements/work/mesh_target_b3.py` (read-only pack reader, hash-printing, snapshot-repointed)
