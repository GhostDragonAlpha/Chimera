"""Join reference data to the creature graph -- EXPLICIT MAPPINGS ONLY.

Automatic joins happen only on stable ids or explicit mapping records. Name
similarity between a creature object and a reference entity produces a
CANDIDATE mapping record that asserts NOTHING: confirming, rejecting, or
acting on it is an explicit adaptation decision (req.sealed_design_is_chimera).

Creature-side mapping kinds:
  candidate  -- name-token match, meaning unknown
  analogue   -- the creature part is an ENGINEERED analogue of the reference
                anatomy (e.g. the thigh compartment is not a human femur); it
                may inform shape/ratios, never identity
"""

import re


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z]+", (text or "").lower()) if len(t) > 3}


# creature segment -> reference-side join intent (explicit, authored table:
# which reference datasets even MAY be joined to which creature objects)
JOIN_INTENT = {
    "seg.thigh_l": {"anatomical_tokens": ["thigh", "femur"],
                    "osim_bodies": ["femur_r"],
                    "mapping_type": "analogue"},
    "seg.shin_l": {"anatomical_tokens": ["shank", "tibia", "fibula", "crus"],
                   "osim_bodies": ["tibia_r"],
                   "mapping_type": "analogue"},
    "seg.foot_l": {"anatomical_tokens": ["foot", "pes", "tarsal", "metatarsal",
                                         "phalanx", "calcaneus", "talus"],
                   "osim_bodies": ["talus_r", "calcn_r", "toes_r"],
                   "mapping_type": "analogue"},
}


def candidate_mappings(g, ref_objects) -> list:
    """Deterministic creature-side mapping records. Returns mapping objects;
    each carries _edges [(src, rel, dst, note)] for the builder to relate."""
    by_id = {o["id"]: o for o in ref_objects}
    uberon_by_token = {}
    osim_by_name = {}
    for o in ref_objects:
        if o["kind"] != "reference_entity":
            continue
        if o["id"].startswith("ref.uberon."):
            for t in _tokens(o.get("name") or ""):
                uberon_by_token.setdefault(t, []).append(o["id"])
        elif o["id"].startswith("ref.osim.") and ".body." in o["id"]:
            short = o["id"].rsplit(".", 1)[-1]
            osim_by_name[short] = o["id"]
    out = []
    for seg_id, intent in JOIN_INTENT.items():
        if seg_id not in g.objects:
            continue
        seg = g.get(seg_id)
        seg_tokens = _tokens(seg.get("name") or "")
        # uberon candidates: exact token match on the authored join table
        for tok in intent["anatomical_tokens"]:
            for ub_id in sorted(uberon_by_token.get(tok, []))[:2]:
                mid = f"map.creature.{seg_id}__{ub_id.replace('ref.', '')}"
                out.append({
                    "id": mid, "kind": "mapping",
                    "name": f"CANDIDATE: {seg_id} ~ {ub_id} (token '{tok}')",
                    "classification": None, "status": "extracted",
                    "priority": None, "build_rank": None,
                    "inventory_anchor": None, "spatial": None,
                    "geometry": None, "physical": None, "attachments": [],
                    "dependencies": [], "evidence": [], "falsifier": {},
                    "mapping_type": intent["mapping_type"],
                    "meaning": "name-token match against the authored join "
                               "table; a CANDIDATE, never an equivalence. The "
                               "creature segment is an ENGINEERED structure "
                               "inside a sealed compartment design -- reference "
                               "anatomy informs, never defines.",
                    "left": seg_id, "right": ub_id,
                    "unknowns": [],
                    "notes": "similar names produce candidates, not automatic "
                             "equivalences",
                    "provenance": {"source_id": "join:creature+uberon",
                                   "rule": "authored join table + exact token"},
                    "_edges": [
                        (seg_id, "derived_from", ub_id,
                         "candidate mapping (provenance citation, not equivalence)"),
                    ],
                })
        # osim body candidates (reference geometry/parameter side)
        for body in intent["osim_bodies"]:
            if body not in osim_by_name:
                continue
            osim_id = osim_by_name[body]
            mid = f"map.creature.{seg_id}__{osim_id.replace('ref.', '')}"
            out.append({
                "id": mid, "kind": "mapping",
                "name": f"CANDIDATE: {seg_id} ~ {osim_id}",
                "classification": None, "status": "extracted", "priority": None,
                "build_rank": None, "inventory_anchor": None, "spatial": None,
                "geometry": None, "physical": None, "attachments": [],
                "dependencies": [], "evidence": [], "falsifier": {},
                "mapping_type": intent["mapping_type"],
                "meaning": "human reference body vs engineered creature segment; "
                           "shape/parameter REFERENCE only (human proportions "
                           "are NOT Chimera proportions)",
                "left": seg_id, "right": osim_id,
                "unknowns": [],
                "notes": "explicit mapping record; selecting any OpenSim "
                         "parameter for the creature is a separate adaptation "
                         "decision with applicability + validation",
                "provenance": {"source_id": "join:creature+opensim",
                               "rule": "authored join table"},
                "_edges": [
                    (seg_id, "derived_from", osim_id,
                     "candidate mapping (provenance citation, not equivalence)"),
                ],
            })
    return out
