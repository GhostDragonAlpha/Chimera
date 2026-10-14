# HIP-QUARANTINE-REVIEW RECORD — Rule 0 membrane, written BEFORE any gathering

Lane `agent/hip-quarantine-review-20260920` (branch `lane/hip-quarantine-review-20260920`
@ 13b3ee5b, FROM the landed hip-arms tip). Mission: review the quarantined hip-relevant
rows (R_RF, R_SAR, R_AB, R_BFS; R_TP optional context) and decide, per the funnel's own
laws, ONE of three outcomes per muscle — QUARANTINE STANDS / RESOLVED-BY-SECOND-SOURCE /
RESOLVED-BY-HOMOLOG — then, for every muscle that gains a lawful force, derive its hip
arm curve (the landed hip-arms machinery, imported unmodified, same 2001-sample scan) and
re-run the hip-extension book + rear-up C* verdict with the extended set. The verdict
updates honestly in either direction; nothing else moves.

This file was written before this lane gathered its first literature byte. Everything
below is a determination on already-committed, sha-verified artifacts; every prediction
band in `receipt.json` was hand-derived from those banked bytes before any search or run.

## RULE 0

**STATEMENT.** The quarantined hip-relevant rows are adjudicable — stand, second-source,
or homolog — by the funnel's own laws (the guimaraes_arch admission law: rows failing the
dataset's own closure identities — mass additivity tol 0.02, PCSA closure tol 0.02, no
blanks — quarantine whole, visibly; the k-fill substitution policy: substitutions only
for ABSENT rows, quarantined rows stay NAMED GAPS), and any muscle that gains a lawful
force re-adjudicates the rear-up class on the landed derived-arm machinery. Someone could
disagree three ways: (a) the admission verdicts may have been classification errors
rather than data-quality defects — answered per muscle by restating the defect and asking
whether any available source resolves it; (b) a published macaque architecture study with
PCSA by dissection, n > 1, may exist for a quarantined muscle — answered by search with
every candidate pinned or named-absent; (c) an admitted extension may move the
rear-up C* verdict — answered by the re-run book with numbers in both directions.

**PREDICTION (pre-named, before any gathering).**
- **P1 — the quarantine STANDS for most (predicted: ALL FIVE) rows.** The admission
  verdicts were data-quality defects in the single Guimaraes specimen row (RF mass
  additivity dev 0.023 vs tol 0.02; SAR 0.095; AB PCSA closure dev 0.684; BFS three blank
  mass cells; TP 0.060), not classification errors, and the banked context states no
  published macaque RF PCSA exists outside the quarantined row. Secondary-source search
  expected to come back absent for RF/SAR/AB/BFS.
- **P2 — the structural argument for P3, from banked geometry:** NONE of the four
  hip-relevant quarantined muscles is a hip EXTENSOR in the deposit (the landed
  hip-arms book's geometry audit): R_RF and R_SAR cross the hip ANTERIORLY (hip flexors —
  their extension-sum contributions are sign-gated to ~0 wherever their arm about
  hip_flexion_r is positive), R_AB is an adductor (Pelvis->thigh_r, small flexion-axis
  arm), and R_BFS spans thigh_r->shank_r WITHOUT a pelvis point — it does not cross the
  hip at all, so its hip arm is identically zero regardless of any force. R_TP
  (context only) spans shank->foot and has no hip role. The only channel through which
  the C* verdict could re-open is an admitted muscle with BOTH a large force AND a large
  NEGATIVE arm — no quarantined row has that geometry.
- **P3 — any admitted extension adds < 20% to the hip-extension book** (hand-derived:
  add band < 2.144 N.m on the landed rear-up cap 10.718030 N.m; realistic adds far
  smaller — RF corrected force would be 30.0 MPa-derived 88.0932 x cos(5.0 deg) =
  87.7577 N but as a FLEXOR it is sign-gated at extension; AB 26.73 x cos(6.1 deg) =
  26.5778 N on a small adductor arm; SAR 12.21 N (pennation blank in the row — the
  declared factor-1.0 law would apply); BFS 302.2977 x cos(26.2 deg) = 271.2392 N but
  arm identically 0 — no hip span). The book therefore stays BELOW the 22.4 window floor:
  the gap is 22.4 - 10.718030 = 11.682 N.m (2.09x), and no <20% addition closes a 2.09x
  gap. **If P3's mechanism holds, rear-up-static is CLOSED as an engine fact and the
  move belongs to the dynamic skill layer — said plainly in the final receipt.** The
  falsifier direction is named in advance: an admitted muscle that adds >= 20% or crosses
  the 22.4 floor FIRES the prediction and the verdict RE-OPENS with its numbers.

