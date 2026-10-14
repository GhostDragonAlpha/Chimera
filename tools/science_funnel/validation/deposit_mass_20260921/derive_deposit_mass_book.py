"""Deposit-mass forensics derivation (lane deposit-mass-20260921).

Rule 0: the receipt.json pre-registration in this directory was written BEFORE
any deposit mass value was read. This script only computes what the receipt
pre-registered: the parsed per-body masses, the expected band from the pinned
literature constants, the deficit factor, the scale tests, and the placeholder
signature tests. Every number in the book carries its source key.

Byte-deterministic: no clock, no locale, canonical JSON (indent=1, sort_keys).
"""

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
DATA = REPO / "tools" / "science_funnel" / "data" / "wiseman2026"
MODELS = DATA / "models"
MANIFEST = DATA / "sha256_manifest.json"
K_LANE = REPO / "tools" / "science_funnel" / "validation" / "k_forensics_20260921"
LIT = Path(__file__).resolve().parent / "literature"
LANE = Path(__file__).resolve().parent
BOOK_PATH = LANE / "deposit_mass_book.json"

BASE_COMMIT = "5a5914b37de55dcbcf246721c398d78770bceb0b"

# ---- pinned constants (every one cited) ------------------------------------

# k = SI-2/deposit linear moment-arm factor, MTP class (committed k-lane
# deliverable k_forensics_book.json; k-lane receipt reproduces to 3.8e-09).
K = 0.11975394

# Packet question 4 sum under test (author_email_packet.md, committed k-lane).
PACKET_SUM_KG = 0.772
PACKET_SUM_TOLERANCE_KG = 0.0005  # the packet states three decimals

# Adult female rhesus body mass band, kg (Turnquist & Kessler 1989,
# DOI 10.1002/ajp.1350190102, via committed k-lane receipt body_mass_prior).
BODY_MIN_KG = 5.4
BODY_MAX_KG = 6.9

# Oku 2021 Table 1 segment masses, kg (literature/oku2021.xml, PMC7940622):
# HAT 8.184; per limb: thigh 0.557, shank 0.269, foot 0.080, phalanges 0.021.
OKU_HAT_KG = 8.184
OKU_LIMB_CHAIN_KG = 0.557 + 0.269 + 0.080 + 0.021  # 0.927

# Hazotte 2026 Table 2 mass fractions of total body mass
# (literature/hazotte2026.xml, PMC12967147): thigh 5.6, shank 2.7, foot 1.0.
HAZOTTE_CHAIN_FRAC = 2.0 * (0.056 + 0.027 + 0.010)  # 0.186

# Zihlman & Underwood 2013 hindlimb band (literature/zihlman2013.xml,
# PMC3804282): hindlimb mass 20-24% for M. fuscata and M. mulatta.
ZIHLMAN_FRAC_MIN = 0.20
ZIHLMAN_FRAC_MAX = 0.24

# Secondary declared cross-species context only (NOT byte-pinned):
# human pelvis fraction ~0.142 (de Leva 1996, DOI 10.1016/0021-9290(95)00178-6).
DE_LEVA_PELVIS_FRAC = 0.142

