# THE VISIBLE MONKEY INTAKE — RUNBOOK (prestaged 2026-09-21)

<!-- Lane agent/visible-monkey-intake-20260921. Base 77f3d279. Rule 0 receipt:
     receipt.json in this directory (statement/prediction/falsifiers banked
     BEFORE the tools existed). This runbook holds the SEQUENCE and the GATES
     for the day the operator's email lands the data. Fill specs, run commands;
     no code should need writing. Every gate refuses by name — a red is a
     finding, never a workaround. -->

**The dataset** (docs/research/20260920_adult_and_muscle_data_options.md §2 Tier-1
lead (f)): Chung et al. 2019, *J Korean Med Sci* 34:e70 (PMCID PMC6393759) +
Kim et al. 2020, PMCID PMC7167398 — one adult-CONFIRMED **93-month female
rhesus** (4.3 kg, 758 mm): whole-body serial sections (0.05 mm head / 0.5 mm
body; 2,967 images, 8688×5792 @ 0.024 mm pixel), **paired 3T T1/T2 MRI + CT of
the same specimen**, and the **167-structure segmented STL set** (Mimics 17.01)
= skin + skeleton + merged-muscle membranes — three membrane layers, one
specimen, TRIANGLES (the doctrine's direct route).

---

## STEP 0 — quarantine and pin the bytes

- [ ] Data arrives by email/certification (ETRI for the STL set; park the
      request and reply in the data root). Create the data root **outside the
      repo** (bulk data never lands in git):
      `E:/ChimeraWork/visible_monkey_data/`
- [ ] sha256 EVERYTHING before touching anything:
      `python -B -c "import hashlib,sys,pathlib; [print(hashlib.sha256(p.read_bytes()).hexdigest(), p) for p in sorted(pathlib.Path('E:/ChimeraWork/visible_monkey_data').rglob('*')) if p.is_file()]" > download_receipt_raw.txt`
- [ ] Copy `tools/science_funnel/data/visible_monkey/dir_spec.template.json`,
      `volume_spec.template.json`, `collection_record.template.json`,
      `labels.template.csv` next to the data. The templates are the CONTRACT.

**GATE 1 — LICENSE (operator's call, never waived in code).** The two papers
are CC BY-NC 4.0; the STL dataset's license is UNSTATED at source; download is
"after user certification" (ETRI). Record the WRITTEN terms that arrive in
`collection_record.json → license`. Commercial use stays NOT PERMITTED unless
the operator says otherwise on the record. If the terms forbid our use: STOP —
blocked-with-evidence, not a workaround.

## STEP 1 — the STAGE GATE (biological law; admission-required)

- [ ] Fill `collection_record.json` from the data's OWN records:
      species `Macaca mulatta`, sex `female`, **`age_months: 93`**,
      `age_source` citing Chung et al. 2019 (93 months = 7.75 y; rhesus
      adulthood ~4–5 y, van Wagenen & Catchpole 1956 — adult with margin),
      `life_stage: "adult"`, `body_mass_kg: 4.3`, `body_length_mm: 758`.
- [ ] **The law the translator enforces:** `adult` is admitted ONLY with age
      evidence (`age_months` + `age_source`); unlabeled = unadmitted
      (`stage_unconfirmed`). One creature, one life stage; any per-structure
      contradiction refuses (`stage_mixing`). There is no allometric code path
      to "fix" a stage mismatch — the H2 3.79–8.8× stretch is the adjudicated
      FANTASY negative example.

## STEP 2 — the STL route (the direct route: triangles → membranes)

- [ ] Land the 167 STLs under `stl/`; fill `labels.csv`
      (`id,label,system[,stated_volume_mm3]` — `system` ∈ skeletal / articular /
      muscular / integumentary / organ; stated volumes from the segmentation
      tables when available — they become a 5% cross-check, `volume_mismatch`
      refuses). Set `stl.expected_count: 167` (any other count refuses
      `structure_count_mismatch`).
- [ ] Fill `dir_spec.json` (copy of the template with real paths; keep
      `enforce_body_fraction_bands: true`).
- [ ] Build + verify:

```bash
python -B tools/science_funnel/visible_monkey_import.py build  <path>/dir_spec.json
python -B tools/science_funnel/visible_monkey_import.py verify <path>/dir_spec.json
```

**GATE 2 — the mesh laws (each refusal names itself):** closed manifold
(`mesh_not_closed` — a non-closed mesh has no defined enclosed volume), labels
(`label_missing` / `label_orphan` / `duplicate_structure_id`), counts
(`structure_count_mismatch`), volumes (`volume_mismatch`), stage (Step 1).
Euler characteristic is REPORTED, not gated (bones have genus).

**GATE 3 — the mass book closes biologically.** Build writes the derivation
book. On the REAL data check: segmented total within **[0.6, 1.3] × 4.3 kg =
[2.58, 5.59] kg** (segmentation excludes blood + GI contents — deviations are
NAMED, never tuned); skeleton fraction **8–15%** of body mass; muscle
**25–50%** (`whole_body_band` / `system_fraction_band`). Densities are cited
in-repo (ICRP 89/23; Yamada 1970; Méndez & Keys 1960; Cowin/Currey); organs
share one soft-tissue material (±5% organ spread named). Bonds do NOT exist
yet: the STL set ships no measured adjacency — zero invented joints, honest
connected components. Measuring touching edges (assembly PDF + mesh contact)
is the named successor; when measured, drop `touching_edges.json` and re-run.

## STEP 3 — the volume route (paired 3T MRI + CT; interior structures)

- [ ] Fill `volume_spec.json` per volume (one spec per MRI/CT):
      `modality: "ct_mri_density"`, volume path + reader, voxel spacing FROM
      THE DICOM HEADERS (never copied), threshold law `density_percentile`
      p95 (the morphosource_ct LAW: it measured 118 on 000875604 and 148 on
      000875599 — two specimens, two numbers, one law; a `fixed` threshold is
      legal only with a recorded reason), morphology open+close 1,
      ≥1000-voxel components, marching cubes at 0.5, cap 25.
- [ ] Build + verify:

```bash
python -B tools/science_funnel/visible_monkey_volume_route.py build  <path>/volume_spec.json
python -B tools/science_funnel/visible_monkey_volume_route.py verify <path>/volume_spec.json
```

Outputs: full-res OBJs + ≤30k-face previews + manifest (per-component volume,
extents, centroids, voxel delta) + sha256 receipt. Feed approved components
through the STL route's translator pattern for matter admission (they are
triangles now).

## STEP 4 — the serial-section images (THIRD modality — UNTESTED, honestly)

The 2,967 COLOR section images segment by COLOR thresholds (per-tissue color
bands / deconvolution at 0.024 mm pixel), not density. The route is hooked and
**refuses** (`modality_untested`) until calibrated on the real sections. It
may NOT be forced open by code changes alone: calibration is successor work
WITH the landed bytes, and its own Rule-0 receipt. Expecting this refusal is
correct behavior; silently "fixing" it is not.

## STEP 5 — assemble + THE REALITY GATE

- [ ] Assemble the creature bundle (bones + merged muscle + skin membranes of
      ONE stage-true specimen; bonds only at measured adjacency).
- [ ] Adjudicate with the reality gate (`tools/creature_graph/reality_gate.py`,
      branch `agent/reality-fantasy-gate-20260920` at prestaging time — merge
      state to check the day this runs): the gate CLASSIFIES
      `{category: reality|fantasy, violations[]}`.
- [ ] **Expected verdict: REALITY** — one adult-confirmed specimen, scale 1.0,
      identity transform, cited materials, measured books. Any FANTASY verdict
      means a violation was introduced during intake: find it, fix it, re-run;
      never reclassify to green.

## STEP 6 — the verification battery (what the lead runs)

- [ ] `python -B -m unittest tools.science_funnel.tests.test_visible_monkey_intake`
      (29 tests: synthetic geometry/mass/refusal/determinism + phantom volume
      route — the machinery proof, banked in `verify.json` 2026-09-21)
- [ ] Translator verify (Step 2) + volume-route verify (Step 3) in a TRUE
      fresh clone of the branch with worktree==blob pre-checked
      (`git hash-object` vs `git rev-parse HEAD:path`) — the sharpened
      reproducibility standard from the Copernicus-EOXML correction.
- [ ] Baseline stays untouched: matter kernel 46 OK; creature_graph 19 passed
      + 27 subtests from repo root AND tools/; the 5 pre-existing reds on base
      77f3d279 (test_coupled_scene / test_earth_scene / test_force_arm /
      test_force_compiler / test_macaque_anatomy — force_models semantic
      replay + anatomy idempotency, failing BEFORE this lane touched anything)
      are recorded in the receipt, owned by their lanes.
- [ ] Commit + push THIS branch only; trailer `Agent: GLM 5.3`. Receipts
      append-only: the REAL-data run appends a new dated record, it never
      edits the pre-registered block.

---

## The exact commands, the day the data lands (summary)

```bash
# 1. pin the bytes (Step 0), fill collection_record.json + labels.csv + dir_spec.json
python -B tools/science_funnel/visible_monkey_import.py build  E:/ChimeraWork/visible_monkey_data/dir_spec.json
python -B tools/science_funnel/visible_monkey_import.py verify E:/ChimeraWork/visible_monkey_data/dir_spec.json
# 2. per MRI/CT volume: fill volume_spec.json (voxels from DICOM headers)
python -B tools/science_funnel/visible_monkey_volume_route.py build  E:/ChimeraWork/visible_monkey_data/volume_spec.json
python -B tools/science_funnel/visible_monkey_volume_route.py verify E:/ChimeraWork/visible_monkey_data/volume_spec.json
# 3. machinery battery (must stay green)
python -B -m unittest tools.science_funnel.tests.test_visible_monkey_intake
# 4. reality gate on the assembled bundle (expected: REALITY)
python -B tools/creature_graph/reality_gate.py <bundle.json> -o <adjudication.json>
```

The one-line law underneath: no reference, no verdict. The collection record
is the stage reference; the written license terms are the license reference;
the analytic synthetic volumes were the pre-data reference for the machinery.
Everything else is named refusal or measured book.
