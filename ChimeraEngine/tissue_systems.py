"""tissue_systems.py -- TISSUE = SEPARATE TRIANGLE SYSTEMS COUPLING AT INTERFACES.

THE_WOLFRAM_FRAME section 3: there is no one body mesh. Skin, muscle, and bone are each
their OWN triangle system; they couple at shared interface nodes, not by merging. This
module is the scaffold for exactly that: N independent TriangleSystems (each with its own
vertices, faces, and local update rule) plus a TissueCoupling that enforces position
equality at the shared interface node set -- the "N mesh slots + cross-system constraints"
the frame names as the engine consequence.

MEMBRANE (Rule 0):
  STATEMENT   tissue is separate triangle systems coupling at interfaces, not one blob.
  PREDICTION  given coupled interface nodes, all three systems satisfy displacement
              continuity at the interfaces within tolerance under a prescribed boundary
              motion of the rigid frame.
  FALSIFIER   interface separation exceeds tolerance after enforcement, or any system
              diverges (non-finite positions, unbounded displacement from rest).

Triangle-primary: the mesh IS the carrier; splats are deferred frosting and do not appear
here. The per-system relaxation parameters are SCAFFOLD placeholders -- the in-between
must be TRAINED later (frame section 5); this file only proves the coupling architecture
holds, with no UE and no splat anywhere.
"""
from __future__ import annotations

import numpy as np


def rot_y(theta: float) -> np.ndarray:
    """Rotation by theta about +Y, column-vector convention (p' = R @ p)."""
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


class TriangleSystem:
    """One tissue system: its own triangle mesh and its own local rule.

    Vertices are row vectors (N,3). A subset -- interface_idx -- is OWNED BY THE
    COUPLING: the system's update rule never moves those vertices; TissueCoupling does.
    Every other vertex is free and moved by the system's own rule alone. That ownership
    split is what keeps the systems separable: nothing in one system's rule reaches into
    another system's state except through the shared interface nodes.
    """

    def __init__(self, name: str, rest: np.ndarray, faces: np.ndarray,
                 interface_idx: np.ndarray):
        self.name = name
        self.rest = np.asarray(rest, dtype=np.float64)
        self.pos = self.rest.copy()
        self.faces = np.asarray(faces, dtype=np.int64)
        self.interface_idx = np.asarray(interface_idx, dtype=np.int64)
        self._edges = self._build_edges()
        self.alpha = 1.0 / self._laplacian_eigenmax()

    @property
    def n_vertices(self) -> int:
        return len(self.rest)

    @property
    def n_faces(self) -> int:
        return len(self.faces)

    def _build_edges(self):
        """Unique undirected edges with rest lengths, from the faces."""
        seen = set()
        edges = []
        for a, b, c in self.faces:
            for i, j in ((a, b), (b, c), (c, a)):
                key = (min(i, j), max(i, j))
                if key not in seen:
                    seen.add(key)
                    rest_len = float(np.linalg.norm(self.rest[i] - self.rest[j]))
                    edges.append((int(i), int(j), rest_len))
        return edges

    def _laplacian_eigenmax(self) -> float:
        """Largest eigenvalue of the lattice's projected edge Laplacian at rest.

        Linearizing spring_relax about the rest shape gives exactly this operator, so
        the Jacobi stability bound alpha < 2/lambda_max follows from it -- the relaxation
        step size is DERIVED from the lattice, not chosen.
        """
        n = self.n_vertices
        L = np.zeros((3 * n, 3 * n))
        for a, b, rest_len in self._edges:
            u = (self.rest[b] - self.rest[a]) / max(rest_len, 1e-12)
            W = np.outer(u, u)
            A, B = slice(3 * a, 3 * a + 3), slice(3 * b, 3 * b + 3)
            L[A, A] += W
            L[B, B] += W
            L[A, B] -= W
            L[B, A] -= W
        return float(np.linalg.eigvalsh(L).max())

    def spring_relax(self, alpha: float | None = None) -> None:
        """Massless spring relaxation of the FREE vertices only.

        Each free vertex moves by alpha times the sum over its edges of (current_len -
        rest_len) along the edge direction -- a simple local rule that runs, not an
        authored deformation. Stable for alpha in (0, 2/lambda_max); self.alpha is the
        derived midpoint 1/lambda_max. The per-tissue value is scaffold until the
        in-between is trained (frame section 5).
        """
        if alpha is None:
            alpha = self.alpha
        p = self.pos
        free = np.setdiff1d(np.arange(self.n_vertices), self.interface_idx)
        for i in free:
            pull = np.zeros(3)
            for (a, b, rest_len) in self._edges:
                if a != i and b != i:
                    continue
                j = b if a == i else a
                d = p[j] - p[i]
                dist = float(np.linalg.norm(d))
                if dist < 1e-12:
                    continue
                pull += (dist - rest_len) * (d / dist)
            p[i] += alpha * pull

    def update(self) -> None:
        raise NotImplementedError


