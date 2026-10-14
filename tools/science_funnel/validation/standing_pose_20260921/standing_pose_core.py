"""standing_pose_core.py -- the shared derivation for THE STANDING POSE lane
(preregistration 63e9def4..., banked before the solve).

Everything here is DERIVED/CITED/COMMITTED, nothing tuned:
  - the registered primitives are the committed hip module, imported VERBATIM,
  - the bounds are the committed definition's own joint_class records,
  - the hip pivots are the registered femoral-head fits, re-derived and
    asserted against the committed hip battery,
  - the knee/elbow/driver pivots and axes are constructions on the bonds' own
    recorded closest-point pairs and the tarsal battery's registered constants,
  - the objective is the preregistered J = V + kappa*d with kappa = V_rest/d_rest
    computed from committed bytes at run time.

Deterministic: no RNG, no timestamps, no set-order leakage.
"""

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRIOR = ROOT / "tools" / "science_funnel" / "validation" / "hip_pivot_proof_20260921"
TARSAL = ROOT / "tools" / "science_funnel" / "validation" / "tarsal_cycle_pivots_20260921"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PRIOR))

import hip_pivot_proof as hp  # the committed module: registered primitives only  # noqa: E402

DATA = ROOT / "tools" / "science_funnel" / "data" / "morphosource_ct" / "matter_skeleton"
DEFN = DATA / "infant_skeleton.body.json"
HIP_BATTERY = PRIOR / "battery.json"
TARSAL_BATTERY = TARSAL / "battery.json"

CUT_MM = 3.0            # the committed touching-class cut
R12 = 12                # the house record rounding
IMMOBILITY_TOL_MM = 1e-9  # P-A5/P-A6 measured-confirmation tolerance
DETECTOR_TOL = 1e-12    # the hip battery's resampling detector

# the pads: the four distalmost limb-end membranes (preregistration section 4)
PAD_BONES = (8, 9, 22, 23)

# the tarsal battery's BANKED constants this lane asserts against (section 3)
BANKED_TARSAL = {
    "bond.joint_06_25": dict(center=[36.83565478293, 32.260135932044, 46.224951880972]),
    "bond.joint_07_24": dict(center=[43.784032845164, 29.623876636742, 26.559001107115]),
}
BANKED_TARSAL_AXIS = [0.330508327523, -0.125396983699, -0.935435642851]


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rnd(x):
    return round(float(x), R12)


