"""P7 — contract C04 scaling check (independent transformed integrals).

Uses this attempt's own exact Fraction route (route A of
derive_si_fc_independent) on the archived U1 multi-cell coupon cells at
unchanged density, scaled by uniform s in {0.5, 2, 10}:

    V(s) = s^3 V(1),  m(s) = s^3 m(1),  I_com(s) = s^5 I_com(1).

Geometry input: the frozen coupon fixture mc_partition.json (archived at
commit 4f610ae1). Scale applies to vertex coordinates only (rigid uniform
length scaling about the origin); density unchanged. Falsifier F-B01-3-class
tolerance: 1e-12 relative on each law. Boundary (not claimed): the exporter's
scale_to_m input path remains U2/B02 scope.
"""
import json
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from derive_si_fc_independent import tet_exact, inertia_about_com  # noqa: E402

PART = HERE.parent / "m02_archived" / "material_volume_campaign" / "agents" / "M02_multicell" / "fixtures" / "mc_partition.json"
RUNS = HERE.parent / "runs"
SCALES = [Fraction(1, 2), Fraction(2), Fraction(10)]


def coupon_cells():
    part = json.loads(PART.read_text(encoding="utf-8"))
    regions = {r["region_id"]: r for r in part["regions"]}
    materials = {m["material_id"]: m for m in part["materials"]}
    verts = {v["vertex_id"]: v["position"] for v in part["vertices"]}
    cells = []
    for c in part["cells"]:
        mat = materials[regions[c["proposals"][0]]["material_id"]]
        cells.append(([verts[i] for i in c["vertex_ids"]],
                      mat["density_kg_m3"]))
    return cells


def props_at_scale(cells, s):
    m_tot = Fraction(0)
    mct = [Fraction(0)] * 3
    rawt = [[Fraction(0)] * 3 for _ in range(3)]
    for verts, dens in cells:
        sv = [[Fraction(str(c)) * s for c in row] for row in verts]
        m, com, raw, _v = tet_exact(sv, dens)
        m_tot += m
        for a in range(3):
            mct[a] += m * com[a]
            for b in range(3):
                rawt[a][b] += raw[a][b]
    com = [mct[a] / m_tot for a in range(3)]
    return m_tot, com, inertia_about_com(m_tot, com, rawt)


def main():
    cells = coupon_cells()
    m1, com1, I1 = props_at_scale(cells, Fraction(1))
    rows = []
    ok_all = True
    for s in SCALES:
        ms, coms, Is = props_at_scale(cells, s)
        mass_law = ms / m1 / (s ** 3)
        err_m = abs(mass_law - 1)
        for a in range(3):
            for b in range(3):
                law = Is[a][b] / I1[a][b] / (s ** 5)
                err = abs(law - 1)
                ok = err <= Fraction(1, 10 ** 12)
                ok_all &= ok
                rows.append((str(s), f"I[{a}][{b}]", float(law), float(err), ok))
        okm = err_m <= Fraction(1, 10 ** 12)
        ok_all &= okm
        rows.append((str(s), "mass", float(mass_law), float(err_m), okm))
    RUNS.mkdir(parents=True, exist_ok=True)
    with open(RUNS / "p7_scaling_law.json", "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump({"rows": [dict(zip(("s", "quantity", "observed_ratio",
                                      "abs_err", "ok"), r)) for r in rows],
                   "all_ok": ok_all}, fh, indent=1)
    for s, q, ratio, err, ok in rows:
        if not ok:
            print(f"FAIL s={s} {q}: ratio {ratio} err {err}")
    print(f"checks: {len(rows)}; m ~ s^3 and I ~ s^5 at unchanged density: "
          f"{'ALL OK (<=1e-12)' if ok_all else 'VIOLATION'}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