class RigidSystem(TriangleSystem):
    """The bone frame: kinematic. Its pose is prescribed; the whole mesh follows exactly."""

    def set_pose(self, R: np.ndarray) -> None:
        self.pos = self.rest @ R.T

    def update(self) -> None:
        pass


class TissueCoupling:
    """Cross-system constraint at the shared interface node set.

    Every member system carries the SAME number of interface vertices and the k-th
    vertex of each is one physical node. enforce() projects all members' copies of each
    node onto their mean -- equal weight, no leader assumed -- so that after enforcement
    every member agrees at every interface node to float precision. It returns the
    pre-enforcement separation (the demand placed on the constraint) and the residual
    after; a healthy coupled run shows bounded demand and ~zero residual.
    """

    def __init__(self, systems):
        self.systems = list(systems)
        n = len(self.systems[0].interface_idx)
        for s in self.systems:
            if len(s.interface_idx) != n:
                raise ValueError(
                    f"system {s.name!r} has {len(s.interface_idx)} interface vertices, "
                    f"expected {n}; the shared node set must match across systems")

    @property
    def n_nodes(self) -> int:
        return len(self.systems[0].interface_idx)

    def enforce(self):
        """One projection pass. Returns (pre_gap_max, post_gap_max, per_node_pre)."""
        S = np.stack([s.pos[s.interface_idx] for s in self.systems])  # (M, K, 3)

        def max_pairwise(A):
            d = np.sqrt(((A[:, None, :] - A[None, :, :]) ** 2).sum(-1))
            return d.max(axis=(0, 1))

        pre = max_pairwise(S)
        mean = S.mean(axis=0)  # (K, 3)
        for s in self.systems:
            s.pos[s.interface_idx] = mean
        post = max_pairwise(np.stack([s.pos[s.interface_idx] for s in self.systems]))
        return float(pre.max()), float(post.max()), pre


def _ring(x: float, radius: float, K: int) -> np.ndarray:
    phi = 2.0 * np.pi * np.arange(K) / K
    return np.column_stack([np.full(K, x), radius * np.cos(phi), radius * np.sin(phi)])


def build_limb_segment(K: int = 8, L: float = 1.0, r_neck: float = 0.2,
                       belly: dict | None = None) -> dict[str, TriangleSystem]:
    """One limb segment as three separate triangle systems with matching interfaces.

    All three share the same two neck rings (K nodes each at x=0 and x=L, radius
    r_neck) -- those 2*K nodes are the shared interface set, positionally corresponding
    across systems. Between the necks each system bulges to its own belly radius:
    bone least, skin most, so the nesting bone < muscle < skin holds at every cross-
    section and nothing is welded together. Muscle gets two belly rings (a denser
    lattice); bone and skin get one.
    """
    if belly is None:
        belly = {"bone": 0.3 * L, "muscle": 0.45 * L, "skin": 0.6 * L}

    return {
        "bone": RigidSystem(*system_args(
            "bone", [(0.0, r_neck), (0.5 * L, belly["bone"]), (L, r_neck)], K)),
        "muscle": TriangleSystem(*system_args(
            "muscle", [(0.0, r_neck), (L / 3, belly["muscle"]),
                       (2.0 * L / 3, belly["muscle"]), (L, r_neck)], K)),
        "skin": TriangleSystem(*system_args(
            "skin", [(0.0, r_neck), (0.5 * L, belly["skin"]), (L, r_neck)], K)),
    }


def system_args(name, ring_specs, K):
    rings = [_ring(x, r, K) for x, r in ring_specs]
    rest = np.vstack(rings)
    faces = []
    for A, B in zip(rings[:-1], rings[1:]):
        base_a, base_b = 0, len(A)
        for k2 in range(K):
            k3 = (k2 + 1) % K
            faces.append((base_a + k2, base_a + k3, base_b + k2))
            faces.append((base_a + k3, base_b + k3, base_b + k2))
    interface_idx = np.concatenate([np.arange(K), np.arange(len(rest) - K, len(rest))])
    return name, rest, np.array(faces, dtype=np.int64), interface_idx
