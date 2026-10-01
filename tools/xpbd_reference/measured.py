"""The MEASURED table this reference model is built on — no invented physics.

Every number here is measured or derived in
    docs/evidence/agent_fleet/SHIP/A1_XPBD/DIAGNOSTIC.md      (the measurement)
    docs/evidence/agent_fleet/SHIP/A1_XPBD/PREREG.md          (the contract)
    docs/evidence/agent_fleet/SHIP/A1_XPBD/diagnostic_results.json (raw)
by tools/xpbd_diagnostic.py against the LIVE engine (GET-only, ticks
3,254,324). This file holds CONSTANTS with provenance; it holds no model.

The world: 4 sealed water cells (the y-bands of the body solid), cut planes
at y = 0.338 (ankle), 1.903 (knee), 3.415 (hip). Cells indexed 0..3 =
feet, calves, thighs/hips, torso.
"""
import numpy as np

# --- constitutive constants -------------------------------------------------
KAPPA = 4.6e-10            # Pa^-1, water at 25 C — ALSO the engine's own
                           # kappa_ (membrane_tick.hpp:206). B = 1/kappa
                           # = 2.174 GPa. Astra's answer and the shipped code
                           # agree on dP = -dV/(kappa*V0) to the last digit.
RHO = 1000.0               # kg/m^3, the body's own mass law (13.8246 m^3
                           # -> 13,824.6 kg, measured lumped to the vertices)
H_TICK = 1.0 / 300.0       # s, the engine tick
G = 9.80665                # m/s^2
MU_FRICTION = 0.8          # the engine's Coulomb coefficient
                           # (ChimeraEngine/contact.py:84, mu: float = 0.8)

# --- the cells (DIAGNOSTIC.md Route 1, validated to ~2 ppm vs live v0) ------
V0 = np.array([0.287914, 0.334578, 0.693006, 12.5091])   # m^3, live v0
CELL_MASS = V0 * RHO                                     # kg: 287.9 .. 12509.1

# --- the cut planes (Route 2, the piston areas = the Jacobian rows) ---------
CUT_Y = np.array([0.338, 1.903, 3.415])                  # m
A_CUT = np.array([0.17535565700000005,                   # m^2 (ankle)
                  0.25492178000000004,                   # m^2 (knee)
                  1.0999349955500002])                   # m^2 (hip)

# --- reduced masses at the planes (free-free; m_below*m_above/(sum)) --------
M_BELOW = np.array([287.914, 622.4920000000001, 1315.498])   # kg
M_ABOVE = np.array([13536.684, 13202.106, 12509.1])          # kg
MU_RED = np.array([281.9178421807274,                        # kg
                   594.4625202231559,
                   1190.3200390926377])

# --- the measured Leibniz Jacobian (cells x planes), DIAGNOSTIC.md ----------
# Ring direction j (upward slide of plane j) trades the two neighboring
# cells: dV_j = +A_j, dV_{j+1} = -A_j; body ends contribute no columns.
J_MEAS = np.zeros((4, 3))
for _j in range(3):
    J_MEAS[_j, _j] += A_CUT[_j]
    J_MEAS[_j + 1, _j] -= A_CUT[_j]

# --- the PREDICTED dynamics (PREREG.md derivation; the falsifier bars) ------
OMEGA_CELL = np.array([907.503256371411,     # rad/s, cell 0 @ ankle plane
                       842.7855812594606,    # rad/s, cell 1 @ knee plane
                       1785.614623890079,    # rad/s, cell 2 @ hip plane
                       420.284331260959])    # rad/s, cell 3 @ hip plane
OMEGA_COUPLED = 1948.9510628679059           # rad/s, ring omega_max
OMEGA_RING_SPEC = np.array([1948.9510628679059, 1363.9682920063797,
                            540.0804899510859])  # full ring spectrum (desc)
ETA_EXPLICIT_BAR = 2.0
N_STABILITY = 4                # ceil(eta/2) = ceil(6.497/2); residual 1.62
ETA_AT_300HZ = 6.49650354289302

# Governing plane per cell for the single-piston probes (larger A^2/mu):
# cells 0,1,2,3 -> planes 0,1,2,2.
GOVERNING_PLANE = np.array([0, 1, 2, 2])

# --- derived here (not measured): the XPBD fidelity clause ------------------
# A converged XPBD substep on one linear mode (mass-normalized, the exact
# map of the code in solver.xpbd_substep) is
#   s'    = (s + h_s s')/(1 + x^2)
#   s'_v  = s'_v - (x^2/(1+x^2)) (s/h_s + s')
# with x = omega*h_s, whose amplification matrix has
#   |eig| = cos(omega_d h_s) = 1/sqrt(1 + x^2)
# — the discrete oscillation decays exactly like its phase. The +-10%
# frequency bar (PREREG P3) holds iff acos(1/sqrt(1+x^2)) >= 0.9*x, i.e.
# x <= 0.603 (root of that equation), giving the fidelity substep count.
X_FIDELITY_10PCT = 0.603
N_FIDELITY_10PCT = int(np.ceil(OMEGA_COUPLED * H_TICK / X_FIDELITY_10PCT))  # 11


def predicted_bias(omega: float, n: int) -> float:
    """The derived XPBD discrete-frequency ratio omega_d/omega at n substeps
    (converged per-substep solve, one linear mode). The battery MEASURES the
    same quantity and asserts the two agree — solver vs map theory."""
    x = omega * H_TICK / n
    return float(np.arccos(1.0 / np.sqrt(1.0 + x * x)) / x)


def predicted_decay(omega: float, n: int) -> float:
    """The derived per-substep amplitude |eig| = 1/sqrt(1+x^2) — the scheme's
    numerical damping of a stiff mode, a port datum for the appliance."""
    x = omega * H_TICK / n
    return float(1.0 / np.sqrt(1.0 + x * x))


def ring_stiffness() -> np.ndarray:
    """Astra's K_water = J^T diag(1/(kappa V0)) J on the 3 ring directions
    (N/m per unit ring displacement) — the diagnostic's coarse coupled
    stiffness, reproduced from the constants above."""
    return J_MEAS.T @ np.diag(1.0 / (KAPPA * V0)) @ J_MEAS


def ring_spectrum() -> np.ndarray:
    """omega^2 spectrum of (M^-1/2 K M^-1/2), descending; the prediction
    machine for OMEGA_RING_SPEC."""
    w2, _ = ring_modes()
    return w2


def ring_modes():
    """The ring's normal modes: (omegas descending, velocity seeds).
    Velocity seed v0 = M^-1/2 u_i (mass-normalized eigenvector) excites mode
    i ALONE, so each mode can be measured with the single-mode AR(2)
    instrument instead of fighting mode tails in one FFT."""
    K = ring_stiffness()
    Minv_half = np.diag(1.0 / np.sqrt(MU_RED))
    w2, U = np.linalg.eigh(Minv_half @ K @ Minv_half)
    order = np.argsort(w2)[::-1]
    return (np.sqrt(w2[order]), Minv_half @ U[:, order])
