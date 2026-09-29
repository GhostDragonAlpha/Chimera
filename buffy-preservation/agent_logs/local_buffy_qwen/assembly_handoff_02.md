# LOCAL-BUFFY-QWEN — assembly_handoff_02

**Assignment (Astra's replacement directive).** Make the real anatomy packet evaluable *without
substitutions* while keeping `dynamics_trial_ready = false` whenever evidence is genuinely missing.
Produce the three/four missing input documents at `tools/assembly_handoff/inputs/`, bind the nine
anatomy matter claims, connect the anatomical ports as far as existing evidence allows, implement
explicit root-frame handling, then integrate and rerun the real-packet example with a before/after
blocker list.

**Status: complete.** The producer module that was left non-executable now runs; all four artifacts
are written; ownership is integrated into readiness; the real packet is rerun with a measured
before/after. `dynamics_trial_ready` stays **false**. Nothing was substituted to make it pass, and
both falsifiers hold (see §6).

This session resumed from `assembly_handoff_01.md` and the mid-implementation handoff. It fixed the
interrupted producer, wired its output into readiness, and verified the after-state against the
numbers the handoff preregistered.

---

## Changed files

All inside owned paths (`tools/assembly_handoff/`, `agent_logs/local_buffy_qwen/`). No upstream file
was edited; no framework/GUI/training/production wiring added.

| Path | State | What it is |
|---|---|---|
| [`tools/assembly_handoff/produce_inputs.py`](../tools/assembly_handoff/produce_inputs.py) | **new** (this session) | producer for the four input documents; reads the same authoritative packets the adapter does |
| [`tools/assembly_handoff/real_packet_readiness.py`](../tools/assembly_handoff/real_packet_readiness.py) | edited (+31 lines) | admits `ownership_bindings.json` present; keeps material-volume + mechanical absent; adds `producer_evidence` |
| [`agent_logs/local_buffy_qwen/assembly_handoff_02.md`](./assembly_handoff_02.md) | **new** | this report |
| [`tools/assembly_handoff/inputs/ownership_bindings.json`](../tools/assembly_handoff/inputs/ownership_bindings.json) | generated (9 components / 9 claims) | authored ownership binding — the item to produce first |
| [`tools/assembly_handoff/inputs/material_volume_document.cannot_produce.json`](../tools/assembly_handoff/inputs/material_volume_document.cannot_produce.json) | generated | records exactly why a reconstructed-volume document is not authorable |
| [`tools/assembly_handoff/inputs/mechanical_requirements.cannot_produce.json`](../tools/assembly_handoff/inputs/mechanical_requirements.cannot_produce.json) | generated | records exactly what each of the 8 ports is missing |
| [`tools/assembly_handoff/inputs/prepared_root_frame_definition.json`](../tools/assembly_handoff/inputs/prepared_root_frame_definition.json) | generated | the exact root-frame definition Astra must author; never silently authored |

The adapter (`assembly_handoff.py`), fixture suite (`run_fixtures.py`), fixtures/parts, and
`DERIVATION.md` were **not** changed this session. The four required fixtures still all pass (see
§7). `tools/material_volume.py` and `tools/finite_area_attachment/` were not touched.

---

## Fix: the producer was left non-executable

The mid-implementation handoff reported a syntax error from an interrupted edit:
`produce_root_frame_definition()`'s `each_value_needs_astra` dict was left open with no closing
brace and no `return`, so the module would not import or run, and nothing could be generated. Two
more things were lost in that same interruption:

* `TOOLS_PREFIX` was referenced by every producer's `"producer"` provenance string but never
  defined → `NameError` at runtime once the syntax error was fixed.
* `main()` never called `produce_root_frame_definition()`, so `prepared_root_frame_definition.json`
  was built-but-never-written even though the report (`assembly_handoff_01.md`) and the plan both
  reference it.

Fixes applied:

1. Completed `each_value_needs_astra` — one entry per value in
   `frame_definition_requires_astra` (`parent_frame_id=null`, `coordinate_unit`, `handedness`,
   `scale_to_m`, `origin_m`, `basis_rows`), each with a "why it needs Astra" string; closed the dict
   and the function's return.
2. Defined `TOOLS_PREFIX = "tools/assembly_handoff/"` — repo-relative POSIX, matching the adapter's
   own `TOOL_NAME` and the relocation-reproducibility invariant from `assembly_handoff_01.md` (a
   producer provenance string is a property of the assembly, not the machine).
3. Wired `produce_root_frame_definition()` into `main()` so the fourth artifact is written.
4. Enhanced it to record `disconnected_component_roots` — the full set of referenced-but-not-self-
   declared parents — so the artifact self-explains why there is no single natural root (see §5).

```
python tools/assembly_handoff/produce_inputs.py        → exit 0, all four artifacts written
```

---

## New producers and supported bindings

`produce_inputs.py` emits exactly what can be authored from the authoritative packets without
inventing physics:

* **`ownership_bindings.json`** — AUTHORABLE NOW. Binds all nine physiology bodies to components
  (`seg-pelvis`, `seg-femur_r/l`, `seg-tibia_r/l`, `seg-humerus/humerus_l`, `seg-radius/radius_l`).
  Every claim is bound with `counts_toward_component_mass: false` and `assert_mass_status` taken
  from the adapter's own rule (`derive_mass_status`): `pelvis → root_reference_frame_only`, the other
  eight → `transported_source_effective`. The reported **17.039978509953905 kg** is declared owned
  but never counted, and never relabelled into validated tissue mass. Components declare no
  `local_frame_id` on purpose (no authored frame tree exists).

  sha256 `6711671030b914af…d4a0`, 5895 B. Histogram `{root_reference_frame_only: 1, transported_source_effective: 8}`.

* **`material_volume_document.cannot_produce.json`** — CANNOT be produced honestly. Segments carry
  only bounding-box `scale`, `fitted_origin`, `frame_basis`; no tetrahedral/vertex geometry and no
  declared `density_source`. Names the missing inputs at field paths instead of fabricating them.

* **`mechanical_requirements.cannot_produce.json`** — CANNOT be produced honestly. Candidates carry
  a resolved `source_pos_local` but no `patch_area_m2`, areal stiffness, minimum couple stiffness or
  weights; and the segment tree declares no authored root frame. Records exactly what each of the 8
  ports is missing.

* **`prepared_root_frame_definition.json`** — `requires_astra_authorship`. Records precisely what the
  root frame(s) must declare, consuming the packet's own coordinate conventions as evidence only
  (never deriving a pose from them). Never silently inserts an identity transform or infers
  alignment.

None of these is admitted by readiness as an authored *input* except `ownership_bindings.json`
(which is required and authorable). The three evidence artifacts are hashed into the report's
`producer_evidence` section and linked into `missing_dependencies`, but they never become a present
`ROLE_MATERIAL_VOLUME` / `ROLE_REQUIREMENTS` input — doing so would make readiness think a required
document exists when it does not.

---

## Port qualification status

The eight anatomical ports are **not** mechanically qualified, and this session did not change that:

* Evidence (`.tmp/anatomy_compiler/runs/attachment_candidates.json`, rev 5, sha256 `854f7097…`):
  8 ports — `radius`/`radius_l`: BIClong-P11, BICshort-P8, BRD-P3, PT-P5 — all with
  `mechanical_qualification: false`, 32 candidates total. The adapter reports exactly 8
  `candidate_port` + 24 `waypoint_not_a_port`.
* No authored mechanical-requirements document exists (left absent on purpose), so nothing can call
  a port qualified. `produce_mechanical_requirements_report()` records, per port, the missing
  parameters (`patch_area_m2`, `kappa_areal_n_m3`, `k_couple_min_n_m_per_rad`, `weights`,
  `anchor_frame_id`, `endpoints[*].local_frame_id`).

No stiffness, patch area, material or frame information was invented. Unsupported ports stay
explicitly unqualified.

---

## Root-frame status

**Not authorably established — recorded as a prepared definition requiring Astra.** Verified against
the real packet bytes:

* 9 segments; **none declares `parent_frame_id null`**; `pelvis` is referenced as a parent but is
  not itself a segment. So no authored transform places any frame at an assembly root.
* The segment tree is a **forest of four disconnected components** whose roots are referenced but
  never self-declared: `disconnected_component_roots = [pelvis, thorax, ulna, ulna_l]`. (`humerus`/
  `humerus_l → "thorax"`; `radius`/`radius_l → "ulna"/"ulna_l`; `femur_r/l` + `thorax_dummy → pelvis`.)
* `_natural_root()` therefore correctly returns `None` — there is no single unambiguous root, so the
  artifact does not pretend pelvis alone is it.

`prepared_root_frame_definition.json` records what the root frame must declare (`frame_id`,
`parent_frame_id=null`, `coordinate_unit`, `handedness`, `scale_to_m`, `origin_m`, `basis_rows`) with
each value annotated for why it needs Astra, and consumes only the packet's own conventions as
evidence (`meta.units = "SI (m, kg, s)"`, handedness `right`, axis vectors from
`coordinate_conventions`). No identity transform is inserted; no alignment is inferred.

---

## Real-packet before / after blocker list

Same adapter, same two present packets, same hashing. Only change: `ownership_bindings.json` is now
admitted **present**; material-volume and mechanical-requirements stay declared absent.

**BEFORE** — manifest digest `afd4cb9fffd18e8d4eb38dd68b225b5562df8dfbbf8f677c32037651972c6a86`

| code | count |
|---|---|
| attachment_port_unqualified | 8 |
| required_input_absent | 3 (material_volume, ownership, requirements) |
| root_frame_ambiguous | 1 |
| unbound_matter_claim | 9 |
| frame_observed_not_bound *(note)* | 3 |

**AFTER** — manifest digest `504deec6f4671b419fab7fe182a0332067573dbf86df0d42266625494758d880`

| code | count | delta |
|---|---|---|
| attachment_port_unqualified | 8 | — |
| required_input_absent | 2 (material_volume, requirements) | ownership **resolved** |
| unbound_matter_claim | 0 | 9 → **0** (all claims now bound) |
| component_frame_missing | 9 | NEW — honest: components declare no authored frame |
| component_mass_undecided | 9 | NEW — honest: components carry no counted/validated mass |
| root_frame_ambiguous | 1 | — |
| frame_observed_not_bound *(note)* | 3 | — |

`dynamics_trial_ready = **False**`. The two new codes are the honest consequence of binding matter
to explicitly-declared components that still have no authored frame or counted mass; they were
anticipated by the handoff as an observed finding, not a regression. Net unresolved records rise
(24 → 32) because matter is now owned and declared with honest status rather than left unbound —
readability improves while readiness stays false on the same two still-absent required documents.

Mass ledger (measured, not asserted): `claims_known=9`, `bound_to_component=9`, `counting_toward_mass=0`,
`validated_tissue_volume=0`, `counted_mass_kg=0.0`, `uncounted_mass_kg=17.039978509953905`,
histogram `{root_reference_frame_only: 1, transported_source_effective: 8}`. The reported transported
+ root-reference mass is **not** promoted; 0 matter counts without an owner.

`missing_dependencies` now carries a `supporting_evidence` link from each still-absent role to its
`.cannot_produce.json`:

* `[material_volume_document]` → `tools/assembly_handoff/inputs/material_volume_document.cannot_produce.json`
* `[mechanical_requirements]` → `tools/assembly_handoff/inputs/mechanical_requirements.cannot_produce.json`

---

## Actual `dynamics_trial_ready` result

**False.** Exit 0 (report produced); exit-3 soundness path not taken. The real packet still lacks a
reconstructed material-volume document and an authored mechanical-requirements document, so it can
never be ready until those are supplied by their authoritative owners.

---

## Falsifiers (§6 of the preregistered plan) — both hold

* **Falsifier A (transported → validated invariant).** If any claim read `validated_tissue_mass=true`,
  the reported mass would have been promoted through relabeling. Measured:
  `transported_source_effective_mass_promoted_to_validated_tissue = False`,
  `matter_counted_without_an_owner = 0`, `validated_tissue_mass_claims = 0`,
  `components_with_validated_tissue_mass = 0`. Invariant intact — the 17.04 kg stays transported.
* **Falsifier B (readiness).** If `dynamics_trial_ready` had flipped true, a readiness rule would
  have been lost. Measured: `dynamics_trial_ready = False`, `soundness_violation = None`.

Also measured and unchanged: `densities_inferred_by_this_adapter = False`, `meshes_repaired = False`,
`silent_defaults_used = False`, `tendon_waypoint_promoted_to_membrane_attachment = False`,
`dynamics_executed = False`.

---

## Regressions / full battery (§7)

```
python tools/assembly_handoff/run_fixtures.py                 → exit 0, all fixtures + controls pass
python tools/assembly_handoff/real_packet_readiness.py        → exit 0, ready=false (expected)
python tools/assembly_handoff/produce_inputs.py               → exit 0, four artifacts written
```

The four required fixtures still map one-for-one to the requirements: complete passes; duplicate
mass ownership is **refused** (no manifest emitted); unresolved anatomy mass **blocks** readiness; a
geometric waypoint without mechanical parameters stays **incomplete**. The duplicate-role refusal,
density-source invariant, and relocation-reproducibility fix are preserved.

---

## Smallest remaining Astra decisions

Three, each with the exact artifact that names what must be supplied:

1. **Material volume** — supply a reconstructed `tools/material_volume.py` v1 partition whose regions
   carry declared tetrahedral geometry **and** a declared `density_source`. This is the only thing
   that turns this packet's bounding-box geometry into validated tissue mass and inertia.
   (Evidence: `tools/assembly_handoff/inputs/material_volume_document.cannot_produce.json`.)
2. **Mechanical requirements** — supply the assembly frame tree plus, per attachment, anchors,
   weights, `patch_area_m2`, `kappa_areal_n_m3`, `k_couple_min_n_m_per_rad`. Without it all 8 ports
   stay unqualified. (Evidence: `tools/assembly_handoff/inputs/mechanical_requirements.cannot_produce.json`.)
3. **Root frame** — decide which of the four disconnected component roots is THE assembly root and
   author its transform (`parent_frame_id=null`, `origin_m`, `basis_rows`, `scale_to_m`,
   `coordinate_unit`, `handedness`). Until then every quantity in both packets is unplaced.
   (Definition: `tools/assembly_handoff/inputs/prepared_root_frame_definition.json`.)

No new anatomical mappings, schema changes, mechanical assumptions, or runtime dynamics wiring were
made — all three above require Astra's decision and are left explicitly open.

---

## Preserved failures / superseded digests

From `assembly_handoff_01.md`, kept intact: the digest-drift correction (recorded digests must be
re-measured, not carried forward), the `root_frame_ambiguous` fourth-gap finding, and the four
adversarially-found defects promoted into permanent fixtures (silent winner between same-role
documents → `duplicate_role_input`; unsourced-density self-contradiction → defence-in-depth guard;
manifest digest covering absolute host paths → `display_path()` repo-relative). The real-packet
digest is re-measured this session: superseded `afd4cb9f…` (ownership absent) by `504deec6…`
(ownership present); both are honest, byte-stable, and machine-independent.
