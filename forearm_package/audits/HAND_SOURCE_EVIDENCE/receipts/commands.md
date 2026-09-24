# COMMANDS — HAND_SOURCE_EVIDENCE (R2 Form A)

All commands run from `E:/PythonChimera` (Git Bash), `PYTHONDONTWRITEBYTECODE=1` throughout,
CPU-only, no GPU/OpenGL/Vulkan context, figures matplotlib Agg (backend set before pyplot
import). Writes confined to `forearm_package/audits/HAND_SOURCE_EVIDENCE/`.

## 0. Pre-measurement integrity + spec read (before prereg froze)

```
$ git status --porcelain -- forearm_package/baseline_snapshot        # -> (empty), PORCELAIN_EMPTY_OK
$ git rev-parse HEAD                                                 # 768f3de04a3b5539a80cf85d9a4587505da8385d
```
Read (no writes): `audits/HAND_EVIDENCE_REQUEST/HAND_EVIDENCE_REQUEST.md` (§R2 governs),
`audits/O1_ulna_orientation/report.md` + `scripts/o1_probe_ulna_mesh.py` (discipline
precedent), `audits/O2_hand_orientation/report.md` (the failed prong),
`baseline_snapshot/source_xml/chimanoid.xml` L620–800 (hand bodies, geoms, sites) and
L845–911 (mesh asset declarations). Inventory listing of `vendor/myo_sim/meshes/` (215
files) + md5 spot-check `1mc.stl` vs `arm_r_1mc.stl` (differ: 456da6958… vs 66dafefe2…).

## 1. Prereg frozen

`prereg.md` written BEFORE any STL was opened/parsed (see its own header for the exact
pre-measurement state). No rule was edited after any measurement.

## 2. S1 — inventory + hashes

```
$ PYTHONDONTWRITEBYTECODE=1 python forearm_package/audits/HAND_SOURCE_EVIDENCE/scripts/s1_inventory_hashes.py \
    2>&1 | tee forearm_package/audits/HAND_SOURCE_EVIDENCE/receipts/s1_inventory_run.log
```
Result: 27 right geoms + 27 left geoms parsed; all 27 vendor `<name>.stl` matched; all
mesh-asset scales `[1.0, 1.0, 1.0]`; hand_r world origin (−0.0731, 0.532647, 0.202699) ==
R2 A4 pin exactly; left `<name>_l.stl` files ABSENT in vendor (all 27 checked).
Per-bone sha256 + tri counts + bboxes in `receipts/s1_inventory.json`.

## 3. S2 — identity assembly (frozen prereg sec.2)

```
$ PYTHONDONTWRITEBYTECODE=1 python forearm_package/audits/HAND_SOURCE_EVIDENCE/scripts/s2_identity_assembly.py \
    2>&1 | tee forearm_package/audits/HAND_SOURCE_EVIDENCE/receipts/s2_identity_run.log
```
Result (43.2 s): d_own per bone recorded; 19 chain links: 10 PASS, 9 FAIL at 3.5 mm
(FROZEN PRIMARY RULE **FIRED** — numbers preserved verbatim in
`receipts/s2_identity.json`); record reproduction: 155.285 mm vs 155.29, rays
66.99/96.42/100.17/89.10/78.61 vs 67.0/96.4/100.2/89.1/78.6 (all < 0.05 mm);
sites: ECRL-P4→2mc 0.80 mm, ECRB-P4→3mc 0.51 mm, ECU-P6→5mc 0.06 mm, FCR-P3→2mc
0.69 mm, FCU-P4→pisiform 16.83 mm (course class).

## 4. S2b — preregistered refined-rule diagnosis (primary fired)

```
$ PYTHONDONTWRITEBYTECODE=1 python forearm_package/audits/HAND_SOURCE_EVIDENCE/scripts/s2b_cmc_diagnosis.py \
    2>&1 | tee forearm_package/audits/HAND_SOURCE_EVIDENCE/receipts/s2b_cmc_diagnosis_run.log
```
Result (125.2 s): all 5 CMC surf–surf gaps **0.00 mm**; all 5 MCP surf–surf gaps
**0.00 mm**; MC proximal reach past own anchor 26.8–35.0 mm (bridges the CMC anchor gaps
26.7–31.3 mm); per-link child→parent-surface vectors recorded.

## 5. S3 — frozen derivation + acceptance (run once)

```
$ PYTHONDONTWRITEBYTECODE=1 python forearm_package/audits/HAND_SOURCE_EVIDENCE/scripts/s3_palm_normal.py \
    2>&1 | tee forearm_package/audits/HAND_SOURCE_EVIDENCE/receipts/s3_palm_normal_run.log
```
Result: n_palm = (+0.128427, −0.168691, −0.977266) hand_r local; pisiform sign-rule dot
−6.97 mm; acceptance split **5/5 CLEAN** (ECRL −3.26, ECRB −9.10, ECU −2.63, FCR +5.29,
FCU +4.36 mm); mirror exact (anchor max |Δ| = 0.0 mm; left normal exact z-mirror; left
split 5/5 clean). Falsifier (b): NOT fired. Falsifier (c): NOT fired.

## 6. Figure (Agg-only)

```
$ PYTHONDONTWRITEBYTECODE=1 python forearm_package/audits/HAND_SOURCE_EVIDENCE/scripts/s4_figure.py \
    2>&1 | tee forearm_package/audits/HAND_SOURCE_EVIDENCE/receipts/figures_run.log
```
`figures/hand_source_assembly_normal.png` — 3 declared views (palmar-side, dorsal-side,
distal) of the assembled skeleton, palm plate + pisiform + n_palm + sites.

## 7. End-of-work integrity

```
$ git status --porcelain -- forearm_package/baseline_snapshot        # -> (empty)  (pasted in report.md sec.7)
```

## Receipts index

| file | content |
|---|---|
| `receipts/s1_inventory.json` (+`_run.log`) | 27-bone inventory: XML anchors, scales, sha256, sizes, tri counts, local bboxes, left-file absence, family spot-checks |
| `receipts/s2_identity.json` (+`_run.log`) | per-bone d_own/inside, 19 links with fired-rule numbers, record reproduction, carpal adjacency (28 pairs), site distances, verdicts |
| `receipts/s2b_cmc_diagnosis.json` (+`_run.log`) | CMC/MCP surf–surf gaps, MC proximal reach, per-link gap vectors |
| `receipts/s3_palm_normal.json` (+`_run.log`) | derivation (n_hat, eigenvalues, pisiform dot), acceptance split R + L, mirror exactness |
| `receipts/figures_run.log`, `figures/*.png` | Agg-only figure |
