# RUNBOOK — Vanhoof S1/S2 extraction + admission (the day the downloads land)

Everything here is Machinery-Ready as of the prestage battery
(`results.json`, this directory).  The synthetic battery proves the machinery;
the REAL tables get a calibration pass FIRST (step 3) — the synthetic recovery
numbers are an upper bound, not a promise.

Prereqs on this host (measured 2026-09-20): Python 3.14, numpy 2.2.6,
PIL 12.2.0, fonts times/arial/cambria/calibri.  NO tesseract — the route is
the deterministic template/grid-detection pipeline in `extract_table.py`
(see `receipt.json` → route).

## 0. RULE 0 — before touching real bytes

Write a NEW pre-registration into `receipt.json` (bump `preregistered_utc`,
add a `real_run` section) stating: the expected per-column layout of the real
S1/S2, the honesty classes you will admit, and the falsifier (e.g. "a column
whose decimal register breaks on >20% of cells suspends the register law and
the sheet is refused wholesale").  Do not reuse this battery's numbers as the
real day's predictions.

## 1. Operator: hand-download (PMC serves browsers, CLI is blocked)

- Part II (quantitative): https://pmc.ncbi.nlm.nih.gov/articles/PMC7812139/
  - Table S1: https://pmc.ncbi.nlm.nih.gov/articles/instance/7812139/bin/JOA-238-321-s001.tif
  - Table S2: https://pmc.ncbi.nlm.nih.gov/articles/instance/7812139/bin/JOA-238-321-s002.tif
- Part I (configuration/homology): https://pmc.ncbi.nlm.nih.gov/articles/PMC7495296/
- AT DOWNLOAD TIME pin the reuse license from https://doi.org/10.1111/joa.13314
  and https://doi.org/10.1111/joa.13222 into the batch receipt (expect an
  Anatomical Society / Wiley licence; unconfirmed).  Same recorded-tension
  treatment as the infant bones — recorded, never waived silently.

## 2. Stage + pin

```
cd E:/ChimeraWork/vh-agent          # branch agent/vanhoof-intake-prestage-20260921
mkdir -p tools/science_funnel/data/vanhoof_forearm
cp <downloads>/JOA-238-321-s001.tif tools/science_funnel/data/vanhoof_forearm/
cp <downloads>/JOA-238-321-s002.tif tools/science_funnel/data/vanhoof_forearm/
python -B -c "import hashlib,sys; [print(f, hashlib.sha256(open(f,'rb').read()).hexdigest()) for f in sys.argv[1:]]" tools/science_funnel/data/vanhoof_forearm/*.tif
```

Write `tools/science_funnel/data/vanhoof_forearm/download_receipt.json`:
source urls, PMC ids, the sha256s, the licence line, download timestamp.
(Shape it on `data/guimaraes_arch/download_receipt.json` on
origin/agent/skeleton-movie-20260919.)

## 3. CALIBRATION on the real S1 — before any admission

The synthetic battery used a 48 px text class; the real TIFFs are their own
thing.  One page, zero admission:

```
python -B - <<'PY'
import sys; sys.path.insert(0, 'tools/science_funnel/validation/vanhoof_prestage_20260921')
import extract_table as E, synth_table as S
bank = E.GlyphBank(S.available_fonts())
gray = E.load_gray('tools/science_funnel/data/vanhoof_forearm/JOA-238-321-s001.tif')
res = E.extract(gray, bank, {})          # no numeric columns yet: read-only pass
from collections import Counter
print('rows', res['n_rows'], 'cols', res['n_cols'])
print(Counter((c['class'], c['code']) for c in res['cells']))
print('score p01/p50:',
      __import__('numpy').percentile([c['conf_min'] for c in res['cells'] if c['conf_min']],[1,50]))
PY
```

Read this like a forensics lane: n_rows should be ~muscles+header; the
class histogram tells you whether the real page sits inside the machinery's
calibrated bands.  If the median true-class confidences land far below the
frozen bands, STOP — the domain gap is the finding; report it, do not retune
the bands silently (new pre-registration first).

## 4. Declare the manifest + homology

- `column_map`: real header label → canonical field (mass_g / volume_cm3 /
  fl_mm / mtu_mm / tendon_ext_mm / tendon_int_mm / pcsa_mm2) per specimen
  column.  Build it on `A.build_column_map` (lane file `admit_vanhoof.py`)
  with the REAL header strings; an unknown header must refuse
  (`unknown_or_duplicate_header`) — never guess.
- Homology table: Vanhoof muscle names → the 39 arm-model names
  (`tools/science_funnel/data/macaque_arm/monkeyArm_current.osim`).  The
  closed vocabulary in the adapter IS the error-correcting gate: unknown
  names refuse (`unknown_muscle`).  Watch the memo's known synonym:
  `ext digiti (minimi)` vs the model's `ext_digiti`.
- The MTU-additivity law is DECLARED but must be measured on the real rows
  first (Guimaraes discipline): if the real MTU − (FL+tendons) deviation is
  continuous, demote it to a recorded condition — quarantine only at the
  bimodal gap, never at a tuned cut.

## 5. Extract + admit

```
python -B - <<'PY'
import sys; sys.path.insert(0, '.')
sys.path.insert(0, 'tools/science_funnel/validation/vanhoof_prestage_20260921')
import extract_table as E, admit_vanhoof as A, synth_table as S
bank = E.GlyphBank(S.available_fonts())
numeric = {c: f for c, f in <your column_map>}
res = E.extract(E.load_gray('tools/science_funnel/data/vanhoof_forearm/JOA-238-321-s001.tif'),
                bank, numeric)
out = A.admit(res, cmap, E.tiff_sha256('tools/science_funnel/data/vanhoof_forearm/JOA-238-321-s001.tif'),
              'JOA-238-321-s001', <vanhoof vocabulary>)
print(out['count_identity'])
json.dump(out, open('tools/science_funnel/data/vanhoof_forearm/s001_records.json','w'))
PY
```

Honesty classes, non-negotiable:
- EXTRACTED-CONFIDENT (bands met) + laws pass → admitted record
  (`batch.property.measurement` v1, SI units, full cell provenance).
- EXTRACTED-LOW-CONFIDENCE → rejection row `low_confidence_extract`,
  the read + confidences preserved in the detail for hand review — NEVER
  admitted, never auto-promoted.
- REFUSED → named code (glyph_merge, decimal_ambiguous, ambiguous_glyph,
  low_contrast, grid_collision, cell_clipped, nonnumeric_cell, blank_cell,
  unknown_muscle, row_law_untestable, *_violation) — operator door.
- Count identity: fetched == admitted + rejected(weighted), zero silent
  drops.  If it does not close, the batch is broken — fix the lane, not the
  arithmetic.

## 6. Replay + gates

- Idempotent replay: re-run the admission on the same bytes; the record set
  must re-propose as no-ops (content-derived ids: vanhoof:sheet:muscle:spec:field).
- `python -B tools/training_gate.py` before anything downstream consumes the
  batch.
- Force-claims stay `force_runtime_ready: false` until the σ/upgrade decision
  (the memo's §2 classes ride along per record).

## 7. What this machinery does NOT do

- It does not read pennation (Vanhoof deliberately omits it — no pennation
  field exists in this source).
- It does not verify species/stage (the operator pins adult M. mulatta from
  the paper text; L1/L3 ride on the record conditions).
- It does not admit the σ-bootstrap's derived records — that is a separate
  batch with its own provenance.
- Synthetic recovery is not real recovery: the real-day numbers come from
  step 3's calibration and step 5's run, reported as measured.
