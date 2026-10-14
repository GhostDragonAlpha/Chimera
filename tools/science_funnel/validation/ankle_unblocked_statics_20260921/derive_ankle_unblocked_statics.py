"""The ankle-unblocked static close-out: the FOURTH cap set - measured knee +
measured MTP + MEASURED ankle (V1_S1, both directions) + held hip/posture.

Rule 0: receipt.json pre-registered every band and crossing verdict BEFORE this
script existed; a band miss is a FIRED falsifier recorded with its number, never
tuned. The receipt's pre_registration block is unedited by this lane.

Instrument chain (falsifier PD1): the vendored BYTE COPY of the wave-4 stance
deriver (724f2464 - the banked table's generator) runs UNMODIFIED in
inputs/run_env_wave4/ and must reproduce the banked stance_hold snapshot
EXACTLY; then sets (a)/(b)/(c) and their walls are RE-DERIVED here under the
statics lane's own laws and asserted FIELD-FOR-FIELD EQUAL to the statics lane's
committed deliverable (inputs/statics_lane_committed_deliverable.json,
sha-pinned). Only then does set (d) enter:

  (d)  measured ankle UNBLOCKED  ankle plantar 6.247077 / dorsal 1.251106
       (ankle-arms book V1_S1, b15ff31e, direction-split by the book's own
       sign gate: plantar negative / dorsal positive), knee 9.576795 and
       MP 1.657925 as at (b), hip/posture HELD
  (d)-S2  the k-gated INVERSION BRACKET: ankle plantar 0.748112 / dorsal
       0.149825, knee 1.146859, MP 0.198543, hip/posture HELD

The wave-10/25 margin wall is re-priced at (d) under the receipt's NAMED
direction law (plantar cap for the wall's ankle term - the artifact carries
ratios only) with the DORSAL bracket computed alongside. The wave-8
MP-Jacobian-corrected variant of every table is carried NAMED (the mission's
"use the corrected variant, named"); the statics receipt measured the ankle
column bit-identical under both machinery versions - re-measured here.

Run:  python -B tools/science_funnel/validation/ankle_unblocked_statics_20260921/derive_ankle_unblocked_statics.py
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
ANKLE_BOOK = LANE / "inputs" / "ankle_arms_book.json"
SNAP_STANCE = LANE / "inputs" / "stance_hold.snapshot.json"
RUN_ENV = LANE / "inputs" / "run_env" / "tools" / "science_funnel" / "validation"
RUN_ENV_WAVE4 = LANE / "inputs" / "run_env_wave4" / "tools" / "science_funnel" / "validation"
VENDORED_SCRIPT = RUN_ENV / "gait_zero_20260919" / "derive_stance_hold.py"
VENDORED_SCRIPT_WAVE4 = RUN_ENV_WAVE4 / "gait_zero_20260919" / "derive_stance_hold.py"
REGEN_STANCE = RUN_ENV / "gait_zero_20260919" / "stance_hold.json"
REGEN_STANCE_WAVE4 = RUN_ENV_WAVE4 / "gait_zero_20260919" / "stance_hold.json"
WAVE10_WALL = LANE / "inputs" / "vendored_gait_zero" / "trunk_vault_reachable.wave10.json"
HIND_BOOK = LANE.parents[0] / "hind_torque_book_20260921" / "hind_torque_book.json"
STATICS_COMMITTED = LANE / "inputs" / "statics_lane_committed_deliverable.json"
OUT = LANE / "ankle_unblocked_statics.json"

PINS = {
    "ankle_arms_book": (ANKLE_BOOK, "7ce03069c1e033b52db0fb315d218eb2223e79a67a9018123da206d68adcb6f6"),
    "stance_hold_snapshot": (SNAP_STANCE, "71e40cd8a161938a3a358792076dda0f98966a8909ae564cec7774a61126a5e5"),
    # the wave-4 script AS COMMITTED at 724f2464 - the version that GENERATED the banked stance_hold.json
    "wave4_machinery_byte_copy": (VENDORED_SCRIPT_WAVE4, "353d07f7f18a7fa371c43eef18e40d3160d58855a24b464ef587e526bd0f81c0"),
    # the wave-8-era script (4198dbdc head; carries the MP-Jacobian fix)
    "wave8_machinery_byte_copy": (VENDORED_SCRIPT, "3c92d188b6aaf01c8cc4319262981b51ba95566370fb59e1ba4d0dd764562f70"),
    "wave10_wall_deliverable": (WAVE10_WALL, "e922153318778e4cd8c1891f59454261c6d5be0a77aebdc5f78d2758ccd2faa7"),
    "hind_torque_book": (HIND_BOOK, "9fc5c0ba09f6ec183d5348bb21cc5dc18b5987240406ccdcdbb34e514e26f01c"),
    "statics_lane_committed_deliverable": (STATICS_COMMITTED, "21d3dbbe2a477d67f7d7d5572f0171cd0c2e8cfe34a6cd1770ccd81abf06908a"),
}

JOINTS = ["hip", "knee", "ankle", "mp", "posture"]
TAU_KEY = {"hip": "tau_hip_Nm", "knee": "tau_knee_Nm", "ankle": "tau_ankle_Nm",
           "mp": "tau_mp_Nm", "posture": "tau_posture_Nm"}

# (d) measured ankle caps from the ankle book (V1_S1 both directions) and the
# S2 gate caps - all traced to key paths in the sha-pinned books (the derive
# reads the books; these paths are asserted to exist and re-pinned in cap_trace).
ANKLE_D = {"plantar": 6.247077, "dorsal": 1.251106}
ANKLE_D_KEY = {"plantar": "cap_book.ankle_plantarflexion.V1_S1_oku_walk_peaks_deposit_arms.cap_N_m",
               "dorsal": "cap_book.ankle_dorsiflexion.V1_S1_oku_walk_peaks_deposit_arms.cap_N_m"}
ANKLE_D_S2 = {"plantar": 0.748112, "dorsal": 0.149825}
ANKLE_D_S2_KEY = {"plantar": "cap_book.ankle_plantarflexion.V1_S2_oku_peaks_si_matched_arms.cap_N_m",
                  "dorsal": "cap_book.ankle_dorsiflexion.V1_S2_oku_peaks_si_matched_arms.cap_N_m"}

PROV_CLASS = {
    "A_live_doc": {"hip": "LIVE_DOC", "knee": "LIVE_DOC", "ankle": "LIVE_DOC",
                   "mp": "LIVE_DOC", "posture": "LIVE_DOC_KEYED_TO_HIP"},
    "B_measured_v1_s1": {"hip": "HELD_FROM_A", "knee": "MEASURED_V1_S1_BOOK",
                         "ankle": "LIVE_DOC_HELD_AT_A_STATICS_LANE_BLOCKED",
                         "mp": "MEASURED_V1_S1_BOOK", "posture": "HELD_FROM_A_KEYED_TO_HIP"},
    "C_provisional_v2_s1": {"hip": "HELD_FROM_A", "knee": "PROVISIONAL_V2_S1_BOOK",
                            "ankle": "LIVE_DOC_HELD_AT_A_STATICS_LANE_BLOCKED",
                            "mp": "PROVISIONAL_V2_S1_BOOK", "posture": "HELD_FROM_A_KEYED_TO_HIP"},
    "D_measured_ankle_unblocked": {"hip": "HELD_FROM_A", "knee": "MEASURED_V1_S1_BOOK",
                                   "ankle": "MEASURED_V1_S1_ANKLE_BOOK_DIRECTION_SPLIT_PLANTAR_NEG_DORSAL_POS",
                                   "mp": "MEASURED_V1_S1_BOOK", "posture": "HELD_FROM_A_KEYED_TO_HIP"},
    "D_S2_si_matched_gate": {"hip": "HELD_FROM_A", "knee": "SI_MATCHED_GATE_BOOK",
                             "ankle": "SI_MATCHED_GATE_ANKLE_BOOK_DIRECTION_SPLIT",
                             "mp": "SI_MATCHED_GATE_BOOK", "posture": "HELD_FROM_A_KEYED_TO_HIP"},
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs():
    """REFUSES to run on any sha mismatch (the traceability falsifier)."""
    for name, (path, pin) in PINS.items():
        got = sha256(path)
        if got != pin:
            raise SystemExit(f"sha mismatch {name}: {path} {got} != {pin}")
    ankle = json.loads(ANKLE_BOOK.read_text(encoding="utf-8"))
    stance = json.loads(SNAP_STANCE.read_text(encoding="utf-8"))
    wall = json.loads(WAVE10_WALL.read_text(encoding="utf-8"))
    book = json.loads(HIND_BOOK.read_text(encoding="utf-8"))
    committed = json.loads(STATICS_COMMITTED.read_text(encoding="utf-8"))
    return ankle, stance, wall, book, committed


def dig(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        cur = cur[part]
    return cur


def book_caps(book):
    """The (a)-(c)/S2 knee/MP caps, the statics lane's own key paths."""
    r = book["rederivation"]
    ke, mf = r["knee_extension"]["variants"], r["mtp_flexion"]["variants"]
    return {
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


def run_vendored_statics(script, out_path):
    """Run a BYTE-UNMODIFIED vendored deriver; return its regenerated rows."""
    res = subprocess.run([sys.executable, "-B", str(script)],
                         capture_output=True, text=True, timeout=300)
    if res.returncode != 0:
        raise SystemExit(f"vendored statics failed:\n{res.stderr}")
    return json.loads(Path(out_path).read_text(encoding="utf-8"))


def stance_table(rows, caps, ankle_dir_split=None):
    """Per-node ratios at one cap set; demands are cap-independent.

    ankle_dir_split=(plantar, dorsal) prices the ankle by the book's sign gate:
    tau < 0 (plantarflexion) at `plantar`, tau > 0 (dorsiflexion) at `dorsal`.
    """
    nodes = []
    for n in rows:
        r = {}
        for j in JOINTS:
            cap = caps[j]
            if j == "ankle" and ankle_dir_split is not None:
                cap = ankle_dir_split[0] if float(n[TAU_KEY[j]]) < 0 else ankle_dir_split[1]
            r[j] = abs(float(n[TAU_KEY[j]])) / cap
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
        if holders:
            mh = max(holders, key=lambda t: t[1])
            holding = {"worst_holding_ratio": round(mh[1], 6), "worst_holding_phi": nodes[mh[0]]["phi"]}
        else:
            # every node over-cap at this joint (reachable at the S2 gate) - no holding class exists
            holding = {"worst_holding_ratio": None, "worst_holding_phi": None}
        per_joint[j] = {
            "worst_ratio": round(max(ratios), 6),
            "binding_node_phi": nodes[binder]["phi"],
            "over_cap_nodes": len(over),
            "over_cap_phis": over,
            **holding,
        }
    worst = max(per_joint.items(), key=lambda kv: kv[1]["worst_ratio"])
    with_holders = [(j, v) for j, v in per_joint.items() if v["worst_holding_ratio"] is not None]
    if with_holders:
        holder = max(with_holders, key=lambda kv: kv[1]["worst_holding_ratio"])
        margin_holding = {"joint": holder[0], "phi": holder[1]["worst_holding_phi"],
                          "ratio": holder[1]["worst_holding_ratio"]}
    else:
        margin_holding = {"joint": None, "phi": None, "ratio": None}
    return {
        "nodes": nodes,
        "per_joint": per_joint,
        "worst_case_ratio": worst[1]["worst_ratio"],
        "worst_case_binder": {"joint": worst[0], "phi": worst[1]["binding_node_phi"]},
        "margin_binder_holding": margin_holding,
    }


def wall_reprice(wall, caps_a, caps_x):
    """The wave-10/25 margin wall re-priced - the statics lane's own law:
    each joint's banked ratio divided by that joint's cap headroom."""
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
    hist = {}
    for nd in nodes:
        hist[nd["binder"]] = hist.get(nd["binder"], 0) + 1
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
        "ankle_term_at_phi_0_5": round(
            next(nd["terms"]["ankle"] for nd in nodes if nd["phi"] == 0.5), 6),
        "binder_histogram": hist,
    }