def sanitize(o):
    if isinstance(o, dict):
        return {k: sanitize(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [sanitize(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return rnd(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def rot_matrix(axis, theta):
    """Rodrigues rotation MATRIX about a unit axis; theta == 0 is the exact
    identity (the rest-identity law)."""
    if theta == 0.0:
        return np.eye(3)
    k = np.asarray(axis, dtype=np.float64)
    k = k / np.linalg.norm(k)
    cos, sin = math.cos(theta), math.sin(theta)
    K = np.array([[0.0, -k[2], k[1]], [k[2], 0.0, -k[0]], [-k[1], k[0], 0.0]])
    return np.eye(3) * cos + K * sin + np.outer(k, k) * (1.0 - cos)


class Xform:
    """A rigid transform as a CHAIN of pivot-anchored rotations applied in
    sequence: p -> pivot + R @ (p - pivot) per step. Anchoring makes each
    step's pivot a BITWISE fixed point (p = pivot: p - pivot == 0 exactly, so
    pivot + R@0 == pivot), which is the P6' Leg-2 signature through COMPOSED
    same-center rotations (the hip's three coordinates share the fitted head
    center). Composition parent @ local concatenates the chains."""

    def __init__(self, chain=None):
        self.chain = [] if chain is None else list(chain)

    @staticmethod
    def rotation(pivot, axis, theta):
        if theta == 0.0:
            return Xform()
        return Xform([(np.asarray(pivot, dtype=np.float64), rot_matrix(axis, theta))])

    def __matmul__(self, other):
        return Xform(self.chain + other.chain)

    def pts(self, pts):
        p = np.asarray(pts, dtype=np.float64)
        for pivot, R in self.chain:
            p = pivot + (p - pivot) @ R.T
        return p

    def same_as(self, other):
        if len(self.chain) != len(other.chain):
            return False
        for (p1, R1), (p2, R2) in zip(self.chain, other.chain):
            if not (np.array_equal(p1, p2) and np.array_equal(R1, R2)):
                return False
        return True


def median_edge(tris):
    return float(np.median(np.concatenate([
        np.linalg.norm(tris[:, 1] - tris[:, 0], axis=1),
        np.linalg.norm(tris[:, 2] - tris[:, 1], axis=1),
        np.linalg.norm(tris[:, 0] - tris[:, 2], axis=1)])))


class StandingDerivation:
    """Loads the committed records/geometry, derives pivots/axes/signs, exposes
    the FK, the objective, and the constraints."""

    def __init__(self):
        self.body = json.loads(DEFN.read_text(encoding="utf-8"))
        self.bonds = {b["id"]: b for b in self.body["bonds"]}
        self.mems = {m["id"]: m for m in self.body["membranes"]}
        self.contacts = {c["id"]: c for c in self.body["pose_contacts"]["contacts"]}

        # committed geometry
        self.geo = {}
        for r in range(1, 26):
            blob, tris = hp.load_blob(r)
            verts, faces = hp.unique_verts(tris)
            self.geo[r] = dict(blob=blob, tris=tris, verts=verts, faces=faces,
                               tree=cKDTree(verts), med=median_edge(tris))

        self._check_input_integrity()
        self._derive_hips()
        self._derive_knees()
        self._derive_elbows()
        self._derive_drivers()
        self._derive_trunk()
        self._derive_objective_constants()

    # ------------------------------------------------------------- integrity
    def _check_input_integrity(self):
        for r in (1, 2, 3, 6, 7, 10, 12):
            if hp.vertex_records_sha(self.geo[r]["blob"]) != \
                    self.mems["mem.bone_%02d" % r]["vertex_sha256"]:
                raise SystemExit("vertex book drift bone_%02d" % r)
        hip = json.loads(HIP_BATTERY.read_text(encoding="utf-8"))
        if not hip.get("hard_checks_pass"):
            raise SystemExit("committed hip battery not green")
        tar = json.loads(TARSAL_BATTERY.read_text(encoding="utf-8"))
        if not tar.get("hard_checks_pass"):
            raise SystemExit("committed tarsal battery not green")
        self.hip_battery = hip
        self.tarsal_battery = tar

    # ----------------------------------------------------------------- hips
    def _derive_hips(self):
        u = np.array(self.hip_battery["axis"]["u"], dtype=np.float64)
        c2 = np.array(self.hip_battery["axis"]["pivot_02_mm"], dtype=np.float64)
        c3 = np.array(self.hip_battery["axis"]["pivot_03_mm"], dtype=np.float64)
        # re-derive the fits with the registered machinery, assert vs committed
        rederived = {}
        for k, bond_id in (("02", "bond.joint_01_02"), ("03", "bond.joint_01_03")):
            ch = int(k)
            bond = self.bonds[bond_id]
            on_ch = np.array(bond["closest_points_mm"]["on_%s" % k], dtype=float)
            fit = hp.inlier_rule(self.geo[ch]["verts"], self.geo[ch]["faces"],
                                 on_ch, self.geo[ch]["med"])
            if fit.get("outcome") != "fixed_point":
                raise SystemExit("hip %s fit refused" % k)
            c = np.array(fit["center_mm"], dtype=np.float64)
            comm = np.array(self.hip_battery["fits"][k]["center_mm"], dtype=np.float64)
            if [rnd(x) for x in c] != [rnd(x) for x in comm]:
                raise SystemExit("hip %s fit drift vs committed battery" % k)
            rederived[k] = c
        if [rnd(x) for x in rederived["02"]] != [rnd(x) for x in c2] or \
           [rnd(x) for x in rederived["03"]] != [rnd(x) for x in c3]:
            raise SystemExit("hip pivot drift vs committed axis record")

        self.hip = {}
        for side, k, bond_id, knee_id in (("L", "02", "bond.joint_01_02", "bond.joint_02_06"),
                                          ("R", "03", "bond.joint_01_03", "bond.joint_03_07")):
            c = rederived[k]
            band = float(self.hip_battery["fits"][k]["rms_residual_mm"])
            rng = self.bonds[bond_id]["joint_class"]["range_rad"]
            on_knee = self._realized_pair(knee_id)[1]  # femur-side realized apposition vertex
            e3raw = on_knee - c
            e3 = e3raw - (e3raw @ u) * u
            e3 = e3 / np.linalg.norm(e3)
            e2 = np.cross(e3, u)
            e2 = e2 / np.linalg.norm(e2)
            flex_sign = int(self.hip_battery["signs"][k]["flexion_sign"])
            self.hip[side] = dict(
                bond=bond_id, child=int(k), c=c, band=band, range=rng,
                e1=u.copy(), e2=e2, e3=e3, flex_sign=flex_sign,
                sign_rule="sigma=+1 (rotation = recorded coordinate about the banked axes); "
                          "the flexion END is named by the committed battery sign %+d" % flex_sign)

    # ---------------------------------------------------------------- knees
    def _realized_pair(self, bond_id):
        """The tarsal battery's derivation-free construction (amendment 1): the
        realizing vertex pair of the committed law metric at theta = 0."""
        b = self.bonds[bond_id]
        pa_mem, ch_mem = b["members"]
        parent = int(pa_mem.split("bone_")[1])
        child = int(ch_mem.split("bone_")[1])
        vq = self.geo[child]["verts"]
        g, prov = hp.law_gap(vq, self.geo[parent]["verts"], self.geo[parent]["tree"])
        on_child = vq[int(prov[1])]
        on_parent = self.geo[parent]["verts"][int(prov[3])]
        return (on_child + on_parent) / 2.0, on_parent, on_child, g

    def _curl_probe_sign(self, pivot, axis, child, curl_pt, probe):
        """The hip battery's curl-deepening rule: +1 iff the +probe rotation
        brings the child's distal landmark (vertex farthest from the pivot)
        nearer the recorded curl point."""
        v = self.geo[child]["verts"]
        landmark = v[int(np.argmax(np.linalg.norm(v - pivot, axis=1)))]
        d_plus = float(np.linalg.norm(hp.rodrigues(landmark[None, :], pivot, axis, probe)[0] - curl_pt))
        d_minus = float(np.linalg.norm(hp.rodrigues(landmark[None, :], pivot, axis, -probe)[0] - curl_pt))
        return 1 if d_plus < d_minus else -1, d_plus, d_minus, probe

    def _derive_knees(self):
        self.knee = {}
        e1 = self.hip["L"]["e1"]
        for side, bond_id, child, pes_id in (
                ("L", "bond.joint_02_06", 6, "bond.joint_02_15"),
                ("R", "bond.joint_03_07", 7, "bond.joint_03_17")):
            M, femur_pt, _, gap0 = self._realized_pair(bond_id)
            rng = self.bonds[bond_id]["joint_class"]["range_rad"]
            band_edge = max(abs(rng[0]), abs(rng[1]))
            probe = band_edge / 5.0
            pes_on_femur = self._realized_pair(pes_id)[1]
            s, dp, dm, pb = self._curl_probe_sign(M, e1, child, pes_on_femur, probe)
            # gait2392 knee_angle: flexion at the NEGATIVE end of the recorded
            # band (law doc section 1.4) => geometric angle = -s * theta
            self.knee[side] = dict(bond=bond_id, child=child, M=M, axis=e1.copy(),
                                   range=rng, sigma=-s, probe_rad=pb, gap0_mm=gap0,
                                   probe_d_plus_mm=dp, probe_d_minus_mm=dm,
                                   flex_end_recorded="negative (the cited gait2392 knee_angle band)")

    # --------------------------------------------------------------- elbows
    def _derive_elbows(self):
        self.elbow = {}
        for side, b1, b2, child1, hand_id in (
                ("L", "bond.joint_04_10", "bond.joint_04_12", 10, "bond.joint_04_08"),
                ("R", "bond.joint_05_11", "bond.joint_05_13", 11, "bond.joint_05_09")):
            M1 = self._realized_pair(b1)[0]
            M2 = self._realized_pair(b2)[0]
            pivot = (M1 + M2) / 2.0
            axis = M2 - M1
            axis = axis / np.linalg.norm(axis)
            rng = self.bonds[b1]["joint_class"]["range_rad"]
            span = rng[1] - rng[0]
            probe = span / 5.0
            hand_on_hum = self._realized_pair(hand_id)[1]
            s, dp, dm, pb = self._curl_probe_sign(pivot, axis, child1, hand_on_hum, probe)
            floor = rng[0]  # the nearest lawful value to rest: argmin |theta-0|
            ch1 = int(self.bonds[b1]["members"][1].split("bone_")[1])
            ch2 = int(self.bonds[b2]["members"][1].split("bone_")[1])
            self.elbow[side] = dict(
                bonds=[b1, b2], children=[ch1, ch2],
                pivot=pivot, axis=axis, range=rng, sigma=s, probe_rad=pb,
                probe_d_plus_mm=dp, probe_d_minus_mm=dm,
                forced_theta=floor,
                forced_rule="the range floor: argmin |theta - 0| over the recorded range "
                            "(theta=0 is outside the monkeyArm elbow record)")

    # -------------------------------------------------------------- drivers
    def _derive_drivers(self):
        u = np.array([BANKED_TARSAL_AXIS], dtype=np.float64)[0]
        self.driver = {}
        for side, bond_id in (("L", "bond.joint_06_25"), ("R", "bond.joint_07_24")):
            pa_mem, ch_mem = self.bonds[bond_id]["members"]
            parent = int(pa_mem.split("bone_")[1])
            child = int(ch_mem.split("bone_")[1])
            vq, fq, medq = self.geo[child]["verts"], self.geo[child]["faces"], self.geo[child]["med"]
            g0, prov = hp.law_gap(vq, self.geo[parent]["verts"], self.geo[parent]["tree"])
            seed = int(prov[1])
            fit = hp.inlier_rule(vq, fq, vq[seed], medq)
            if fit.get("outcome") != "fixed_point":
                raise SystemExit("driver %s fit refused" % bond_id)
            c = np.array(fit["center_mm"], dtype=np.float64)
            bk = np.array(BANKED_TARSAL[bond_id]["center"], dtype=np.float64)
            if [rnd(x) for x in c] != [rnd(x) for x in bk]:
                raise SystemExit("driver %s fit drift vs banked tarsal constants" % bond_id)
            rng = self.bonds[bond_id]["joint_class"]["range_rad"]
            self.driver[side] = dict(bond=bond_id, child=child, c=c, axis=u.copy(),
                                     range=rng, band=fit["rms_residual_mm"],
                                     gap0_mm=g0,
                                     sign_rule="DEFERRED per the tarsal receipt (symmetric band)")

    # ---------------------------------------------------------------- trunk
    def _derive_trunk(self):
        c1 = self.geo[1]["verts"]
        cen = c1.mean(axis=0)
        cov = np.cov((c1 - cen).T)
        evals, evecs = np.linalg.eigh(cov)
        a = evecs[:, int(np.argmax(evals))]
        hips_mid = (self.hip["L"]["c"] + self.hip["R"]["c"]) / 2.0
        far = c1[int(np.argmax(np.linalg.norm(c1 - hips_mid, axis=1)))]
        if (far - hips_mid) @ a < 0:
            a = -a
        self.trunk_axis = a
        self.trunk_far_vertex = far
        self.hips_midpoint = hips_mid

    # ------------------------------------------------------------ objective
    def pad_centroids(self, x):
        T = self.fk(x)
        return np.array([T[r].pts(self.geo[r]["verts"]).mean(axis=0) for r in PAD_BONES])

    @staticmethod
    def _plane_stats(P):
        Pc = P - P.mean(axis=0)
        w, U = np.linalg.eigh(Pc.T @ Pc)
        return float(w[0]) / 4.0, U[:, 0]

    def objective_terms(self, x):
        P = self.pad_centroids(x)
        V, n = self._plane_stats(P)
        d = float((self.trunk_axis @ n) ** 2)
        return V, d

    def _derive_objective_constants(self):
        V0, n0 = self._plane_stats(np.array(
            [self.geo[r]["verts"].mean(axis=0) for r in PAD_BONES]))
        d0 = float((self.trunk_axis @ n0) ** 2)
        if d0 <= 0.0:
            raise SystemExit("degenerate rest trunk-level deficit")
        self.V_rest = V0
        self.d_rest = d0
        self.kappa = V0 / d0
        self.J_rest = V0 + self.kappa * d0

    # ------------------------------------------------------------------ FK
    BONE_PLAN = {
        1: (), 14: (), 16: (), 19: (),          # root / unbonded singletons
        4: (), 8: (), 5: (), 9: (),             # fore roots and hands (0-DOF to humerus)
        2: ("HL",), 15: ("HL",),
        6: ("HL", "KL"), 20: ("HL", "KL"),
        25: ("HL", "KL", "DL"), 22: ("HL", "KL", "DL"),
        3: ("HR",), 17: ("HR",),
        7: ("HR", "KR"), 21: ("HR", "KR"), 18: ("HR", "KR"),
        24: ("HR", "KR", "DR"), 23: ("HR", "KR", "DR"),
        10: ("EL",), 12: ("EL",), 11: ("ER",), 13: ("ER",),
    }
    # x = [hipL f,a,r; hipR f,a,r; kneeL; kneeR; driverL; driverR]

    def local_xforms(self, x):
        x = list(x)
        hl, hr = self.hip["L"], self.hip["R"]
        kl, kr = self.knee["L"], self.knee["R"]
        dl, dr = self.driver["L"], self.driver["R"]
        el, er = self.elbow["L"], self.elbow["R"]
        th_eL = el["sigma"] * el["forced_theta"]
        th_eR = er["sigma"] * er["forced_theta"]
        H_L = Xform.rotation(hl["c"], hl["e1"], x[0]) @ \
            Xform.rotation(hl["c"], hl["e2"], x[1]) @ \
            Xform.rotation(hl["c"], hl["e3"], x[2])
        H_R = Xform.rotation(hr["c"], hr["e1"], x[3]) @ \
            Xform.rotation(hr["c"], hr["e2"], x[4]) @ \
            Xform.rotation(hr["c"], hr["e3"], x[5])
        K_L = Xform.rotation(kl["M"], kl["axis"], kl["sigma"] * x[6])
        K_R = Xform.rotation(kr["M"], kr["axis"], kr["sigma"] * x[7])
        D_L = Xform.rotation(dl["c"], dl["axis"], x[8])
        D_R = Xform.rotation(dr["c"], dr["axis"], x[9])
        E_L = Xform.rotation(el["pivot"], el["axis"], th_eL)
        E_R = Xform.rotation(er["pivot"], er["axis"], th_eR)
        return {"HL": H_L, "HR": H_R, "KL": K_L, "KR": K_R,
                "DL": D_L, "DR": D_R, "EL": E_L, "ER": E_R}

    def fk(self, x):
        loc = self.local_xforms(x)
        out = {}
        for r, chain in self.BONE_PLAN.items():
            T = Xform()
            for step in chain:
                T = T @ loc[step]
            out[r] = T
        return out

    def posed_verts(self, x, r):
        return self.fk(x)[r].pts(self.geo[r]["verts"])

    # ----------------------------------------------------------- law checks
    def law_gap_posed(self, x, child, parent):
        vq = self.posed_verts(x, child)
        return hp.law_gap(vq, self.geo[parent]["verts"], self.geo[parent]["tree"])

    def relative_gap(self, x, bone_a, bone_b):
        """Law gap between two posed membranes (both transformed)."""
        va = self.posed_verts(x, bone_a)
        vb = self.posed_verts(x, bone_b)
        return hp.law_gap(va, vb, cKDTree(vb))

    def rest_gap(self, bone_a, bone_b):
        return hp.law_gap(self.geo[bone_a]["verts"], self.geo[bone_b]["verts"],
                          self.geo[bone_b]["tree"])

    # ------------------------------------------------------ the solve input
    def bounds(self):
        b = []
        for side in ("L", "R"):
            b.extend([tuple(r) for r in self.hip[side]["range"]])
        b.append(tuple(self.knee["L"]["range"]))
        b.append(tuple(self.knee["R"]["range"]))
        b.append(tuple(self.driver["L"]["range"]))
        b.append(tuple(self.driver["R"]["range"]))
        return b

    def hip_seat_constraints(self, x):
        vals = []
        for side, k in (("L", 2), ("R", 3)):
            g, _ = self.law_gap_posed(x, k, 1)
            vals.append(CUT_MM - g)
        return np.array(vals)

    def all_seat_constraints(self, x):
        """Hip seats + the two tarsal loop seats (amendment 2: the committed cut
        as the derived band narrowing the class record itself pre-registered)."""
        vals = list(self.hip_seat_constraints(x))
        for a, b in ((20, 25), (21, 24)):
            g, _ = self.relative_gap(x, a, b)
            vals.append(CUT_MM - g)
        return np.array(vals)

    VAR_NAMES = ["hipL_flexion", "hipL_adduction", "hipL_rotation",
                 "hipR_flexion", "hipR_adduction", "hipR_rotation",
                 "kneeL", "kneeR", "driverL_06_25", "driverR_07_24"]
