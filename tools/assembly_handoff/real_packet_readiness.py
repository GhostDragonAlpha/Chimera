"""Example 5 — the REAL anatomy packet, run through the assembly-handoff adapter.

This is not a fixture and it is not made to pass. It answers, for the anatomy the
anatomy compiler actually produced (`.tmp/anatomy_compiler/runs/`):

    "Does this assembly have the explicitly authored information needed for a
     dynamics trial, and exactly what is missing?"

The two packets that exist are admitted as `real`, with their bytes hashed. The three
inputs a dynamics trial still needs — a reconstructed material-volume document, an
ownership/mass-binding document and an authored mechanical-requirements document — are
declared ABSENT at the paths they would have to appear at. Nothing is substituted for
them: no density is inferred from the transported anatomy masses, no attachment patch
is invented from tendon waypoints, no frame transform is conjured to bind the packets'
own rest frames to an assembly root.

The report therefore says what is missing and why, and keeps every failure visible.

Run:  python tools/assembly_handoff/real_packet_readiness.py [--out out/real_packet_readiness.json]
Exit: 0 = report produced (readiness may be false — it is expected to be false here)
      3 = the adapter reported a REAL assembly as dynamics-ready, which would mean a
          readiness rule had been lost. That is treated as a bug, not a success.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from assembly_handoff import (  # noqa: E402
    GEO_PORT, GEO_WAYPOINT, MECH_QUALIFIED, ROLE_ANATOMY, ROLE_ANATOMY_ADMISSION,
    ROLE_CANDIDATES, ROLE_MATERIAL_VOLUME, ROLE_OWNERSHIP, ROLE_REQUIREMENTS,
    HandoffAssembler, canonical_json, display_path, sha256_bytes,
)

REPORT_SCHEMA = "chimera.assembly_handoff_real_packet_report.v1"
REPO_ROOT = HERE.parent.parent           # E:/PythonChimera
RUNS = REPO_ROOT / ".tmp" / "anatomy_compiler" / "runs"
# Inputs the producer (produce_inputs.py) writes into tools/assembly_handoff/inputs/.
INPUTS = REPO_ROOT / "tools" / "assembly_handoff" / "inputs"
OWNERSHIP_INPUT = INPUTS / "ownership_bindings.json"

# What each missing role has to supply before a dynamics trial can be authored.
MISSING_ROLE_CONTRACT = {
    ROLE_MATERIAL_VOLUME: (
        "a reconstructed_material_volume partition (tools/material_volume.py v1) whose "
        "regions carry a declared density_source; it is the only thing that can turn "
        "geometry into validated tissue mass, mass properties and inertia"),
    ROLE_OWNERSHIP: (
        "an ownership document naming every component, its kind, its local frame, and "
        "which single matter representation counts toward its mass — the membrane/body "
        "double-count boundary cannot be inferred, it has to be authored"),
    ROLE_REQUIREMENTS: (
        "an authored mechanical-requirements document: the assembly frame tree plus, per "
        "attachment, anchor positions, weights, patch area, areal stiffness and the minimum "
        "couple stiffness the bond must deliver"),
}


def _file_row(path: Path, role: str, admitted_as: str, note: str) -> dict[str, Any]:
    """Hash an evidence file that exists; name the absence of one that does not."""
    shown = display_path(path, REPO_ROOT)
    if path.is_file():
        data = path.read_bytes()
        return {"path": shown, "exists": True, "sha256": sha256_bytes(data),
                "bytes": len(data), "role": role, "admitted_as": admitted_as, "note": note}
    return {"path": shown, "exists": False, "sha256": None, "bytes": None,
            "role": role, "admitted_as": admitted_as, "note": note}


def build_bundle() -> dict[str, Any]:
    """The real-packet bundle: two present packets, three named absences."""
    inputs: list[dict[str, Any]] = []

    for label, path, role in (
            ("actual_monkey_fit", RUNS / "actual_monkey_fit.json", ROLE_ANATOMY),
            ("attachment_candidates_actual", RUNS / "attachment_candidates.json",
             ROLE_CANDIDATES)):
        if not path.is_file():
            inputs.append({"label": label, "role": role, "admitted_as": "real",
                           "absent": True, "expected_path": str(path),
                           "reason": "the anatomy compiler has not produced this packet yet"})
        else:
            inputs.append({"label": label, "role": role, "admitted_as": "real",
                           "path": str(path)})

    ledger = RUNS / "admission_actual_monkey.json"
    if ledger.is_file():
        inputs.append({"label": "admission_actual_monkey", "role": ROLE_ANATOMY_ADMISSION,
                       "admitted_as": "real", "path": str(ledger),
                       "note": "anatomy owner's admission ledger: hashed as evidence, "
                               "not integrated into readiness"})

    # ownership_bindings.json is now authored (produce_inputs.py::produce_ownership): admit it
    # present so the nine anatomy matter claims get bound. material_volume_document and
    # mechanical_requirements still have no authoritative source, so they stay declared absent
    # at the paths a dynamics trial would require them at — readiness stays false.
    if OWNERSHIP_INPUT.is_file():
        inputs.append({"label": "ownership_bindings", "role": ROLE_OWNERSHIP,
                       "admitted_as": "real", "path": str(OWNERSHIP_INPUT)})
    else:
        inputs.append({"label": f"absent:{ROLE_OWNERSHIP}", "role": ROLE_OWNERSHIP,
                       "admitted_as": "real", "absent": True,
                       "expected_path": str(OWNERSHIP_INPUT),
                       "reason": MISSING_ROLE_CONTRACT[ROLE_OWNERSHIP]})

    for role in (ROLE_MATERIAL_VOLUME, ROLE_REQUIREMENTS):
        inputs.append({"label": f"absent:{role}", "role": role, "admitted_as": "real",
                       "absent": True,
                       "expected_path": str(INPUTS / f"{role}.json"),
                       "reason": MISSING_ROLE_CONTRACT[role]})

    return {"schema_version": "chimera.assembly_bundle.v1",
            "assembly_id": "actual-monkey-anatomy-packet",
            "_intent": ("real anatomy packet; the three missing inputs are declared absent "
                        "and must stay absent — this example reports readiness, it does not "
                        "manufacture it"),
            "inputs": inputs}


def _gap_census(manifest: dict[str, Any]) -> dict[str, int]:
    census: dict[str, int] = {}
    for rec in manifest["unresolved"]:
        census[rec["code"]] = census.get(rec["code"], 0) + 1
    return dict(sorted(census.items()))


PRODUCER_ARTIFACTS = (
    "material_volume_document.cannot_produce.json",
    "mechanical_requirements.cannot_produce.json",
    "prepared_root_frame_definition.json",
)


def _producer_artifacts() -> list[dict[str, Any]]:
    """Hash the producer artifacts that are EVIDENCE, never authored inputs.

    The two cannot_produce docs record exactly what a dynamics trial is still missing; the
    prepared_root_frame_definition.json records the exact root-frame definition Astra must
    author. Hashed from bytes so their provenance travels between machines."""
    out = []
    for name in PRODUCER_ARTIFACTS:
        path = INPUTS / name
        if not path.is_file():
            continue
        data = path.read_bytes()
        doc = json.loads(data.decode("utf-8"))
        out.append({"name": name, "path": display_path(path, REPO_ROOT),
                    "sha256": sha256_bytes(data), "bytes": len(data),
                    "verdict": doc.get("verdict"),
                    "required_role": doc.get("required_role")})
    return sorted(out, key=lambda r: r["name"])


def _missing_dependencies(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Every required role with no present input, named at the path it would live at."""
    rows_by_role: dict[str, dict[str, Any]] = {}
    for row in manifest["inputs"]:
        if row["role"] and row["presence"] != "present":
            rows_by_role.setdefault(row["role"], row)
    artifacts = _producer_artifacts()
    out = []
    for rec in manifest["unresolved"]:
        if rec["code"] != "required_input_absent":
            continue
        role = rec["subject_id"] or ""
        row = rows_by_role.get(role, {})
        out.append({"dependency_role": role,
                    "expected_path": row.get("path"),
                    "declared_absent": row.get("source_kind") == "declared_absent",
                    "sha256": row.get("sha256"),
                    "what_it_must_supply": MISSING_ROLE_CONTRACT.get(role, ""),
                    "supporting_evidence": [a["path"] for a in artifacts
                                            if a.get("required_role") == role],
                    "field_path": rec["field_path"]})
    return sorted(out, key=lambda r: r["dependency_role"])


