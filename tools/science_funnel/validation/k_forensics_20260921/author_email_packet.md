# Author email packet — the k-scale divergence (k-forensics-20260921)

PASTE-READY TECHNICAL NOTE for the operator to send to the authors of:
Wiseman AL, van Beesel J, Vereecke E (2026), "Comparative analysis of primate
hind limb muscle moment arms using subject-specific three-dimensional
musculoskeletal models", R Soc Open Sci 13: rsos.260107.
Everything below is measured from the authors' own public deposits (Zenodo
20041122 Primate_models.zip, Figshare SI 1/SI 2) and cited literature.

---

SUBJECT: Moment-arm scale factor between your deposited models and SI table 2 (rsos.260107)

Dear Dr Wiseman, Dr van Beesel, and Prof Vereecke,

Thank you for depositing the primate musculoskeletal models and supplements
(CC BY 4.0) — we have been using the macaque model's path geometry for
independent moment-arm derivations, and we would value your help resolving
one systematic discrepancy we can measure but cannot resolve from the
deposits alone.

**1. What we measure.** Re-deriving -dL/dq moment arms directly from the
deposited Macaque_model.osim path geometry (exact tangent wrapping on your
wrap cylinders/ellipsoid, 2001-sample scans over the SI table's recorded
joint ranges) reproduces the SI 2 macaque rows' SHAPE exactly — same signs,
same triceps ordering |MG| > |LG| > |SOL|, same per-muscle extrema patterns —
but at a uniform scale: every SI 2 macaque moment arm equals our
deposit-geometry arm times k = 0.119754, constant to 4-5 significant digits
across:

  - the MTP flexion class (R_FDL II-V, R_FHL; pure point geometry):
    k = 0.11975394, spread [0.1197283, 0.11976842];
  - the knee extension class (R_RF, R_VI, R_VL, R_VMed; condyle-cylinder
    pulley engaged 2001/2001 samples): consistent with the same k to within
    0.089 mm at every endpoint;
  - the ankle class (R_SOL, R_MG, R_TA, R_PB, R_PL, R_EHL — a third joint):
    k = 0.11976026, spread [0.11975902, 0.11976056].

The same derivation on your Gorilla and Gibbon deposits gives different
per-taxon constants (gorilla k = 0.0329, gibbon k = 0.10845, macaque
k = 0.11975), each constant across both tested joints. Because the three
constants differ, this cannot be one spreadsheet-wide unit conversion; and
because it is constant within each taxon across three joints, it looks
exactly like a uniform geometric scale difference between the deposited
.osim builds and whatever model builds produced SI table 2.

**2. Which scale is anatomical?** Your deposited macaque bone meshes measure
as an adult female rhesus: femur maximum length (exact maximum pairwise
vertex distance, the digital twin of caliper absolute maximum length)
173.13 mm, tibia 156.81 mm — inside the adult female year-mean ranges of the
Cayo Santiago skeletal series (Francis & Wang 2023, Am J Biol Anthropol,
635 mature specimens: female femur 158.9-175.2 mm, tibia 146.5-161.6 mm;
males 178.4-207.4 mm and 165.1-184.5 mm). The acquisition-scale reading of
your deposit is confirmed per bone. Meanwhile the two readings of the k
factor imply:

  - if SI 2 numbers are MILLIMETRES of the SI-model, the SI-model's femur
    would be 173.13 x 0.119754 = 20.7 mm — a mass-implied ~10 g animal,
    below any postnatal rhesus (newborn ~0.4-0.57 kg; interpolated newborn
    femur ~73 mm). Physically impossible for the adult animals your arms
    must belong to;
  - if SI 2 numbers are CENTIMETRES, the SI-model is 173.13 x 1.19754 =
    207.3 mm at the femur — the very top of your adult MALE range, against
    a deposit that sits in the female band.

We also note (secondary): the deposited model's segment masses sum to
0.772 kg — infant-class for M. mulatta (adult females 5.4-6.9 kg,
Turnquist & Kessler 1989) — while its bone geometry measures adult-female
class, so the deposit's mass set and geometry appear to come from
different scaling sources as well.

