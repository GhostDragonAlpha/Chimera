"""Read-only loader for the actual monkey target geometry (Charset: ASCII).

Reads WITHOUT modifying:
  - Saved/meshes/monkey_birth.bin   (mesh_bin: [int32 N][int32 M][N*3 float32 xyz][M*3 uint32 idx])
  - Saved/meshes/monkey_joints.bin  (JNT3 pack: JNT3 <III nv,nj,nl> names \
                                      assign_i32 w_f32 J_f32 AX_f32 ROM_f32 parents_i32 joint2 w2)

Records SHA-256 of both inputs (a read that silently touched a file is a read
that returned wrong facts).  Unit scale is deliberately AUTHORED, not inferred:
   MESH_UNIT_TO_M = 0.065   # prototype scale, not a biological measurement.

Measured facts this module exposes for the actual-target fit (all in kilometres -> no, meters):
  - joint_pos_m[name]      joint position in AUTHORED metres,
  - joint_axis[name]       sweep axis (already what the engine runs, verbatim),
  - joint_parent[name]     FK parent (root spine_lower),
  - bone_len_m(parent_child_chain)   axial evidence per segment,
  - band_extent_m(joint, dir)        transverse cross-section spread of a joint's vertices,
  - tip positions for extremities the rig itself measures on the mesh (hand/foot/tail),
  - degrees_of_freedom ledger: which source body has NO target joint -> its segment is unresolved.

Run:  python mesh_target.py           (prints the ledger + a few measured bones)
"""
from __future__ import annotations

import hashlib
import os
import struct

import numpy as np

MESH_BIRTH = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_birth.bin"  # A2 audit copy: baseline snapshot input
PACK_JNT3 = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_joints.bin"  # A2 audit copy: baseline snapshot input

# AUTHORED prototype scale (mesh units -> metres). Not a biological measurement:
# it makes the ~9.3-unit tall mesh a ~0.60 m tall macaque, which is the size
# class the source anatomy models. The number itself is an authorship.
MESH_UNIT_TO_M = 0.065


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_mesh(path: str) -> tuple[np.ndarray, np.ndarray]:
    """(V, F) in mesh units: [N][M][N*3 xyz f32][M*3 idx u32]."""
    b = open(path, "rb").read()
    N, M = struct.unpack("<ii", b[:8])
    V = np.frombuffer(b, np.float32, N * 3, 8).reshape(N, 3).astype(np.float64)
    F = np.frombuffer(b, np.uint32, M * 3, 8 + N * 12).reshape(M, 3)
    return V, F


def load_pack(path: str) -> dict:
    """JNT3 pack -> dict of arrays (mesh units). Replicates tools/rig_factory_fit.py."""
    b = open(path, "rb").read()
    tag = b[:4]
    assert tag == b"JNT3", tag
    nv, nj, nl = struct.unpack("<III", b[4:16])
    names = [n.decode("ascii") for n in b[16 : 16 + nl].split(b"\x00") if n][:nj]
    p = 16 + nl
    assign = np.frombuffer(b, np.int32, nv, p).copy()
    p += nv * 4
    w = np.frombuffer(b, np.float32, nv, p).copy()
    p += nv * 4
    J = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3).astype(np.float64).copy()
    p += nj * 12
    AX = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3).astype(np.float64).copy()
    p += nj * 12
    ROM = np.frombuffer(b, np.float32, nj * 2, p).reshape(nj, 2).copy()
    p += nj * 8
    parents = np.frombuffer(b, np.int32, nj, p).copy()
    p += nj * 4
    joint2 = np.frombuffer(b, np.int32, nv, p).copy()
    p += nv * 4
    w2 = np.frombuffer(b, np.float32, nv, p).copy()
    assert p + nv * 4 == len(b), (p + nv * 4, len(b))
    return {
        "names": names, "assign": assign, "w": w, "J": J, "AX": AX,
        "ROM": ROM, "parents": parents, "joint2": joint2, "w2": w2,
    }