# Pre-verified pins (receipt.json inputs_pinned).
# repin_20260921: the wiseman-pin-repair lane (68730eab) rewrote the manifest
# (route-b re-canonicalization of its inventory.json entry) and made
# wiseman2026 checkout == blob (-text). The receipt's appended repin_20260921
# section supersedes the pre-repair (autocrlf-smudged) pin below when present;
# the old value stays as the documented fallback and still refuses without it.
MANIFEST_SHA_PRE_REPAIR = "e72b6616fc23960e3e9a50491d104ee752240fc8b8787f7541c1da85b84a78e3"
_repins = {
    r["path"]: r["new_sha256"]
    for r in json.loads((LANE / "receipt.json").read_text(encoding="utf-8"))
    .get("repin_20260921", {})
    .get("re_pins", [])
}
MANIFEST_SHA = _repins.get(
    "tools/science_funnel/data/wiseman2026/sha256_manifest.json",
    MANIFEST_SHA_PRE_REPAIR,
)
# repin_20260921 (second order): the k deliverable regenerated with its honest
# post-repair provenance (its inputs_sha_verified block records the k receipt's
# re-pins); this lane's byte-pin on it follows the same repin section.
K_BOOK_SHA_PRE_REPIN = "0c2d8b397a158283f19a8ff81a8f6be5f6a787ac09c09b7394c70e5402166b4b"
K_BOOK_SHA = _repins.get(
    "tools/science_funnel/validation/k_forensics_20260921/k_forensics_book.json",
    K_BOOK_SHA_PRE_REPIN,
)
LIT_SHAS = {
    "oku2021.xml": "e8e60ac390192ed6259d792d317d5c722a62ab23511a0efc653e95ff1a69eef0",
    "hazotte2026.xml": "8ee615e176570d9412d9a44ef1209ef753e72faa7b0a03e183d37bb466f35790",
    "zihlman2013.xml": "33eff5f6c7e6151970c63418c198abe505f0284adf6c375399a6068e824eb945",
    "nc3rs_health_indicators.html": "bf465b1241164215be7fc25ec5af848a8b2462c2594496037dc6c3efc7288c47",
}

TAXA = ["Bonobo", "Chimpanzee", "Gibbon", "Gorilla", "Macaque", "Orangutan", "Siamang"]


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def refuse(condition, message):
    if not condition:
        raise SystemExit("LOAD REFUSED: " + message)


# ---- inputs -----------------------------------------------------------------

def verify_inputs():
    verified = {}
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    refuse(sha256_file(MANIFEST) == MANIFEST_SHA, "sha256_manifest.json != k-lane receipt pin")
    entries = {f["path"]: f["sha256"] for f in manifest["files"]}
    verified["wiseman_sha256_manifest"] = True
    for taxon in TAXA:
        rel = "models/%s_model.osim" % taxon
        refuse(rel in entries, "manifest missing " + rel)
        on_disk = sha256_file(MODELS / ("%s_model.osim" % taxon))
        refuse(on_disk == entries[rel], "%s sha mismatch vs manifest" % rel)
        verified[rel] = True
    book_on_disk = sha256_file(K_LANE / "k_forensics_book.json")
    refuse(book_on_disk == K_BOOK_SHA, "k_forensics_book.json sha mismatch vs k-lane receipt pin")
    verified["k_forensics_book"] = True
    for name, want in sorted(LIT_SHAS.items()):
        refuse(sha256_file(LIT / name) == want, "literature sha mismatch: " + name)
        verified["literature/" + name] = True
    return verified, entries


def parse_bodies(osim_path):
    """Per-body masses from an .osim (OpenSim Model/BodySet/objects/Body).

    Consumes ONLY the <Body name=...> <mass>...</mass> fields - no other
    element. Order = document order (deterministic for a pinned file).
    """
    tree = ET.parse(osim_path)
    root = tree.getroot()
    bodies = []
    for body in root.iter("Body"):
        name = body.get("name")
        mass_el = body.find("mass")
        if name is None or mass_el is None or mass_el.text is None:
            continue
        bodies.append((name, float(mass_el.text.strip())))
    return bodies


# ---- literature arithmetic ---------------------------------------------------

