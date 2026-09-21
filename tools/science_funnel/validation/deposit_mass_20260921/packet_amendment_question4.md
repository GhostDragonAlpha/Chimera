# Packet amendment — question 4 (deposit-mass-20260921)

APPEND-ONLY amendment to `tools/science_funnel/validation/k_forensics_20260921/author_email_packet.md`:
paste the lines below directly AFTER the existing question 4 ("Is the deposit's
0.772 kg segment-mass sum intentional ... or subject-derived?"). The packet file
itself is NOT edited; this lane's record is
`deposit_mass_book.json` (sha256 6779e5dc48c8ab93c29a0cd01852b6a4fa5a3f41aee90397525a58732cc0a8d6)
+ `receipt.json` in this directory.

---

## Paste section (measured, 2026-09-21)

  - Measured against the literature, the mass set is 1.29-2.15x LOW: adult
    female rhesus run 5.4-6.9 kg (Turnquist & Kessler 1989) and carry
    18.5-24% of body mass in the hindlimb chains ALONE (pelvis excluded:
    2 x 0.927/10.038 = 18.5% in the Oku/Ogihara CT-derived Japanese macaque
    model, Oku et al. 2021 Table 1; 20-24% by dissection, stated explicitly
    for M. fuscata and M. mulatta, Zihlman & Underwood 2013), i.e. an
    expected 0.997-1.656 kg against your 0.772 kg — and under anatomical
    fractions the set implies a 3.2-4.2 kg (immature-class) animal;
  - the set is also too structured to be a 1 N-style stamp (seven distinct
    per-body values, 5-7 decimal places) and matches no scaling we can form:
    neither k = 0.119754 nor k^3 turns any adult-female anatomical mass set
    into 0.772 kg (0.772/k would demand 6.44 kg of pelvis+hindlimbs in the
    source — more than the animal's whole body; 0.772/k^3, a 449 kg one);
  - and it cannot be a density reading of the deposited meshes themselves:
    thigh, shank and toes L-R masses are byte-equal, but foot_l = 28.383 g
    vs foot_r = 2.605 g (10.9x, with foot_r within 0.7 mg of R_Hallux),
    while the femur/tibia meshes are exact mirror copies — if you can name
    the mass set's source (template, density convention, scaling input), our
    question 4 is answered.

---

## Operator reference (not part of the paste)

| quantity | value | source |
|---|---|---|
| parsed sum, 10 bodies | 0.7717839 kg (reproduces the packet's 0.772 to 0.0002161 kg) | this lane, Macaque_model.osim (manifest sha d5c65cbc...), deposit_mass_book.json |
| pelvis share | 0.37876 kg = 49.08% of the sum | this lane |
| expected envelope | 0.99737-1.656 kg (pelvis conservatively 0) | Oku 2021 Table 1 (PMC7940622) + Zihlman & Underwood 2013 (PMC3804282) x Turnquist & Kessler 1989 band |
| deficit factor | 1.291930-2.145078x (rises if pelvis > 0) | this lane |
| implied body at anatomical fractions | 3.215766-4.178626 kg (immature class) | this lane |
| foot asymmetry | foot_l 0.028383 / foot_r 0.0026046 = 10.897259x; foot_r - R_Hallux = 0.0000007 kg | this lane |
| scale tests | expected x k = 0.119439-0.198313 kg; expected x k^3 = 0.001713-0.002844 kg — neither closes | this lane, k = 0.11975394 (committed k-lane deliverable) |
| cross-taxon pelvis+hindlimbs totals | Bonobo 6.603 / Chimp 31.933 / Gibbon 0.173 / Gorilla 4.086 / Macaque 0.772 / Orangutan 4.771 / Siamang 1.913 kg | this lane, all 7 pinned .osim |
