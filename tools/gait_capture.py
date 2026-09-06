"""Offline capture-law falsifier. Run from repo root: python tools/gait_capture.py.

numpy + stdlib only. Reads the canonical blobs through gait_mirror; never writes
them, drives the engine, or silently enables an uncertified gait. See
docs/THE_CAPTURE_LAW.md for the predeclared statements/predictions/falsifiers.
Exit 0 = numerical checks ran, NOT permission to walk; --require-ready exits 2
when the integration gate is closed. --self-test runs analytic controls only.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from itertools import product
import math

import numpy as np

try:
    from . import gait_mirror as mirror
except ImportError:
    import gait_mirror as mirror

STATE_TOL = 1e-9
CLOCK_TOL = 1e-10
FOOT_FRACTION = 0.005
IK_TOL = 1e-10  # numerical inverse tolerance, distinct from the task's foot gate


@dataclass(frozen=True)
class Orbit:
    h: float
    leg: float
    T: float
    speed: float  # mean forward speed: a task/reference choice, not LIPM output

    @property
    def w(self):
        return math.sqrt(mirror.G / self.h)

    @property
    def a(self):
        return self.speed * self.T / 2

    @property
    def vb(self):
        return self.w * self.a / math.tanh(self.w * self.T / 2)

    @property
    def vc(self):
        return self.w * self.a / math.sinh(self.w * self.T / 2)

    @property
    def xi0(self):
        return -self.a + self.vb / self.w

    @property
    def energy(self):
        return self.vc**2 / 2

    def flow(self, x, v, t):
        c, s = math.cosh(self.w*t), math.sinh(self.w*t)
        return np.array([c*x + s*v/self.w, self.w*s*x + c*v])

    def state(self, t):
        return self.flow(-self.a, self.vb, t)

    def E(self, state):
        x, v = state
        return (v*v - self.w*self.w*x*x) / 2

    def xi(self, state):
        return state[0] + state[1] / self.w


def capture_margin(xi_relative, delay, w, dmin, dmax):
    """One-step stopping interval, relative to the CURRENT support point.

    After a delay, the only torque-free stopping foot is exp(w*delay)*xi.
    Positive margin says this point lies within the supplied placement interval;
    it does NOT say that the interval is realizable by this rig.
    """
    foot = math.exp(w*delay) * xi_relative
    return min(foot-dmin, dmax-foot)


def cp_reset(o, state):
    """Place at d=exp(wT)*xi-xi_ref, zero impulse: xi-only deadbeat."""
    pre = o.flow(*state, o.T)
    d = o.xi(pre) - o.xi0
    return pre - np.array([d, 0.0]), d, 0.0


def hybrid_reset(o, state):
    """Two independently actuated inputs: foot displacement and signed J/m."""
    pre = o.flow(*state, o.T)
    d, impulse = pre[0] + o.a, o.vb - pre[1]
    return pre + np.array([-d, impulse]), d, impulse


def two_step_reset(o, state):
    """Placement-only full-state deadbeat has TWO-step, not one-step, horizon."""
    c, s = math.cosh(o.w*o.T), math.sinh(o.w*o.T)
    gain = np.array([2*c, (2*c*c-1)/(o.w*s)])
    d = 2*o.a + float(gain @ (state-[-o.a, o.vb]))
    return o.flow(*state, o.T)-[d, 0], d, 0.0


def elliptic_k(k):
    """Complete K by arithmetic-geometric mean (modulus, not parameter)."""
    if not 0 <= k < 1:
        raise ValueError("elliptic modulus outside [0,1)")
    a, b = 1.0, math.sqrt(1-k*k)
    for _ in range(64):
        if abs(a-b) < 1e-15:
            return math.pi / (2*a)
        a, b = (a+b)/2, math.sqrt(a*b)
    raise RuntimeError("AGM failed")


def swing_period(T, leg, speed):
    ratio = speed*T / (2*leg)
    if not 0 < ratio < 1:
        raise ValueError("swing amplitude outside point-pendulum reach")
    alpha = math.asin(ratio)
    return 2*math.sqrt(leg/mirror.G)*elliptic_k(math.sin(alpha/2))


def candidate_clock(leg, speed):
    """Finite-amplitude surrogate fixed point. Does not invent an impulse budget."""
    T = math.pi * math.sqrt(leg/mirror.G)
    for iteration in range(1, 65):
        nxt = swing_period(T, leg, speed)
        if abs(nxt-T) < CLOCK_TOL:
            return nxt, iteration, abs(swing_period(nxt, leg, speed)-nxt)
        T = nxt
    raise RuntimeError("FALSIFIER C4: clock loop did not converge in 64 iterations")


def capture_clock_limit(h, leg, speed, upper):
    """Maximum T for xi-only correction of +10% vb within assumed d<=2L.

    d(T)=speed*T + .1*exp(wT)*vb(T)/w is strictly increasing for T>0.
    Bisection solves the inequality boundary; this is not a cadence sweep.
    """
    lo, hi = 1e-12, upper
    def excess(T):
        o = Orbit(h, leg, T, speed)
        return speed*T + .1*math.exp(o.w*T)*o.vb/o.w - 2*leg
    if excess(lo) >= 0 or excess(hi) <= 0:
        raise ValueError('capture-clock bound is not bracketed')
    while hi-lo > CLOCK_TOL:
        mid = (lo+hi)/2
        if excess(mid) > 0:
            hi = mid
        else:
            lo = mid
    return (lo+hi)/2


def rk4(fun, y, t, dt):
    k1 = fun(t, y)
    k2 = fun(t+dt/2, y+dt*k1/2)
    k3 = fun(t+dt/2, y+dt*k2/2)
    k4 = fun(t+dt, y+dt*k3)
    return y + dt*(k1+2*k2+2*k3+k4)/6


def swing_samples(o, n=4096):
    """Independent ODE integration of the fixed-pivot pendulum surrogate."""
    alpha = math.asin(o.a/o.leg)
    fun = lambda t, y: np.array([y[1], -mirror.G/o.leg*math.sin(y[0])])
    dt = o.T/n
    y = np.array([-alpha, 0.0])
    history = [y.copy()]
    # One extra step brackets the return of angular velocity through zero.
    for i in range(n+1):
        y = rk4(fun, y, i*dt, dt)
        history.append(y.copy())
    history = np.array(history)
    hits = np.flatnonzero((history[:-1, 1] > 0) & (history[1:, 1] <= 0))
    if not len(hits):
        raise RuntimeError("FALSIFIER C4: no independent swing return")
    i = int(hits[0])
    fraction = history[i, 1] / (history[i, 1]-history[i+1, 1])
    measured_T = (i+fraction)*dt
    return history[:n+1], abs(measured_T-o.T)


def numerical_controls(o):
    """Known-answer, ablation and perturbation controls; failures cannot pass."""
    z = np.array([-o.a, o.vb])
    mirror_orbit = dict(omega=o.w, step_time=o.T, half_step=o.a)
    for t in (0, o.T/2, o.T):
        assert abs(mirror.lipm_x(t, mirror_orbit)-o.state(t)[0]) < STATE_TOL, 'C1 mirror orbit'
    y = z.copy()
    dt = o.T/2048
    fun = lambda t, state: np.array([state[1], o.w**2*state[0]])
    for i in range(2048):
        y = rk4(fun, y, i*dt, dt)
    scale = np.array([1.0, 1/o.w])
    flow_error = float(np.max(abs((y-o.flow(*z, o.T))*scale)))
    assert flow_error < 1e-8, ("C1 flow", flow_error)
    assert np.array_equal(o.flow(0, 0, o.T), [0, 0]), "C1 standstill"
    perturbed = z + np.array([0, 0.1*o.vb])
    cp, d, _ = cp_reset(o, perturbed)
    hybrid, hd, j = hybrid_reset(o, perturbed)
    assert abs(o.xi(cp)-o.xi0) < STATE_TOL, "C2 xi reset"
    assert np.max(abs((cp-z)*scale)) > STATE_TOL, "C2 full-state counterexample"
    assert np.max(abs((hybrid-z)*scale)) < STATE_TOL, "C2 hybrid reset"
    second = two_step_reset(o, two_step_reset(o, perturbed)[0])[0]
    assert np.max(abs((second-z)*scale)) < STATE_TOL, "C2 two-step placement"
    open_state = o.flow(*perturbed, o.T) - np.array([2*o.a, 0])
    assert abs(o.xi(open_state)-o.xi0) > abs(o.xi(perturbed)-o.xi0), "C2 ablation"
    nominal = hybrid_reset(o, z)[0]
    assert abs(o.E(nominal)-o.energy) < 1e-9, "C3 nominal energy"
    # Arbitrary states, not merely the one reference trace.
    for dx, dv in ((0.2*o.a, -0.07*o.vb), (-0.1*o.a, 0.1*o.vb)):
        state = z + [dx, dv]
        pre = o.flow(*state, o.T)
        post, displacement, impulse = hybrid_reset(o, state)
        ledger = pre[1]*impulse + impulse**2/2 + o.w**2*(pre[0]*displacement-displacement**2/2)
        assert abs(o.E(post)-o.E(pre)-ledger) < 1e-9, "C3 reset ledger"
        assert abs(o.E(pre)-o.E(state)) < 1e-9, "C3 stance energy"
    assert capture_margin(2.0, 0, o.w, -1, 1) < 0, "C1 outside control"
    assert capture_margin(0.0, 0, o.w, -1, 1) > 0, "C1 inside control"
    # Stable-manifold startup under the NOMINAL periodic support schedule.
    startup = np.array([0.0, o.w*o.xi0])
    after = o.flow(*startup, o.T)-[2*o.a, 0]
    expected = z + math.exp(-o.w*o.T)*(startup-z)
    assert np.max(abs((after-expected)*scale)) < STATE_TOL, "C2 startup manifold"
    assert abs(o.xi([o.xi0, 0])-o.xi0) < STATE_TOL, "C2 controlled lean manifold"
    return flow_error, cp, d, hd, j


def plane(v):
    # (Y,Z) plane: rotation about +X is the ordinary 2-D positive rotation.
    return np.asarray(v)[[1, 2]]


def planar_seed(pack, chain, marker, target):
    """Two-link inverse for THIS reversed fixed-pivot product, flat full frame.

    q-A-(P-H) = R(k+a)(H-K) + R(a)(K-A), with h+k+a=0.
    Both cosine-law branches are evaluated. Infeasible requests return no seeds;
    no clipping a target into reach and subsequently reporting a success.
    """
    H, K, A = pack.pivot[chain]
    b1, b2 = plane(H-K), plane(K-A)
    d = plane(target-A-(marker-H))
    l1, l2, r = np.linalg.norm(b1), np.linalg.norm(b2), np.linalg.norm(d)
    if abs(target[0]-marker[0]) > 1e-10 or not abs(l1-l2) <= r <= l1+l2 or r < 1e-12:
        return []
    arg = lambda b: math.atan2(b[1], b[0])
    beta = math.acos(float(np.clip((r*r+l1*l1-l2*l2)/(2*r*l1), -1, 1)))
    seeds = []
    for sign in (-1, 1):
        phi1 = arg(d) + sign*beta - arg(b1)
        c, s = math.cos(phi1), math.sin(phi1)
        remainder = d - np.array([[c, -s], [s, c]]) @ b1
        phi2 = arg(remainder)-arg(b2)
        angles = np.array([-phi1, phi1-phi2, phi2])
        angles = (angles+math.pi) % (2*math.pi)-math.pi
        seeds.append(angles / pack.axis[chain, 0])
    return seeds


def rom_representatives(q, lo, hi):
    """Enumerate equivalent angles in the actual ROM; never clip a seed."""
    choices = []
    for angle, lower, upper in zip(q, lo, hi):
        first = math.ceil((lower-angle)/(2*math.pi)-1e-12)
        last = math.floor((upper-angle)/(2*math.pi)+1e-12)
        choices.append([angle+2*math.pi*k for k in range(first,last+1)])
    return [np.array(v) for v in product(*choices)]


def free_frame_seeds(pack, chain, marker, target):
    """Reverse three-hinge IK with a DERIVED redundant-frame orientation.

    U=Q-A, b0=P-H, b1=H-K, b2=K-A.  Select |U-R(phi)b0|^2
    halfway through the intersection of the two attainable squared-radius
    intervals: this maximizes the minimum squared slack to their four edges.
    Both orientations and both elbow branches are enumerated, then ROM-filtered.
    The returned delta is virtual-link bend, not the stored knee angle.
    """
    H,K,A = pack.pivot[chain]
    b0,b1,b2,U = map(plane, (marker-H,H-K,K-A,target-A))
    l0,l1,l2,r = map(float, map(np.linalg.norm, (b0,b1,b2,U)))
    if abs(target[0]-marker[0]) > 1e-10:
        return [], float('nan')
    lower = max(abs(l1-l2), abs(l0-r))
    upper = min(l1+l2, l0+r)
    if lower > upper+1e-12 or l0*l1*l2 == 0:
        return [], float('nan')
    rho2 = (lower*lower+upper*upper)/2
    delta = math.acos(float(np.clip((rho2-l1*l1-l2*l2)/(2*l1*l2),-1,1)))
    if r < 1e-12:
        orientations = [0.0]  # rotationally degenerate; not an exhaustive ROM proof
    else:
        alpha = math.acos(float(np.clip((r*r+l0*l0-rho2)/(2*r*l0),-1,1)))
        offset = math.atan2(U[1],U[0])-math.atan2(b0[1],b0[0])
        orientations = [offset-alpha,offset+alpha]
    lo,hi = np.radians(pack.rom[chain]).T
    seeds = []
    for phi in orientations:
        virtual_marker = H + mirror.rot(np.array([1.,0.,0.]),phi) @ (marker-H)
        for q in planar_seed(pack,chain,virtual_marker,target):
            q[0] += phi / pack.axis[chain[0],0]
            seeds.extend(rom_representatives(q,lo,hi))
    return seeds, delta


def mirrored_rom(pack):
    """Return a copied recommended ROM table and measured axial parity.

    M=diag(-1,1,1) reflects positions. Axial vectors reflect by det(M)*M.
    If a_R=s*det(M)*M*a_L, theta_R=s*theta_L and I_R=s*I_L.
    Left intervals are the declared reference; a nonparallel axis needs a
    new spatial joint law, not an invented scalar sign adjustment.
    """
    ix = {name:i for i,name in enumerate(pack.names)}
    rom = pack.rom.copy()
    rows = []
    for name,i in ix.items():
        if not name.endswith('_L') or name[:-2]+'_R' not in ix:
            continue
        j = ix[name[:-2]+'_R']
        expected_axis = np.array([1.,-1.,-1.])*pack.axis[i]
        dot = float(pack.axis[j] @ expected_axis)
        if abs(abs(dot)-1) > 1e-10:
            raise ValueError(f'{name}: axes are not related by scalar mirror parity')
        sign = 1 if dot >= 0 else -1
        recommended = pack.rom[i].copy() if sign == 1 else -pack.rom[i,::-1]
        rows.append((pack.names[j],sign,pack.rom[j].copy(),recommended.copy()))
        rom[j] = recommended
    return replace(pack,rom=rom), rows


def rom_gauge_control(rest,pack):
    """One contrived opposite-axis knee is a known-answer S2 control only."""
    knee = pack.names.index('knee_R')
    axes = pack.axis.copy(); axes[knee] *= -1
    changed = replace(pack,axis=axes)
    corrected,_ = mirrored_rom(changed)
    assert np.array_equal(corrected.rom[knee],-pack.rom[knee,::-1]), 'S2 sign-swap'
    theta = np.zeros(len(pack.names))
    theta[knee] = math.radians(pack.rom[knee,1])
    negated_theta = theta.copy(); negated_theta[knee] *= -1
    error = float(np.max(abs(mirror.pose_points(rest,pack,theta)-mirror.pose_points(rest,corrected,negated_theta))))
    assert error <= IK_TOL, 'S2 negated-axis spatial equivalence'
    for angle in np.radians(pack.rom[knee]):
        assert np.radians(corrected.rom[knee,0])-1e-12 <= -angle <= np.radians(corrected.rom[knee,1])+1e-12
    # Show the unchanged-ROM ablation loses a real spatial endpoint.
    endpoint_lost = not (pack.rom[knee,0] <= -pack.rom[knee,1] <= pack.rom[knee,1])
    assert endpoint_lost, 'S2 missing ROM swap must be observable on this asymmetric interval'
    return error


def bounded_refine(fun,target,seed,lo,hi):
    """Same bounded Gauss-Newton objective as the mirror, stable at rank loss.

    Stop on a solved residual. Solve the augmented least-squares system rather
    than squaring its condition number in J.T J. Inward differences retain a
    derivative at an upper ROM boundary. Constants match the inherited solver.
    """
    q = np.clip(seed.copy(),lo,hi)
    damping = 1e-4
    for _ in range(80):
        residual = fun(q)-target
        if np.linalg.norm(residual) <= IK_TOL:
            break
        jac = np.empty((len(residual),len(q)))
        for k in range(len(q)):
            d = min(1e-5,hi[k]-q[k])
            if d < 1e-10:
                d = -min(1e-5,q[k]-lo[k])
            if d == 0:
                jac[:,k] = 0
            else:
                perturbed=q.copy(); perturbed[k]+=d
                jac[:,k]=(fun(perturbed)-fun(q))/d
        augmented=np.vstack((jac,math.sqrt(damping)*np.eye(len(q))))
        rhs=np.concatenate((-residual,np.zeros(len(q))))
        step=np.linalg.lstsq(augmented,rhs,rcond=None)[0]
        candidate=np.clip(q+step,lo,hi)
        if np.linalg.norm(fun(candidate)-target) < np.linalg.norm(residual):
            q=candidate
            damping=max(damping*.3,np.finfo(float).eps)
        else:
            damping*=10
        if np.linalg.norm(step)<1e-7:
            break
    return q


class Rig:
    def __init__(self, rest, pack, seed_law='free'):
        self.rest, self.pack = rest, pack
        self.seed_law = seed_law
        self.ix = {s: i for i, s in enumerate(pack.names)}
        self.chain = {s: np.array([self.ix[f'{j}_{s}'] for j in ('hip', 'knee', 'ankle')]) for s in 'LR'}
        self.ids, self.small, self.marker = {}, {}, {}
        for side in 'LR':
            band = np.flatnonzero(pack.assign == self.chain[side][2])
            if not len(band):
                raise ValueError(f"empty ankle band {side}")
            ids = band[rest[band, 1] <= np.quantile(rest[band, 1], .10)]
            self.ids[side] = ids
            self.small[side] = replace(pack, assign=pack.assign[ids], weight=pack.weight[ids],
                                       joint2=pack.joint2[ids], weight2=pack.weight2[ids])
            self.marker[side] = rest[ids].mean(axis=0)
            axes = pack.axis[self.chain[side]]
            if np.max(abs(axes[:, 1:])) > 1e-12:
                raise ValueError("non-parasagittal axes: planar inverse is inapplicable")
            # Known-answer inverse control, not a gait angle choice: a flat
            # frame with signed h+k+b=0, forwarded by the imported mirror.
            fixture = np.array([.1, -.15, .05]) / axes[:, 0]
            theta = np.zeros(len(pack.names))
            theta[self.chain[side]] = fixture
            mats, trans = mirror.frames(pack, theta)
            ankle = self.chain[side][2]
            target = mats[ankle] @ self.marker[side] + trans[ankle]
            seeds = planar_seed(pack, self.chain[side], self.marker[side], target)
            inverse_errors = []
            for seed in seeds:
                theta[self.chain[side]] = seed
                mats, trans = mirror.frames(pack, theta)
                inverse_errors.append(np.linalg.norm(mats[ankle] @ self.marker[side]+trans[ankle]-target))
            assert inverse_errors and min(inverse_errors) < 1e-10, 'C5 reverse IK known-answer control'

    def points(self, theta, side):
        return mirror.pose_points(self.rest[self.ids[side]], self.small[side], theta)

    def endpoint(self, q, side):
        theta = np.zeros(len(self.pack.names))
        theta[self.chain[side]] = q
        return self.points(theta, side).mean(axis=0)

    def solve(self, target, side, previous):
        chain = self.chain[side]
        lo, hi = np.radians(self.pack.rom[chain]).T
        flat_seeds = planar_seed(self.pack, chain, self.marker[side], target)
        free_seeds, _ = free_frame_seeds(self.pack, chain, self.marker[side], target) if self.seed_law == 'free' else ([],0)
        seeds = [*flat_seeds, *free_seeds]
        fun = lambda q: self.endpoint(q, side)
        # A continuous previous solution plus BOTH analytic IK branches; not a
        # parameter sweep. No claim of global impossibility from a local miss.
        refine = bounded_refine if self.seed_law == 'free' else mirror.damped_ls
        candidates = [refine(fun, target, seed, lo, hi) for seed in [previous, *seeds]]
        accurate = [q for q in candidates if np.linalg.norm(fun(q)-target) <= IK_TOL]
        if self.seed_law == 'free' and accurate:
            # Once numerically solved, tiny residual differences are not a
            # reason to jump between redundant branches. Keep the closest pose.
            q = min(accurate,key=lambda q:np.linalg.norm(q-previous))
        else:
            q = min(candidates, key=lambda q: np.linalg.norm(fun(q)-target))
        return q, not bool(flat_seeds)


def gait_target(rig, side, t, o, swing):
    """Body-relative candidate targets; L/R separated by one stance interval."""
    phase = (t + (o.T if side == 'R' else 0)) % (2*o.T)
    target = rig.marker[side].copy()
    if phase < o.T:
        target[2] -= o.state(phase)[0]
    else:
        u = (phase-o.T)/o.T
        phi = float(np.interp(u*(len(swing)-1), np.arange(len(swing)), swing[:, 0]))
        alpha = math.asin(o.a/o.leg)
        target[2] += o.leg*math.sin(phi)
        target[1] += o.leg*(math.cos(phi)-math.cos(alpha))
    return target


def synchronized_side_control(o,rig,swing):
    """Same local phase and same initial warm starts: distinguish history
    from a genuine L/R spatial law difference. No live pack mutation.
    """
    previous = {s:np.zeros(3) for s in 'LR'}
    max_position_difference = max_angle_difference = 0.0
    for local in (0.,.25,.5,.75,1.,1.5,2.):
        achieved,angles = {},{}
        for side in 'LR':
            target = gait_target(rig,side,(local-(1 if side=='R' else 0))*o.T,o,swing)
            q,_ = rig.solve(target,side,previous[side]); previous[side] = q
            achieved[side] = rig.endpoint(q,side); angles[side] = q
        max_position_difference = max(max_position_difference,float(np.linalg.norm(achieved['L']*[-1,1,1]-achieved['R'])))
        max_angle_difference = max(max_angle_difference,float(np.max(abs(angles['L']-angles['R']))))
    assert max_position_difference < 1e-6, 'S4 synchronized spatial parity'
    return dict(position=max_position_difference,angle=max_angle_difference)


def rig_stride(o, rig, swing):
    # Mirror's 60 Hz measurement convention, rounded UP and exact boundaries.
    n = max(2, math.ceil(o.T*mirror.FPS))
    times = np.linspace(0, 2*o.T, 2*n+1)
    previous = {s: np.zeros(3) for s in 'LR'}
    errors, thetas, targets, misses, tilt = [], [], [], 0, []
    records = []
    min_bend = math.inf
    min_seed_count = math.inf
    max_seed_fk_error = 0.0
    max_full_error = 0.0
    for fi, t in enumerate(times):
        theta = np.zeros(len(rig.pack.names))
        desired = []
        for side in 'LR':
            target = gait_target(rig, side, t, o, swing)
            q, outside = rig.solve(target, side, previous[side])
            seeds,bend = free_frame_seeds(rig.pack,rig.chain[side],rig.marker[side],target)
            min_bend = min(min_bend,bend)
            min_seed_count = min(min_seed_count,len(seeds))
            for seed in seeds:
                tt = np.zeros(len(rig.pack.names)); tt[rig.chain[side]] = seed
                mats,trans = mirror.frames(rig.pack,tt)
                ankle = rig.chain[side][2]
                seed_error = np.linalg.norm(mats[ankle] @ rig.marker[side]+trans[ankle]-target)
                max_seed_fk_error = max(max_seed_fk_error,float(seed_error))
                assert seed_error <= IK_TOL, 'S1 free-frame seed FK parity'
            previous[side] = q
            theta[rig.chain[side]] = q
            desired.append(target)
            misses += int(outside)
            tilt.append(abs(float(q @ rig.pack.axis[rig.chain[side], 0])))
        # Both legs active together, including any second-owner dependencies.
        for si, side in enumerate('LR'):
            actual = rig.points(theta, side).mean(axis=0)
            error = float(np.linalg.norm(actual-desired[si]))
            errors.append(error)
            local = float(((t+(o.T if side=='R' else 0))%(2*o.T))/o.T)
            flat_miss = not bool(planar_seed(rig.pack,rig.chain[side],rig.marker[side],desired[si]))
            records.append(dict(error=error,side=side,phase=local,flat_miss=flat_miss,
                                q=theta[rig.chain[side]].tolist()))
        if fi in (0, n//2, n, 3*n//2, 2*n):
            full = mirror.pose_points(rig.rest, rig.pack, theta)
            for side in 'LR':
                max_full_error = max(max_full_error, float(np.max(abs(full[rig.ids[side]]-rig.points(theta, side)))))
        thetas.append(theta)
        targets.append(desired)
    assert max_full_error < 1e-10, ("C5 mirror subset parity", max_full_error)
    # Same command returns the same FK result; no incremental vertex rotation.
    th = np.array(thetas)
    endpoint_error = max(float(np.max(abs(rig.points(th[-1], s)-rig.points(th[0], s)))) for s in 'LR')
    target_loop_error = float(np.max(abs(np.array(targets[-1])-np.array(targets[0]))))
    assert target_loop_error < 1e-10, 'C6 target position closure'
    phase_errors = {}
    for side in 'LR':
        for category in ('swing','stance_flat_miss','stance_flat_seed'):
            selected = [r['error'] for r in records if r['side']==side and
                        (('swing' if r['phase']>=1 else ('stance_flat_miss' if r['flat_miss'] else 'stance_flat_seed'))==category)]
            phase_errors[side+'_'+category] = dict(count=len(selected),max=max(selected,default=0.),
                                                  rms=math.sqrt(float(np.mean(np.square(selected)))) if selected else 0.)
    return dict(max_error=max(errors), rms_error=math.sqrt(float(np.mean(np.square(errors)))),
                full_subset_error=max_full_error, flat_seed_unreachable=misses,
                max_full_frame_tilt=max(tilt), pose_loop_error=endpoint_error,
                samples=len(times), theta_loop_error=float(np.max(abs(th[-1]-th[0]))),
                target_loop_error=target_loop_error, max_sample_joint_jump=float(np.max(abs(np.diff(th,axis=0)))),
                free_seed_min_bend_rad=min_bend,free_seed_min_count=min_seed_count,
                free_seed_max_fk_error=max_seed_fk_error,phase_errors=phase_errors,
                worst_samples=sorted(records,key=lambda r:-r['error'])[:3])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--require-ready', action='store_true')
    ap.add_argument('--seed-law',choices=('flat','free'),default='free',help='flat retains the PR #5 ablation; free is the corrected inverse')
    args = ap.parse_args()
    if args.self_test:
        T, _, _ = candidate_clock(3.091285, math.sqrt(mirror.FR_WALK*mirror.G*3.091285))
        numerical_controls(Orbit(5.615640, 3.091285, T, math.sqrt(mirror.FR_WALK*mirror.G*3.091285)))
        print('analytic controls PASS (synthetic calibration; not a real-blob run)')
        return 0
    rest, indices = mirror.load_mesh(mirror.DEFAULT_MESH)
    pack = mirror.load_pack(mirror.DEFAULT_PACK)
    if pack.tag != b'JNT3':
        raise ValueError('requires the canonical JNT3 pack')
    pack,rom_rows = mirrored_rom(pack)
    gauge_error = rom_gauge_control(rest,pack)
    rig = Rig(rest, pack,args.seed_law)
    print(f'seed_law={args.seed_law} root_drop=0 skeleton_delta=0 rom_gauge_control_error={gauge_error:.3e}')
    for name,parity,old,new in rom_rows:
        if name.startswith(('hip','knee','ankle')):
            print(f'ROM {name} axial_parity={parity:+d} shipped={old.tolist()} recommended={new.tolist()}')
    com = rest.mean(axis=0)
    if len(indices) % 3 or np.max(indices) >= len(rest) or len(pack.assign) != len(rest):
        raise ValueError('invalid mesh/pack topology')
    print(f'pack_vertices={len(rest)} joints={len(pack.names)} triangles={len(indices)//3}; original_brief_triangles=36424 (nonbinding, repo wins)', flush=True)
    if not np.allclose(com, [-0.0002198713, 5.5961329890, 0.4057449222], rtol=0, atol=5e-10):
        raise ValueError(f'binding COM mismatch: {com}')
    h = float(rest[:, 1].mean()-rest[:, 1].min())
    leg = float(np.mean([np.linalg.norm(pack.pivot[c[2]]-pack.pivot[c[0]]) for c in rig.chain.values()]))
    if abs(h-5.615640) > .0000005 or abs(leg-3.091285) > .0000005:
        raise ValueError(f'binding calibration mismatch H={h} leg={leg}')
    # Reuse the mirror's speed reference; do NOT call its diagnostic clock.
    speed = math.sqrt(mirror.FR_WALK*mirror.G*leg)
    T, iterations, residual = candidate_clock(leg, speed)
    o = Orbit(h, leg, T, speed)
    swing, return_error = swing_samples(o)
    assert residual < CLOCK_TOL and return_error < 1e-7, 'C4 surrogate clock'
    flow_error, cp, cp_d, hybrid_d, j = numerical_controls(o)
    print(f'calibration H_com={h:.9f} leg={leg:.9f} omega={o.w:.9f}', flush=True)
    print(f'clock_candidate T_stance=T_swing={T:.9f} stride={2*T:.9f} cadence_hz={1/T:.9f} step_length={2*o.a:.9f}')
    print(f'clock_loop_iterations={iterations} clock_loop_residual={residual:.3e}s independent_swing_return_residual={return_error:.3e}s')
    cap_T = capture_clock_limit(h, leg, speed, T)
    print(f'cp_only_10pct_capture_T_max={cap_T:.9f}s required_swing_period_at_bound={swing_period(cap_T,leg,speed):.9f}s '
          f'coupling_gap_at_capture_bound={swing_period(cap_T,leg,speed)-cap_T:.9f}s')
    print('clock_status=CONDITIONAL point-pendulum, fixed hip; physical stride clock=UNIDENTIFIED')
    print(f'boundary_velocity={o.vb:.9f} midpoint_velocity={o.vc:.9f} orbital_energy={o.energy:.9f}')
    print(f'first_step_impulse_per_mass={o.vc:.9f} wu/s at x=0; first_contact_time={T/2:.9f}s')
    print(f'stable_manifold_startup_impulse_per_mass={o.w*o.xi0:.9f} wu/s; nominal_first_contact_time={T:.9f}s')
    print(f'controlled_lean_for_stable_manifold_x={o.xi0:.9f} wu geometric_angle={math.atan(o.xi0/h):.9f}rad')
    print('first_step_total_impulse=UNKNOWN (mass missing); impulse_budget=UNKNOWN; passive_lean_only_exact_E_entry=IMPOSSIBLE')
    print(f'flow_rk4_residual={flow_error:.3e} deadbeat_cp_convergence_steps=1 deadbeat_full_state_with_impulse_steps=1')
    print(f'cp_only_full_state_error_after_one={np.linalg.norm((cp-[-o.a,o.vb])*[1,1/o.w]):.9f} (NOT full-state deadbeat)')
    print(f'10pct_velocity hybrid_placement={hybrid_d:.9f} signed_impulse_per_mass={j:.9f} cp_only_placement={cp_d:.9f}')
    for label, reset in (('cp_only', cp_reset), ('two_step', two_step_reset), ('hybrid', hybrid_reset)):
        state = np.array([-o.a, 1.1*o.vb])
        for k in range(4):
            pre = o.flow(*state, T)
            post, displacement, impulse = reset(o, state)
            error = float(np.max(abs((post-[-o.a,o.vb])*[1,1/o.w])))
            print(f'perturbed_controller={label} step={k} d={displacement:.9f} '
                  f'placement_margin_optimistic={2*leg-abs(displacement):.9f} '
                  f'J_over_m={impulse:.9f} xi_error={abs(o.xi(post)-o.xi0):.3e} '
                  f'full_state_error={error:.3e} E_before={o.E(pre):.9f} E_after={o.E(post):.9f}')
            state = post
    print('capture intervals: scheduled [0,step_length]; optimistic reach [-2*leg,+2*leg], NOT certified FK reach')
    for k in range(4):
        phase_margins = [capture_margin(o.xi(o.state(t)), o.T-t, o.w, -2*leg, 2*leg) for t in np.linspace(0,T,33)]
        m = capture_margin(o.xi0, T, o.w, 0, 2*o.a)
        print(f'step={k} next_support={(k+1)*2*o.a:.9f} stopping_margin_scheduled={m:.9f} stopping_margin_optimistic_min={min(phase_margins):.9f} continuing_placement_margin={2*leg-2*o.a:.9f}')
    print(f'first_halfstep_optimistic_stopping_margin={capture_margin(o.vc/o.w,T/2,o.w,-2*leg,2*leg):.9f}')
    print(f'minimum_LIPM_stance_friction_coefficient={o.a/o.h:.9f} (availability unknown)')
    result = rig_stride(o, rig, swing)
    print('synchronized_LR_control='+repr(synchronized_side_control(o,rig,swing)))
    eps = FOOT_FRACTION*h
    print('rig_result=' + repr(result))
    print(f'foot_error_max={result["max_error"]:.12g} foot_error_rms={result["rms_error"]:.12g} threshold={eps:.9f} wu')
    print(f'foot_tracking_gate={"PASS" if result["max_error"] <= eps else "FAIL"}')
    print('exact_Rodrigues_substeps=1; accumulated_small_angle_drift=0 (algebraic, excludes float roundoff)')
    print('substeps_for_total_stride_0.5pctH=' + ('UNATTAINABLE_FOR_RECORDED_PROFILE' if result['max_error'] > eps else 'NOT_CERTIFIED_CONTINUOUSLY') + '; finer timing cannot fix the same erroneous sampled poses')
    # At transfer the passive relative swing velocity is zero whereas planted
    # contact requires -vb. This falsifies the full coupled ballistic closure.
    print(f'swing_stance_velocity_jump={o.vb:.9f} wu/s; startup_swing_time_deficit={T/2:.9f}s')
    print(f'missing_moving_hip_forcing_at_toeoff={o.w**2*o.a*math.cos(math.asin(o.a/leg))/leg:.9f} rad/s^2')
    print('full_clock_loop_residual=UNDEFINED: surrogate return passes, coupled FK/contact swing has not closed')
    print('integration_gate=CLOSED: actuator/impact budget absent; ballistic contact/startup closure falsified; lateral balance uncertified')
    print('No fallback cadence, engine writes, or changed blob data. See docs/THE_CAPTURE_LAW.md.')
    return 2 if args.require_ready else 0


if __name__ == '__main__':
    raise SystemExit(main())
