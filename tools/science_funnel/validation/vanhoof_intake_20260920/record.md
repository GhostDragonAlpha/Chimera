# VANHOOF INTAKE 20260920 — lane record (the real day the prestage runbook is for)

Lane: `lane/vanhoof-intake-20260920` @ base `e3ae3dff` (INTEGRATION PASS 4 receipt).
Prestage: `tools/science_funnel/validation/vanhoof_prestage_20260921/` — its battery proved
the MACHINERY (deterministic grid+NCC extraction, named refusals, closure-law admission);
this lane runs the real day: downloads → calibration → manifest → extraction → admission.
RULE 0 prereg: `receipt.json` in this directory, written BEFORE any download. The
runbook's "write the new prereg into receipt.json" is honored by this lane's own receipt
(the prestage's committed receipt is a frozen record; F5 forbids rewriting committed receipts).

## Scope reconstruction — what the prestage names (quoted)

1. **RUNBOOK.md step 1** (the download list, verbatim):
   > Part II (quantitative): https://pmc.ncbi.nlm.nih.gov/articles/PMC7812139/
   > - Table S1: https://pmc.ncbi.nlm.nih.gov/articles/instance/7812139/bin/JOA-238-321-s001.tif
   > - Table S2: https://pmc.ncbi.nlm.nih.gov/articles/instance/7812139/bin/JOA-238-321-s002.tif
   > - Part I (configuration/homology): https://pmc.ncbi.nlm.nih.gov/articles/PMC7495296/
   > - AT DOWNLOAD TIME pin the reuse license ... (expect an Anatomical Society / Wiley licence; unconfirmed). Same recorded-tension treatment as the infant bones — recorded, never waived silently.

2. **receipt.json → context.target** (the extraction target, verbatim):
   > 7 adult M. mulatta (Mm1-Mm7), ~40+ forearm/hand muscles/heads, per-muscle mass / volume / MTU / fascicle length / external+internal tendon / derived PCSA (no pennation by the authors' stated omission). Tables exist ONLY as TIFF images.

3. **RUNBOOK.md steps 3-6** (the admission plan): read-only calibration on the real S1
   BEFORE any admission (median confidences far below the frozen bands ⇒ STOP, the domain
   gap is the finding) → declare `column_map` + homology vocabulary (39 arm-model names,
   `monkeyArm_current.osim`; the memo's known synonym `ext digiti (minimi)` vs `ext_digiti`)
   → extract + admit (`admit_vanhoof.admit`, honesty classes non-negotiable, count identity
   must close) → idempotent replay + `python tools/training_gate.py`.

4. **Scope limits inherited**: macaque rows only (gibbon columns refused/reported, never
   admitted); no pennation (the source omits it); nothing extracted from Part I (it feeds
   the homology vocabulary only); Part II article figures and Part I supplementary figure
   TIFFs are NOT named data — not downloaded, decision recorded in the receipt.

## Reconciliation notes (decisions, not drifts)

- **Prereg location**: RUNBOOK step 0 says to write the real-day prereg "into receipt.json".
  This lane writes it into `vanhoof_intake_20260920/receipt.json` and POINTS at the prestage
  — a committed receipt is a record of what was believed then; editing it would be
  history-rewriting (F5).
- **Staged data committed, not gitignored**: the brief's generic shape says "bulk data stays
  OUT of git"; the prestage RUNBOOK step 2 stages the TIFFs under
  `tools/science_funnel/data/vanhoof_forearm/` and pins their sha256s, and the funnel's own
  precedent commits the sha-pinned source bytes (guimaraes_arch 321 KB xlsx; esa_worldcover
  4.6 MB TIFF + 4.1 MB PDF; largest committed data blob 80 MB). The datasets-out-of-git law
  targets re-fetchable bulk corpora (e.g. `research_references/human/gait_osf/`), not the
  primary source bytes a sha pin must be able to verify ("a file existing is not proof").
  The two table TIFFs (~16 MB total) + two article PDFs are committed under
  `tools/science_funnel/data/vanhoof_forearm/` with the byte-stability law
  (`.gitattributes`: `tools/science_funnel/data/** -text`) holding checkout-invariance.
- **PMC CLI block**: the runbook says "PMC serves browsers, CLI is blocked". Downloads go
  through PowerShell `Invoke-WebRequest` (browser UA); on 403 the europepmc REST mirror
  supplies the same bytes (the guimaraes receipt documents the mirror's re-zip caveat and
  the inner-member sha stability that makes the pin honest).

## The day's ledger (appended as measured)

- prereg written + committed: BEFORE any download (this commit).
- downloads: see `tools/science_funnel/data/vanhoof_forearm/download_receipt.json` (post-download).
- calibration: see `calibration_s1.json` (post-run).
- extraction/admission: see `extraction_s1.json` / `extraction_s2.json` + the staged
  `s001_records.json` etc. (post-run).
- falsifier verdicts: `receipt.json` → `real_run` section (post-run), summarized in the
  final lane message.
