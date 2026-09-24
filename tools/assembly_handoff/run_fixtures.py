"""run_fixtures.py — the four synthetic assembly-handoff fixtures, with assertions.

Each fixture is an authored synthetic bundle under `fixtures/`. This runner asserts
the outcome the contract promises and writes the resulting manifest (or refusal)
to `out/`. A failing assertion is a hard failure: it exits non-zero and prints the
offending records rather than quietly accepting a different answer.

Negative controls are mutations of fixture 1 applied here, in the open, so the
refusal paths are exercised too:
  * (a) assert a transported anatomy mass is "reconstructed_tissue_volume" -> refusal
  * (b) reference a tendon waypoint with no authored role                  -> refusal
  * (c) bind nothing to a matter claim                                     -> blocking gap
  * (d) drop the material-volume document entirely                         -> blocking gap
  * (e) declare a zero-thickness membrane patch to carry volume mass       -> refusal
  * (f) count one region's matter toward two components                    -> refusal
  * (g) supply two documents for one role                                  -> refusal

Run:  python tools/assembly_handoff/run_fixtures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from assembly_handoff import (  # noqa: E402
    MECH_INCOMPLETE, MECH_QUALIFIED, GEO_PORT, GEO_WAYPOINT, AssemblyRefusal,
    HandoffAssembler, canonical_json,
)

FIXTURES = HERE / "fixtures"
OUT = HERE / "out"

# Claim-reference prefixes used by the synthetic parts (see fixtures/parts/PROVENANCE.md).
MV_REGION = "material_volume:materials_synthetic:region:"


def _load_bundle(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _write(name: str, payload: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _codes(manifest: dict[str, Any]) -> set[str]:
    return {r["code"] for r in manifest["unresolved"]}


def _subjects(manifest: dict[str, Any], code: str) -> set[str | None]:
    return {r["subject_id"] for r in manifest["unresolved"] if r["code"] == code}


def _run(bundle_name: str, out_name: str) -> dict[str, Any]:
    bundle = _load_bundle(bundle_name)
    manifest = HandoffAssembler(bundle, bundle_dir=FIXTURES).build()
    _write(out_name, manifest)
    return manifest


def _expect_refusal(bundle: dict[str, Any], code: str, label: str) -> None:
    try:
        manifest = HandoffAssembler(bundle, bundle_dir=FIXTURES).build()
    except AssemblyRefusal as ex:
        assert ex.code == code, f"{label}: refused with {ex.code!r}, expected {code!r}"
        _write(f"refusal_{code}.json", {"refused": ex.to_record()})
        print(f"  REFUSED as required: {code} at {ex.field_path}")
        return
    raise AssertionError(
        f"{label}: expected refusal {code!r}, but a manifest was emitted "
        f"(ready={manifest['readiness']['dynamics_trial_ready']})")


def fixture_1_complete() -> None:
    print("[fixture 1] complete synthetic assembly must pass")
    m = _run("complete_assembly.json", "complete_assembly_manifest.json")
    r = m["readiness"]
    assert r["dynamics_trial_ready"], (
        f"expected ready, blocking={r['blocking_codes']} "
        f"checks={[k for k, v in r['checks'].items() if not v]}")
    assert not r["blocking_codes"], r["blocking_codes"]
    # mass: two tissue volumes validated by the material-volume compiler, two
    # membrane patches authored massless; transported anatomy mass counted nowhere.
    masses = {c["component_id"]: c["mass"] for c in m["components"]}
    assert masses["body-upper"]["validated_tissue_mass"] is True
    assert masses["body-upper"]["authority_claim_ref"] == (
        "material_volume:materials_synthetic:region:region-upper")
    assert abs(masses["body-upper"]["mass_kg"] - 1.0 / 3.0) < 1e-12
    assert masses["skin-patch-upper"]["status"] == "declared_massless"
    anatomy_claims = [c for c in m["mass_ownership_ledger"]["claims"]
                      if c["claim_ref"].startswith("anatomy:")]
    assert all(c["counts_toward_component_mass"] is False for c in anatomy_claims)
    assert all(c["mass_status"] == "transported_source_effective" for c in anatomy_claims)
    counted = m["mass_ownership_ledger"]["counted_mass_kg"]
    assert not counted["incomplete"] and abs(counted["value"] - 1.0) < 1e-12, counted
    # geometry vs mechanics stay separate: 4 candidates, 2 ports, 2 waypoints.
    cands = m["attachments"]["geometric_candidates"]
    assert len(cands) == 4 and len([c for c in cands if c["status"] == GEO_PORT]) == 2
    assert len([c for c in cands if c["status"] == GEO_WAYPOINT]) == 2
    assert all(c["source_mechanical_qualification"] is False for c in cands)
    atts = m["attachments"]["mechanical_attachments"]
    assert [a["status"] for a in atts] == [MECH_QUALIFIED, MECH_QUALIFIED], atts
    lam_min = min(a["gate_result"]["couple_stiffness_eigenvalues_n_m_per_rad"][0]
                  for a in atts)
    assert 31.9 < lam_min < 32.1, lam_min
    # Invariant behind the mass rule: nothing is called validated tissue mass unless it is a
    # reconstructed volume whose density carries a declared source. A component could only be
    # validated through a claim, so checking the claim closes the loop.
    claims = {c["claim_ref"]: c for c in m["mass_ownership_ledger"]["claims"]}
    for c in m["components"]:
        if c["mass"]["validated_tissue_mass"]:
            ref = c["mass"]["authority_claim_ref"]
            assert claims[ref]["mass_status"] == "reconstructed_tissue_volume", (ref, c)
            assert str(claims[ref]["source"].get("upstream_status")) == \
                "compiled_by_material_volume", (ref, c)
            assert any(str(a).startswith("density_source=") and
                       not str(a).endswith("None'") for a in claims[ref]["assumptions"]), \
                f"{ref} validated without a declared density source"
    # No matter may be counted toward mass without an owner binding.
    assert all(c["counts_toward_component_mass"] is not None for c in claims.values())
    # observed packet frames are notes, never adopted as bound roots.
    observed = [f for f in m["frames"] if not f["authored"]]
    assert len(observed) == 3 and all(f["status"] == "observed_unbound" for f in observed)
    assert {"frame:assembly-root", "frame:upper", "frame:lower",
            "frame:patch-upper", "frame:patch-lower"} <= {f["frame_id"] for f in m["frames"]}
    print(f"  ready=True, counted mass {counted['value']:.6f} kg, "
          f"{r['counts']['mechanically_qualified']}/{r['counts']['mechanical_attachments']} "
          f"attachments qualified, lambda_min={lam_min:.3f} N*m/rad, "
          f"{len(_codes(m) & {'frame_observed_not_bound'})} note code(s)")


def fixture_2_duplicate_mass() -> None:
    print("[fixture 2] duplicate mass ownership must be refused")
    _expect_refusal(_load_bundle("duplicate_mass_ownership.json"),
                    "duplicate_mass_ownership", "fixture 2")


def fixture_3_unresolved_anatomy_mass() -> None:
    print("[fixture 3] unresolved anatomy mass must block readiness")
    m = _run("unresolved_anatomy_mass.json", "unresolved_anatomy_mass_manifest.json")
    r = m["readiness"]
    assert not r["dynamics_trial_ready"], "transported anatomy mass must not read as ready"
    assert r["blocking_codes"] == ["component_mass_not_validated"], r["blocking_codes"]
    assert _subjects(m, "component_mass_not_validated") == {"body-upper", "body-lower"}
    masses = {c["component_id"]: c["mass"] for c in m["components"]}
    assert masses["body-upper"]["validated_tissue_mass"] is False
    assert masses["body-upper"]["status"] == "transported_source_effective"
    # the transported numbers are still reported verbatim (with their assumption),
    # they are simply never called validated tissue mass.
    assert abs(masses["body-upper"]["mass_kg"] - 0.42) < 1e-12
    assert "source_effective_x_det_scale" in masses["body-upper"]["assumptions"]
    print("  ready=False, blocking=['component_mass_not_validated'] (x2 components)")


def fixture_4_waypoint_incomplete() -> None:
    print("[fixture 4] waypoint + missing mechanical parameters stays incomplete")
    m = _run("waypoint_not_attachment.json", "waypoint_not_attachment_manifest.json")
    r = m["readiness"]
    assert not r["dynamics_trial_ready"], "must not be ready with null patch parameters"
    codes = _codes(m)
    assert {"attachment_parameter_missing", "attachment_not_qualified"} <= codes, codes
    atts = {a["attachment_id"]: a for a in m["attachments"]["mechanical_attachments"]}
    incomplete = atts["att-patch-lower-waypoint"]
    assert incomplete["status"] == MECH_INCOMPLETE
    assert incomplete["gate_result"] is None, "the gate must not be reached without inputs"
    assert incomplete["missing_fields"] == [
        "requirements[requirements_waypoint_incomplete].attachments[1].kappa_areal_n_m3",
        "requirements[requirements_waypoint_incomplete].attachments[1].patch_area_m2",
        "requirements[requirements_waypoint_incomplete].attachments[1].stiffness_kbar",
    ], incomplete["missing_fields"]
    assert atts["att-patch-upper"]["status"] == MECH_QUALIFIED
    # the waypoint is still a waypoint geometrically, even though it was authored in.
    cands = {c["candidate_id"]: c for c in m["attachments"]["geometric_candidates"]}
    way = cands["cand:candidates_synthetic:upper:s_up_2"]
    assert way["status"] == GEO_WAYPOINT and way["endpoint_roles"] == []
    assert "waypoint_authored_as_port" in codes
    note = [x for x in m["unresolved"] if x["code"] == "waypoint_authored_as_port"][0]
    assert note["severity"] == "note", note
    print(f"  ready=False, {len(incomplete['missing_fields'])} authored fields left "
          f"missing, waypoint kept as {way['status']}")


def negative_controls() -> None:
    print("[controls] refusal paths, mutated from fixture 1")
    base = _load_bundle("complete_assembly.json")

    # (a) promoting transported anatomy mass to validated tissue mass.
    ownership_doc = json.loads((FIXTURES / "parts" / "ownership_complete.json")
                               .read_text(encoding="utf-8"))
    for claim in ownership_doc["mass_claims"]:
        if claim["claim_ref"].startswith("anatomy:"):
            claim["assert_mass_status"] = "reconstructed_tissue_volume"
    promo = json.loads(json.dumps(base))
    promo["inputs"] = [i for i in promo["inputs"] if i["label"] != "ownership_complete"]
    promo["inputs"].append({"label": "ownership_complete", "role": "ownership_bindings",
                            "admitted_as": "synthetic", "document": ownership_doc})
    _expect_refusal(promo, "mass_status_promotion", "control a (mass promotion)")

    # (b) a tendon waypoint referenced as an endpoint with no authored role.
    way = json.loads(json.dumps(base))
    req_doc = json.loads((FIXTURES / "parts" / "requirements_complete.json")
                         .read_text(encoding="utf-8"))
    for att in req_doc["attachments"]:
        if att["attachment_id"] == "att-patch-lower":
            att["endpoints"].append({
                "endpoint_id": "att-patch-lower/waypoint", "component_id": "body-upper",
                "local_frame_id": "frame:upper", "position_m": [0.03, 0.25, 0.0],
                "port_candidate_id": "cand:candidates_synthetic:upper:s_up_2"})
    way["inputs"] = [i for i in way["inputs"] if i["label"] != "requirements_complete"]
    way["inputs"].append({"label": "requirements_complete", "role": "mechanical_requirements",
                          "admitted_as": "synthetic", "document": req_doc})
    _expect_refusal(way, "waypoint_promoted_to_attachment", "control b (waypoint promotion)")

    # (c) matter that nobody owns: a blocking gap, never a silent drop.
    unowned = json.loads(json.dumps(base))
    partial = json.loads((FIXTURES / "parts" / "ownership_complete.json")
                         .read_text(encoding="utf-8"))
    partial["mass_claims"] = [c for c in partial["mass_claims"]
                              if not c["claim_ref"].startswith("anatomy:")]
    unowned["inputs"] = [i for i in unowned["inputs"] if i["label"] != "ownership_complete"]
    unowned["inputs"].append({"label": "ownership_complete", "role": "ownership_bindings",
                              "admitted_as": "synthetic", "document": partial})
    m = HandoffAssembler(unowned, bundle_dir=FIXTURES).build()
    _write("control_unbound_matter_manifest.json", m)
    assert not m["readiness"]["dynamics_trial_ready"]
    assert "unbound_matter_claim" in _codes(m)
    print("  unbound matter blocked readiness as required")

    # (d) a required input that is simply absent. The ownership document must drop the
    # bindings to the vanished packet (they would be dangling references), so what is
    # left proves the absence itself blocks readiness rather than being ignored.
    missing = json.loads(json.dumps(base))
    missing["inputs"] = [i for i in missing["inputs"]
                         if i["role"] != "material_volume_document"]
    doc_d = json.loads((FIXTURES / "parts" / "ownership_complete.json")
                       .read_text(encoding="utf-8"))
    doc_d["mass_claims"] = [c for c in doc_d["mass_claims"]
                             if not c["claim_ref"].startswith("material_volume:")]
    missing["inputs"] = [i for i in missing["inputs"] if i["label"] != "ownership_complete"]
    missing["inputs"].append({"label": "ownership_complete", "role": "ownership_bindings",
                              "admitted_as": "synthetic", "document": doc_d})
    m = HandoffAssembler(missing, bundle_dir=FIXTURES).build()
    _write("control_missing_input_manifest.json", m)
    assert not m["readiness"]["dynamics_trial_ready"]
    assert "required_input_absent" in _codes(m), _codes(m)
    print("  absent material-volume document blocked readiness as required")

    # (e) a zero-thickness membrane patch declared to carry mass.
    sheet = json.loads(json.dumps(base))
    doc_e = json.loads((FIXTURES / "parts" / "ownership_complete.json")
                       .read_text(encoding="utf-8"))
    doc_e["mass_claims"] = [c for c in doc_e["mass_claims"]
                             if c["claim_ref"] != f"{MV_REGION}region-upper"]
    doc_e["mass_claims"].append({
        "claim_ref": f"{MV_REGION}region-upper",
        "component_id": "skin-patch-upper", "counts_toward_component_mass": True,
        "assert_mass_status": "reconstructed_tissue_volume",
        "reason": "the patch is also the volume"})
    sheet["inputs"] = [i for i in sheet["inputs"] if i["label"] != "ownership_complete"]
    sheet["inputs"].append({"label": "ownership_surface", "role": "ownership_bindings",
                            "admitted_as": "synthetic", "document": doc_e})
    _expect_refusal(sheet, "unsupported_surface_mass_claim", "control e (sheet mass)")

    # (f) the same matter counted toward two different components.
    twice = json.loads(json.dumps(base))
    doc_f = json.loads((FIXTURES / "parts" / "ownership_complete.json")
                       .read_text(encoding="utf-8"))
    doc_f["mass_claims"] = [c for c in doc_f["mass_claims"]
                             if c["claim_ref"] != f"{MV_REGION}region-lower"]
    doc_f["mass_claims"].append({
        "claim_ref": f"{MV_REGION}region-upper",
        "component_id": "body-lower", "counts_toward_component_mass": True,
        "assert_mass_status": "reconstructed_tissue_volume",
        "reason": "CONFLICT: region-upper is already counted by body-upper"})
    twice["inputs"] = [i for i in twice["inputs"] if i["label"] != "ownership_complete"]
    twice["inputs"].append({"label": "ownership_counted_twice", "role": "ownership_bindings",
                            "admitted_as": "synthetic", "document": doc_f})
    _expect_refusal(twice, "duplicate_mass_ownership", "control f (matter counted twice)")

    # (g) two documents claiming one role. Neither may silently win: whichever dropped its
    # bindings would change the mass ledger without a word about it.
    dup_role = json.loads(json.dumps(base))
    second = json.loads((FIXTURES / "parts" / "ownership_complete.json")
                        .read_text(encoding="utf-8"))
    second["mass_claims"] = []          # harmless on its own; the ambiguity is the point
    dup_role["inputs"].append({"label": "ownership_second", "role": "ownership_bindings",
                               "admitted_as": "synthetic", "document": second})
    _expect_refusal(dup_role, "duplicate_role_input", "control g (two documents, one role)")


def main() -> int:
    fixture_1_complete()
    fixture_2_duplicate_mass()
    fixture_3_unresolved_anatomy_mass()
    fixture_4_waypoint_incomplete()
    negative_controls()
    print(f"\nall fixtures and controls passed; manifests in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
