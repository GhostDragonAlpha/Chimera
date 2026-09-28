"""MAT2-M04 passive response evaluator: rest/current geometry + material
history -> stress/force + updated history + stored/dissipated energy.

Implements EXACTLY the three frozen passive profiles of the preregistration
(PREREGISTRATION.md, this directory):

- rigid:                x = 0 for any load; transmits F_out = F_in bitwise;
                        U = Q = 0; no strain state exists.
- compliant_maxwell:    Hooke spring k = E*A/L0 in SERIES with a linear
                        dashpot c (tau = c/k). Exact exponential per-tick
                        integrator (no Euler drift):
                          dF/dt = k*v - F/tau   (position rate v)
                          F(t+dt) = e^(-dt/tau)*F + c*v*(1 - e^(-dt/tau))
                        Exact within-tick integrals:
                          int F dt   = b*dt + (a-b)*tau*(1 - alpha)
                          int F^2 dt = b^2*dt + 2*b*(a-b)*tau*(1-alpha)
                                       + (a-b)^2*(tau/2)*(1 - alpha^2)
                        with alpha = e^(-dt/tau), a = F_start, b = c*v.
- fiber_reinforced:     E(theta) = E_trans + (E_fiber - E_trans)*cos^2(theta),
                        elastic x = F*L0/(A*E(theta)).

Force-ramp protocol (protocol V) uses the exact within-tick ramp integrals
for F(tau) = r*(t_n + tau):
  Phi          = r*(t_n*dt + dt^2/2)             (= int F dtau)
  int F^2 dtau = r^2*(t_n^2*dt + t_n*dt^2 + dt^3/3)
  W_tick       = (r/k)*Phi + (1/c)*int F^2 dtau
  Q_tick       = (1/c)*int F^2 dtau;  U = F(t+dt)^2/(2k)

Density NEVER enters any stiffness/force/energy computation: the response
API takes declared parameters only (probe P8 enforces bitwise density
invariance; falsifier bite F1 proves a density-coupled tamper is caught).

The strain gate refuses `outside_valid_strain_range` BEFORE any state update.
The ledger refuses `unexplained_energy` when W != U + Q beyond tolerance or
when U/Q go negative. Area-scaled interface shares refuse zero/negative area.

CPU-only, stdlib-only, deterministic (no RNG, no wall-clock).
"""
from __future__ import annotations

import math

PROFILES = ('rigid', 'compliant_maxwell', 'fiber_reinforced')
LEDGER_TOL = 1e-9


def require(ok, code):
    if not ok:
        raise ValueError(code)


def effective_modulus(E_fiber, E_trans, theta_rad):
    """Frozen anisotropy law: E(theta) = E_trans + (E_fiber-E_trans)*cos^2."""
    c = math.cos(theta_rad)
    return E_trans + (E_fiber - E_trans) * c * c


def angle_between(axis_a, axis_b):
    """Angle (rad) between two vectors, in [0, pi]."""
    dot = (axis_a[0] * axis_b[0] + axis_a[1] * axis_b[1]
           + axis_a[2] * axis_b[2])
    dot = max(-1.0, min(1.0, dot))
    return math.acos(dot)


def _check_strain(x, rest_length_m, band):
    eps = x / rest_length_m
    require(band[0] <= eps <= band[1], 'outside_valid_strain_range')
    return eps


def extension_from_law(law_row, gauge_row, direction_row, load_N):
    """Document-driven quasi-static elastic extension for one assignment.

    law_row: profiles[] row from the passive_law document (parameters dict).
    gauge_row: gauges[] row (axis, rest_length_m, area_m2).
    direction_row: directions[] row or None (fiber axis).
    Returns (extension_m, stiffness_N_per_m or None for rigid).
    Refusals are named; the strain gate fires BEFORE any state is produced.
    """
    require(math.isfinite(load_N), 'nonfinite_load')
    profile = law_row['id']
    require(profile in PROFILES, 'unknown_profile:' + profile)
    band = law_row['valid_strain_range']
    require(band[0] <= 0.0 <= band[1], 'invalid_strain_band')
    L0 = gauge_row['rest_length_m']
    A = gauge_row['area_m2']
    require(L0 > 0.0 and A > 0.0, 'invalid_gauge')
    params = law_row['parameters']

    if profile == 'rigid':
        return 0.0, None
    if profile == 'compliant_maxwell':
        E = params['E_Pa']
        require(E > 0.0, 'invalid_modulus')
        k = E * A / L0
        x = load_N / k
        _check_strain(x, L0, band)
        return x, k
    if profile == 'fiber_reinforced':
        Ef = params['E_fiber_Pa']
        Et = params['E_trans_Pa']
        require(Ef > 0.0 and Et > 0.0, 'invalid_modulus')
        require(direction_row is not None,
                'fiber_profile_requires_direction')
        theta = angle_between(direction_row['axis'], gauge_row['axis'])
        E = effective_modulus(Ef, Et, theta)
        k = E * A / L0
        x = (load_N * L0) / (A * E)
        _check_strain(x, L0, band)
        return x, k
    raise ValueError('unknown_profile:' + profile)


