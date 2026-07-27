"""planner.py — WHERE DOES THE NEXT CONTACT GO? (THE_BODY.md §4)

    "Everything is like a mountain climber even when walking on two feet... all we'd have to do is
     calculate getting up and then calculate what is the FIRST STEP, because that's all we ever
     need -- we repeat it... It happens instantaneously. There's no training on the spot."
                                                                    -- the operator, 2026-07-26

This is the half of movement that needs NO TRAINING. It enumerates where a limb could go, scores
each against six limits that are all measurable physics, and picks. Walking, climbing and getting
up are the same loop with different contact sets and different costs.

    RECEDING HORIZON. Plan one contact, execute it, THROW THE PLAN AWAY, re-plan. Never plan the
    route; plan the step. That is what makes it cheap enough to run every tick.

    THE SIX LIMITS replace the industry's hard-coded "slopes over 45 degrees are unclimbable" --
    and tan(45 deg) = 1.0 exactly, so that constant was always a claim about friction (mu = 1.0)
    that nobody wrote down and everybody then applied to ice and gravel alike.

      slip          tan(theta) > mu                 the friction cone
      collapse      theta > angle of repose         loose ground will not hold the slope
      reach         beyond the limb's length        geometry
      topple        COM leaves the support polygon  what is left holding you up while this limb moves
      strength      required moment > muscles make   the body's own torque limits
      not worth it  cost of transport                energy

    THE NODE BUDGET IS A CHARACTER STAT (§4.8), and it obeys the rule that keeps stats honest:
    a stat may change the BODY or the DECISION, never the PHYSICS. A clumsy character and an expert
    meet the same mu on the same rock. The expert just looks at more options.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field as dfield
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fields import Coupling, ROCK, REGOLITH                                  # noqa: E402


# Angle of repose: the steepest a loose material will hold. 40.03 deg for lunar regolith is not a
# guess -- core/trainables/granular.py MEASURED it as an emergent property of a grain pile.
REPOSE = {'rock': np.pi, 'regolith': np.radians(40.03), 'sand': np.radians(34.0),
          'ice': np.pi, 'scree': np.radians(37.0)}
FRICTION = {'rock': 0.90, 'regolith': 0.60, 'sand': 0.55, 'ice': 0.10, 'scree': 0.50}


@dataclass
class Terrain:
    """What the planner is allowed to ask the ground. Deliberately small: a height, a normal, and
    what it is made of. Anything more and the planner starts depending on level metadata."""
    kind: str = 'flat'
    material: str = 'rock'
    slope_deg: float = 0.0
    step_height: float = 0.0
    step_at: float = 1.0
    boulders: list = dfield(default_factory=list)      # [(x, y, radius, height)]
    # MATERIAL VARIES ACROSS THE GROUND, and that is not decoration -- a patch of dry rock on an
    # ice field is the difference between a route and no route, and it is invisible to any test
    # that asks only about SHAPE. [(x, y, radius, material)]
    patches: list = dfield(default_factory=list)

    def height_at(self, x: float, y: float) -> float:
        h = 0.0
        if self.kind in ('slope', 'ramp'):
            h += x * np.tan(np.radians(self.slope_deg))
        if self.kind == 'step' and x > self.step_at:
            h += self.step_height
        for (bx, by, r, bh) in self.boulders:
            d = np.hypot(x - bx, y - by)
            if d < r:
                h += bh * np.sqrt(max(0.0, 1.0 - (d / r) ** 2))
        return float(h)

    def height_many(self, X, Y):
        """Height for a whole candidate sweep at once. The per-point version walked a Python loop
        over boulders and patches for EVERY sample, so a 96-candidate sweep paid that ~500 times
        once normals are counted. Same arithmetic, one pass."""
        X = np.asarray(X, float); Y = np.asarray(Y, float)
        h = np.zeros_like(X)
        if self.kind in ('slope', 'ramp'):
            h = h + X * np.tan(np.radians(self.slope_deg))
        if self.kind == 'step':
            h = h + np.where(X > self.step_at, self.step_height, 0.0)
        for (bx, by, r, bh) in self.boulders:
            d = np.hypot(X - bx, Y - by)
            h = h + np.where(d < r, bh * np.sqrt(np.maximum(0.0, 1.0 - (d / r) ** 2)), 0.0)
        return h

    def slope_many(self, X, Y, eps: float = 0.02):
        X = np.asarray(X, float); Y = np.asarray(Y, float)
        dzdx = (self.height_many(X + eps, Y) - self.height_many(X - eps, Y)) / (2 * eps)
        dzdy = (self.height_many(X, Y + eps) - self.height_many(X, Y - eps)) / (2 * eps)
        nz = 1.0 / np.sqrt(dzdx ** 2 + dzdy ** 2 + 1.0)
        return np.arccos(np.clip(nz, -1.0, 1.0)), np.stack([-dzdx * nz, -dzdy * nz, nz], axis=-1)

    def mu_many(self, X, Y):
        X = np.asarray(X, float); Y = np.asarray(Y, float)
        mu = np.full(X.shape, FRICTION.get(self.material, 0.7))
        rep = np.full(X.shape, REPOSE.get(self.material, np.pi))
        for (px, py, r, mat) in self.patches:
            inside = np.hypot(X - px, Y - py) <= r
            mu = np.where(inside, FRICTION.get(mat, 0.7), mu)
            rep = np.where(inside, REPOSE.get(mat, np.pi), rep)
        return mu, rep

    def normal_at(self, x: float, y: float, eps: float = 0.02) -> np.ndarray:
        dzdx = (self.height_at(x + eps, y) - self.height_at(x - eps, y)) / (2 * eps)
        dzdy = (self.height_at(x, y + eps) - self.height_at(x, y - eps)) / (2 * eps)
        n = np.array([-dzdx, -dzdy, 1.0])
        return n / np.linalg.norm(n)

    def slope_at(self, x: float, y: float) -> float:
        """Local slope angle in radians -- what both the friction cone and repose are read against."""
        return float(np.arccos(np.clip(self.normal_at(x, y)[2], -1.0, 1.0)))

    def material_at(self, x: float, y: float) -> str:
        for (px, py, r, mat) in self.patches:
            if np.hypot(x - px, y - py) <= r:
                return mat
        return self.material

    def mu_at(self, x: float, y: float) -> float:
        return FRICTION.get(self.material_at(x, y), 0.7)

    def repose_at(self, x: float, y: float) -> float:
        return REPOSE.get(self.material_at(x, y), np.pi)


@dataclass
class Candidate:
    """One place a limb could go, and everything the planner concluded about it."""
    limb: str
    point: np.ndarray
    normal: np.ndarray
    slope: float
    feasible: bool = True
    refused_by: str = ''
    cost: float = 0.0
    progress: float = 0.0

    def __repr__(self):
        tag = 'OK ' if self.feasible else f'NO({self.refused_by})'
        return (f"<{self.limb} at ({self.point[0]:+.2f},{self.point[1]:+.2f},{self.point[2]:+.2f}) "
                f"slope {np.degrees(self.slope):4.1f} {tag} cost {self.cost:.3f}>")


@dataclass
class Stance:
    """Where the body is: which limbs are down, and where its centre of mass is.

    Deliberately NOT the full physics state -- the planner reasons about CONTACTS and a COM, which
    is all six limits need. Keeping it this small is what lets the planner run without a simulator.
    """
    com: np.ndarray
    contacts: dict                                     # limb name -> world point
    hip: dict = dfield(default_factory=dict)           # limb name -> where that limb hangs from
    reach: dict = dfield(default_factory=dict)         # limb name -> max distance from its hip
    mass: float = 70.0
    max_hip_torque: float = 200.0

    def support_points(self, lifting: str = None) -> list:
        return [p for k, p in self.contacts.items() if k != lifting]


@dataclass
class Planner:
    """Enumerate, score, pick. No training, no simulator, no search deeper than the budget allows."""
    terrain: Terrain
    up: np.ndarray = dfield(default_factory=lambda: np.array([0.0, 0.0, 1.0]))
    gravity: float = 9.80665
    node_budget: int = 96              # THE CHARACTER STAT. More options looked at, not more luck.
    n_dirs: int = 8
    n_dists: int = 6
    blocked: dict = dfield(default_factory=dict)       # (limb, rounded point) -> ticks remaining

    # ── enumerate ────────────────────────────────────────────────────────────────────────────
    def candidates(self, st: Stance, limb: str, goal_dir=None) -> list:
        """Sample the annulus this limb can reach. Sampling, not solving: the feasibility test is
        cheap enough that generate-and-check beats trying to characterise the reachable set."""
        hip = st.hip.get(limb, st.com)
        reach = st.reach.get(limb, 0.9)
        # THE REACHABLE GROUND IS A CIRCLE OF RADIUS sqrt(L^2 - h^2), NOT OF RADIUS L. I sampled at
        # a horizontal radius up to the leg's length and then measured 3D distance from a hip 0.9 m
        # up with a 0.85 m leg -- so nothing could reach the floor and every candidate was refused.
        # The geometry also says something true: a FULLY EXTENDED standing leg can barely step at
        # all, which is why walking bends the stance leg. That is an outcome, not an assertion.
        ground_h = self.terrain.height_at(float(hip[0]), float(hip[1]))
        h = max(0.0, float(hip[2]) - ground_h)
        r_max = float(np.sqrt(max(0.0, reach * reach - h * h)))
        if r_max < 1e-3:
            return []                                   # standing bolt upright: no step available
        # BUDGET BUYS RESOLUTION IN BOTH AXES. Scaling only the distance samples left the angular
        # sweep fixed at 8, so a bigger budget could not FIND a foothold a smaller one missed -- it
        # only refined one it had already found. On easy ground that is worth almost nothing and on
        # hard ground it is worth everything, which is the whole point of the stat.
        n_d = int(np.clip(round(np.sqrt(self.node_budget / 1.4)), 2, self.n_dists))
        n_dirs = int(np.clip(self.node_budget // max(1, n_d), 4, 40))
        # ONE SWEEP, NOT A LOOP. Every candidate's position, height, slope and normal comes out
        # of a handful of array ops instead of ~500 scalar terrain calls.
        bias = np.arctan2(goal_dir[1], goal_dir[0]) if goal_dir is not None else 0.0
        A = 2 * np.pi * np.arange(n_dirs) / n_dirs + bias
        R = r_max * (0.25 + 0.72 * np.arange(n_d) / max(1, n_d - 1))
        AA, RR = np.meshgrid(A, R, indexing='ij')
        X = (hip[0] + RR * np.cos(AA)).ravel()[:self.node_budget]
        Y = (hip[1] + RR * np.sin(AA)).ravel()[:self.node_budget]
        Z = self.terrain.height_many(X, Y)
        SL, NR = self.terrain.slope_many(X, Y)
        MU, REP = self.terrain.mu_many(X, Y)
        d3 = np.sqrt((X - hip[0]) ** 2 + (Y - hip[1]) ** 2 + (Z - hip[2]) ** 2)
        # the three PURELY LOCAL refusals, decided for the whole sweep at once
        bad = np.where(np.tan(SL) > MU, 'slip',
              np.where(SL > REP, 'collapse',
              np.where(d3 > reach, 'reach', '')))
        out = []
        for k in range(len(X)):
            c = Candidate(limb=limb, point=np.array([X[k], Y[k], Z[k]]),
                          normal=NR[k], slope=float(SL[k]))
            if bad[k]:
                c.feasible, c.refused_by = False, str(bad[k])
            out.append(c)
        return out

    # ── the six limits ───────────────────────────────────────────────────────────────────────
    def evaluate(self, st: Stance, c: Candidate, goal=None) -> Candidate:
        x, y = c.point[0], c.point[1]
        if not c.feasible:            # already refused by the vectorised sweep
            return c

        if self.blocked.get((c.limb, tuple(np.round(c.point, 2))), 0) > 0:
            c.feasible, c.refused_by = False, 'tried'
            return c

        mu = self.terrain.mu_at(x, y)
        if np.tan(c.slope) > mu:                        # THE FRICTION CONE
            c.feasible, c.refused_by = False, 'slip'
            return c

        if c.slope > self.terrain.repose_at(x, y):      # loose ground will not hold that slope
            c.feasible, c.refused_by = False, 'collapse'
            return c

        hip = st.hip.get(c.limb, st.com)
        d = float(np.linalg.norm(c.point - hip))
        if d > st.reach.get(c.limb, 0.9):
            c.feasible, c.refused_by = False, 'reach'
            return c

        # TOPPLE: while this limb swings, the others hold you. Is the COM over what is left?
        sup = st.support_points(lifting=c.limb)
        if not self._com_supported(st.com, sup):
            c.feasible, c.refused_by = False, 'topple'
            return c

        # STRENGTH: the further the COM sits from the support, the more moment the hip must make.
        lever = self._com_offset(st.com, sup)
        if st.mass * self.gravity * lever > st.max_hip_torque:
            c.feasible, c.refused_by = False, 'strength'
            return c

        # COST OF TRANSPORT: lifting costs mgh; travelling costs work against friction. Both are
        # energy, so preferred step length is an OUTCOME rather than a tuned number.
        rise = max(0.0, float(np.dot(c.point - hip, self.up)) + 0.9)
        c.cost = float(st.mass * self.gravity * rise * 0.02 + 0.5 * d * d)
        if goal is not None:
            g = np.asarray(goal, float) - st.com
            g = g - np.dot(g, self.up) * self.up
            n = np.linalg.norm(g)
            if n > 1e-9:
                step = c.point - hip
                c.progress = float(np.dot(step - np.dot(step, self.up) * self.up, g / n))
        return c

    def _com_supported(self, com, sup) -> bool:
        """Is the COM's shadow inside the polygon of the remaining contacts?

        One contact cannot support anything; two give a LINE, which is why a walking biped is
        never statically stable mid-step and why real walking is a controlled fall. The tolerance
        below is what makes single-support steps admissible at all.
        """
        if len(sup) == 0:
            return False
        pts = np.array([p - np.dot(p, self.up) * self.up for p in sup])
        c = com - np.dot(com, self.up) * self.up
        if len(sup) == 1:
            return bool(np.linalg.norm(c - pts[0]) < 0.25)
        if len(sup) == 2:
            a, b = pts[0], pts[1]
            ab = b - a
            t = float(np.clip(np.dot(c - a, ab) / (np.dot(ab, ab) + 1e-12), 0.0, 1.0))
            return bool(np.linalg.norm(c - (a + t * ab)) < 0.25)
        return bool(self._inside(c, pts))

    @staticmethod
    def _inside(c, pts) -> bool:
        ctr = pts.mean(axis=0)
        ang = np.argsort([np.arctan2(*(p - ctr)[[1, 0]]) for p in pts])
        poly = pts[ang]
        sign = 0
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            cr = np.cross(b - a, c - a)
            s = float(cr[2]) if np.ndim(cr) else float(cr)
            if abs(s) < 1e-12:
                continue
            if sign == 0:
                sign = np.sign(s)
            elif np.sign(s) != sign:
                return False
        return True

    def _com_offset(self, com, sup) -> float:
        if not sup:
            return 1e9
        pts = np.array([p - np.dot(p, self.up) * self.up for p in sup])
        c = com - np.dot(com, self.up) * self.up
        return float(np.linalg.norm(c - pts.mean(axis=0)))

    # ── decide ───────────────────────────────────────────────────────────────────────────────
    def plan(self, st: Stance, limbs, goal=None, mode='walk') -> tuple:
        """Best next contact over the given limbs. Returns (choice, all_scored)."""
        goal_dir = None
        if goal is not None:
            g = np.asarray(goal, float) - st.com
            g = g - np.dot(g, self.up) * self.up
            if np.linalg.norm(g) > 1e-9:
                goal_dir = g / np.linalg.norm(g)
        scored = []
        share = max(8, self.node_budget // max(1, len(limbs)))
        for limb in limbs:
            saved, self.node_budget = self.node_budget, share
            for c in self.candidates(st, limb, goal_dir):
                scored.append(self.evaluate(st, c, goal))
            self.node_budget = saved
        ok = [c for c in scored if c.feasible]
        if not ok:
            return None, scored
        if mode == 'rise':                              # GET UP: buy height, not distance
            best = max(ok, key=lambda c: float(np.dot(c.point, self.up)) - 0.4 * c.cost)
        else:                                           # WALK: buy progress per unit energy
            best = max(ok, key=lambda c: c.progress - 0.25 * c.cost)
        return best, scored

    # ── the runtime memory that makes it look like it is thinking ────────────────────────────
    def mark_failed(self, c: Candidate, ticks: int = 120) -> None:
        """The controller could not reach it. Remember for a moment, then forget.

        PER-SITUATION, not per-policy: the character remembers that THIS rock defeated it for the
        next couple of seconds. It does not rewrite what it knows how to do. That is the whole
        cost of "try, fail, route around", and it is why the search looks like intelligence."""
        self.blocked[(c.limb, tuple(np.round(c.point, 2)))] = ticks

    def tick(self) -> None:
        for k in list(self.blocked):
            self.blocked[k] -= 1
            if self.blocked[k] <= 0:
                del self.blocked[k]