def first_diff(a, b, path="", exclude=()):
    """First field-level difference between two JSON structures (top-level
    `exclude` keys of `a` are lane additions the committed schema does not
    carry - skipped, never absorbed)."""
    if type(a) is not type(b):
        return f"{path}: type {type(a).__name__} vs {type(b).__name__}"
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k in exclude and k not in b:
                continue
            if k not in a:
                return f"{path}.{k}: missing in recomputed"
            if k not in b:
                return f"{path}.{k}: missing in committed"
            d = first_diff(a[k], b[k], f"{path}.{k}")
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return f"{path}: len {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    if a != b:
        return f"{path}: {a!r} vs {b!r}"
    return None


def derive_once(ankle, stance, wall, book, committed):
    """Full derivation: pure function of the sha-verified inputs."""
    caps_book = book_caps(book)
    ab = ankle["cap_book"]
    ankle_d = {
        "plantar": ab["ankle_plantarflexion"]["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"],
        "dorsal": ab["ankle_dorsiflexion"]["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"],
    }
    ankle_ds2 = {
        "plantar": ab["ankle_plantarflexion"]["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"],
        "dorsal": ab["ankle_dorsiflexion"]["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"],
    }
    # the receipt's inline pins must equal the books (the pins are assertions)
    assert ankle_d == ANKLE_D, f"ankle (d) caps drifted: {ankle_d} != {ANKLE_D}"
    assert ankle_ds2 == ANKLE_D_S2, f"ankle (d)-S2 caps drifted: {ankle_ds2} != {ANKLE_D_S2}"

    cap_sets = {
        "A_live_doc": {"hip": 11.2125, "knee": 6.6375, "ankle": 7.4, "mp": 0.8875, "posture": 11.2125},
        "B_measured_v1_s1": {"hip": 11.2125, "knee": caps_book["knee_B"][0], "ankle": 7.4,
                             "mp": caps_book["mp_B"][0], "posture": 11.2125},
        "C_provisional_v2_s1": {"hip": 11.2125, "knee": caps_book["knee_C"][0], "ankle": 7.4,
                                "mp": caps_book["mp_C"][0], "posture": 11.2125},
        "D_measured_ankle_unblocked": {"hip": 11.2125, "knee": caps_book["knee_B"][0],
                                       "ankle": ankle_d["plantar"],
                                       "mp": caps_book["mp_B"][0], "posture": 11.2125},
    }
    s2_caps = {"hip": 11.2125, "knee": caps_book["knee_S2"][0], "ankle": 7.4,
               "mp": caps_book["mp_S2"][0], "posture": 11.2125}
    ds2_caps = {"hip": 11.2125, "knee": caps_book["knee_S2"][0],
                "ankle": ankle_ds2["plantar"], "mp": caps_book["mp_S2"][0], "posture": 11.2125}

    # 1. instrument: the wave-4 generator must reproduce the banked snapshot
    #    EXACTLY; the wave-8 head runs for the NAMED corrected-MP variant.
    regen_w4 = run_vendored_statics(VENDORED_SCRIPT_WAVE4, REGEN_STANCE_WAVE4)
    regen_w8 = run_vendored_statics(VENDORED_SCRIPT, REGEN_STANCE)
    eq_w4 = regen_w4["stance_nodes"] == stance["stance_nodes"]
    mp_diffs = [
        {"phi": x["phi"], "banked_mp": y["tau_mp_Nm"], "wave8_corrected_mp": x["tau_mp_Nm"]}
        for x, y in zip(regen_w8["stance_nodes"], stance["stance_nodes"]) if x != y
    ]
    ankle_identical = all(
        x["tau_ankle_Nm"] == y["tau_ankle_Nm"]
        for x, y in zip(regen_w8["stance_nodes"], stance["stance_nodes"]))
    instrument = {
        "wave4_script_run": "inputs/run_env_wave4/.../derive_stance_hold.py (byte copy of 724f2464, the banked table's generator)",
        "wave4_reproduces_banked_exactly": eq_w4,
        "rows": len(regen_w4["stance_nodes"]),
        "banked_rows": len(stance["stance_nodes"]),
        "wave8_script_run": "inputs/run_env/.../derive_stance_hold.py (byte copy of the 4198dbdc head; the wave-8 MP-Jacobian fix)",
        "wave8_vs_banked_diff_cells": len(mp_diffs),
        "ankle_column_bit_identical_wave8_vs_wave4": ankle_identical,
        "lineage_note": ("the wave-8 corrected MP column is the NAMED variant (the mission's 'use the corrected "
                         "variant, named'); the ankle/knee/hip/posture columns are re-measured bit-identical here, "
                         "so no ANKLE verdict depends on the machinery choice"),
    }
    if not eq_w4:
        instrument["first_diff_w4"] = next(
            (i for i, (x, y) in enumerate(zip(regen_w4["stance_nodes"], stance["stance_nodes"])) if x != y),
            None)
    rows = stance["stance_nodes"]

    # 2. tables: (a)-(c) recomputed (the chain), (d) + S2 gate (the new sets).
    #    (d) prices the ankle DIRECTION-SPLIT per the receipt's named law
    #    (plantar negative / dorsal positive) - the banked ankle column carries
    #    both signs, so a single-cap price would be a law violation, not a
    #    convention choice.
    tables = {name: stance_table(rows, caps) for name, caps in cap_sets.items()
              if name != "D_measured_ankle_unblocked"}
    tables["D_measured_ankle_unblocked"] = stance_table(
        rows, cap_sets["D_measured_ankle_unblocked"],
        ankle_dir_split=(ankle_d["plantar"], ankle_d["dorsal"]))
    tables["S2_si_matched_gate"] = stance_table(rows, s2_caps)
    tables["D_S2_si_matched_gate"] = stance_table(rows, ds2_caps, ankle_dir_split=(ankle_ds2["plantar"], ankle_ds2["dorsal"]))
    tables_mp_corrected = {name: stance_table(regen_w8["stance_nodes"], caps)
                           for name, caps in cap_sets.items()}
    tables_mp_corrected["D_S2_si_matched_gate"] = stance_table(
        regen_w8["stance_nodes"], ds2_caps, ankle_dir_split=(ankle_ds2["plantar"], ankle_ds2["dorsal"]))

    # 3. the PD1 chain: (a)/(b)/(c) + their walls must equal the committed
    #    statics deliverable FIELD-FOR-FIELD
    chain_sets = ["A_live_doc", "B_measured_v1_s1", "C_provisional_v2_s1", "S2_si_matched_gate"]
    chain = {"committed_sha256": PINS["statics_lane_committed_deliverable"][1], "checks": {}}
    chain_ok = True
    for name in chain_sets:
        d = first_diff(tables[name], committed["stance_tables"][name], f"stance_tables.{name}")
        chain["checks"][f"stance_tables.{name}"] = d or "EQUAL"
        chain_ok = chain_ok and d is None
    for name in [n for n in chain_sets if n in committed["stance_tables_wave8_corrected_mp_VARIANT"]]:
        d = first_diff(tables_mp_corrected[name], committed["stance_tables_wave8_corrected_mp_VARIANT"][name],
                       f"stance_tables_wave8_corrected_mp_VARIANT.{name}")
        chain["checks"][f"mp_variant.{name}"] = d or "EQUAL"
        chain_ok = chain_ok and d is None
    walls_all = {name: wall_reprice(wall, cap_sets["A_live_doc"], caps)
                 for name, caps in list(cap_sets.items()) + [("S2_si_matched_gate", s2_caps)]}
    walls_all["D_S2_si_matched_gate"] = wall_reprice(wall, cap_sets["A_live_doc"], ds2_caps)
    # the dorsal-bracket wall at (d): the receipt's named bracket (same law,
    # ankle priced at the dorsal cap)
    dorsal_caps = dict(cap_sets["D_measured_ankle_unblocked"])
    dorsal_caps["ankle"] = ankle_d["dorsal"]
    walls_all["D_dorsal_bracket"] = wall_reprice(wall, cap_sets["A_live_doc"], dorsal_caps)
    walls_all["D_dorsal_bracket"]["named_law"] = "the receipt's DORSAL bracket: every wall ankle term priced at the dorsal cap 1.251106 - the pessimistic direction of the named plantar law"
    for name in chain_sets:
        d = first_diff(walls_all[name], committed["margin_wall"][name], f"margin_wall.{name}",
                       exclude=("ankle_term_at_phi_0_5", "binder_histogram", "named_law"))
        chain["checks"][f"margin_wall.{name}"] = d or "EQUAL"
        chain_ok = chain_ok and d is None
    chain["all_equal_committed_statics"] = chain_ok

    # 4. provenance on the table
    prov = {
        "cap_sets": {name: {"caps": cap_sets[name], "provenance_class": PROV_CLASS[name]}
                     for name in cap_sets},
        "cap_sets_direction_split": {
            "D_measured_ankle_unblocked": {"ankle_plantarflexion_tau_negative": ankle_d["plantar"],
                                           "ankle_dorsiflexion_tau_positive": ankle_d["dorsal"]},
            "D_S2_si_matched_gate": {"ankle_plantarflexion_tau_negative": ankle_ds2["plantar"],
                                     "ankle_dorsiflexion_tau_positive": ankle_ds2["dorsal"]},
        },
        "ankle_cap_trace": {
            "input": "inputs/ankle_arms_book.json (git blob f55ebe5f at b15ff31e, branch agent/ankle-arms-20260921)",
            "sha256": PINS["ankle_arms_book"][1],
            "key_paths": {**ANKLE_D_KEY, **ANKLE_D_S2_KEY},
            "values": {**{f"D_{k}": v for k, v in ankle_d.items()},
                       **{f"D_S2_{k}": v for k, v in ankle_ds2.items()}},
            "sign_gate": "the ankle book's cap_law: 'plantar negative / dorsal positive'",
        },
        "hind_book_cap_trace": {
            "input": "tools/science_funnel/validation/hind_torque_book_20260921/hind_torque_book.json (in-tree at eab707f5)",
            "sha256": PINS["hind_torque_book"][1],
            "key_paths": {k: v[1] for k, v in caps_book.items()},
            "values": {k: v[0] for k, v in caps_book.items()},
        },
        "demand_trace": {
            "input": "inputs/stance_hold.snapshot.json (byte copy, sha equals the statics receipt's pin)",
            "sha256": PINS["stance_hold_snapshot"][1],
            "key_path": "stance_nodes[].tau_{hip,knee,ankle,mp,posture}_Nm",
            "ankle_sign_classes": {"dorsiflexion_tau_positive_phis": [0.0, 0.05, 0.1, 0.15, 0.2, 0.25],
                                   "plantarflexion_tau_negative_phis": [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.449]},
        },
        "wall_trace": {
            "input": "inputs/vendored_gait_zero/trunk_vault_reachable.wave10.json (byte copy at 4198dbdc)",
            "sha256": PINS["wave10_wall_deliverable"][1],
            "key_path": "nodes[].leg_ratios + nodes[].posture_ratio",
            "direction_law": "the wall artifact carries leg_ratios ONLY (no signed ankle torques); the ankle term re-prices at the PLANTAR cap per the receipt's NAMED law, the DORSAL bracket wall computed alongside (walls.D_dorsal_bracket)",
        },
        "cap_provenance_classes": {
            "LIVE_DOC": "1.25 x the DOC-ROUNDED Oku walk peaks - the live graph-contract/engine pin (torque book audit)",
            "LIVE_DOC_KEYED_TO_HIP": "the posture drive borrows the hip cap (cap-on-each, the live contract) - the (a) set's class, carried for the chain check",
            "MEASURED_V1_S1_BOOK": "Oku measured walk forces x pulley-lane MEASURED deposit arms (hind book V1_S1)",
            "PROVISIONAL_V2_S1_BOOK": "PCSA x sigma x cos(pennation) x measured deposit arms (hind book V2_S1) - PROVISIONAL by the standing order (the sigma caveat)",
            "MEASURED_V1_S1_ANKLE_BOOK_DIRECTION_SPLIT_PLANTAR_NEG_DORSAL_POS": "the ankle-arms lane's MEASURED wrap-arm caps, V1_S1, both directions, sign-gated per the book's own cap_law (blob f55ebe5f at b15ff31e)",
            "SI_MATCHED_GATE_ANKLE_BOOK_DIRECTION_SPLIT": "the ankle book's V1_S2 caps (arms x k = 0.11975394), both directions",
            "SI_MATCHED_GATE_BOOK": "the hind book's S2 caps (arms x k) - the standing scale gate, INVERSION bracket",
            "HELD_FROM_A": "this lane re-derives nothing for the hip (the posture-cap lane's 10.54 N.m amendment stays banked-unconsumed)",
            "HELD_FROM_A_KEYED_TO_HIP": "the posture cap stays at the (a) hip-keyed value",
            "LIVE_DOC_HELD_AT_A_STATICS_LANE_BLOCKED": "the (b)/(c) ankle cap the statics lane doc-held (blocked at its base) - carried UNCHANGED for the chain check, superseded by (d)",
        },
    }

    # 5. the verdict
    d_tab = tables["D_measured_ankle_unblocked"]
    d_s2_tab = tables["D_S2_si_matched_gate"]
    d_wall = walls_all["D_measured_ankle_unblocked"]
    d_wall_dorsal = walls_all["D_dorsal_bracket"]
    ds2_wall = walls_all["D_S2_si_matched_gate"]
    d_corr = tables_mp_corrected["D_measured_ankle_unblocked"]
    b_wall = walls_all["B_measured_v1_s1"]
    a_tab = tables["A_live_doc"]
    verdict = {
        "instrument_chain_held": bool(eq_w4 and chain_ok),
        "ankle_unblocked_verdict": {
            "question": "the stance-hold table at (d): the ankle's worst ratio and over-cap count - the ankle lane's statics-side table predicted 6 over-cap nodes at V1_S1",
            "ankle_over_cap_nodes": d_tab["per_joint"]["ankle"]["over_cap_nodes"],
            "ankle_over_cap_phis": d_tab["per_joint"]["ankle"]["over_cap_phis"],
            "ankle_worst_ratio": d_tab["per_joint"]["ankle"]["worst_ratio"],
            "ankle_binding_phi": d_tab["per_joint"]["ankle"]["binding_node_phi"],
            "dorsal_class_over_cap_nodes": len([nd for nd in d_tab["nodes"]
                                                if nd["tau_Nm"]["ankle"] > 0 and nd["ratio"]["ankle"] > 1.0]),
            "dorsal_class_worst_ratio": max(nd["ratio"]["ankle"] for nd in d_tab["nodes"] if nd["tau_Nm"]["ankle"] > 0),
            "ankle_lane_prediction": "consumption_map.stance_hold_ankle_nodes (ankle book): after=6 over, binding demand -7.215 at phi=0.3 ratio_after 1.1549",
            "verified_from_the_statics_side": (
                d_tab["per_joint"]["ankle"]["over_cap_nodes"] == 6
                and d_tab["per_joint"]["ankle"]["binding_node_phi"] == 0.3),
        },
        "wall_verdict": {
            "question": "does the statics lane's 1.0-crossing (0.977235 at (b)/(c), ankle doc-held) SURVIVE the measured ankle - and does the 0.9 margin move",
            "wall_ratio_B_doc_held_ankle": b_wall["max_combined_ratio"],
            "wall_ratio_D_measured_ankle": d_wall["max_combined_ratio"],
            "wall_binder_D": d_wall["max_binder"],
            "ankle_term_at_phi_0_5_D": d_wall["ankle_term_at_phi_0_5"],
            "crosses_1_0_under_D": d_wall["crosses_1_0"],
            "crosses_1_0_under_B_was": b_wall["crosses_1_0"],
            "margin_0_9_reachable_under_D": d_wall["margin_0_9_reachable"],
            "margin_value_moved": "0.977235 -> {v:.6f} - AWAY from the 0.9 margin (it does not move toward reachability; it re-blocks)".format(v=d_wall["max_combined_ratio"]),
            "knee_term_at_phi_0_75_D": d_wall["knee_term_at_phi_0_75"],
            "dorsal_bracket_wall_max": d_wall_dorsal["max_combined_ratio"],
            "dorsal_bracket_binder": d_wall_dorsal["max_binder"],
            "nodes_over_1_0_D": d_wall["nodes_over_1_0"],
            "statement": ("THE CROSSING DOES NOT SURVIVE. The doc cap the wall wore at (a)-(c) (7.4) was TIGHTER-"
                          "bound only by the knee; once the knee clears (the statics lane's result) the wall's fate "
                          "rests entirely on the ankle - and the MEASURED plantar cap (6.247077) is TIGHTER than the "
                          "doc cap by factor 0.8447, so the binding ankle term GROWS: {b:.6f} -> {d:.6f}. The wall "
                          "RE-BLOCKS at phi=0.5 ankle-bound. The statics receipt's own finding pointed here: its (b)/(c) "
                          "crossing was held UNDER 1.0 precisely by the BLOCKED (over-generous) doc ankle - the honest "
                          "statics verdict under measured caps for ALL loaded leg joints is that the banked wave-10 "
                          "optimum is INFEASIBLE again, and the ANKLE owns the wall. Direction-robust: under the "
                          "receipt's dorsal bracket the same node re-blocks at {db:.6f}. Clearing 1.0 now needs the "
                          "ankle-side capability (the PROVISIONAL V2_S1 plantar cap 18.595726 would clear it) or a "
                          "re-collocation hearing at the new caps - both named future work, not measured here."
                          ).format(b=b_wall["max_combined_ratio"], d=d_wall["max_combined_ratio"],
                                   db=d_wall_dorsal["max_combined_ratio"]),
        },
        "binder_map": {
            "question": "which joint owns what at (d)",
            "stance_table_worst_case_binder_banked_mp": {
                "joint": d_tab["worst_case_binder"]["joint"], "phi": d_tab["worst_case_binder"]["phi"],
                "ratio": d_tab["worst_case_ratio"]},
            "stance_table_worst_case_binder_wave8_corrected_mp_VARIANT": {
                "joint": d_corr["worst_case_binder"]["joint"], "phi": d_corr["worst_case_binder"]["phi"],
                "ratio": d_corr["worst_case_ratio"],
                "note": ("the windlass MP class VANISHES under the corrected column (the statics receipt's F3, "
                         "confirmed at (d)); the table's worst case falls to the POSTURE column (the receipt's "
                         "pre-registered band named the HIP - the prior omitted the posture column's worst; FIRED, "
                         "recorded with its number in the receipt's measured block)")},
            "wall_owner": {"joint": d_wall["max_binder"]["joint"], "phi": d_wall["max_binder"]["phi"],
                           "state": "OVER-CAP - the ankle OWNS the wall (at (b)/(c) it merely held it at 0.977235)"},
            "wall_binder_histogram_D": d_wall["binder_histogram"],
            "margin_binder_holding_class": {
                "joint": d_tab["margin_binder_holding"]["joint"], "phi": d_tab["margin_binder_holding"]["phi"],
                "ratio": d_tab["margin_binder_holding"]["ratio"],
                "migration": "(a) ankle-plantar 0.975 @ phi=0.3 -> (d) ankle-DORSAL 0.987926 @ phi=0.25 - the last sub-unity ankle class is the dorsal double-support one, and it sits at 0.988"},
            "per_joint_d": {j: {k: v for k, v in d_tab["per_joint"][j].items()} for j in JOINTS},
        },
        "the_scale_gate": ("S1 GATE ON EVERY VERDICT ABOVE: sets (b)/(c)/(d) stand on the DEPOSIT arm scale (the "
                           "ankle book's own SI2 cross-check fits k_ankle = 0.11976026 over the point-class arms - "
                           "consistent with the MTP class and with the k = 0.11975394 used for the S2 caps). At the "
                           "SI-matched scale the books collapse (knee 1.146859, MP 0.198543, ankle plantar 0.748112, "
                           "dorsal 0.149825) and every (d) verdict INVERTS: the ankle is over-cap at {s2n}/15 nodes "
                           "(worst {s2w} at phi=0.3; the dorsal class too: {s2d} at phi=0.25), knee {s2k}/15, wall "
                           "max combined {s2wall} ankle-bound at phi=0.5 (plantar law; knee term {s2kt} at phi=0.75) - "
                           "the walker can neither hold nor vault. No engine consumption is lawful until the operator "
                           "resolves the k divergence (the torque book's standing gate, inherited verbatim).").format(
                               s2n=d_s2_tab["per_joint"]["ankle"]["over_cap_nodes"],
                               s2w=d_s2_tab["per_joint"]["ankle"]["worst_ratio"],
                               s2d=max(nd["ratio"]["ankle"] for nd in d_s2_tab["nodes"] if nd["tau_Nm"]["ankle"] > 0),
                               s2k=d_s2_tab["per_joint"]["knee"]["over_cap_nodes"],
                               s2wall=ds2_wall["max_combined_ratio"],
                               s2kt=ds2_wall["knee_term_at_phi_0_75"]),
        "worst_case_ratios": {name: tables[name]["worst_case_ratio"] for name in tables},
        "honest_reds": [
            "the wall's direction law is an ALIGNMENT decision, not a measurement: the wave-10 artifact carries "
            "ratios only, so the receipt NAMED the plantar law before compute and bounds it with the dorsal bracket "
            "[1.157587, 5.780115] at phi=0.5 - a signed-torque wave-10 artifact would retire it",
            "the stance-hold push-off tail stays OVER at (d): knee ratios at phi 0.55/0.6/0.65 unchanged from (b) "
            "({b55:.4f}/{b6:.4f}/{b65:.4f}) - the measured knee book covers entry/mid-window, not the push-off "
            "statics (only the PROVISIONAL V2 cap clears them)".format(
                b55=next(nd["ratio"]["knee"] for nd in tables["B_measured_v1_s1"]["nodes"] if nd["phi"] == 0.55),
                b6=next(nd["ratio"]["knee"] for nd in tables["B_measured_v1_s1"]["nodes"] if nd["phi"] == 0.6),
                b65=next(nd["ratio"]["knee"] for nd in tables["B_measured_v1_s1"]["nodes"] if nd["phi"] == 0.65)),
            "the hip and posture columns gain NOTHING at (d) (caps held): 4/15 over each, unchanged from every set - "
            "the 10.54 N.m muscle-grounded posture amendment stays banked-unconsumed",
            "the banked MP windlass flags (phi 0.0-0.25) stay over at (d) on the banked demands (worst {m:.4f}) - "
            "the wave-8 corrected column says the class is an ARTIFACT (worst {c:.4f}); the table is carried both "
            "ways, named, never silently substituted".format(
                m=d_tab["per_joint"]["mp"]["worst_ratio"], c=d_corr["per_joint"]["mp"]["worst_ratio"]),
            "the wall verdict is measured AT THE BANKED wave-10 optimum under the statics lane's re-price law; a "
            "collocation re-hearing at the measured caps could move the ankle terms - named future work",
        ],
    }

    return {
        "schema": "chimera.ankle_unblocked_statics.v1",
        "lane": "ankle-unblocked-statics-20260921",
        "derived_from_commit": "eab707f5 (branch agent/measured-caps-statics-20260921); ankle artifacts from b15ff31e (branch agent/ankle-arms-20260921, blob f55ebe5f)",
        "receipt": "receipt.json (pre-registration written before this script existed)",
        "instrument": instrument,
        "statics_chain_reproduction": chain,
        "cap_sets": prov["cap_sets"],
        "cap_sets_direction_split": prov["cap_sets_direction_split"],
        "cap_provenance_classes": prov["cap_provenance_classes"],
        "ankle_cap_trace": prov["ankle_cap_trace"],
        "hind_book_cap_trace": prov["hind_book_cap_trace"],
        "demand_trace": prov["demand_trace"],
        "wall_trace": prov["wall_trace"],
        "stance_tables": tables,
        "stance_tables_wave8_corrected_mp_VARIANT": tables_mp_corrected,
        "margin_wall": walls_all,
        "verdict": verdict,
    }


