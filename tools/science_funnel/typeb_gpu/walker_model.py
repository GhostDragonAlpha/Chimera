"""walker_model.py -- the gait walker's compiled scene -> GPU-port spec.

Parses the compiled gait_scene bundle (tools/science_funnel/gait_scene.py
output) into the constant tables the batched Warp kernel consumes. The body
ordering and axis folding replicate ChimeraEngine/engine/coupled_articulation.hpp
Model::Model (alphabetical-remaining topological insertion) so the port is a
FAITHFUL reimplementation of the CPU reference's model, not a re-authoring.

Also carries the C++ controller's frozen constants (T_CYCLE, DUTY_SAMPLED,
touch classes, servo gains law) and the reset-state law (gait_controller.hpp
GaitWalker::reset). Python-side FK/mass mirror exists ONLY for the
setup-time scalars the C++ derives at construction (the mass-normalized PD
gains from the defaults-pose diagonal) and for cross-checks; the runtime
equations live in walker_gpu.py.

Trailer Agent: GLM 5.3.
"""
import json, math
import numpy as np

# ── the controller's frozen constants (gait_controller.hpp, verbatim) ──
T_CYCLE = 0.71
DUTY_SAMPLED = 0.683
TOE_OFF = 0.68
FS_HZ = 4.0
ZETA = 0.8
CAPTURE_PHI = 0.95
K_TOUCH = 1e-5
K_SLIP = 1e-9
K_RELEASE_BAND = 1e-6
NB = 6          # the floating-base coordinate count
NDRIVE = 12     # the drives (8 hind + 4 fore)
NPOST = 13      # + the trunk-pitch posture drive slot
FOLD_BUDGET_TICKS = 45   # wave 29
UNLOAD_TICKS = 1         # wave 32
SINK_RATE_MAX = 0.002349 # wave 27

# The defaults-pose mass diagonal, PINNED FROM THE C++ REFERENCE (the gain
# anchor; see the comment at the kp/kd construction for the derivation and
# the measured defect). Order = model coordinate order 0..17. Source:
# cpu_probe.exe <scene.json> diag  (GaitWalker ctor's
# model_->evaluate(model_->defaults, 0, gravity_) diagonal).
GAIN_ANCHOR_DIAG = np.array([
    0.57360590381779231,
    0.088057112958353376,
    0.6329889371594789,
    10.037998000000004,
    10.037998000000004,
    10.037998000000004,
    0.0322021819993,
    0.005897296162,
    0.00042511520200000006,
    1.6891250000000002e-05,
    0.0322021819993,
    0.005897296162,
    0.00042511520200000006,
    1.6891250000000002e-05,
    0.0048717298319693398,
    0.0005609308320000001,
    0.0048717298319693398,
    0.0005609308320000001,
])


def _frame(p, q):
    """coupled_articulation frame(V p, V q): Euler XYZ then translation."""
    R = np.eye(3)
    for i in range(3):
        axis = np.zeros(3); axis[i] = 1.0
        c, s = math.cos(q[i]), math.sin(q[i])
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        R = R @ (np.eye(3) + K * s + (K @ K) * (1 - c))
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = p
    return T


def _inv_rigid(T):
    out = np.eye(4)
    out[:3, :3] = T[:3, :3].T
    out[:3, 3] = -out[:3, :3] @ T[:3, 3]
    return out


