# HIP-QUARANTINE ADJUDICATION (2026-09-20 lane) — per-muscle verdicts

Written AFTER the search, BEFORE any arm scan of this lane. Companion machine-readable
record: `adjudication.json`. The prereg (`record.md` + `receipt.json`) is untouched.

## THE LAW APPLIED (read from the books, applied unchanged)

- **The admission law** (the funnel's own, from the admitting lane's audit —
  `guimaraes_pairing_20260921/audit_table.json`, sha 843d1e70...): the guimaraes_arch
  connector quarantines "rows failing the dataset's own closure identities (PCSA =
  m/(rho*FL), muscle = belly + tendon) ... whole, visibly"; enforced tolerances
  mass_additivity 0.02 and pcsa_closure 0.02; blank cells quarantine. The Guimaraes
  M. mulatta row set is n = 1 (one specimen per species — the intake's own declared gap;
  the paper's Table 1: specimen 127, KU Leuven, male adult, "This study").
- **The substitution law** (k-fill record.md D2 + k-fill receipt citation_integrity):
  substitutions are lawful ONLY for ABSENT rows; QUARANTINED rows stay NAMED GAPS; "a
  homolog number would be a silent fill of a knowingly-conflicted number"; "any filled
  quarantined row is a violation". CONSEQUENCE (decided in the prereg, F1): the
  RESOLVED-BY-HOMOLOG route is UNAVAILABLE for every muscle under review. Myatt et al.
  2011 is named as still-future, never consumed.
- **The second-source law** (mission D2 + this lane's reading): a resolution by second
  source is a NEW intake judged on its own data-quality merits — published peer-reviewed;
  Macaca-genus muscle architecture by dissection; per-muscle PCSA published or derivable
  under the closure laws; n > 1 specimens; the candidate's own rows pass the funnel's
  data-quality laws. The Guimaraes verdict itself always STANDS; a second source replaces
  the quarantined row as the muscle's force source only with an explicit substitution
  record. Oku 2021 never qualifies (its own intake record: "simulation output trajectories
  of a planar nine-link model, not biological measurement").

## THE SEARCH (every source pinned or named-absent; F3)

Byte-pinned (in-repo):
- **Guimaraes et al. 2026** — AJPA 190(4):e70329, DOI 10.1002/ajpa.70329, PMC13425262.
  Full text XML pinned (sha a1ded31f...), S1 xlsx member sha 08ead4a9... (pinned inside
  the k-fill lane's annotation). DECISIVE NEGATIVE: the paper's Table 1 details ALL 30
  specimens of the study (the study's own new dissections PLUS the prior studies it
  compiles: Vereecke 2005, Payne 2006b, Myatt 2011, Oishi 2009, Charles 2019): exactly
  ONE Macaca mulatta exists in the whole compilation (n = 1, specimen 127). No other
  macaque row exists in the largest recent primate hindlimb-architecture survey.
- **Oku et al. 2021** — Commun Biol 4, DOI 10.1038/s42003-021-01831-w, PMC7940622 (full
  text XML pinned in-repo). Simulation output; its muscle parameter table reads "Values
  from Ogihara et al." — no dissection PCSA of its own.

Citation-pinned (examined, none lawful):
- **Ogihara et al. 2009** — AJPA 139(3):323-338, PMID 19115360, DOI 10.1002/ajpa.20986.
  Whole-body musculoskeletal model of M. fuscata; per-muscle mass and fascicle length
  recorded by dissection, PCSA derived. THE NEAREST MISS: built from "dissection of a
  cadaver" (abstract, singular; one adult male) — n = 1, the SAME single-specimen defect
  class as the quarantined rows. FAILS the n > 1 law. Non-OA; not admitted; recorded.
- **Myatt et al. 2011** — J Anat, great apes (per Guimaraes Table 1: gorilla/bonobo/
  chimpanzee/orangutan rows, "PCSA and fiber lengths only"). THE HOMOLOG ROUTE — closed
  by the books' substitution law; named as still-future for RF/SAR/AB/BFS.
- **Payne et al. 2006b** (apes + humans; cited by Guimaraes Table 1 only for gorilla
  rows) — no macaque. **Vereecke et al. 2005** (gibbons) — no macaque. **Oishi et al.
  2009** (gorilla) — no macaque. **Charles et al. 2019** (human DTI) — no macaque.
- **Marchi, Leischner, Pastor & Hartstone-Rose 2018**, Anat Rec, "Leg Muscle Architecture
  in Primates..." — primate leg architecture survey; no macaque surfaced in its sample
  and it is cited nowhere as a macaque source (Guimaraes Table 1 silent). Named-absent.
- **Wright et al. 2022** (NSF PAR) — small-bodied generalist MAMMALS (opossum et al.).
  Not macaque. Named-absent.
- **Anton 1999**, Int J Primatol 20:441-462 — macaque MASSETER internal architecture.
  Jaw, not hindlimb. Out of scope.
- **"Muscle dimensions in the Japanese macaque hand" (2012)** — hand/forelimb. Out of
  scope.
- **Walker & Schrodt 1974**, Anat Rec 178(1):63-81 — I-segment/thin-filament
  ultrastructure of rhesus fibers. Sarcomere-level, no per-muscle PCSA. Not lawful.
- **Acosta et al. 1987** (cynomolgus hindlimb fiber-TYPE composition, 3 males) —
  histochemistry, no PCSA. **Maxwell 1979** (rhesus fiber histochemistry) — no per-muscle
  PCSA. **Colman et al. 2005** (rhesus age-related muscle mass, 90 animals) — no
  per-muscle architecture. None lawful.
- **Casteleyn et al. 2023** (Vet Sci 10(3):172, PMC10051720) — rhesus topographical
  anatomy, pelvic limb: descriptive, no muscle architecture/PCSA. Named-examined.
- **Van Beesel et al. 2025** — cited in the pinned Guimaraes text as the KU Leuven
  project context of the SAME specimen environment (specimen 127); not surfaced as an
  independent architecture dataset; any such data would be n = 1. Not lawful.
- **Hazotte et al. 2026** (J Exp Biol 10.1242/jeb.252010) — kinematics/kinetics only.
- **Saito et al. 2021** (Front Syst Neurosci) — hand model, forelimb.

**SEARCH CONCLUSION:** no published macaque (Macaca sp.) architecture study with
per-muscle PCSA by dissection and n > 1 exists for RF, SAR, AB, BFS, or TP. The
quarantined rows are the ONLY published macaque PCSA for these muscles, and their rows
fail the funnel's admission law.

## PER-MUSCLE VERDICTS

### R_RF (rectus femoris) — QUARANTINE STANDS
- Defect (restated, from the pinned audit): `mass_additivity_dev_0.023` — belly 28.06 g +
  tendon 3.25 g = 31.31 g vs whole muscle 32.06 g; dev 0.0234 vs enforced tolerance 0.02
  (sheet row 11, cells G11/I11/K11). The row fails its own dataset's closure identity by
  2.34% — a data-quality fact of the single n = 1 specimen row, not a classification
  error.
- Unresolvable: no second source (search conclusion); the row itself is the only
  published macaque RF PCSA in existence; homolog route closed by law (Myatt 2011 named
  still-future).
- Deposit role (pinned geometry audit): R_RF crosses the hip ANTERIORLY (Pelvis->thigh->
  shank with rFemoralneck + rFemoralCondyles_Cylinder2 wraps) — a hip FLEXOR; its
  extension-book contribution is sign-gated. Named reading below measures its arm curve;
  its force stays null and is consumed by no sum.

### R_SAR (sartorius) — QUARANTINE STANDS
- Defect (restated): `mass_additivity_dev_0.095` — belly 9.39 g + tendon 0.90 g =
  10.29 g vs whole muscle 9.40 g; the parts EXCEED the whole by 9.5% (sheet row 21). The
  0.90 g tendon mass on a 9.4 g sartorius is itself the anomaly (the source's own
  additivity identity cannot hold). Additionally the row carries NO pennation (pennation
  was published only for the 19 homologous muscles of the 217-observation subset).
- Unresolvable: no second source; homolog closed.

### R_AB (adductor brevis) — QUARANTINE STANDS
- Defect (restated): `pcsa_closure_dev_0.684` — published PCSA 8.91e-05 m2 (E8) vs the
  dataset's own closure law PCSA = m/(1060 x FL) = 0.0049/(1060 x 0.0308) = 1.5010e-04 m2;
  the published PCSA sits 40.6% BELOW its own mass/FL closure (dev 0.684 in the funnel's
  relative form). The mass additivity on this row happens to pass (dev 0.014) — the
  defect is specifically the PCSA, i.e. exactly the number a force would be derived from.
- Unresolvable: no second source; homolog closed.

### R_BFS (biceps femoris short head) — QUARANTINE STANDS
- Defect (restated): `musc_mass_blank`, `belly_mass_blank`, `tendon_mass_blank` (sheet
  row 23) — the closure identities are UNCHECKABLE on this row.
- Additional recorded smell: the row's FL (D23 = 0.0712), PCSA (E23 = 1.007659e-3) and
  pennation (L23 = 26.2) are byte-identical to the R_BFL row 22 cells (D22/E22/L22) —
  consistent with a sheet-copying artifact, not independent measurements.
- Deposit role: R_BFS spans thigh_r -> shank_r with NO pelvis point — it does NOT cross
  the hip; its hip arm is identically zero (measured below), so it cannot enter the hip
  book regardless of any force. No published macaque BFS PCSA exists outside this row.

### R_TP (tibialis posterior) — QUARANTINE STANDS (context; not hip scope)
- Defect (restated): `mass_additivity_dev_0.060` (14.11 + 1.00 = 15.11 vs 14.25 g; sheet
  row 9). Not a hip muscle in the deposit (shank_r -> foot_r, R_Ankle_Cylinder wrap). The
  plantar book's named TP gap is unchanged by this lane.

## THE EXTENDED BOOK CONSEQUENCE

Admitted set: EMPTY. The landed hip book (forces byte-equal to the k-fill set, class
R_BFL + R_GMax + R_SM + R_ST, derived arms) is consumed UNCHANGED; the lane re-derives
the class curves with the landed protocol (byte-asserted against the landed book), scans
the four quarantined muscles as NAMED READINGS (no force), and computes the
COUNTERFACTUAL BOUNDS (never consumed) that make the rear-up closure robust: even if a
future lawful resolution admitted any quarantined muscle at its sheet PCSA, the
capability cannot cross the C* window floor. Deliverable: `extended_hip_book.json`
(3-run byte-identical). The rear-up C* verdict carries UNCHANGED: **NOT COVERED**, and
the prereg's P1/P2/P3 predictions are recorded as measured in `receipt.json`.