def main():
    ankle, stance, wall, book, committed = load_inputs()
    d1 = derive_once(ankle, stance, wall, book, committed)
    d2 = derive_once(ankle, stance, wall, book, committed)
    j1 = json.dumps(d1, sort_keys=True, indent=1)
    j2 = json.dumps(d2, sort_keys=True, indent=1)
    if j1 != j2:
        raise SystemExit("NON-DETERMINISTIC: two in-process derivations disagree")
    OUT.write_text(j1 + "\n", encoding="utf-8", newline="\n")
    digest = hashlib.sha256((j1 + "\n").encode("utf-8")).hexdigest()
    print("deliverable:", OUT)
    print("sha256:", digest)
    print("instrument_chain_held:", d1["verdict"]["instrument_chain_held"])
    for name in ("D_measured_ankle_unblocked", "D_S2_si_matched_gate"):
        t = d1["stance_tables"][name]
        aj = t["per_joint"]["ankle"]
        print(f"{name}: ankle worst {aj['worst_ratio']} over {aj['over_cap_nodes']}/15 {aj['over_cap_phis']} "
              f"table-worst {t['worst_case_ratio']} ({t['worst_case_binder']['joint']} phi={t['worst_case_binder']['phi']})")
    for name in ("D_measured_ankle_unblocked", "D_dorsal_bracket", "D_S2_si_matched_gate"):
        w = d1["margin_wall"][name]
        print(f"wall {name}: max {w['max_combined_ratio']} binder {w['max_binder']} "
              f"crosses_1_0 {w['crosses_1_0']} margin_0_9 {w['margin_0_9_reachable']}")


if __name__ == "__main__":
    main()
