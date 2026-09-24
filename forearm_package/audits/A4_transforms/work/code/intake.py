"""Intake: parse the FreeMusco chimanoid.xml into a SourceAnatomy.

Read-only stdlib parser. Facts enforced here (measured from the real file, see
DERIVATION.md §2):
  - coordinate ownership comes from a body's DIRECT <joint> children only — the XML
    also carries duplicate descendant joint lists (141 elements for 39 distinct names)
    which are ignored for ownership and preserved nowhere;
  - spatial tendons are <site> chains; nothing else is accepted;
  - muscle force/timeconst/lengthrange are ingested as authored strings (text) — the
    compiler must not interpret units it does not own.
"""
from __future__ import annotations

import hashlib
import os
import xml.etree.ElementTree as ET

import numpy as np

from schema import SourceAnatomy, SourceBody, SourceJoint, SourceSite, SourceTendon, SourceMuscle
from correspondence import Refusal

REVISION = "e021d5d9d1698dafea93c0dcf34b4bc8ce1530e7"


def _vec(text: str | None) -> np.ndarray:
    return np.array([float(v) for v in (text or "").split()], dtype=np.float64)


def _wu(text: str | None) -> np.ndarray:
    return np.array([float(v) for v in (text or "1 0 0 0").split()][:4], dtype=np.float64)


def _quat_to_rotmat(q: np.ndarray) -> np.ndarray:
    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def _boolish(text: str | None, default: bool = True) -> bool:
    if text is None:
        return default
    return text.strip().lower() not in ("false", "0", "")


def _range(a: dict) -> list[float]:
    lo, hi = _vec(a.get("range", "0 0"))
    return [float(lo), float(hi)]


