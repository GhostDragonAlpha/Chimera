"""M06 frozen malformed-case matrix (preregistered BEFORE any case execution).

Baseline: the documented two-body coupon (fixtures/baseline/{manifest,partition,groups}.json),
verified green immediately before this file was frozen:
  admission CLI -> decision validation_only_admissible, exit 0
  export CLI    -> export_status complete, exit 0, masses 2.0 kg / 1.0 kg

Expectations are derived from (a) the two JSON Schemas, (b) the two docs
(Chimera/docs/matter/material_volume_admission.md, material_volume_body_export.md)
and (c) the refusal names defined by the tools.  The falsifier under test:
ANY case whose invalid input still yields a successful mass export
(export_status complete/partial with non-null mass_properties, or an admission
report emitting reconstructed_mass_properties) is a CRITICAL defect.

Doc anchors for exit codes:
  admission doc: "Exit status 0 means the declared validation boundary passed;
  1 means valid inputs were not admitted ...; 2 means malformed inputs or a
  named geometry/compiler refusal."
  body_export doc: "refused: malformed request, duplicate cell/body ownership,
  missing group cell, or invalid authored frame."  (Exporter exit codes are not
  documented; expectation is nonzero exit for refused/blocked, 0 only for the
  documented complete/partial/unsupported outcomes.)

Run semantics per case: "runs" lists each CLI executed and the NAMED reason that
must appear in that CLI's stdout report, plus the expected exit ("2"/"1" exact
for admission per its doc; "nonzero" for the exporter whose exit code mapping is
undocumented).  "adm"/"exp" = admission / body-export CLI.
Raw-text cases (NaN/Infinity JSON tokens, duplicate JSON key) patch baseline
bytes directly because they are not representable via json.dumps.
"""

BASE = "fixtures/baseline"

# ---------------------------------------------------------------- mutations --
def _rot0(g):
    g["body_groups"][0]["body_frame"]["domain_from_body"]["rotation"] = \
        [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]]

def _rot_refl(g):
    g["body_groups"][0]["body_frame"]["domain_from_body"]["rotation"] = \
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]]

def _rot_zero(g):
    g["body_groups"][0]["body_frame"]["domain_from_body"]["rotation"] = \
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]

def _rot_2x2(g):
    g["body_groups"][0]["body_frame"]["domain_from_body"]["rotation"] = [[1.0, 0.0], [0.0, 1.0]]

def _rot_str(g):
    g["body_groups"][0]["body_frame"]["domain_from_body"]["rotation"][0][0] = "1.0"

def _hand_left(g):
    g["body_groups"][0]["body_frame"]["handedness"] = "left"

def _frame_hand_left(m, p):
    m["coordinate_frame"]["handedness"] = "left"
    p["coordinate_frame"]["handedness"] = "left"

def _frame_scale_neg(m, p):
    m["coordinate_frame"]["scale_to_m"] = -1.0
    p["coordinate_frame"]["scale_to_m"] = -1.0

def _rot_inf_entry(g):
    g["body_groups"][0]["body_frame"]["domain_from_body"]["rotation"][0][0] = 1e400

def _unit_mm(g):
    g["body_groups"][0]["body_frame"]["coordinate_unit"] = "mm"

def _origin_inf_num(g):
    g["body_groups"][0]["body_frame"]["domain_from_body"]["origin_m"][2] = 1e400

def _dup_body_id(g):
    g["body_groups"][1]["body_id"] = "coupon-body-A"

def _cross_group_cell(g):
    g["body_groups"][1]["cell_ids"] = ["cell-A", "cell-B"]

def _dup_cell_in_group(g):
    g["body_groups"][0]["cell_ids"] = ["cell-A", "cell-A"]

def _unknown_group_cell(g):
    g["body_groups"][0]["cell_ids"] = ["cell-A", "cell-Z"]

def _pass_flag(g):
    g["admission_status"] = "validation_only_admissible"

