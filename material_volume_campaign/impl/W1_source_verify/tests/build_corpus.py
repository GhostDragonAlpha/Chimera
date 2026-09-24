"""W1 adversarial corpus builder — regenerates agents/B7_faultinjection's
frozen matrix mutations into the W1 dir (the B7 dir is read-only and is never
edited). Sources of truth:
  - the genuine example triple in tools/ (read-only),
  - the frozen matrix definitions in
    material_volume_campaign/agents/B7_faultinjection/work/mutation_matrix_frozen.json
    (read-only; matrix ids and targets are transcribed below exactly).

Outputs into tests/corpus/:
  valid_report.json            fresh exporter output for the example triple
  corrupt_M{01..14}.json       the 14 report-level value-class mutations
  inputs_mutated_M07b/         density-nulled partition inputs (B7 control)
  inputs_mutated_M09b/         duplicate-owner inputs (B7 control)
  regenerated_M07b.json        pinned-equivalent regeneration from M07b inputs
  regenerated_M09b.json        pinned-equivalent regeneration from M09b inputs

The regenerated control reports VERIFY against their own mutated inputs — that
is the decision's caveat demonstrated (agreement with the producer), while the
reports themselves say blocked/not_admitted and the retained analytic checks
(admission/compiler refusals) are what flag the inputs.

Run: python tests/build_corpus.py
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

TOOLS = Path("E:/ChimeraWork/mvc-20260924/tools")
CORPUS = Path(__file__).resolve().parent / "corpus"
MATRIX = Path("E:/ChimeraWork/mvc-20260924/material_volume_campaign/agents/"
              "B7_faultinjection/work/mutation_matrix_frozen.json")


def body(report, body_id):
    return next(row for row in report["body_groups"]
                if row["body_id"] == body_id)


def regenerate(manifest_path: Path, partition_path: Path,
               groups_path: Path) -> dict:
    sys.path.insert(0, str(TOOLS))
    import material_volume_body_export as exporter
    return exporter.build_export_report(
        exporter.read_json_file(str(manifest_path)),
        exporter.read_json_file(str(partition_path)),
        exporter.read_json_file(str(groups_path)))


def write(path: Path, report: dict, allow_nan: bool = False) -> None:
    # Canonical single-line form (matches what a producer emits, modulo the
    # platform pipe newline); allow_nan only for the M14 NaN-literal row, as
    # in the B7 fixture.
    text = json.dumps(report, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=allow_nan) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    CORPUS.mkdir(parents=True, exist_ok=True)
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    known = {row["id"] for row in matrix["matrix"]}
    assert known == {f"M{i:02d}" for i in range(1, 15)} | {"M07b", "M09b", "M10b"}, known

    valid = regenerate(TOOLS / "material_volume_body_export_manifest_example.json",
                       TOOLS / "material_volume_body_export_partition_example.json",
                       TOOLS / "material_volume_body_export_groups_example.json")
    assert valid["export_status"] == "complete"
    write(CORPUS / "valid_report.json", valid)

    def mutated(mut_id, mutate):
        report = copy.deepcopy(valid)
        mutate(report)
        write(CORPUS / f"corrupt_{mut_id}.json", report,
              allow_nan=(mut_id == "M14"))

    # --- report-level mutations (frozen matrix targets, verbatim values) ---
    mutated("M01", lambda r: set_inertia(r, "coupon-body-B", 0, 1, -0.0125))
    mutated("M02", lambda r: set_inertia(r, "coupon-body-B", 0, 0, 0.076))
    mutated("M03", lambda r: set_inertia(r, "coupon-body-A", 0, 1, 0.0251))
    mutated("M04", lambda r: set_mass(r, "coupon-body-A", 2.5))
    mutated("M05", lambda r: set_mass(r, "coupon-body-A", -2.0))
    mutated("M06", lambda r: set_com(r, "coupon-body-A", 0.75))
    mutated("M07", mutate_m07)
    mutated("M08", lambda r: body(r, "coupon-body-A").pop(
        "material_mass_source_provenance"))
    mutated("M09", mutate_m09)
    mutated("M10", lambda r: r.__setitem__("export_status", "partial"))
    mutated("M10b", lambda r: body(r, "coupon-body-A").__setitem__(
        "export_status", "not_exported"))
    mutated("M11", lambda r: r.__setitem__("dynamics_readiness_claimed", True))
    mutated("M12", lambda r: body(r, "coupon-body-A").__setitem__(
        "admission_report_sha256", "0" * 64))
    mutated("M13", lambda r: body(r, "coupon-body-B")["mass_properties"]
            ["inertia_tensor_about_com"].__setitem__(
                "value", [[0.075, 0.0125],
                          *body(r, "coupon-body-B")["mass_properties"]
                          ["inertia_tensor_about_com"]["value"][1:]]))
    mutated("M14", lambda r: set_inertia(r, "coupon-body-A", 2, 2, float("nan")))

    # --- input-mutation controls (B7 M07b / M09b), reports regenerated here ---
    manifest = json.loads((TOOLS / "material_volume_body_export_manifest_example.json")
                          .read_text(encoding="utf-8"))
    partition = json.loads((TOOLS / "material_volume_body_export_partition_example.json")
                           .read_text(encoding="utf-8"))
    groups_bytes = (TOOLS / "material_volume_body_export_groups_example.json")\
        .read_bytes()

    m07b_dir = CORPUS / "inputs_mutated_M07b"
    m07b_dir.mkdir(exist_ok=True)
    m07b_partition = copy.deepcopy(partition)
    for material in m07b_partition["materials"]:
        if material["material_id"] == "tissue-A":
            material["density_kg_m3"] = None
            material["density_source"] = None
            material["conditions"] = None
    (m07b_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    (m07b_dir / "partition.json").write_text(
        json.dumps(m07b_partition, indent=2) + "\n", encoding="utf-8", newline="\n")
    (m07b_dir / "groups.json").write_bytes(groups_bytes)
    write(CORPUS / "regenerated_M07b.json",
          regenerate(m07b_dir / "manifest.json", m07b_dir / "partition.json",
                     m07b_dir / "groups.json"))

    m09b_dir = CORPUS / "inputs_mutated_M09b"
    m09b_dir.mkdir(exist_ok=True)
    m09b_manifest = copy.deepcopy(manifest)
    m09b_partition = copy.deepcopy(partition)
    for regions in (m09b_manifest["regions"], m09b_partition["regions"]):
        for region in regions:
            if region["mass_owner_id"] == "owner-B":
                region["mass_owner_id"] = "owner-A"
    for claim in m09b_manifest["matter_ownership"]:
        if claim["mass_owner_id"] == "owner-B":
            claim["mass_owner_id"] = "owner-A"
    (m09b_dir / "manifest.json").write_text(
        json.dumps(m09b_manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    (m09b_dir / "partition.json").write_text(
        json.dumps(m09b_partition, indent=2) + "\n", encoding="utf-8", newline="\n")
    (m09b_dir / "groups.json").write_bytes(groups_bytes)
    write(CORPUS / "regenerated_M09b.json",
          regenerate(m09b_dir / "manifest.json", m09b_dir / "partition.json",
                     m09b_dir / "groups.json"))

    print(f"corpus built in {CORPUS}")


def inertia(report, body_id):
    return body(report, body_id)["mass_properties"]["inertia_tensor_about_com"]["value"]


def set_inertia(report, body_id, i, j, value):
    inertia(report, body_id)[i][j] = value


def set_mass(report, body_id, value):
    body(report, body_id)["mass_properties"]["mass"]["value"] = value


def set_com(report, body_id, x):
    body(report, body_id)["mass_properties"]["center_of_mass"]["value"][0] = x


def mutate_m07(report):
    group = body(report, "coupon-body-A")
    for row in group["cell_provenance"]:
        row["density_kg_m3"] = 13.0
    group["material_mass_source_provenance"]["material_records"][0]\
        ["density_kg_m3"] = 13.0


def mutate_m09(report):
    group = body(report, "coupon-body-A")
    for row in group["cell_provenance"]:
        row["mass_owner_id"] = "owner-IMPOSTOR"
    group["material_mass_source_provenance"]["mass_owner_ids"][0] = "owner-IMPOSTOR"


if __name__ == "__main__":
    main()
