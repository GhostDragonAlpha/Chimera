"""RUN 33 (STEP-3 FORK-2, F2-b -- PRE-REGISTERED in tools/kernel_walk.py's
docstring): the POLICY TRAINING HARNESS.

Physics: tools/kernel_batch.py's BatchBear (RUN 32 regression PASS --
the verified float64 port), initialized from the gait_dump state
(models/cad_bear/bear_build_gait.npz -- post-prestress, AUDIT-clean).
ML supplies ONLY the 8-dim joint command signal; every force is the
kernel's (gravity, floor wall, bond nets).

Modes:
  sweep   -- the pre-registered OPEN-LOOP SANITY DIAGNOSTIC, run FIRST:
             a fixed ankle_L command (phi_s = +/-cmd_xfer = 0.75 deg,
             RUN 30) held 0.5 s must move the whole-bear com_x with the
             derived sign and scale: +command moves the sole centroid
             -x (Gx = -0.196 m/rad, RUN 11) and the inverted pendulum
             accelerates the com +x (x'' = (g/h_c)|Gx|th; RUN 33
             erratum in kernel_walk.py's docstring). If it does not,
             the port's command path is broken -- stop before training.
  train   -- separable CMA-ES (rank-mu core: per-dimension sigma,
             weighted recombination; no evolution paths -- a documented
             simplification) over a LINEAR policy act = CMD_CLIP *
             tanh(W obs + b), 152 parameters, sigma0 = cmd_xfer
             (0.0131 rad -- the derived transfer command magnitude).
             Episode: H = 2.0 s (the FSM's derived xfer timeout,
             2xT_xfer, RUN 25), zero-order hold at the 50 ms rec2
             cadence. Reward (frozen metrics only):
               r = (BASE_GAP - min_t |com_x - X_R|) / BASE_GAP
             with com_x the whole-bear COM, X_L = 58.0 mm / X_R = 2.0
             mm (RUN 25 transfer geometry), BASE_GAP = 56 mm (the
             zero-command baseline gap); an episode that breaches the
             corridor (trunk tilt > 17.2 deg, the RUN 26 arrest
             measurement) freezes its progress at the breach. Zero
             command scores 0; full transfer scores 1.
             Budget: generations derived from MEASURED throughput,
             capped at the wallclock argument (default 6 h, the
             pre-registered cap). Best policy saved to
             models/cad_bear/policy_run33.npz after every generation.

Usage:
  .venv-gs/Scripts/python.exe -u tools/kernel_policy.py sweep
  .venv-gs/Scripts/python.exe -u tools/kernel_policy.py train [E] [hours]
  .venv-gs/Scripts/python.exe -u tools/kernel_policy.py eval [npz]

RUN 34 (F2-c) ERRATUM (2026-08-22): the reference-harness replay of
policy_run33.npz fell at t=0.58 s (trunk tilt 48 deg > corridor 17.2).
Post-run audit: train() saved m labeled with a SAMPLE's reward -- the
npz 'reward' field is not the saved theta's own score. Fixed: train now
saves the actual best sample; eval mode MEASURES any npz's true reward
through the port episode instead of trusting the label.
"""

import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kernel_batch import BatchBear, BUILD_GAIT, DEV, DTYPE, BODY_NAMES

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "models" / "cad_bear" / "policy_run33.npz"

# ---- frozen, measured constants (see docstring) ----
X_L = 0.0580                       # m, RUN 25 transfer geometry
X_R = 0.0020                       # m
BASE_GAP = abs(X_L - X_R)          # 56 mm zero-command baseline gap
TILT_MAX = float(np.deg2rad(17.2))  # corridor, RUN 26 arrest
CMD_CLIP = float(np.deg2rad(17.0))  # RUN 28 clip
CMD_XFER = float(np.deg2rad(0.75))  # RUN 30 derived transfer command
H = 2.0                            # s, FSM xfer timeout (2xT_xfer)
GX = -0.196                        # m/rad, RUN 11 steering gain (dP_x/dth_z)
H_C = 0.157                        # m, whole-bear COM height (2x W*h=3.86
                                   # at W=24.57 N, gait_dump printout)
N_OBS, N_ACT = 18, 8
N_PAR = N_ACT * N_OBS + N_ACT      # linear policy + bias = 152

_Y = torch.tensor([0.0, 1.0, 0.0], dtype=DTYPE, device=DEV)