def _no_body_frame(g):
    del g["body_groups"][0]["body_frame"]

def _no_domain_from_body(g):
    del g["body_groups"][0]["body_frame"]["domain_from_body"]

def _no_schema_version(g):
    del g["schema_version"]

def _no_cell_ids(g):
    del g["body_groups"][0]["cell_ids"]

def _empty_cell_ids(g):
    g["body_groups"][0]["cell_ids"] = []

def _no_handedness(g):
    del g["body_groups"][0]["body_frame"]["handedness"]

def _no_origin(g):
    del g["body_groups"][0]["body_frame"]["domain_from_body"]["origin_m"]

def _vtx_inf(p):
    p["vertices"][0]["position"][0] = 1e400

def _density_inf(p):
    p["materials"][0]["density_kg_m3"] = 1e400

def _density_neg(p):
    p["materials"][0]["density_kg_m3"] = -12.0

def _density_zero(p):
    p["materials"][0]["density_kg_m3"] = 0.0

def _density_str(p):
    p["materials"][0]["density_kg_m3"] = "12.0"

def _density_bool(p):
    p["materials"][0]["density_kg_m3"] = True

def _scale_str(p):
    p["coordinate_frame"]["scale_to_m"] = "1.0"

def _scale_bool(p):
    p["coordinate_frame"]["scale_to_m"] = True

def _pos_str(p):
    p["vertices"][1]["position"] = ["1.0", "0.0", "0.0"]

def _no_materials(p):
    del p["materials"]

def _no_frame_scale(p):
    del p["coordinate_frame"]["scale_to_m"]

def _no_vertex_position(p):
    del p["vertices"][0]["position"]

def _no_partition_cells(p):
    del p["cells"]

def _dup_vertex_id(p):
    p["vertices"][1]["vertex_id"] = "a0"

def _dup_cell_id(p):
    p["cells"][1]["cell_id"] = "cell-A"

def _dup_region_id(p):
    p["regions"][1]["region_id"] = "region-A"

def _dup_material_id(p):
    p["materials"][1]["material_id"] = "tissue-A"

def _dup_mass_owner(m, p):
    m["regions"][1]["mass_owner_id"] = "owner-A"
    p["regions"][1]["mass_owner_id"] = "owner-A"

def _unknown_region_ref(p):
    p["cells"][1]["proposals"] = ["region-Z"]

def _inverted_tet(p):
    p["cells"][0]["vertex_ids"] = ["a1", "a0", "a2", "a3"]

def _dup_vertex_position(m, p):
    m["vertices"][1]["position"] = [0.0, 0.0, 0.0]
    p["vertices"][1]["position"] = [0.0, 0.0, 0.0]

def _no_mass_authority(m):
    del m["mass_authority"]

def _no_ownership(m):
    del m["matter_ownership"]

def _no_segment_ids(m):
    del m["source_effective_segment_ids"]

def _mixed_authority(m):
    m["source_effective_segment_ids"] = ["seg-1"]

def _empty_segments(m):
    m["mass_authority"] = "source_effective_segment_mass"
    m["source_effective_segment_ids"] = []
    m["matter_ownership"] = [{"matter_id": "seg-matter",
                              "representation": "source_effective_segment",
                              "mass_owner_id": "seg-1"}]

def _partition_source_only(m, p):
    p["mass_authority"] = "source_effective_segment_mass"

def _segment_claim_under_reconstructed(m):
    m["matter_ownership"] = [{"matter_id": "seg-matter",
                              "representation": "source_effective_segment",
                              "mass_owner_id": "seg-spine-1"}]

def _smuggled_payload(m):
    m["matter_ownership"][0]["segment_mass_kg"] = 5.0

def _dup_segment_ids(m):
    m["mass_authority"] = "source_effective_segment_mass"
    m["source_effective_segment_ids"] = ["seg-1", "seg-1"]
    m["matter_ownership"] = [{"matter_id": "seg-matter",
                              "representation": "source_effective_segment",
                              "mass_owner_id": "seg-1"}]

