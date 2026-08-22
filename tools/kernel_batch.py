"""RUN 32 (STEP-3 FORK-2, pre-registered in tools/kernel_walk.py's
docstring): the BATCHED KERNEL DYNAMICS PORT.

Loads the stand_dump contract (models/cad_bear/bear_build_stand.npz --
the t=0 build state from the proven Python harness) and runs E
parallel bears with the IDENTICAL step math (DRAW gravity; K_S floor
wall + per-packet critical damping + Coulomb-capped viscous stick;
four spring-bond networks, stand mode = unstressed anchors, no
control; semi-implicit Euler + Rodrigues at the same dt), torch
float64 on the GPU.

Then the regression: compares every 50 ms checkpoint against the
Python reference (models/cad_bear/bear_stand_ref.npz). Pre-registered
tolerance: |dcom| < 1e-6 m per body, |dtilt| < 1e-4 deg, at every
checkpoint over SETTLE_T = 3.0 s. PASS/FAIL is printed; FAIL = the
falsifier fired (a math difference, not a float effect) -- find it or
fork 2 stops.

RUN 32 RESULT: PASS (61 checkpoints, max |dcom| = 3.704e-16 m, max
|dtilt| = 4.505e-12 deg -- float64 machine epsilon).

F2-b extension (RUN 33, pre-registered in kernel_walk.py's docstring):
BatchBear.step(act=None) accepts an (E,8) command tensor -- (phi_s,
th) per net in NET_NAMES order -- rotating each net's rest anchors by
Q = Rz(phi_s) @ Rx(th) about jf = JP - parent.com, mirroring
kernel_walk.py:3465-3478 exactly (zero command = identity rotation =
the verified uncommanded path, bit-identical). obs() returns the
measured state channels for the policy. Load the GAIT build
(bear_build_gait.npz -- post-prestress) for training; the stand
build/ref pair stays the regression contract.

Usage: .venv-gs/Scripts/python.exe -u tools/kernel_batch.py [E]
"""

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "models" / "cad_bear" / "bear_build_stand.npz"
BUILD_GAIT = ROOT / "models" / "cad_bear" / "bear_build_gait.npz"
REF = ROOT / "models" / "cad_bear" / "bear_stand_ref.npz"

DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
DTYPE = torch.float64

BODY_NAMES = ("trunk", "leg_L", "leg_R", "foot_L", "foot_R")
NET_NAMES = ("hip_L", "ankle_L", "hip_R", "ankle_R")

# pre-registered tolerance (kernel_walk.py docstring, RUN 32)
TOL_COM = 1e-6      # m per body per checkpoint
TOL_TILT = 1e-4     # deg per body per checkpoint


def _t(a: np.ndarray) -> torch.Tensor:
    return torch.as_tensor(a, dtype=DTYPE, device=DEV)


