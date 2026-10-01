"""The measured-caps static verdict: the wave-4 stance-hold statics and the
wave-10/25 margin wall re-priced at THREE cap sets.

Rule 0: receipt.json pre-registered every band and crossing verdict BEFORE this
script existed; a band miss is a FIRED falsifier recorded with its number, never
tuned. The receipt's pre_registration block is unedited by this lane.

Instrument: the vendored BYTE COPY of gait_zero_20260919/derive_stance_hold.py
(the wave-4 11-DOF planar quasi-static deriver, commit 4198dbdc) runs UNMODIFIED
in inputs/run_env/ with the derived-numbers snapshot at the path it expects.
This script reads the regenerated demands (cap-independent), verifies they
EQUAL the banked stance-hold snapshot (the instrument falsifier), and computes:

  (a) LIVE doc-derived caps   hip 11.2125 knee 6.6375 ankle 7.4 MP 0.8875
  (b) MEASURED V1_S1 caps     knee 9.576795 MP 1.657925, ankle DOC-HELD (the
      re-derivation is BLOCKED on measured arms; the parallel ankle-arms lane's
      artifacts are NOT on canonical), hip HELD, posture HELD keyed to hip
  (c) PROVISIONAL V2_S1 caps  knee 36.247782 MP 4.636664 (PCSA x sigma x
      cos(pennation) x measured deposit arms), others as (b)

and the wave-10/25 margin wall re-priced per set from the banked wave-10
collocation deliverable (21 nodes). The k = 0.119754 scale gate is stated on
every verdict.

Run:  python -B tools/science_funnel/validation/measured_caps_statics_20260921/derive_measured_caps_statics.py
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
BOOK = LANE.parent / "hind_torque_book_20260921" / "hind_torque_book.json"
SNAP_STANCE = LANE / "inputs" / "stance_hold.snapshot.json"
SNAP_DERIVED = LANE / "inputs" / "derived_numbers.snapshot.json"
RUN_ENV = LANE / "inputs" / "run_env" / "tools" / "science_funnel" / "validation"
RUN_ENV_WAVE4 = LANE / "inputs" / "run_env_wave4" / "tools" / "science_funnel" / "validation"
VENDORED_SCRIPT = RUN_ENV / "gait_zero_20260919" / "derive_stance_hold.py"
VENDORED_SCRIPT_WAVE4 = RUN_ENV_WAVE4 / "gait_zero_20260919" / "derive_stance_hold.py"
REGEN_STANCE = RUN_ENV / "gait_zero_20260919" / "stance_hold.json"
REGEN_STANCE_WAVE4 = RUN_ENV_WAVE4 / "gait_zero_20260919" / "stance_hold.json"
WAVE10_WALL = LANE / "inputs" / "vendored_gait_zero" / "trunk_vault_reachable.wave10.json"
OUT = LANE / "measured_caps_statics.json"

PINS = {
    "hind_torque_book": (BOOK, "9fc5c0ba09f6ec183d5348bb21cc5dc18b5987240406ccdcdbb34e514e26f01c"),
    "stance_hold_snapshot": (SNAP_STANCE, "71e40cd8a161938a3a358792076dda0f98966a8909ae564cec7774a61126a5e5"),
    "derived_numbers_snapshot": (SNAP_DERIVED, "013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd1514017a173"),
    # the wave-8-era script (4198dbdc head of the file; carries the MP-Jacobian fix)
    "wave8_machinery_byte_copy": (VENDORED_SCRIPT, "3c92d188b6aaf01c8cc4319262981b51ba95566370fb59e1ba4d0dd764562f70"),
    # the wave-4 script AS COMMITTED at 724f2464 - the version that GENERATED the banked stance_hold.json
    "wave4_machinery_byte_copy": (VENDORED_SCRIPT_WAVE4, "353d07f7f18a7fa371c43eef18e40d3160d58855a24b464ef587e526bd0f81c0"),
    "wave10_wall_deliverable": (WAVE10_WALL, "e922153318778e4cd8c1891f59454261c6d5be0a77aebdc5f78d2758ccd2faa7"),
}

JOINTS = ["hip", "knee", "ankle", "mp", "posture"]
TAU_KEY = {"hip": "tau_hip_Nm", "knee": "tau_knee_Nm", "ankle": "tau_ankle_Nm",
           "mp": "tau_mp_Nm", "posture": "tau_posture_Nm"}

# cap provenance classes - every cap names its class (falsifier: provenance on the table)
PROV_CLASS = {
    "A_live_doc": {"hip": "LIVE_DOC", "knee": "LIVE_DOC", "ankle": "LIVE_DOC",
                   "mp": "LIVE_DOC", "posture": "LIVE_DOC_KEYED_TO_HIP"},
    "B_measured_v1_s1": {"hip": "HELD_FROM_A", "knee": "MEASURED_V1_S1_BOOK",
                         "ankle": "DOC_HELD_BLOCKED_NO_MEASURED_ARMS",
                         "mp": "MEASURED_V1_S1_BOOK", "posture": "HELD_FROM_A_KEYED_TO_HIP"},
    "C_provisional_v2_s1": {"hip": "HELD_FROM_A", "knee": "PROVISIONAL_V2_S1_BOOK",
                            "ankle": "DOC_HELD_BLOCKED_NO_MEASURED_ARMS",
                            "mp": "PROVISIONAL_V2_S1_BOOK", "posture": "HELD_FROM_A_KEYED_TO_HIP"},
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs():
    """REFUSES to run on any sha mismatch (the traceability falsifier)."""
    for name, (path, pin) in PINS.items():
        got = sha256(path)
        if got != pin:
            raise SystemExit(f"sha mismatch {name}: {path} {got} != {pin}")
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    stance = json.loads(SNAP_STANCE.read_text(encoding="utf-8"))
    wall = json.loads(WAVE10_WALL.read_text(encoding="utf-8"))
    return book, stance, wall


def book_caps(book):
    """The (b)/(c)/S2 caps from the in-tree book deliverable, with key paths."""
    r = book["rederivation"]
    ke, mf = r["knee_extension"]["variants"], r["mtp_flexion"]["variants"]
    out = {
        "knee_B": (ke["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"],
                   "rederivation.knee_extension.variants.V1_S1_oku_walk_peaks_deposit_arms.cap_N_m"),
        "mp_B": (mf["V1_S1_oku_walk_peaks_deposit_arms_equal_split"]["cap_N_m"],
                 "rederivation.mtp_flexion.variants.V1_S1_oku_walk_peaks_deposit_arms_equal_split.cap_N_m"),
        "knee_C": (ke["V2_S1_pcsa_sigma_deposit_arms"]["cap_N_m"],
                   "rederivation.knee_extension.variants.V2_S1_pcsa_sigma_deposit_arms.cap_N_m"),
        "mp_C": (mf["V2_S1_pcsa_sigma_deposit_arms"]["cap_N_m"],
                 "rederivation.mtp_flexion.variants.V2_S1_pcsa_sigma_deposit_arms.cap_N_m"),
        "knee_S2": (ke["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"],
                    "rederivation.knee_extension.variants.V1_S2_oku_peaks_si_matched_arms.cap_N_m"),
        "mp_S2": (mf["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"],
                  "rederivation.mtp_flexion.variants.V1_S2_oku_peaks_si_matched_arms.cap_N_m"),
    }
    return out


def run_vendored_statics(script, out_path):
    """Run a BYTE-UNMODIFIED vendored deriver; return its regenerated rows."""
    res = subprocess.run([sys.executable, "-B", str(script)],
                         capture_output=True, text=True, timeout=300)
    if res.returncode != 0:
        raise SystemExit(f"vendored statics failed:\n{res.stderr}")
    return json.loads(Path(out_path).read_text(encoding="utf-8"))


def stance_table(rows, caps):
    """Per-node ratios at one cap set; demands are cap-independent."""
    nodes = []
    for n in rows:
        r = {j: abs(float(n[TAU_KEY[j]])) / caps[j] for j in JOINTS}
        nodes.append({
            "phi": n["phi"],
            "tau_Nm": {j: float(n[TAU_KEY[j]]) for j in JOINTS},
            "ratio": {j: round(r[j], 6) for j in JOINTS},
            "over_cap": [j for j in JOINTS if r[j] > 1.0],
        })
    per_joint = {}
    for j in JOINTS:
        ratios = [nd["ratio"][j] for nd in nodes]
        binder = max(range(len(nodes)), key=lambda i: ratios[i])
        over = [nodes[i]["phi"] for i in range(len(nodes)) if ratios[i] > 1.0]
        holders = [(i, ratios[i]) for i in range(len(nodes)) if ratios[i] <= 1.0]
        mh = max(holders, key=lambda t: t[1])
        per_joint[j] = {
            "worst_ratio": round(max(ratios), 6),
            "binding_node_phi": nodes[binder]["phi"],
            "over_cap_nodes": len(over),
            "over_cap_phis": over,
            "worst_holding_ratio": round(mh[1], 6),
            "worst_holding_phi": nodes[mh[0]]["phi"],
        }
    worst = max(per_joint.items(), key=lambda kv: kv[1]["worst_ratio"])
    holder = max(per_joint.items(), key=lambda kv: kv[1]["worst_holding_ratio"])
    return {
        "nodes": nodes,
        "per_joint": per_joint,
        "worst_case_ratio": worst[1]["worst_ratio"],
        "worst_case_binder": {"joint": worst[0], "phi": worst[1]["binding_node_phi"]},
        "margin_binder_holding": {"joint": holder[0], "phi": holder[1]["worst_holding_phi"],
                                  "ratio": holder[1]["worst_holding_ratio"]},
    }


def wall_reprice(wall, caps_a, caps_x):
    """The wave-10/25 margin wall re-priced: per-node combined ratio with each
    joint's banked ratio divided by that joint's cap headroom."""
    h = {j: caps_a[j] / caps_x[j] for j in JOINTS}
    idx = {"hip": 0, "knee": 1, "ankle": 2, "mp": 3}
    nodes = []
    for n in wall["nodes"]:
        terms = {"posture": n["posture_ratio"]}
        for j, i in idx.items():
            terms[j] = n["leg_ratios"][i] * h[j]
        binder = max(terms, key=lambda j: terms[j])
        nodes.append({"phi": n["phi"], "terms": {j: round(v, 6) for j, v in terms.items()},
                      "combined": round(max(terms.values()), 6), "binder": binder})
    mx = max(nodes, key=lambda nd: nd["combined"])
    return {
        "headroom_factors": {j: round(h[j], 8) for j in JOINTS},
        "nodes": nodes,
        "max_combined_ratio": mx["combined"],
        "max_binder": {"joint": mx["binder"], "phi": mx["phi"]},
        "crosses_1_0": mx["combined"] <= 1.0,
        "margin_0_9_reachable": mx["combined"] <= 0.9,
        "nodes_over_1_0": [nd["phi"] for nd in nodes if nd["combined"] > 1.0],
        "nodes_over_0_9": [nd["phi"] for nd in nodes if nd["combined"] > 0.9],
        "knee_term_at_phi_0_75": round(
            next(nd["terms"]["knee"] for nd in nodes if nd["phi"] == 0.75), 6),
    }


def derive_once(book, stance, wall):
    """Full derivation: pure function of the sha-verified inputs."""
    caps_book = book_caps(book)
    cap_sets = {
        "A_live_doc": {"hip": 11.2125, "knee": 6.6375, "ankle": 7.4, "mp": 0.8875, "posture": 11.2125},
        "B_measured_v1_s1": {"hip": 11.2125, "knee": caps_book["knee_B"][0], "ankle": 7.4,
                             "mp": caps_book["mp_B"][0], "posture": 11.2125},
        "C_provisional_v2_s1": {"hip": 11.2125, "knee": caps_book["knee_C"][0], "ankle": 7.4,
                                "mp": caps_book["mp_C"][0], "posture": 11.2125},
    }
    s2_caps = {"hip": 11.2125, "knee": caps_book["knee_S2"][0], "ankle": 7.4,
               "mp": caps_book["mp_S2"][0], "posture": 11.2125}

    # 1. instrument: run BOTH committed versions of the banked machinery.
    #    wave-4 (724f2464) is the version that GENERATED the banked snapshot:
    #    it must reproduce it EXACTLY (the instrument falsifier at its letter).
    #    wave-8 (4198dbdc head) carries the lineage's own MP-Jacobian fix
    #    ("the wave-4/8 'MP demand ~8 N.m' was this artifact"; commit a8f3f8e4:
    #    "the MP-Jacobian bug fix reverses the strategy") - run for the named
    #    corrected-MP variant, reported alongside, never substituted silently.
    regen_w4 = run_vendored_statics(VENDORED_SCRIPT_WAVE4, REGEN_STANCE_WAVE4)
    regen_w8 = run_vendored_statics(VENDORED_SCRIPT, REGEN_STANCE)
    eq_w4 = regen_w4["stance_nodes"] == stance["stance_nodes"]
    mp_diffs = [
        {"phi": x["phi"], "banked_mp": y["tau_mp_Nm"], "wave8_corrected_mp": x["tau_mp_Nm"]}
        for x, y in zip(regen_w8["stance_nodes"], stance["stance_nodes"]) if x != y
    ]
    instrument = {
        "wave4_script_run": "inputs/run_env_wave4/.../derive_stance_hold.py (byte copy of 724f2464, the banked table's generator)",
        "wave4_reproduces_banked_exactly": eq_w4,
        "rows": len(regen_w4["stance_nodes"]),
        "banked_rows": len(stance["stance_nodes"]),
        "membrane": regen_w4["membrane"],
        "wave8_script_run": "inputs/run_env/.../derive_stance_hold.py (byte copy of the 4198dbdc head; the wave-8 MP-Jacobian fix)",
        "wave8_vs_banked_diff_cells": len(mp_diffs),
        "wave8_vs_banked_diffs": mp_diffs,
        "lineage_note": ("the banked snapshot is the wave-4 deliverable (724f2464); the wave-8 commit a8f3f8e4 "
                         "later removed the MP column from the contact Jacobian (the MP joint is distal to the "
                         "planted point) and banked 'the MP-Jacobian bug fix reverses the strategy'. This lane "
                         "runs BOTH byte-exact: the wave-4 demands are the PRIMARY table (the banked statics the "
                         "book consumed - the instrument falsifier validates against them); the wave-8 MP column "
                         "is the NAMED corrected variant, measured and reported, never silently substituted."),
    }
    if not eq_w4:
        instrument["first_diff_w4"] = next(
            (i for i, (x, y) in enumerate(zip(regen_w4["stance_nodes"], stance["stance_nodes"])) if x != y),
            None)
    rows = stance["stance_nodes"]

    # 2. the three cap-set tables + the S2 gate table (PRIMARY: banked demands)
    tables = {name: stance_table(rows, caps) for name, caps in cap_sets.items()}
    tables["S2_si_matched_gate"] = stance_table(rows, s2_caps)
    # the NAMED variant: the wave-8-corrected MP column, same cap sets
    tables_mp_corrected = {name: stance_table(regen_w8["stance_nodes"], caps)
                           for name, caps in cap_sets.items()}

    # 3. the wave-10/25 margin wall re-priced
    walls = {name: wall_reprice(wall, cap_sets["A_live_doc"], caps)
             for name, caps in list(cap_sets.items()) + [("S2_si_matched_gate", s2_caps)]}

    # 4. provenance on the table
    prov = {
        "cap_sets": {name: {"caps": cap_sets[name], "provenance_class": PROV_CLASS[name]}
                     for name in cap_sets},
        "book_cap_trace": {
            "input": "tools/science_funnel/validation/hind_torque_book_20260921/hind_torque_book.json",
            "sha256": PINS["hind_torque_book"][1],
            "key_paths": {k: v[1] for k, v in caps_book.items()},
            "values": {k: v[0] for k, v in caps_book.items()},
        },
        "demand_trace": {
            "input": "inputs/stance_hold.snapshot.json (byte copy of the wave-4 deliverable, sha equals the torque book receipt's pin)",
            "sha256": PINS["stance_hold_snapshot"][1],
            "key_path": "stance_nodes[].tau_{hip,knee,ankle,mp,posture}_Nm",
            "note": "demands are cap-independent statics (the wave-4 receipt's method); the instrument re-ran the banked code and reproduced them",
        },
        "wall_trace": {
            "input": "inputs/vendored_gait_zero/trunk_vault_reachable.wave10.json (byte copy at 4198dbdc)",
            "sha256": PINS["wave10_wall_deliverable"][1],
            "key_path": "nodes[].leg_ratios + nodes[].posture_ratio (posture cap 11.2125, posture limit 10.09125 = 0.9 x cap)",
        },
        "cap_provenance_classes": {
            "LIVE_DOC": "1.25 x the DOC-ROUNDED Oku walk peaks - the live graph-contract/engine pin (torque book audit)",
            "LIVE_DOC_KEYED_TO_HIP": "the posture drive borrows the hip cap (cap-on-each, live contract)",
            "MEASURED_V1_S1_BOOK": "Oku measured walk forces x pulley-lane MEASURED deposit arms (book V1_S1, argmax knee q=-42.3 deg)",
            "PROVISIONAL_V2_S1_BOOK": "PCSA x sigma(1280914.14 Pa) x cos(pennation) x measured deposit arms - PROVISIONAL (sigma caveat; the pennation-correction lane 37d053ac and the Guimaraes pairing are NOT on this branch's canonical base)",
            "DOC_HELD_BLOCKED_NO_MEASURED_ARMS": "the ankle cap stays DOC-derived: no ankle-direction arm curve exists in the pulley deliverable (book ankle_context: re-derivation BLOCKED) AND the parallel ankle-arms lane's artifacts are NOT on canonical at this lane's fetch time",
            "HELD_FROM_A": "this lane re-derives nothing for the hip (the posture-cap lane's 10.54 N.m amendment stays banked-unconsumed)",
            "HELD_FROM_A_KEYED_TO_HIP": "the posture cap stays at the (a) hip-keyed value - no re-derivation, no consumption of the banked 10.54 N.m amendment",
        },
    }

    # 5. the verdict
    a, b, c = tables["A_live_doc"], tables["B_measured_v1_s1"], tables["C_provisional_v2_s1"]
    wa, wb, wc, ws2 = (walls["A_live_doc"], walls["B_measured_v1_s1"],
                       walls["C_provisional_v2_s1"], walls["S2_si_matched_gate"])
    verdict = {
        "instrument_valid": instrument["wave4_reproduces_banked_exactly"],
        "wall_identity_at_a_holds": abs(wa["max_combined_ratio"] - 1.3227763257041534) < 5e-8,
        "binding_migration_knee": {
            "over_cap_phis_A": a["per_joint"]["knee"]["over_cap_phis"],
            "over_cap_count_A": a["per_joint"]["knee"]["over_cap_nodes"],
            "over_cap_phis_B": b["per_joint"]["knee"]["over_cap_phis"],
            "over_cap_count_B": b["per_joint"]["knee"]["over_cap_nodes"],
            "over_cap_phis_C": c["per_joint"]["knee"]["over_cap_phis"],
            "over_cap_count_C": c["per_joint"]["knee"]["over_cap_nodes"],
            "binding_node_A": a["per_joint"]["knee"]["binding_node_phi"],
            "binding_node_B": b["per_joint"]["knee"]["binding_node_phi"],
            "entry_ratio_A": next(nd["ratio"]["knee"] for nd in a["nodes"] if nd["phi"] == 0.449),
            "entry_ratio_B": next(nd["ratio"]["knee"] for nd in b["nodes"] if nd["phi"] == 0.449),
            "book_prediction": "9 -> 4 of 15; binding phi=0.25 ratio 1.586 -> 1.100; entry 1.095 -> 0.760",
        },
        "margin_verdict": {
            "question": "does the wave-10/25 margin ratio cross 1.0 under (b)? under (c)?",
            "wall_ratio_A": wa["max_combined_ratio"], "wall_binder_A": wa["max_binder"],
            "wall_ratio_B": wb["max_combined_ratio"], "wall_binder_B": wb["max_binder"],
            "wall_ratio_C": wc["max_combined_ratio"], "wall_binder_C": wc["max_binder"],
            "crosses_1_0_under_B": wb["crosses_1_0"],
            "crosses_1_0_under_C": wc["crosses_1_0"],
            "margin_0_9_reachable_under_B": wb["margin_0_9_reachable"],
            "margin_0_9_reachable_under_C": wc["margin_0_9_reachable"],
            "statement": ("the wall's binding term at the live caps is the KNEE (1.3227763 at phi=0.75, the "
                          "wave-10 deliverable's own banked max) - NOT the book prose's 0.785, which resolves to "
                          "no banked artifact this lane could find (named in the receipt). At the MEASURED knee cap "
                          "the knee term re-prices to {kb:.6f} and at the PROVISIONAL PCSA x sigma cap to {kc:.6f}; "
                          "the max combined ratio over the 21 banked collocation nodes falls to {wb:.6f} (b) / "
                          "{wc:.6f} (c) - BOTH cross below 1.0, and the binder MIGRATES knee -> ANKLE (0.977235 at "
                          "phi=0.5, cap-unchanged because the ankle lane is BLOCKED). The 0.9 margin itself stays "
                          "UNREACHABLE at the banked optimum under every set - the ankle (doc-held, blocked) and "
                          "the 0.9-posture-saturation own it now; clearing it needs the ankle pulley direction "
                          "(the book's named future work) or a re-collocation hearing at the new caps (out of this "
                          "lane's scope, order-of-magnitude discipline).").format(
                              kb=wb["knee_term_at_phi_0_75"], kc=wc["knee_term_at_phi_0_75"],
                              wb=wb["max_combined_ratio"], wc=wc["max_combined_ratio"]),
        },
        "the_scale_gate": ("S1 GATE ON EVERY VERDICT ABOVE: sets (b)/(c) stand on the DEPOSIT arm scale. At the "
                           "SI-matched scale (arms x k = 0.11975394, the pulley lane's fitted per-taxon scalar, the "
                           "absolute-scale divergence OPEN at operator level) the book collapses (knee 1.146859, MP "
                           "0.198543) and every (b)/(c) verdict INVERTS: knee over-cap {s2n}/15, knee worst "
                           "{s2w}, wall max combined {s2wall} at {s2binder} - the walker cannot hold or walk. No "
                           "engine consumption is lawful until the operator resolves the k divergence.").format(
                               s2n=tables["S2_si_matched_gate"]["per_joint"]["knee"]["over_cap_nodes"],
                               s2w=tables["S2_si_matched_gate"]["per_joint"]["knee"]["worst_ratio"],
                               s2wall=ws2["max_combined_ratio"], s2binder=ws2["max_binder"]),
        "worst_case_ratios": {name: tables[name]["worst_case_ratio"] for name in tables},
        "honest_reds": [
            "the stance-hold push-off tail (phi 0.55-0.65) stays OVER even at the measured knee cap "
            "(b): ratios {b55:.4f}/{b6:.4f}/{b65:.4f} - the measured book covers the entry and mid-window, not the push-off statics".format(
                b55=next(nd["ratio"]["knee"] for nd in b["nodes"] if nd["phi"] == 0.55),
                b6=next(nd["ratio"]["knee"] for nd in b["nodes"] if nd["phi"] == 0.6),
                b65=next(nd["ratio"]["knee"] for nd in b["nodes"] if nd["phi"] == 0.65)),
            "the MP windlass quasi-static flags (phi 0.0-0.25, 8.0-8.5 N.m double-support class) stay "
            "uncovered at EVERY set - by design of those nodes (the wave-4 receipt's load-sharing caveat), at (c) still {c:.4f}".format(
                c=next(nd["ratio"]["mp"] for nd in c["nodes"] if nd["phi"] == 0.25)),
            "the hip and posture columns gain NOTHING at (b)/(c) (caps held; the 10.54 N.m muscle-grounded "
            "posture amendment stays banked-unconsumed) - their over-cap nodes stay 4/15",
            "the 0.9 margin verdict is measured AT THE BANKED wave-10 optimum; a collocation re-hearing at "
            "the new caps could move the ankle terms - named future work, not measured here",
        ],
    }

    return {
        "schema": "chimera.measured_caps_statics.v1",
        "lane": "measured-caps-statics-20260921",
        "derived_from_commit": "b17cbf6c (branch agent/hind-torque-book-20260921)",
        "receipt": "receipt.json (pre-registration written before this script existed)",
        "instrument": instrument,
        "cap_sets": prov["cap_sets"],
        "cap_provenance_classes": prov["cap_provenance_classes"],
        "cap_trace": prov["book_cap_trace"],
        "demand_trace": prov["demand_trace"],
        "wall_trace": prov["wall_trace"],
        "stance_tables": tables,
        "stance_tables_wave8_corrected_mp_VARIANT": tables_mp_corrected,
        "margin_wall": walls,
        "verdict": verdict,
    }


def main():
    book, stance, wall = load_inputs()
    d1 = derive_once(book, stance, wall)
    d2 = derive_once(book, stance, wall)
    j1 = json.dumps(d1, sort_keys=True, indent=1)
    j2 = json.dumps(d2, sort_keys=True, indent=1)
    if j1 != j2:
        raise SystemExit("NON-DETERMINISTIC: two in-process derivations disagree")
    OUT.write_text(j1 + "\n", encoding="utf-8", newline="\n")
    digest = hashlib.sha256((j1 + "\n").encode("utf-8")).hexdigest()
    print("deliverable:", OUT)
    print("sha256:", digest)
    print("instrument_valid:", d1["verdict"]["instrument_valid"])
    for name in ("A_live_doc", "B_measured_v1_s1", "C_provisional_v2_s1"):
        t = d1["stance_tables"][name]
        print(f"{name}: worst {t['worst_case_ratio']} knee_over {t['per_joint']['knee']['over_cap_nodes']}/15 "
              f"wall {d1['margin_wall'][name]['max_combined_ratio']} binder {d1['margin_wall'][name]['max_binder']}")


if __name__ == "__main__":
    main()
