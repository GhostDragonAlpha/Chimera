# SOURCE VERDICTS — species-hand lane, phase 1 (acquisition + screening records; NO physics runs)

Lane: `wk-species-hand`. Campaign clock context: the Captain's both-in-parallel
ruling on the species-geometry referral (LIEUTENANT_RESUME_v2.json line 144/147);
the referral stays open. Phase 1 performed 2026-10-04 (host UTC). Acceptance =
sealed receipts, never prose; every load-bearing sha256 in EVIDENCE.md
(same directory). NO_WORKTREES honored: no worktree, no clone; the one CPU
execution (the STL structural inspection) ran through the canonical runner on
slot 2 as a sealed job. No physics run of any kind was executed.

## Source (a): Pisa rhesus skeleton STL — VERDICT: RESOLVED + LICENSED (CC BY-SA 4.0), but NOT per-bone segmented

- WHAT: `Macaca_mulatta_3d_scan_Natural_History_Museum_University_of_Pisa_C_1549.stl`,
  Wikimedia Commons. Mounted skeleton, specimen C 1549, Museo di Storia
  Naturale dell'Università di Pisa. Artist Patrizia17 (own work), 30 July 2024.
- LICENSE AT RETRIEVAL (verified twice, 2026-10-04): CC BY-SA 4.0 — Commons
  API extmetadata (UsageTerms "Creative Commons Attribution-Share Alike 4.0",
  LicenseUrl creativecommons.org/licenses/by-sa/4.0, AttributionRequired
  true) AND the archived file description page (revision 1146578100; category
  CC-BY-SA-4.0; Wikidata statement P275 = Q18199165). Obligations carried:
  attribution (artist + museum); share-alike on published derivatives (any
  derived per-bone mesh published outside the working environment must carry
  CC BY-SA 4.0). Internal screening is unencumbered.
- INTEGRITY: 124,518,634 bytes; source-declared SHA1
  `67e0dcbffb7f64195da29d4507bfd7f0bc9a8ff4` reproduced EXACTLY on download;
  local SHA256 `3f1536a9ab5c60479364535238d1531bd0b05862bd692edcf53047af51e526fe`.
  Stored in the data store `E:/ChimeraWork/research-data/20261004-species-hand/`.
- SEGMENTATION SCREENING (the campaign's need: per-bone geometry for the
  19-bone set or at least distal phalanges + metacarpals): SEALED RUNNER JOB
  `cb5d4a640caf4020ab6874d4361e7570` (slot 2, PASSED, exit 0,
  cleanup_verified TRUE, base `28a110f2eb3ec6495318bb70738d4408859e4ac3`
  = the astra tip / PR #344 merge, sealed manifest
  `ccce193f0fea329cfdd63339b31f17c3c213aee3800dbc8983a9d58c015c4155`).
  Result: binary STL, 2,490,371 triangles; global AABB extents (270.199,
  493.65, 369.055) units; under BOTH bit-exact and crack-tolerant welds the
  file has exactly TWO connected components: the whole skeleton as ONE merged
  surface (2,490,359 triangles) + one stray 12-triangle chip.
  **THE HAND BONES ARE NOT PER-BONE SEGMENTED.** Unit inference: max extent
  493.65 sits in the declared millimeters-plausible band — recorded
  reasoning, not a verdict. Per-bone anatomical labeling was NOT attempted
  (text-only worker; belongs to Stage 0 with independent visual review).
- CONSEQUENCE: the file IS usable as a species-true rhesus geometry SOURCE,
  but only through a declared segmentation + registration stage
  (geometry-AUTHORING with anti-tuning law) before the proven instrument
  ladder can rerun. That stage is preregistered as Stage 0 in
  `PREREGISTRATION_SPECIES_SCREEN.md` (same directory), which also freezes
  the honest UNKNOWN prediction and every carried assumption.

## Source (b): MorphoSource Nasalis larvatus hand micro-CT (DOI 10.17602/M2/M84422) — VERDICT: CHECK ONLY; NOT RESOLVED FOR USE; NO DOWNLOAD

