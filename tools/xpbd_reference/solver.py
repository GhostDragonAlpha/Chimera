"""The solvers under test.

xpbd_tick  — THE preregistered coupled solve (PREREG.md source-of-truth 2,
             DESIGN.md section 0, verbatim in shape):

    loop n = n_sub substeps (h_sub = h/n):
        predict (x += h_sub*v, external forces as h_sub^2 impulses)
        reset lambdas
        loop iterations:
            stack the constraints: [volume | joint | servo | contact]
            solve (J M^-1 J^T + Lambda/h_sub^2) dlambda
                    = -C - (Lambda/h_sub^2) lambda
            apply; REFRESH the nonlinear Jacobians (every iteration here)
        x += J^T lambda_total                 (accumulated position correction)
        v += M^-1 J^T lambda_total / h_sub    (CONSISTENT velocity update)

    Pressure recovery: at convergence the regularized solve leaves
    C + (alpha/h_sub^2) lambda = 0, so for the volume rows
    P = lambda/h_sub^2 = -dV/(kappa V0) — the engine's own law, Astra's
    sign convention (positive when compressed). This identity IS prereg
    bar P1; pressure_check measures it.

explicit_tick_ring — the EXPLICIT baseline (the current architecture's
             idealization): water generalized forces F = J^T P evaluated
             from the CURRENT volumes, semi-implicit Euler, no coupled
             solve. The prereg measures THIS update's divergence at
             eta = h*omega_max = 6.497 (> 2 diverges).
"""
import numpy as np

from . import measured as M

DIVERGE_RATIO = 1.0e3     # divergence criterion for falsifier (b), stated


class SolveReport:
    """Per-tick witness numbers — the /xpbd_state fields the appliance carries."""

    def __init__(self):
        self.iterations = 0        # total constraint iterations this tick
        self.substeps = 0
        self.pressure = None       # per-cell P = lambda/h_sub^2, last substep
        self.residual = 0.0        # |C| inf-norm at the final refresh


def volume_rows(sys):
    """The volume constraint object of a system (there is exactly one)."""
    for r in sys.rows:
        if r.name.startswith("volume"):
            return r
    raise RuntimeError("no volume rows in system")


def volume_deviations(sys):
    """Actual dV_i at the current q — the constraint's own evaluation."""
    return np.atleast_1d(volume_rows(sys).evaluate(sys.q)[0])


def amplitude(sys):
    """Boundedness metric: worst cell's relative volume deviation."""
    dV = volume_deviations(sys)
    return float(np.max(np.abs(dV) / M.V0[: len(dV)]))


def ring_force(sys):
    """The explicit water generalized force J^T P at the current state
    (P = -dV/(kappa V0), the engine's own law, evaluated explicitly)."""
    C, J, _ = volume_rows(sys).evaluate(sys.q)
    dV = np.atleast_1d(C)
    P = -dV / (M.KAPPA * M.V0[: len(dV)])
    return J.T @ P


def xpbd_substep(sys, h_s, tol=1e-12, max_iters=200):
    """One coupled-solve substep at step h_s: predict, reset lambdas, iterate
    the regularized solve with nonlinear-Jacobian refresh, correct positions,
    consistent velocity update. Returns (lambda, iterations, |C| residual)."""
    Minv = 1.0 / sys.w
    sys.q += h_s * sys.v + h_s * h_s * sys.external / sys.w   # predict
    lam = np.zeros(len(sys.stack()[0]))                       # reset lambdas
    iters = 0
    for _it in range(max_iters):
        C, J, alpha = sys.stack()                             # NONLINEAR refresh
        reg = alpha / h_s**2
        r = C + reg * lam
        # Convergence is tested on the REGULARIZED residual r = C + (alpha/
        # h_s^2) * lambda — the solve's OWN equation. A compliant constraint's
        # converged state carries raw C = -(alpha/h_s^2) * lambda != 0 (the
        # compliance IS the point), so a raw-C tolerance sized for rigid rows
        # can never pass under load: the loop burned the cap on idempotent
        # solves (measured: 800 iterations/tick, 240 ms/tick, before this
        # test was fixed). r is quadratic under Newton and exact after one
        # iteration for linear rows; the scale term makes the test relative
        # across the stacked rows' mixed units (m^3 | m | rad).
        if np.max(np.abs(r)) <= tol * (1.0 + np.max(np.abs(C))
                                       + np.max(np.abs(reg * lam))):
            break
        A_sys = (J * Minv) @ J.T + np.diag(reg)
        dlam = np.linalg.solve(A_sys, -r)
        lam += dlam
        # position correction, the PBD rule: dx = M^-1 J^T dlambda
        # (the M^-1 weight is what makes the solve's Newton denominator
        #  J M^-1 J^T the TRUE curvature of C under dx — an unweighted
        #  J^T overshoots by the mass ratio and diverges)
        sys.q += Minv * (J.T @ dlam)
        iters += 1
    C, J, alpha = sys.stack()                                 # final refresh
    sys.v += Minv * (J.T @ lam) / h_s                         # CONSISTENT update
    return lam, iters, float(np.max(np.abs(C)))