def _bad_authority(m):
    m["mass_authority"] = "combined_mass_authority"

def _bad_representation(m):
    m["matter_ownership"][0]["representation"] = "point_mass_lump"

def _bad_schema_version(m):
    m["schema_version"] = "chimera.fitting_manifest.v2"

def _partition_bad_authority(m, p):
    p["mass_authority"] = "not_chosen"

def _source_effective_valid(m, p):
    """E01: the legal source-effective selection, to prove no mass is exported."""
    m["mass_authority"] = "source_effective_segment_mass"
    m["source_effective_segment_ids"] = ["seg-spine-1"]
    m["matter_ownership"] = [{"matter_id": "seg-matter",
                              "representation": "source_effective_segment",
                              "mass_owner_id": "seg-spine-1"}]
    p["mass_authority"] = "source_effective_segment_mass"

# raw-text patches: (file, old, new) applied to the baseline bytes
RAW = {
    "C02": [("partition", '"density_kg_m3": 12.0', '"density_kg_m3": NaN')],
    "C03": [("groups", '"origin_m": [3.0, -2.0, 1.0]', '"origin_m": [3.0, -2.0, Infinity]')],
    "C07": [("manifest", '"vertex_id": "a1", "position": [1.0, 0.0, 0.0]',
             '"vertex_id": "a1", "position": [NaN, 0.0, 0.0]')],
    "G08": [("groups", '"cell_ids": ["cell-A"],', '"cell_ids": ["cell-A"], "cell_ids": ["cell-A"],')],
}

MUT = {
    "A01": (_rot0, ()), "A02": (_rot_refl, ()), "A03": (_hand_left, ()),
    "A04": (_unit_mm, ()), "A07": (_rot_2x2, ()), "A08": (_rot_zero, ()),
    "A05": (_frame_hand_left, ("manifest", "partition")),
    "A06": (_frame_scale_neg, ("manifest", "partition")),
    "B01": (_no_body_frame, ()), "B02": (_no_domain_from_body, ()),
    "B03": (_no_schema_version, ()), "B04": (_no_cell_ids, ()),
    "B05": (_empty_cell_ids, ()), "B06": (_no_handedness, ()), "B07": (_no_origin, ()),
    "C05": (_rot_inf_entry, ()),
    "C06": (_origin_inf_num, ()),
    "E07": (_pass_flag, ()),
    "G01": (_dup_body_id, ()), "G02": (_cross_group_cell, ()),
    "G09": (_dup_cell_in_group, ()), "G11": (_unknown_group_cell, ()),
    "C01": (_vtx_inf, ("partition",)), "C04": (_density_inf, ("partition",)),
    "D01": (_density_neg, ("partition",)), "D02": (_density_zero, ("partition",)),
    "F01": (_scale_str, ("partition",)), "F02": (_density_str, ("partition",)),
    "F03": (_pos_str, ("partition",)), "F04": (_density_bool, ("partition",)),
    "F06": (_scale_bool, ("partition",)),
    "B08": (_no_materials, ("partition",)), "B11": (_no_frame_scale, ("partition",)),
    "B12": (_no_vertex_position, ("partition",)), "B14": (_no_partition_cells, ("partition",)),
    "G03": (_dup_vertex_id, ("partition",)), "G04": (_dup_cell_id, ("partition",)),
    "G05": (_dup_region_id, ("partition",)), "G06": (_dup_material_id, ("partition",)),
    "G07": (_dup_mass_owner, ("manifest", "partition")),
    "H04": (_unknown_region_ref, ("partition",)),
    "I01": (_inverted_tet, ("partition",)),
    "I02": (_dup_vertex_position, ("manifest", "partition")),
    "H05": (_partition_bad_authority, ("manifest", "partition")),
    "B09": (_no_mass_authority, ("manifest",)), "B10": (_no_ownership, ("manifest",)),
    "B13": (_no_segment_ids, ("manifest",)), "E02": (_mixed_authority, ("manifest",)),
    "E03": (_empty_segments, ("manifest",)), "E04": (_partition_source_only, ("manifest", "partition")),
    "E05": (_segment_claim_under_reconstructed, ("manifest",)),
    "E06": (_smuggled_payload, ("manifest",)), "G10": (_dup_segment_ids, ("manifest",)),
    "H01": (_bad_authority, ("manifest",)), "H02": (_bad_representation, ("manifest",)),
    "H03": (_bad_schema_version, ("manifest",)),
    "E01": (_source_effective_valid, ("manifest", "partition")),
}