- MEASURED LICENSE CORRECTION (record fields retrieved 2026-10-04 via a
  reader-service fetch of the record page; the site's public pages return an
  Anubis bot-check wall to direct fetches — the campaign's manual-fetch
  constraint, re-observed): the record states **NO Creative Commons license
  at all** ("Creative Commons license: --", "Copyright statement: Copyright
  Undetermined"), MorphoSource use agreement type "Standard", "Commercial
  Use Not Permitted", "3D Printing Permitted", "Required archival of
  published derivatives: On MorphoSource". The earlier campaign shorthand
  "CC BY-NC" is therefore IMPRECISE: the actual terms are stricter and
  less defined than CC BY-NC (copyright undetermined, no formal CC license).
- WHAT THE TERMS (as stated at the record) WOULD PERMIT, for an authorized
  human acceptor of the agreement: non-commercial research use, 3D printing,
  with citation of Almecija et al. 2024 Scientific Data
  (doi 10.1038/s41597-024-04261-5), NSF funding attribution (BCS 1316947),
  and re-archival of published derivatives on MorphoSource. WHAT THEY
  FORBID: commercial use (unqualified); the download flow itself requires
  account login + an explicit click-through acceptance ("I agree to all
  terms and conditions of use for this data...") + a 50-character intent
  statement read by site administrators and data contributors.
- DETERMINATION (per mission): DOWNLOAD REFUSED. The acceptance flow is a
  contract acceptance this agent cannot verify or accept on the operator's
  behalf. Additionally, even if accepted: (i) the campaign's downstream
  includes an open-source engine and a future game whose visibility/license
  is UNSELECTED — a Commercial-Use-Not-Permitted, Copyright-Undetermined
  asset cannot lawfully feed any released-product path; (ii) N. larvatus
  (colobine) is NOT Macaca mulatta — species-true only in the broad
  nonhuman-primate sense, with known colobine/macaque hand differences
  (e.g., thumb reduction); (iii) the media is a RAW CT STACK (2,049 TIFF
  slices, 0.076354 mm isotropic, 912 MB zip) — all segmentation labor would
  be on this project.
- RECORD: `E:/ChimeraWork/research-data/20261004-species-hand/morphosource_m84422_license_check_receipt.json`
  (+ the bot-wall HTML archived as `morphosource_m84422_page.html`).

## Source (c): additional sources searched — VERDICT: NO DIRECTLY USABLE PERMISSIVE SOURCE FOUND at this lane's access level; leads recorded

1. Commons Pisa collection (same uploader/museum, category "STL files from
   Museo di storia naturale dell'Università di Pisa", 100 files listed):
   ALL primate entries are WHOLE-SKELETON scans (Macaca mulatta C 1549;
   M. nigra; M. sinica; M. sylvanus; Papio x3; Colobus x2; Semnopithecus x2;
   Hylobates; Cercopithecus; Daubentonia x2; Ailurops) — same workflow as
   C 1549, so the same merged-mesh limitation applies BY WORKFLOW INFERENCE
   (measured only for C 1549; the inference is declared, not measured per
   file). Only large mammals have part scans (mandibles/skulls); no primate
   hand-only STL exists in the collection.
2. "Primate Phenotypes" MorphoSource project 00000C706 (Almecija et al.
   2024 Scientific Data; 6,192 media, 386 specimens, 47 genera; the paper
   notes hands/feet are the best-covered regions): publication status "open
   download" per the paper, but the per-record terms MEASURED at its member
   M84422 (no CC license, copyright undetermined, commercial use not
   permitted, click-through agreement) govern the family; per-record license
   verification for any OTHER record requires a manual operator account
   (bot wall). NOT usable this phase; manual-operator follow-up named.
3. oVert / openVertebrate collection on MorphoSource (collection 000368762):
   reported CC0-oriented, but (i) whether it contains ANY Macaca hand CT is
   UNVERIFIED, and (ii) per-record licenses are behind the same bot wall.
   LEAD ONLY — named manual-operator check; nothing adopted.
4. Visible Monkey (Chung/Kim/Park, JKMS 2019/2020; whole-body sectioned
   images of a female rhesus at >0.05 mm intervals, 167 structures segmented
   incl. skeleton): paper is CC BY-NC 4.0 and data access is gated behind
   "user certification by the Electronics and Telecommunications Research
   Institute" — the same restricted class as (b); per-bone hand segmentation
   is not demonstrated (167 whole-body structures). NOT usable.
5. Limblab `monkeyArm_current.osim` (already campaign-pinned, sha256
   `4148aee2...`): carries the measured rhesus references the A05 frame uses
   (hand mass, wrist ranges, hand-length envelope), but its hand is a SINGLE
   body with an envelope surface (`hand.vtp`) — NO per-bone geometry. It
   remains the frame/constraint source, never a bone-shape source.
6. "Hand Musculature of the Rhesus Monkey (Macaca mulatta)" (Anatomia/MDPI,
   CC BY 2024): descriptive dissection anatomy with photographs — useful
   anatomical CONTEXT for future muscle work, contains NO 3D bone geometry.

## The honest absent list (carried assumptions; every one DECLARED)

1. NO species-true tendon/muscle data (no morphometry, attachments, or force
   capacities for the true anatomy; Cheng tables exist for the limb but are
   license-flagged and are NOT inputs here).
2. NO species-true digit joint axes/ranges — the A05 conventions carry the
   human digit pattern + human-scaled ranges; only the wrist ranges are
   measured-rhesus (Limblab). The mounted scan pose contributes no
   kinematics.
3. NO cartilage/soft tissue, NO volar pads (A2-class absent), NO measured
   volar friction (0.6/0.4 remain NAMED placeholders; the NB-01/02 gap
   stands).
4. NO museum-cataloged per-bone mapping — Stage 0 authoring + independent
   review; n=1 specimen (C 1549), museum-cataloged age/sex/pathology
   recorded not verified.
5. Cut surfaces are AUTHORED (declared-degradation law); living
   articulation gaps are not resolved by a mounted-skeleton surface scan.
6. Wrist/kinematic chain assumptions (wrist-anchored root, -Y long axis,
   19-edge naming) carried from the A05 frame unchanged.
7. Units inference (millimeters) is recorded reasoning, pinned as a declared
   Stage-0 conversion step.

## THE HONEST GO/NO-GO for the species-true ladder

**CONDITIONAL GO — gated exactly on Stage 0, with a real NO-GO branch.**

- The ONLY licensed-verified species-true rhesus geometry source is a fused
  whole-skeleton surface scan (measured, sealed receipt). The proven ladder
  (instrument `9514c5b1...`, same tolerances, same families + digit-side
  extensions, frozen 74 mm trunk) can rerun against it ONLY after a
  segmentation + registration stage that is geometry-AUTHORING. The
  campaign has already rejected authored geometry tuned to success (R3
  precedent), so Stage 0 is admissible ONLY under the preregistered
  anti-tuning law: fidelity to the SOURCE BYTES, declared cut-fraction
  ceilings, `UNRESOLVED_BONE` class non-verdict-bearing, independent visual
  review of the anatomical labels (this lane cannot inspect pictures),
  firewall between Stage-0 workers and any ladder result.
- If the Lieutenant does not authorize an authored-segmentation stage, the
  honest verdict is NO-GO for the species-true ladder this phase: no
  directly usable permissive source exists ((b) and the (c) leads are
  license-gated or unverified; the Commons collection is whole-skeleton
  scans), and the referral's species question stays answered at exactly the
  point this record leaves it — the source is real, licensed, and not yet
  per-bone.
- Under NO branch does this lane adopt (b) or any click-through source
  without an authorized human acceptance; under NO branch does any
  prediction exist beyond the preregistered UNKNOWN + the battery prediction;
  under NO branch does a "clean placement" claim extend beyond feasibility
  evidence at the scanned geometry.

## Chain position and handoff

- Phase 1 artifacts: data store
  `E:/ChimeraWork/research-data/20261004-species-hand/` (STL + receipts +
  archives); lane `E:/ChimeraWork/monkey-coordination/species-hand/`
  (prereg draft, verdicts, EVIDENCE.md, sealed package + twins). All
  load-bearing sha256 values in `EVIDENCE.md` (same directory).
- NEXT (the Lieutenant): (1) record the (b) license correction chain-wide —
  the "CC BY-NC" shorthand is superseded by the measured record fields;
  (2) decide the Stage-0 authorization question above; (3) if GO, commit
  `PREREGISTRATION_SPECIES_SCREEN.md` ALONE FIRST on the publication lineage
  and return the commit pin (implementation packages then pin it); if NO-GO,
  the referral closes honestly with this record. Sergeant review of THIS
  phase's records is requested through the Lieutenant (no self-review; no
  picture claims from this text-only worker).