def whole_com_x(bear: BatchBear) -> torch.Tensor:
    """(E,) whole-bear COM x, mass-weighted."""
    num = sum(bear.M[n] * bear.com[:, bear.bidx[n], 0] for n in BODY_NAMES)
    return num / sum(bear.M[n] for n in BODY_NAMES)


def trunk_tilt(bear: BatchBear) -> torch.Tensor:
    """(E,) rad, trunk up-vector off vertical."""
    it = bear.bidx["trunk"]
    up = torch.einsum("eij,j->ei", bear.R[:, it], _Y)
    return torch.arccos(torch.clamp(up[:, 1], -1.0, 1.0))


def policy_act(theta: torch.Tensor, obs: torch.Tensor) -> torch.Tensor:
    """theta (E,N_PAR), obs (E,18) -> act (E,8), tanh-clipped."""
    W = theta[:, :N_ACT * N_OBS].view(-1, N_ACT, N_OBS)
    b = theta[:, N_ACT * N_OBS:]
    return CMD_CLIP * torch.tanh(torch.bmm(obs.unsqueeze(1),
                                           W.transpose(1, 2))
                                 .squeeze(1) + b)


def episode(bear: BatchBear, theta: torch.Tensor) -> torch.Tensor:
    """Run one batched episode (E thetas at once). Returns reward (E,)."""
    E = bear.n_env
    steps_ep = int(H / bear.dt)
    nctl = max(1, int(0.05 / bear.dt))
    bear.reset()
    min_gap = torch.full((E,), float("inf"), dtype=DTYPE, device=DEV)
    fallen = torch.zeros(E, dtype=torch.bool, device=DEV)
    act = torch.zeros(E, N_ACT, dtype=DTYPE, device=DEV)
    for k in range(steps_ep):
        if k % nctl == 0:
            new_act = policy_act(theta, bear.obs())
            act = torch.where(fallen.unsqueeze(1), act, new_act)
            gap = (whole_com_x(bear) - X_R).abs()
            min_gap = torch.where(fallen, min_gap,
                                  torch.minimum(min_gap, gap))
            fallen = fallen | (trunk_tilt(bear) > TILT_MAX)
            if bool(fallen.all()):
                break
        bear.step(act)
    return (BASE_GAP - min_gap) / BASE_GAP


def sweep() -> int:
    """The pre-registered open-loop diagnostic (run BEFORE training)."""
    bear = BatchBear(BUILD_GAIT, 3)
    act = torch.zeros(3, N_ACT, dtype=DTYPE, device=DEV)
    act[:, 2] = torch.tensor([-CMD_XFER, 0.0, CMD_XFER],
                             dtype=DTYPE, device=DEV)  # ankle_L phi_s
    steps = int(0.5 / bear.dt)
    nrec = max(1, int(0.1 / bear.dt))
    x0 = whole_com_x(bear).detach().cpu().numpy()
    # Derived expectation (RUN 33 erratum, kernel_walk.py docstring):
    # +phi_s moves the sole centroid -x (Gx < 0); the pendulum inverts
    # it -- x'' = (G/H_C)*|Gx|*th, so +command moves com_x POSITIVE.
    x_acc = (bear.G / H_C) * abs(GX) * CMD_XFER   # m/s^2
    print(f"sweep: ankle_L phi_s = (-0.75, 0, +0.75) deg held 0.5 s  "
          f"com_x0 = {x0[1]*1000:.2f} mm")
    print(f"pendulum-inverted Gx predicts com_x(+0.75 deg) moves +, "
          f"x''={x_acc:.3f} m/s^2 (~{0.5*x_acc*0.25*1000:.0f} mm at 0.5 s "
          f"naive, less as the sole re-seats)")
    for k in range(steps):
        bear.step(act)
        if (k + 1) % nrec == 0:
            x = whole_com_x(bear).detach().cpu().numpy()
            d = (x - x0) * 1000
            print(f"  t={(k+1)*bear.dt:4.2f} s  Dcom_x = ({d[0]:+6.3f}, "
                  f"{d[1]:+6.3f}, {d[2]:+6.3f}) mm  (-, 0, +)")
    x = whole_com_x(bear).detach().cpu().numpy()
    d_pos, d_neg = (x[2] - x0[2]), (x[0] - x0[0])
    # corrected check (RUN 33 erratum): +command -> com_x +, -command
    # -> com_x -, both beyond 1 mm, zero-command drift under 0.1 mm
    ok = (d_pos > 1e-3 and d_neg < -1e-3 and abs(x[1] - x0[1]) < 1e-4)
    verdict = ("OK -- command path verified" if ok else
               "BROKEN -- STOP, repair the port command path")
    print(f"RUN 33 SWEEP: sign/scale {verdict}")
    return 0 if ok else 2