**FALSIFIERS (the mission's five, verbatim in substance).**
- **F1 LAW-VIOLATION** — any silent fill (a quarantined row's force entering any sum
  without an explicit adjudication record), or any homolog used without the books'
  substitution law explicitly permitting it. The books' law is READ and it does NOT
  permit homolog substitution: k-fill record.md D2 ("substitutions are lawful only for
  ABSENT rows; QUARANTINED rows ... stay NAMED GAPS — overriding the funnel's own
  admission verdict with a homolog number would be a silent fill of a
  knowingly-conflicted number") and k-fill receipt citation_integrity ("quarantined rows
  ... appear in the deliverable ONLY as named gaps with their quarantine status; any
  filled quarantined row is a violation"). Consequence, decided BEFORE the search:
  outcome (3) RESOLVED-BY-HOMOLOG is UNAVAILABLE for every muscle under review; where no
  lawful second source exists the verdict is (1) QUARANTINE STANDS with the Myatt et al.
  2011 great-ape homolog named as still-future. A second-source admission is lawful only
  as a NEW intake judged on its own data-quality merits (see D2), never as a silent
  override of the Guimaraes verdict, which STANDS.
- **F2 SWEEP-BAN** — no constant moves except lawfully-admitted forces + their derived
  arms. Forces sigma 0.30 MPa (the one cited constant), demand C* fixed (33.6 top /
  22.4 floor), class law fixed (cap = max over window of SUM F |r| with the per-q sign
  gate), windows fixed, machinery fixed. Nothing else moves.
- **F3 TRACEABILITY** — every source and every row sha-pinned or citation-pinned
  (DOI/PMCID + the pinned bytes where fetched); zero uncited numbers.
- **F4 DETERMINISM** — the re-run derivation is 3-run byte-identical; sha256 recorded.
- **F5 SCOPE** — no source changes outside
  `tools/science_funnel/validation/hip_quarantine_review_20260920/`; the landed machinery
  (`pulley_rederivation_20260920/derive_pulley_arms.py`, `hip_arms_20260920/derive_hip_arms.py`)
  imported UNMODIFIED (sha-pinned); gait_controller.hpp, gait_* validation,
  first_skill_prestage_20260922/, master, and shared tooling untouched.

Any hit is measured and recorded. Nothing is tuned.

## DECISIONS (openly recorded, one number one reason, nothing swept)

**D1 — THE ADJUDICATION LAW PER MUSCLE.** For each of R_RF, R_SAR, R_AB, R_BFS (+ R_TP
context): (i) restate the quarantine defect from the pinned audit (guimaraes_pairing_20260921
audit_table.json rows + k-fill book QUARANTINED_* entries); (ii) state whether the defect
is resolvable from available sources; (iii) verdict = QUARANTINE STANDS (defect real,
unresolvable — restated) | RESOLVED-BY-SECOND-SOURCE (a lawful second source admitted per
D2, explicit substitution record) | RESOLVED-BY-HOMOLOG (unavailable per F1; recorded as
still-future via Myatt et al. 2011).

**D2 — WHAT COUNTS AS A LAWFUL SECOND SOURCE (fixed in advance).** All of: published
peer-reviewed study; Macaca-genus muscle architecture measured BY DISSECTION (not
imaging-estimate, not model fit, not simulation output — Oku 2021 is simulation output
per its own intake record and never qualifies); per-muscle PCSA published or derivable
from published mass/FL/pennation under the funnel's own closure laws; n > 1 specimens
(explicitly stronger than the quarantined row's n = 1 — the guimaraes_arch intake
declares "one specimen per species"); the candidate's own rows pass the funnel's
data-quality laws (mass additivity tol 0.02, PCSA closure tol 0.02, no blanks) — checked,
not assumed; species and n recorded explicitly on the substitution record; the force then
derives under the one cited sigma 0.30 MPa and the pennation-correction law, with the
pennation factor declared (blank pennation -> factor 1.0, the k-fill declared law on the
four absent-admitted muscles AM/GRA/PB/PL). A source that is itself quarantined or
closure-failing CANNOT be admitted — replacing one conflicted row with another is no
resolution.

**D3 — THE EXTENDED BOOK LAW (fixed in advance).** For every muscle that gains a lawful
force: derive its hip_flexion_r arm curve with the landed hip-arms lane's exact protocol
(scan_muscle from `hip_arms_20260920/derive_hip_arms.py` imported unmodified — hip
declared range [-1.5708, 1.5708] rad, 2001 samples, FD 1e-4 rad central differences,
per-call wrap-cache purge, artifact flag 0.172 m, scan stops recorded never
interpolated). The extended hip book = the landed class (R_BFL + R_GMax + R_SM + R_ST,
forces byte-equal to the k-fill set) + the admitted muscles, cap law and windows
unchanged (WALK = Oku before-alteration range; REAR-UP = extension side of the declared
range; C* covered iff > 33.6; the 22.4 floor read as the landed book's window floor).
The rear-up verdict updates honestly in either direction. Admitted muscles that are not
hip extensors enter the same sign gate as everyone else — the gate is the law, not a
filter I choose per muscle.

**D4 — DETERMINISM (F4).** Three independent full derivations of the extended book to
three paths; the deliverable's sha256 identical across all three; recorded in the receipt.

## CONSEQUENCE MAP

The verdict this lane hands the operator is per-muscle quarantine adjudications + an
extended hip-extension book + the rear-up C* verdict, which updates in whichever
direction the numbers go. If the prediction fires (quarantine stands, extension gain < 20%),
the plain closing statement is: **rear-up-static is CLOSED as an engine fact** — the
derived animal's hip-extension capability cannot reach the C* window floor from any
lawfully available force in the deposit's geometry, and the rear-up move belongs to the
dynamic skill layer (momentum, not static capability).