def xpbd_tick(sys, h=M.H_TICK, n_sub=M.N_STABILITY, tol=1e-12, max_iters=200):
    """One engine tick through the coupled XPBD solve. Returns SolveReport."""
    rep = SolveReport()
    h_s = h / n_sub
    lam, iters, residual = None, 0, 0.0
    for _ in range(n_sub):
        lam, it, residual = xpbd_substep(sys, h_s, tol, max_iters)
        rep.substeps += 1
        rep.iterations += it
    rep.residual = residual
    rep.pressure = lam[:_n_volume_rows(sys)] / h_s**2
    return rep


def _n_volume_rows(sys):
    return len(np.atleast_1d(volume_rows(sys).evaluate(sys.q)[0]))


def pressure_check(sys, report):
    """P1 instrument: recovered pressure P = lambda/h_sub^2 vs the engine's
    own law P = -dV/(kappa V0) from the ACTUAL post-solve volumes.
    Returns (P_lambda, P_law, miss_percent) per cell."""
    dV = volume_deviations(sys)
    P_lam = np.atleast_1d(report.pressure)
    P_law = -dV / (M.KAPPA * M.V0[: len(dV)])
    denom = np.maximum(np.abs(P_law), 1e-9)
    miss = 100.0 * np.abs(P_lam - P_law) / denom
    return P_lam, P_law, miss


def explicit_tick_ring(sys, h=M.H_TICK):
    """Explicit baseline for particle systems: F = J^T P from current
    volumes, symplectic Euler (v, then x)."""
    F = ring_force(sys) + sys.external
    sys.v += h * F / sys.w
    sys.q += h * sys.v
    return sys.q.copy()


# ---------------------------------------------------------------------------
def divergence_probe(sys, h, n_sub, family, press_dofs, press_force,
                     press_ticks=3, max_ticks=60):
    """Falsifier (b) / P2's probe: a step press at `press_dofs` (generalized
    indices) for `press_ticks` ticks, then release; up to max_ticks.

    family 'explicit': symplectic Euler at h/n per substep (n=1 -> the
    single-step explicit update the prereg indicts).
    family 'xpbd': the coupled solve at n substeps.

    Divergence: amplitude (worst |dV|/V0) exceeds DIVERGE_RATIO x the
    press-on amplitude, or goes non-finite. Returns (trace, diverged_at).
    """
    q0, v0 = sys.copy_state()
    trace, diverged_at, amp_press = [], None, None
    for t in range(max_ticks):
        pressing = t < press_ticks
        if family == "explicit":
            for _ in range(n_sub):
                F = ring_force(sys)
                if pressing:
                    F = F + _press_vector(sys, press_dofs, press_force)
                sys.v += (h / n_sub) * F / sys.w
                sys.q += (h / n_sub) * sys.v
        elif family == "xpbd":
            sys.external = _press_vector(sys, press_dofs, press_force) \
                if pressing else np.zeros(sys.ndof)
            xpbd_tick(sys, h=h, n_sub=n_sub)
        else:
            raise ValueError(family)
        amp = amplitude(sys)
        trace.append(float(amp) if np.isfinite(amp) else float("inf"))
        if amp_press is None and t >= press_ticks - 1:
            amp_press = max(trace[-1], 1e-300)
        if amp_press is not None and (not np.isfinite(amp)
                                      or amp > DIVERGE_RATIO * amp_press):
            diverged_at = t + 1
            break
    sys.set_state(q0, v0)
    return trace, diverged_at


def _press_vector(sys, dofs, force):
    f = np.zeros(sys.ndof)
    f[np.asarray(dofs, int)] = force
    return f


