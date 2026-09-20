"""Build the four pre-registered creature/data BUNDLES from pinned measured files.

Every number a bundle carries is READ from the repo's committed receipts
(no hand-typed measurements): the v3 bone arbiter, the mesh manifests, the
mount-reconciliation scales, and the walker's derived_numbers.json. The one
synthesized bundle (the chimera) is explicitly a developer construction and
says so in its own provenance strings.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tools" / "creature_graph")]

import reality_gate as rg  # noqa: E402

BUNDLE_SCHEMA = rg.BUNDLE_SCHEMA

INFANT_ARBITER = rg.PINNED["infant_arbiter_v3"]
ADULT_NUMBERS = rg.PINNED["adult_table1"]
RECONCILIATION = ROOT / "tools" / "science_funnel" / "validation" / "mount_reconciliation_20260919" / "reconciliation.json"

SPEC_A = "000875604"
SPEC_B = "000875599"

INFANT_STAGE_A = {
    "label": "infant",
    "provenance": "MorphoSource CT 000875604, Macaca mulatta USNM 497136-3, infant, 160um "
                  "(tools/science_funnel/data/morphosource_ct/meshes/manifest.json source field)",
    "confirmed": True,
}
INFANT_STAGE_B = {
    "label": "infant",
    "provenance": "MorphoSource CT 000875599, Macaca mulatta USNM 497135, 160um "
                  "(tools/science_funnel/data/morphosource_ct/mesh_receipt_875599.json)",
    "confirmed": True,
}
ADULT_STAGE_TABLE1 = {
    "label": "adult",
    "provenance": "Oku, Ide, Ogihara et al. 2021, Communications Biology PMC7940622: adult female Japanese "
                  "macaque musculoskeletal model, Table-1 (tools/science_funnel/validation/"
                  "gait_controller_20260918/derived_numbers.json body_model)",
    "confirmed": True,
}


def _bones_components(spec_id, spec, stage):
    out = []
    for b in spec["bones"]:
        if not b.get("segment_label"):
            continue
        out.append({
            "id": "%s_bone_%d" % (spec_id, b["rank"]),
            "kind": "anatomy",
            "segment_label": b["segment_label"],
            "stage": stage,
            "species": "Macaca mulatta",
            "length_mm": b["length_mm"],
            "elongation": b.get("elongation"),
            "confidence": b.get("confidence"),
            "source": "chimera.ct_bone_identification.v3 (%s)" % spec_id,
        })
    return out


def _chain_ratios_with_overrides(spec, scale_overrides):
    """Bundle's own measured chain-level ratios; `scale_overrides` maps rank ->
    multiplier applied to that bone's length (the chimera's construction)."""
    bones = {str(b["rank"]): b for b in spec["bones"]}
    def L(rank):
        b = bones[str(rank)]
        return b["length_mm"] * scale_overrides.get(rank, 1.0)
    ratios, origins = {}, {}
    hinds, fores = [], []
    for chain in spec.get("chains", []):
        labels = chain.get("labels", {})
        fem = [m for m, lb in labels.items() if lb == "femur"]
        tib = [m for m, lb in labels.items() if lb == "tibia"]
        hum = [m for m, lb in labels.items() if lb == "humerus"]
        fclass = [m for m, lb in labels.items() if lb == "forearm_class"]
        if fem and tib:
            hinds.append((fem[0], tib[0]))
        if hum and fclass:
            fores.append((hum[0], fclass))
    for hf, tf in hinds:
        key = "femur:tibia"
        ratios.setdefault(key, []).append(L(hf) / L(tf))
        origins.setdefault(key, []).append("ranks %d/%d" % (int(hf), int(tf)))
    for hu, fa in fores:
        fam = sum(L(m) for m in fa) / len(fa)
        key = "humerus:forearm"
        ratios.setdefault(key, []).append(L(hu) / fam)
        origins.setdefault(key, []).append("rank %d vs mean %s" % (int(hu), [int(m) for m in fa]))
    for hf, tf in hinds:
        for hu, fa in fores:
            fam = sum(L(m) for m in fa) / len(fa)
            for key, num, den in (("humerus:femur", L(hu), L(hf)), ("forearm:tibia", fam, L(tf))):
                ratios.setdefault(key, []).append(num / den)
                origins.setdefault(key, []).append("ranks %d/%d" % (int(hu) if key == "humerus:femur" else int(fa[0]), int(hf if key == "humerus:femur" else tf)))
    return ratios, origins


def _mean_ratios(ratios, origins):
    out = {}
    for k, vals in ratios.items():
        out[k] = {"value": sum(vals) / len(vals), "n": len(vals),
                  "from": ["bundle chains: " + o for o in origins[k]],
                  "source": "chimera.ct_bone_identification.v3 chain lengths (pose-free within-bundle ratios)"}
    return out


def bundle_a_infant_ct():
    spec = _load(INFANT_ARBITER)["specimens"][SPEC_A]
    return {
        "schema": BUNDLE_SCHEMA,
        "name": "infant_ct_specimen_000875604",
        "description": "the first reality creature: a stage-true infant Macaca mulatta, measured, not constructed",
        "species": [{"name": "Macaca mulatta",
                     "provenance": "mesh_receipt.json source_ct Macaca_mulatta-USNM497136-3-160um-000875604.tif; pinned NCBI taxdmp extract tax_id 9544"}],
        "components": _bones_components(SPEC_A, spec, INFANT_STAGE_A),
        "allometry": {
            "stage": "infant",
            "expectation_exclusions": [SPEC_A],
            "ratios": _mean_ratios(*_chain_ratios_with_overrides(spec, {})),
        },
    }


def bundle_b_h2_mount():
    recon = _load(RECONCILIATION)
    arbiter = _load(INFANT_ARBITER)
    spec = arbiter["specimens"][SPEC_A]
    h2 = recon["h2_per_bone"]["generalized"]
    scales = {}
    for group in ("femur_mounts", "tibia_mounts", "foot_mounts"):
        for rank, m in sorted(h2[group].items(), key=lambda kv: int(kv[0])):
            scales[int(rank)] = m["scale"]
    scaffold = recon["h2_per_bone"]["scaffold"]
    components = []
    for rank in sorted(scales):
        bone = next(b for b in spec["bones"] if b["rank"] == rank)
        components.append({
            "id": "h2_bone_%d" % rank,
            "kind": "anatomy",
            "segment_label": bone["segment_label"],
            "stage": INFANT_STAGE_A,
            "species": "Macaca mulatta",
            "length_mm": bone["length_mm"],
            "mount_scale_factor": scales[rank],
            "source": "chimera.ct_bone_identification.v3 rank %d; scale from mount_reconciliation_20260919/reconciliation.json h2_per_bone.generalized" % rank,
        })
    for seg, length_m in sorted(scaffold["segments_m"].items()):
        components.append({
            "id": "h2_scaffold_%s" % seg,
            "kind": "scaffold_segment",
            "segment_label": seg,
            "stage": ADULT_STAGE_TABLE1,
            "species": "Macaca fuscata",
            "length_m": length_m,
            "source": "mount_reconciliation_20260919/reconciliation.json h2_per_bone.scaffold (Table-1 derived)",
        })
    return {
        "schema": BUNDLE_SCHEMA,
        "name": "h2_per_bone_scaffold_mounting",
        "description": "infant CT bones per-bone-scaled onto the adult Table-1 standing scaffold "
                       "(the mounting lane's H2, the operator's 'adult arms on a baby' case, already measured)",
        "species": [
            {"name": "Macaca mulatta", "provenance": "the CT bones (specimen 000875604)"},
            {"name": "Macaca fuscata", "provenance": "the Table-1 scaffold (Oku/Ogihara 2021 adult female Japanese macaque model)"},
        ],
        "components": components,
        "allometry": {
            "stage": "infant",
            "expectation_exclusions": [SPEC_A],
            "per_bone_scale_factors": {("h2_bone_%d" % r): s for r, s in sorted(scales.items())},
            "reference_uniform_scale": recon["scale_conflict"]["h1_scale_scene_per_mm"],
            "reference_uniform_scale_source": "mount_reconciliation_20260919/reconciliation.json scale_conflict: trunk-anchored rigid scale (HAT/trunk_PCA_span)",
        },
        "fantasy_manifest_acknowledged": True,
        "construction_provenance": "explicit developer construction (agent/mount-reconciliation lane): "
                                   "per-bone scale = adult Table-1 segment length / infant joint span; "
                                   "classified FANTASY would be the honest verdict of the reconciliation itself",
    }


def bundle_c_walker():
    d = _load(ADULT_NUMBERS)
    body = d["body_model"]
    seg = body["segments_Table1"]
    before = d["oku_before_alteration"]
    janisch = d["janisch_cercopithecoids"]["stats"]
    weight = body["weight_N"]
    # measured closures from the walker's own banked numbers:
    per_drive_sum = sum(v["positive_J_at_10kg"] for v in d["per_drive_budget_check_J"].values())
    impulse_closure = before["grf_v_mean_stance_N"] * before["stance_dur_s"]
    components = []
    for name, s in sorted(seg.items()):
        components.append({
            "id": "walker_segment_%s" % name,
            "kind": "anatomy",
            "segment_label": name.lower(),
            "stage": ADULT_STAGE_TABLE1,
            "species": "Macaca fuscata",
            "length_m": s["length_m"],
            "mass_kg": s["mass_kg"],
            "source": "derived_numbers.json body_model.segments_Table1",
        })
    return {
        "schema": BUNDLE_SCHEMA,
        "name": "walker_table1_adult",
        "description": "the walker: the adult Japanese macaque model the physics already uses (Table-1 proportions, literature stage)",
        "species": [{"name": "Macaca fuscata",
                     "provenance": "PMC7940622 (Oku/Ide/Ogihara 2021); pinned NCBI taxdmp extract tax_id 9542"}],
        "components": components,
        "allometry": {
            "stage": "adult",
            "expectation_exclusions": [],
            "ratios": {
                "thigh:shank": {"value": seg["thigh"]["length_m"] / seg["shank"]["length_m"],
                                "from": ["segments_Table1"], "source": "derived_numbers.json"},
                "shank:thigh": {"value": seg["shank"]["length_m"] / seg["thigh"]["length_m"],
                                "from": ["segments_Table1"], "source": "derived_numbers.json"},
                "thigh:HAT": {"value": seg["thigh"]["length_m"] / seg["HAT"]["length_m"],
                              "from": ["segments_Table1"], "source": "derived_numbers.json"},
                "shank:HAT": {"value": seg["shank"]["length_m"] / seg["HAT"]["length_m"],
                              "from": ["segments_Table1"], "source": "derived_numbers.json"},
                "foot:HAT": {"value": seg["foot"]["length_m"] / seg["HAT"]["length_m"],
                             "from": ["segments_Table1"], "source": "derived_numbers.json"},
            },
        },
        "physics_bars": [
            {"law": "conservation",
             "verdict": "pass" if abs(per_drive_sum / before["work_positive_total_J"] - 1.0) <= 0.15 else "fail",
             "measured": {"work_positive_total_J": before["work_positive_total_J"],
                          "per_drive_budget_sum_J": round(per_drive_sum, 4),
                          "closure_deviation_frac": per_drive_sum / before["work_positive_total_J"] - 1.0},
             "falsifier": "per-drive positive work must sum to the banked total positive work within the 15% house band",
             "source": "derived_numbers.json oku_before_alteration.work_positive_total_J + per_drive_budget_check_J"},
            {"law": "pose",
             "verdict": "pass" if janisch["hipExcur"]["min"] <= before["angles"]["hip"]["excursion_deg"] <= janisch["hipExcur"]["max"] else "fail",
             "measured": {"hip_excursion_deg": before["angles"]["hip"]["excursion_deg"],
                          "cercopithecoid_cohort_min_deg": janisch["hipExcur"]["min"],
                          "cercopithecoid_cohort_max_deg": janisch["hipExcur"]["max"],
                          "cercopithecoid_cohort_mean_deg": janisch["hipExcur"]["mean"],
                          "n_strides": janisch["hipExcur"]["n"]},
             "falsifier": "simulated hip excursion must land inside the measured cercopithecoid cohort range (145 wild-primate strides, janisch_kinematics)",
             "source": "derived_numbers.json oku_before_alteration.angles.hip + janisch_cercopithecoids.stats.hipExcur"},
            {"law": "touch",
             "verdict": "pass" if abs(impulse_closure / before["grf_v_impulse_Ns"] - 1.0) <= 0.15 else "fail",
             "measured": {"grf_v_impulse_Ns": before["grf_v_impulse_Ns"],
                          "mean_stance_N_x_stance_dur_s": round(impulse_closure, 4),
                          "closure_deviation_frac": impulse_closure / before["grf_v_impulse_Ns"] - 1.0,
                          "grf_v_peak_xBW": before["grf_v_peak_xBW"], "weight_N": weight},
             "falsifier": "vertical impulse must equal mean stance force x stance duration within the 15% house band",
             "source": "derived_numbers.json oku_before_alteration GRF block"},
        ],
        "named_circularity": "the adult allometry table IS this bundle's source (Oku/Ogihara Table-1): this adjudication certifies provenance + coherence, not independent adult replication; an independent adult forelimb reference is OPEN",
    }


def bundle_d_chimera():
    spec = _load(INFANT_ARBITER)["specimens"][SPEC_A]
    recon = _load(RECONCILIATION)
    femur_rule = recon["h2_per_bone"]["as_committed"]["femur_mounts"]["2"]["scale"]
    forelimb_ranks = {4, 5, 8, 9, 10, 11, 12, 13}
    constructed_stage = {
        "label": "adult",
        "provenance": "developer construction (this lane): forelimb stretched by the committed compiler's own "
                      "femur mount rule factor %.4f (163.0mm Table-1 thigh / 42.7336mm infant femur joint span); "
                      "no measurement confirms any adult anatomy here" % femur_rule,
        "confirmed": False,
    }
    components = []
    for b in spec["bones"]:
        if not b.get("segment_label"):
            continue
        if b["rank"] in forelimb_ranks:
            components.append({
                "id": "chimera_bone_%d" % b["rank"], "kind": "anatomy",
                "segment_label": b["segment_label"], "stage": constructed_stage,
                "species": "Macaca mulatta", "length_mm": b["length_mm"] * femur_rule,
                "construction": "infant rank %d stretched x%.4f and relabeled adult" % (b["rank"], femur_rule),
                "source": "chimera.ct_bone_identification.v3 rank %d, constructed in build_bundles.py" % b["rank"],
            })
        else:
            components.append({
                "id": "chimera_bone_%d" % b["rank"], "kind": "anatomy",
                "segment_label": b["segment_label"], "stage": INFANT_STAGE_A,
                "species": "Macaca mulatta", "length_mm": b["length_mm"],
                "source": "chimera.ct_bone_identification.v3 rank %d" % b["rank"],
            })
    overrides = {str(r): femur_rule for r in forelimb_ranks}
    ratios, origins = _chain_ratios_with_overrides(spec, overrides)
    return {
        "schema": BUNDLE_SCHEMA,
        "name": "chimera_adult_forelimb_on_infant",
        "description": "deliberate chimera: adult-proportioned forelimbs on the stage-true infant bundle "
                       "(synthesized for this adjudication; the user's RIGHT, classified honestly)",
        "species": [{"name": "Macaca mulatta",
                     "provenance": "all bones derive from infant CT specimen 000875604"}],
        "components": components,
        "allometry": {
            "stage": "infant",
            "expectation_exclusions": [SPEC_A],
            "ratios": _mean_ratios(ratios, origins),
        },
        "fantasy_manifest_acknowledged": True,
        "construction_provenance": "explicit developer construction (build_bundles.py): the operator's example class - "
                                   "a half-adult half-baby animal is buildable, and the gate must SAY it violates "
                                   "the laws of nature, itemized",
    }


def _load(path):
    with open(path, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


BUNDLES = {
    "a_infant_ct": bundle_a_infant_ct,
    "b_h2_mount": bundle_b_h2_mount,
    "c_walker": bundle_c_walker,
    "d_chimera": bundle_d_chimera,
}


def main():
    for key, fn in sorted(BUNDLES.items()):
        out = HERE / ("%s_bundle.json" % key)
        out.write_text(json.dumps(fn(), indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print("wrote", out)


if __name__ == "__main__":
    main()
