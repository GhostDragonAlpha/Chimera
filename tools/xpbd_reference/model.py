"""The reference model: three constructions on ONE constraint machinery.

All three are the piston idealization A12 measured (DIAGNOSTIC.md): each seal
cut is a PISTON — an axial slide of the cut plane that trades volume between
the two neighboring cells at the measured cut area (the Leibniz identity
dV/dp = A(p) is the Jacobian row). The sealed water is the axial spring: its
volume constraint with compliance alpha = kappa*V0 IS the stiffness; no
separate spring is ever added.

  rig_single_piston — one cell, one plane, the diagnostic's free-free reduced
                      masses. The single-piston system the per-cell omega
                      table was derived on.
  ring_coupled      — the 3 ring directions (plane slides) with the measured
                      Leibniz Jacobian and reduced-mass inertia: Astra's
                      coarse coupled system, the machine the 1949.0 rad/s
                      prediction was derived on.
  SlabChain         — the full planar model: 4 rigid slabs (the cells'
                      masses, rho*V0), piston volume coupling + lateral
                      pins + servo hinges at the 3 cuts. This is the port
                      blueprint: the appliance solves THIS shape of stack
                      (volume | joint | servo | contact in one system).

A System is: state q, velocity v, diagonal inertia M, and a constraint stack
whose rows report (C, J, alpha) — refreshed from the CURRENT q every solver
iteration (the nonlinear-Jacobian doctrine). The solver (solver.py) never
knows which construction it is running.
"""
import numpy as np

from . import measured as M


# ---------------------------------------------------------------------------
class System:
    """Bare bones: flat DOF vector + diagonal inertia + constraint rows."""

    def __init__(self, ndof, w):
        self.ndof = ndof
        self.w = np.asarray(w, float)      # diagonal inertia (mass / inertia)
        self.q = np.zeros(ndof)
        self.v = np.zeros(ndof)
        self.rows = []                     # list of RowConstraint
        self.external = np.zeros(ndof)     # generalized external force

    def add(self, constraint):
        self.rows.append(constraint)
        return constraint

    def stack(self):
        """Evaluate every constraint row at the CURRENT q — the nonlinear
        refresh. Returns C (n,), J (n, ndof), alpha (n,)."""
        C, J, a = [], [], []
        for r in self.rows:
            Ci, Ji, ai = r.evaluate(self.q)
            C.append(np.atleast_1d(Ci))
            J.append(np.atleast_2d(Ji))
            a.append(np.atleast_1d(ai))
        return np.concatenate(C), np.vstack(J), np.concatenate(a)

    def kinetic(self):
        return 0.5 * float(self.w @ (self.v * self.v))

    def copy_state(self):
        return self.q.copy(), self.v.copy()

    def set_state(self, q, v):
        self.q[:] = q
        self.v[:] = v


class RowConstraint:
    """Constraint rows given by a callable q -> (C, J, alpha)."""

    def __init__(self, evaluate, name=""):
        self.evaluate = evaluate
        self.name = name


def _particle_system(masses):
    """Axial (vertical) particles: DOF k = upward position of mass k."""
    return System(len(masses), masses)


# ---------------------------------------------------------------------------
# Construction 1: the single-piston rig (per-cell frequency bars)
# ---------------------------------------------------------------------------
def rig_single_piston(cell: int) -> System:
    """The single-piston system behind OMEGA_CELL[cell] (PREREG P3's per-cell
    bars): cell `cell`'s volume spring against the governing plane's free-free
    reduced masses — the two sub-bodies the diagnostic partitioned at that
    plane (m_below, m_above). omega^2 = A^2/(kappa V0 mu) by construction;
    the battery MEASURES the solver's discrete oscillation against the bar.
    """
    j = M.GOVERNING_PLANE[cell]
    sys = _particle_system([M.M_BELOW[j], M.M_ABOVE[j]])
    A, alpha = M.A_CUT[j], M.KAPPA * M.V0[cell]

    def rows(q):
        e = q[1] - q[0]          # upward slide of the plane vs the body below
        return (np.array([A * e]),        # dV_cell = +A e  (measured J sign)
                np.array([[-A, +A]]),
                np.array([alpha]))

    sys.add(RowConstraint(rows, f"volume_cell{cell}"))
    return sys