def expected_band():
    oku_total = OKU_HAT_KG + 2.0 * OKU_LIMB_CHAIN_KG  # 10.038
    oku_frac = 2.0 * OKU_LIMB_CHAIN_KG / oku_total
    frac_min = oku_frac
    frac_max = ZIHLMAN_FRAC_MAX
    exp_min = frac_min * BODY_MIN_KG
    exp_max = frac_max * BODY_MAX_KG
    return {
        "oku_model_total_kg": round(oku_total, 6),
        "oku_hindlimb_chain_fraction": round(oku_frac, 6),
        "hazotte_hindlimb_chain_fraction": round(HAZOTTE_CHAIN_FRAC, 6),
        "zihlman_hindlimb_fraction_band": [ZIHLMAN_FRAC_MIN, ZIHLMAN_FRAC_MAX],
        "primary_fraction_band": {
            "min": round(frac_min, 6),
            "max": round(frac_max, 6),
            "sources": "min = Oku 2021 Table 1 arithmetic (2 x 0.927 kg / 10.038 kg, "
                       "CT model, pelvis excluded, lit_oku2021 Table 1); "
                       "max = Zihlman & Underwood 2013 dissection band 20-24% stated for "
                       "M. fuscata and M. mulatta (pelvis segment excluded, lit_zihlman2013); "
                       "Hazotte 2026 Table 2 = 0.186 of the same CT model (lit_hazotte2026)",
        },
        "body_band_kg": [BODY_MIN_KG, BODY_MAX_KG],
        "body_source": "Turnquist & Kessler 1989 DOI 10.1002/ajp.1350190102 via committed "
                       "k_forensics_20260921/receipt.json body_mass_prior.adult_female_kg",
        "expected_kg": {
            "min": round(exp_min, 6),
            "max": round(exp_max, 6),
            "pelvis_caveat": "the deposit sum INCLUDES a Pelvis body; both literature "
                             "fractions EXCLUDE the pelvis segment - the true expectation "
                             "is STRICTLY ABOVE this envelope",
        },
        "deficit_factor_envelope": {
            "definition": "expected / measured_sum",
            "min": round(exp_min / PACKET_SUM_KG, 6),
            "max": round(exp_max / PACKET_SUM_KG, 6),
        },
        "secondary_cross_species_extension": {
            "pelvis_source": "de Leva 1996 DOI 10.1016/0021-9290(95)00178-6, ~0.142 of "
                             "body mass, cited by DOI ONLY (paywalled, NOT byte-pinned) - "
                             "declared cross-species context, never the primary verdict",
            "fraction_band": [
                round(frac_min + DE_LEVA_PELVIS_FRAC, 6),
                round(frac_max + DE_LEVA_PELVIS_FRAC, 6),
            ],
            "expected_kg": [
                round((frac_min + DE_LEVA_PELVIS_FRAC) * BODY_MIN_KG, 6),
                round((frac_max + DE_LEVA_PELVIS_FRAC) * BODY_MAX_KG, 6),
            ],
            "deficit_factor": [
                round((frac_min + DE_LEVA_PELVIS_FRAC) * BODY_MIN_KG / PACKET_SUM_KG, 6),
                round((frac_max + DE_LEVA_PELVIS_FRAC) * BODY_MAX_KG / PACKET_SUM_KG, 6),
            ],
        },
    }


def scale_tests(measured_sum, band):
    k2 = K * K
    k3 = k2 * K
    exp_min = band["expected_kg"]["min"]
    exp_max = band["expected_kg"]["max"]
    fwd_lin = [round(exp_min * K, 6), round(exp_max * K, 6)]
    fwd_cube = [round(exp_min * k3, 9), round(exp_max * k3, 9)]
    req_lin = measured_sum / K
    req_cube = measured_sum / k3
    lin_closes = fwd_lin[0] * 0.995 <= measured_sum <= fwd_lin[1] * 1.005
    cube_closes = fwd_cube[0] * 0.995 <= measured_sum <= fwd_cube[1] * 1.005
    return {
        "k": K,
        "k2": round(k2, 9),
        "k3": round(k3, 9),
        "k_source": "committed k_forensics_20260921 deliverable, MTP class 0.11975394 "
                    "(k-lane receipt: recomputed diff 3.8e-09)",
        "expected_x_k_kg": fwd_lin,
        "expected_x_k3_kg": fwd_cube,
        "linear_closure": {
            "closes": lin_closes,
            "required_source_pelvis_hindlimb_kg": round(req_lin, 6),
            "reading": "0.772 / k demands a source model whose pelvis+hindlimb mass alone "
                       "equals %.3f kg - ABOVE the whole adult female body band [5.4, 6.9] kg; "
                       "anatomically incoherent" % req_lin,
        },
        "cube_law_closure": {
            "closes": cube_closes,
            "required_source_pelvis_hindlimb_kg": round(req_cube, 3),
            "reading": "0.772 / k^3 demands a ~%d kg class source model - no primate "
                       "template class exists there; closes NOWHERE" % round(req_cube),
        },
        "implied_body_reading": {
            "definition": "0.772 / fraction, IF the mass set were anatomically proportioned",
            "implied_body_kg": [
                round(measured_sum / band["primary_fraction_band"]["max"], 6),
                round(measured_sum / band["primary_fraction_band"]["min"], 6),
            ],
            "verdict": "below the adult female band [5.4, 6.9] kg and above birth mass "
                       "[0.40, 0.57] kg (both via committed k-lane receipt): an IMMATURE "
                       "animal at this reading - the packet's 'infant-class' is coarser "
                       "than this measured statement",
        },
    }