def R(tool, reason, exit_):
    return {"tool": tool, "expect": "refusal", "reason": reason, "exit": exit_}

CASES = [
 # ---------------- A. invalid frames (authored body frames, declared frames) --
 ("A01", "invalid_frame", "groups rotation scaled x2: orthonormality violated, det=+8",
  [R("exp", "invalid_authored_frame", "nonzero")],
  "body_export doc: 'R must already be finite, orthonormal, and proper (det R = +1); it is not normalized or repaired.'"),
 ("A02", "invalid_frame", "groups rotation with det=-1 (reflected, wrong handedness transform)",
  [R("exp", "invalid_authored_frame", "nonzero")],
  "schema rotation3: 'Must be a proper orthonormal rotation (R^T R=I, det R=+1)'"),
 ("A03", "invalid_frame", "groups body_frame.handedness = 'left' (declared wrong handedness)",
  [R("exp", "unsupported_authored_frame", "nonzero")],
  "schema bodyFrame.handedness const 'right'; exporter: 'body frames must be right-handed'"),
 ("A04", "invalid_frame", "groups body_frame.coordinate_unit = 'mm' (schema const 'm')",
  [R("exp", "unsupported_authored_frame", "nonzero")],
  "body_export doc: authored frame supplies 'coordinate_unit: m'"),
 ("A05", "invalid_frame", "manifest+partition coordinate_frame.handedness = 'left'",
  [R("adm", "unsupported_coordinate_frame", "2"), R("exp", "unsupported_coordinate_frame", "nonzero")],
  "admission doc: 'Non-right-handed frames, reflections ... [unsupported]'; schema const 'right'"),
 ("A06", "invalid_frame", "manifest+partition coordinate_frame.scale_to_m = -1.0 (schema exclusiveMinimum 0)",
  [R("adm", "bad_scale", "2"), R("exp", "bad_scale", "nonzero")],
  "admission doc: 'positive finite scale_to_m'; schema exclusiveMinimum 0"),
 ("A07", "invalid_frame", "groups rotation given as 2x2 (bad shape)",
  [R("exp", "bad_shape", "nonzero")],
  "schema rotation3 minItems/maxItems 3"),
 ("A08", "invalid_frame", "groups rotation = zero matrix (singular, not a rotation)",
  [R("exp", "invalid_authored_frame", "nonzero")],
  "body_export doc: 'R must already be finite, orthonormal, and proper (det R = +1)'"),
 # ---------------- B. missing required fields (enumerated from the schemas) --
 ("B01", "missing_field", "groups: body_groups[0] missing required 'body_frame'",
  [R("exp", "bad_schema", "nonzero")], "schema bodyGroup required [body_id, cell_ids, body_frame]"),
 ("B02", "missing_field", "groups: body_frame missing required 'domain_from_body'",
  [R("exp", "bad_schema", "nonzero")], "schema bodyFrame required [... 'domain_from_body']"),
 ("B03", "missing_field", "groups: root missing required 'schema_version'",
  [R("exp", "bad_schema", "nonzero")], "schema root required ['schema_version', 'body_groups']"),
 ("B04", "missing_field", "groups: body_groups[0] missing required 'cell_ids'",
  [R("exp", "bad_schema", "nonzero")], "schema bodyGroup required"),
 ("B05", "missing_field", "groups: cell_ids = [] (schema minItems 1)",
  [R("exp", "empty_body_group", "nonzero")],
  "body_export doc: 'a non-empty list of stable cell_ids'"),
 ("B06", "missing_field", "groups: body_frame missing required 'handedness'",
  [R("exp", "bad_schema", "nonzero")], "schema bodyFrame required"),
 ("B07", "missing_field", "groups: domain_from_body missing required 'origin_m'",
  [R("exp", "bad_schema", "nonzero")], "schema domain_from_body required ['rotation', 'origin_m']"),
 ("B08", "missing_field", "partition: missing required 'materials' array",
  [R("adm", "bad_schema", "2"), R("exp", "bad_schema", "nonzero")],
  "schema materialPartition required includes 'materials'"),
 ("B09", "missing_field", "manifest: missing required 'mass_authority'",
  [R("adm", "bad_schema", "2"), R("exp", "bad_schema", "nonzero")],
  "admission doc: 'Required explicit choice ... There is no inferred or combined authority.'"),
 ("B10", "missing_field", "manifest: missing required 'matter_ownership'",
  [R("adm", "bad_schema", "2"), R("exp", "bad_schema", "nonzero")],
  "schema fittingManifest required includes 'matter_ownership'"),
 ("B11", "missing_field", "partition: coordinate_frame missing required 'scale_to_m'",
  [R("adm", "bad_schema", "2"), R("exp", "bad_schema", "nonzero")],
  "schema coordinateFrame required includes 'scale_to_m'"),
 ("B12", "missing_field", "partition: vertex row missing required 'position'",
  [R("adm", "bad_schema", "2"), R("exp", "bad_schema", "nonzero")],
  "schema vertex required ['vertex_id', 'position']"),
 ("B13", "missing_field", "manifest: missing required 'source_effective_segment_ids'",
  [R("adm", "bad_schema", "2"), R("exp", "bad_schema", "nonzero")],
  "schema fittingManifest required includes 'source_effective_segment_ids'"),
 ("B14", "missing_field", "partition: missing required 'cells' array",
  [R("adm", "bad_schema", "2"), R("exp", "unknown_group_cell_id", "nonzero")],
  "schema materialPartition required includes 'cells'; exporter refuses group cells absent from partition"),
 # ---------------- C. non-finite values ----------------------------------
 ("C01", "nonfinite", "partition vertex position coordinate = 1e400 (parses to float inf)",
  [R("adm", "nonfinite_input", "2"), R("exp", "nonfinite_input", "nonzero")],
  "admission doc: 'three finite coordinates'; runtime _number refuses non-finite"),
 ("C02", "nonfinite", "partition density as literal NaN JSON token (rejected by the JSON reader)",
  [R("adm", "input_read_error", "2"), R("exp", "input_read_error", "nonzero")],
  "admission doc: report serialization 'allow_nan=False'; readers reject nonstandard constants"),
 ("C03", "nonfinite", "groups origin_m containing literal Infinity JSON token",
  [R("exp", "input_read_error", "nonzero")],
  "body_export doc: 'R must already be finite'; output has 'no non-finite numbers'"),
 ("C04", "nonfinite", "partition density_kg_m3 = 1e400 (float inf)",
  [R("adm", "nonfinite_input", "2"), R("exp", "nonfinite_input", "nonzero")],
  "admission doc: material records carry density; compiler: 'density must be finite and positive'"),
 ("C05", "nonfinite", "groups rotation entry = 1e400 (float inf)",
  [R("exp", "nonfinite_input", "nonzero")], "body_export doc: 'R must already be finite'"),
 ("C06", "nonfinite", "groups origin_m entry = 1e400 (float inf)",
  [R("exp", "nonfinite_input", "nonzero")], "body_export doc: authored frame must be finite"),
 ("C07", "nonfinite", "manifest vertex position as literal NaN JSON token",
  [R("adm", "input_read_error", "2"), R("exp", "input_read_error", "nonzero")],
  "admission doc: 'three finite coordinates'"),
 # ---------------- D. negative / zero density where prohibited -----------
 ("D01", "prohibited_density", "partition density_kg_m3 = -12.0 (schema exclusiveMinimum 0)",
  [R("adm", "invalid_density", "2"), R("exp", "invalid_density", "nonzero")],
  "schema material.density_kg_m3 exclusiveMinimum 0; compiler: 'density must be finite and positive'; exporter 'never substitutes a default density'"),
 ("D02", "prohibited_density", "partition density_kg_m3 = 0.0 (schema exclusiveMinimum 0)",
  [R("adm", "invalid_density", "2"), R("exp", "invalid_density", "nonzero")],
  "schema material.density_kg_m3 exclusiveMinimum 0"),
 # ---------------- E. unauthorized source-effective authority -------------
 ("E01", "unauthorized_authority", "LEGAL source_effective_segment_mass selection end-to-end: exporter must NOT export mass (doc-promised 'unsupported', exit 0 documented outcome)",
  [{"tool": "adm", "expect": "doc_behavior_no_mass"},
   {"tool": "exp", "expect": "doc_behavior_no_mass"}],
  "body_export doc: 'unsupported: source effective segment authority was selected; body properties are not exported and source values are not consumed.' admission doc: 'reconstructed_mass_properties is always null'. CRITICAL if any mass is emitted."),
 ("E02", "unauthorized_authority", "mixed authority: reconstructed_tissue_mass WITH non-empty source_effective_segment_ids",
  [R("adm", "mixed_mass_authority", "2"), R("exp", "mixed_mass_authority", "nonzero")],
  "admission doc: 'No mixing of these choices ... is admitted'; schema allOf maxItems 0 under reconstructed"),
 ("E03", "unauthorized_authority", "source_effective_segment_mass with EMPTY source_effective_segment_ids",
  [R("adm", "missing_segment_authority", "2"), R("exp", "missing_segment_authority", "nonzero")],
  "admission doc: 'one or more opaque stable IDs for source effective segment authority'; schema allOf minItems 1"),
 ("E04", "unauthorized_authority", "cross-document authority mismatch: manifest reconstructed vs partition source_effective_segment_mass",
  [R("adm", "mass_authority_mismatch", "1"), R("exp", "mass_authority_mismatch", "nonzero")],
  "admission doc: 'the same explicit mass-authority choice' in both inputs"),
 ("E05", "unauthorized_authority", "source_effective_segment ownership claims UNDER reconstructed_tissue_mass authority",
  [R("adm", "mass_authority_ownership_mismatch", "1"), R("exp", "mass_authority_ownership_mismatch", "nonzero")],
  "admission doc: for reconstructed mass 'each region owner must be claimed once as tetrahedral_volume'"),
 ("E06", "unauthorized_authority", "smuggled numeric legacy segment payload field inside a matter_ownership claim",
  [R("adm", "bad_schema", "2"), R("exp", "bad_schema", "nonzero")],
  "admission doc: 'Numeric legacy mass payloads are neither accepted nor read by this adapter.'"),
 ("E07", "unauthorized_authority", "caller-supplied pass flag 'admission_status' injected into groups request",
  [R("exp", "bad_schema", "nonzero")],
  "body_export doc: 'It recomputes admission from the actual manifest and partition; no caller-supplied status/pass flag is accepted.'"),
 # ---------------- F. type errors -----------------------------------------
 ("F01", "type_error", "partition scale_to_m as string \"1.0\" (schema type number)",
  [R("adm", "bad_number", "2"), R("exp", "bad_number", "nonzero")], "schema scale_to_m type number"),
 ("F02", "type_error", "partition density_kg_m3 as string \"12.0\"",
  [R("adm", "bad_number", "2"), R("exp", "bad_number", "nonzero")], "schema density type ['number','null']"),
 ("F03", "type_error", "partition vertex position entries as strings",
  [R("adm", "bad_number", "2"), R("exp", "bad_number", "nonzero")], "schema position items type number"),
 ("F04", "type_error", "partition density_kg_m3 = true (JSON bool where number)",
  [R("adm", "bad_number", "2"), R("exp", "bad_number", "nonzero")], "schema density type ['number','null']; bool is not a number"),
 ("F05", "type_error", "groups rotation entry as string \"1.0\"",
  [R("exp", "bad_number", "nonzero")], "schema rotation3 items type number"),
 ("F06", "type_error", "partition scale_to_m = true (bool where number)",
  [R("adm", "bad_number", "2"), R("exp", "bad_number", "nonzero")], "schema scale_to_m type number"),
 # ---------------- G. duplicate ids where unique required -----------------
 ("G01", "duplicate_id", "duplicate body_id across two body groups",
  [R("exp", "duplicate_body_id", "nonzero")], "body_export doc: 'duplicates refuse the request'"),
 ("G02", "duplicate_id", "same cell assigned to two different body groups",
  [R("exp", "duplicate_cell_ownership", "nonzero")],
  "body_export doc: 'A cell cannot be assigned to multiple body groups; duplicates refuse the request.'"),
 ("G03", "duplicate_id", "duplicate vertex_id rows in partition",
  [R("adm", "duplicate_vertex_id", "2"), R("exp", "duplicate_vertex_id", "nonzero")],
  "schema vertex_id identifier; runtime unique"),
 ("G04", "duplicate_id", "duplicate cell_id rows in partition",
  [R("adm", "duplicate_cell_id", "2"), R("exp", "duplicate_cell_id", "nonzero")],
  "runtime: 'partition repeats cell ID'"),
 ("G05", "duplicate_id", "duplicate region_id rows in partition regions",
  [R("adm", "duplicate_region_id", "2"), R("exp", "duplicate_region_id", "nonzero")],
  "admission doc: 'Exact region catalogue'"),
 ("G06", "duplicate_id", "duplicate material_id rows in partition materials",
  [R("adm", "duplicate_material_id", "2"), R("exp", "duplicate_material_id", "nonzero")],
  "compiler CompilerReason.DUPLICATE_MATERIAL_ID"),
 ("G07", "duplicate_id", "duplicate mass_owner_id across region catalogue (manifest+partition)",
  [R("adm", "duplicate_mass_owner_id", "2"), R("exp", "duplicate_mass_owner_id", "nonzero")],
  "admission doc: regions have 'unique mass_owner_id'"),
 ("G08", "duplicate_id", "duplicate JSON object key ('cell_ids' twice) inside a body group",
  [R("exp", "duplicate_json_key", "nonzero")], "duplicate keys are ambiguous documents; reader refuses"),
 ("G09", "duplicate_id", "same cell twice inside ONE group's cell_ids (schema uniqueItems)",
  [R("exp", "duplicate_cell_ownership", "nonzero")], "schema cell_ids uniqueItems true"),
 ("G10", "duplicate_id", "duplicate entry in manifest source_effective_segment_ids (schema uniqueItems)",
  [R("adm", "duplicate_identifier", "2"), R("exp", "duplicate_identifier", "nonzero")],
  "schema source_effective_segment_ids uniqueItems true"),
 ("G11", "duplicate_id", "group references cell id absent from partition (missing group cell)",
  [R("exp", "unknown_group_cell_id", "nonzero")],
  "body_export doc: 'refused: ... missing group cell'"),
 # ---------------- H. unknown enum values ---------------------------------
 ("H01", "unknown_enum", "manifest mass_authority = 'combined_mass_authority' (not in enum)",
  [R("adm", "bad_mass_authority", "2"), R("exp", "bad_mass_authority", "nonzero")],
  "admission doc: 'There is no inferred or combined authority.'"),
 ("H02", "unknown_enum", "matter_ownership.representation = 'point_mass_lump' (not in enum)",
  [R("adm", "bad_matter_representation", "2"), R("exp", "bad_matter_representation", "nonzero")],
  "schema representation enum [tetrahedral_volume, surface_mass_overlay, source_effective_segment]"),
 ("H03", "unknown_enum", "manifest schema_version = 'chimera.fitting_manifest.v2' (const mismatch)",
  [R("adm", "bad_schema", "2"), R("exp", "bad_schema", "nonzero")], "schema const 'chimera.fitting_manifest.v1'"),
 ("H04", "unknown_enum", "partition proposal referencing an unknown region id",
  [R("adm", "unknown_region_reference", "1"), R("exp", "unknown_region_reference", "nonzero")],
  "admission doc: 'Unknown region references are retained in the row and cause a named refusal; they are never remapped.'"),
 ("H05", "unknown_enum", "partition mass_authority = 'not_chosen' (not in enum)",
  [R("adm", "bad_mass_authority", "2"), R("exp", "bad_mass_authority", "nonzero")],
  "admission doc: 'Required explicit choice'"),
 # ---------------- I. invalid mesh frames (orientation/degeneracy) --------
 ("I01", "mesh_orientation", "partition tetrahedron with negative orientation (swapped vertices; det<0)",
  [R("adm", "inverted_tetrahedron", "2"), R("exp", "inverted_tetrahedron", "nonzero")],
  "admission doc: 'It does not reorder or repair tetrahedron orientation.'"),
 ("I02", "mesh_orientation", "two vertices at the identical position (degenerate/duplicate-position cell)",
  [R("adm", "duplicate_vertex_position", "2"), R("exp", "duplicate_vertex_position", "nonzero")],
  "compiler CompilerReason.DUPLICATE_VERTEX_POSITION"),
]

