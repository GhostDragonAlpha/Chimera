"""run_controls.py -- executes preregistered rows R1-R4 (holodeck-mat-05)
against the reference model in ONE process and writes the checks/*.txt
evidence files. Read-only with respect to the repo; writes only inside this
evidence scope. Any row miss = that row's falsifier FIRED; the fired run is
retained as checks/<name>.run1-FIRED-<cause>.txt and reported, never patched.
"""
from __future__ import annotations

import dataclasses
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "reference"))

import mat05_reference_model as m  # noqa: E402

CHECKS = HERE.parent / "checks"
CHECKS.mkdir(exist_ok=True)

fired_runs = []


def _write(name: str, title: str, rows: list, threshold: int):
    """rows: list of (id, ok, detail). Writes the .txt evidence; on any miss,
    retains a fired-run copy and exits nonzero."""
    passed = sum(1 for _, ok, _ in rows if ok)
    lines = [f"{title}",
             f"threshold: {threshold}/{len(rows)} required; "
             f"measured: {passed}/{len(rows)}",
             f"verdict: {'HOLD' if passed == len(rows) else 'FIRED'}",
             ""]
    for rid, ok, detail in rows:
        lines.append(f"[{'PASS' if ok else 'FAIL'}] {rid}")
        lines.append(f"  {detail}")
    out = CHECKS / name
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if passed != len(rows):
        fired = CHECKS / name.replace(".txt", "") + ".run1-FIRED" \
            if False else CHECKS / (out.stem + ".run1-FIRED.txt")
        fired.write_text("\n".join(lines) + "\n", encoding="utf-8")
        fired_runs.append(fired.name)
    return passed == len(rows)


def refusal_of(fn, *a, **kw):
    """Run fn; return (reason, message) if Mat05Refusal raised, else None."""
    try:
        fn(*a, **kw)
        return None
    except m.Mat05Refusal as e:
        return (e.reason, str(e))
    except Exception as e:  # unexpected exception type is a row failure
        return (f"UNEXPECTED:{type(e).__name__}", str(e))


# ---- R1 positive controls (7/7) ----------------------------------------------

def r1():
    part = m.MaterialPartition()
    rows = []

    # (a) plush_stuffed preset with SG control 0.25
    try:
        rec = part.presets.author(
            "torso_fiction", "plush_stuffed", "density", 250.0, "kg/m^3",
            "SYNTHETIC stuffed-plush assembly; declared, not measured",
            sg=0.25)
        rows.append(("R1a", rec.synthetic is True
                     and bool(rec.synthetic_label.strip()),
                     f"authored frozen PresetRecord synthetic={rec.synthetic} "
                     f"label={rec.synthetic_label!r}"))
    except Exception as e:
        rows.append(("R1a", False, f"raised {type(e).__name__}: {e}"))

    # (b) acrylic preset density 1180 -> PRESET store; calibrated stays empty
    try:
        part.presets.author(
            "eye_fiction", "acrylic", "density", 1180.0, "kg/m^3",
            "SYNTHETIC PMMA-like preset; declared, not measured", sg=1.18)
        ok = len(part.presets) == 2 and len(part.calibrated) == 0
        rows.append(("R1b", ok, f"preset store n={len(part.presets)}, "
                     f"calibrated store n={len(part.calibrated)} (must be 0)"))
    except Exception as e:
        rows.append(("R1b", False, f"raised {type(e).__name__}: {e}"))

    # (c) calibrated researched white-oak density with source + conditions
    try:
        crec = part.calibrated.admit(
            "white_oak", "density", 680.0, "kg/m^3",
            "USDA FPL GTR-190 T5-3b via SG 0.68 x 1000 kg/m^3 basis",
            "clear straight-grained wood, 12% MC", "researched")
        ok = (crec.provenance == "researched"
              and len(part.calibrated) == 1)
        rows.append(("R1c", ok, f"admitted calibrated record "
                     f"{crec.name}.{crec.prop} provenance={crec.provenance}"))
    except Exception as e:
        rows.append(("R1c", False, f"raised {type(e).__name__}: {e}"))

    # (d) sg_to_density(0.68, 1000) -> Quantity 680, Dimension (L^-3 M)
    try:
        q = m.sg_to_density(0.68, 1000.0)
        want = m.m01.Dimension((-3, 1, 0))
        ok = q.value == 680.0 and q.dimension == want
        rows.append(("R1d", ok,
                     f"sg_to_density(0.68, 1000) = Quantity({q.value}, "
                     f"{q.dimension}) via MATH-01 algebra; want value 680.0, "
                     f"dimension (L^-3 M)"))
    except Exception as e:
        rows.append(("R1d", False, f"raised {type(e).__name__}: {e}"))

    # (e) fixture band SG 0.25/0.30/1.18 all inside (0, 22.59]
    band_ok, detail = True, []
    for name, dom, sgv in (("torso_fiction", "plush_stuffed", 0.25),
                           ("sweater_fiction", "knit", 0.30),
                           ("eye_fiction", "acrylic", 1.18)):
        try:
            part.presets.author(name, dom, "sg", sgv, "sg",
                                f"SYNTHETIC {dom} SG control", sg=sgv)
            detail.append(f"{dom} SG {sgv} admitted")
        except Exception as e:
            band_ok = False
            detail.append(f"{dom} SG {sgv} REFUSED {e}")
    rows.append(("R1e", band_ok, "; ".join(detail)))

    # (f) snapshots: immutable mappings, identical content, no shared keys
    try:
        ps, cs = part.presets.snapshot(), part.calibrated.snapshot()
        immut = True
        try:
            ps["x"] = 1
            immut = False
        except TypeError:
            pass
        shared = set(map(str, ps)) & set(map(str, cs))
        rows.append(("R1f", immut and not shared and len(cs) == 1,
                     f"preset snapshot {len(ps)} records, calibrated snapshot "
                     f"{len(cs)} records; mapping forbids item assignment: "
                     f"{immut}; shared keys: {sorted(shared)}"))
    except Exception as e:
        rows.append(("R1f", False, f"raised {type(e).__name__}: {e}"))

    # (g) preset_get returns the record labeled synthetic
    try:
        got = part.preset_get("torso_fiction", "density")
        rows.append(("R1g", got.synthetic is True
                     and "SYNTHETIC" in got.synthetic_label,
                     f"preset_get -> synthetic={got.synthetic}, "
                     f"label={got.synthetic_label!r}"))
    except Exception as e:
        rows.append(("R1g", False, f"raised {type(e).__name__}: {e}"))

    return _write("r1_positive.txt",
                  "R1 positive controls (model must ACCEPT) -- card statement "
                  "side", rows, 7)


