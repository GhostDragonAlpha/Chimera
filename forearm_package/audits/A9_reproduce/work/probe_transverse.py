"""Probe: source-side transverse evidence — for each limb body, the max spread of the
body's OWN sites along the segment's b (lateral) and c (dorso-ventral) axes. A body
needs a site pair spanning each axis to supply transverse EVIDENCE; without one, the
axis needs an authored assumption or the segment is unresolved."""
from __future__ import annotations
import itertools
import numpy as np
from synthetic_fixtures import load_real, chain_child
from intake import global_site_positions
from compiler import onb_from_points


def main() -> int:
    real = load_real()
    sw = global_site_positions(real)
    names = ["femur_r", "tibia_r", "humerus", "ulna", "radius", "thorax_dummy", "thorax"]
    print(f"{'body':13s} {'#sites':>6s} {'b_span':>7s} {'c_span':>7s}  notes")
    for body in names:
        b = real.body_by_name[body]
        child = chain_child(real, body)
        if child is not None:
            D = real.body_by_name[child].pos_global
        else:
            own = [s for s in real.sites if s.body == body and s.referenced_by]
            D = max((sw[s.name] for s in own), key=lambda p: np.linalg.norm(p - b.pos_global))
        A = b.pos_global
        # roll ref from the fixture's own rule
        a = D - A
        a = a / np.linalg.norm(a)
        cand = [s for s in real.sites if s.body in (body, b.parent, child)] if child else \
               [s for s in real.sites if s.body in (body, b.parent)]
        q = max(cand, key=lambda s: np.linalg.norm(sw[s.name] - A - a * ((sw[s.name] - A) @ a)))
        qw = sw[q.name]
        aa, bb, cc = onb_from_points(A, D, qw)
        sts = [s for s in real.sites if s.body == body]
        pts = np.array([sw[s.name] for s in sts])
        if len(pts) < 2:
            print(f"{body:13s} {len(pts):6d} {'--':>7s} {'--':>7s}  <2 sites: no transverse evidence")
            continue
        rel = pts - A
        bproj = rel @ bb
        cproj = rel @ cc
        b_span = bproj.max() - bproj.min()
        c_span = cproj.max() - cproj.min()
        notes = []
        if b_span < 0.01:
            notes.append("b too thin (<0.01 m)")
        if c_span < 0.01:
            notes.append("c too thin (<0.01 m)")
        print(f"{body:13s} {len(pts):6d} {b_span:7.4f} {c_span:7.4f}  {'; '.join(notes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())