assert len(CASES) >= 20, "matrix must contain at least 20 cases"
_seen = set()
for cid, _cat, _desc, _runs, _doc in CASES:
    assert cid not in _seen, f"duplicate case id {cid}"
    _seen.add(cid)

def targets(cid):
    """Which baseline files the case mutates (for receipt naming)."""
    for name in RAW.get(cid, []):
        yield name
    fn, args = MUT[cid]
    for a in args:
        yield a
    if not args and cid not in RAW and cid in MUT:
        yield "groups"

if __name__ == "__main__":
    import hashlib, sys
    from pathlib import Path
    here = Path(__file__).resolve().parent
    if len(sys.argv) > 1 and sys.argv[1] == "matrix":
        lines = ["# M06 malformed-case matrix (FROZEN before execution)", "",
                 "Baseline: two-body coupon, verified green pre-freeze (admission exit 0",
                 "validation_only_admissible; export exit 0 complete, 2.0 kg + 1.0 kg).", "",
                 f"Total cases: {len(CASES)}.  Expected verdict per run: NAMED-REFUSAL (named reason +",
                 "nonzero exit; admission exit 2 refused / 1 not_admitted per its doc) except E01, which",
                 "expects the DOCUMENTED 'unsupported' non-export (no mass emitted).", "",
                 "| id | category | mutation | expected refusal (tool: adm=admission CLI, exp=body-export CLI) | expected exit | doc anchor |",
                 "|---|---|---|---|---|---|"]
        for cid, cat, desc, runs, doc in CASES:
            exp = "; ".join(f"{r['tool']}: {r.get('reason', r.get('expect'))}" for r in runs)
            ex = "; ".join(str(r.get("exit", "doc")) for r in runs)
            lines.append(f"| {cid} | {cat} | {desc} | {exp} | {ex} | {doc} |")
        (here / "matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("matrix.md written")
    blob = (Path(__file__).read_text(encoding="utf-8"))
    print("cases.py sha256:", hashlib.sha256(blob.encode("utf-8")).hexdigest())
