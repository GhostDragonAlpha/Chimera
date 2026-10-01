"""Reality/fantasy adjudicator -- THE TWO-CATEGORY LAW, measured.

THE LAWS (operator-banked, verbatim in validation/reality_gate_20260920/receipt.json):

  THE BIOLOGICAL LAW -- no life-stage mixing. (a) one creature, one life stage;
  (b) allometric coherence: segment proportions must match the stage's scaling
  laws; (c) stage labels are ADMISSION-REQUIRED for anatomy data (adult must be
  adult-CONFIRMED, like sha256); (d) a stage-true baby creature is VALID.

  THE TWO-CATEGORY LAW -- REALITY (follows the laws) and FANTASY (chimeras,
  developer-driven explicit construction, never accidental data mixing).
  REALITY FIRST: reality is the reference; everything else is fantasy BY
  DEFAULT (measured deviation).

  THE GATE OUTPUT LAW -- gates CLASSIFY, not just refuse:
  {category: reality|fantasy, violations: [...]}; violations are itemized and
  NEVER silent; the fantasy construction mode requires acknowledging the
  manifest.

Design contract:
  * Every check is a NAMED LAW with a MEASURED verdict. A check that cannot
    measure the law it names refuses (never a vibes-verdict).
  * Physics bars reuse the EXISTING aliveness-law vocabulary -- conservation /
    pressure / pose / touch (A1/A2/A3, tools/bring_alive.py) -- and only
    adjudicate bars the bundle carries with numbers. No new physics.
  * Allometry expectations are DERIVED at run time from the pinned measured
    files (never duplicated numbers that can drift): the adult table from the
    walker's Table-1 (Oku/Ogihara 2021 model, gait_controller_20260918), the
    infant table from the two infant CT specimens (v3 arbiter,
    mount_reconciliation_20260919). Leave-one-out is expressed by
    `expectation_exclusions`, so an adjudication of specimen A is judged
    against specimen B (a replication test, not circularity).
  * Tolerance: the house 15% band (the mount-reconciliation chain falsifier).
  * Taxonomic distance uses the pinned NCBI taxdmp extract
    (tools/science_funnel/data/ncbi_taxdmp).
  * Output is deterministic (no wall-clock in the verdict; the receipt owns
    timestamps), so re-runs are byte-identical.

Run:
    python -B tools/creature_graph/reality_gate.py <bundle.json> [-o out.json]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SCHEMA = "chimera.reality_gate.v1"
BUNDLE_SCHEMA = "chimera.creature_bundle.v1"

# The house band: same 15% tolerance the mount-reconciliation chain falsifier
# already banked. One number, already in the repo -- not a new choice.
TOLERANCE_FRAC = 0.15

LAW_STAGES = "stage_consistency"
LAW_ALLOMETRY = "allometric_coherence"
LAW_TAXONOMY = "taxonomic_coherence"
LAW_PHYSICS = "physics_bars"
LAWS = (LAW_STAGES, LAW_ALLOMETRY, LAW_TAXONOMY, LAW_PHYSICS)

# The aliveness bars' vocabulary (A1/A2/A3): conservation = volume/energy
# conserved across import/seal (bring_alive A1), pose = poses travel with
# conservation held under pose (A2), pressure/touch = the press path answers
# with a measured dP/dimple (A3). Wired, not invented.
PHYSICS_BAR_LAWS = ("conservation", "pressure", "pose", "touch")

PINNED = {
    "infant_arbiter_v3": ROOT / "tools/science_funnel/validation/mount_reconciliation_20260919/bone_identification_v3.json",
    "adult_table1": ROOT / "tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json",
    "tax_nodes": ROOT / "tools/science_funnel/data/ncbi_taxdmp/macaca_nodes.tsv",
    "tax_names": ROOT / "tools/science_funnel/data/ncbi_taxdmp/macaca_names.tsv",
}

# Stage-level literature entries. `status` is honest about provenance:
#   pinned-bytes       -- derivable from files sha-pinned in this repo
#   provisional-derived -- derivation stated below; NOT a bare guess, NOT pinned
# These are gated ONLY when the bundle carries the corresponding measurement.
STAGE_LEVEL_ENTRIES = {
    "infant": {
        "body_mass_kg_birth_range": {
            "value": [0.4, 0.55],
            "status": "provisional-derived",
            "sources": [
                "NC3Rs Macaques resource (macaques.nc3rs.org.uk), rhesus birth weight 0.4-0.55 kg, citing Catchpole & van Wagenen (1975)",
                "van Wagenen & Catchpole (1956), Am J Phys Anthropol 14:245-273 (longitudinal growth of Macaca mulatta)",
            ],
        },
        "head_body_ratio_multiplier_vs_adult": {
            "value": 2.42,
            "status": "provisional-derived",
            "derivation": ("brain volume ~64% of adult at ~1 week (Scott et al. 2016, longitudinal rhesus brain MRI) "
                           "=> head linear ~0.64**(1/3)=0.862 of adult under cubic scaling; neonate body mass ~0.45 kg "
                           "vs the pinned adult Table-1 mass 10.038 kg => body linear ~0.045**(1/3)=0.356 of adult; "
                           "ratio multiplier 0.862/0.356=2.42"),
            "sources": ["Scott et al. 2016 (J Neurosci, developing rhesus brain)", "NC3Rs birth mass (above)"],
        },
    },
    "adult": {},
}


class BundleError(Exception):
    """Malformed bundle manifest -- refuse, never classify."""


# ---------------------------------------------------------------------------
# measured expectation tables, derived from pinned bytes (no duplicated truth)
# ---------------------------------------------------------------------------

def _load_json(path):
    with open(path, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def adult_table():
    """MEASURED adult reference: the walker's Table-1 (Oku, Ide, Ogihara et al.
    2021, Communications Biology -- the musculoskeletal model the physics
    already uses). Derives ratios from the pinned derived_numbers.json."""
    d = _load_json(PINNED["adult_table1"])
    seg = d["body_model"]["segments_Table1"]
    mass = d["body_model"]["mass_kg"]
    hat = seg["HAT"]["length_m"]
    ratios = {
        "thigh:shank": seg["thigh"]["length_m"] / seg["shank"]["length_m"],
        "shank:thigh": seg["shank"]["length_m"] / seg["thigh"]["length_m"],
        "thigh:HAT": seg["thigh"]["length_m"] / hat,
        "shank:HAT": seg["shank"]["length_m"] / hat,
        "foot:HAT": seg["foot"]["length_m"] / hat,
        "phalanges:HAT": seg["phalanges"]["length_m"] / hat,
    }
    return {
        "stage": "adult",
        "status": "pinned-bytes",
        "source": "Oku/Ide/Ogihara 2021 Communications Biology Table-1 (tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json)",
        "segments_m": {k: v["length_m"] for k, v in seg.items()},
        "mass_kg": mass,
        "ratios": {k: {"mean": v, "n": 1, "measured_spread_abs": 0.0, "band_frac": TOLERANCE_FRAC}
                   for k, v in ratios.items()},
        # Table-1 folds the forelimbs into HAT (named in
        # mount_reconciliation_20260919): adult cross-limb ratios are NOT
        # gated until a measured adult forelimb reference lands.
        "not_gated": ["forelimb ratios (folded into HAT in the source table)"],
    }


def _specimen_chain_ratios(spec):
    """Per-specimen chain-level segment ratios from the v3 arbiter's chains.

    Chain pairing is the arbiter's own banked anatomy (femur<->tibia in a hind
    chain; humerus + forearm_class bones in a fore chain); this derives
    pose-free, anchor-free WITHIN-bundle ratios from its measured lengths."""
    bones = {str(b["rank"]): b for b in spec["bones"]}
    r = {"femur:tibia": [], "humerus:forearm": [], "humerus:femur": [], "forearm:tibia": []}
    hinds, fores = [], []
    for chain in spec.get("chains", []):
        labels = chain.get("labels", {})
        members = {str(m): bones[str(m)]["length_mm"] for m in chain["members"]}
        femora = [m for m, lb in labels.items() if lb == "femur" and members.get(m)]
        tibiae = [m for m, lb in labels.items() if lb == "tibia" and members.get(m)]
        humeri = [m for m, lb in labels.items() if lb == "humerus" and members.get(m)]
        forearms = [m for m, lb in labels.items() if lb == "forearm_class" and members.get(m)]
        if femora and tibiae:
            hinds.append((femora[0], tibiae[0]))
            r["femur:tibia"].append(members[femora[0]] / members[tibiae[0]])
        if humeri and forearms:
            fores.append((humeri[0], forearms))
            fa = sum(members[m] for m in forearms) / len(forearms)
            r["humerus:forearm"].append(members[humeri[0]] / fa)
    for hf, tf in hinds:
        for hu, _fa in fores:
            r["humerus:femur"].append(bones[hu]["length_mm"] / bones[hf]["length_mm"])
            r["forearm:tibia"].append(
                (sum(bones[m]["length_mm"] for m in _fa) / len(_fa)) / bones[tf]["length_mm"])
    return {k: v for k, v in r.items() if v}


def infant_table(exclusions=()):
    """MEASURED infant reference from the two real infant CT specimens
    (MorphoSource 000875604 / 000875599, Macaca mulatta, 160um). `exclusions`
    names specimens to leave OUT of the expectation (leave-one-out: judging
    specimen A against specimen B is a replication test, not circularity)."""
    d = _load_json(PINNED["infant_arbiter_v3"])
    per_specimen, pooled = {}, {}
    for sid, spec in d["specimens"].items():
        if sid in exclusions:
            continue
        ratios = _specimen_chain_ratios(spec)
        per_specimen[sid] = ratios
        for k, vals in ratios.items():
            pooled.setdefault(k, []).extend(vals)
    table = {}
    for k, vals in pooled.items():
        mean = sum(vals) / len(vals)
        spread = max(max(vals) - mean, mean - min(vals))
        table[k] = {"mean": mean, "n": len(vals), "measured_spread_abs": spread,
                    "band_frac": max(TOLERANCE_FRAC, spread / mean if mean else 0.0)}
    return {
        "stage": "infant",
        "status": "pinned-bytes",
        "source": "two infant CT specimens (tools/science_funnel/validation/mount_reconciliation_20260919/bone_identification_v3.json; meshes manifests)",
        "per_specimen": per_specimen,
        "ratios": table,
        "exclusions": sorted(exclusions),
        "stage_level_entries": STAGE_LEVEL_ENTRIES["infant"],
    }


def stage_table(stage, exclusions=()):
    if stage == "adult":
        t = adult_table()
        t["stage_level_entries"] = STAGE_LEVEL_ENTRIES["adult"]
        return t
    if stage == "infant":
        return infant_table(exclusions)
    raise BundleError("no allometry table for stage %r (tables: adult, infant)" % (stage,))


# ---------------------------------------------------------------------------
# pinned taxonomy (taxonomic distance is MEASURED on the NCBI extract)
# ---------------------------------------------------------------------------

def load_taxonomy():
    """name -> tax_id and tax_id -> parent, from the pinned NCBI extract."""
    nodes, names = {}, {}
    for line in PINNED["tax_nodes"].read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 3:
            nodes[int(parts[0])] = int(parts[1])
    for line in PINNED["tax_names"].read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) >= 4:
            names.setdefault(parts[1], int(parts[0]))
    return nodes, names


def _tax_chain(nodes, tax_id):
    chain, cur = [tax_id], tax_id
    while cur in nodes:
        cur = nodes[cur]
        chain.append(cur)
    return chain


def taxonomic_distance(nodes, names, name_a, name_b):
    """Number of parent edges on the shortest path through the LCA, measured
    on the pinned extract. Raises BundleError if a name is unresolvable."""
    ia, ib = names.get(name_a), names.get(name_b)
    if ia is None or ib is None or ia not in nodes or ib not in nodes:
        raise BundleError("species not resolvable in pinned taxdmp extract: %r/%r" % (name_a, name_b))
    ca, cb = _tax_chain(nodes, ia), _tax_chain(nodes, ib)
    lca = None
    lca_set = set(ca)
    for t in cb:
        if t in lca_set:
            lca = t
            break
    if lca is None:
        raise BundleError("no LCA within pinned taxdmp extract for %r/%r" % (name_a, name_b))
    return ca.index(lca) + cb.index(lca)


# ---------------------------------------------------------------------------
# bundle checks -- each a named law with a measured verdict
# ---------------------------------------------------------------------------

def _violation(law, code, message, measured, **named):
    v = {"law": law, "code": code, "message": message, "measured": measured}
    v.update(named)
    return v


def check_stage_consistency(bundle):
    """BIOLOGICAL LAW (a)+(c): one creature, one life stage; stage labels are
    ADMISSION-REQUIRED (adult must be adult-CONFIRMED)."""
    components = bundle.get("components", [])
    violations, labels = [], {}
    unlabeled, unconfirmed = [], []
    for comp in components:
        stage = comp.get("stage") or {}
        label = stage.get("label")
        cid = comp.get("id", "?")
        if not label:
            unlabeled.append(cid)
            continue
        labels.setdefault(label, []).append(cid)
        if label == "adult" and not (stage.get("confirmed") and stage.get("provenance")):
            unconfirmed.append(cid)
    if unlabeled:
        violations.append(_violation(
            LAW_STAGES, "stage-unlabeled",
            "anatomy data without a stage label is inadmissible (admission-required, like sha256)",
            {"unlabeled_count": len(unlabeled)}, components=unlabeled))
    if len(labels) > 1:
        violations.append(_violation(
            LAW_STAGES, "stage-mixed",
            "one creature, one life stage: stages mixed inside one bundle",
            {"stage_component_counts": {k: len(v) for k, v in sorted(labels.items())}},
            components_by_stage={k: v for k, v in sorted(labels.items())}))
    if unconfirmed:
        violations.append(_violation(
            LAW_STAGES, "adult-unconfirmed",
            "adult stage label requires confirmation with provenance (adult-CONFIRMED, like sha256)",
            {"unconfirmed_count": len(unconfirmed)}, components=unconfirmed))
    measured = {"stage_component_counts": {k: len(v) for k, v in sorted(labels.items())},
                "unlabeled_count": len(unlabeled), "unconfirmed_adult_count": len(unconfirmed)}
    return {"law": LAW_STAGES, "verdict": "violation" if violations else "pass",
            "measured": measured}, violations


def check_allometric_coherence(bundle):
    """BIOLOGICAL LAW (b): segment proportions must match the stage's scaling
    laws. Every deviation is measured per segment against the pinned table."""
    allo = bundle.get("allometry") or {}
    stage = allo.get("stage")
    if not stage:
        return ({"law": LAW_ALLOMETRY, "verdict": "violation",
                 "measured": {"declared_stage": None}},
                [_violation(LAW_ALLOMETRY, "allometry-stage-unlabeled",
                            "allometric coherence cannot be measured without the stage the bundle claims",
                            {"declared_stage": None})])
    table = stage_table(stage, tuple(allo.get("expectation_exclusions", ())))
    violations, measured_segments = [], {}
    for name, entry in sorted((allo.get("ratios") or {}).items()):
        if name not in table["ratios"]:
            violations.append(_violation(
                LAW_ALLOMETRY, "allometry-unmeasurable-expectation",
                "no measured expectation for ratio %r at stage %r -- the gate refuses to emit a vibes-verdict"
                % (name, stage),
                {"ratio": name, "declared_value": entry.get("value")}, segment=name))
            continue
        exp = table["ratios"][name]
        value = entry.get("value")
        dev = (value - exp["mean"]) / exp["mean"]
        measured_segments[name] = {"value": value, "expected_mean": exp["mean"],
                                   "deviation_frac": dev, "band_frac": exp["band_frac"],
                                   "within_band": abs(dev) <= exp["band_frac"],
                                   "from": entry.get("from", [])}
        if abs(dev) > exp["band_frac"]:
            violations.append(_violation(
                LAW_ALLOMETRY, "allometric-deviation",
                "segment ratio %s deviates %.1f%% from the %s scaling table (band %.1f%%)"
                % (name, dev * 100.0, stage, exp["band_frac"] * 100.0),
                measured_segments[name], segment=name))
    scales = allo.get("per_bone_scale_factors") or {}
    ref = allo.get("reference_uniform_scale")
    measured_bones = {}
    if scales:
        if not ref:
            violations.append(_violation(
                LAW_ALLOMETRY, "allometry-unmeasurable-reference",
                "per-bone scale factors declared without the stage-true reference scale -- unmeasurable, refused",
                {"declared_scales": len(scales), "reference_uniform_scale": None}))
        else:
            for bone, scale in sorted(scales.items()):
                dev = scale / ref - 1.0
                measured_bones[bone] = {"scale": scale, "reference_scale": ref,
                                        "deviation_frac": dev,
                                        "within_band": abs(dev) <= TOLERANCE_FRAC}
                if abs(dev) > TOLERANCE_FRAC:
                    violations.append(_violation(
                        LAW_ALLOMETRY, "allometric-scale-incoherence",
                        "per-bone scale %.4f deviates %+.1f%% from the assembly's stage-true scale %.4f "
                        "(band %.0f%%): the assembly has no single animal in it"
                        % (scale, dev * 100.0, ref, TOLERANCE_FRAC * 100.0),
                        measured_bones[bone], component=bone))
    measured = {"stage": stage, "expectation_source": table["source"],
                "expectation_exclusions": table.get("exclusions", []),
                "segments": measured_segments, "per_bone_scales": measured_bones,
                "ratios_gated": sorted(measured_segments), "bones_gated": sorted(measured_bones)}
    return {"law": LAW_ALLOMETRY, "verdict": "violation" if violations else "pass",
            "measured": measured}, violations


def check_taxonomic_coherence(bundle):
    """Two-category law corollary: one bundle, one taxon; a cross-species
    substitution is named with its measured taxonomic distance."""
    species = bundle.get("species") or []
    comp_species = [(c.get("id", "?"), c.get("species")) for c in bundle.get("components", []) if c.get("species")]
    named = []
    for sp in species:
        if isinstance(sp, dict):
            named.append(sp.get("name"))
        else:
            named.append(sp)
    named += [sp for _cid, sp in comp_species]
    named = [n for n in named if n]
    distinct = sorted(set(named))
    violations = []
    if not distinct:
        return ({"law": LAW_TAXONOMY, "verdict": "violation",
                 "measured": {"species_named": 0}},
                [_violation(LAW_TAXONOMY, "species-unlabeled",
                            "no species label anywhere in the bundle -- never silent",
                            {"species_named": 0})])
    nodes, names = load_taxonomy()
    unresolvable = [n for n in distinct if n not in names]
    for n in unresolvable:
        violations.append(_violation(
            LAW_TAXONOMY, "species-unresolvable",
            "species %r not in the pinned taxdmp extract -- cannot be silently waved through" % (n,),
            {"name": n, "resolvable": False}))
    if len(distinct) > 1:
        for i, a in enumerate(distinct):
            for b in distinct[i + 1:]:
                if a in unresolvable or b in unresolvable:
                    continue
                dist = taxonomic_distance(nodes, names, a, b)
                violations.append(_violation(
                    LAW_TAXONOMY, "cross-species-substitution",
                    "taxa %s and %s in one bundle: taxonomic distance %d parent edges (pinned NCBI extract)"
                    % (a, b, dist),
                    {"pair": [a, b], "taxonomic_distance_edges": dist}))
    measured = {"species_named": sorted(distinct),
                "component_species": {cid: sp for cid, sp in comp_species}}
    return {"law": LAW_TAXONOMY, "verdict": "violation" if violations else "pass",
            "measured": measured}, violations


def check_physics_bars(bundle):
    """Wire to the EXISTING aliveness bars only (conservation/pressure/pose/
    touch). Absent bars are reported_not_gated, never invented; a carried bar
    without numbers is a violation (a gate that cannot measure a law it names
    is RED); a failed bar is a violation with its numbers."""
    bars = bundle.get("physics_bars") or []
    violations, adjudicated = [], []
    for bar in bars:
        law = bar.get("law")
        if law not in PHYSICS_BAR_LAWS:
            violations.append(_violation(
                LAW_PHYSICS, "physics-bar-unknown-law",
                "bar names law %r outside the aliveness vocabulary %s -- inventing new physics is forbidden"
                % (law, list(PHYSICS_BAR_LAWS)),
                {"named": law, "vocabulary": list(PHYSICS_BAR_LAWS)}))
            continue
        measured = bar.get("measured")
        entry = {"law": law, "verdict": bar.get("verdict"), "measured": measured,
                 "source": bar.get("source")}
        if not isinstance(measured, dict) or not measured:
            violations.append(_violation(
                LAW_PHYSICS, "physics-bar-unmeasured",
                "bar %r carries no measured numbers -- a verdict without a number is refused" % (law,),
                {"named": law, "measured": None}, source=bar.get("source")))
            continue
        if bar.get("verdict") not in ("pass", "fail"):
            violations.append(_violation(
                LAW_PHYSICS, "physics-bar-verdict-unnamed",
                "bar %r has numbers but no pass/fail verdict" % (law,),
                {"named": law, "verdict": bar.get("verdict")}, measured=measured))
            continue
        adjudicated.append(entry)
        if bar["verdict"] == "fail":
            violations.append(_violation(
                LAW_PHYSICS, "physics-bar-failed",
                "aliveness bar %r FAILED with measured numbers" % (law,),
                measured, source=bar.get("source")))
    measured = {"bars_carried": len(bars), "bars_adjudicated": adjudicated,
                "vocabulary": list(PHYSICS_BAR_LAWS)}
    return {"law": LAW_PHYSICS, "verdict": "violation" if violations else "pass",
            "measured": measured}, violations


# ---------------------------------------------------------------------------
# the adjudication
# ---------------------------------------------------------------------------

def adjudicate(bundle):
    """THE GATE: classify {category: reality|fantasy, violations: [...]},
    every violation itemized with its measured numbers, never silent."""
    if bundle.get("schema") != BUNDLE_SCHEMA:
        raise BundleError("bundle schema %r != %s" % (bundle.get("schema"), BUNDLE_SCHEMA))
    if not bundle.get("name"):
        raise BundleError("bundle carries no name")

    checks, violations, not_gated = [], [], []
    for fn in (check_stage_consistency, check_allometric_coherence,
               check_taxonomic_coherence):
        check, vs = fn(bundle)
        checks.append(check)
        violations.extend(vs)
    physics, vs = check_physics_bars(bundle)
    checks.append(physics)
    violations.extend(vs)
    not_gated.extend(["physics_bars"] if physics["measured"]["bars_carried"] == 0 else [])

    acknowledged = bool(bundle.get("fantasy_manifest_acknowledged"))
    if violations and not acknowledged:
        violations.append(_violation(
            "two_category_law", "fantasy-unacknowledged",
            "the bundle deviates from the laws but its manifest is not acknowledged: "
            "chimeras are developer-driven EXPLICIT construction, never accidental data mixing",
            {"violations_before_acknowledgement": len(violations),
             "fantasy_manifest_acknowledged": False}))
    category = "reality" if not violations else "fantasy"
    # every check must carry measured numbers or the gate itself is RED
    for check in checks:
        if "measured" not in check:
            raise BundleError("law check %r emitted without a measurement -- RED" % (check.get("law"),))
    caveats = []
    if bundle.get("named_circularity"):
        caveats.append(bundle["named_circularity"])
    return {
        "schema": SCHEMA,
        "bundle": bundle.get("name"),
        "category": category,
        "violations": violations,
        "checks": checks,
        "reported_not_gated": not_gated,
        "construction": {"mode": "reality" if category == "reality" else "explicit-fantasy",
                         "fantasy_manifest_acknowledged": acknowledged if violations else None},
        "caveats": caveats,
        "laws": list(LAWS),
        "tolerance_frac": TOLERANCE_FRAC,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="reality/fantasy adjudicator (the two-category law, measured)")
    ap.add_argument("bundle", help="path to a chimera.creature_bundle.v1 JSON manifest")
    ap.add_argument("-o", "--out", help="write the verdict JSON here (default: stdout)")
    args = ap.parse_args(argv)
    bundle = _load_json(Path(args.bundle))
    verdict = adjudicate(bundle)
    text = json.dumps(verdict, indent=1, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