# ---------------------------------------------------------------------------
# Construction 2: the coupled ring (the 1949.0 rad/s bar)
# ---------------------------------------------------------------------------
def ring_coupled() -> System:
    """Astra's coarse coupled system: the 3 plane slides with reduced-mass
    inertia; the 4 cell volumes coupled through the measured Leibniz J with
    compliance kappa*V0. Ends fixed (no end columns) — exactly the machine
    OMEGA_COUPLED was derived on (DIAGNOSTIC.md, modal estimate).
    """
    sys = _particle_system(M.MU_RED)
    Jm, alphas = M.J_MEAS, M.KAPPA * M.V0

    def rows(q):
        return (Jm @ q, Jm.copy(), alphas)   # linear system, constant J

    sys.add(RowConstraint(rows, "volume_cells"))
    return sys


# ---------------------------------------------------------------------------
# Construction 3: the planar slab chain (the port blueprint)
# ---------------------------------------------------------------------------
class SlabChain:
    """4 rigid slabs (the cells) joined at the 3 seal cuts.

    Per cut joint j (lower slab lo=j, upper slab up=j+1):
      piston extension  e_j = (r_up - r_lo) . d_hat
        r_lo/r_up: the cut-face anchors (body-local, fixed);
        d_hat: axial unit = R((theta_lo+theta_up)/2) applied to y_hat.
      The 4 cell volumes are ONE constraint block through the measured
      Leibniz J:  C_i = sum_j J_MEAS[i,j] e_j,  alpha_i = kappa V0_i.
        (A shared cell — calves bounded by ankle AND knee — is ONE row.)
      pin:    lateral offset (r_up - r_lo) . n_hat = 0, rigid (alpha=0).
      servo:  theta_up - theta_lo - target, compliance 1/k_servo.
              The axial direction stays FREE — the sealed water is the axial
              spring. Servo intents are constraints: equal and opposite
              torque pair through the joint, never a pose write.

    k_servo derivation (Rule 1, stated requirements, no taste): the hip
    servo must hold the torso weight through the half-width lever with
    droop <= THETA_DROOP:  k_s = m_torso g (w_hip/2) / THETA_DROOP.
    """

    THETA_DROOP = np.deg2rad(1.0)          # allowed static droop, full load
    Y_BOTTOM = -0.019507                   # measured feet-cell band bottom
    # measured cell bands (DIAGNOSTIC.md Route 1): (ylo, yhi) per cell
    BAND = np.array([[-0.019507, 0.338], [0.338, 1.903],
                     [1.903, 3.415], [3.415, 9.97118]])

    def __init__(self):
        m = M.CELL_MASS
        w = np.array([M.A_CUT[0], M.A_CUT[1], M.A_CUT[2], M.A_CUT[2]])
        L = self.BAND[:, 1] - self.BAND[:, 0]
        self.width, self.length, self.m = w, L, m
        self.inertia = m * (w**2 + L**2) / 12.0
        self.y_center = self.BAND.mean(axis=1)

        W = np.empty(12)
        for i in range(4):
            W[3 * i:3 * i + 3] = [m[i], m[i], self.inertia[i]]
        self.sys = System(12, W)
        self.sys.q[1::3] = self.y_center   # rest pose: straight stack
        self.servo_target = np.zeros(3)

        k_servo = m[3] * M.G * (w[2] / 2.0) / self.THETA_DROOP
        self.alpha_servo = 1.0 / k_servo

        # per joint: the cut-face anchors in body-local coordinates
        self.cut_local = []
        for j in range(3):
            self.cut_local.append(
                (np.array([0.0, M.CUT_Y[j] - self.y_center[j]]),
                 np.array([0.0, M.CUT_Y[j] - self.y_center[j + 1]])))

        self._add_volume_block()
        for j in range(3):
            self._add_pin_row(j)
            self._add_servo_row(j)

    # -- kinematics ---------------------------------------------------------
    def world_point(self, i, local):
        x, y, th = self.sys.q[3 * i:3 * i + 3]
        c, s = np.cos(th), np.sin(th)
        return np.array([x + c * local[0] - s * local[1],
                         y + s * local[0] + c * local[1]])

    def _point_jac(self, i, local):
        """d(world point of slab i)/d(slab i DOF): (2,3)."""
        th = self.sys.q[3 * i + 2]
        c, s = np.cos(th), np.sin(th)
        ry = s * local[0] + c * local[1]
        rx = c * local[0] - s * local[1]
        return np.array([[1.0, 0.0, -ry],
                         [0.0, 1.0, rx]])

    def _joint_geom(self, j):
        lo, up = j, j + 1
        loc_lo, loc_up = self.cut_local[j]
        r_lo = self.world_point(lo, loc_lo)
        r_up = self.world_point(up, loc_up)
        # The joint frame rides the LOWER slab (not a mean angle): then the
        # constraint's generalized force has zero component on the pair's
        # rigid rotation mode — angular momentum is conserved EXACTLY. A
        # mean-angle frame leaks angular momentum at O(anchor separation).
        th_lo = self.sys.q[3 * lo + 2]
        c, s = np.cos(th_lo), np.sin(th_lo)
        d_hat = np.array([-s, c])          # R(th_lo) y_hat: axial
        n_hat = np.array([c, s])           # R(th_lo) x_hat: lateral
        return lo, up, loc_lo, loc_up, r_lo, r_up, d_hat, n_hat

    def _extension_jac(self, j, vec, geom):
        """d/dq of C = (r_up - r_lo) . vec, vec a unit vector of the LOWER
        slab's frame. Per body: translation columns +-vec; the theta column
        from the anchor arm (dR/dtheta . loc = z_hat x arm); the frame term
        (vec's own spin with the lower frame) lands on theta_lo ONLY — that
        placement is what makes the pin momentum-neutral."""
        lo, up, loc_lo, loc_up, r_lo, r_up, d_hat, n_hat = geom
        z = lambda a: np.array([-a[1], a[0]])            # z_hat x a
        out = np.zeros(12)
        out[3 * lo] = -vec[0]
        out[3 * lo + 1] = -vec[1]
        out[3 * up] = +vec[0]
        out[3 * up + 1] = +vec[1]
        arm_lo = r_lo - self.world_point(lo, np.zeros(2))
        arm_up = r_up - self.world_point(up, np.zeros(2))
        out[3 * lo + 2] = -(z(arm_lo) @ vec) + (r_up - r_lo) @ z(vec)
        out[3 * up + 2] = +(z(arm_up) @ vec)
        return out

    def extensions(self):
        """Current piston extensions e_j (3,)."""
        e = np.zeros(3)
        for j in range(3):
            geom = self._joint_geom(j)
            e[j] = (geom[5] - geom[4]) @ geom[6]     # (r_up - r_lo) . d_hat
        return e

    # -- constraint rows ----------------------------------------------------
    def _add_volume_block(self):
        """The 4 cell volumes as ONE block through the measured J."""
        def rows(q):
            e = self.extensions()                       # (3,)
            C = M.J_MEAS @ e                            # (4,) dV per cell
            dE = np.zeros((3, 12))                      # de_j/dq
            for j in range(3):
                geom = self._joint_geom(j)
                dE[j] = self._extension_jac(j, geom[6], geom)
            return C, M.J_MEAS @ dE, M.KAPPA * M.V0

        self.sys.add(RowConstraint(rows, "volume_cells"))

    def _add_pin_row(self, j):
        def rows(q, j=j):
            geom = self._joint_geom(j)
            lo, up, r_lo, r_up, n_hat = geom[0], geom[1], geom[4], geom[5], geom[7]
            C = np.array([(r_up - r_lo) @ n_hat])
            J = self._extension_jac(j, n_hat, geom)
            return C, J[None, :], np.array([0.0])       # rigid
        self.sys.add(RowConstraint(rows, f"pin_joint{j}"))

    def _add_servo_row(self, j):
        def rows(q, j=j):
            lo, up = j, j + 1
            C = np.array([self.sys.q[3 * up + 2] - self.sys.q[3 * lo + 2]
                          - self.servo_target[j]])
            J = np.zeros((1, 12))
            J[0, 3 * lo + 2] = -1.0
            J[0, 3 * up + 2] = +1.0
            return C, J, np.array([self.alpha_servo])
        self.sys.add(RowConstraint(rows, f"servo_joint{j}"))

    def set_servo_target(self, j, value):
        self.servo_target[j] = value

    # -- contacts and balance (static form; see battery.balance_gate) -------
    def foot_points(self):
        """The two feet-bottom corners (planar contact points)."""
        hw = self.width[0] / 2.0
        return [self.world_point(0, np.array([-hw, self.Y_BOTTOM - self.y_center[0]])),
                self.world_point(0, np.array([+hw, self.Y_BOTTOM - self.y_center[0]]))]

    def com(self):
        com = np.zeros(2)
        for i in range(4):
            com = com + self.m[i] * self.world_point(i, np.zeros(2))
        return com / self.m.sum()

    def momentum(self):
        """Total linear momentum (2,) and angular momentum about the origin
        (z scalar) of the slab system."""
        p = np.zeros(2)
        L = 0.0
        for i in range(4):
            x, y, th = self.sys.q[3 * i:3 * i + 3]
            vx, vy, wz = self.sys.v[3 * i:3 * i + 3]
            p += self.m[i] * np.array([vx, vy])
            L += self.inertia[i] * wz + self.m[i] * (x * vy - y * vx)
        return p, L