def train(n_env: int, hours: float) -> int:
    lam = n_env
    mu = lam // 2
    w = torch.log(torch.tensor(mu + 0.5, dtype=DTYPE, device=DEV)) \
        - torch.log(torch.arange(1, mu + 1, dtype=DTYPE, device=DEV))
    w = w / w.sum()
    m = torch.zeros(N_PAR, dtype=DTYPE, device=DEV)
    sig = torch.full((N_PAR,), CMD_XFER, dtype=DTYPE, device=DEV)
    c_sig = 0.3
    bear = BatchBear(BUILD_GAIT, lam)
    t0 = time.time()
    budget = hours * 3600.0
    best_r, best_th = -float("inf"), None
    gen = 0
    print(f"train: E=lam={lam}  mu={mu}  n_par={N_PAR}  sigma0={CMD_XFER:.4f} rad "
          f"(cmd_xfer)  H={H}s  budget={hours:.1f} h")
    while True:
        eps = torch.randn(lam, N_PAR, dtype=DTYPE, device=DEV)
        thetas = m.unsqueeze(0) + sig.unsqueeze(0) * eps
        r = episode(bear, thetas)
        order = torch.argsort(r, descending=True)
        r = r[order]
        eps_s = eps[order]
        m = (w.unsqueeze(1) * eps_s[:mu]).sum(0) * sig + m
        sig = sig * torch.exp(
            c_sig * ((w.unsqueeze(1) * eps_s[:mu] ** 2).sum(0) - 1.0) / 2)
        if float(r[0]) > best_r:
            # RUN 34 erratum (2026-08-22): save the ACTUAL best sample
            # -- the old code saved m labeled with a sample's reward.
            best_r = float(r[0])
            best_th = thetas[order[0]].clone()
            np.savez(OUT, theta=best_th.cpu().numpy(), reward=best_r,
                     gen=gen)
        el = time.time() - t0
        print(f"gen {gen:4d}  r best={float(r[0]):+.4f}  "
              f"mu-med={float(r[mu//2]):+.4f}  worst={float(r[-1]):+.4f}  "
              f"sig=({float(sig.min()):.4f},{float(sig.max()):.4f})  "
              f"elapsed={el/60:.1f} min", flush=True)
        gen += 1
        if el > budget:
            break
        if gen == 1:
            # derive the generation count the budget buys (measured)
            est = int(budget // el)
            print(f"measured {el:.0f}s/gen -> budget buys ~{est} "
                  f"generations", flush=True)
    print(f"RUN 33 TRAIN DONE: gens={gen}  best reward={best_r:+.4f}  "
          f"saved -> {OUT}")
    return 0


def evaluate(npz_path: str | None = None) -> int:
    """RUN 34 erratum (2026-08-22): measure a SAVED theta's true reward
    through the port episode -- E=1 deterministic replay. The npz
    'reward' field must be verified, not trusted."""
    p = Path(npz_path) if npz_path else OUT
    d = np.load(p)
    th = torch.as_tensor(d["theta"], dtype=DTYPE, device=DEV).unsqueeze(0)
    bear = BatchBear(BUILD_GAIT, 1)
    r = episode(bear, th)
    gap = BASE_GAP * (1.0 - float(r[0]))
    print(f"eval {p.name}: measured reward={float(r[0]):+.4f} "
          f"(frozen min gap {gap * 1000:.2f} mm) vs npz label "
          f"{float(d['reward']):+.4f} (gen {int(d['gen'])})")
    ok = abs(float(r[0]) - float(d["reward"])) < 1e-4
    print("RUN 34 EVAL:", "label verified"
          if ok else "LABEL MISMATCH -- npz reward does not belong to its theta")
    return 0 if ok else 2


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "sweep"
    if mode == "sweep":
        return sweep()
    if mode == "train":
        n_env = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        hours = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
        return train(n_env, hours)
    if mode == "eval":
        return evaluate(sys.argv[2] if len(sys.argv) > 2 else None)
    print(f"unknown mode {mode!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
