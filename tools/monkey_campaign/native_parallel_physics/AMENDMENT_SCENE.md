# Scene placement amendment for the rebased base, 2026-10-02 UTC

The first sealed run at base `b9dfdd17` (job `f6cb105de21f4ce395bc9f23a7073347`)
failed in `controls_baseline` with `coupled_contact_initial_penetration`. Root
cause: master's seven engine commits added an authored contact plane
(`contact_plane_height_m` 0.35 m world Up, `proxy_radius_m` 0.007) and an
unconditional constructor probe requiring a strictly positive reset gap. This
suite's `dynamics_controls.cpp` passed shift `V{}` (model origin), where the
reset hand gap is -0.457224 m: the probe refuses. The pre-rebase base
(7222729e) had no plane, so the zero shift passed there. Physics source, test
thresholds and tolerances are unchanged.

Adopted fix, following master's own qualified convention
(`tests_coupled_arm/native.cpp` reads `scene.at("scene").at("arm_translation_m")`):

- `scene_fixture.json` gains a top-level `scene.arm_translation_m = [0.0, 0.55, 0.0]`,
  copied from the pinned graph object `model.environment.earth_patch`
  `physical.contract.arm_translation_m` at base `b9dfdd17` (the qualified
  placement master's own gates use with this plane).
- `dynamics_controls.cpp` reads that placement and passes it to every
  `CoupledDynamics` construction (previously `V{}`).
- A second sealed run (job `7cf4b75a1df94b758685213f03bdd8fc`) then passed all
  four controls configurations and failed the same way in `baseline.exe`:
  `native_probe.cpp` `run_trajectory` also constructs `CoupledDynamics` (two
  sites), so it reads the same placement now. No other driver constructs
  `CoupledDynamics`; the probe/batch/executor binaries evaluate the `Model`
  directly and never touch the plane.
- `INPUTS.json` re-pins `scene_fixture_sha256` accordingly.
- Recipe/model continue to be asserted byte-equal to the pinned graph objects;
  only the world placement of the mounted arm changed.

Analytic reset gap at the adopted placement: hand model-space Up -0.114224 m,
world gap = -0.114224 + 0.55 + 0.007 - 0.35 = +0.092776 m > 1e-6 (probe passes
with margin). At zero shift it is -0.457224 m (the observed refusal).

Prediction and falsifiers remain the original preregistration and the MSVC/BATCH
amendments: exact within-backend byte parity serial vs 1/2/4 workers, retained
analytic/reference/control checks, deterministic executor behavior, bounded
energy residuals, refinement ratio within [12, 20]. A uniform world translation
is a rigid offset; it does not alter trajectory convergence differences, energy
accounting residuals, or the byte-parity comparison (all runs use the same
scene). No contact-qualified claim is added: the suite keeps
`contact_enabled` false by default.
