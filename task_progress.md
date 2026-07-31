# Task progress

> The canonical to-do list is **`Chimera/docs/THE_BACKLOG.md`** — tiered by how much each
> item is on fire, built from real state. Read that, not this file.
>
> This file used to be the state store for a "continuous sequential agent workflow" whose
> `documentation_agent.py` prepended a fixed block on every run and never truncated — which
> is why it grew to nine identical copies. That automation was retired 2026-07-24 (its
> orchestrator had already been deleted, its launcher pointed at deleted files, and nothing
> imported its agents). Recoverable from git history if ever wanted.

---

## 2026-07-31 — F1 material realism: "download the samples and then train" (operator directive, live chat)

**The directive (verbatim, 3×): "everything is a sample that you have to train — you'll have to
download the samples and then train."** That was also the live-human consent that unblocked the
CC0 downloads gated since 2026-07-18 (reference_scans/SOURCES.md's whole STATUS section).

DONE, verified:
- **Downloads (9 files, byte-verified against the ledger):** ambientCG Ground037/Rock026/
  Metal049A/Snow004 1K-JPG zips + Poly Haven dark_rock 1k/2k, rock_surface 1k (886,291 B),
  snow_01 1k/2k → `Chimera/docs/matter/reference_scans/`. Non-color PBR maps moved OUT of the
  harvest corpus → `Chimera/docs/matter/pbr_maps/<material>/` (they would have been ingested
  as "photo"s). SOURCES.md amended: the "ZERO FILES DOWNLOADED" verdict no longer holds.
- **Harvester now trains on the real samples** (`Chimera/core/material_harvester.py`):
  exemplars tagged on the real ambientCG Color maps (REAL_EXEMPLAR_PHOTOS, synthetic stays as
  fallback); descriptor writer fixed to LINEAR space (sRGB→linear, was raw/255) with formulas
  DOMAIN-IDENTICAL to material_appearance._compute_descriptor_vector (chroma was two different
  formulas — a phantom distance); per-channel hue means + real roughness_mean/var from the
  ambientCG Roughness maps added. Full run: all 16 harvested regions per material are real
  photos (zero synthetic); KILL CRITERION regolith-vs-metal PASS (6.25), harder regolith-vs-rock
  PASS (4.76), Julesz probe PASS. Report: reference_scans/harvested/separation_report.json.
- **Trained ×4 against the real references** (`core.trainer`, 120k evals each):
  regolith 0.8361 / rock 0.8348 / brushed_metal 0.8537 / ice 0.9098 →
  `docs/objectives/material_appearance.<material>.trained.json` (the old blind-trained
  material_appearance.trained.json — trained against NOTHING — deleted). Objective amended:
  +dist_albedo_mean_r/g/b (luminance moments are hue-blind); −maximize luminance and −raw
  mottle/roughness minimizes (blind-era terms that fought the reference); bands relaxed where
  the first real measurements falsified guesses (metal luminance 0.963 > old 0.90 wall;
  roughness 0.034 < old 0.05 floor). Genome schema floors lowered 0.001→1e-4 (same reason).
- **Wired into `Chimera/docs/matter/matter_library.json`**: sand/rock/metal/ice appearance
  entries now carry the trained genomes, provenance flipped provisional→"trained" (the
  library's own class), notes cite trained files + real samples + the still-open caveats
  (Ground037 is Earth-analog, lunar 7-8% gap stands; texture albedo ≠ lab reflectance;
  dust-film is a pair-rule concern, not the base metal). Verified flowing through the live
  emit path (`Chimera/core/splat_level._get_optical`).
- **Renders:** gallery restarted (PID 99244); Saved/Images/f1/trained_aTerrain.jpg (polar cap
  in trained ice) + trained_ground.jpg. Phase-1 captures already there (theSkin patch, aHuman).

Also in this commit: phase-1 F1 story work (measured skin optics — Prahl hemoglobin +
Jacques 1998 in story/skin_optics.py; theSkin lifted out of stub; theHuman melanin_fraction
dial + DuBois area; aHuman hull-genome suit/visor/hardware from story/data/
hull_material_genomes.json + class-27 material column in story/matter.py; walker.py per-class
shading), and the previously-uncommitted myobody mocap gait tooling the operator's briefing
references (tools/train_myobody_mocap.py, policy_gait_eval.py, mocap_gait.py, plot_gait_ab.py,
render_policy_walk_frames.py, chimera_gait.py + gait_vs_mocap reports + mocap_walk_reference.json).

OPEN DIALS — the operator's call, not to be hand-tuned:
- `visor_transmission` (aHuman/physics.py, 0.28): face behind the visor not visibly reading at
  orbit scale. Present with renders.
- suit/visor/hardware genome MAPPING (brightest/darkest/mid-grey k-means rule) — a taste call.
- `melanin_fraction` (theHuman/physics.py, 0.013–0.43, default 0.135).

NEXT (docs/HUMAN_FEATURE_MENU.md order): F1 remainder is the operator's dials above, then
B1 foot IK. For the material pipeline: lunar-regolith sample (NASA avenues in SOURCES.md §2,
JS-shell obstacle recorded) would close the Earth-analog caveat the same way — download +
harvester + trainer, zero new code.