class BatchBear:
    """E parallel copies of the 5-body kernel bear, float64 GPU."""

    def __init__(self, path: Path, n_env: int):
        d = np.load(path, allow_pickle=False)
        self.n_env = n_env
        self.G = float(d["G"])
        self.K_S = float(d["K_S"])
        self.MU = float(d["MU"])
        self.dt = float(d["dt"])
        self.steps = int(d["steps"])

        # per-body static tensors (shared across envs)
        self.rel, self.mass, self.I, self.M = {}, {}, {}, {}
        self.band_idx, self.c_tp = {}, {}
        for n in BODY_NAMES:
            rel = _t(d[f"rel_{n}"])
            mass = _t(d[f"mass_{n}"])
            self.rel[n] = rel
            self.mass[n] = mass
            self.I[n] = _t(d[f"I_{n}"])
            self.M[n] = float(d[f"mass_{n}"].sum())
            band = d[f"band_{n}"]
            self.band_idx[n] = torch.as_tensor(
                np.nonzero(band)[0], dtype=torch.long, device=DEV)
            if len(self.band_idx[n]):
                self.c_tp[n] = 2.0 * torch.sqrt(
                    self.K_S * mass[self.band_idx[n]])
        self.c_n = {n: float(d[f"c_n_{n}"]) for n in ("foot_L", "foot_R")}
        self.c_r = {n: _t(d[f"c_r_{n}"]) for n in ("foot_L", "foot_R")}

        # bond nets (stand mode: anchors as dumped, no command rotation)
        self.nets = []
        for nm in NET_NAMES:
            child = str(d[f"net_{nm}_child"])
            parent = str(d[f"net_{nm}_parent"])
            idx_np = np.asarray(d[f"net_{nm}_idx"])
            self.nets.append({
                "parent": parent,
                "child": child,
                "JP": _t(d[f"net_{nm}_JP"]),
                "rel_idx": _t(d[f"rel_{child}"][idx_np]),
                "anchor": _t(d[f"net_{nm}_anchor"]),
                "k_b": float(d[f"net_{nm}_kb"]),
                "cb": _t(d[f"net_{nm}_cb"]),
            })

        # per-env state
        self.com = torch.stack([_t(d[f"com0_{n}"]) for n in BODY_NAMES])
        self.com = self.com.unsqueeze(0).repeat(n_env, 1, 1)  # (E,5,3)
        self.R = torch.eye(3, dtype=DTYPE, device=DEV)
        self.R = self.R.view(1, 1, 3, 3).repeat(n_env, 5, 1, 1)
        self.v = torch.zeros(n_env, 5, 3, dtype=DTYPE, device=DEV)
        self.wv = torch.zeros(n_env, 5, 3, dtype=DTYPE, device=DEV)
        # per-env foot normal forces, refreshed every step (obs channel)
        self.Fn = torch.zeros(n_env, 2, dtype=DTYPE, device=DEV)
        self.bidx = {n: i for i, n in enumerate(BODY_NAMES)}
        self._com0 = self.com.clone()
        self._R0 = self.R.clone()

    def reset(self) -> None:
        """Restore the dumped t=0 state (F2-b: between episodes)."""
        self.com.copy_(self._com0)
        self.R.copy_(self._R0)
        self.v.zero_()
        self.wv.zero_()
        self.Fn.zero_()

    def _world(self, name: str, rel: torch.Tensor) -> torch.Tensor:
        i = self.bidx[name]
        return (torch.einsum("eij,pj->epi", self.R[:, i], rel)
                + self.com[:, i:i + 1, :])

    def step(self, act: torch.Tensor | None = None) -> None:
        E = self.n_env
        force = torch.zeros(E, 5, 3, dtype=DTYPE, device=DEV)
        torque = torch.zeros(E, 5, 3, dtype=DTYPE, device=DEV)
        # DRAW
        for i, n in enumerate(BODY_NAMES):
            force[:, i, 1] -= self.M[n] * self.G
        # RESISTANCE: floor wall on each foot's band
        for fi, fn in enumerate(("foot_L", "foot_R")):
            i = self.bidx[fn]
            wb = self._world(fn, self.rel[fn][self.band_idx[fn]])
            pen = -wb[:, :, 1]
            contact = pen > 0
            Fy = torch.where(contact, self.K_S * pen,
                             torch.zeros_like(pen))
            Fn = Fy.sum(1)                                    # (E,)
            self.Fn[:, fi] = Fn
            has_c = contact.any(1).to(DTYPE).unsqueeze(1)     # (E,1)
            r = wb - self.com[:, i:i + 1, :]
            damped = Fn - self.c_n[fn] * self.v[:, i, 1]
            force[:, i, 1] += (has_c[:, 0]
                               * torch.clamp(damped, min=0.0))
            z3 = torch.zeros_like(Fy)
            Fcol = torch.stack([z3, Fy, z3], dim=2)           # (E,P,3)
            torque[:, i] += torch.cross(r, Fcol, dim=2).sum(1)
            torque[:, i] -= has_c * self.c_r[fn] * self.wv[:, i]
            # Coulomb-capped tangential stick (viscous form)
            v_p = (self.v[:, i:i + 1, :]
                   + torch.cross(self.wv[:, i:i + 1, :].expand(-1, r.shape[1], -1),
                                 r, dim=2))
            v_t = v_p.clone()
            v_t[:, :, 1] = 0.0
            sp = torch.linalg.norm(v_t, dim=2)
            c_tp = self.c_tp[fn].unsqueeze(0)                 # (1,P)
            Ft = torch.minimum(self.MU * Fy, c_tp * sp)
            moving = (sp > 0) & contact
            scale = torch.where(moving,
                                -Ft / torch.clamp(sp, min=1e-300),
                                torch.zeros_like(sp))
            F3 = scale.unsqueeze(2) * v_t
            force[:, i] += F3.sum(1)
            torque[:, i] += torch.cross(r, F3, dim=2).sum(1)
        # RESISTANCE: the four spring-bond networks. act=None reproduces
        # the verified uncommanded path bit-identically; otherwise each
        # net's rest anchors rotate by Q = Rz(phi_s) @ Rx(th) about
        # jf = JP - parent.com (kernel_walk.py:3465-3478, mirrored).
        for ni, net in enumerate(self.nets):
            ip, ic = self.bidx[net["parent"]], self.bidx[net["child"]]
            if act is None:
                A = self._world(net["parent"], net["anchor"])
            else:
                jf = net["JP"].unsqueeze(0) - self.com[:, ip]   # (E,3)
                phi_s, th = act[:, 2 * ni], act[:, 2 * ni + 1]
                cp, sp = torch.cos(phi_s), torch.sin(phi_s)
                ct, st = torch.cos(th), torch.sin(th)
                z = torch.zeros_like(cp)
                # Q = Rz(phi_s) @ Rx(th), rows:
                # [cp, -sp*ct, sp*st] [sp, cp*ct, -cp*st] [0, st, ct]
                Q = torch.stack([
                    torch.stack([cp, -sp * ct, sp * st], 1),
                    torch.stack([sp, cp * ct, -cp * st], 1),
                    torch.stack([z, st, ct], 1)], dim=1)         # (E,3,3)
                rel_a = (net["anchor"].unsqueeze(0)
                         - jf.unsqueeze(1))                      # (E,P,3)
                at = (jf.unsqueeze(1)
                      + torch.einsum("epj,ekj->epk", rel_a, Q))
                A = (torch.einsum("eij,epj->epi", self.R[:, ip], at)
                     + self.com[:, ip:ip + 1, :])
            P = self._world(net["child"], net["rel_idx"])
            va = (self.v[:, ip:ip + 1, :]
                  + torch.cross(self.wv[:, ip:ip + 1, :].expand(-1, A.shape[1], -1),
                                A - self.com[:, ip:ip + 1, :], dim=2))
            vp = (self.v[:, ic:ic + 1, :]
                  + torch.cross(self.wv[:, ic:ic + 1, :].expand(-1, P.shape[1], -1),
                                P - self.com[:, ic:ic + 1, :], dim=2))
            F = net["k_b"] * (A - P) - net["cb"].unsqueeze(0).unsqueeze(2) * (vp - va)
            Fs = F.sum(1)
            force[:, ic] += Fs
            torque[:, ic] += torch.cross(P - self.com[:, ic:ic + 1, :],
                                         F, dim=2).sum(1)
            force[:, ip] -= Fs
            torque[:, ip] -= torch.cross(A - self.com[:, ip:ip + 1, :],
                                         F, dim=2).sum(1)
        # integrate (semi-implicit Euler + Rodrigues, batched)
        for i, n in enumerate(BODY_NAMES):
            self.v[:, i] += (force[:, i] / self.M[n]) * self.dt
            self.com[:, i] += self.v[:, i] * self.dt
            Iw = self.R[:, i] @ self.I[n] @ self.R[:, i].transpose(1, 2)
            self.wv[:, i] += torch.linalg.solve(Iw, torque[:, i]) * self.dt
            wn = torch.linalg.norm(self.wv[:, i], dim=1, keepdim=True)
            th = wn * self.dt                                  # (E,1)
            ax = self.wv[:, i] / torch.clamp(wn, min=1e-300)   # (E,3)
            Km = torch.zeros(E, 3, 3, dtype=DTYPE, device=DEV)
            Km[:, 0, 1] = -ax[:, 2]; Km[:, 0, 2] = ax[:, 1]
            Km[:, 1, 0] = ax[:, 2];  Km[:, 1, 2] = -ax[:, 0]
            Km[:, 2, 0] = -ax[:, 1]; Km[:, 2, 1] = ax[:, 0]
            eye = torch.eye(3, dtype=DTYPE, device=DEV).expand(E, 3, 3)
            sth = torch.sin(th).unsqueeze(2)
            cth = (1.0 - torch.cos(th)).unsqueeze(2)
            self.R[:, i] = (eye + sth * Km + cth * (Km @ Km)) @ self.R[:, i]

    def checkpoint(self):
        """(com (5,3) env-0, tilt deg (5,) env-0) at the CURRENT state --
        the reference records at loop top, pre-apply; callers match the
        cadence."""
        coms = self.com[0].detach().cpu().numpy()
        up = torch.einsum("eij,j->ei", self.R[0],
                          torch.tensor([0.0, 1.0, 0.0],
                                       dtype=DTYPE, device=DEV))
        tls = np.rad2deg(np.arccos(np.clip(
            up[:, 1].cpu().numpy(), -1.0, 1.0)))
        return coms, tls

    def obs(self) -> torch.Tensor:
        """(E,18) measured state channels (RUN 33 pre-registration):
        up-vector (x,z) of trunk/leg_L/leg_R [6]; com (x,z) of trunk,
        foot_L, foot_R in mm [6]; trunk v (x,z) in mm/s [2]; trunk wv
        (x,z) [2]; Fn_L, Fn_R as fractions of total weight [2] -- the
        channels the 21-run tree steered with."""
        E = self.n_env
        y = torch.tensor([0.0, 1.0, 0.0], dtype=DTYPE, device=DEV)
        cols = []
        for n in ("trunk", "leg_L", "leg_R"):
            up = torch.einsum("eij,j->ei", self.R[:, self.bidx[n]], y)
            cols += [up[:, 0:1], up[:, 2:3]]
        for n in ("trunk", "foot_L", "foot_R"):
            c = self.com[:, self.bidx[n]]
            cols += [c[:, 0:1] * 1e3, c[:, 2:3] * 1e3]
        it = self.bidx["trunk"]
        cols += [self.v[:, it, 0:1] * 1e3, self.v[:, it, 2:3] * 1e3]
        cols += [self.wv[:, it, 0:1], self.wv[:, it, 2:3]]
        W = sum(self.M[n] for n in BODY_NAMES) * self.G
        cols += [(self.Fn[:, 0:1] / W), (self.Fn[:, 1:2] / W)]
        return torch.cat(cols, dim=1)                            # (E,18)


