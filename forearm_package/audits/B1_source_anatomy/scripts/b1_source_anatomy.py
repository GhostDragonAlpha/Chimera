"""B1 source-side dossier: hierarchy, joints, sites, inertial for the four unresolved bodies.

Read-only on baseline_snapshot/source_xml/chimanoid.xml. Output -> receipts/source_anatomy.txt
plus a JSON machine record receipts/source_anatomy.json.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

XML = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot\source_xml\chimanoid.xml")
TARGETS = ["ulna", "ulna_l", "hand_r", "hand_l"]
OUT_TXT = Path(r"E:\PythonChimera\forearm_package\audits\B1_source_anatomy\receipts\source_anatomy.txt")
OUT_JSON = Path(r"E:\PythonChimera\forearm_package\audits\B1_source_anatomy\receipts\source_anatomy.json")


def main() -> int:
    root = ET.parse(XML).getroot()
    worldbody = root.find("worldbody")

    # ---- body tree ---------------------------------------------------------
    tree: dict[str, dict] = {}

    def walk(el, parent):
        for b in el.findall("body"):
            name = b.get("name")
            tree[name] = {"parent": parent, "el": b}
            walk(b, name)

    walk(worldbody, None)

    lines = []
    out_json: dict = {}

    lines.append(f"source: {XML}")
    raw = XML.read_bytes()
    lines.append(f"bytes={len(raw)}")
    lines.append(f"bodies in tree: {len(tree)}")
    lines.append("body tree:")
    for name, rec in tree.items():
        lines.append(f"  {name:14s} parent={rec['parent']}")

    # names of all bodies, sorted, for the sibling analysis
    lines.append("")

    # tendon spatial site references (which sites are referenced by spatial tendons).
    # NOTE: the XML nests the 120 spatials inside wrapper elements; iterate ALL
    # <spatial> descendants (DERIVATION.md §2: 120 spatial tendons in the 2nd wrapper).
    referenced: set[str] = set()
    spatial_tendons = 0
    for sp in root.iter("spatial"):
        spatial_tendons += 1
        for s in sp.findall("site"):
            referenced.add(s.get("site"))

    for name in TARGETS:
        if name not in tree:
            lines.append(f"### {name}: NOT IN TREE")
            continue
        el = tree[name]["el"]
        parent = tree[name]["parent"]
        rec: dict = {"name": name, "parent": parent}
        children = [b.get("name") for b in el.findall("body")]
        lines.append(f"### {name}")
        lines.append(f"  parent={parent}")
        lines.append(f"  direct children={children}")
        siblings = [b for b, r in tree.items() if r["parent"] == parent]
        lines.append(f"  siblings (same parent)={siblings}")
        lines.append(f"  attrs: pos={el.get('pos')!r} quat={el.get('quat')!r} orientation={el.get('orientation')!r} euler={el.get('euler')!r}")

        # direct joints
        joints = el.findall("joint")
        rec["joints"] = []
        lines.append(f"  direct <joint> children: {len(joints)}")
        for j in joints:
            jn = j.get("name")
            line = (f"    joint {jn!r} type={j.get('type')!r} pos={j.get('pos')!r} "
                    f"axis={j.get('axis')!r} range={j.get('range')!r} limited={j.get('limited')!r}")
            lines.append(line)
            rec["joints"].append({
                "name": jn, "type": j.get("type"), "pos": j.get("pos"),
                "axis": j.get("axis"), "range": j.get("range"),
            })

        # all descendant joint names (duplicate-down-chain check)
        desc = [j.get("name") for j in el.iter("joint")]
        lines.append(f"  ALL descendant joint names (incl. own + descendants): {desc}")

        # sites
        sites = el.findall("site")
        rec["sites"] = []
        lines.append(f"  direct <site> children: {len(sites)}")
        n_ref = 0
        for s in sites:
            sn = s.get("name")
            is_ref = sn in referenced
            n_ref += is_ref
            lines.append(f"    site {sn!r} pos={s.get('pos')!r} type={s.get('type')!r} tendon_referenced={is_ref}")
            rec["sites"].append({"name": sn, "pos": s.get("pos"), "referenced": is_ref})
        rec["n_sites_referenced"] = n_ref
        lines.append(f"  of which referenced by spatial tendons: {n_ref}")

        # inertial
        inert = el.find("inertial")
        if inert is not None:
            rec["inertial"] = {k: inert.get(k) for k in ("pos", "mass", "fullinertia")}
            lines.append(f"  <inertial> pos={inert.get('pos')!r} mass={inert.get('mass')!r} fullinertia={inert.get('fullinertia')!r}")
        else:
            rec["inertial"] = None
            lines.append("  <inertial> NONE")

        # geom
        geoms = el.findall("geom")
        lines.append(f"  direct <geom> children: {len(geoms)}" + (f" types={[g.get('type') for g in geoms]}" if geoms else ""))
        if name.startswith("hand"):
            for g in geoms:
                lines.append(f"    geom name={g.get('name')!r} type={g.get('type')!r} "
                             f"fromto={g.get('fromto')!r} size={g.get('size')!r} pos={g.get('pos')!r} group={g.get('group')!r}")
        lines.append("")

        out_json[name] = rec

    # global counts for context
    all_sites = root.findall(".//site")
    lines.append(f"global: total <site> elements={len(all_sites)}  spatial tendons={spatial_tendons}  "
                 f"sites referenced by spatial tendons={len(referenced)}")
    all_bodies = root.findall(".//body")
    lines.append(f"global: total <body> elements (descendant search)={len(all_bodies)}")

    # digit joints anywhere?
    digitish = [j.get("name") for j in root.iter("joint") if j.get("name") and any(
        k in (j.get("name") or "").lower() for k in ("finger", "digit", "thumb", "prox", "dist", "mcp", "pip", "dip"))]
    lines.append(f"digit-like joint names anywhere in source (finger/digit/thumb/mcp/pip/dip/prox/dist): {digitish}")
    hand_joints = []
    for name in TARGETS:
        if name in tree:
            for j in tree[name]["el"].iter("joint"):
                hand_joints.append((name, j.get("name")))
    lines.append(f"joints anywhere under the four bodies (descendant search): {hand_joints}")

    txt = "\n".join(lines)
    OUT_TXT.write_text(txt, encoding="utf-8")
    OUT_JSON.write_text(json.dumps(out_json, indent=1), encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
