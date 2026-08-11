"""matrix_store.py -- the writer side of the matrix.

The record IS the matrix: ``record.npz`` holds ``pos (T, N, 3)`` and
``vel (T, N, 3)`` per membrane -- the exact schema ``physics.emit`` already
reads.  The master loop's missing half was a WRITER: it evolved live state
every pass and then threw it away.  This store gives every membrane the same
shape as theLight's record, so anything the master loop does becomes a
replayable record by the same needle, at zero conversion on the render path
(the hot path never changes format -- that is the performance claim).

Gradient-descent framing (the operator's): a groove is a COUPLING -- the
control signal that changes how the descent is applied (an LLM switching from
"angry mode" to "happy mode" is a coupling switch).  Positions are the walked
state.  The store therefore keeps both histories side by side:

    <root>/matrix/<membrane>/record.npz      pos (T,N,3) f32, vel (T,N,3) f32
    <root>/matrix/<membrane>/couplings.npz   couplings (T,K) f32  (the grooves)
    <root>/matrix/<membrane>/meta.json       packets, pass count, membrane meta

Replaying a stored membrane re-applies its recorded couplings over its
recorded state -- the same descent, the same law, the same look.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

NCOLS = 3


@dataclass
class Membrane:
    """One membrane of the matrix: walked state + the couplings that walked it."""

    name: str
    n_packets: int
    coupling_names: tuple[str, ...] = ()
    pos: np.ndarray = field(default_factory=lambda: np.zeros((0, 1, 3), np.float32))
    vel: np.ndarray = field(default_factory=lambda: np.zeros((0, 1, 3), np.float32))
    couplings: np.ndarray = field(default_factory=lambda: np.zeros((0, 0), np.float32))
    meta: dict = field(default_factory=dict)

    def append(self, pos: np.ndarray, vel: np.ndarray | None = None,
               couplings: np.ndarray | None = None) -> None:
        p = np.ascontiguousarray(pos, dtype=np.float32).reshape(1, -1, 3)
        v = (np.zeros_like(p) if vel is None else
             np.ascontiguousarray(vel, dtype=np.float32).reshape(1, -1, 3))
        if self.pos.size == 0:
            self.pos = p
            self.vel = v
        else:
            self.pos = np.concatenate([self.pos, p], axis=0)
            self.vel = np.concatenate([self.vel, v], axis=0)
        if couplings is not None:
            c = np.ascontiguousarray(couplings, dtype=np.float32).reshape(1, -1)
            if self.couplings.size == 0:
                self.couplings = c
            else:
                self.couplings = np.concatenate([self.couplings, c], axis=0)
        elif self.couplings.size == 0:
            self.couplings = np.zeros((self.pos.shape[0], 0), np.float32)

    @property
    def passes(self) -> int:
        return self.pos.shape[0]


@dataclass
class MatrixStore:
    """All membranes written by one master-loop run."""

    root: Path
    membranes: dict[str, Membrane] = field(default_factory=dict)

    def add(self, name: str, n_packets: int,
            coupling_names: tuple[str, ...] = (), meta: dict | None = None) -> Membrane:
        m = Membrane(name=name, n_packets=n_packets,
                     coupling_names=tuple(coupling_names), meta=meta or {})
        self.membranes[name] = m
        return m

    def save(self) -> Path:
        base = Path(self.root)
        for name, m in self.membranes.items():
            d = base / name
            d.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(d / "record.npz", pos=m.pos, vel=m.vel)
            if m.couplings.size:
                np.savez_compressed(d / "couplings.npz",
                                    couplings=m.couplings,
                                    names=np.asarray(m.coupling_names, dtype="U"))
            meta = dict(m.meta, packets=m.n_packets, passes=m.passes,
                        couplings=m.coupling_names)
            (d / "meta.json").write_text(json.dumps(meta, indent=2))
        return base

    @classmethod
    def load(cls, root: Path) -> "MatrixStore":
        root = Path(root)
        st = cls(root)
        for d in sorted(root.iterdir()):
            if not d.is_dir():
                continue
            rec = np.load(d / "record.npz", allow_pickle=False)
            coups = np.load(d / "couplings.npz", allow_pickle=False) \
                if (d / "couplings.npz").exists() else None
            names = tuple(str(x) for x in coups["names"]) if coups is not None else ()
            m = Membrane(
                name=d.name,
                n_packets=rec["pos"].shape[1],
                coupling_names=names,
                pos=rec["pos"].astype(np.float32),
                vel=rec["vel"].astype(np.float32),
                couplings=(coups["couplings"].astype(np.float32)
                           if coups is not None else np.zeros((0, 0), np.float32)),
                meta=json.loads((d / "meta.json").read_text()),
            )
            st.membranes[d.name] = m
        return st