class MonkeyTarget:
    """Immutable actual-target geometry (all positions -> authored metres)."""

    def __init__(self, birth_path: str = MESH_BIRTH, pack_path: str = PACK_JNT3):
        self.birth_sha = sha256_of(birth_path)
        self.pack_sha = sha256_of(pack_path)
        self.input_bytes = {"birth": os.path.getsize(birth_path), "pack": os.path.getsize(pack_path)}
        V, F = load_mesh(birth_path)
        pk = load_pack(pack_path)
        self.V = V * MESH_UNIT_TO_M
        self.F = F
        self.names = pk["names"]
        self.assign = pk["assign"]
        self.J = pk["J"] * MESH_UNIT_TO_M
        self.AX = pk["AX"]
        self.ROM = pk["ROM"]
        self.parents = pk["parents"]
        self.idx = {n: i for i, n in enumerate(self.names)}
        self._pk = pk  # raw for band math (units are ratios, keep as-is)
        self._check_frame_consistent()
        self.tips = self._measure_tips()

    def _check_frame_consistent(self) -> None:
        """The pack was measured on THIS mesh: every joint must sit on/near the surface."""
        nn = self._nearest(self.J, self.V)
        d = np.linalg.norm(self.J - self.V[nn], axis=1)
        worst = float(d.max())
        # bones sit on the skin surface (medoid-snapped); a 3 cm (in mesh-units ~0.46)
        # tolerance is enough to catch a frame mismatch without being a shape critic.
        if worst > 0.5 * MESH_UNIT_TO_M:
            raise ValueError(f"pack J and birth mesh disagree in frame: max surface gap {worst:.4f} m")

    @staticmethod
    def _nearest(pts: np.ndarray, V: np.ndarray) -> np.ndarray:
        out = np.empty(len(pts), dtype=np.int64)
        for i, p in enumerate(pts):
            out[i] = int(np.argmin(np.sum((V - p) ** 2, axis=1)))
        return out

    # ---- measured facts ----------------------------------------------------
    def joint_pos(self, name: str) -> np.ndarray:
        return self.J[self.idx[name]].copy()

    def bone_len(self, prox: str, dist: str) -> float:
        """Axial evidence: |J_dist - J_prox| in metres (both ends measured joints)."""
        return float(np.linalg.norm(self.J[self.idx[dist]] - self.J[self.idx[prox]]))

    def band_verts(self, name: str) -> np.ndarray:
        """Vertices whose primary owner is `name`, in metres. Returns empty if none."""
        ids = np.where(self.assign == self.idx[name])[0]
        return self.V[ids].copy()

    def _measure_tips(self) -> dict[str, np.ndarray]:
        """Reproducible extremity tips (metres): centroid of the k mesh vertices
        farthest beyond the distal joint (the rig's own measurement law)."""
        out = {}

        def beyond(dist_joint: str, prox_joint: str, k: int, cap: float) -> np.ndarray:
            dJ = self.J[self.idx[dist_joint]]
            pJ = self.J[self.idx[prox_joint]]
            dd = np.linalg.norm(self.V - dJ.reshape(1, 3), axis=1)
            pdd = np.linalg.norm(self.V - pJ.reshape(1, 3), axis=1)
            arm = np.linalg.norm(dJ - pJ)
            cand = np.where((pdd < cap * arm) & (dd > arm))[0]
            if len(cand) == 0:
                cand = np.argsort(-dd)[:k]
            ids = cand[np.argsort(-dd[cand])][:k]
            return self.V[ids].mean(axis=0)

        out["hand_tip"] = beyond("wrist_L", "elbow_L", 30, 1.2)
        out["foot_tip"] = beyond("ankle_L", "knee_L", 30, 1.0)
        aJ = self.J[self.idx["ankle_L"]]
        d = np.linalg.norm(self.V - aJ.reshape(1, 3), axis=1)
        out["toe_tip"] = self.V[np.argsort(-d)[:30]].mean(axis=0)
        return out

    def band_extent(self, name: str, direction: np.ndarray) -> float:
        """Transverse evidence: max-min vertex spread of a joint's own band along
        `direction` (a unit vector], in metres.  0 if the band is empty."""
        v = self.band_verts(name)
        if len(v) == 0:
            return 0.0
        d = np.asarray(direction, dtype=np.float64)
        d = d / np.linalg.norm(d)
        proj = v @ d
        return float(proj.max() - proj.min())

    # ---- ledger -------------------------------------------------------------
    def limb_xml_chain(self) -> dict[str, tuple[str, str, str]]:
        """(source_body) -> (pack_prox_joint, pack_dist_joint, kind) for each
        source segment that HAS a joint-pair target. kind: 'joint_pair' | 'tip'. """
        chains = {
            "femur_r": ("hip_L", "knee_L", "joint_pair"),
            "tibia_r": ("knee_L", "ankle_L", "joint_pair"),
            "humerus": ("shoulder_L", "elbow_L", "joint_pair"),
            "ulna": ("elbow_L", "wrist_L", "joint_pair"),
            "radius": ("wrist_L", "hand_tip", "tip"),
            "talus_r": ("ankle_L", "foot_tip", "tip"),
            "toes_r": ("foot_tip", "toe_tip", "tip"),
            "thorax_dummy": ("spine_lower", "spine_mid", "joint_pair"),
            "thorax": ("spine_mid", "spine_upper", "joint_pair"),
        }
        within = {}
        for src, (p, d, kind) in chains.items():
            suffix = "" if src.endswith(("humerus", "ulna", "radius", "thorax_dummy", "thorax")) else ""
            within[src] = (p, d, kind)
        return within


def main() -> int:
    mt = MonkeyTarget()
    print(f"birth  sha256 {mt.birth_sha}  ({mt.input_bytes['birth']} bytes)")
    print(f"pack   sha256 {mt.pack_sha}  ({mt.input_bytes['pack']} bytes)")
    print(f"mesh verts {len(mt.V)} tris {len(mt.F)}  x-range "
          f"[{mt.V[:,0].min():.3f},{mt.V[:,0].max():.3f}] y [{mt.V[:,1].min():.3f},{mt.V[:,1].max():.3f}] "
          f"z [{mt.V[:,2].min():.3f},{mt.V[:,2].max():.3f}] m")
    print(f"joints {len(mt.names)}:", ", ".join(mt.names))
    chains = mt.limb_xml_chain()
    for src, (p, d, kind) in chains.items():
        if kind == "joint_pair":
            ln = mt.bone_len(p, d)
        else:
            p_ref = mt.joint_pos(p) if p in mt.idx else mt.tips[p]
            ln = float(np.linalg.norm(mt.tips[d] - p_ref))
        print(f"  {src:13s} {p:>11s}->{d:>10s} = {ln:.4f} m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())