def transmit_force_rigid(load_N):
    """Rigid profile transmits the applied load exactly (bitwise)."""
    require(math.isfinite(load_N), 'nonfinite_load')
    return load_N


def refuse_rigid_strain(extension_m):
    """Any nonzero extension claim on the rigid profile is a refusal."""
    require(extension_m == 0.0, 'rigid_has_no_strain')
    return 0.0


# ---------------------------------------------------------------- Maxwell
def maxwell_force_update(F_prev, dx_dt, dt, k, c):
    """Exact exponential update of the Maxwell element over one tick.

    dF/dt = k*dx_dt - F/tau, tau = c/k.
    F_next = e^(-dt/tau)*F_prev + c*dx_dt*(1 - e^(-dt/tau)).
    """
    require(dt > 0.0, 'invalid_dt')
    require(math.isfinite(F_prev) and math.isfinite(dx_dt), 'nonfinite_state')
    tau = c / k
    alpha = math.exp(-dt / tau)
    return alpha * F_prev + c * dx_dt * (1.0 - alpha)


def maxwell_tick_integrals(F_prev, dx_dt, dt, k, c):
    """Exact within-tick integrals for the exponential force shape.

    Returns (int F dt, int F^2 dt) used for work and dissipation.
    """
    require(dt > 0.0, 'invalid_dt')
    tau = c / k
    alpha = math.exp(-dt / tau)
    a, b = F_prev, c * dx_dt
    int_F_dt = b * dt + (a - b) * tau * (1.0 - alpha)
    d = a - b
    int_F2_dt = b * b * dt + 2.0 * b * d * tau * (1.0 - alpha) \
        + d * d * (tau / 2.0) * (1.0 - alpha * alpha)
    return int_F_dt, int_F2_dt


def maxwell_relaxation_closed_form(F_ramp, hold_s, k, c):
    """Closed form used by the E2 oracle: F(hold) = F_ramp * e^(-hold/tau)."""
    tau = c / k
    return F_ramp * math.exp(-hold_s / tau)


def maxwell_creep_closed_form(F, t, k, c):
    """Closed form: extension of a Maxwell element under constant load F.

    x(t) = F/k (spring, instant) + F*t/c (dashpot creep).
    """
    require(math.isfinite(F) and t >= 0.0, 'nonfinite_creep_input')
    return F / k + F * t / c


def stored_energy(F, k):
    """Spring only: U = F^2 / (2k); the dashpot stores nothing."""
    require(math.isfinite(F), 'nonfinite_force')
    u = F * F / (2.0 * k)
    require(u >= 0.0, 'negative_stored_energy')
    return u


def check_ledger(W, U, Q, tol_rel=LEDGER_TOL):
    """Unaccounted-energy refusal: W == U + Q within tolerance; U, Q >= 0."""
    require(math.isfinite(W) and math.isfinite(U) and math.isfinite(Q),
            'nonfinite_ledger')
    require(U >= 0.0, 'negative_stored_energy')
    require(Q >= 0.0, 'unexplained_energy:negative_dissipation')
    residual = abs(W - (U + Q))
    require(residual <= tol_rel * max(abs(W), 1e-300),
            'unexplained_energy:residual_%r' % residual)
    return {'W_J': W, 'U_J': U, 'Q_J': Q, 'residual_J': residual,
            'tolerance_relative': tol_rel}