def run_free(sys, ticks, n_sub, signal, h=M.H_TICK):
    """Free-run the coupled solve for `ticks` ticks at n_sub substeps,
    recording `signal(sys)` after EVERY SUBSTEP (dt = h/n_sub).

    Per-substep sampling is not a style choice: the solver's own time grid is
    the substep, and the stiff modes (up to 310 Hz coupled) ALIAS against the
    300 Hz tick grid — a tick-sampled trace reads the hip cell at its alias,
    not its frequency. Returns (trace, h/n_sub).
    """
    h_s = h / n_sub
    trace = np.empty(ticks * n_sub)
    k = 0
    for _ in range(ticks):
        for _s in range(n_sub):
            xpbd_substep(sys, h_s)
            trace[k] = signal(sys)
            k += 1
    return trace, h_s


def frequency_probe(sys_builder, excite, signal, n_sub, ticks=2048, h=M.H_TICK):
    """Falsifier (a) / P3's instrument: build a fresh system, seed velocities
    with `excite(sys)` (a fixed, momentum-free impulse), free-run the coupled
    solve at n_sub substeps, FFT the per-substep trace. Returns the dominant
    omega in rad/s."""
    sys = sys_builder()
    excite(sys)
    trace, h_s = run_free(sys, ticks, n_sub, signal, h)
    return spectral_peak(trace, h_s), trace


def _energy_window(signal, min_len=64, margin=30.0):
    """Trim a decaying trace where it still carries SIGNAL, not solver
    jitter: estimate the noise floor from the tail median and cut at the
    last sample above margin x floor. Without this, a frequency fit locks
    onto the tolerance jitter's cadence (it reads as the sampling Nyquist)."""
    x = np.asarray(signal, float)
    if len(x) < 16:
        return x
    tail = x[-max(1, len(x) // 10):]
    noise = float(np.median(np.abs(tail))) + 1e-300
    thresh = max(margin * noise, 1e-12 * float(np.max(np.abs(x))))
    alive = np.nonzero(np.abs(x) > thresh)[0]
    last = int(alive[-1]) + 1 if len(alive) else len(x)
    return x[:max(last, min(min_len, len(x)))]


def _fft_lobes(x, dt):
    """Hann-windowed FFT of a mean-removed trace -> (spec, freqs)."""
    x = x - np.mean(x)
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    return spec, np.fft.rfftfreq(len(x), dt)


def _interp_peak(spec, freqs, k):
    """Parabolic interpolation of the lobe at bin k, interpolation weight
    clamped to +-0.5 bins (an unclamped ratio explodes on noise-floor bins
    and invents frequencies above Nyquist)."""
    if 0 < k < len(spec) - 1:
        y0, y1, y2 = spec[k - 1], spec[k], spec[k + 1]
        dk = 0.5 * (y0 - y2) / (y0 - 2.0 * y1 + y2 + 1e-300)
        dk = float(np.clip(dk, -0.5, 0.5))
        f = freqs[k] + dk * (freqs[1] - freqs[0])
    else:
        f = freqs[k]
    return float(2.0 * np.pi * abs(f))


def spectral_peak(signal, dt):
    """Dominant angular frequency of a decaying single-mode trace:
    energy-window, then an AR(2) fit z_{k+1} = c z_k - d z_{k-1} over the
    alive samples (exact for one damped mode, robust where an FFT of a
    30-sample burst is not). Returns rad/s."""
    x = _energy_window(signal)
    c, d = _ar2_fit(x)
    theta = np.arccos(np.clip(c / (2.0 * np.sqrt(max(d, 1e-300))), -1.0, 1.0))
    return float(theta / dt)


def _ar2_fit(x):
    """Least-squares AR(2) coefficients of the interior of the trace:
    fits x[k+2] = c x[k+1] - d x[k]."""
    z0, z1 = x[:-2], x[1:-1]          # x[k], x[k+1]
    z2 = x[2:]                        # x[k+2]
    A = np.column_stack([z1, -z0])
    (c, d), *_ = np.linalg.lstsq(A, z2, rcond=None)
    return float(c), float(d)


def spectrum_peaks(signal, dt, n_peaks):
    """Top-n distinct spectral peaks (rad/s), descending in frequency.
    Used by the coupled-ring probe to resolve all three ring modes."""
    x = _energy_window(signal)
    spec, freqs = _fft_lobes(x, dt)
    order = np.argsort(spec)[::-1]
    peaks, taken = [], np.zeros(len(spec), bool)
    for k in order:
        if k == 0 or taken[k]:
            continue
        if any(abs(k - kk) <= 6 for kk, _ in peaks):   # same lobe
            continue
        peaks.append((k, spec[k]))
        taken[max(0, k - 6):k + 7] = True
        if len(peaks) == n_peaks:
            break
    return sorted((_interp_peak(spec, freqs, k) for k, _ in peaks),
                  reverse=True)