**3. Angulation agrees; no scale anchor exists in the SI.** Every SI 2 joint
range we checked (26 rows across KneeFE/AnkleFE/MTPFE) reproduces your
scans' angular ranges exactly, and every range sits inside the deposited
model's coordinate ranges — angles are scale-invariant, so the divergence is
purely in the length columns. SI 1 and SI 2 carry no body mass, bone length,
or subject table, so the deposits alone cannot tell us which build is which.

**4. Why it matters to us (and possibly to you).** At deposit scale, the
measured ankle musculature covers the experimentally measured walking
demand of adult macaques (plantarflexion capability 6.25 N.m vs 5.92 N.m
measured walk peak; Oku et al.'s intramuscular-force animals), and the knee
and MP books close similarly; at SI scale every joint collapses to 0.13-0.22x
of the demand — an adult animal cannot walk on ankles that small. So our
working hypothesis is: the DEPOSITED models are anatomically scaled, and the
SI 2 tables were computed from differently-scaled (subject-specific?) builds.

**Our specific questions:**

1. Are the deposited Zenodo models at anatomical (adult) scale, and were the
   SI 2 moment-arm tables computed from DIFFERENTLY-SCALED subject-specific
   model builds (e.g., scaled to each specimen's CT-derived anthropometry)?
   Or is the deposit the subject-specific build and SI 2 something else?
2. If the SI models were scaled, what scaling source was used (segment
   lengths from CT/MRI? body-mass allometry?), and is k = 0.11975 the linear
   scale ratio for the macaque build?
3. What unit are SI 2's moment-arm columns in (the sheet states none; our
   measurements are only consistent with centimetres of the SI-model)?
4. Is the deposit's 0.772 kg segment-mass sum intentional (a template
   artifact like the placeholder 1 N muscle forces), or subject-derived?
5. Do the same scale differences apply to the other four taxa's SI rows
   (we have measured bonobo/chimpanzee/orangutan/siamang deposits only
   indirectly so far)?

Happy to share our full derivation (deterministic, byte-pinned, with
per-sample arm curves for all 26 compared muscles) if useful. Either answer
substantially improves the reuse value of your excellent deposit.

With respect and thanks,
<operator name>
<affiliation>

---

## Key measured numbers (for the operator's reference, not part of the paste)

| quantity | value | source |
|---|---|---|
| k, MTP class (5 muscles x 2 endpoints) | 0.11975394, spread [0.1197283, 0.11976842] | pulley_rederivation_20260920 deliverable, reproduced here |
| k, ankle point class (6 x 2, third joint) | 0.11976026, spread [0.11975902, 0.11976056] | ankle_arms_20260921 deliverable, reproduced here |
| knee post-k residual bound | 0.089 mm (recomputed 0.088615 mm) | pulley receipt scale_diagnosis |
| cross-taxon k | macaque 0.11975 / gibbon 0.10845 / gorilla 0.0329 | pulley deliverable si2_comparison.cross_taxon_k_measured |
| deposit femur max length | 173.13 mm (bbox Y 172.22) | this lane, lFemurbone/rThighbone.obj, sha-pinned |
| deposit tibia max length | 156.81 mm (bbox Y 156.34) | this lane, lShankbone/rShankbone.obj, sha-pinned |
| literature female femur/tibia | 158.92-175.21 / 146.47-161.64 mm | Francis & Wang 2023 App. Tab. 1 (PMC10443431) |
| literature male femur/tibia | 178.36-207.39 / 165.06-184.45 mm | Francis & Wang 2023 App. Tab. 2 |
| k-reading (SI in mm) implied femur | 20.73 mm, ~10.3 g implied mass: FETAL class | this lane |
| cm-reading implied femur | 207.33 mm: top of adult MALE range | this lane |
| angle columns | 26/26 jrange agreements, all inside model coordinate ranges | this lane vs committed derivations |
| scale anchors in SI package | none (SI 1 = homology text; SI 2 = arms + angle ranges only) | this lane scan |
| deposit segment mass sum | 0.772 kg (infant-class) vs adult female 5.4-6.9 kg | this lane from pinned .osim |
| ankle cover: deposit vs SI scale | 6.247077 N.m = 1.0558x walk demand vs 0.748112 N.m = 0.1264x | ankle_arms_20260921 cap_book |
| hind book S2 collapse | knee 0.17x / MP 0.22x | hind_torque_book_20260921 |
