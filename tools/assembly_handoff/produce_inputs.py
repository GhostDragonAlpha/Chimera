"""Producers for the three input documents a dynamics trial needs.

    tools/assembly_handoff/inputs/{ownership_bindings.json,
                                   material_volume_document.cannot_produce.json,
                                   mechanical_requirements.cannot_produce.json}

This is NOT a fourth mass/attachment authority. It reads the SAME authoritative upstream
packets the adapter does (the anatomy compiler's fitted packet + attachment-candidates
packet) and emits what can be authored from them WITHOUT inventing physics:

  * ownership_bindings.json   AUTHORABLE NOW. Names every component, its kind, which single
                              matter representation is owned by it, and — crucially — that
                              the transported / root-reference anatomy mass does NOT count
                              toward validated tissue mass. assert_mass_status is derived
                              with the adapter's own rule (see derive_mass_status) so a
                              transported record can never be relabelled into validated
                              tissue mass here. This is routine implementation within an
                              existing contract (chimera.assembly_ownership.v1).

  * material_volume_document  CANNOT be produced honestly. The anatomy segments carry only a
      .cannot_produce.json  bounding-box `scale`, a `fitted_origin` and a `frame_basis`; there
                            is no tetrahedral / vertex geometry for tools/material_volume.py to
                            partition, and no declared density_source. Inventing densities or
                            volumes would violate the density-source invariant, so this producer
                            records EXACTLY what is missing (field paths) instead of fabricating.

  * mechanical_requirements   CANNOT be produced honestly. The attachment candidates carry a
      .cannot_produce.json  resolved `source_pos_local` but NO patch_area_m2, areal stiffness,
                            minimum couple stiffness or weights, and the segment tree declares
                            no authored root frame (no segment has parent=null; pelvis is not
                            itself a segment). Producing those values would be inventing
                            mechanical assumptions + an alignment nobody authored, so this
                            producer records exactly what each port is missing.

The two cannot_produce artifacts are deliberately NOT written under the adapter's
ROLE_MATERIAL_VOLUME / ROLE_REQUIREMENTS role: putting them there would make readiness think a
required input is present when it is not. They are evidence for the report, consumed as plain
JSON by real_packet_readiness.py, never as authored inputs.

Run:  python tools/assembly_handoff/produce_inputs.py [--out-dir inputs] [--anatomy <path>]
        [--candidates <path>]            (defaults point at the real packet)
Exit: 0 always — a producer that honestly reports "cannot produce" is a successful run, not a
       failure. Readiness stays false because the required documents stay absent.
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
    MASS_ROOT_REFERENCE, MASS_TRANSPORTED, MASS_UNRESOLVED,
)

# Repo-relative POSIX prefix for producer provenance strings. Kept repo-relative (not the
# absolute host path) so artifact digests are a property of the assembly, not the machine —
# the same relocation-reproducibility invariant the adapter enforces on its manifests.
TOOLS_PREFIX = "tools/assembly_handoff/"

OWNERSHIP_SCHEMA = "chimera.assembly_ownership.v1"
# Component kind for an authored body segment. The physiology records are body
# representations carried as transported / root-reference mass; rigid_body is the honest
# mechanical description and it admits no thin-sheet mass on its own.
KIND_RIGID_BODY = "rigid_body"


def derive_mass_status(mass_kind: Any, status: Any) -> str:
    """The adapter's exact mass-status rule, copied here so a producer can never promote.

    root_ref_frame_unscaled            -> root_reference_frame_only  (pelvis)
    source_effective_x_det_scale       -> transported_source_effective (the other 8)
    status == requires_density_validation -> transported_source_effective
    anything else                       -> unresolved
    """
    if mass_kind == "root_ref_frame_unscaled":
        return MASS_ROOT_REFERENCE
    if mass_kind == "source_effective_x_det_scale" or status == "requires_density_validation":
        return MASS_TRANSPORTED
    return MASS_UNRESOLVED


def _physiology_records(anatomy_doc: dict[str, Any]) -> list[dict[str, Any]]:
    phys = anatomy_doc.get("physiology") or []
    if isinstance(phys, dict):  # tolerate a keyed mapping; sort by body for determinism
        phys = [phys[k] for k in sorted(phys)]
    return [p for p in phys if isinstance(p, dict)]


def _segment_tree(anatomy_doc: dict[str, Any]) -> list[dict[str, Any]]:
    segs = anatomy_doc.get("segments") or []
    if isinstance(segs, dict):
        segs = [segs[k] for k in sorted(segs)]
    return [s for s in segs if isinstance(s, dict)]


# --------------------------------------------------------------------------- #
# 1. ownership_bindings.json  (authorable)                                     #
# --------------------------------------------------------------------------- #
def produce_ownership(anatomy_doc: dict[str, Any], label: str) -> dict[str, Any]:
    """Bind the nine physiology bodies to components; transported mass stays uncounted.

    Every claim is bound with counts_toward_component_mass=false and assert_mass_status
    taken from derive_mass_status(), so the reported 17.04 kg of transported + root-reference
    mass is declared owned but NEVER counted toward, or relabelled into, validated tissue
    mass. Components declare no local_frame_id on purpose: there is no authored frame tree to
    name one (see produce_mechanical_requirements_root_frame_status); naming a missing frame
    would be a guess the adapter records as component_frame_missing rather than a silent fix.
    """
    components: list[dict[str, Any]] = []
    mass_claims: list[dict[str, Any]] = []
    seen_bodies: set[str] = set()

    for rec in _physiology_records(anatomy_doc):
        body = (rec.get("body") or "").strip()
        if not body or body in seen_bodies:
            continue
        seen_bodies.add(body)
        mass_status = derive_mass_status(rec.get("mass_kind"), rec.get("status"))
        ref = f"anatomy:{label}:physiology:{body}"
        components.append({
            "component_id": f"seg-{body}",
            "kind": KIND_RIGID_BODY,
            # No local_frame_id: no authored root frame exists (documented in the report +
            # prepared_root_frame_definition.json). The adapter records this honestly.
            "local_frame_id": None,
            # No inline mass on ANY component. Nothing here is reconstructed/validated, so no
            # component may claim a validated-tissue mass; pelvis's 11.777 kg root-reference
            # quantity must NOT be turned into declared_massless (that would drop it from the
            # uncounted sum). The true masses live in the ledger as uncounted/unvalidated.
            "mass": None,
        })
        # Root-reference (pelvis) is an authored zero-placement reference quantity; the eight
        # transported segments are source-effective under a density assumption. Neither counts.
        reason = ("root reference frame only: identity scale carries the original mass as a "
                  "reference-frame quantity; it does not measure or validate pelvis size") \
            if mass_status == MASS_ROOT_REFERENCE else (
            "transported source-effective mass under a uniform density-scale assumption; it is "
            "excluded from the component-mass sum so the same matter is never counted twice and "
            "is never promoted to validated tissue mass here")
        mass_claims.append({
            "claim_ref": ref,
            "component_id": f"seg-{body}",
            "counts_toward_component_mass": False,
            "assert_mass_status": mass_status,
            "reason": reason,
        })

    return {
        "schema_version": OWNERSHIP_SCHEMA,
        "_intent": ("AUTHORED ownership binding for the real anatomy packet. Every matter "
                    "representation is owned by exactly one component; transported and "
                    "root-reference mass are declared but never counted or validated, so the "
                    "membrane/body double-count boundary is authored, not inferred."),
        "_frame_status": ("components intentionally declare no local_frame_id: no authored root "
                          "frame exists in the packet (see prepared_root_frame_definition.json); "
                          "the adapter records component_frame_missing rather than inventing one."),
        "components": components,
        "mass_claims": mass_claims,
    }


# --------------------------------------------------------------------------- #
# 2. material_volume_document — cannot be produced honestly                    #
# --------------------------------------------------------------------------- #
def produce_material_volume_report(anatomy_doc: dict[str, Any]) -> dict[str, Any]:
    """Record exactly why a reconstructed material-volume partition is not authorable.

    The segments carry bounding-box `scale`, `fitted_origin` and `frame_basis` only — no
    tetrahedral / vertex geometry for tools/material_volume.py to partition, and no declared
    density_source. This producer does NOT invent densities or volumes; it names the missing
    inputs at their field paths so a human (Astra) can supply them.
    """
    segs = _segment_tree(anatomy_doc)
    bodies_with_scale = [s.get("source_body") for s in segs
                         if isinstance(s.get("scale"), list)]
    return {
        "producer": TOOLS_PREFIX + "produce_inputs.py::produce_material_volume_report",
        "verdict": "cannot_produce",
        "required_role": "material_volume_document",
        "why_not_authorable": (
            "the anatomy segments carry only a bounding-box scale, a fitted_origin and a "
            "frame_basis; there is no tetrahedral/vertex geometry for tools/material_volume.py "
            "to partition and no declared density_source. Producing reconstructed_tissue_volume "
            "here would invent densities/volumes and violate the density-source invariant."),
        "evidence": {
            "segments_present": len(segs),
            "segment_bodies_with_scale": sorted({b for b in bodies_with_scale if b}),
            "tetrahedral_geometry_declared": False,
            "density_source_declared": False,
            "missing_fields": [
                "material_volume_document.json:reconstructed_material_volume (a partition whose "
                "regions carry a declared density_source)",
                "material_volume_document.json:*.region.density_source",
                "material_volume_document.json:*.region.vertices|tetrahedra",
            ],
        },
        "what_astra_must_supply": (
            "a reconstructed material-volume partition (tools/material_volume.py v1) whose "
            "regions carry declared tetrahedral geometry AND a declared density_source; the only "
            "thing that can turn this packet's geometry into validated tissue mass and inertia."),
    }


# --------------------------------------------------------------------------- #
# 3. mechanical_requirements — cannot be produced honestly                     #
# --------------------------------------------------------------------------- #
def _declares_root_frame(segs: list[dict[str, Any]]) -> bool:
    """A segment tree has an authored root only if some segment declares parent=null."""
    return any(s.get("parent") is None for s in segs)


def produce_mechanical_requirements_report(
        anatomy_doc: dict[str, Any], candidates_doc: dict[str, Any] | None) -> dict[str, Any]:
    """Record exactly why an authored mechanical-requirements document is not authorable.

    The attachment candidates carry a resolved `source_pos_local` but no patch_area_m2, areal
    stiffness, minimum couple stiffness or weights; and the segment tree declares no authored
    root frame (no segment has parent=null; pelvis — the natural root — is not itself a
    segment). Producing those values would invent mechanical assumptions + an alignment nobody
    authored. This producer records exactly what each port is missing instead.
    """
    segs = _segment_tree(anatomy_doc)
    bodies = (candidates_doc or {}).get("bodies") or {} if isinstance(candidates_doc, dict) else {}
    ports: list[dict[str, Any]] = []
    if isinstance(bodies, dict):
        for body in sorted(bodies):
            body_row = bodies.get(body) or {}
            for i, cand in enumerate(body_row.get("candidates") or []):
                roles = (cand.get("endpoint_roles") or []) + [
                    m.get("role") for m in (cand.get("tendon_membership") or [])]
                if any(str(r).strip() and not str(r).startswith("waypoint") for r in roles):
                    ports.append({
                        "port_id": cand.get("site_id"),
                        "source_body": body,
                        "mechanical_qualification": cand.get("mechanical_qualification"),
                        "has_source_pos_local": isinstance(cand.get("source_pos_local"), list),
                        "missing_parameters": [
                            "patch_area_m2", "kappa_areal_n_m3",
                            "k_couple_min_n_m_per_rad", "weights",
                            "anchor_frame_id (bound authored root frame)",
                            "endpoints[*].local_frame_id (bound authored frame)"],
                    })
    return {
        "producer": TOOLS_PREFIX + "produce_inputs.py::produce_mechanical_requirements_report",
        "verdict": "cannot_produce",
        "required_role": "mechanical_requirements",
        "why_not_authorable": (
            "the candidates carry a resolved source_pos_local but no patch_area_m2, areal "
            "stiffness, minimum couple stiffness or weights; and the segment tree declares no "
            "authored root frame. Producing those values would invent mechanical assumptions and "
            "an alignment nobody authored."),
        "evidence": {
            "segment_tree_declares_root_frame": _declares_root_frame(segs),
            "natural_root_is_a_segment": any(
                s.get("source_body") == "pelvis" for s in segs),
            "ports_identified": len(ports),
        },
        "ports_missing_parameters": ports,
        "what_astra_must_supply": (
            "an authored mechanical-requirements document: the assembly frame tree with exactly "
            "one authored root frame declaring parent_frame_id null plus origin_m/basis_rows/"
            "scale_to_m, and per attachment its anchors, weights, patch_area_m2, kappa_areal_n_m3 "
            "and k_couple_min_n_m_per_rad."),
    }


# --------------------------------------------------------------------------- #
# 4. prepared_root_frame_definition — requires Astra, never silently authored   #
# --------------------------------------------------------------------------- #
def _natural_root(segs: list[dict[str, Any]]) -> str | None:
    """A parent that no segment itself declares is the assembly's natural root.

    pelvis is referenced as `parent` by femur_r/l and thorax_dummy but is not itself a
    segment in this packet; every segment has a non-null parent, so nothing authored ties
    any frame to an assembly root. Returns that dangling-root name, or None if there is no
    single natural root.
    """
    bodies = {s.get("source_body") for s in segs}
    parents = [s.get("parent") for s in segs]
    roots = sorted({p for p in parents if p not in bodies and p is not None})
    return roots[0] if len(roots) == 1 else None


def produce_root_frame_definition(anatomy_doc: dict[str, Any]) -> dict[str, Any]:
    """The EXACT root-frame definition the assembly root must carry — authored by Astra.

    No documented source transform uniquely establishes the assembly root: no segment declares
    parent=null, and the packet's segment tree is a FOREST of disconnected components whose
    roots are referenced but never themselves segments (see disconnected_component_roots).
    The adapter will NOT silently insert an identity transform or infer alignment from the
    child segments' fitted origins. Instead it records precisely what the root frame(s) must
    declare, consuming the packet's own coordinate conventions as evidence (not deriving a
    pose from them).
    """
    segs = _segment_tree(anatomy_doc)
    meta = anatomy_doc.get("meta") or {}
    conv = meta.get("coordinate_conventions") or {}
    bodies = {s.get("source_body") for s in segs}
    parents = [s.get("parent") for s in segs]
    disconnected = sorted({p for p in parents if p not in bodies and p is not None})
    root = _natural_root(segs)  # single natural root, or None when the forest has several
    return {
        "producer": TOOLS_PREFIX + "produce_inputs.py::produce_root_frame_definition",
        "verdict": "requires_astra_authorship",
        "required_role": "mechanical_requirements.frames[0]",
        "why_not_derivable": (
            "no segment declares parent_frame_id null and the packet's segment tree is a forest "
            "of disconnected components; every referenced-but-unsegmented parent is a dangling "
            "root, so no authored transform places any frame at an assembly root. The child "
            "segments' fitted_origin/frame_basis are relative to their own parents, not to a "
            "root. This adapter will not insert an identity transform or infer the root pose from "
            "them."),
        "natural_root_frame_id": root,
        "disconnected_component_roots": disconnected,
        "consumed_evidence": {
            "coordinate_unit_from_meta_units": meta.get("units"),
            "handedness_from_conventions": conv.get("handedness"),
            "axis_vectors_from_conventions": {k: conv.get(k) for k in ("up", "anterior", "right")},
        },
        "frame_definition_requires_astra": {
            "frame_id": root,
            "parent_frame_id": None,
            "coordinate_unit": meta.get("units"),
            "handedness": conv.get("handedness"),
            "scale_to_m": None,
            "origin_m": None,
            "basis_rows": None,
        },
        "each_value_needs_astra": {
            "parent_frame_id=null": ("the assembly root must declare exactly one null parent; no segment in the packet does, so this is an authored decision rather than a derived one"),
            "coordinate_unit": ("the frame's length unit must be authored — the adapter reads meta.units as evidence only and will not assume metres"),
            "handedness": ("the frame chirality must be authored; handedness in meta is convention, not a pose constraint on the root basis rows"),
            "scale_to_m": ("a non-unity scale rescales every child frame, so it must be explicitly authored rather than inferred from the children's fitted scales"),
            "origin_m": ("the root origin has no authored value; deriving it from a child fitted_origin would be an alignment the adapter refuses to invent"),
            "basis_rows": ("the three orthonormal axis vectors have no authored value and cannot be reconstructed from child frames without assuming alignment"),
        },
    }


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_bytes().decode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out-dir", default=str(HERE / "inputs"))
    p.add_argument("--anatomy", default=None, help="path to actual_monkey_fit.json (default: real packet)")
    p.add_argument("--candidates", default=None, help="path to attachment_candidates.json (default: real packet)")
    args = p.parse_args(argv)

    runs = Path(__file__).resolve().parents[2] / ".tmp" / "anatomy_compiler" / "runs"
    anatomy_path = Path(args.anatomy) if args.anatomy else runs / "actual_monkey_fit.json"
    candidates_path = Path(args.candidates) if args.candidates else runs / "attachment_candidates.json"

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    anatomy_doc = _load(anatomy_path)
    label = "actual_monkey_fit"
    candidates_doc = _load(candidates_path) if candidates_path.is_file() else None

    # 1. ownership — authorable, written to disk and consumed by readiness.
    ownership = produce_ownership(anatomy_doc, label)
    own_path = out_dir / "ownership_bindings.json"
    own_path.write_text(json.dumps(ownership, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # 2/3. cannot-produce artifacts — evidence for the report, NOT authored inputs.
    mv_report = produce_material_volume_report(anatomy_doc)
    (out_dir / "material_volume_document.cannot_produce.json").write_text(
        json.dumps(mv_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    mech_report = produce_mechanical_requirements_report(anatomy_doc, candidates_doc)
    (out_dir / "mechanical_requirements.cannot_produce.json").write_text(
        json.dumps(mech_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # 4. prepared root-frame definition — requires Astra authorship; never silently authored.
    root_frame = produce_root_frame_definition(anatomy_doc)
    (out_dir / "prepared_root_frame_definition.json").write_text(
        json.dumps(root_frame, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Console summary.
    print(f"anatomy packet : {display(anatomy_path)}  ({len(_physiology_records(anatomy_doc))} bodies)")
    print(f"candidates     : {display(candidates_path)} "
          f"({mech_report['evidence']['ports_identified']} ports identified)")
    print(f"\nownership_bindings.json        -> {own_path.name} "
          f"(len={len(ownership['components'])} components, {len(ownership['mass_claims'])} claims)")
    statuses = {}
    for c in ownership["mass_claims"]:
        statuses[c["assert_mass_status"]] = statuses.get(c["assert_mass_status"], 0) + 1
    print(f"  mass-status histogram: {json.dumps(statuses, sort_keys=True)}")
    print(f"  all counts_toward_component_mass=false -> "
          f"{all(not c['counts_toward_component_mass'] for c in ownership['mass_claims'])}")
    print(f"\nmaterial_volume_document.cannot_produce.json -> {mv_report['verdict']}")
    print(f"mechanical_requirements.cannot_produce.json  -> {mech_report['verdict']} "
          f"({mech_report['evidence']['ports_identified']} ports, root_frame={mech_report['evidence']['segment_tree_declares_root_frame']})")
    print(f"prepared_root_frame_definition.json      -> {root_frame['verdict']} "
          f"(natural_root={root_frame['natural_root_frame_id']!r})")
    return 0


def display(path: Path) -> str:
    try:
        return path.relative_to(Path(__file__).resolve().parents[2]).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