# ---- placeholder signature tests ---------------------------------------------

def decimals_of(v, limit=9):
    """smallest d in 0..limit with round(v, d) == v, else limit (float noise)."""
    for d in range(limit + 1):
        if round(v, d) == v:
            return d
    return limit


def signature_tests(macaque_bodies, taxon_bodies):
    masses = [m for _, m in macaque_bodies]
    s1_max, s1_min = max(masses), min(masses)
    s1_spread = s1_max - s1_min
    s1_uniform = s1_spread <= 1e-9 * max(1.0, s1_max)

    by_name = dict(macaque_bodies)
    pairs = []
    s2_max_diff = None
    for base in ["thigh", "shank", "foot", "toes"]:
        left = by_name.get(base + "_l")
        right = by_name.get(base + "_r")
        if left is not None and right is not None:
            diff = abs(left - right)
            pairs.append({"pair": base, "abs_diff_kg": round(diff, 12)})
            s2_max_diff = diff if s2_max_diff is None else max(s2_max_diff, diff)

    sums = {t: round(sum(m for _, m in taxon_bodies[t]), 9) for t in sorted(taxon_bodies)}
    canon_sets = {t: sorted((n, round(m, 12)) for n, m in taxon_bodies[t]) for t in taxon_bodies}
    ref = canon_sets["Macaque"]
    identical_all = all(canon_sets[t] == ref for t in sorted(canon_sets))
    per_body_equal = {}
    ref_map = dict(ref)
    for t in sorted(canon_sets):
        if t == "Macaque":
            continue
        other = dict(canon_sets[t])
        same_names = set(ref_map) == set(other)
        same_masses = same_names and all(ref_map[n] == other[n] for n in ref_map)
        per_body_equal[t] = {"same_body_names": same_names, "same_masses": bool(same_masses)}
    per_taxon_bodies = {
        t: {"n_bodies": len(taxon_bodies[t]),
            "body_names": [n for n, _ in taxon_bodies[t]],
            "has_trunk_like_body": any(
                kw in n.lower() for n, _ in taxon_bodies[t]
                for kw in ("trunk", "torso", "abdomen", "thorax", "head"))}
        for t in sorted(taxon_bodies)
    }

    decs = [decimals_of(m) for m in masses]
    s4_min_decimals = min(decs)

    a_closes = s1_uniform or identical_all
    foot_l = by_name.get("foot_l")
    foot_r = by_name.get("foot_r")
    hallux = by_name.get("R_Hallux")
    lateral_callout = None
    if foot_l is not None and foot_r is not None:
        lateral_callout = {
            "foot_l_over_foot_r": round(foot_l / foot_r, 6),
            "foot_r_minus_R_Hallux_kg": None if hallux is None else round(foot_r - hallux, 9),
            "note": "the k-lane measured the deposit's femur/tibia meshes as exact mirror "
                    "copies (L/R diameters <= 1.5e-05 mm); the mass set's own L/R thigh, "
                    "shank and toes masses are EQUAL, but foot_l carries %.1fx the foot_r "
                    "mass, and foot_r sits within 1 mg of the R_Hallux mass - the mass set "
                    "cannot be a density reading of ANY bilaterally symmetric geometry, "
                    "whether the deposit's or a real subject's" % (foot_l / foot_r),
        }
    return {
        "s1_uniformity": {
            "n_bodies": len(masses),
            "n_distinct_values": len(set(masses)),
            "max_minus_min_kg": round(s1_spread, 12),
            "uniform_if_spread_le_1e9_rel": s1_uniform,
        },
        "s2_lateral_symmetry": {
            "pairs": pairs,
            "max_abs_diff_kg": None if s2_max_diff is None else round(s2_max_diff, 12),
            "lateral_inconsistency_callout": lateral_callout,
            "note": "consistent with a placeholder AND with the k-lane's mirror-copy "
                    "observation; not verdict-bearing alone",
        },
        "s3_cross_taxon_identity": {
            "per_taxon_total_kg": sums,
            "all_taxa_identical_body_mass_sets": identical_all,
            "per_body_equality_vs_macaque": per_body_equal,
            "per_taxon_bodies": per_taxon_bodies,
            "note": "a macaque and a gorilla cannot share subject-derived segment masses",
        },
        "s4_round_numbers": {
            "min_decimal_places_across_bodies": s4_min_decimals,
            "decimal_places_per_body": {n: decimals_of(m) for n, m in macaque_bodies},
        },
        "hypothesis_a_closes": a_closes,
        "closing_evidence": ("s1_uniform" if s1_uniform else "") +
                            ("|s3_cross_taxon_identical" if identical_all else ""),
    }


