# DERIVATION — assembly_handoff (Rule 0)

## STATEMENT

An assembly is dynamics-ready **if and only if** three things hold in the authored record:

1. every mass-bearing component has exactly one matter representation bound to it, and that
   representation is a reconstructed tetrahedral volume whose density carries a declared source;
2. every frame an authored quantity is expressed in binds through a single authored root, with no
   cycle and an orthonormal basis;
3. every anatomical port is covered by an attachment whose authored anchor set, weights, patch
   area and stiffness pass the finite-area couple-stiffness gate owned by
   `tools/finite_area_attachment/`.

Equivalently: **readiness is a property of what was explicitly authored, never of what could be
inferred.** The adapter's job is to answer "is this ready, and exactly what is missing?" without
ever becoming the thing that supplies the missing part.

The corollaries that do the real work are prohibitions, and they are the falsifiable content:

* transported source-effective anatomy mass can never become validated tissue mass;
* a tendon waypoint can never become a membrane attachment patch by geometric proximity;
* absent patch area, stiffness, material or frame information stays absent in the output;
* one piece of matter can never be counted toward the mass of two components.

## PREDICTION

Run against the anatomy the compiler actually produced (`.tmp/anatomy_compiler/runs/`), with the
three inputs a dynamics trial still needs declared absent rather than substituted, the adapter will
report `dynamics_trial_ready = false`, and every blocking record will name an author who is not
this adapter: three absent documents, nine anatomy physiology bodies whose matter has no owner,
eight anatomical ports with no qualified attachment, and one frame tree with no authored root.

Run against a complete synthetic bundle in which those same four things *are* authored, it will
report ready — so the negative result above is about the packet's actual gaps, not about an
adapter that always says no.

## FALSIFIER (named before the run)

Any one of these refutes the theory:

* **F1** any manifest reports `dynamics_trial_ready = true` while a required field on which
  readiness depends is null;
* **F2** the real anatomy packet reaches `dynamics_trial_ready = true`;
* **F3** a component carries `validated_tissue_mass = true` on the strength of a claim whose
  density has no declared source, or on the strength of a transported anatomy record;
* **F4** a candidate with geometric status `waypoint_not_a_port` is reported as covered by a
  qualified attachment without an authored endpoint role making that so;
* **F5** two representations of the same matter both count toward component mass, or one claim's
  matter counts toward two components;
* **F6** any value present in a manifest was produced by a default rather than authored —
  including a default reached *through a dependency*;
* **F7** two manifests built from byte-identical inputs differ.

## Result of the run (measured)

F1–F5 and F7 held after fixes; **F6 and F3 each caught a live defect**, which is recorded in
`agent_logs/local_buffy_qwen/assembly_handoff_01.md` rather than quietly repaired:

* **F6 — silent default reached through a dependency.** `AttachmentSpec(stiffness=None)` defaults
  to a scalar 1 N/m. An attachment that authored no `stiffness_kbar` would have been qualified
  against that number. Now: authored → used; absent but κ_areal and patch area present → derived
  as κ·A with the derivation recorded in `stiffness_kbar_source` and a note-level gap; both absent
  → listed in `missing_fields`. No route to the dependency's default remains.
* **F3 — validation without a source.** A material region whose `density_source` was missing still
  received status `reconstructed_tissue_volume`, so its component read
  `validated_tissue_mass = true` while the manifest simultaneously carried a record saying the
  mass "is reported but never validated". Added status `reconstructed_volume_density_unsourced`;
  only a sourced reconstruction validates. (Upstream `material_volume.compile_document()` already
  refuses an empty or whitespace source, so this guard is defence in depth — stated as such rather
  than claimed as the active path.)
* **F5/F7-adjacent — silent winner between two documents.** Several inputs claiming one role were
  resolved by keeping the first. That silently decided which authored information counted, and it
  was found only by probing, not by the fixtures. Now refused outright (`duplicate_role_input`).

Manifest digests are byte-identical when the whole tree is relocated to a different filesystem
root — verified over all ten outputs — because manifest paths are recorded relative to the repo
root rather than as absolute host paths. Before that fix the digest covered `E:\PythonChimera\...`,
so two agents on two machines would have reported different digests for identical inputs, which
would have made "stable hashes" a claim about the machine rather than the assembly.

## Why there is no sweep here (Rule 1)

The adapter has no tunable parameter and performs no fit: it reads authored documents, delegates
mass to `material_volume.compile_document()` and qualification to
`AttachmentSpec.assert_min_couple_stiffness()`, and records what is missing. Every number in the
fixtures is derived from an arithmetic relation stated in
[`fixtures/parts/PROVENANCE.md`](fixtures/parts/PROVENANCE.md) before the run — 1 kg total mass is
`2·(1/6) + 4·(1/6)`, not a value adjusted until the fixture passed. There is nothing to sweep, and
the absence of a sweep is the point: readiness was derived from the authored record, not chosen.