def main() -> int:
    n_env = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    bear = BatchBear(BUILD, n_env)
    ref = np.load(REF)
    ref_t = ref["t"]
    rec2 = max(1, int(0.05 / bear.dt))   # identical to the reference's
    print(f"batch port: E={n_env}  dt={bear.dt:.3e}  steps={bear.steps}  "
          f"device={DEV}  dtype={DTYPE}")
    max_dcom = 0.0
    max_dtilt = 0.0
    n_ck = 0
    for k in range(bear.steps):
        if k % rec2 == 0 and n_ck < len(ref_t):
            coms, tls = bear.checkpoint()
            dc = max(float(np.abs(coms[j] - ref[f"com_{n}"][n_ck]).max())
                     for j, n in enumerate(BODY_NAMES))
            dtl = max(abs(float(tls[j] - ref[f"tilt_{n}"][n_ck]))
                      for j, n in enumerate(BODY_NAMES))
            max_dcom = max(max_dcom, dc)
            max_dtilt = max(max_dtilt, dtl)
            n_ck += 1
        bear.step()
    print(f"checkpoints compared: {n_ck} (ref has {len(ref_t)})")
    print(f"max |dcom|  = {max_dcom:.3e} m   (tol {TOL_COM:.0e})")
    print(f"max |dtilt| = {max_dtilt:.3e} deg (tol {TOL_TILT:.0e})")
    ok = (max_dcom < TOL_COM and max_dtilt < TOL_TILT
          and n_ck == len(ref_t))
    print(f"RUN 32 F2-a REGRESSION: {'PASS' if ok else 'FALSIFIER FIRED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
