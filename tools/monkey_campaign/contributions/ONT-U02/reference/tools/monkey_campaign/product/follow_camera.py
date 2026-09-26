"""The U02 follow camera: a Python-side camera controller over the engine's
frozen HTTP contract.

Architecture law (AGENTS.md, this worktree): the C++ Vulkan engine is a FROZEN
SERVICE consumed only through its HTTP routes; this module writes ZERO C++ and
issues ZERO body-touching commands. Frozen preregistration:
`tools/monkey_campaign/agents/U02_camera/PREREGISTRATION.md` (Amendments 1-2
included); contract discovery with citations:
`tools/monkey_campaign/agents/U02_camera/discovery_note.md`.

Contract surface (verified at base 33e7a444, HEAD 8feea42a):
- Write: exactly ONE route -- `POST /camera` with ALL 8 fields
  (cam_radius, cam_theta, cam_phi, pan_x, pan_y, target_x, target_y, target_z).
  Omitted fields DEFAULT engine-side (12/0/0.3/0/0/0/0/0), so a partial POST
  resets the rest -- this module always sends all 8. Pan is frozen at 0.
- Reads: `GET /joints` (rig rest centers J + parents + live thetas),
  `GET /scene` (body-row mesh extent `r=`), `POST /project` (apply echo),
  `GET /frame` (freshness harness only -- the module itself never pulls frames).
- Never: /membrane, /mesh_bin, /joints_bin, /joints POST, /hinge_bin, /gait*,
  /stride*, /pose_apply, /tick_*, /matter, /skin_bin, /volp_bin, /scene POST,
  /cameras POST, /ui_click, /water_vis, /eye_bin, or anything else that could
  move, re-pose, or re-load the animal. THE CAMERA NEVER MOVES THE ANIMAL.

Engine laws replicated here (citations in the discovery note):
  eye = target + R*[cos(phi)*sin(theta), sin(phi), -cos(phi)*cos(theta)] + pan
  up  = [-sin(phi)*sin(theta), cos(phi), sin(phi)*cos(theta)]
  vertical FOV 45 deg (tan_half = 0.41421356); engine radius floor
  max(1.0, 1.02*mesh_sphere); right-handed Y-up metres, ground plane y=0.

stdlib only. Python 3.11+.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Frozen constants (PREREGISTRATION.md; each cites its law there)
# ---------------------------------------------------------------------------

TAN_HALF_FOV = 0.41421356          # tan(45 deg / 2) -- engine.cpp:3280
HALF_FOV = math.atan(TAN_HALF_FOV)  # 22.5 deg, rad
SAFE_K = 0.8                        # feet-in-frame safe fraction of the half-FOV
FIT_MARGIN = 1.05                   # the engine's own fit margin (engine.cpp:3246)
R_MAX = 40.0                        # scene bound: F01 clearing full extent 2 x 20 m
PHI_MAX_GROUND = SAFE_K * (math.pi / 8.0)   # 0.8 x 22.5 deg -- feet stay framed
PHI_CAP = math.pi / 2.0 - HALF_FOV  # 67.5 deg: last elevation with ground in frame
H_EYE_MIN = 0.5                     # m = 2 x F01 body envelope (0.25 m)
MARGIN_CAM = 0.25                   # m = one F01 body envelope clearance (EYE)
MARGIN_RAY = 0.02                   # m = optical clearance (LOOK-RAY only,
                                    # Amendment 4.1)
HEIGHT_STEPS = 64                   # height-law scan resolution (Amendment 4.3)
V_CAM_FLOOR = 0.05                  # m/s settling floor = 2 envelopes / s
TAU_DEFAULT = 0.30                  # s = 6 x the 20 Hz command interval (C12 seam)
TICK_PERIOD = 0.05                  # s = the existing 20 Hz seam
DEADBAND_R = 0.0025                 # fraction of R (~0.3% screen height)
DEADBAND_ANG = 0.005                # rad (~0.5% of R target shift)
DEADBAND_T = 0.01                   # m (2% of the body-envelope diameter)
CUT_FACTOR = 2.0                    # snap when |anchor - smoothed| > 2 x shot radius
TRUNK_EXIT_HYST = 0.5               # m = 2 x F01 body envelope
AVOID_EXIT_HYST = 0.25              # m = one F01 body envelope
ORBIT_STEP = HALF_FOV               # 22.5 deg -- each step is a genuinely new sight-line
ORBIT_SWEEP_MAX = math.pi / 2.0     # +-90 deg total; beyond that follow semantics die
STEPPEN_STEP = HALF_FOV / 2.0       # 11.25 deg elevation sweep step
TRUNK_MIN_R = 0.25                  # m = half F01's trunk footprint bound (0.5):
                                    # posts (r ~ 0.12) are never "the trunk"
                                    # (Amendment 5 designation law)

DEFAULT_BOOKMARK = "u02_follow"     # retained for report naming only (no bookmarks)

# The command stream the invariant is proven on. TICK allowlist = exactly what
# the module issues; verify_apply()/tests may add POST /project + GET /frame.
ALLOWED_ROUTES = frozenset({
    ("GET", "/joints"), ("GET", "/scene"), ("GET", "/state"),
    ("GET", "/cameras"), ("GET", "/frame"),
    ("POST", "/project"), ("POST", "/camera"),
})
FORBIDDEN_PATHS = frozenset({
    "/membrane", "/mesh_bin", "/joints_bin", "/hinge_bin", "/gait", "/gait_bin",
    "/stride", "/stride_bin", "/pose_apply", "/matter", "/skin_bin",
    "/volp_bin", "/ui_click", "/water_vis", "/eye_bin",
})


class CameraConfigError(ValueError):
    """Strict intake: a frozen-law violation at construction or bind time."""


# ---------------------------------------------------------------------------
# Small vector helpers (3-tuples of float; no third-party deps)
# ---------------------------------------------------------------------------


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a):
    return math.sqrt(_dot(a, a))


def _dist(a, b):
    return _norm(_sub(a, b))


def _dist2(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


# ---------------------------------------------------------------------------
# Engine laws, replicated (the ONLY place in this module allowed to know them)
# ---------------------------------------------------------------------------


def engine_eye(v):
    """Eye position for camera state v = [R, th, ph, tx, ty, tz, px, py].
    Law: engine.cpp:6730-6736 (verified at 33e7a444)."""
    r, th, ph = v[0], v[1], v[2]
    c, s = math.cos(ph), math.sin(ph)
    cx, sx = math.cos(th), math.sin(th)
    return (v[3] + r * c * sx + v[6],
            v[4] + r * s + v[7],
            v[5] - r * c * cx)


def subtend_deg_from_axis(eye, target, point):
    """Angle between the view axis (eye->target) and eye->point, radians.
    The anchor is IN the frame iff this is < HALF_FOV (prereg falsifier FE)."""
    axis = _sub(target, eye)
    to_pt = _sub(point, eye)
    na, np_ = _norm(axis), _norm(to_pt)
    if na <= 0.0 or np_ <= 0.0:
        return 0.0
    c = max(-1.0, min(1.0, _dot(axis, to_pt) / (na * np_)))
    return math.acos(c)


# ---------------------------------------------------------------------------
# The declared obstacle model (vertical cylinders; the engine exposes NO
# obstacle geometry over HTTP -- discovery note section 3/6 -- so obstacles are
# INJECTED, never discovered; an unmodeled obstacle can still occlude)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Cylinder:
    """Vertical cylinder, base on the ground plane y=0 (declared model)."""
    cx: float
    cz: float
    r: float
    top: float

    def __post_init__(self):
        if not all(map(math.isfinite, (self.cx, self.cz, self.r, self.top))):
            raise CameraConfigError("non-finite cylinder")
        if self.r <= 0.0 or self.top <= 0.0:
            raise CameraConfigError("cylinder r/top must be positive")


def _segment_hits_disk_2d(p0, p1, cyl, margin):
    """2D (xz) intersection of segment p0->p1 with the margin-expanded disk.
    Returns (t0, t1) parameters or None."""
    dx, dz = p1[0] - p0[0], p1[2] - p0[2]
    fx, fz = p0[0] - cyl.cx, p0[2] - cyl.cz
    a = dx * dx + dz * dz
    b = 2.0 * (fx * dx + fz * dz)
    c = fx * fx + fz * fz - (cyl.r + margin) ** 2
    if a <= 1e-12:                       # degenerate segment: a point
        if c <= 0.0:
            return (0.0, 0.0)
        return None
    disc = b * b - 4.0 * a * c
    if disc <= 0.0:
        return None
    sq = math.sqrt(disc)
    t0 = (-b - sq) / (2.0 * a)
    t1 = (-b + sq) / (2.0 * a)
    lo, hi = max(0.0, t0), min(1.0, t1)
    if lo > hi:
        return None
    return (lo, hi)


def point_clear(eye, cyl, margin=MARGIN_CAM):
    """The EYE is clear of the cylinder (outside, with margin, height-aware)."""
    if eye[1] >= cyl.top + margin:
        return True
    return _dist2(eye, (cyl.cx, eye[1], cyl.cz)) >= cyl.r + margin


def ray_clear(eye, target, cyl, margin=MARGIN_RAY):
    """The LOOK-RAY (eye->target) is clear of the height-aware cylinder.
    The ray carries the OPTICAL margin only; the camera-body margin applies to
    the eye (Amendment 4.1)."""
    hit = _segment_hits_disk_2d(eye, target, cyl, margin)
    if hit is None:
        return True
    t0, t1 = hit
    # y is linear in t; the ray is blocked iff it passes below top+margin
    # anywhere inside the 2D hit interval -> check the interval's y minimum.
    y0, y1 = eye[1], target[1]
    y_lo = min(y0 + t0 * (y1 - y0), y0 + t1 * (y1 - y0))
    return y_lo >= cyl.top + margin


def pose_clear(eye, target, obstacles):
    """Full pose check: eye at the camera-body margin, ray at the optical
    margin (Amendment 4.1)."""
    return (all(point_clear(eye, o, MARGIN_CAM) for o in obstacles)
            and all(ray_clear(eye, target, o, MARGIN_RAY) for o in obstacles))


# ---------------------------------------------------------------------------
# Anchor providers (the animal state source is injected; the engine exposes no
# root-motion route today -- discovery note section 3 -- so the rig envelope
# center is the default anchor and any future root source slots in here)
# ---------------------------------------------------------------------------


@dataclass
class AnchorReading:
    point: tuple            # (x, y, z) world anchor
    heading: tuple | None   # unit (hx, hz) horizontal heading, or None
    ts: float               # provider timestamp (monotonic)


class StaticAnchorProvider:
    """A fixed anchor (in-place stride demos; deterministic tests). `extent`
    carries the rig envelope radius when known (the tests pin it to the same
    joints the mock engine serves)."""

    def __init__(self, point, extent=0.0):
        self.point = tuple(float(c) for c in point)
        self.extent = float(extent)
        if not all(map(math.isfinite, self.point)):
            raise CameraConfigError("non-finite anchor")
        if not math.isfinite(self.extent) or self.extent < 0.0:
            raise CameraConfigError("bad extent")

    def read(self):
        return AnchorReading(self.point, None, time.monotonic())


class CallableAnchorProvider:
    """Adapts `f(now) -> (point, heading|None)` -- e.g. a walker-state reader."""

    def __init__(self, fn):
        self.fn = fn

    def read(self):
        p, h = self.fn(time.monotonic())
        return AnchorReading(tuple(float(c) for c in p), h, time.monotonic())


class EngineRigProvider:
    """Reads the animal state through the contract: GET /joints for the rig
    (envelope center = anchor), GET /scene once for the mesh extent `r=`.
    `client` is any object with get(path) -> (status, bytes, content_type),
    matching tools/product_viewer/server.py::EngineClient."""

    def __init__(self, client):
        self.client = client
        self.mesh_r = 1.0       # engine absolute floor if /scene says nothing
        self._extent = None     # envelope radius (recomputed per read)

    def _get_json(self, path):
        import json
        st, body, _ = self.client.get(path)
        if st != 200:
            raise CameraConfigError(f"{path} http {st}")
        return json.loads(body.decode("utf-8", "replace"))

    def bind(self):
        scene = self._get_json("/scene")
        for row in scene.get("rows", []):
            if row.get("id") == "body":
                detail = str(row.get("detail", ""))
                if "r=" in detail:
                    try:
                        self.mesh_r = float(detail.split("r=")[-1].rstrip(", "))
                    except ValueError:
                        pass
        doc = self._get_json("/joints")
        if not doc.get("loaded") or not doc.get("joints"):
            raise CameraConfigError("no joints pack loaded (GET /joints)")
        return doc

    def read(self):
        import json
        doc = self._get_json("/joints")
        joints = doc.get("joints") or []
        if not joints:
            raise CameraConfigError("GET /joints returned no joints")
        pts = [(float(j["J"][0]), float(j["J"][1]), float(j["J"][2]))
               for j in joints]
        c = tuple(sum(p[k] for p in pts) / len(pts) for k in range(3))
        self._extent = max(_dist(p, c) for p in pts)
        return AnchorReading(c, None, time.monotonic())

    @property
    def extent(self):
        return self._extent if self._extent is not None else 0.0


# ---------------------------------------------------------------------------
# RecordingClient: wraps any engine client (e.g.
# tools/product_viewer/server.py::EngineClient) and records the command
# stream -- the object the NEVER-moves-the-animal invariant is PROVEN on.
# ---------------------------------------------------------------------------


class RecordingClient:
    """Delegates get()/post_json()/post_raw() verbatim and records every
    (method, path, payload_or_None). Provides the invariant queries."""

    def __init__(self, inner):
        self.inner = inner
        self.log = []                      # list of (method, path, payload)

    def _record(self, method, path, payload=None):
        self.log.append((method, path.split("?")[0], payload))

    def get(self, path):
        self._record("GET", path)
        return self.inner.get(path)

    def post_json(self, path, payload, timeout=None):
        self._record("POST", path, payload)
        return self.inner.post_json(path, payload, timeout=timeout)

    def post_raw(self, path, body, ctype="application/octet-stream",
                 timeout=None):
        self._record("POST", path, f"<{len(body)} raw bytes>")
        return self.inner.post_raw(path, body, ctype=ctype, timeout=timeout)

    # -- invariant queries ----------------------------------------------------

    def allowlist_violations(self):
        return [e for e in self.log if (e[0], e[1]) not in ALLOWED_ROUTES]

    def forbidden_hits(self):
        hits = []
        for method, path, _payload in self.log:
            if path in FORBIDDEN_PATHS or path.startswith("/tick"):
                hits.append((method, path))
        return hits

    def camera_writes(self):
        return [payload for m, p, payload in self.log
                if (m, p) == ("POST", "/camera")]


# ---------------------------------------------------------------------------
# The follow-camera controller
# ---------------------------------------------------------------------------


@dataclass
class TickReport:
    t_state: float = 0.0        # t0 monotonic: state read start
    t_anchor: float = 0.0       # t1: anchor computed
    t_solution: float = 0.0     # t2: camera solution computed
    t_acked: float = 0.0        # t3: POST /camera acked
    mode: str = "ground"        # ground | trunk
    commanded_v: tuple = ()     # the 8 floats sent
    wrote: bool = False         # False = deadband suppressed the write
    cut: bool = False           # a declared snap (teleport-scale anchor jump)
    degraded: bool = False
    degrade_reason: str = ""
    hint: str = ""              # e.g. "low_eye" (Amendment 1 priority law)
    anchor: tuple = ()
    v_animal: float = 0.0       # measured animal speed this tick, m/s
    avoidance: dict = field(default_factory=dict)


class FollowCamera:
    """Smooth follow camera: ground mode + trunk-approach mode + declared
    obstruction avoidance. NEVER issues a body-touching command."""

    def __init__(self, client, anchor_provider, obstacles=(),
                 tick_period=TICK_PERIOD, tau=TAU_DEFAULT,
                 mesh_r=None, heading_enabled=True):
        self.client = client
        self.provider = anchor_provider
        obs = tuple(obstacles)
        for o in obs:
            if not isinstance(o, Cylinder):
                raise CameraConfigError("obstacles must be Cylinder instances")
        self.obstacles = obs
        if tick_period <= 0.0 or tau <= 0.0:
            raise CameraConfigError("tick_period/tau must be positive")
        self.tick_period = float(tick_period)
        self.tau = float(tau)
        self.heading_enabled = bool(heading_enabled)

        # subject size: injected, or taken from an EngineRigProvider
        if mesh_r is not None:
            self.mesh_r = float(mesh_r)
        elif isinstance(anchor_provider, EngineRigProvider):
            self.mesh_r = anchor_provider.mesh_r
        else:
            self.mesh_r = 1.0
        if self.mesh_r <= 0.0 or not math.isfinite(self.mesh_r):
            raise CameraConfigError("mesh_r must be positive finite")

        self._trunk = self._select_trunk()   # the largest cylinder, or None
        self._smoothed = None                # smoothed anchor
        self._theta = 0.0                    # smoothed orbit azimuth
        self._theta_des = None               # desired theta from a heading, if any
        self._smoothed_anchor_ref = None     # framing check reference (FE)
        self._radius = None                  # current commanded radius
        self._phi = None                     # current commanded elevation
        self._last_anchor = None             # raw anchor for speed measurement
        self._last_t = None
        self._avoid_active = set()           # hysteresis latch (Amendment 4.4)
        self._last_solution = None           # (r, theta, phi) last clear pose
        self._last_cmd_v = None
        self._trunk_mode = False

    # -- setup --------------------------------------------------------------

    def _select_trunk(self):
        """The designated trunk: the largest TRUNK-SCALE cylinder (r >=
        TRUNK_MIN_R, Amendment 5); posts and small rocks never qualify, and a
        scene without trunk-scale geometry has no trunk-approach mode."""
        candidates = [o for o in self.obstacles if o.r >= TRUNK_MIN_R]
        if not candidates:
            return None
        return max(candidates, key=lambda o: o.r * o.top)

    def bind(self):
        """Read the rig/scene once through the contract; derive the frozen
        ground-mode framing. Strict: refuses non-finite geometry."""
        doc = None
        if isinstance(self.provider, EngineRigProvider):
            doc = self.provider.bind()
            self.mesh_r = self.provider.mesh_r
        reading = self.provider.read()
        extent = getattr(self.provider, "extent", 0.0) or 0.0
        if extent <= 0.0:
            # no measured envelope: fall back to the mesh extent only
            extent = 0.0
        self.r_subject = extent + self.mesh_r
        self.r_floor = max(1.0, 1.02 * self.mesh_r)   # engine.cpp:56 law
        self.r_ground = max(self.r_floor,
                            min(R_MAX, self.r_subject / TAN_HALF_FOV * FIT_MARGIN))
        # Amendment 1 priority law: the feet criterion dominates; when the
        # eye-height bound is unreachable the hint is recorded, never hidden.
        phi_min = math.asin(min(1.0, H_EYE_MIN / self.r_ground))
        if phi_min > PHI_MAX_GROUND:
            self.phi_ground = PHI_MAX_GROUND
            self._low_eye_hint = "low_eye"
        else:
            self.phi_ground = 0.5 * (phi_min + PHI_MAX_GROUND)
            self._low_eye_hint = ""
        self._smoothed = reading.point
        self._last_anchor = reading.point
        self._last_t = reading.ts
        self._theta = 0.0
        self._smoothed_anchor_ref = reading.point
        self._phi = self.phi_ground
        self._radius = self.r_ground
        return self

    # -- framing laws -------------------------------------------------------

    def _mode_for(self, anchor):
        if self._trunk is None:
            return False
        d = _dist2(anchor, (self._trunk.cx, 0.0, self._trunk.cz))
        enter = (self.r_ground * math.cos(self.phi_ground) + self._trunk.r)
        if self._trunk_mode:
            return d <= enter + TRUNK_EXIT_HYST
        return d <= enter

    def _framing(self, anchor, mode):
        """(target, radius, theta_base, phi) for the mode -- prereg 'Derived
        constants'; trunk contact on the SURFACE nearest the anchor
        (Amendment 4.2); trunk theta DERIVED (Amendment 1.4)."""
        if not mode or self._trunk is None:
            theta_base = (self._theta_des if self._theta_des is not None
                          else self._theta)
            return anchor, self.r_ground, theta_base, self.phi_ground
        t = self._trunk
        dx, dz = anchor[0] - t.cx, anchor[2] - t.cz
        n = math.hypot(dx, dz)
        if n > 1e-9:
            contact_y = min(max(anchor[1], 0.0), t.top)
            trunk_pt = (t.cx + t.r * dx / n, contact_y, t.cz + t.r * dz / n)
            theta = math.atan2(dx / n, -dz / n)       # eye on the anchor's side
        else:                                          # degenerate: atop the axis
            contact_y = min(max(anchor[1], 0.0), t.top)
            trunk_pt = (t.cx, contact_y, t.cz)
            theta = self._theta
        target = _scale(_add(anchor, trunk_pt), 0.5)
        d = _dist(anchor, trunk_pt)
        clear_needed = 0.5 * d + MARGIN_CAM + t.r     # envelope + trunk bound
        r_trunk = max(self.r_floor,
                      min(R_MAX, clear_needed / TAN_HALF_FOV * FIT_MARGIN))
        return target, r_trunk, theta, self.phi_ground

    # -- obstruction avoidance (frozen order; Amendment 1) -------------------

    def _avoid(self, target, radius, theta, phi):
        """Returns (radius, theta, phi, avoidance_info). Frozen order:
        latch (Amendment 4.4) -> pull-in (Amendment 3.1) -> steepen sweep ->
        height-law numeric scan (Amendment 4.3) -> orbit sweep; else degraded.
        Every candidate re-verifies eye clearance, ray clearance, and framing."""
        info = {"order": []}
        obstacles = self.obstacles
        if not obstacles:
            self._avoid_active = set()
            self._last_solution = (radius, theta, phi)
            return radius, theta, phi, info

        def eye_of(r, th, ph):
            return engine_eye((r, th, ph,
                               target[0], target[1], target[2], 0.0, 0.0))

        def try_pose(r, th, ph):
            e = eye_of(r, th, ph)
            if not pose_clear(e, target, obstacles):
                return False
            if subtend_deg_from_axis(e, target,
                                     self._smoothed_anchor_ref) >= HALF_FOV:
                return False
            return True

        base_eye = eye_of(radius, theta, phi)
        eye_bad = [i for i, o in enumerate(obstacles)
                   if not point_clear(base_eye, o)]
        ray_bad = [i for i, o in enumerate(obstacles)
                   if not ray_clear(base_eye, target, o)]

        # (0) hysteresis latch: keep the previous solution while the base eye
        # remains within r + m + hysteresis of any latched cylinder's axis
        latch = False
        for i in list(self._avoid_active):
            if i >= len(obstacles):
                self._avoid_active.discard(i)
                continue
            o = obstacles[i]
            if _dist2(base_eye, (o.cx, base_eye[1], o.cz)) < \
                    o.r + MARGIN_CAM + AVOID_EXIT_HYST:
                latch = True
            else:
                self._avoid_active.discard(i)
        if latch and not eye_bad and not ray_bad and self._last_solution:
            r0, th0, ph0 = self._last_solution
            if try_pose(r0, th0, ph0):
                info["order"].append("latch")
                return r0, th0, ph0, info

        if not eye_bad and not ray_bad:
            self._last_solution = (radius, theta, phi)
            return radius, theta, phi, info

        # (1) pull-in: eye violations and near-eye ray crossings (Amend. 3.1);
        # scan downward, keep the LARGEST feasible radius (prereg OC7)
        if eye_bad:
            info["order"].append("pull_in")
            r_floor_mode = self._pull_floor(radius)
            if radius > r_floor_mode:
                step = max(1e-3, (radius - r_floor_mode) / 64.0)
                r_try = radius - step
                while r_try >= r_floor_mode - 1e-9:
                    if try_pose(r_try, theta, phi):
                        self._update_latch(eye_of(r_try, theta, phi))
                        self._last_solution = (r_try, theta, phi)
                        return r_try, theta, phi, info
                    r_try -= step

        # (2) steepen sweep at the current radius
        info["order"].append("steepen")
        ph = phi
        while ph < PHI_CAP - 1e-9:
            ph = min(PHI_CAP, ph + STEPPEN_STEP)
            if try_pose(radius, theta, ph):
                self._update_latch(eye_of(radius, theta, ph))
                self._last_solution = (radius, theta, ph)
                return radius, theta, ph, info

        # (3) height-law radius: numeric upward scan at the cap (Amendment 4.3)
        top_max = max(o.top for o in obstacles)
        q = 0.0
        for o in obstacles:
            q = max(q, max(0.0, _dist2(target, (o.cx, 0.0, o.cz))
                           - (o.r + MARGIN_RAY)))
        tan_cap = math.tan(PHI_CAP)
        bound = math.inf
        if tan_cap > 1e-9:
            bound = (q + (top_max + MARGIN_CAM - target[1]) / tan_cap) \
                / math.cos(PHI_CAP)
        if bound > radius:
            info["order"].append("height_radius")
            r_hi = min(R_MAX, radius * ((R_MAX / radius) ** (1.0 / HEIGHT_STEPS)))
            while r_hi <= min(R_MAX, bound) + 1e-9:
                if try_pose(r_hi, theta, PHI_CAP):
                    self._update_latch(eye_of(r_hi, theta, PHI_CAP))
                    self._last_solution = (r_hi, theta, PHI_CAP)
                    return r_hi, theta, PHI_CAP, info
                r_hi = min(R_MAX, r_hi * ((R_MAX / radius) ** (1.0 / HEIGHT_STEPS)))
                if r_hi >= R_MAX - 1e-9:
                    if try_pose(R_MAX, theta, PHI_CAP):
                        self._update_latch(eye_of(R_MAX, theta, PHI_CAP))
                        self._last_solution = (R_MAX, theta, PHI_CAP)
                        return R_MAX, theta, PHI_CAP, info
                    break

        # (4) orbit sweep at the current radius/phi
        info["order"].append("orbit")
        for sgn in self._orbit_sides():
            sw = ORBIT_STEP
            while sw <= ORBIT_SWEEP_MAX + 1e-9:
                for th in self._orbit_candidates(theta, sgn, sw):
                    if try_pose(radius, th, phi):
                        self._update_latch(eye_of(radius, th, phi))
                        self._last_solution = (radius, th, phi)
                        return radius, th, phi, info
                sw += ORBIT_STEP

        info["degraded"] = "occluded: no clear pose within declared bounds"
        return radius, theta, phi, info

    def _update_latch(self, solution_eye):
        """Latch the cylinders the SOLUTION eye is still near (Amendment 4.4)."""
        self._avoid_active = set()
        for i, o in enumerate(self.obstacles):
            if _dist2(solution_eye, (o.cx, solution_eye[1], o.cz)) < \
                    o.r + MARGIN_CAM + AVOID_EXIT_HYST:
                self._avoid_active.add(i)

    def _pull_floor(self, radius):
        return max(self.r_ground, self.r_floor)

    def _orbit_sides(self):
        return (1, -1)      # deterministic tie order: + first (prereg)

    def _orbit_candidates(self, theta, sgn, sweep):
        th = theta + sgn * sweep
        while th > math.pi:
            th -= 2.0 * math.pi
        while th < -math.pi:
            th += 2.0 * math.pi
        return (th,)

    # -- smoothing / speed laws ----------------------------------------------

    @staticmethod
    def _wrap_pi(a):
        while a > math.pi:
            a -= 2.0 * math.pi
        while a < -math.pi:
            a += 2.0 * math.pi
        return a

    def _smooth_anchor(self, raw, now):
        dt = max(1e-6, now - self._last_t)
        jump = _dist(raw, self._smoothed)
        cut = jump > CUT_FACTOR * self.r_ground
        if cut:
            self._smoothed = raw                      # declared snap
            return self._smoothed, True, 0.0
        a = 1.0 - math.exp(-dt / self.tau)
        tgt = _add(self._smoothed, _scale(_sub(raw, self._smoothed), a))
        v_animal = _dist(raw, self._last_anchor) / dt
        v_cam = max(V_CAM_FLOOR, 2.0 * v_animal)      # never outrun the animal
        step = _sub(tgt, self._smoothed)
        step_len = _norm(step)
        max_step = v_cam * dt
        if step_len > max_step:
            tgt = _add(self._smoothed, _scale(step, max_step / step_len))
        self._smoothed = tgt
        return self._smoothed, False, v_animal

    # -- the command (the ONLY write) ----------------------------------------

    def _post_camera(self, v, now):
        payload = {"cam_radius": v[0], "cam_theta": v[1], "cam_phi": v[2],
                   "pan_x": v[6], "pan_y": v[7],
                   "target_x": v[3], "target_y": v[4], "target_z": v[5]}
        st, body = self.client.post_json("/camera", payload)
        import json
        ok = st == 200 and b'"ok":true' in body
        if not ok:
            raise CameraConfigError(f"POST /camera rejected: http {st} {body[:80]!r}")
        self._last_cmd_v = tuple(v)
        return time.perf_counter()

    def _deadbanded(self, v):
        if self._last_cmd_v is None:
            return False
        p = self._last_cmd_v
        return (abs(v[0] - p[0]) < DEADBAND_R * max(v[0], 1e-6)
                and abs(self._wrap_pi(v[1] - p[1])) < DEADBAND_ANG
                and abs(v[2] - p[2]) < DEADBAND_ANG
                and _dist(v[3:6], p[3:6]) < DEADBAND_T)

    # -- the tick -------------------------------------------------------------

    def tick(self, now=None):
        report = TickReport()
        report.t_state = time.perf_counter()
        reading = self.provider.read()
        report.t_anchor = time.perf_counter()
        report.anchor = reading.point
        if reading.heading is not None and self.heading_enabled:
            hx, hz = reading.heading
            n = math.hypot(hx, hz)
            if n > 1e-9:
                self._theta_des = math.atan2(-hx / n, hz / n)
            # no heading this tick -> keep the last desired theta

        anchor, cut, v_animal = self._smooth_anchor(reading.point,
                                                    reading.ts)
        self._last_anchor = reading.point
        self._last_t = reading.ts
        report.cut = cut
        report.v_animal = v_animal

        self._trunk_mode = self._mode_for(anchor)
        report.mode = "trunk" if self._trunk_mode else "ground"
        target, radius, theta_base, phi = self._framing(anchor, self._trunk_mode)

        # smooth theta toward the framing base (shortest arc), then avoid
        self._theta += self._wrap_pi(theta_base - self._theta)
        self._smoothed_anchor_ref = anchor
        radius, theta, phi, avoid = self._avoid(target, radius,
                                                self._theta, phi)
        self._theta = theta
        report.avoidance = avoid
        report.degraded = bool(avoid.get("degraded"))
        report.degrade_reason = str(avoid.get("degraded", ""))
        report.hint = self._low_eye_hint

        v = (radius, self._theta, phi,
             target[0], target[1], target[2], 0.0, 0.0)
        report.t_solution = time.perf_counter()
        report.commanded_v = v
        if self._deadbanded(v):
            report.wrote = False
        else:
            t_ack = self._post_camera(v, now)
            report.wrote = True
            report.t_acked = t_ack
        self._radius, self._phi = radius, phi
        return report

    def verify_apply(self):
        """Explicit (off-tick) check that the engine APPLIED the last command:
        POST /project's cam echo must equal the last commanded v within 1e-3
        (prereg falsifier FG)."""
        if self._last_cmd_v is None:
            return {"ok": False, "error": "no command issued yet"}
        st, body = self.client.post_json("/project",
                                         {"x": 0.0, "y": 0.0, "z": 0.0})
        import json
        doc = json.loads(body.decode("utf-8", "replace"))
        cam = doc.get("cam")
        if not cam or len(cam) != 8:
            return {"ok": False, "error": f"bad cam echo: {cam!r}"}
        err = max(abs(float(a) - float(b))
                  for a, b in zip(cam, self._last_cmd_v))
        return {"ok": err <= 1e-3, "max_err": err, "echo": cam}

    def state(self):
        return {"mode": "trunk" if self._trunk_mode else "ground",
                "r_subject": getattr(self, "r_subject", None),
                "r_ground": getattr(self, "r_ground", None),
                "phi_ground": getattr(self, "phi_ground", None),
                "theta": self._theta, "radius": self._radius, "phi": self._phi,
                "hint": self._low_eye_hint,
                "degraded_last": bool(self._last_cmd_v is None)}
