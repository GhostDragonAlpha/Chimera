#!/usr/bin/env python3
"""extract_muscle_atlas.py - data-lane extraction for the MUSCLE_ATLAS membrane.

Re-runnable extractor. Reads fetched, license-clean OpenSim models under
external/anatomy/ and writes:

  external/anatomy/muscle_parameters.json  - per-muscle parameters, origin/
    insertion (segment + normalized coordinates), crossing joints, and
    per-field line provenance, for every muscle of the standing chain plus
    the fetched arm subset.
  external/anatomy/joint_definitions.json  - per-joint class, parent/child,
    axes, DoF, measured ranges, and a systematic cross-check of the
    LightEngine kernel joint classes against the measured model.

Sources (all Apache-2.0, opensim-org/opensim-models GitHub, no registration):
  Rajagopal2016.osim            canonical full-body model (80 MTUs)
  gait2392.osim                 thelen2003 fallback (92 MTUs)
  Arm26.osim                    open arm subset (6 elbow muscles)

The gait2392 and Arm26 files are fetched into external/anatomy/_fetch_*.osim
by the lane session; this script promotes them to canonical names (idempotent).

Usage:  python tools/extract_muscle_atlas.py [--root <repo root>]

No code outside external/anatomy/ is written. LightEngine modules are only
READ for the joint-class cross-check.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent

MODELS = {
    "Rajagopal2016": {
        "file": "external/anatomy/Rajagopal2016.osim",
        "url": "https://raw.githubusercontent.com/opensim-org/opensim-models/master/Models/Rajagopal/Rajagopal2016.osim",
        "license": "Apache-2.0",
        "citation": "Rajagopal, A., Dembia, C. L., DeMers, M. S., Delp, D. D., Hicks, J. L., Delp, S. L. (2016). Full-Body Musculoskeletal Model for Muscle-Driven Simulation of Human Gait. IEEE TBME 63(10), 2068-2079. doi:10.1109/TBME.2016.2586891",
        "role": "primary",
    },
    "gait2392": {
        "file": "external/anatomy/gait2392.osim",
        "fetch": "external/anatomy/_fetch_gait2392.osim",
        "url": "https://raw.githubusercontent.com/opensim-org/opensim-models/master/Models/Gait2392_Simbody/gait2392_thelen2003muscle.osim",
        "license": "Apache-2.0",
        "citation": "Delp et al. (1990) Gait2392 lower-limb model; Thelen (2003) musculotendon dynamics.",
        "role": "fallback",
    },
    "Arm26": {
        "file": "external/anatomy/Arm26.osim",
        "fetch": "external/anatomy/_fetch_arm26.osim",
        "url": "https://raw.githubusercontent.com/opensim-org/opensim-models/master/Models/Arm26/arm26.osim",
        "license": "Apache-2.0",
        "citation": "OpenSim Arm26 planar arm model (2-DoF, 6 muscles).",
        "role": "arm subset",
    },
}

# Functional role per muscle stem. The role label is the modeler's mapping;
# the parameters themselves come from the model. Crossing is computed from
# geometry; this table only names the group the skeleton's joint rows need.
ROLE = {
    "psoas": "hip_flexor", "iliacus": "hip_flexor", "recfem": "hip_flexor",
    "sart": "hip_flexor", "tfl": "hip_flexor",
    "glmax1": "hip_extensor", "glmax2": "hip_extensor", "glmax3": "hip_extensor",
    "bflh": "hip_extensor", "bfsh": "hip_extensor",
    "semimem": "hip_extensor", "semiten": "hip_extensor",
    "glmed1": "hip_abductor", "glmed2": "hip_abductor", "glmed3": "hip_abductor",
    "glmin1": "hip_abductor", "glmin2": "hip_abductor", "glmin3": "hip_abductor",
    "addbrev": "hip_adductor", "addlong": "hip_adductor",
    "addmagDist": "hip_adductor", "addmagIsch": "hip_adductor",
    "addmagMid": "hip_adductor", "addmagProx": "hip_adductor",
    "grac": "hip_adductor", "piri": "hip_rotator",
    "vasint": "knee_extensor", "vaslat": "knee_extensor", "vasmed": "knee_extensor",
    "semimel": "knee_flexor",
    "gastroc_med": "ankle_plantarflexor", "gastroc_lat": "ankle_plantarflexor",
    "gasmed": "ankle_plantarflexor", "gaslat": "ankle_plantarflexor",
    "soleus": "ankle_plantarflexor", "tibpost": "ankle_plantarflexor",
    "perbrev": "ankle_plantarflexor", "perlong": "ankle_plantarflexor",
    "fdl": "ankle_plantarflexor", "fhl": "ankle_plantarflexor",
    "tibant": "ankle_dorsiflexor", "edl": "ankle_dorsiflexor", "ehl": "ankle_dorsiflexor",
    "iliopsoas": "hip_flexor",
    "TRIlong": "elbow_extensor", "TRIlat": "elbow_extensor", "TRImed": "elbow_extensor",
    "BIClong": "elbow_flexor", "BICshort": "elbow_flexor", "BRA": "elbow_flexor",
    # gait2392 (fallback) stem names -- same functional groups.
    "glut_med": "hip_abductor", "glut_min": "hip_abductor",
    "glut_max": "hip_extensor",
    "glmax": "hip_extensor", "glmed": "hip_abductor", "glmin": "hip_abductor",
    "bifemlh": "hip_extensor", "bifemsh": "hip_extensor",
    "semimem": "hip_extensor", "semiten": "hip_extensor",
    "sar": "hip_flexor",
    "add_long": "hip_adductor", "add_brev": "hip_adductor",
    "add_mag": "hip_adductor", "pect": "hip_adductor",
    "quad_fem": "hip_rotator", "gem": "hip_rotator", "peri": "hip_rotator",
    "rect_fem": "hip_flexor",
    "vas_med": "knee_extensor", "vas_int": "knee_extensor", "vas_lat": "knee_extensor",
    "med_gas": "ankle_plantarflexor", "lat_gas": "ankle_plantarflexor",
    "tib_post": "ankle_plantarflexor",
    "flex_dig": "ankle_plantarflexor", "flex_hal": "ankle_plantarflexor",
    "per_brev": "ankle_plantarflexor", "per_long": "ankle_plantarflexor",
    "per_tert": "ankle_dorsiflexor",
    "ext_dig": "ankle_dorsiflexor", "ext_hal": "ankle_dorsiflexor",
    "tib_ant": "ankle_dorsiflexor",
    "ercspn": "torso_extensor", "intobl": "torso_flexor", "extobl": "torso_flexor",
}

MUSCLE_TAGS = ("Millard2012EquilibriumMuscle", "Thelen2003Muscle")


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def children_text(el: ET.Element, tag: str) -> str | None:
    for c in el:
        if c.tag == tag and c.text and c.text.strip():
            return c.text.strip()
    return None


def child_el(el: ET.Element, tag: str) -> ET.Element | None:
    for c in el:
        if c.tag == tag:
            return c
    return None


def body_from_socket(value: str | None, frame_bodies: dict) -> str | None:
    """Resolve a socket value to a body name. Handles '/bodyset/pelvis'
    paths and joint-owned PhysicalOffsetFrame names."""
    if not value:
        return None
    v = value.strip()
    if v in frame_bodies:
        return frame_bodies[v]
    return v.split("/")[-1]


def parse_osim(path: pathlib.Path):
    """Parse an OpenSim file into an ElementTree plus an exact 1-based line
    number for every element, recorded via a SAX locator (not regex -- the
    file contains hundreds of attribute-less containers like <objects>)."""
    root = None
    stack: list[ET.Element] = []
    line_of: dict[int, int] = {}

    import xml.sax
    from xml.sax.handler import ContentHandler

    class _Handler(ContentHandler):
        def __init__(self):
            self._text = []

        def setDocumentLocator(self, locator):
            self._loc = locator

        def startElement(self, tag, attrs):
            nonlocal root
            el = ET.Element(tag, dict(attrs))
            line_of[id(el)] = self._loc.getLineNumber()
            if stack:
                stack[-1].append(el)
            else:
                root = el
            stack.append(el)
            self._text = []

        def endElement(self, tag):
            el = stack[-1]
            if self._text:
                el.text = "".join(self._text)
            stack.pop()
            self._text = []

        def characters(self, content):
            self._text.append(content)

    xml.sax.parse(str(path), _Handler())
    return root.find("Model"), line_of


def extract_muscles(model: ET.Element, line_of: dict) -> list[dict]:
    forceset = child_el(model, "ForceSet")
    if forceset is None:
        return []
    objects = child_el(forceset, "objects")
    if objects is None:
        return []
    muscles = []
    for el in objects:
        if el.tag not in MUSCLE_TAGS:
            continue
        name = el.get("name")
        if name == "default":
            continue
        rec = {"name": name, "type": el.tag, "line": line_of.get(id(el))}
        for field in ("max_isometric_force", "optimal_fiber_length",
                      "tendon_slack_length", "pennation_angle_at_optimal"):
            v = children_text(el, field)
            if v is not None:
                rec[field] = float(v)
        gpath = child_el(el, "GeometryPath")
        points = []
        if gpath is not None:
            pset = child_el(gpath, "PathPointSet")
            if pset is not None:
                container = child_el(pset, "objects")
                children = list(container) if container is not None else list(pset)
                for p in children:
                    if p.tag != "PathPoint":
                        continue
                    body = body_from_socket(
                        children_text(p, "socket_parent_frame"), {})
                    if body is None:
                        body = children_text(p, "body")
                    loc = children_text(p, "location")
                    points.append({
                        "name": p.get("name"),
                        "body": body,
                        "location_m": [float(x) for x in loc.split()] if loc else None,
                        "line": line_of.get(id(p)),
                    })
        rec["origin"] = points[0] if points else None
        rec["insertion"] = points[-1] if points else None
        rec["path_points"] = points
        muscles.append(rec)
    return muscles


def extract_joints(model: ET.Element, line_of: dict) -> list[dict]:
    js = child_el(model, "JointSet")
    if js is None:
        return []
    objects = child_el(js, "objects")
    if objects is None:
        return []
    joints = []
    for el in objects:
        # Joint-owned offset frames: name -> (parent body, translation).
        frame_bodies = {}
        frame_locs = {}
        frames = child_el(el, "frames")
        if frames is not None:
            for f in frames:
                if f.tag != "PhysicalOffsetFrame":
                    continue
                fname = f.get("name")
                parent = children_text(f, "socket_parent")
                tr = children_text(f, "translation")
                if fname is not None:
                    frame_bodies[fname] = body_from_socket(parent, {})
                    frame_locs[fname] = ([float(x) for x in tr.split()]
                                         if tr else None)

        parent = body_from_socket(children_text(el, "socket_parent_frame"),
                                  frame_bodies)
        child = body_from_socket(children_text(el, "socket_child_frame"),
                                 frame_bodies)
        if parent is None:
            parent = children_text(el, "parent_body")
        if child is None:
            child = children_text(el, "child_body")

        loc_in_parent = children_text(el, "location_in_parent")
        loc_in_child = children_text(el, "location_in_child")
        loc_in_parent_m = ([float(x) for x in loc_in_parent.split()]
                           if loc_in_parent else None)
        loc_in_child_m = ([float(x) for x in loc_in_child.split()]
                          if loc_in_child else None)

        # Coordinates container is <coordinates> (v4) or <Coordinates> (v3).
        coords_el = child_el(el, "coordinates")
        if coords_el is None:
            coords_el = child_el(el, "Coordinates")
        coords = []
        if coords_el is not None:
            for co in coords_el:
                if co.tag != "Coordinate":
                    continue
                rng = children_text(co, "range")
                coords.append({
                    "name": co.get("name"),
                    "range_rad": ([float(x) for x in rng.split()]
                                  if rng else None),
                    "default_rad": _to_float(children_text(co, "default_value")),
                    "clamped": children_text(co, "clamped"),
                    "locked": children_text(co, "locked"),
                    "line": line_of.get(id(co)),
                })

        # SpatialTransform axes.
        axes = []
        st = child_el(el, "SpatialTransform")
        if st is not None:
            for ta in st:
                if ta.tag == "TransformAxis":
                    coord = children_text(ta, "coordinates")
                    ax = children_text(ta, "axis")
                    if coord is not None:
                        axes.append({
                            "coordinate": coord.split()[-1],
                            "axis": ([float(x) for x in ax.split()]
                                     if ax else None),
                            "line": line_of.get(id(ta)),
                        })

        # Resolve frame translations into location_in_parent/child where the
        # file did not carry them directly.
        parent_sock = children_text(el, "socket_parent_frame")
        child_sock = children_text(el, "socket_child_frame")
        if loc_in_parent_m is None and parent_sock in frame_locs:
            loc_in_parent_m = frame_locs[parent_sock]
        if loc_in_child_m is None and child_sock in frame_locs:
            loc_in_child_m = frame_locs[child_sock]

        pin_axis = children_text(el, "axis")
        joints.append({
            "name": el.get("name"),
            "class": el.tag,
            "parent_body": parent,
            "child_body": child,
            "location_in_parent_m": loc_in_parent_m,
            "location_in_child_m": loc_in_child_m,
            "pin_axis": ([float(x) for x in pin_axis.split()]
                         if pin_axis else None),
            "axes": axes,
            "coordinates": coords,
            "dof": len(coords),
            "line": line_of.get(id(el)),
        })
    return joints


def _to_float(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def classify_joint_type(j: dict) -> str:
    """Map the OpenSim joint element to the atlas six-pair class."""
    cls = j["class"]
    if cls == "PinJoint":
        return "revolute"
    if cls == "UniversalJoint":
        return "universal"
    if cls == "BallJoint":
        return "spherical"
    if cls == "FreeJoint":
        return "free"
    if cls == "CustomJoint":
        dof = j["dof"]
        if dof == 1:
            return "revolute"
        if dof == 2:
            return "universal"
        if dof == 3:
            return "spherical"
        if dof >= 6:
            return "free"
    return cls


def build_body_tree(joints: list[dict]) -> dict[str, str]:
    parent_of = {}
    for j in joints:
        if j["parent_body"] and j["child_body"]:
            parent_of[j["child_body"]] = j["parent_body"]
    return parent_of


def subtree(parent_of: dict, root: str) -> set[str]:
    out = set()
    stack = [root]
    while stack:
        b = stack.pop()
        if b in out:
            continue
        out.add(b)
        for c, p in parent_of.items():
            if p == b:
                stack.append(c)
    return out


def crossing_joints(muscle: dict, joints: list[dict], parent_of: dict) -> list[str]:
    bodies = {p["body"] for p in muscle["path_points"] if p and p["body"]}
    if len(bodies) < 2:
        return []
    crossed = []
    for j in joints:
        child = j["child_body"]
        if child is None or j["parent_body"] is None:
            continue
        if j["name"] in ("ground_platform", "ground_pelvis"):
            continue
        sub = subtree(parent_of, child)
        in_sub = bodies & sub
        out_sub = bodies - sub
        if in_sub and out_sub:
            crossed.append(j["name"])
    return crossed


def normalize_attachment(pt: dict, body_lengths: dict) -> dict:
    """Segment + normalized coordinates: t = fraction along the body's
    measured proximal->distal axis, p_offset = perpendicular offset (m),
    length_m = body axis length. UNKNOWN where the model provides no
    distal joint for the body."""
    if pt is None or pt.get("body") is None or pt.get("location_m") is None:
        return None
    info = body_lengths.get(pt["body"])
    out = {"segment": pt["body"], "location_m": pt["location_m"]}
    if not info:
        out["normalized"] = None
        return out
    prox, dist = info
    u = [(d - p) for d, p in zip(dist, prox)]
    L = math.sqrt(sum(x * x for x in u))
    if L < 1e-9:
        out["normalized"] = None
        return out
    u = [x / L for x in u]
    p = pt["location_m"]
    rel = [x - y for x, y in zip(p, prox)]
    t = sum(a * b for a, b in zip(rel, u))
    perp = [r - t * a for r, a in zip(rel, u)]
    p_off = math.sqrt(sum(x * x for x in perp))
    out["normalized"] = {"t": round(t, 6), "p_offset_m": round(p_off, 6),
                         "length_m": round(L, 6)}
    return out


def body_axes(joints: list[dict]) -> dict[str, tuple[list, list]]:
    proximal = {}
    distal = {}
    for j in joints:
        cb = j["child_body"]
        pb = j["parent_body"]
        if cb is not None and j["location_in_child_m"] is not None:
            proximal.setdefault(cb, j["location_in_child_m"])
        if pb is not None and j["location_in_parent_m"] is not None:
            distal.setdefault(pb, j["location_in_parent_m"])
    out = {}
    for body in set(proximal) | set(distal):
        if body in proximal and body in distal:
            out[body] = (proximal[body], distal[body])
        elif body in proximal:
            out[body] = (proximal[body], proximal[body])
        elif body in distal:
            out[body] = (distal[body], distal[body])
    return out


# Measured Rajagopal joint name for each kernel joint_key. Kernel joint_key is
# the anatomical center used by the kernel (e.g. hip_R); the kernel models it
# with one or more child links. Measured classes are read from the extracted
# Rajagopal joints.
KERNEL_KEY_TO_MEASURED = {
    "hip_R": "hip_r", "hip_L": "hip_l",
    "knee_R": "walker_knee_r", "knee_L": "walker_knee_l",
    "ankle_R": "ankle_r", "ankle_L": "ankle_l",
    "elbow_R": "elbow_r", "elbow_L": "elbow_l",
    "shoulder_R": "acromial_r", "shoulder_L": "acromial_l",
    "wrist_R": "radius_hand_r", "wrist_L": "radius_hand_l",
    "mtp_R": "mtp_r", "mtp_L": "mtp_l",
}

# Kernel child links whose prox joint is the patellofemoral joint, which the
# kernel keys under knee_*; compared against the measured patellofemoral joint.
PATELLA_MEASURED = {"patella_R": "patellofemoral_r", "patella_L": "patellofemoral_l"}

KERNEL_CLASS_TO_ATLAS = {
    "hinge": "revolute",
    "ball-cup": "spherical",
    "saddle": "universal",
    "suture": "suture",
}

DOF_OF_ATLAS = {"revolute": 1, "universal": 2, "spherical": 3,
                "suture": 0, "free": 6}


def kernel_joint_crosscheck(measured_joints: list[dict]) -> dict:
    """Diff the LightEngine kernel joint classes against the measured
    Rajagopal model. Reads (never writes) LightEngine modules."""
    sys.path.insert(0, str(ROOT))
    try:
        from LightEngine.kinematic.skeleton_spec import _topology, build_spec
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"error": f"kernel import failed: {exc}"}

    kernel_joints = build_spec()["joints"]
    topo = _topology()

    measured = {j["name"]: j for j in measured_joints}

    def measured_dof(name):
        m = measured.get(name)
        if m is None:
            return None
        # DoF = number of coordinates (the joint's kinematic class). A
        # coordinate may be locked=true for the model's task; that is a
        # task-level setting, reported per-coordinate, not a structural DoF.
        return len(m["coordinates"])

    rows_out = []
    for child, (parent, key) in topo.items():
        if parent is None or key is None:
            continue
        kj = kernel_joints.get(child)
        if kj is None:
            continue
        kernel_class = kj["dof_class"]
        atlas = KERNEL_CLASS_TO_ATLAS.get(kernel_class, kernel_class)
        kdof = DOF_OF_ATLAS.get(atlas)

        if child in PATELLA_MEASURED:
            mname = PATELLA_MEASURED[child]
        else:
            mname = KERNEL_KEY_TO_MEASURED.get(key)
        if mname is None:
            # Kernel-only articulation (no Rajagopal equivalent): record a
            # note row rather than a spurious mismatch.
            rows_out.append({
                "kernel_joint": child,
                "joint_key": key,
                "kernel_class": kernel_class,
                "atlas_class": atlas,
                "kernel_dof": kdof,
                "measured_joint": None,
                "measured_class": None,
                "measured_dof": None,
                "match": None,
                "note": "kernel-only joint; no Rajagopal2016 equivalent (granularity difference).",
            })
            continue
        mj = measured.get(mname)
        if mj is None:
            continue
        measured_class = mj.get("atlas_class", classify_joint_type(mj))
        mdof = measured_dof(mname)
        match = (atlas == measured_class) and (kdof == mdof)
        if atlas != measured_class and kdof == mdof:
            note = "class differs, DoF matches"
        elif atlas == measured_class and kdof != mdof:
            note = "class matches, DoF differs"
        elif atlas != measured_class and kdof != mdof:
            note = "class and DoF differ"
        else:
            note = ""
        rows_out.append({
            "kernel_joint": child,
            "joint_key": key,
            "kernel_class": kernel_class,
            "atlas_class": atlas,
            "kernel_dof": kdof,
            "measured_joint": mname,
            "measured_class": measured_class,
            "measured_dof": mdof,
            "match": match,
            "note": note,
        })
    compared = [r for r in rows_out if r["match"] is not None]
    mismatches = [r for r in compared if not r["match"]]
    return {
        "kernel_joints_total": len(kernel_joints),
        "standing_chain_compared": len(compared),
        "rows": rows_out,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "note": ("kernel_class = build_spec()['joints'][child]['dof_class']; "
                 "measured_class = Rajagopal2016 joint element mapped to the "
                 "atlas six-pair set. Kernel-only joints (spine segments, "
                 "clavicle/scapula) have match=None and are granularity "
                 "differences, not errors."),
    }


def write_json(path: pathlib.Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=1, sort_keys=False),
                    encoding="utf-8")


def main() -> int:
    root = ROOT
    for k, v in MODELS.items():
        if "fetch" in v:
            fetch = root / v["fetch"]
            target = root / v["file"]
            if fetch.exists():
                if not target.exists():
                    fetch.rename(target)
                else:
                    fetch.unlink()

    source_meta = {}
    for k, v in MODELS.items():
        p = root / v["file"]
        if not p.exists():
            print(f"ERROR: missing {v['file']}", file=sys.stderr)
            return 1
        source_meta[k] = {
            "file": v["file"],
            "sha256": sha256(p),
            "url": v["url"],
            "license": v["license"],
            "citation": v["citation"],
            "role": v["role"],
        }

    muscle_out = {}
    joint_out = {}
    for model_name, meta in MODELS.items():
        path = root / meta["file"]
        model, line_of = parse_osim(path)
        muscles = extract_muscles(model, line_of)
        joints = extract_joints(model, line_of)
        parent_of = build_body_tree(joints)
        axes = body_axes(joints)

        for j in joints:
            j["atlas_class"] = classify_joint_type(j)

        for m in muscles:
            name = m["name"]
            crossed = crossing_joints(m, joints, parent_of)
            origin = normalize_attachment(m["origin"], axes)
            insertion = normalize_attachment(m["insertion"], axes)
            stem = re.sub(r"_[lr]$", "", name)
            stem = re.sub(r"_(left|right)$", "", stem)
            stem = re.sub(r"\d+$", "", stem)
            role = ROLE.get(stem, "unclassified")
            ml = m["line"]
            entry = {
                "source_model": model_name,
                "name": name,
                "group": role,
                "crosses_joints": crossed,
                "origin": origin,
                "insertion": insertion,
                "max_isometric_force_N": {
                    "value": m.get("max_isometric_force"),
                    "line": _field_line(path, ml, "max_isometric_force"),
                },
                "optimal_fiber_length_m": {
                    "value": m.get("optimal_fiber_length"),
                    "line": _field_line(path, ml, "optimal_fiber_length"),
                },
                "tendon_slack_length_m": {
                    "value": m.get("tendon_slack_length"),
                    "line": _field_line(path, ml, "tendon_slack_length"),
                },
                "pennation_angle_rad": {
                    "value": m.get("pennation_angle_at_optimal"),
                    "line": _field_line(path, ml, "pennation_angle_at_optimal"),
                },
                "muscle_element_line": ml,
            }
            muscle_out[f"{model_name}:{name}"] = entry

        joint_out[model_name] = joints

    # Cross-check against the extracted Rajagopal joints (not a hand table).
    crosscheck = kernel_joint_crosscheck(joint_out.get("Rajagopal2016", []))

    muscles_json = {
        "domain": "muscle_parameters",
        "statement": "Every muscle of the standing chain (ankle/knee/hip) plus the fetched arm subset has parameters from a published open model; the arm set beyond the fetched subset is an explicit gap, not an estimate.",
        "sources": source_meta,
        "normalization": ("origin/insertion: model body-frame location_m plus "
                          "segment-normalized coordinates t = fraction along "
                          "the body's measured proximal->distal axis, "
                          "p_offset_m = perpendicular offset, length_m = "
                          "measured body axis length. UNKNOWN where the model "
                          "provides no distal joint for the body."),
        "provenance": "per-field 'line' = 1-based line number of the field tag in the source .osim file.",
        "muscles": muscle_out,
        "muscle_count": len(muscle_out),
    }

    joints_json = {
        "domain": "joint_definitions",
        "statement": ("Every joint the skeleton needs has a measured class, "
                      "axes, DoF, and range from the Rajagopal2016 model; the "
                      "atlas pair is classified from the OpenSim joint element."),
        "sources": source_meta,
        "joints": joint_out,
        "crosscheck_vs_lightengine": crosscheck,
    }

    out_m = root / "external/anatomy/muscle_parameters.json"
    out_j = root / "external/anatomy/joint_definitions.json"
    write_json(out_m, muscles_json)
    write_json(out_j, joints_json)

    print(f"wrote {out_m}")
    print(f"wrote {out_j}")
    print(f"muscles extracted: {len(muscle_out)}")
    print(f"joints extracted: {sum(len(v) for v in joint_out.values())}")
    cc = crosscheck
    if "rows" in cc:
        print("kernel cross-check:")
        print(f"  standing-chain joints compared: {cc['standing_chain_compared']}")
        print(f"  mismatches: {cc['mismatch_count']}")
        for r in cc["rows"]:
            if r["match"] is None:
                mark = "N/A"
            else:
                mark = "OK " if r["match"] else "DIFF"
            mc = r["measured_class"] if r["measured_class"] else "-"
            md = r["measured_dof"] if r["measured_dof"] is not None else "-"
            kc = r["atlas_class"] if r["atlas_class"] else "-"
            kd = r["kernel_dof"] if r["kernel_dof"] is not None else "-"
            print(f"    [{mark}] {r['joint_key']:10s} "
                  f"kernel={kc:10s} measured={mc:10s} "
                  f"dof {kd} vs {md}")
    return 0


def _field_line(path: pathlib.Path, muscle_line: int, field: str) -> int:
    """Line of the first occurrence of <field> after the muscle's opening tag."""
    if muscle_line is None:
        return None
    lines = path.read_text(errors="replace").splitlines()
    pat = re.compile(r"<" + re.escape(field) + r">")
    for i in range(muscle_line - 1, len(lines)):
        if pat.search(lines[i]):
            return i + 1
    return None


if __name__ == "__main__":
    raise SystemExit(main())
