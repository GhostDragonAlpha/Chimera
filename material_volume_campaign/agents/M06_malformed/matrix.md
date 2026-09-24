# M06 malformed-case matrix (FROZEN before execution)

Baseline: two-body coupon, verified green pre-freeze (admission exit 0
validation_only_admissible; export exit 0 complete, 2.0 kg + 1.0 kg).

Total cases: 62.  Expected verdict per run: NAMED-REFUSAL (named reason +
nonzero exit; admission exit 2 refused / 1 not_admitted per its doc) except E01, which
expects the DOCUMENTED 'unsupported' non-export (no mass emitted).

| id | category | mutation | expected refusal (tool: adm=admission CLI, exp=body-export CLI) | expected exit | doc anchor |
|---|---|---|---|---|---|
| A01 | invalid_frame | groups rotation scaled x2: orthonormality violated, det=+8 | exp: invalid_authored_frame | nonzero | body_export doc: 'R must already be finite, orthonormal, and proper (det R = +1); it is not normalized or repaired.' |
| A02 | invalid_frame | groups rotation with det=-1 (reflected, wrong handedness transform) | exp: invalid_authored_frame | nonzero | schema rotation3: 'Must be a proper orthonormal rotation (R^T R=I, det R=+1)' |
| A03 | invalid_frame | groups body_frame.handedness = 'left' (declared wrong handedness) | exp: unsupported_authored_frame | nonzero | schema bodyFrame.handedness const 'right'; exporter: 'body frames must be right-handed' |
| A04 | invalid_frame | groups body_frame.coordinate_unit = 'mm' (schema const 'm') | exp: unsupported_authored_frame | nonzero | body_export doc: authored frame supplies 'coordinate_unit: m' |
| A05 | invalid_frame | manifest+partition coordinate_frame.handedness = 'left' | adm: unsupported_coordinate_frame; exp: unsupported_coordinate_frame | 2; nonzero | admission doc: 'Non-right-handed frames, reflections ... [unsupported]'; schema const 'right' |
| A06 | invalid_frame | manifest+partition coordinate_frame.scale_to_m = -1.0 (schema exclusiveMinimum 0) | adm: bad_scale; exp: bad_scale | 2; nonzero | admission doc: 'positive finite scale_to_m'; schema exclusiveMinimum 0 |
| A07 | invalid_frame | groups rotation given as 2x2 (bad shape) | exp: bad_shape | nonzero | schema rotation3 minItems/maxItems 3 |
| A08 | invalid_frame | groups rotation = zero matrix (singular, not a rotation) | exp: invalid_authored_frame | nonzero | body_export doc: 'R must already be finite, orthonormal, and proper (det R = +1)' |
| B01 | missing_field | groups: body_groups[0] missing required 'body_frame' | exp: bad_schema | nonzero | schema bodyGroup required [body_id, cell_ids, body_frame] |
| B02 | missing_field | groups: body_frame missing required 'domain_from_body' | exp: bad_schema | nonzero | schema bodyFrame required [... 'domain_from_body'] |
| B03 | missing_field | groups: root missing required 'schema_version' | exp: bad_schema | nonzero | schema root required ['schema_version', 'body_groups'] |
| B04 | missing_field | groups: body_groups[0] missing required 'cell_ids' | exp: bad_schema | nonzero | schema bodyGroup required |
| B05 | missing_field | groups: cell_ids = [] (schema minItems 1) | exp: empty_body_group | nonzero | body_export doc: 'a non-empty list of stable cell_ids' |
| B06 | missing_field | groups: body_frame missing required 'handedness' | exp: bad_schema | nonzero | schema bodyFrame required |
| B07 | missing_field | groups: domain_from_body missing required 'origin_m' | exp: bad_schema | nonzero | schema domain_from_body required ['rotation', 'origin_m'] |
| B08 | missing_field | partition: missing required 'materials' array | adm: bad_schema; exp: bad_schema | 2; nonzero | schema materialPartition required includes 'materials' |
| B09 | missing_field | manifest: missing required 'mass_authority' | adm: bad_schema; exp: bad_schema | 2; nonzero | admission doc: 'Required explicit choice ... There is no inferred or combined authority.' |
| B10 | missing_field | manifest: missing required 'matter_ownership' | adm: bad_schema; exp: bad_schema | 2; nonzero | schema fittingManifest required includes 'matter_ownership' |
| B11 | missing_field | partition: coordinate_frame missing required 'scale_to_m' | adm: bad_schema; exp: bad_schema | 2; nonzero | schema coordinateFrame required includes 'scale_to_m' |
| B12 | missing_field | partition: vertex row missing required 'position' | adm: bad_schema; exp: bad_schema | 2; nonzero | schema vertex required ['vertex_id', 'position'] |
| B13 | missing_field | manifest: missing required 'source_effective_segment_ids' | adm: bad_schema; exp: bad_schema | 2; nonzero | schema fittingManifest required includes 'source_effective_segment_ids' |
| B14 | missing_field | partition: missing required 'cells' array | adm: bad_schema; exp: unknown_group_cell_id | 2; nonzero | schema materialPartition required includes 'cells'; exporter refuses group cells absent from partition |
| C01 | nonfinite | partition vertex position coordinate = 1e400 (parses to float inf) | adm: nonfinite_input; exp: nonfinite_input | 2; nonzero | admission doc: 'three finite coordinates'; runtime _number refuses non-finite |
| C02 | nonfinite | partition density as literal NaN JSON token (rejected by the JSON reader) | adm: input_read_error; exp: input_read_error | 2; nonzero | admission doc: report serialization 'allow_nan=False'; readers reject nonstandard constants |
| C03 | nonfinite | groups origin_m containing literal Infinity JSON token | exp: input_read_error | nonzero | body_export doc: 'R must already be finite'; output has 'no non-finite numbers' |
| C04 | nonfinite | partition density_kg_m3 = 1e400 (float inf) | adm: nonfinite_input; exp: nonfinite_input | 2; nonzero | admission doc: material records carry density; compiler: 'density must be finite and positive' |
| C05 | nonfinite | groups rotation entry = 1e400 (float inf) | exp: nonfinite_input | nonzero | body_export doc: 'R must already be finite' |
| C06 | nonfinite | groups origin_m entry = 1e400 (float inf) | exp: nonfinite_input | nonzero | body_export doc: authored frame must be finite |
| C07 | nonfinite | manifest vertex position as literal NaN JSON token | adm: input_read_error; exp: input_read_error | 2; nonzero | admission doc: 'three finite coordinates' |
| D01 | prohibited_density | partition density_kg_m3 = -12.0 (schema exclusiveMinimum 0) | adm: invalid_density; exp: invalid_density | 2; nonzero | schema material.density_kg_m3 exclusiveMinimum 0; compiler: 'density must be finite and positive'; exporter 'never substitutes a default density' |
| D02 | prohibited_density | partition density_kg_m3 = 0.0 (schema exclusiveMinimum 0) | adm: invalid_density; exp: invalid_density | 2; nonzero | schema material.density_kg_m3 exclusiveMinimum 0 |
| E01 | unauthorized_authority | LEGAL source_effective_segment_mass selection end-to-end: exporter must NOT export mass (doc-promised 'unsupported', exit 0 documented outcome) | adm: doc_behavior_no_mass; exp: doc_behavior_no_mass | doc; doc | body_export doc: 'unsupported: source effective segment authority was selected; body properties are not exported and source values are not consumed.' admission doc: 'reconstructed_mass_properties is always null'. CRITICAL if any mass is emitted. |
| E02 | unauthorized_authority | mixed authority: reconstructed_tissue_mass WITH non-empty source_effective_segment_ids | adm: mixed_mass_authority; exp: mixed_mass_authority | 2; nonzero | admission doc: 'No mixing of these choices ... is admitted'; schema allOf maxItems 0 under reconstructed |
| E03 | unauthorized_authority | source_effective_segment_mass with EMPTY source_effective_segment_ids | adm: missing_segment_authority; exp: missing_segment_authority | 2; nonzero | admission doc: 'one or more opaque stable IDs for source effective segment authority'; schema allOf minItems 1 |
| E04 | unauthorized_authority | cross-document authority mismatch: manifest reconstructed vs partition source_effective_segment_mass | adm: mass_authority_mismatch; exp: mass_authority_mismatch | 1; nonzero | admission doc: 'the same explicit mass-authority choice' in both inputs |
| E05 | unauthorized_authority | source_effective_segment ownership claims UNDER reconstructed_tissue_mass authority | adm: mass_authority_ownership_mismatch; exp: mass_authority_ownership_mismatch | 1; nonzero | admission doc: for reconstructed mass 'each region owner must be claimed once as tetrahedral_volume' |
| E06 | unauthorized_authority | smuggled numeric legacy segment payload field inside a matter_ownership claim | adm: bad_schema; exp: bad_schema | 2; nonzero | admission doc: 'Numeric legacy mass payloads are neither accepted nor read by this adapter.' |
| E07 | unauthorized_authority | caller-supplied pass flag 'admission_status' injected into groups request | exp: bad_schema | nonzero | body_export doc: 'It recomputes admission from the actual manifest and partition; no caller-supplied status/pass flag is accepted.' |
| F01 | type_error | partition scale_to_m as string "1.0" (schema type number) | adm: bad_number; exp: bad_number | 2; nonzero | schema scale_to_m type number |
| F02 | type_error | partition density_kg_m3 as string "12.0" | adm: bad_number; exp: bad_number | 2; nonzero | schema density type ['number','null'] |
| F03 | type_error | partition vertex position entries as strings | adm: bad_number; exp: bad_number | 2; nonzero | schema position items type number |
| F04 | type_error | partition density_kg_m3 = true (JSON bool where number) | adm: bad_number; exp: bad_number | 2; nonzero | schema density type ['number','null']; bool is not a number |
| F05 | type_error | groups rotation entry as string "1.0" | exp: bad_number | nonzero | schema rotation3 items type number |
| F06 | type_error | partition scale_to_m = true (bool where number) | adm: bad_number; exp: bad_number | 2; nonzero | schema scale_to_m type number |
| G01 | duplicate_id | duplicate body_id across two body groups | exp: duplicate_body_id | nonzero | body_export doc: 'duplicates refuse the request' |
| G02 | duplicate_id | same cell assigned to two different body groups | exp: duplicate_cell_ownership | nonzero | body_export doc: 'A cell cannot be assigned to multiple body groups; duplicates refuse the request.' |
| G03 | duplicate_id | duplicate vertex_id rows in partition | adm: duplicate_vertex_id; exp: duplicate_vertex_id | 2; nonzero | schema vertex_id identifier; runtime unique |
| G04 | duplicate_id | duplicate cell_id rows in partition | adm: duplicate_cell_id; exp: duplicate_cell_id | 2; nonzero | runtime: 'partition repeats cell ID' |
| G05 | duplicate_id | duplicate region_id rows in partition regions | adm: duplicate_region_id; exp: duplicate_region_id | 2; nonzero | admission doc: 'Exact region catalogue' |
| G06 | duplicate_id | duplicate material_id rows in partition materials | adm: duplicate_material_id; exp: duplicate_material_id | 2; nonzero | compiler CompilerReason.DUPLICATE_MATERIAL_ID |
| G07 | duplicate_id | duplicate mass_owner_id across region catalogue (manifest+partition) | adm: duplicate_mass_owner_id; exp: duplicate_mass_owner_id | 2; nonzero | admission doc: regions have 'unique mass_owner_id' |
| G08 | duplicate_id | duplicate JSON object key ('cell_ids' twice) inside a body group | exp: duplicate_json_key | nonzero | duplicate keys are ambiguous documents; reader refuses |
| G09 | duplicate_id | same cell twice inside ONE group's cell_ids (schema uniqueItems) | exp: duplicate_cell_ownership | nonzero | schema cell_ids uniqueItems true |
| G10 | duplicate_id | duplicate entry in manifest source_effective_segment_ids (schema uniqueItems) | adm: duplicate_identifier; exp: duplicate_identifier | 2; nonzero | schema source_effective_segment_ids uniqueItems true |
| G11 | duplicate_id | group references cell id absent from partition (missing group cell) | exp: unknown_group_cell_id | nonzero | body_export doc: 'refused: ... missing group cell' |
| H01 | unknown_enum | manifest mass_authority = 'combined_mass_authority' (not in enum) | adm: bad_mass_authority; exp: bad_mass_authority | 2; nonzero | admission doc: 'There is no inferred or combined authority.' |
| H02 | unknown_enum | matter_ownership.representation = 'point_mass_lump' (not in enum) | adm: bad_matter_representation; exp: bad_matter_representation | 2; nonzero | schema representation enum [tetrahedral_volume, surface_mass_overlay, source_effective_segment] |
| H03 | unknown_enum | manifest schema_version = 'chimera.fitting_manifest.v2' (const mismatch) | adm: bad_schema; exp: bad_schema | 2; nonzero | schema const 'chimera.fitting_manifest.v1' |
| H04 | unknown_enum | partition proposal referencing an unknown region id | adm: unknown_region_reference; exp: unknown_region_reference | 1; nonzero | admission doc: 'Unknown region references are retained in the row and cause a named refusal; they are never remapped.' |
| H05 | unknown_enum | partition mass_authority = 'not_chosen' (not in enum) | adm: bad_mass_authority; exp: bad_mass_authority | 2; nonzero | admission doc: 'Required explicit choice' |
| I01 | mesh_orientation | partition tetrahedron with negative orientation (swapped vertices; det<0) | adm: inverted_tetrahedron; exp: inverted_tetrahedron | 2; nonzero | admission doc: 'It does not reorder or repair tetrahedron orientation.' |
| I02 | mesh_orientation | two vertices at the identical position (degenerate/duplicate-position cell) | adm: duplicate_vertex_position; exp: duplicate_vertex_position | 2; nonzero | compiler CompilerReason.DUPLICATE_VERTEX_POSITION |
