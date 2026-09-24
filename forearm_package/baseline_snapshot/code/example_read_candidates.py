"""example_read_candidates.py — minimal reader of the attachment-candidates packet.

Shows the two lookup shapes a consumer needs:
  1) by SITE : what the site is (port candidate / waypoint) and for which tendons
  2) by TENDON: its ordered path with each site's role on the forearm

Run:  python example_read_candidates.py
"""
from __future__ import annotations

import json
from pathlib import Path

RUNS = Path(r"E:\PythonChimera\.tmp\anatomy_compiler\runs")


def main() -> int:
    cand = json.loads((RUNS / "attachment_candidates.json").read_text(encoding="utf-8"))

    print("== by site (radius, first 6 records) ==")
    for rec in cand["bodies"]["radius"]["candidates"][:6]:
        roles = rec["endpoint_roles"] or ["waypoint"]
        loop = rec["skin_containment"]["loop"]
        print(f"  {rec['site_id']:14s} roles={roles!r:34s} mech_qual={rec['mechanical_qualification']} "
              f"loop={loop.get('verdict', 'not_measured'):10s} "
              f"pos_global_m={rec['fitted']['fitted_pos_global']}")

    print("\n== by tendon (ordered path on radius/radius_l) ==")
    for tendon in sorted({m["tendon"] for b in cand["bodies"].values()
                          for r in b["candidates"] for m in r["tendon_membership"]}):
        entries = []
        for b in ("radius", "radius_l"):
            for r in cand["bodies"][b]["candidates"]:
                for m in r["tendon_membership"]:
                    if m["tendon"] == tendon:
                        entries.append((m["index_in_path"], r["site_id"], m["role"]))
        entries.sort()
        print(f"  {tendon:14s} -> {', '.join(f'{sn}[{role}]' for _, sn, role in entries)}")

    rule = cand["port_vs_waypoint_rule"]
    print("\n" + rule)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())