"""build_ansur_anchors.py -- the measured human, distilled.

Reads the ANSUR II public CSVs (6,068 subjects x 93 measures, US Army 2012, public since 2017 --
see research_references/human/SOURCES.md) and writes research_references/human/ansur_anchors.json:
the medians and 5th/95th percentiles the body's membranes derive from. Data, not code -- a chapter
reads the anchors, never the 3 MB CSV, and the anchors carry their provenance.
"""
from __future__ import annotations

import csv
import json
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent / "research_references" / "human"
OUT = HERE / "ansur_anchors.json"


def _load(path: Path):
    with open(path, newline="", encoding="cp1252") as f:
        return list(csv.DictReader(f))


def _col(rows, name):
    vals = []
    for r in rows:
        try:
            vals.append(float(r[name]))
        except (KeyError, ValueError):
            pass
    return vals


def _stats(vals, scale=1.0):
    vals = sorted(v * scale for v in vals if v > 0)
    if not vals:
        return None
    n = len(vals)
    return {"median": st.median(vals),
            "p5": vals[int(0.05 * n)],
            "p95": vals[min(n - 1, int(0.95 * n))],
            "mean": st.fmean(vals),
            "n": n}


def main() -> int:
    male = _load(HERE / "ANSUR_II_MALE_Public.csv")
    female = _load(HERE / "ANSUR_II_FEMALE_Public.csv")
    print(f"subjects: {len(male)} male, {len(female)} female")

    # ANSUR II units: lengths in mm, weightkg in 100 g units -- verified against the published
    # means (male mean mass ~85.5 kg, female ~67.6 kg, Paquette 2014).
    def anchors(rows, label):
        a = {}
        stature = _col(rows, "stature")
        troch = _col(rows, "trochanterionheight")
        weight = _col(rows, "weightkg")
        a["stature_m"] = _stats(stature, 0.001)
        a["trochanterion_m"] = _stats(troch, 0.001)
        # leg fraction: per-subject ratio, then median -- the honest way (ratio of medians biases)
        ratios = [t / s for t, s in zip(troch, stature) if s > 0 and t > 0]
        a["leg_frac_of_stature"] = _stats(ratios)
        eye = _col(rows, "tragiontopofhead")
        eye_frac = [(s - e) / s for s, e in zip(stature, eye) if s > 0 and e > 0]
        a["eye_frac_of_stature"] = _stats(eye_frac)
        bmi = [w * 0.1 / (s * 0.001) ** 2 for w, s in zip(weight, stature) if s > 0 and w > 0]
        a["bmi"] = _stats(bmi)
        a["mass_kg"] = _stats(weight, 0.1)
        a["foot_length_m"] = _stats(_col(rows, "footlength"), 0.001)
        a["foot_breadth_m"] = _stats(_col(rows, "footbreadthhorizontal"), 0.001)
        a["hand_length_m"] = _stats(_col(rows, "handlength"), 0.001)
        a["hand_breadth_m"] = _stats(_col(rows, "handbreadth"), 0.001)
        a["hand_circumference_m"] = _stats(_col(rows, "handcircumference"), 0.001)
        a["head_height_m"] = _stats(_col(rows, "tragiontopofhead"), 0.001)
        waist = _col(rows, "waistheightomphalion")
        waist_frac = [w / s for w, s in zip(waist, stature) if s > 0 and w > 0]
        a["waist_frac_of_stature"] = _stats(waist_frac)
        print(f"  {label}: stature {a['stature_m']['median']:.3f} m, "
              f"leg_frac {a['leg_frac_of_stature']['median']:.4f}, "
              f"bmi {a['bmi']['median']:.1f}, mass {a['mass_kg']['median']:.1f} kg")
        return a

    out = {
        "source": "ANSUR II (US Army Anthropometric Survey 2012, public release 2017) -- "
                  "4,082 male + 1,986 female subjects, 93 measures; Penn State OPEN Design Lab",
        "male": anchors(male, "male"),
        "female": anchors(female, "female"),
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