# ---- R2 authoring-refusal negatives (8/8) ------------------------------------

def r2():
    part = m.MaterialPartition()
    before = (len(part.presets), len(part.calibrated))
    rows = []
    cases = [
        ("R2a", lambda: part.presets.author(
            "x", "unobtanium", "density", 100.0, "kg/m^3", "label"),
         "unsupported_domain"),
        ("R2b", lambda: part.presets.author(
            "fake_wood", "wood", "density", 700.0, "kg/m^3", "label"),
         "unsupported_domain"),
        ("R2c", lambda: part.presets.author(
            "fake_metal", "metal", "density", 7800.0, "kg/m^3", "label"),
         "unsupported_domain"),
        ("R2d", lambda: part.presets.author(
            "fake_water", "water", "density", 1000.0, "kg/m^3", "label"),
         "unsupported_domain"),
        ("R2e", lambda: part.presets.author(
            "x", "knit", "density", float("nan"), "kg/m^3", "label"),
         "nonfinite"),
        ("R2f", lambda: part.presets.author(
            "x", "knit", "sg", 0.0, "sg", "label", sg=0.0), "sg_out_of_domain"),
        ("R2g", lambda: part.presets.author(
            "x", "knit", "sg", 30.0, "sg", "label", sg=30.0),
         "sg_out_of_domain"),
        ("R2h", lambda: part.calibrated.admit(
            "y", "density", 500.0, "kg/m^3", "   ", "12% MC", "researched"),
         "missing_basis"),
    ]
    for rid, fn, want in cases:
        got = refusal_of(fn)
        ok = got is not None and got[0] == want
        detail = ("refused: " + repr(got)) if got else "NOT REFUSED (accepted!)"
        rows.append((rid, ok, detail))
    after = (len(part.presets), len(part.calibrated))
    post_ok = before == after
    rows.append(("R2-post", post_ok,
                 f"store sizes before {before} == after {after}: "
                 f"{post_ok} (nothing admitted on any refusal)"))
    return _write("r2_authoring_refusals.txt",
                  "R2 card-prediction negatives -- authoring refusals "
                  "(model must REFUSE, reason verbatim)", rows, 8)


# ---- R3 card-falsifier paths (6/6) -------------------------------------------

