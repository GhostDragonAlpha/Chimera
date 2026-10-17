"""AP02 finite-area port coupling: two independent ports joined by one qualified
finite-area attachment. Each port is a rigid carrier exactly welded to the node
of an AP01 fan (rim fixed); carrier B is bolted to a fixed fixture, carrier A is
the loaded port. The joint is the unchanged CPU reference module
tools/finite_area_attachment, admitted through its own gates. This measures the
force AND moment a finite-area patch transfers between ports — the scalar rail
coupon has no moment path.

Sign conventions: load_n is the external force [N] applied at carrier A's
origin; torque_nm is the external torque [N*m] (conjugate to the spatial
incremental rotation chart of the reference module). The fan pulls its node
toward the rim plane with reaction R = dE/dh, i.e. force (0,0,-R) on carrier A.
"""
from __future__ import annotations
import hashlib
import importlib.util
import math
import numpy as np
from .core import ROOT, Refusal, require
from .core import recipe as recipe1, detailed as detailed1

FAA_PATH = ROOT / "tools/finite_area_attachment/finite_area_attachment.py"

def _load_faa():
    spec = importlib.util.spec_from_file_location("chimera_faa_reference", FAA_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

faa = _load_faa()

def faa_source_hash():
    return hashlib.sha256(FAA_PATH.read_bytes()).hexdigest()

KAPPA_AREAL = 1e8            # N/m^3, declared synthetic areal stiffness density
PATCH_RADIUS = 0.02          # m, anchor circle radius
K_COUPLE_MIN = 1e-3          # N*m/rad, authored fixture requirement

def patch_spec(n_anchors=4, radius=PATCH_RADIUS, collinear=False):
    """Finite-area patch: anchors on a circle (or a line, for the falsifier),
    uniform weights, isotropic Kbar = kappa_areal * nominal patch area."""
    if collinear:
        anchors = np.array([[-radius, 0., 0.], [0., 0., 0.], [radius, 0., 0.]])
        area = 2*radius*radius
    else:
        angles = np.arange(n_anchors) * (2*math.pi/n_anchors)
        anchors = np.column_stack([radius*np.cos(angles), radius*np.sin(angles), np.zeros(n_anchors)])
        area = math.pi*radius**2
    return faa.AttachmentSpec(anchors, stiffness=KAPPA_AREAL*area), area

def admit(spec, area):
    """The reference module's own admission gates; returns measured verdicts."""
    quality = spec.assert_constrains_all_six()
    eigen = spec.assert_min_couple_stiffness(K_COUPLE_MIN, kappa_areal=KAPPA_AREAL, patch_area=area)
    return {"verdict": quality.verdict, "rank": quality.rank_constraint,
            "couple_stiffness_eigen_nm_per_rad": [float(v) for v in eigen]}

def port_state(spec, c_a, R_a, c_b=None, R_b=None):
    c_a = np.asarray(c_a, dtype=float)
    c_b = np.zeros(3) if c_b is None else np.asarray(c_b, dtype=float)
    R_b = np.eye(3) if R_b is None else np.asarray(R_b, dtype=float)
    x_a = c_a + (np.asarray(R_a, dtype=float) @ spec.bone_anchors.T).T   # carrier A anchors, world
    return faa.BondState(x_a, np.zeros_like(x_a), c_b, R_b, np.zeros(3), np.zeros(3))

def joint_wrenches(spec, st, c_a):
    """(F_A, tau_A about c_A, F_B, tau_B about c_B) [N, N*m] from the reference."""
    f_mem, F_b, tau_b = faa.forces(spec, st)
    F_a = f_mem.sum(axis=0)
    tau_a = np.cross(st.membrane_x - c_a, f_mem).sum(axis=0)
    return F_a, tau_a, F_b, tau_b

def total_energy(spec, fan_recipe, c_a, R_a, c_b=None, R_b=None):
    return (faa.energy(spec, port_state(spec, c_a, R_a, c_b, R_b))
            + detailed1(fan_recipe, float(np.asarray(c_a, dtype=float)[2]))["energy"])

def _fan_force_z(fan_recipe, z):
    return -detailed1(fan_recipe, float(z))["reaction"]

def measure_transfer(spec, fan_recipe, c_a, phi):
    """Prescribed port-A pose against the fixed port-B fixture: the cross-port
    force and moment, with exact wrench balance and FD-gradient agreement."""
    c_a = np.asarray(c_a, dtype=float)
    R_a = faa.rot_exp(np.asarray(phi, dtype=float))
    st = port_state(spec, c_a, R_a)
    F_a, tau_a, F_b, tau_b = joint_wrenches(spec, st, c_a)
    balance_f = F_a + F_b
    balance_t = tau_a + np.cross(c_a, F_a) + tau_b
    # Generalized analytic force on A's FREE DOFs (z, spatial theta): joint + fan.
    # c_a x/y are frozen, so F_a's x/y components have no conjugate DOF.
    analytic = np.array([F_a[2] + _fan_force_z(fan_recipe, c_a[2]), tau_a[0], tau_a[1], tau_a[2]])
    fd = np.zeros(4); delta = 1e-6
    for j in range(4):
        e = np.zeros(4); e[j] = delta
        if j == 0:
            fd[j] = -(total_energy(spec, fan_recipe, c_a+np.array([0,0,delta]), R_a) -
                      total_energy(spec, fan_recipe, c_a-np.array([0,0,delta]), R_a))/(2*delta)
        else:
            u = np.zeros(3); u[j-1] = delta
            fd[j] = -(total_energy(spec, fan_recipe, c_a, faa.rot_exp(u) @ R_a) -
                      total_energy(spec, fan_recipe, c_a, faa.rot_exp(-u) @ R_a))/(2*delta)
    # generalized forces can vanish physically (e.g. pure lateral offset has zero
    # z/theta gradient): normalize against the physical K*delta scale as well
    scale = max(float(np.max(np.abs(analytic))),
                float(spec.Kbar[0, 0]) * max(float(np.linalg.norm(c_a)), PATCH_RADIUS * float(np.linalg.norm(phi))),
                1e-30)
    return {"F_b_N": [float(v) for v in F_b], "tau_b_Nm": [float(v) for v in tau_b],
            "F_a_N": [float(v) for v in F_a], "tau_a_Nm": [float(v) for v in tau_a],
            "wrench_balance_force_n": float(np.max(np.abs(balance_f))),
            "wrench_balance_torque_nm": float(np.max(np.abs(balance_t))),
            "gradient_fd_max_error_relative": float(np.max(np.abs(fd - analytic))/scale)}

def equilibrium_loaded_port(spec, fan_recipe, load_n, torque_nm, *, tolerance=1e-9):
    """Port A free on its z-rail with free rotation, loaded by force load_n and
    torque_nm; port B fixed. Newton on the 4-DOF total potential; returns the
    equilibrium pose and the reaction wrench measured at port B."""
    load = np.asarray(load_n, dtype=float); torque = np.asarray(torque_nm, dtype=float)
    require(load.shape == (3,) and torque.shape == (3,) and np.all(np.isfinite(load)) and np.all(np.isfinite(torque)), "invalid_wrench")
    def potential(q):
        c_a = np.array([0., 0., q[0]]); R_a = faa.rot_exp(q[1:])
        return total_energy(spec, fan_recipe, c_a, R_a) - load[2]*q[0] - torque @ q[1:]
    def gradient(q):
        """Analytic generalized force: the reference module's own wrenches are
        exact, so no finite-difference noise floor limits the residual."""
        c_a = np.array([0., 0., q[0]]); R_a = faa.rot_exp(q[1:])
        F_a, tau_a, _, _ = joint_wrenches(spec, port_state(spec, c_a, R_a), c_a)
        fan_r = detailed1(fan_recipe, float(q[0]))["reaction"]
        g = np.zeros(4)
        g[0] = -(load[2] - fan_r + F_a[2])
        g[1:] = -(torque + tau_a)   # fan force acts at c_a || z: zero generalized torque
        return g
    q = np.zeros(4); g = gradient(q)
    for iteration in range(60):
        if abs(g[0]) <= tolerance and float(np.max(np.abs(g[1:]))) <= tolerance:
            break
        d = 1e-5
        H = np.zeros((4,4))
        for j in range(4):
            e = np.zeros(4); e[j] = d
            H[:,j] = (gradient(q+e) - gradient(q-e))/(2*d)
        H = .5*(H+H.T)
        try: step = -np.linalg.solve(H, g)
        except np.linalg.LinAlgError: raise Refusal("joint_hessian_singular")
        lam = 1.0
        for _ in range(40):
            if potential(q+lam*step) <= potential(q) + 1e-4*lam*g @ step or lam < 1e-10:
                q = q + lam*step; break
            lam *= .5
        else:
            raise Refusal("joint_equilibrium_not_converged")
        g = gradient(q)
    else:
        raise Refusal("joint_equilibrium_not_converged")
    c_a = np.array([0., 0., q[0]]); R_a = faa.rot_exp(q[1:])
    st = port_state(spec, c_a, R_a)
    F_a, tau_a, F_b, tau_b = joint_wrenches(spec, st, c_a)
    fan_reaction = detailed1(fan_recipe, float(q[0]))["reaction"]
    resid_f = load + np.array([0., 0., -fan_reaction]) + F_a
    resid_t = torque + np.cross(c_a, np.array([0., 0., -fan_reaction])) + tau_a
    return {"q": [float(v) for v in q],
            "residual_force_n": abs(float(g[0])), "residual_torque_nm": float(np.max(np.abs(g[1:]))),
            "fan_reaction_n": float(fan_reaction),
            "F_b_N": [float(v) for v in F_b], "tau_b_Nm": [float(v) for v in tau_b],
            "carrier_balance_force_n": float(np.max(np.abs(resid_f))),
            "carrier_balance_torque_nm": float(np.max(np.abs(resid_t)))}