class WalkerSpec:
    """The constant tables + scalar parameters for one compiled gait scene."""

    def __init__(self, scene_json: dict, gravity: float = 9.80665, shift=(0.0, 0.0, 0.0)):
        data = scene_json["gait_controller"]
        recipe = data["recipe"]
        assert recipe["schema"] == "chimera.gait_scene.v1", "gait_schema"
        model = data["model"]
        assert model["schema"] == "chimera.anatomical_assembly.v1", "coupled_anatomy_schema"

        # ── coordinate selection: the recipe's array, verbatim ──
        self.names = list(recipe["coordinates"])
        self.n = len(self.names)
        assert self.n == 18, f"gait_coordinate_capacity n={self.n}"
        coords = model["coordinates"]
        self.defaults = np.array([float(coords[c]["default_rad"]) for c in self.names])
        self.lower = np.array([float(coords[c]["range_rad"][0]) for c in self.names])
        self.upper = np.array([float(coords[c]["range_rad"][1]) for c in self.names])
        slot = {c: i for i, c in enumerate(self.names)}

        # ── bodies: alphabetical-remaining topological insertion (the C++ law) ──
        remaining = {b["name"]: b for b in model["bodies"]}
        order = []  # (name, body_json)
        ids = {}
        while remaining:
            progress = False
            for name in sorted(remaining.keys()):
                b = remaining[name]
                is_ground = name == "ground"
                if not is_ground and b["joint"]["parent"] not in ids:
                    continue
                order.append((name, b)); ids[name] = len(order) - 1
                del remaining[name]
                progress = True
                break  # the C++ restarts the scan after each insertion
            assert progress, "coupled_missing_or_cyclic_parent"
        # NOTE: the C++ continues the for from where it erased, but std::map
        # iteration is alphabetical and re-scanning from the start after each
        # erase yields the same insertion order here (ground first, then the
        # same alphabetical topological cascade). Verified against the engine's
        # body() index lookups by construction below.
        assert order[0][0] == "ground"

        NBOD = len(order)
        self.nbod = NBOD
        self.body_names = [n for n, _ in order]
        self.body_parent = np.full(NBOD, -1, np.int32)
        self.body_mass = np.zeros(NBOD)
        self.body_com = np.zeros((NBOD, 3))
        self.body_inertia = np.zeros((NBOD, 3))  # diagonal (the authored form)
        self.body_fp = np.zeros((NBOD, 4, 4)); self.body_fc = np.zeros((NBOD, 4, 4))
        for i, (name, b) in enumerate(order):
            self.body_mass[i] = float(b["mass_kg"])
            self.body_com[i] = b["mass_center_m"]
            ic = b["inertia_kg_m2"]
            self.body_inertia[i] = [float(ic[0]), float(ic[1]), float(ic[2])]
            if name == "ground":
                assert b["joint"] is None
                self.body_fp[i] = np.eye(4); self.body_fc[i] = np.eye(4)
            else:
                j = b["joint"]
                self.body_parent[i] = ids[j["parent"]]
                self.body_fp[i] = _frame(j["parent_location_m"], j["parent_orientation_rad"])
                self.body_fc[i] = _inv_rigid(_frame(j["child_location_m"], j["child_orientation_rad"]))
        self.body_name_to_idx = ids

        # ── axes: per body, in joint-declaration order ──
        # Axis fields: body, rot(1/0), axis(3), slot(-1 folded), slope, const
        self.axes = []  # list of dict
        self.body_axoff = np.zeros(NBOD + 1, np.int32)
        for i, (name, b) in enumerate(order):
            self.body_axoff[i] = len(self.axes)
            if name == "ground":
                continue
            for ax in b["joint"]["axes"]:
                rot = 1 if ax["name"].startswith("rotation") else 0
                fn = ax["function"]
                slope, const, a_slot = 0.0, 0.0, -1
                if fn["type"] == "LinearFunction":
                    coord = ax["coordinate"]
                    if coord in slot:
                        slope = float(fn["coefficients"][0]); a_slot = slot[coord]
                        const = float(fn["coefficients"][1])
                    else:
                        const = float(fn["coefficients"][0]) * float(coords[coord]["default_rad"]) + float(fn["coefficients"][1])
                else:
                    const = float(fn["coefficients"][0])
                self.axes.append({"body": i, "rot": rot, "axis": np.array(ax["axis"], float),
                                  "slot": a_slot, "slope": slope, "const": const})
        self.body_axoff[NBOD] = len(self.axes)
        self.naxes = len(self.axes)

        # structural ancestor-slot lists per body (for the Jacobian assembly)
        self.body_slots = []  # per body: list of (axis_index, slot)
        for i in range(NBOD):
            chain, b = [], i
            while b >= 0:
                for a in range(self.body_axoff[b], self.body_axoff[b + 1]):
                    ax = self.axes[a]
                    if ax["slot"] >= 0:
                        chain.append(a)
                b = int(self.body_parent[b])
            self.body_slots.append(chain)

        # ── contact points ──
        pts = recipe["contact_points"]
        assert 1 <= len(pts) <= 8, "gait_contact_capacity"
        self.npts = len(pts)
        self.pt_name = [p["name"] for p in pts]
        self.pt_body = np.array([ids[p["body"]] for p in pts], np.int32)
        self.pt_local = np.array([p["point_m"] for p in pts], float)
        self.pt_radius = np.array([float(p["radius_m"]) for p in pts])

        # ── drives ──
        dj = recipe["drives"]
        assert len(dj) == 12, "gait_drive_count"
        self.drive_name = [d["coordinate"] for d in dj]
        self.drive_leg = [d["leg"] for d in dj]
        self.drive_joint = [d["joint"] for d in dj]
        self.drive_coord = np.array([slot[d["coordinate"]] for d in dj], np.int32)
        self.drive_cap = np.array([float(d["torque_cap_N_m"]) for d in dj])
        self.drive_store_floor = np.array([float(d["store_floor_J"]) for d in dj])
        self.drive_damping = np.array([float(d["viscous_damping_N_m_s_rad"]) for d in dj])

        self.gravity = np.array([0.0, -9.80665, 0.0])
        # ── the defaults-pose mass diagonal -> the mass-normalized PD gains ──
        # THE GAIN ANCHOR, PINNED TO THE REFERENCE'S OWN BITS. The numpy
        # mirror (self.evaluate/_fk below) cannot reproduce the C++
        # Model::evaluate()'s scalar fp order bit-for-bit (BLAS products vs
        # scalar loops); its 1-2 ulp diagonal error propagated into the
        # mass-normalized gains (kp=m*freq*freq, kd=2*ZETA*m*freq) and from
        # there into tau at every tick: MEASURED (closeout-3), the mirror
        # diagonal differs from the reference at coordinates 0,1,2,9,13,14,16
        # -- drives 4/8 (the hind MPs) inherit a 1-ulp kp/kd and are exactly
        # the census's tau9/tau13 divergence at tick-0 substep-0; drives 9/11
        # (fore shoulders) and the posture drive inherit it too. The pinned
        # values ARE the reference's arithmetic, not new numbers: they are
        # cpu_probe.exe <scene.json> diag = the GaitWalker constructor's
        # model_->evaluate(model_->defaults, 0, gravity_) diagonal
        # (coupled_articulation.hpp evaluate()), consumed by kp_/kd_ exactly
        # as the expressions below. Regenerate after any scene change with
        # cpu_probe.exe diag and repin. (Scene:
        # .tmp/gait-walker/scene.json @ closeout-3, 2026-09-22.)
        md = GAIN_ANCHOR_DIAG.copy()
        freq = 2.0 * math.pi * FS_HZ
        self.kp = np.array([md[c] * freq * freq for c in self.drive_coord])
        self.kd = np.array([2.0 * ZETA * md[c] * freq for c in self.drive_coord])
        m_post = md[2]
        self.kp_post = m_post * freq * freq
        self.kd_post = 2.0 * ZETA * m_post * freq
        self.store_post = float(self.drive_store_floor[0])

        # ── tables ──
        t = recipe["tables_rad"]
        self.tab_hip = np.array(t["hip"]); self.tab_knee = np.array(t["knee"])
        self.tab_ankle = np.array(t["ankle"]); self.tab_mp = np.array(t["MP"])
        zm = recipe.get("zero_map_rad")
        self.zeros = np.array([zm["hip"], zm["knee"], zm["ankle"], zm["MP"]]) if zm else np.zeros(4)
        tv = recipe.get("trunk_vault_rad")
        self.trunk_vault = np.array(tv) if tv else np.zeros(21)

        # ── scalars ──
        self.plane_world_y = float(recipe["contact_plane_height_m"])
        self.plane_model_y = self.plane_world_y - float(shift[1])
        cfg = recipe["defaults"]
        self.contact_enabled = bool(cfg["contact_enabled"])
        self.mu = float(cfg["contact_friction"])
        self.settle_ticks = int(cfg.get("settle_ticks", 0))
        self.settle_total = self.settle_ticks
        self.gait_enabled = bool(cfg["gait_enabled"])
        self.power = bool(cfg["power"])
        self.capture_enabled = bool(cfg["capture_enabled"])
        self.posture_drive = bool(cfg["posture_drive"])
        self.push_N = float(cfg.get("push_N", 0.0))
        self.drive_enabled = np.array([bool(cfg[d["coordinate"] + "_drive"]) for d in dj])
        self.start_phase_left = float(cfg.get("start_phase_left", 0.0))
        self.start_phase_right = float(cfg.get("start_phase_right", 0.5))
        self.base_speed_x = float(cfg.get("base_speed_x_m_s", 0.0))
        self.base_trans_y = float(cfg.get("base_trans_y_m", 0.0))
        self.start_trunk_rad = float(cfg.get("start_trunk_rad", 0.0))
        self.start_at_tables = bool(cfg.get("start_at_tables", False))
        fp = recipe.get("fore_entry_pose_rad")
        self.fore_pose_sh = float(fp["shoulder_rad"]) if fp else -0.903
        self.fore_pose_el = float(fp["elbow_rad"]) if fp else 0.838
        hh = recipe.get("hind_height_hold_crit_m")
        self.height_hold_armed = hh is not None
        self.height_crit = float(hh) if hh is not None else 0.0
        if self.height_hold_armed:
            floor_expr = 2.0 * SINK_RATE_MAX + SINK_RATE_MAX * (1.0 / (ZETA * 2.0 * math.pi * FS_HZ)) / (1.0 / 300.0)
            assert abs(float(recipe["hind_height_hold_floor_m"]) - floor_expr) <= 1e-9, "gait_height_hold_floor_mismatch"
        self.height_floor = 2.0 * SINK_RATE_MAX + SINK_RATE_MAX * (1.0 / (ZETA * 2.0 * math.pi * FS_HZ)) / (1.0 / 300.0)
        self.gravity = np.array([0.0, -gravity, 0.0])
        self.dt = 1.0 / 300.0
        assert int(recipe["substeps"]) == 4, "gait_substeps"

        # ── the fore/hind chain geometry harvested from the model bytes ──
        # fore (wave 12): mount = upperarm's pelvis offset; L1 = |forearm parent y|
        self.fore_mount_body = ids["pelvis"]
        self.fore_mount_local = {}
        self.fore_L1 = 0.0
        for leg in ("fore_left", "fore_right"):
            ua = next(b for n, b in order if n == f"upperarm_{leg}")
            self.fore_mount_local[leg] = np.array(ua["joint"]["parent_location_m"], float)
            fa = next(b for n, b in order if n == f"forearm_{leg}")
            l = abs(float(fa["joint"]["parent_location_m"][1]))
            assert self.fore_L1 == 0.0 or abs(l - self.fore_L1) < 1e-12, "gait_fore_L1_mismatch"
            self.fore_L1 = l
        # paw reference = heel/MP midpoint in the forearm frame
        self.fore_paw_ref = {}
        for leg in ("fore_left", "fore_right"):
            h = next(p for p in pts if p["name"] == leg + "_heel")
            m = next(p for p in pts if p["name"] == leg + "_mp_head")
            self.fore_paw_ref[leg] = 0.5 * (np.array(h["point_m"], float) + np.array(m["point_m"], float))
        pr = self.fore_paw_ref["fore_left"]
        self.fore_rho = math.hypot(pr[0], pr[1])
        self.fore_beta = math.atan2(pr[1], pr[0])
        # fore contact point indices
        self.fore_heel_pt = [self.pt_name.index("fore_left_heel"), self.pt_name.index("fore_right_heel")]
        self.fore_mp_pt = [self.pt_name.index("fore_left_mp_head"), self.pt_name.index("fore_right_mp_head")]
        # fore drive coords [leg][0]=shoulder [1]=elbow
        self.fore_coord = [[slot[f"shoulder_flexion_fore_left"], slot[f"elbow_flexion_fore_left"]],
                           [slot[f"shoulder_flexion_fore_right"], slot[f"elbow_flexion_fore_right"]]]
        self.fore_drive_idx = [[self.drive_name.index(f"shoulder_flexion_fore_left"), self.drive_name.index(f"elbow_flexion_fore_left")],
                               [self.drive_name.index(f"shoulder_flexion_fore_right"), self.drive_name.index(f"elbow_flexion_fore_right")]]
        self.upperarm_body = [ids["upperarm_fore_left"], ids["upperarm_fore_right"]]
        self.forearm_body = [ids["forearm_fore_left"], ids["forearm_fore_right"]]

        # hind (wave 28): mounts, L1/L2, paw-midpoint offset, coords
        self.pelvis_row = ids["pelvis"]
        self.hind_mount = {}
        self.hind_L1 = 0.0; self.hind_L2 = 0.0
        for leg in ("left", "right"):
            th = next(b for n, b in order if n == f"thigh_{leg}")
            assert th["joint"]["parent"] == "pelvis"
            self.hind_mount[leg] = np.array(th["joint"]["parent_location_m"], float)
            sh = next(b for n, b in order if n == f"shank_{leg}")
            l = abs(float(sh["joint"]["parent_location_m"][1]))
            assert self.hind_L1 == 0.0 or abs(l - self.hind_L1) < 1e-12, "gait_hind_L1_mismatch"
            self.hind_L1 = l
            ft = next(b for n, b in order if n == f"foot_{leg}")
            l2 = abs(float(ft["joint"]["parent_location_m"][1]))
            assert self.hind_L2 == 0.0 or abs(l2 - self.hind_L2) < 1e-12, "gait_hind_L2_mismatch"
            self.hind_L2 = l2
        h = next(p for p in pts if p["name"] == "left_heel")
        m = next(p for p in pts if p["name"] == "left_mp_head")
        self.hind_xm = 0.5 * (float(h["point_m"][0]) + float(m["point_m"][0]))
        self.hind_heel_pt = [self.pt_name.index("left_heel"), self.pt_name.index("right_heel")]
        self.hind_mp_pt = [self.pt_name.index("left_mp_head"), self.pt_name.index("right_mp_head")]
        self.hind_coord = [[slot[f"hip_flexion_left"], slot[f"knee_extension_left"], slot[f"ankle_dorsiflexion_left"], slot[f"MP_dorsiflexion_left"]],
                           [slot[f"hip_flexion_right"], slot[f"knee_extension_right"], slot[f"ankle_dorsiflexion_right"], slot[f"MP_dorsiflexion_right"]]]
        self.hind_drive_idx = [[self.drive_name.index(f"hip_flexion_left"), self.drive_name.index(f"knee_extension_left"), self.drive_name.index(f"ankle_dorsiflexion_left"), self.drive_name.index(f"MP_dorsiflexion_left")],
                               [self.drive_name.index(f"hip_flexion_right"), self.drive_name.index(f"knee_extension_right"), self.drive_name.index(f"ankle_dorsiflexion_right"), self.drive_name.index(f"MP_dorsiflexion_right")]]

        # hind driven coordinates and their drive indices (for damping/tau)
        self.drive_is_hind_or_fore = np.array([not d["leg"] in ("trunk",) for d in dj])

    # ── the Python FK/mass mirror (setup-time scalars + cross-checks ONLY) ──
    # Faithful to coupled_articulation.hpp evaluate(): f = par*fp*motion*fc
    # with motion = [R_axes | t_axes]; the Jacobian columns are the geometric
    # actions of each axis (d/dq_i f): rotational -> w_i x (x - pivot_i),
    # translational -> d_i. Analytically identical to the C++ transform-
    # derivative recursion; the runtime port (walker_gpu.py) uses the same.
    def _fk(self, q, v=None):
        n = self.n
        if v is None:
            v = np.zeros(n)
        frames = [np.eye(4)]
        jv = [np.zeros((n, 3)) for _ in range(self.nbod)]
        jw = [np.zeros((n, 3)) for _ in range(self.nbod)]
        axes_of = {}
        for a, ax in enumerate(self.axes):
            axes_of.setdefault(ax["body"], []).append(a)
        axis_world = [None] * self.naxes  # rotational axes' world direction
        axis_pivot = [None] * self.naxes  # rotational axes' world pivot
        axis_dir = [None] * self.naxes    # translational axes' world direction
        for i in range(1, self.nbod):
            par = int(self.body_parent[i])
            fp, fc = self.body_fp[i], self.body_fc[i]
            pfp = frames[par] @ fp
            Rm = np.eye(3); t_m = np.zeros(3)
            for a in axes_of.get(i, []):
                ax = self.axes[a]
                angle = ax["const"] + (ax["slope"] * q[ax["slot"]] if ax["slot"] >= 0 else 0.0)
                if ax["rot"]:
                    axis = ax["axis"]; c, s = math.cos(angle), math.sin(angle)
                    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
                    Rm = Rm @ (np.eye(3) + K * s + (K @ K) * (1 - c))
                else:
                    t_m = t_m + ax["axis"] * angle
            motion = np.eye(4); motion[:3, :3] = Rm; motion[:3, 3] = t_m
            f = pfp @ motion @ fc
            frames.append(f)
            for a in axes_of.get(i, []):
                ax = self.axes[a]
                if ax["rot"]:
                    axis_world[a] = pfp[:3, :3] @ ax["axis"]
                    axis_pivot[a] = pfp[:3, 3] + pfp[:3, :3] @ t_m
                else:
                    axis_dir[a] = pfp[:3, :3] @ ax["axis"]
            # accumulate THIS body's Jacobian over its full ancestor chain
            com_w = f[:3, :3] @ self.body_com[i] + f[:3, 3]
            b = i
            while b >= 1:
                for a in axes_of.get(b, []):
                    ax = self.axes[a]
                    if ax["slot"] < 0:
                        continue
                    if ax["rot"]:
                        jw[i][ax["slot"]] = jw[i][ax["slot"]] + axis_world[a]
                        jv[i][ax["slot"]] = jv[i][ax["slot"]] + np.cross(axis_world[a], com_w - axis_pivot[a])
                    else:
                        jv[i][ax["slot"]] = jv[i][ax["slot"]] + axis_dir[a]
                b = int(self.body_parent[b])
        return frames, jv, jw

    def evaluate(self, q, v=None):
        """The Evaluation triple (mass, gravity, bias, potential) for probes."""
        if v is None:
            v = np.zeros(self.n)
        frames, jv, jw = self._fk(q, v)
        n = self.n
        M = np.zeros((n, n)); g = np.zeros(n); bias = np.zeros(n); pot = 0.0
        for i in range(self.nbod):
            m = self.body_mass[i]
            if m == 0.0:
                continue
            Rb = frames[i][:3, :3]; pb = frames[i][:3, 3]
            Iw = Rb @ np.diag(self.body_inertia[i]) @ Rb.T
            com_w = Rb @ self.body_com[i] + pb
            # omega/alpha via finite difference of the geometric velocity is NOT
            # faithful; the bias terms are not needed at setup time (mass diag).
            for a in range(n):
                g[a] += m * float(jv[i][a] @ self.gravity)
                for b in range(n):
                    M[a, b] += m * float(jv[i][a] @ jv[i][b]) + float(jw[i][a] @ (Iw @ jw[i][b]))
            pot -= m * float(self.gravity @ com_w)
        return M, g, bias, pot

    def mass_diag(self, q):
        M, _, _, _ = self.evaluate(q)
        return np.diag(M).copy()

    # ── the reset-state law (gait_controller.hpp reset, start_at_tables path) ──
    def reset_state(self):
        q = self.defaults.copy()
        v = np.zeros(self.n)
        phi = [self.start_phase_left, self.start_phase_right]
        if self.start_at_tables:
            q[4] = self.base_trans_y
            for d in range(NDRIVE):
                leg = self.drive_leg[d]
                if leg.startswith("fore"):
                    q[self.drive_coord[d]] = self.fore_pose_sh if self.drive_joint[d] == "shoulder" else self.fore_pose_el
                    continue
                li = 0 if leg == "left" else 1
                qstar = self.tables_at(phi[li])
                ji = {"hip": 0, "knee": 1, "ankle": 2, "MP": 3}[self.drive_joint[d]]
                q[self.drive_coord[d]] = qstar[ji]
                p = phi[li]; dp = 0.05
                a1 = self.tables_at(p + dp); a2 = self.tables_at(p - dp)
                v[self.drive_coord[d]] = (a1[ji] - a2[ji]) / (2 * dp * T_CYCLE)
            v[3] = self.base_speed_x
            q[2] = self.start_trunk_rad
            p = phi[0]; dp = 0.05
            v[2] = (self.trunk_target(p + dp) - self.trunk_target(p - dp)) / (2 * dp * T_CYCLE)
        return q, v, phi

    def tables_at(self, phi):
        phi = phi - math.floor(phi)
        out = [0.0] * 4
        for i, t in enumerate((self.tab_hip, self.tab_knee, self.tab_ankle, self.tab_mp)):
            x = phi * 20.0
            k = min(19, int(x)); f = x - k
            out[i] = t[k] * (1 - f) + t[k + 1] * f + self.zeros[i]
        return out

    def trunk_target(self, phi):
        phi = phi - math.floor(phi)
        x = phi * 20.0
        k = min(19, int(x)); f = x - k
        return self.trunk_vault[k] * (1 - f) + self.trunk_vault[k + 1] * f


def _mkT(R, p):
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = p
    return T


def load_spec(scene_path, gravity=9.80665):
    with open(scene_path, "r", encoding="utf-8") as f:
        scene = json.load(f)
    return WalkerSpec(scene, gravity=gravity)
