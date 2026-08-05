"""synergy.py — THE SYNERGY DECODER.

THEORY (stated so it can fail):
  STATEMENT  The stand policy maps a 5-D observation {z, pitch, roll, com_x, com_y}
              through a linear-per-muscle formula (a0 + kh*(tgt-z) + kp*pitch + kr*roll
              + kx*com_x + ky*com_y) into 290 muscle activations, and that 290-D
              activation vector lives on a ~16-dimensional manifold extracted by ICA-PCA.
  PREDICTION  Adding CoM BoS feedback (kx, ky) increases held-out survival median by
              >=30% relative to P-only, by giving the policy direct access to the
              base-of-support margins that determine lateral stability.
  FALSIFIER   If CoM gains train to near-zero, or survival does not improve, the
              BoS feedback hypothesis is dead.

WHAT THIS FILE HOLDS
  The decoder that bridges the trained theta (output/ports/stand_theta.npy) and
  the MuJoCo simulation (ChimeraEngine render loop). It is NOT the parser
  (tools/parser.py) — the parser is the button-layer contract. This is the
  physics-layer contract: it reads muJoCo state, assembles observations
  {z, ż, pitch, pitcḣ, roll, roll̇, com_x, com_y}, and applies the policy
  formula to produce 290 muscle activations.

  A 4-block theta is bit-identical to the parser's stand_formula_fn (backward
  compatible). A 6-block theta adds CoM BoS gains — kx, ky.
  A 7-block theta adds velocity gains — kdz, kdp, kdr.
  A 9-block theta adds both — velocity + CoM feedback.

THE POLICY:
  P-only (4 blocks):  u = clip(a0 + kh*(tgt-z) + kp*pitch + kr*roll, 0, 1)
  P+CoM (6 blocks):   u = clip(a0 + kh*(tgt-z) + kp*pitch + kr*roll
                              + kx*com_x + ky*com_y, 0, 1)
  PD     (7 blocks):  u = clip(a0 + kh*(tgt-z) + kdz*ż + kp*pitch + kdp*pitcḣ
                              + kr*roll + kdr*roll̇, 0, 1)
  PD+CoM (9 blocks):  u = clip(a0 + kh*(tgt-z) + kdz*ż + kp*pitch + kdp*pitcḣ
                              + kr*roll + kdr*roll̇ + kx*com_x + ky*com_y, 0, 1)
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_PORTS = _ROOT / "ChimeraEngine" / "output" / "ports"
_SYNFILE = _ROOT / "ChimeraEngine" / "myobody_synergies.npz"
# control cadence: 20 MuJoCo timesteps = 0.02 s at 50 Hz
CTRL_EVERY = 20
# default MuJoCo timestep; may be overridden by the model
_DT_DEFAULT = 0.001


class SynergyDecoder:
    """Decode observations to 290 muscle activations through the trained theta.

    The decoder holds the theta as flat blocks of `nu` muscles each. The number
    of blocks determines which formula applies:

      4 blocks (a0|kh|kp|kr)       → P-only, backward-compatible with parser
      6 blocks (a0|kh|kp|kr|kx|ky) → P-only + CoM BoS feedback
      7 blocks (a0|kh|kdz|kp|kdp|kr|kdr) → PD with velocity feedback
      9 blocks (a0|kh|kdz|kp|kdp|kr|kdr|kx|ky) → PD + CoM BoS feedback

    The synergy basis (ICA-PCA) is optional: it is loaded for analysis and
    projection, but the policy output is always 290-D (the full muscle space).
    """

    def __init__(self, theta_path=None, synergy_path=None, tgt=None, nu=None):
        self.theta_path = Path(theta_path) if theta_path else _PORTS / "stand_theta.npy"
        self.synergy_path = Path(synergy_path) if synergy_path else _SYNFILE
        self.theta = np.load(self.theta_path)
        if self.theta.ndim != 1:
            raise ValueError(f"theta must be 1-D, got shape {self.theta.shape}")
        if nu is not None:
            self.nu = int(nu)
        else:
            self.nu = self.theta.size if self.theta.size < 700 else 290
        if self.theta.size % self.nu != 0:
            raise ValueError(
                f"theta size {self.theta.size} is not a multiple of nu={self.nu}")
        self.blocks = self.theta.size // self.nu
        self._validate_blocks()
        self._load_blocks()
        self.tgt = float(tgt) if tgt is not None else self._derive_target()
        self._load_basis()

    def _validate_blocks(self):
        if self.blocks in (4, 6, 7, 9):
            return  # valid layouts
        if self.blocks == 5:
            return  # P-only + load (legacy)
        raise ValueError(
            f"theta has {self.blocks} blocks of {self.nu}; "
            f"expected 4 (P-only), 6 (P+CoM), 7 (PD), or 9 (PD+CoM).")

    def _load_blocks(self):
        nu = self.nu
        th = self.theta
        if self.blocks == 9:
            # PD+CoM layout: a0 | kh | kdz | kp | kdp | kr | kdr | kx | ky
            self.a0  = th[0*nu:1*nu]
            self.kh  = th[1*nu:2*nu]
            self.kdz = th[2*nu:3*nu]
            self.kp  = th[3*nu:4*nu]
            self.kdp = th[4*nu:5*nu]
            self.kr  = th[5*nu:6*nu]
            self.kdr = th[6*nu:7*nu]
            self.kx  = th[7*nu:8*nu]
            self.ky  = th[8*nu:9*nu]
            self.kw = np.zeros(nu)
        elif self.blocks == 7:
            # PD layout: a0 | kh | kdz | kp | kdp | kr | kdr
            self.a0  = th[0*nu:1*nu]
            self.kh  = th[1*nu:2*nu]
            self.kdz = th[2*nu:3*nu]
            self.kp  = th[3*nu:4*nu]
            self.kdp = th[4*nu:5*nu]
            self.kr  = th[5*nu:6*nu]
            self.kdr = th[6*nu:7*nu]
            self.kx = self.ky = None
            self.kw = np.zeros(nu)
        elif self.blocks == 6:
            # P+CoM layout: a0 | kh | kp | kr | kx | ky
            self.a0  = th[0*nu:1*nu]
            self.kh  = th[1*nu:2*nu]
            self.kp  = th[2*nu:3*nu]
            self.kr  = th[3*nu:4*nu]
            self.kx  = th[4*nu:5*nu]
            self.ky  = th[5*nu:6*nu]
            self.kdz = self.kdp = self.kdr = None
            self.kw = np.zeros(nu)
        else:
            # P-only layout: a0 | kh | kp | kr [| kw]
            self.a0  = th[0*nu:1*nu]
            self.kh  = th[1*nu:2*nu]
            self.kp  = th[2*nu:3*nu]
            self.kr  = th[3*nu:4*nu] if th.size >= 4*nu else np.zeros(nu)
            self.kw  = th[4*nu:5*nu] if th.size >= 5*nu else np.zeros(nu)
            self.kdz = self.kdp = self.kdr = None
            self.kx = self.ky = None

    def _derive_target(self):
        """Read the derived pelvis target from the stand port if available."""
        try:
            import sys
            _tools = _ROOT / "tools"
            sys.path.insert(0, str(_tools))
            from stand_port import derive_stand_port
            P = derive_stand_port()
            return float(P["OUT pelvis_target_m"])
        except Exception:
            return 0.9201465  # measured from agent_logs/stand_survival_stand_theta.json

    def _load_basis(self):
        """Load the ICA-PCA synergy basis for analysis."""
        if self.synergy_path.exists():
            z = np.load(self.synergy_path, allow_pickle=True)
            self.mean = z["mean"] if "mean" in z else np.zeros(self.nu)
            self.synergies = z["synergies"] if "synergies" in z else np.eye(self.nu)
            self.scale = z["scale"] if "scale" in z else np.ones(self.synergies.shape[0])
            self.explained = z["explained"] if "explained" in z else None
            self.dims = z["dims"] if "dims" in z else None
        else:
            self.mean = np.zeros(self.nu)
            self.synergies = np.eye(self.nu)
            self.scale = np.ones(1)
            self.explained = None
            self.dims = None

    # ── observation building ─────────────────────────────────────────────────

    @staticmethod
    def obs_from_mujoco(d, m, tgt, dt=None, prev=None):
        """Build the observation dict from MuJoCo state.

        Returns (obs_dict, prev_state) where prev_state carries z/pitch/roll
        for the next call's finite-difference velocity.

        `m` is the MuJoCo MjModel (not the mujoco module); `dt` defaults to
        CTRL_EVERY * m.opt.timestep.
        """
        if dt is None:
            dt = CTRL_EVERY * float(m.opt.timestep)
        z = float(d.qpos[2])
        q = d.qpos[3:7]
        pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                  1 - 2 * (q[1]**2 + q[2]**2)))
        roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                 1 - 2 * (q[1]**2 + q[2]**2)))
        # THE FOOT CENTRE IS THE FOOT POLYGON, NOT THE HEELS -- measured 2026-08-02: against
        # heels alone the CoM reads ~15 cm forward and OUTSIDE the base; against heels AND toes
        # it is comfortably inside. com_x/com_y are the CoM offset from that polygon centre,
        # the base-of-support margins that determine lateral stability.
        com = d.subtree_com[0]
        foot = 0.25 * (d.xpos[m.body("calcn_r").id] + d.xpos[m.body("calcn_l").id]
                       + d.xpos[m.body("toes_r").id] + d.xpos[m.body("toes_l").id])
        obs = {"z": z, "pitch": pitch, "roll": roll, "tgt": tgt,
               "com_x": float(com[0] - foot[0]), "com_y": float(com[1] - foot[1])}
        if prev is not None:
            obs["z_dot"] = (z - prev["z"]) / dt
            obs["pitch_dot"] = (pitch - prev["pitch"]) / dt
            obs["roll_dot"] = (roll - prev["roll"]) / dt
        else:
            obs["z_dot"] = 0.0
            obs["pitch_dot"] = 0.0
            obs["roll_dot"] = 0.0
        return obs, {"z": z, "pitch": pitch, "roll": roll}

    # ── decoding ─────────────────────────────────────────────────────────────

    def decode(self, obs):
        """Map an observation dict to 290 muscle activations.

        obs keys: z, pitch, roll, com_x, com_y, (z_dot, pitch_dot, roll_dot) — all floats.
        The observation is the body's state relative to the stand target.
        The target (tgt - z) is the height error; pitch/roll are lean angles; com_x/com_y
        are the CoM offset from the foot-polygon centre. 6-block and 9-block thetas REQUIRE
        com_x/com_y in obs and raise if absent, so a CoM theta cannot run blind.
        """
        z = float(obs["z"]); pitch = float(obs["pitch"]); roll = float(obs["roll"])
        z_err = self.tgt - z
        u = self.a0 + self.kh * z_err + self.kp * pitch + self.kr * roll
        if self.blocks in (7, 9):
            zd = float(obs["z_dot"])
            pd = float(obs["pitch_dot"])
            rd = float(obs["roll_dot"])
            u = u + self.kdz * zd + self.kdp * pd + self.kdr * rd
        if self.blocks in (6, 9):
            u = u + self.kx * float(obs["com_x"]) + self.ky * float(obs["com_y"])
        return np.clip(u, 0.0, 1.0)

    def decode_with_basis(self, obs):
        """Decode, then project the result through the synergy basis.

        Returns (u_290, c_16) where c is the 16-D synergy coefficient vector.
        This is for analysis: it shows how much of the activation lives on
        each extracted synergy mode.
        """
        u = self.decode(obs)
        c = self.project_activations(u)
        return u, c

    def project_activations(self, u):
        """Project a 290-D activation vector onto the synergy basis.

        c = synergies @ (u - mean)   →  16-D coefficients
        """
        centered = u - self.mean
        if self.scale.size > 1:
            c = (self.synergies * self.scale[:, None]) @ centered
        else:
            c = self.synergies @ centered
        return c

    def reconstruct_from_synergy(self, c):
        """Reconstruct 290-D activations from 16-D synergy coefficients.

        u = mean + synergies.T @ (c / scale)
        """
        if self.scale.size > 1:
            c_norm = c / self.scale
        else:
            c_norm = c
        return self.mean + self.synergies.T @ c_norm

    # ── diagnostics ──────────────────────────────────────────────────────────

    def synergy_report(self, u):
        """Report how the activation distributes across the synergy basis."""
        c = self.project_activations(u)
        var = c**2
        total = float(var.sum()) + 1e-12
        frac = var / total
        order = np.argsort(-frac)
        return {
            "explained": self.explained,
            "dims": self.dims,
            "coeffs": c,
            "variance_frac": frac,
            "top_index": int(order[0]),
            "top_frac": float(frac[order[0]]),
            "cumulative_8": float(frac[order[:8]].sum()),
        }


def load_theta(path=None):
    """Convenience: load a theta and report its shape."""
    p = Path(path) if path else _PORTS / "stand_theta.npy"
    th = np.load(p)
    nu = 290
    blocks = th.size // nu
    return th, nu, blocks


if __name__ == "__main__":
    import sys
    th, nu, blocks = load_theta(sys.argv[1] if len(sys.argv) > 1 else None)
    names = ["a0", "kh", "kp", "kr", "kw", "kdz", "kdp", "kr", "kdr"]
    print(f"theta: {th.size} numbers = {blocks} blocks x {nu} muscles")
    if blocks == 4:
        print("  formula: a0 + kh*(tgt-z) + kp*pitch + kr*roll  [P-only]")
    elif blocks == 6:
        print("  formula: a0 + kh*(tgt-z) + kp*pitch + kr*roll + kx*com_x + ky*com_y  [P+CoM]")
    elif blocks == 7:
        print("  formula: a0 + kh*(tgt-z) + kdz*ż + kp*pitch + kdp*θ̇ + kr*roll + kdr*ṙ  [PD]")
    elif blocks == 9:
        print("  formula: a0 + kh*(tgt-z) + kdz*ż + kp*pitch + kdp*θ̇ + kr*roll + kdr*ṙ"
              " + kx*com_x + ky*com_y  [PD+CoM]")
    dec = SynergyDecoder()
    print(f"  target: {dec.tgt:.4f} m")
    if dec.synergies.shape[0] < dec.nu:
        print(f"  synergy basis: {dec.synergies.shape[0]} modes (reduced from {dec.nu}-D)")
        report = dec.synergy_report(dec.theta[:nu])
        print(f"  top synergy: {report['top_index']} ({report['top_frac']:.1%})")
        print(f"  cumulative 8: {report['cumulative_8']:.1%} variance explained")
