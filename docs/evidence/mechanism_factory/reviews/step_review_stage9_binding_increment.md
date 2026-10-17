# Step review: stage 9 binding increment

S1 CONFIRMED. Imports: `composed_chain.build_star`, `membrane_scale_lab.fixture_generator.high_degree_fan`, `surface_energy_reference.evaluate_surface`. No new physics; only rigid scaling `V = V * scale` (native_binding.py:242, composed_chain.py:182).

S2 CONFIRMED. (a) Tampered transaction with recomputed hash: `apply_transaction` refused `binding_transaction_stale` via re-derivation. (b) Drifted record port_id after world built: `restore_world` refused `binding_restore_mismatch`. (c) All refusals leave caller bytes byte-identical. Battery: 5/5 W1-W5 green, exit 0.

S3 CONFIRMED. Star valid_scales: [0.75, 1.0, 1.5, 2.0] — lacks 0.5x. Piece valid_scales: [0.5, 0.75, 1.0, 2.0] — lacks 1.5x. Asymmetric by record, not code.

S4 CONFIRMED. `_ids_for_star` refused swapped node_id (`binding_recipe_unmatched`). Port-to-hanger binding refused mismatched port_id (`binding_port_ambiguous`). IDs are re-derived from recipe + compile path stacking.

S5 CONFIRMED with caveat. Git status shows only the two target files as new untracked; no engine or existing-owner modifications. Note: unrelated untracked `old_patch_equilibrium.py` present in workspace, outside target scope. Render-binding gap recorded as `physical_to_render: "unset"` in both records.