def build_report() -> dict[str, Any]:
    bundle = build_bundle()
    manifest = HandoffAssembler(bundle, bundle_dir=HERE, repo_root=REPO_ROOT).build()

    anatomy_rows = [r for r in manifest["inputs"] if r["role"] == ROLE_ANATOMY]
    candidates_rows = [r for r in manifest["inputs"] if r["role"] == ROLE_CANDIDATES]
    evidence = []
    for row in sorted(manifest["inputs"], key=lambda r: r["label"]):
        note = row["note"] or MISSING_ROLE_CONTRACT.get(row["role"] or "", "")
        if row["path"] and row["presence"] == "present":
            # manifest paths are repo-relative (so digests travel between machines);
            # resolve them back against the repo root before hashing the bytes.
            evidence.append(_file_row(REPO_ROOT / row["path"], row["role"] or "unrecognised",
                                      row["admitted_as"], note))
        else:
            evidence.append({"path": row["path"], "exists": False, "sha256": None,
                             "bytes": None, "role": row["role"] or "unrecognised",
                             "admitted_as": row["admitted_as"], "note": note})

    cands = manifest["attachments"]["geometric_candidates"]
    atts = manifest["attachments"]["mechanical_attachments"]
    claims = manifest["mass_ownership_ledger"]["claims"]

    report = {
        "schema_version": REPORT_SCHEMA,
        "generated_by": {"tool": "tools/assembly_handoff/real_packet_readiness.py",
                         "adapter_version": manifest["generated_by"]["adapter_version"]},
        "question_answered": ("does the real anatomy packet carry the explicitly authored "
                              "information needed for a dynamics trial"),
        "packets_present": [{"label": r["label"], "role": r["role"], "sha256": r["sha256"],
                             "bytes": r["bytes"], "schema_detected": r["schema_detected"]}
                            for r in sorted(anatomy_rows + candidates_rows,
                                            key=lambda r: r["label"])],
        "evidence_files": evidence,
        "readiness": manifest["readiness"],
        "missing_dependencies": _missing_dependencies(manifest),
        "gap_census": _gap_census(manifest),
        "unresolved": manifest["unresolved"],
        "mass_status_summary": {
            "matter_claims_known": len(claims),
            "claims_bound_to_a_component": sum(1 for c in claims if c["component_id"]),
            "claims_counting_toward_any_mass": sum(
                1 for c in claims if c.get("counts_toward_component_mass")),
            "mass_status_histogram": _histogram(c["mass_status"] for c in claims),
            "validated_tissue_mass_claims": sum(
                1 for c in claims if c["mass_status"] == "reconstructed_tissue_volume"),
            "components_with_validated_tissue_mass": sum(
                1 for c in manifest["components"] if c["mass"]["validated_tissue_mass"]),
            "counted_mass_kg": manifest["mass_ownership_ledger"]["counted_mass_kg"],
            "uncounted_mass_kg": manifest["mass_ownership_ledger"]["uncounted_mass_kg"],
        },
        "attachment_status_summary": {
            "geometric_candidates": len(cands),
            "candidate_status_histogram": _histogram(c["status"] for c in cands),
            "anatomical_ports_covered_by_a_qualified_attachment": sum(
                1 for c in cands if c["status"] == GEO_PORT
                and c["covered_by_qualified_attachment"]),
            "mechanical_attachments_authored": len(atts),
            "mechanically_qualified": sum(1 for a in atts if a["status"] == MECH_QUALIFIED),
        },
        # Each of these is measured from the manifest, not asserted: a true value would
        # mean the adapter promoted something it was told to leave alone.
        "policy_declaration": {
            "transported_source_effective_mass_promoted_to_validated_tissue": any(
                c["mass_status"] == "reconstructed_tissue_volume"
                and c["claim_ref"].startswith("anatomy:") for c in claims),
            "tendon_waypoint_promoted_to_membrane_attachment": any(
                c["status"] == GEO_WAYPOINT and c["covered_by_qualified_attachment"]
                for c in cands),
            "matter_counted_without_an_owner": sum(
                1 for c in claims if not c.get("counts_toward_component_mass")
                and c["mass_status"] == "reconstructed_tissue_volume"),
            "densities_inferred_by_this_adapter": False,
            "meshes_repaired": False,
            "silent_defaults_used": False,
            "dynamics_executed": False,
        },
        "producer_evidence": _producer_artifacts(),
        "manifest_digest": manifest["digest"],
    }

    # Falsifier guard: a REAL packet reaching dynamics-ready would mean a rule was lost.
    if manifest["readiness"]["dynamics_trial_ready"]:
        report["soundness_violation"] = (
            "the real anatomy packet reported dynamics_trial_ready=true; at least one "
            "required authored input is absent, so this can only come from a lost rule")
    return report


