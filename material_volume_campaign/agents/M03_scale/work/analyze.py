"""M03 analysis: compare exporter/admission receipts against the FROZEN prereg.

Three verdict layers, reported separately and honestly:
  A. PREREG-AS-FROZEN: absolute comparison against the anchor values exactly as
     written in PREREG.md (sha256 59adffa6...). Deviations here are recorded as
     they stand -- if the frozen anchor was mis-derived, that deviation is
     PRESERVED, never silently retuned.
  B. CORRECTED ANCHORS (logged errata): exact rational re-derivation, shown in
     ERRATA.md with the arithmetic that corrects the frozen slips.
  C. LAW / RATIO TESTS (anchor-free, the objective of this task):
     observed(s)/observed(1) must equal s^3 (mass, volume), s (COM with o=0),
     the affine law (COM with o!=0, tested absolutely), and s^5 (all 9 inertia
     entries). Plus the discrimination test: COM_B must NOT follow the
     pure-linear law s*COM_B(1), because origin_m is in metres and unscaled.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENTS = HERE.parent
RECEIPTS = AGENTS / "receipts"

SCALES = [("1.0", "s1p0"), ("0.5", "s0p5"), ("2.0", "s2p0"), ("0.065", "s0p065")]
TOL = Fraction(1, 10**9)


def F(*args) -> Fraction:
    return Fraction(*args)


# ---------------------------------------------------------------- anchors ----
# Exactly as frozen in PREREG.md.
FROZEN = {
    "A_mass": F(2), "A_volume": F(1, 6),
    "A_com": [F(1, 4)] * 3,
    "A_inertia": [[F(3, 20), F(1, 40), F(1, 40)],
                  [F(1, 40), F(3, 20), F(1, 40)],
                  [F(1, 40), F(1, 40), F(3, 20)]],
    "B_mass": F(1), "B_volume": F(1, 6),
    "B_com": [F(1, 4)] * 3,
    "B_inertia": [[F(3, 40), F(-1, 80), F(1, 80)],
                  [F(-1, 80), F(3, 40), F(-1, 80)],
                  [F(1, 80), F(-1, 80), F(3, 40)]],
    "geo_volume": F(1, 3), "comb_mass": F(3),
    "comb_com": [F(13, 12), F(-5, 12), F(7, 12)],
    "comb_inertia": [[F(347, 144), F(803, 240), F(-397, 240)],
                     [F(803, 240), F(491, 144), F(329, 240)],
                     [F(-397, 240), F(329, 240), F(683, 144)]],
}

# Corrected anchors (see ERRATA.md): body-B tensor sign fix via x_body(b2) =
# (0,1,0) not (0,-1,0); combined diagonals fixed (denominator slips), verified
# by the independent trace check tr(I_comb(1)) = 0.45+0.225+2*(2*5/4+1*5) = 15.675.
CORRECTED = dict(FROZEN)
CORRECTED["B_inertia"] = [[F(3, 40), F(1, 80), F(1, 80)],
                          [F(1, 80), F(3, 40), F(1, 80)],
                          [F(1, 80), F(1, 80), F(3, 40)]]
CORRECTED["comb_inertia"] = [[F(427, 120), F(803, 240), F(-397, 240)],
                             [F(803, 240), F(607, 120), F(329, 240)],
                             [F(-397, 240), F(329, 240), F(847, 120)]]


def expected(anchors: dict, scale: Fraction):
    """Expected value of every preregistered quantity at a scale (exact)."""
    s3, s5 = scale**3, scale**5
    com_b = [F(2) - 7 * scale / 4, F(3) - 11 * scale / 4, 5 * scale / 4 - 1]
    exp = {
        "A.mass_kg": anchors["A_mass"] * s3,
        "A.volume_m3": anchors["A_volume"] * s3,
        "B.mass_kg": anchors["B_mass"] * s3,
        "B.volume_m3": anchors["B_volume"] * s3,
        "geo.volume_m3": anchors["geo_volume"] * s3,
        "comb.mass_kg": anchors["comb_mass"] * s3,
    }
    exp.update({
        f"A.com[{axis}]": anchors["A_com"][i] * scale for i, axis in enumerate("xyz")
    })
    exp.update({
        f"B.com[{axis}]": com_b[i] for i, axis in enumerate("xyz")
    })
    exp.update({
        f"comb.com[{axis}]": anchors["comb_com"][i] * scale
        for i, axis in enumerate("xyz")
    })
    for i, axis in enumerate("xyz"):
        for j, name in enumerate("xyz"):
            exp[f"A.I[{axis}{name}]"] = anchors["A_inertia"][i][j] * s5
            exp[f"B.I[{axis}{name}]"] = anchors["B_inertia"][i][j] * s5
            exp[f"comb.I[{axis}{name}]"] = anchors["comb_inertia"][i][j] * s5
    return exp


def observed(scale_tag: str):
    """Observed values from receipts for one scale."""
    export = json.loads((RECEIPTS / f"export_{scale_tag}.json").read_text(encoding="utf-8"))
    admission = json.loads((RECEIPTS / f"admission_{scale_tag}.json").read_text(encoding="utf-8"))
    bodies = {g["body_id"]: g for g in export["body_groups"]}
    obs = {}
    for prefix, body_id in (("A", "m03-body-A"), ("B", "m03-body-B")):
        props = bodies[body_id]["mass_properties"]
        obs[f"{prefix}.mass_kg"] = float(props["mass"]["value"])
        obs[f"{prefix}.volume_m3"] = float(props["volume"]["value"])
        for i, axis in enumerate("xyz"):
            obs[f"{prefix}.com[{axis}]"] = float(props["center_of_mass"]["value"][i])
        tensor = props["inertia_tensor_about_com"]["value"]
        for i, axis in enumerate("xyz"):
            for j, name in enumerate("xyz"):
                obs[f"{prefix}.I[{axis}{name}]"] = float(tensor[i][j])
    mp = admission["mass_authority"]["reconstructed_mass_properties"]
    obs["geo.volume_m3"] = float(admission["geometry"]["geometric_volume_m3"])
    obs["comb.mass_kg"] = float(mp["mass_kg"])
    for i, axis in enumerate("xyz"):
        obs[f"comb.com[{axis}]"] = float(mp["center_of_mass_m"][i])
    tensor = mp["inertia_com_kg_m2"]
    for i, axis in enumerate("xyz"):
        for j, name in enumerate("xyz"):
            obs[f"comb.I[{axis}{name}]"] = float(tensor[i][j])
    return obs


def rel_dev(value: float, exact: Fraction) -> float:
    expected_value = float(exact)
    return abs(value - expected_value) / abs(expected_value)


def compare_layer(observed_by_scale: dict, anchors: dict) -> list[dict]:
    rows = []
    names = sorted(expected(anchors, F(SCALES[0][0])).keys())
    for name in names:
        row = {"quantity": name}
        for scale_text, tag in SCALES:
            dev = rel_dev(observed_by_scale[tag][name], expected(anchors, F(scale_text))[name])
            row[tag] = dev
            row[f"pass_{tag}"] = dev <= float(TOL)
        row["verdict"] = "PASS" if all(row[f"pass_{tag}"] for _, tag in SCALES) else "FAIL"
        rows.append(row)
    return rows


def ratio_rows(observed_by_scale: dict) -> list[dict]:
    """Anchor-free law tests: ratios vs the s=1 run."""
    base = observed_by_scale["s1p0"]
    rows = []
    cubed = [n for n in base if n.endswith("mass_kg") or n.endswith("volume_m3")]
    quintic = [n for n in base if ".I[" in n]
    linear_com = [n for n in base if ".com[" in n and n.startswith("A.")]
    affine_com = [n for n in base if n.startswith("B.com")]
    for name in sorted(cubed):
        law = {tag: F(st) ** 3 for st, tag in SCALES}
        rows.append(law_row(name, base, observed_by_scale, law, "ratio = s^3"))
    for name in sorted(quintic):
        law = {tag: F(st) ** 5 for st, tag in SCALES}
        rows.append(law_row(name, base, observed_by_scale, law, "ratio = s^5"))
    for name in sorted(linear_com):
        law = {tag: F(st) for st, tag in SCALES}
        rows.append(law_row(name, base, observed_by_scale, law, "ratio = s (o=0)"))
    for name in sorted(affine_com):
        rows.append(affine_row(name, base, observed_by_scale))
    return rows


def law_row(name, base, observed_by_scale, law, label):
    row = {"quantity": name, "law": label}
    worst = 0.0
    for _, tag in SCALES:
        ratio = observed_by_scale[tag][name] / base[name]
        dev = abs(ratio - float(law[tag])) / abs(float(law[tag]))
        row[tag] = dev
        worst = max(worst, dev)
    row["verdict"] = "PASS" if worst <= float(TOL) else "FAIL"
    return row


def affine_row(name, base, observed_by_scale):
    row = {"quantity": name, "law": "obs(s) = s*obs(1) + (s-1)*R^T o"}
    worst = 0.0
    worst_linear = 0.0
    for scale_text, tag in SCALES:
        s = F(scale_text)
        predicted = float(s) * base[name] + float(s - 1) * AFFINE_OFFSET[name]
        dev = abs(observed_by_scale[tag][name] - predicted) / abs(predicted)
        row[tag] = dev
        worst = max(worst, dev)
        linear_pred = float(s) * base[name]
        if s != 1:
            worst_linear = max(worst_linear,
                               abs(observed_by_scale[tag][name] - linear_pred)
                               / max(abs(linear_pred), 1e-300))
    row["verdict"] = "PASS" if worst <= float(TOL) else "FAIL"
    row["max_rel_dev_vs_affine"] = worst
    row["max_rel_dev_vs_pure_linear"] = worst_linear
    return row


AFFINE_OFFSET = {
    "B.com[x]": -2.0,  # (R^T o)[0]
    "B.com[y]": -3.0,  # (R^T o)[1]
    "B.com[z]": 1.0,   # (R^T o)[2]
}


def main() -> int:
    observed_by_scale = {tag: observed(tag) for _, tag in SCALES}
    frozen_rows = compare_layer(observed_by_scale, FROZEN)
    corrected_rows = compare_layer(observed_by_scale, CORRECTED)
    law_rows = ratio_rows(observed_by_scale)

    summary = {
        "tolerance_relative": float(TOL),
        "prereg_as_frozen": {"fired": any(r["verdict"] == "FAIL" for r in frozen_rows),
                             "failing_quantities": [r["quantity"] for r in frozen_rows
                                                    if r["verdict"] == "FAIL"],
                             "rows": frozen_rows},
        "corrected_anchors": {"fired": any(r["verdict"] == "FAIL" for r in corrected_rows),
                              "failing_quantities": [r["quantity"] for r in corrected_rows
                                                     if r["verdict"] == "FAIL"],
                              "rows": corrected_rows},
        "law_ratio_tests": {"fired": any(r["verdict"] == "FAIL" for r in law_rows),
                            "failing_quantities": [r["quantity"] for r in law_rows
                                                   if r["verdict"] == "FAIL"],
                            "rows": law_rows},
    }
    (RECEIPTS / "analysis.json").write_text(json.dumps(summary, indent=1) + "\n",
                                            encoding="utf-8")

    for layer, rows in (("PREREG-AS-FROZEN", frozen_rows), ("CORRECTED ANCHORS", corrected_rows),
                        ("LAW/RATIO TESTS", law_rows)):
        failing = [r["quantity"] for r in rows if r["verdict"] == "FAIL"]
        worst = max((max(r[t] for _, t in SCALES if isinstance(r[t], float)), r["quantity"])
                    for r in rows)
        print(f"{layer}: {len(rows) - len(failing)}/{len(rows)} PASS; "
              f"failing: {failing if failing else 'none'}; worst deviation "
              f"{worst[0]:.3e} ({worst[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