def r3():
    part = m.MaterialPartition()
    preset = part.presets.author(
        "magic_wood", "plush_stuffed", "density", 700.0, "kg/m^3",
        "SYNTHETIC wood-LIKE preset; declared fiction, not measured wood",
        sg=0.70)
    rows = []
    before_hex = preset.quantity.value.hex()

    # (a) provenance flip on the frozen record
    try:
        object.__setattr__  # noqa: provider for readability below
        preset.provenance = "researched"
        rows.append(("R3a", False, "provenance flip SUCCEEDED (not frozen!)"))
    except dataclasses.FrozenInstanceError as e:
        after = part.preset_get("magic_wood", "density")
        ok = (after.provenance == m.PROVENANCE_SYNTHETIC
              and after.quantity.value.hex() == before_hex)
        rows.append(("R3a", ok, f"flip raised FrozenInstanceError; record "
                     f"after: provenance={after.provenance}, "
                     f"value bits unchanged: "
                     f"{after.quantity.value.hex() == before_hex}"))
    except Exception as e:
        rows.append(("R3a", False, f"raised {type(e).__name__}: {e}"))

    # (b) label strip/overwrite on the frozen record
    try:
        preset.synthetic_label = "measured white oak"
        rows.append(("R3b", False, "label overwrite SUCCEEDED (not frozen!)"))
    except dataclasses.FrozenInstanceError:
        after = part.preset_get("magic_wood", "density")
        rows.append(("R3b", "SYNTHETIC" in after.synthetic_label,
                     f"label after: {after.synthetic_label!r}"))
    except Exception as e:
        rows.append(("R3b", False, f"raised {type(e).__name__}: {e}"))

    # (c) calibrated_get of a preset-only name
    got = refusal_of(part.calibrated_get, "magic_wood", "density")
    rows.append(("R3c", got is not None
                 and got[0] == "synthetic_not_calibrated",
                 "refused: " + repr(got) if got else "NOT REFUSED"))

    # (d) fabricated-citation path: same values re-claimed as researched
    got = refusal_of(part.admit_calibrated, "magic_wood", "density", 700.0,
                     "kg/m^3", "Wood Handbook FPL-GTR-190 Table 5-3b",
                     "clear straight-grained wood, 12% MC", "researched")
    rows.append(("R3d", got is not None and got[0] == "fictional_claim",
                 "refused: " + repr(got) if got else "NOT REFUSED"))

    # (e) hostile dict injected into the preset bag, then served
    part.presets._records[("injected", "density")] = {
        "name": "injected", "value": 999.0}
    got = refusal_of(part.preset_get, "injected", "density")
    part.presets._records.pop(("injected", "density"))  # clean probe artifact
    rows.append(("R3e", got is not None
                 and got[0] == "not_a_store_member",
                 "refused at serve time: " + repr(got) if got
                 else "NOT REFUSED (dict served!)"))

    # (f) the preset record itself offered as-is to the calibrated door
    got = refusal_of(part.calibrated.admit, "magic_wood", "density", 700.0,
                     "kg/m^3", "some source", "some conditions",
                     m.PROVENANCE_SYNTHETIC)
    rows.append(("R3f", got is not None and got[0] == "fictional_claim",
                 "refused: " + repr(got) if got else "NOT REFUSED"))

    return _write("r3_falsifier_paths.txt",
                  "R3 CARD FALSIFIER probes -- fictional preset presented as "
                  "measured wood/metal/water (all paths must refuse)",
                  rows, 6)


# ---- R4 separation invariants (4/4) ------------------------------------------

def r4():
    part = m.MaterialPartition()
    part.presets.author("p1", "knit", "density", 300.0, "kg/m^3",
                        "SYNTHETIC knit-like preset", sg=0.30)
    cal_before = (len(part.calibrated),
                  repr(sorted(map(str, part.calibrated.snapshot()))))
    rows = []

    # (a) authoring a preset leaves the calibrated store byte-identical
    part.presets.author("p2", "acrylic", "density", 1180.0, "kg/m^3",
                        "SYNTHETIC acrylic preset", sg=1.18)
    cal_after = (len(part.calibrated),
                 repr(sorted(map(str, part.calibrated.snapshot()))))
    rows.append(("R4a", cal_before == cal_after,
                 f"calibrated store before {cal_before[0]} records / after "
                 f"{cal_after[0]} records; snapshot repr identical: "
                 f"{cal_before[1] == cal_after[1]}"))

    # (b) same name on both planes: two distinct records, no aliasing
    part.calibrated.admit("p1", "density", 298.0, "kg/m^3",
                          "measured knit-bulk assembly, lab run 42",
                          "23 C, 45% RH", "researched")
    a = part.calibrated_get("p1", "density")
    b = part.preset_get("p1", "density")
    ok = (a.quantity.value == 298.0 and a.provenance == "researched"
          and b.synthetic is True and b.quantity.value == 300.0
          and a is not b)
    rows.append(("R4b", ok,
                 f"calibrated_get(p1) -> {a.quantity.value} "
                 f"({a.provenance}); preset_get(p1) -> {b.quantity.value} "
                 f"(synthetic={b.synthetic}); distinct objects: {a is not b}"))

    # (c) snapshot -> serve round trip reproduces identical value bits
    snap_hex = part.preset_get("p1", "density").quantity.value.hex()
    rt_hex = part.presets.snapshot()[("p1", "density")].quantity.value.hex()
    rows.append(("R4c", snap_hex == rt_hex,
                 f"snapshot value bits {snap_hex} == served {rt_hex}"))

    # (d) duplicate authoring refused, first record intact
    got = refusal_of(part.presets.author, "p1", "knit", "density", 555.0,
                     "kg/m^3", "duplicate attempt")
    kept = part.preset_get("p1", "density")
    rows.append(("R4d", got is not None and got[0] == "duplicate_authoring"
                 and kept.quantity.value == 300.0,
                 f"refused: {got!r}; first record intact at "
                 f"{kept.quantity.value}"))

    return _write("r4_separation.txt",
                  "R4 separation invariants (card statement's structural "
                  "side)", rows, 4)


def main():
    results = {"R1": r1(), "R2": r2(), "R3": r3(), "R4": r4()}
    summary = {
        "rows": {k: ("HOLD" if v else "FIRED") for k, v in results.items()},
        "fired_runs_retained": fired_runs,
    }
    (CHECKS / "controls_summary.txt").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