# ------------------------------------------------- area-scaled interface
def triangle_force_shares(areas_m2, total_load_N):
    """F_i = F_total * A_i / sum(A); refuses zero/negative area inputs.

    The declared distribution law of the preregistration; the summed load is
    checked within 1e-12 relative and its bitwise exactness is recorded
    (observed, never forced).
    """
    require(isinstance(areas_m2, list) and len(areas_m2) >= 1,
            'empty_interface')
    total_area = 0.0
    for a in areas_m2:
        require(math.isfinite(a) and a > 0.0, 'zero_area_interface')
        total_area += a
    require(total_area > 0.0, 'zero_area_interface')
    shares = [total_load_N * a / total_area for a in areas_m2]
    summed = math.fsum(shares)
    require(abs(summed - total_load_N) <= 1e-12 * abs(total_load_N),
            'interface_share_sum_drift')
    return {'shares_N': shares, 'summed_N': summed,
            'sum_bitwise_exact': summed == total_load_N,
            'total_area_m2': total_area}


# --------------------------------------------------------------- history
def new_state():
    return {'tick': 0, 't': 0.0, 'x': 0.0, 'F': 0.0,
            'U_J': 0.0, 'Q_J': 0.0, 'W_J': 0.0, 'rows': []}


def step_position_controlled(state, dx_dt, dt, k, c, rest_length_m, band):
    """One tick of position-controlled Maxwell response (E2 protocol).

    Applies the strain gate to the END-OF-TICK extension BEFORE any update;
    appends the updated history row (port contract: updated history +
    stored/dissipated energy).
    """
    x_next = state['x'] + dx_dt * dt
    _check_strain(x_next, rest_length_m, band)
    F_next = maxwell_force_update(state['F'], dx_dt, dt, k, c)
    int_F_dt, int_F2_dt = maxwell_tick_integrals(state['F'], dx_dt, dt, k, c)
    W_next = state['W_J'] + dx_dt * int_F_dt
    Q_next = state['Q_J'] + int_F2_dt / c
    U_next = stored_energy(F_next, k)
    row = {'tick': state['tick'] + 1, 't': state['t'] + dt,
           'x_m': x_next, 'F_N': F_next, 'U_J': U_next, 'Q_J': Q_next,
           'W_J': W_next, 'dx_dt_m_per_s': dx_dt}
    state['tick'] = row['tick']
    state['t'] = row['t']
    state['x'], state['F'] = x_next, F_next
    state['U_J'], state['Q_J'], state['W_J'] = U_next, Q_next, W_next
    state['rows'].append(row)
    return row


def step_force_ramp(state, rate_N_per_s, dt, k, c, rest_length_m, band):
    """One tick of force-ramp response (protocol V): F(tau) = r*(t_n + tau).

    Spring equilibrates instantly (x_s = F/k); dashpot creeps x_d += int F/c.
    Exact within-tick ramp integrals; strain gate before any update.
    """
    require(dt > 0.0 and math.isfinite(rate_N_per_s), 'invalid_force_ramp')
    t_n = state['t']
    Phi = rate_N_per_s * (t_n * dt + dt * dt / 2.0)
    int_F2 = rate_N_per_s ** 2 * (t_n * t_n * dt + t_n * dt * dt
                                  + dt ** 3 / 3.0)
    F_end = rate_N_per_s * (t_n + dt)
    # spring: instant x_s = F/k, so delta-x_s = r*dt/k (exact);
    # dashpot: delta-x_d = (1/c) * int F dtau = Phi / c.
    x_next = state['x'] + rate_N_per_s * dt / k + Phi / c
    _check_strain(x_next, rest_length_m, band)
    W_next = state['W_J'] + (rate_N_per_s / k) * Phi + int_F2 / c
    Q_next = state['Q_J'] + int_F2 / c
    U_next = stored_energy(F_end, k)
    row = {'tick': state['tick'] + 1, 't': t_n + dt, 'x_m': x_next,
           'F_N': F_end, 'U_J': U_next, 'Q_J': Q_next, 'W_J': W_next,
           'F_rate_N_per_s': rate_N_per_s}
    state['tick'] = row['tick']
    state['t'] = row['t']
    state['x'], state['F'] = x_next, F_end
    state['U_J'], state['Q_J'], state['W_J'] = U_next, Q_next, W_next
    state['rows'].append(row)
    return row