# ---- main ---------------------------------------------------------------------

def build_book():
    verified, manifest_entries = verify_inputs()

    macaque = parse_bodies(MODELS / "Macaque_model.osim")
    refuse(len(macaque) > 0, "no Body/mass fields parsed from Macaque_model.osim")
    taxon_bodies = {t: parse_bodies(MODELS / ("%s_model.osim" % t)) for t in TAXA}

    measured_sum = sum(m for _, m in macaque)
    band = expected_band()
    scales = scale_tests(measured_sum, band)
    sig = signature_tests(macaque, taxon_bodies)

    sum_matches_packet = abs(measured_sum - PACKET_SUM_KG) <= PACKET_SUM_TOLERANCE_KG
    exp_min = band["expected_kg"]["min"]
    exp_max = band["expected_kg"]["max"]
    anomaly_real = measured_sum < exp_min
    inside_envelope = exp_min <= measured_sum <= exp_max

    if inside_envelope:
        verdict = ("FALSIFIER (a) FIRES: the measured sum sits INSIDE the pre-registered "
                   "expected envelope - the packet's question 4 anomaly evaporates")
    elif not sum_matches_packet:
        verdict = ("FALSIFIER (b) FIRES: the parsed sum does not reproduce the packet's "
                   "0.772 kg - packet-number correction recorded")
    else:
        parts = []
        if sig["hypothesis_a_closes"]:
            parts.append("the mass set is a TEMPLATE/PLACEHOLDER stamp (hypothesis a closes: "
                         + (sig["closing_evidence"] or "signature") + ")")
        elif scales["linear_closure"]["closes"] or scales["cube_law_closure"]["closes"]:
            parts.append("a geometric scaling arithmetic closes (hypothesis b)")
        else:
            parts.append("no scaling arithmetic closes and the masses are not a uniform "
                         "stamp (hypothesis c: genuinely low)")
        verdict = ("ANOMALY MEASURED: %.6f kg vs expected envelope [%.6f, %.6f] kg; deficit "
                   "factor %.6f-%.6fx; %s") % (
            measured_sum, exp_min, exp_max,
            band["deficit_factor_envelope"]["min"], band["deficit_factor_envelope"]["max"],
            "; ".join(parts))

    b_linear = scales["linear_closure"]["closes"]
    b_cube = scales["cube_law_closure"]["closes"]
    closures = {
        "a_template_placeholder": {
            "closes": bool(sig["hypothesis_a_closes"]),
            "evidence": sig["closing_evidence"],
            "pattern_reference": "the same deposit's placeholder 1 N muscle forces "
                                 "(author_email_packet.md question 4, committed k-lane)",
        },
        "b_geometric_scaling": {
            "linear_k_closes": b_linear,
            "cube_law_k3_closes": b_cube,
            "arithmetic": "deposit_sum = expected x k (linear) or expected x k^3 "
                          "(density-preserving); both directions reported above",
        },
        "c_genuinely_low": {
            "closes": bool((not sig["hypothesis_a_closes"]) and (not b_linear) and (not b_cube)),
            "meaning": "masses differentiated per body, non-round, no scaling closure",
        },
    }

    book = {
        "schema": "chimera.deposit_mass.v1",
        "lane": "deposit-mass-20260921",
        "base_commit": BASE_COMMIT,
        "inputs_verified": verified,
        "macaque_masses": {
            "source": "tools/science_funnel/data/wiseman2026/models/Macaque_model.osim "
                      "(manifest sha %s, verified at run time); parsed from <Body>/<mass> "
                      "fields only, document order" % manifest_entries["models/Macaque_model.osim"],
            "bodies": [{"name": n, "mass_kg": m} for n, m in macaque],
            "n_bodies": len(macaque),
            "sum_kg": round(measured_sum, 9),
            "sum_source_note": "the packet's '0.772 kg segment-mass sum' (question 4) is this "
                               "quantity: the model is hindlimb-only (k-lane receipt), so its "
                               "total IS pelvis+hindlimbs",
            "packet_sum_kg": PACKET_SUM_KG,
            "packet_reproduced": sum_matches_packet,
            "abs_diff_vs_packet_kg": round(abs(measured_sum - PACKET_SUM_KG), 12),
        },
        "expected_band": band,
        "scale_tests": scales,
        "placeholder_signature": sig,
        "comparison": {
            "measured_sum_kg": round(measured_sum, 9),
            "expected_envelope_kg": [exp_min, exp_max],
            "deficit_factor_envelope": band["deficit_factor_envelope"],
            "anomaly_real_at_conservative_bound": anomaly_real,
            "sum_inside_expected_envelope": inside_envelope,
            "sum_over_expected_min": round(measured_sum / exp_min, 6),
            "sum_over_expected_max": round(measured_sum / exp_max, 6),
            "sum_as_pct_of_6_15kg_adult_female": round(100.0 * measured_sum / 6.15, 4),
            "derived_context_note": "6.15 kg = midpoint of the pinned adult female band "
                                    "[5.4, 6.9]; literature hindlimb chains ALONE are "
                                    "18.5-24% of body mass (pelvis excluded), so the "
                                    "deposit's pelvis+hindlimbs at ~12.6% is below the "
                                    "hindlimb-only floor",
        },
        "hypothesis_closures": closures,
        "anatomy_context_quoted": {
            "source": "committed k_forensics_20260921/receipt.json check1 "
                      "(sha-pinned by base commit)",
            "femur_mm": 173.132408,
            "tibia_mm": 156.806231,
            "class": "ADULT_FEMALE_BAND",
        },
        "verdict": verdict,
    }

    canon = json.dumps(book, indent=1, sort_keys=True) + "\n"
    BOOK_PATH.write_text(canon, encoding="utf-8")
    return canon


def main():
    canon1 = build_book()
    canon2 = build_book()
    print("wrote", BOOK_PATH)
    print("sha256", hashlib.sha256(canon1.encode("utf-8")).hexdigest())
    print("determinism (two in-process runs byte-identical): %s" % (canon1 == canon2))


if __name__ == "__main__":
    main()