def load_source(path: str) -> SourceAnatomy:
    with open(path, "rb") as fh:
        data = fh.read()
    sha = hashlib.sha256(data).hexdigest()
    # documented local transformation: the on-disk bytes equal the pinned upstream
    # bytes plus a trailing CRLF. The canonical variant normalizes line endings so a
    # reader can distinguish upstream byte identity from that local text transform.
    canonical = data.replace(b"\r\n", b"\n").rstrip(b"\n") + b"\n"
    sha_canonical = hashlib.sha256(canonical).hexdigest()
    canonicalization = {
        "transformation": "on-disk bytes normalized (CRLF -> LF, trailing CRLF stripped)",
        "source_sha256": sha,
        "source_sha256_canonical": sha_canonical,
        "bytes": len(data),
        "bytes_canonical": len(canonical),
        "note": "differs from pinned upstream bytes ONLY by a trailing CRLF (documented "
        "text transform, not a semantic model change)",
    }
    root = ET.fromstring(data)
    wb = root.find("worldbody")
    assert wb is not None, "no worldbody"

    joints_top = root.findall(".//joint")
    joint_types = {}
    for j in joints_top:
        joint_types.setdefault(j.get("name"), j.get("type") or "hinge")
    joint_limited = {}
    joint_range = {}
    for j in joints_top:
        n = j.get("name")
        if n is not None:
            joint_limited[n] = _boolish(j.get("limited"), True)
            joint_range[n] = _range(j.attrib)

    bodies: list[SourceBody] = []
    sites: list[SourceSite] = []
    joints: list[SourceJoint] = []

    seen_coords: set[str] = set()

    def walk(body_elem, parent_name, parent_world, parent_rot, depth):
        name = body_elem.get("name")
        pos = _vec(body_elem.get("pos", "0 0 0"))
        quat = _wu(body_elem.get("quat"))
        rot = parent_rot @ _quat_to_rotmat(quat)
        world = parent_world + parent_rot @ pos

        joint_names: list[str] = []
        for j in body_elem.findall("joint"):
            jname = j.get("name")
            if jname is None:
                continue
            if jname in seen_coords:
                # duplicate direct listing (defensive; ownership is direct-children by
                # construction, so this only guards double-counterparts)
                continue
            seen_coords.add(jname)
            joint_names.append(jname)
            axis_local = _vec(j.get("axis", "0 0 1"))
            if np.linalg.norm(axis_local) < 1e-12:
                axis_local = np.array([0.0, 0.0, 1.0])
            axis_local = axis_local / np.linalg.norm(axis_local)
            jpos = _vec(j.get("pos", "0 0 0"))
            joints.append(
                SourceJoint(
                    name=jname,
                    body=name,
                    joint_type=joint_types.get(jname, "hinge"),
                    axis=axis_local.copy(),
                    axis_global=(rot @ axis_local),
                    limited=joint_limited.get(jname, True),
                    range=list(joint_range.get(jname, [0.0, 0.0])),
                    pos_local=jpos,
                )
            )

        site_names: list[str] = []
        for s in body_elem.findall("site"):
            sname = s.get("name")
            if sname is None:
                continue
            site_names.append(sname)
            sites.append(SourceSite(name=sname, body=name, pos_local=_vec(s.get("pos", "0 0 0"))))

        inertial_el = body_elem.find("inertial")
        mass = None
        com_local = None
        inertia_local = None
        if inertial_el is not None:
            mass = float(inertial_el.get("mass")) if inertial_el.get("mass") else None
            if inertial_el.get("pos"):
                com_local = _vec(inertial_el.get("pos"))
            if inertial_el.get("fullinertia"):
                ixx, iyy, izz, ixy, ixz, iyz = _vec(inertial_el.get("fullinertia"))
                inertia_local = np.array(
                    [[ixx, ixy, ixz], [ixy, iyy, iyz], [ixz, iyz, izz]], dtype=np.float64
                )
            elif inertial_el.get("diaginertia"):
                d = _vec(inertial_el.get("diaginertia"))
                inertia_local = np.diag(d)

        bodies.append(
            SourceBody(
                name=name,
                parent=parent_name,
                pos_global=world,
                quat=quat.copy(),
                joint_names=joint_names,
                site_names=site_names,
                mass=mass,
                com_local=com_local,
                inertia_local=inertia_local,
            )
        )

        for child in body_elem.findall("body"):
            walk(child, name, world, rot, depth + 1)

    for b in wb.findall("body"):
        walk(b, None, np.zeros(3), np.eye(3), 0)

    # tendons: only <tendon> elements that actually contain <spatial>
    tendons: list[SourceTendon] = []
    for t in root.findall(".//tendon"):
        for sp in t.findall("spatial"):
            sites_in = [s.get("site") for s in sp.findall("site")]
            if any(s is None for s in sites_in):
                continue
            tendons.append(SourceTendon(name=sp.get("name") or "", site_names=[s for s in sites_in]))

    # muscles: ACTUAL ACTUATORS only — <actuator><muscle> elements. The model also
    # carries an inherited <default class="muscle"><muscle .../></default> element;
    # that default is RESOLVED for missing actuator attributes but never emitted as
    # an actuator itself (no phantom muscle records). Every actuator must have a
    # unique nonempty name and a tendon that resolves to a <tendon> above.
    default_muscle_attrs: dict[str, str] = {}
    for d in root.findall(".//default"):
        for m in d.findall("muscle"):
            default_muscle_attrs.update({k: v for k, v in m.attrib.items()})
    default_muscle_attrs = dict(sorted(default_muscle_attrs.items()))
    all_muscles: list[SourceMuscle] = []
    names_seen: set[str] = set()
    tendon_names = {t.name for t in tendons}
    for m in root.findall(".//actuator/muscle"):
        name = m.get("name")
        tendon = m.get("tendon")
        if not name or not name.strip():
            raise Refusal("unnamed_actuator", "<actuator><muscle> without a name")
        if name in names_seen:
            raise Refusal("duplicate_actuator", f"actuator name {name!r} is not unique")
        names_seen.add(name)
        if not tendon or tendon not in tendon_names:
            raise Refusal(
                "invalid_tendon_ref",
                f"actuator {name!r}: tendon {tendon!r} does not resolve to a <tendon>",
            )
        declared = dict(m.attrib)

        def _attr(key: str) -> str:
            src = "declared" if key in declared else "default_class"
            val = declared.get(key, default_muscle_attrs.get(key))
            return val or "", src

        force, force_src = _attr("force")
        timeconst, tc_src = _attr("timeconst")
        lengthrange, lr_src = _attr("lengthrange")
        ctrl_limited = m.get("ctrllimited") or default_muscle_attrs.get("ctrllimited", "true")
        ctrl_range, cr_src = _attr("ctrlrange")
        all_muscles.append(
            SourceMuscle(
                name=name,
                tendon=tendon,
                force=force or None,
                timeconst=timeconst or None,
                lengthrange=lengthrange or None,
                ctrllimited=_boolish(ctrl_limited, True),
                ctrlrange=ctrl_range or "0 1",
                attr_source={
                    "name": "declared",
                    "tendon": "declared",
                    "force": force_src,
                    "timeconst": tc_src,
                    "lengthrange": lr_src,
                    "ctrllimited": "declared" if "ctrllimited" in declared else "default_class",
                    "ctrlrange": cr_src,
                },
            )
        )

    ana = SourceAnatomy(
        meta={
            "source_file": os.path.basename(path),
            "source_path": path,
            "revision": REVISION,
            "sha256": sha,
            "canonicalization": canonicalization,
            "root_body": wb.findall("body")[0].get("name"),
            "n_distinct_coords": len(seen_coords),
            "n_actuators": len(all_muscles),
            "muscle_defaults": default_muscle_attrs,
            "muscle_defaults_note": dict(
                sorted(
                    {
                        k: "inherited declaration (verbatim, never an actuator)"
                        for k in default_muscle_attrs
                    }.items()
                )
            ),
        },
        bodies=bodies,
        joints=joints,
        sites=sites,
        tendons=tendons,
        muscles=all_muscles,
    )
    ana.index()
    # post-condition: the counts the membrane cites
    assert len(ana.bodies) == 19, len(ana.bodies)
    assert len(ana.joints) == 39, len(ana.joints)
    assert len([s for s in ana.sites if s.referenced_by]) == 468, len(ana.sites)
    assert len(ana.tendons) == 120, len(ana.tendons)
    # actuators only: the default-block muscle is resolved, never counted, never emitted
    assert len(ana.muscles) == 120, len(ana.muscles)
    assert all(m.tendon is not None for m in ana.muscles)
    assert len({m.name for m in ana.muscles}) == len(ana.muscles)
    return ana


def global_site_positions(ana: SourceAnatomy) -> dict[str, np.ndarray]:
    """World-frame positions of every body site at the source rest pose."""
    out: dict[str, np.ndarray] = {}
    rot_for = {}
    for b in ana.bodies:
        rot_for[b.name] = (
            rot_for[b.parent] @ _quat_to_rotmat(b.quat) if b.parent else _quat_to_rotmat(b.quat)
        )
    for s in ana.sites:
        b = ana.body_by_name[s.body]
        out[s.name] = b.pos_global + rot_for[s.body] @ s.pos_local
    return out


if __name__ == "__main__":
    import sys

    ana = load_source(sys.argv[1] if len(sys.argv) > 1 else r"E:\PythonChimera\.tmp\chimanoid.xml")
    print("bodies:", len(ana.bodies))
    print("coords:", len(ana.joints), "| slides:", sum(1 for j in ana.joints if j.joint_type == "slide"))
    print("tendon-referenced sites:", len([s for s in ana.sites if s.referenced_by]))
    print("tendons:", len(ana.tendons), "| muscles:", len(ana.muscles))
    print("path length hist:", sorted({(len(t.site_names)) for t in ana.tendons}))