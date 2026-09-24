# R1 — CITATION RECEIPT (receipts = citation list + arithmetic)

Statuses: APPLICABLE (measures a quantity transformable into the common definition D) / INAPPLICABLE (measures a different quantity; kept with the explicit finding, never forced).

## A. APPLICABLE primary sources (human = the Chimanoid's base anatomy; n = 3)

**S1.** London JT. "Kinematics of the elbow." *J Bone Joint Surg Am* 1981;63(4):529–535. PMID 7217119.
- Measured: 8 normal elbows (4 cadaveric, 4 living subjects), true lateral roentgenograms, special technique. Finding: flexion occurs about a **single axis through the centers of the arcs of the trochlear sulcus and the capitellar periphery**; carrying angle constant during flexion; surface motion sliding except at motion extremes.
- Relevance: the humeroulnar (trochlear) and humeroradial (capitellar) articular surfaces are **coaxial** — the radius, articulating with the capitellum and rotating with the forearm about this axis, has its center at the elbow-joint level. Transformable: axial offset of the radial head from the humeroulnar hinge ≈ 0 (technique error mm-scale ⇒ ≈ 0 % ± ~1 % of forearm length). Uncertainty: axis-location technique error is millimeter-scale (paper-level; exact per-specimen errors in full text, not in the abstract).
- Variance reported in abstract: none (n = 8 elbows stated).

**S2.** Brownhill JR, Ferreira LM, Pichora JE, Johnson JA, King GJ. "Defining the flexion-extension axis of the ulna: implications for intra-operative elbow alignment." *J Biomech Eng* 2009;131(2):021005. DOI 10.1115/1.3005203. PMID 19102564.
- Measured: 12 cadaveric specimens; 5 ulnar flexion-axis determination techniques (3 kinematic, 2 anatomic) compared against the screw displacement axis of simulated elbow flexion. Finding: the anatomic technique using **the guiding ridge of the greater sigmoid notch of the ulna and the radial head** most accurately replicated the screw displacement axis (p < 0.05).
- Relevance: the radial head is a DEFINING landmark of the elbow flexion-extension axis together with the humeroulnar (greater sigmoid notch) surface ⇒ radial head center lies on the hinge axis ⇒ axial offset ≈ 0. Transformable: same as S1, independent specimen set (n = 12).
- Variance reported in abstract: p < 0.05 for technique comparison; per-technique mm errors are in the full text (not in the abstract).

**S3.** Hollister AM, Gellman H, Waters RL. "The relationship of the interosseous membrane to the axis of rotation of the forearm." *Clin Orthop Relat Res* 1994;(298):272–276. PMID 8118987.
- Measured: fresh anatomic specimen forearms with a mechanical "axis finder". Finding: the forearm rotation axis is **constant and independent of elbow flexion/extension; it runs from the center of the radial head to the center of the distal ulna**; interosseous membrane fibers cross the axis near their distal insertions.
- Relevance: the radial head center IS the proximal terminus of the forearm's longitudinal axis — i.e., the forearm segment BEGINS at the radial head; there is no positive fraction of forearm length between the elbow joint and the radial head along that axis. Transformable: proximal-anchor fraction ≡ 0 by axis construction (fresh specimens; no variance given in abstract).

## B. INAPPLICABLE primary sources (explicit findings — searched, evaluated, not forced)

**I1.** Cheng EJ, Scott SH. "Morphometry of Macaca mulatta forelimb. I. Shoulder and elbow muscles and segment inertial parameters." *J Morphol* 2000;245(3):206–224. (n = 6 *M. mulatta* + 3 *M. fascicularis*).
- Measures: muscle architectural parameters (L0M, LST, PCSA, pennation, mass) and segment inertial parameters. **No radial-head position, no forearm proportion transformable into D.** INAPPLICABLE. (Nearest-taxon = campaign-target family; recorded because it is the closest primary morphometry the search located for Macaca.)

**I2.** Graham KM, Scott SH. "Morphometry of Macaca mulatta forelimb. III. Moment arm of shoulder and elbow muscles." *J Morphol* 2003;255(3):301–314.
- Measures: moment arms of 14 muscles vs joint angle. Different quantity; INAPPLICABLE. (Series part II = Singh et al. 2002, J Morphol 251:323–332, distal forelimb — same series, same finding.)

**I3.** Rose MD. "Another look at the anthropoid elbow." *J Hum Evol* 1988 (17:193–224) — comparative elbow morphology lane (name-target taxon Pan). Located but paywalled; no transformable NUMBER extracted. Qualitative primary morphology only ⇒ INAPPLICABLE for the numeric comparison (recorded, not cited as a number — the architect's bar forbids "a citation mentioning a similar percentage").

**I4.** Kim M, Lee Y. "FreeMusco: Motion-Free Learning of Latent Control for Morphology-Adaptive Locomotion in Musculoskeletal Characters." arXiv:2511.14205 (2025), SIGGRAPH Asia 2025. — PROVENANCE source (species determination), not anatomical evidence.

**I5.** Radial-tuberosity–distance search (15 PMIDs screened, e.g. "The Radioulnar Distance at the Level of the Radial Tuberosity" Clin Anat 2020, PMID 31576589): measures interosseous space / nerve-safe-zone distances, **not** tuberosity-to-elbow position ⇒ INAPPLICABLE. Consequence: the model's biceps-tuberosity site fraction (8.02 %) is compared only qualitatively against the proximal-forearm tuberosity band (no primary number claimed for it in this audit).

## C. The common definition D (stated once, used everywhere)

**D (proximal radioulnar offset fraction)** ≡ axial distance from the humeroulnar elbow hinge to the radius's proximal anchor, divided by the elbow→wrist straight-line distance, in the authored/authored-equivalent rest pose. Sub-variants: D_axial (projection on the forearm axis — the definition under which the re-anchored target anchor is placed and the claim is worded) and D_total (full 3D offset distance). All model-side numbers are exact authored floats; all primary-side numbers are mm-scale measurements over ~240–260 mm human forearms ⇒ ≈ 0 % ± ~1 %.