def _histogram(values) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(HERE / "out" / "real_packet_readiness.json"))
    args = parser.parse_args(argv)

    report = build_report()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(canonical_json(report) + "\n", encoding="utf-8")

    r = report["readiness"]
    print(f"assembly: actual-monkey-anatomy-packet   manifest digest {report['manifest_digest']}")
    print(f"dynamics_trial_ready = {r['dynamics_trial_ready']}")
    print(f"blocking codes: {json.dumps(r['blocking_codes'])}")
    print("gap census:")
    for code, n in report["gap_census"].items():
        print(f"  {code}: {n}")
    print("missing dependencies (named, not substituted):")
    for row in report["missing_dependencies"]:
        print(f"  [{row['dependency_role']}] absent={row['declared_absent']} "
              f"expected at {row['expected_path']}")
    for a in report["producer_evidence"]:
        print(f"producer evidence : {a['name']} -> {a['verdict']} "
              f"(required_role={a.get('required_role')!r})")
    m = report["mass_status_summary"]
    print(f"matter: {m['matter_claims_known']} claims, "
          f"{m['claims_counting_toward_any_mass']} counting, "
          f"{m['validated_tissue_mass_claims']} validated tissue volume, "
          f"counted {m['counted_mass_kg']['value']:.6f} kg "
          f"(incomplete={m['counted_mass_kg']['incomplete']}), "
          f"uncounted {m['uncounted_mass_kg']['value']:.6f} kg")
    a = report["attachment_status_summary"]
    print(f"attachments: {a['geometric_candidates']} candidates "
          f"{json.dumps(a['candidate_status_histogram'])}, "
          f"{a['anatomical_ports_covered_by_a_qualified_attachment']} ports covered, "
          f"{a['mechanically_qualified']}/{a['mechanical_attachments_authored']} qualified")
    if report.get("soundness_violation"):
        print(f"SOUNDNESS VIOLATION: {report['soundness_violation']}", file=sys.stderr)
        return 3
    print(f"report written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
