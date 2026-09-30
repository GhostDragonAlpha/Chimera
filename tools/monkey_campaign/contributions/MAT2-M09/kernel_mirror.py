"""MAT2-M09 kernel mirror — the declared CUDA transcription source (numpy).

MirrorWorld re-states AssemblyRun's declared substep order
(gravity_damping -> connective_elements -> contact -> integration_projection)
over ONE flat system state (X/V rows 0..7 = bone_a, 8..15 = bone_b; the
pinned ground is a static constant table), with per-bone/per-substep partials
folded in the declared interleaved order into the resident diagnostic block
slots the CUDA world (resident_bones.py) emits. The contact solve is a
statement-level transcription of the hash-pinned M06 local_contact
solve_contact (pure float arithmetic), and the swept candidate search keeps
the pinned M06 sweep_prune/tri_tri_closest calls on identical inputs, so the
mirror is validated BITWISE against the oracle (mirror_rehearsal mode:
every row float and both state_hash chains) before any GPU work — the
CPU-FIRST law. The CUDA kernels are a mechanical transcription of these
functions; X3 (the GPU bank) measures that port under the frozen windows.

No GPU is touched here. Refusals are named codes; no RNG; no wall-clock.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
for _p in (str(HERE), str(CONTRIB / 'MAT2-M01'), str(CONTRIB / 'MAT2-M03'),
           str(CONTRIB / 'MAT2-M05'), str(CONTRIB / 'MAT2-M06')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import assembly as asm  # noqa: E402  (the CPU oracle: constants + digest)
import local_contact as lc  # noqa: E402  (M06 narrow phase, hash-pinned)
import pressure_membrane as pm  # noqa: E402  (M03 Membrane, hash-pinned)

# ---- frozen sizes -----------------------------------------------------------
N_BONES, N_VERT, N_TRI, N_EDGES = 2, 8, 12, 24
NV = N_BONES * N_VERT                 # 16 flat vertex rows
N_ENTRIES = 26                        # 12 + 12 bone tris + 2 ground tris
N_SUB = asm.N_SUB
DT_S = asm.DT_S
H_SUB = asm.H_SUB
GS_TOL_N_S = asm.GS_TOL_N_S
GS_CAP = asm.GS_CAP
XPBD_TOL_M = asm.XPBD_TOL_M
XPBD_ITERATIONS_CAP = asm.XPBD_ITERATIONS_CAP
XPBD_COMPLIANCE = asm.XPBD_COMPLIANCE_M_PER_N
THICKNESS_M = asm.THICKNESS_M
CONTACT_MARGIN_M = lc.MARGIN
CCD_TOL_M = lc.CCD_TOL_M
BETA_OVER_DT = lc.BETA / lc.DT
SLOP_M = lc.SLOP_M
MU_TINY = lc.MU_TINY
RESTITUTION = lc.RESTITUTION
G_M_S2 = asm.G_M_S2
TICKS = asm.TICKS
MAX_ACTIVE = 128                      # declared device cap (fixture max 30)

SCHEMA = 'chimera.m09_kernel_mirror.v1'
DIAG = 96

# diagnostic block slots (must match resident_bones.py exactly)
(D_KE, D_USCAFF, D_COMX, D_COMY, D_COMZ, D_MAXSPD, D_MINZ,
 D_GAP, D_JGAP, D_JNX, D_JNY, D_JNZ, D_JJN, D_ACTIVE, D_ITERS, D_GSRES,
 D_JNTOT, D_DFRIC, D_DIMP, D_WCKE, D_WACT, D_WLIG, D_WCAP, D_WGRAV,
 D_QDAMP, D_QCONTACT, D_QPROJ, D_EDISS, D_RESID, D_BOUND, D_EMECH,
 D_LIGT, D_LIGFX, D_LIGFY, D_LIGFZ, D_LIGEXT, D_CAPAX, D_CAPFX, D_CAPFY,
 D_CAPFZ, D_ULIG, D_UCAP, D_LIGBOUND, D_CAPBOUND,
 D_REST00, D_REST01, D_REST02, D_REST10, D_REST11, D_REST12, D_REST20,
 D_REST21, D_REST22,
 D_LEDGERW, D_ANCHORERR, D_GIMPX, D_GIMPY, D_GIMPZ, D_GJNA, D_GJNB,
 D_RECIP, D_TICK, D_STATUS, D_DIGEST) = range(64)
# slots 64..95 spare (kept zero; the digest folds the whole declared block)

# per-bone per-substep pass slots
N_PASS = 18
(P_WGRAV, P_QDAMP, P_IMPGX, P_IMPGY, P_IMPGZ, P_DMPX, P_DMPY, P_DMPZ,
 P_WLIG, P_WCAP, P_WACT, P_ELMX, P_ELMY, P_ELMZ, P_CIMPX, P_CIMPY,
 P_CIMPZ, P_LEDGER) = range(N_PASS)

# system per-substep pass slots
N_SYS = 31
(S_QCONTACT, S_DFRIC, S_DIMP, S_JNTOT, S_ITERS, S_GSRES, S_ACTIVE,
 S_JGAP, S_JHAS, S_JNX, S_JNY, S_JNZ, S_JJN, S_GJNA, S_GJNB,
 S_BBIX, S_BBIY, S_BBIZ, S_CAX, S_CAY, S_CAZ, S_CBX, S_CBY, S_CBZ,
 S_CGX, S_CGY, S_CGZ, S_RECX, S_RECY, S_RECZ, S_QPROJ) = range(N_SYS)

STATUS_OK = 0.0
STATUS_PAIRCAP = 102.0
STATUS_CONVERGENCE = 103.0
STATUS_NONFINITE = 104.0

E_ORDER = 'declared_order_mismatch'
E_TICK = 'tick_sequence_invalid'
E_BYTES = 'state_roundtrip_budget_exceeded'
E_PAIRCAP = 'contact_pair_slot_overflow'

TELEMETRY_BUDGET_UP_PER_TICK = 256
TELEMETRY_BUDGET_DOWN_PER_COMP = 1024
CMD_F64 = 5                           # tick, act_force_x, damping, bind, release


def require(condition, code):
    if not condition:
        raise ValueError(code)


def npsum(a, n):
    """numpy ndarray.sum() pairwise order (n<8 sequential from 0.0, else
    the 8-accumulator blocked scheme with sequential remainder)."""
    if n < 8:
        res = 0.0
        for i in range(n):
            res += a[i]
        return res
    r0 = a[0]; r1 = a[1]; r2 = a[2]; r3 = a[3]
    r4 = a[4]; r5 = a[5]; r6 = a[6]; r7 = a[7]
    lim = n - (n % 8)
    i = 8
    while i < lim:
        r0 += a[i]; r1 += a[i + 1]; r2 += a[i + 2]; r3 += a[i + 3]
        r4 += a[i + 4]; r5 += a[i + 5]; r6 += a[i + 6]; r7 += a[i + 7]
        i += 8
    res = ((r0 + r1) + (r2 + r3)) + ((r4 + r5) + (r6 + r7))
    while i < n:
        res += a[i]
        i += 1
    return res


def sha_digest(value):
    return asm.digest(value)


def block_digest(block, tick):
    """The declared tick-digest chain over the diagnostic block (the D_DIGEST
    slot folds as 0.0 — zero-then-fold, the M08 convention; the accumulator's
    drift makes skip-the-slot NOT equivalent)."""
    d = 0.0
    for i in range(DIAG):
        v = 0.0 if i == D_DIGEST else block[i]
        d = (d * 1.0000000000000002 + v * (i + 1)) % 1000000007.0
    return (d + float(tick) * 7919.0) % 1000000007.0


# ---- host topology tables (construction only; from the oracle's builder) ----

class _Tables:
    """Immutable per-bone topology extracted ONCE from the declared
    BoneBody construction (never per tick)."""

    def __init__(self):
        bones = (asm.BoneBody('bone_a', asm.bone_a_vertices(), asm.MASS_A_KG),
                 asm.BoneBody('bone_b', asm.bone_b_vertices(), asm.MASS_B_KG))
        self.rest = [b.rest.copy() for b in bones]
        self.tris = [b.triangles.copy() for b in bones]
        self.edges = [np.array(b.edge_list, dtype=np.int64) for b in bones]
        self.rest_lengths = [np.array(b.rest_lengths, dtype=np.float64)
                             for b in bones]
        self.masses = [b.masses.copy() for b in bones]
        self.inv_masses = [b.inv_masses.copy() for b in bones]
        self.rest_mean = [b.rest_mean.copy() for b in bones]
        self.rest_head_anchor = [b.rest_head_anchor.copy() for b in bones]
        self.head_tri_vids = [list(b.head_tri_vids) for b in bones]
        self.total_mass = [b.total_mass for b in bones]
        ground = asm.ground_body()
        self.ground_verts = np.array(ground.vertices, dtype=np.float64)
        self.ground_tris = np.array(ground.triangles, dtype=np.int64)


TABLES = _Tables()


# ---- flat port views (the BoneTriPort/GroundPort protocol on flat state) ----

class _BoneView:
    """Per-bone (8,3) views into the flat world arrays."""

    def __init__(self, world, b):
        self._world = world
        self.b = b
        self.body_id = ('bone_a', 'bone_b')[b]
        self.x = world.X[b * N_VERT:(b + 1) * N_VERT]
        self.v = world.V[b * N_VERT:(b + 1) * N_VERT]
        self.triangles = TABLES.tris[b]

    def mean_translation(self):
        return self.x.mean(axis=0) - TABLES.rest_mean[self.b]

    @property
    def head_anchor(self):
        return TABLES.rest_head_anchor[self.b] + self.mean_translation()

    def tri_area_now(self, tri_index):
        m = pm.Membrane(self.x, self.triangles, self.body_id)
        return float(m.areas[int(tri_index)])


class _FlatBonePort:
    """Transcription of BoneTriPort (assembly.py) over flat state. The port
    SHARES the world's per-bone view object (single state owner; the stages
    write the world buffers in place, exactly like the resident kernels)."""

    def __init__(self, world, b, tri_index):
        self._view = world.views[b]
        self.tri_index = int(tri_index)
        self.vids = tuple(int(i) for i in TABLES.tris[b][tri_index])
        self.mass_kg = float(TABLES.masses[b][list(self.vids)].sum())
        require(self.mass_kg > 0.0, 'port_mass_invalid')
        self.mu_s, self.mu_k = asm.BONE_MU
        self.thickness_m = THICKNESS_M
        self.id = f'{self._view.body_id}/port:t{self.tri_index}'
        self.matter_id = f'mat_{self._view.body_id}'

    @property
    def velocity(self):
        return self._view.v[list(self.vids)].mean(axis=0)

    @velocity.setter
    def velocity(self, value):
        delta = np.asarray(value, dtype=np.float64) - self.velocity
        self._view.v[list(self.vids)] += delta

    def inv_mass(self):
        return 1.0 / self.mass_kg

    def verts(self):
        return [tuple(self._view.x[i]) for i in self.vids]

    def tri_area_now(self, tri_index):
        return self._view.tri_area_now(tri_index)


class _FlatGroundPort:
    """Transcription of GroundPort (assembly.py): pinned."""

    def __init__(self, tri_index):
        self.tri_index = int(tri_index)
        self.vids = tuple(int(i) for i in TABLES.ground_tris[tri_index])
        self.mu_s, self.mu_k = asm.GROUND_MU
        self.thickness_m = THICKNESS_M
        self.id = f'ground/port:t{self.tri_index}'
        self.matter_id = 'mat_ground'
        self.mass_kg = 0.0

    @property
    def velocity(self):
        return np.zeros(3)

    @velocity.setter
    def velocity(self, value):
        pass  # pinned: the reaction is the recorded impulse itself

    def inv_mass(self):
        return 0.0

    def verts(self):
        return [tuple(TABLES.ground_verts[i]) for i in self.vids]


def _body_of(port_id):
    head = port_id.split('/')[0]
    require(head in ('bone_a', 'bone_b', 'ground'), 'unknown_port_body')
    return head


# ---- the contact solve, statement-level (local_contact.solve_contact) -------

def solve_contact_mirror(body_a, body_b, gap, normal, pair_key):
    """Statement-level transcription of the hash-pinned M06 solve_contact
    (the CUDA transcription source; float ops in the declared order)."""
    require(lc.finite_vec(normal), 'nonfinite_state')
    n = normal
    inv_ma, inv_mb = body_a.inv_mass(), body_b.inv_mass()
    denom = inv_ma + inv_mb
    require(denom > 0.0, 'nonfinite_state')
    m_eff = 1.0 / denom
    va = body_a.velocity
    vb = body_b.velocity
    rv = lc.vsub(va, vb)
    vn = lc.vdot(rv, n)
    pen = -gap
    bias = lc.BETA / lc.DT * max(pen - lc.SLOP_M, 0.0)
    jn = max(m_eff * (-(1.0 + lc.RESTITUTION) * vn + bias), 0.0)
    jn_vec = lc.vscale(n, jn)
    body_a.velocity = lc.vadd(body_a.velocity, lc.vscale(jn_vec, inv_ma))
    body_b.velocity = lc.vsub(body_b.velocity, lc.vscale(jn_vec, inv_mb))
    rv = lc.vsub(body_a.velocity, body_b.velocity)
    vn_after = lc.vdot(rv, n)
    vt_vec = lc.vsub(rv, lc.vscale(n, vn_after))
    vt_pre = lc.vlen(vt_vec)
    mu_s, mu_k = lc.pair_mu(body_a, body_b)
    jt_mag, mode = 0.0, 'still'
    jt_vec = (0.0, 0.0, 0.0)
    if vt_pre > MU_TINY:
        jt_req = m_eff * vt_pre
        jt_dir = lc.vscale(vt_vec, -1.0 / vt_pre)
        if jt_req <= mu_s * jn:
            jt_mag, mode = jt_req, 'stick'
        else:
            jt_mag, mode = mu_k * jn, 'slip'
        jt_vec = lc.vscale(jt_dir, jt_mag)
        body_a.velocity = lc.vadd(body_a.velocity, lc.vscale(jt_vec, inv_ma))
        body_b.velocity = lc.vsub(body_b.velocity, lc.vscale(jt_vec, inv_mb))
    rv = lc.vsub(body_a.velocity, body_b.velocity)
    vt_post_vec = lc.vsub(rv, lc.vscale(n, lc.vdot(rv, n)))
    vt_post = lc.vlen(vt_post_vec)
    w_f_ke = 0.5 * m_eff * max(vt_pre * vt_pre - vt_post * vt_post, 0.0)
    impulse = lc.vadd(jn_vec, jt_vec)
    return {
        'pair_key': pair_key, 'normal': list(n), 'gap_m': gap,
        'penetration_m': pen, 'jn_Ns': jn, 'jt_Ns': jt_mag, 'mode': mode,
        'impulse_on_a': list(impulse),
        'impulse_on_b': list(lc.vscale(impulse, -1.0)),
        'inv_ma': inv_ma, 'inv_mb': inv_mb, 'm_eff': m_eff,
        'vt_pre': vt_pre, 'vt_post': vt_post, 'w_f_ke_J': w_f_ke,
        'mu_used': (0.0 if jt_mag == 0.0 else
                    (mu_s if mode == 'stick' else mu_k)),
    }


# ---- connective elements (transcribed element laws) --------------------------

class _ElemState:
    """The M05 BondElement status machine fields the mirror needs."""

    def __init__(self, kind):
        self.kind = kind                # 'lig' | 'cap'
        self.status = 'planned'
        self.bound_tick = None
        self.released_tick = None
        self.e_release_j = None
        self.rest_length_m = (asm.LIG_REST_LENGTH_M if kind == 'lig'
                              else None)

    @property
    def active(self):
        return self.status == 'qualified'


# ---- the mirror world --------------------------------------------------------

class MirrorWorld:
    """Flat-state executor of M09's declared tick; produces the oracle row
    (bitwise) and the resident diagnostic block (declared-order fold)."""

    def __init__(self):
        self.X = np.array([TABLES.rest[0], TABLES.rest[1]],
                          dtype=np.float64).reshape(NV, 3).copy()
        self.V = np.zeros_like(self.X)
        self.views = (_BoneView(self, 0), _BoneView(self, 1))
        self.ports = {
            'bone_a': [_FlatBonePort(self, 0, i) for i in range(N_TRI)],
            'bone_b': [_FlatBonePort(self, 1, i) for i in range(N_TRI)],
            'ground': [_FlatGroundPort(i) for i in range(2)],
        }
        self.lig = None
        self.cap = None
        self.e_diss_release = 0.0
        self.ticks = []
        self.tick = 0
        self.host_bytes_up = 0
        self.host_bytes_down = 0
        self.blocks = []
        self.digests = ([], [])
        self._pass = np.zeros((N_BONES, N_SUB, N_PASS), dtype=np.float64)
        self._sys = np.zeros((N_SUB, N_SYS), dtype=np.float64)
        self._vstart_tick = np.zeros((N_BONES, N_VERT, 3), dtype=np.float64)
        self._vstart_sub = np.zeros((N_BONES, N_SUB, N_VERT, 3))
        self._vgrav_sub = np.zeros((N_BONES, N_SUB, N_VERT, 3))
        self._ld_sub = np.zeros((N_BONES, N_SUB, N_VERT, 3))
        self.declaration = {
            'schema': SCHEMA,
            'order': list(asm.DECLARED_ORDER),
            'dt_s': DT_S, 'substeps_per_tick': N_SUB, 'ticks': TICKS,
            'n_bones': N_BONES, 'n_vert_per_bone': N_VERT,
            'n_entries': N_ENTRIES, 'max_active': MAX_ACTIVE,
            'diag_f64_per_comp': DIAG, 'cmd_f64': CMD_F64,
            'telemetry_budget_up_bytes_per_tick':
                TELEMETRY_BUDGET_UP_PER_TICK,
            'telemetry_budget_down_bytes_per_comp':
                TELEMETRY_BUDGET_DOWN_PER_COMP,
            'windows': {'position_m': 1e-12, 'scalar_relative': 1e-9},
        }
        self.order_digest = sha_digest(self.declaration)

    # -- element laws (transcribed; np calls identical to the oracle) -------
    def _head(self, b):
        return self.views[b].head_anchor

    def _lig_delta(self):
        return self._head(1) - self._head(0)

    def _lig_axis(self):
        d = self._lig_delta()
        n = float(np.linalg.norm(d))
        require(n > 0.0, 'degenerate_ligament_axis')
        return d / n

    def _lig_extension(self):
        return float(np.linalg.norm(self._lig_delta())) \
            - asm.LIG_REST_LENGTH_M

    def _shear(self, d, a):
        return d - float(np.dot(d, a)) * a

    def _lig_tension(self):
        if self.lig.status == 'planned':
            raise ValueError('bond_not_bound')
        if not self.lig.active:
            return 0.0
        return asm.LIG_K_T_N_PER_M * max(0.0, self._lig_extension())

    def _lig_force_on_b(self):
        if self.lig.status == 'planned':
            raise ValueError('bond_not_bound')
        if not self.lig.active:
            return np.zeros(3)
        t = self._lig_tension()
        shear = asm.LIG_K_S_N_PER_M * self._shear(self._lig_delta(),
                                                  self._lig_axis())
        return -t * self._lig_axis() - shear

    def _lig_stored_energy(self):
        if self.lig.status == 'planned':
            raise ValueError('bond_not_bound')
        if not self.lig.active:
            return 0.0
        e = max(0.0, self._lig_extension())
        d = self._shear(self._lig_delta(), self._lig_axis())
        return (0.5 * asm.LIG_K_T_N_PER_M * e * e
                + 0.5 * asm.LIG_K_S_N_PER_M * float(np.dot(d, d)))

    def _cap_delta(self):
        return self._head(1) - self._head(0)

    def _cap_axis(self):
        d = self._cap_delta()
        n = float(np.linalg.norm(d))
        require(n > 0.0, 'degenerate_capsule_axis')
        return d / n

    def _cap_extension(self):
        return float(np.linalg.norm(self._cap_delta())) \
            - self.cap.rest_length_m

    def _cap_axial(self):
        if self.cap.status == 'planned':
            raise ValueError('bond_not_bound')
        if not self.cap.active:
            return 0.0
        return asm.CAP_K_C_N_PER_M * self._cap_extension()

    def _cap_force_on_b(self):
        if self.cap.status == 'planned':
            raise ValueError('bond_not_bound')
        if not self.cap.active:
            return np.zeros(3)
        f = self._cap_axial()
        shear = asm.CAP_K_S_N_PER_M * self._shear(self._cap_delta(),
                                                  self._cap_axis())
        return -f * self._cap_axis() - shear

    def _cap_stored_energy(self):
        if self.cap.status == 'planned':
            raise ValueError('bond_not_bound')
        if not self.cap.active:
            return 0.0
        e = self._cap_extension()
        d = self._shear(self._cap_delta(), self._cap_axis())
        return (0.5 * asm.CAP_K_C_N_PER_M * e * e
                + 0.5 * asm.CAP_K_S_N_PER_M * float(np.dot(d, d)))

    def _distribute_to_head(self, b, force):
        """BoneBody.distribute_to_head transcription (pm.Membrane areas)."""
        view = self.views[b]
        m = pm.Membrane(view.x, view.triangles, view.body_id)
        a = np.array([m.areas[0], m.areas[1]])
        total = float(a.sum())
        share0 = force * (a[0] / total)
        share1 = force - share0
        loads = np.zeros_like(view.x)
        for tri, share in zip(TABLES.head_tri_vids[b], (share0, share1)):
            for vid in tri:
                loads[vid] += share / 3.0
        return loads

    # -- assembly acts -------------------------------------------------------
    def _bind(self, tick):
        require(self.lig is None and self.cap is None,
                'connections_already_exist')
        require(tick == asm.BIND_TICK, 'bind_tick_mismatch')
        self.lig = _ElemState('lig')
        self.cap = _ElemState('cap')
        self.lig.status = 'qualified'
        self.lig.bound_tick = int(tick)
        self.cap.status = 'qualified'
        self.cap.bound_tick = int(tick)
        self.cap.rest_length_m = float(np.linalg.norm(self._cap_delta()))

    def _release(self, tick):
        require(tick == asm.RELEASE_TICK, 'release_tick_mismatch')
        require(self.lig is not None and self.cap is not None,
                'release_of_unbound_bond')
        self.lig.e_release_j = self._lig_stored_energy()
        self.lig.status = 'released'
        self.lig.released_tick = int(tick)
        self.cap.e_release_j = self._cap_stored_energy()
        self.cap.status = 'released'
        self.cap.released_tick = int(tick)
        self.e_diss_release = self.lig.e_release_j + self.cap.e_release_j

    # -- stage helpers -------------------------------------------------------
    def _element_loads(self):
        view_a, view_b = self.views
        zeros_a = np.zeros_like(view_a.x)
        zeros_b = np.zeros_like(view_b.x)
        lig_a = np.zeros_like(view_a.x)
        lig_b = np.zeros_like(view_b.x)
        cap_a = np.zeros_like(view_a.x)
        cap_b = np.zeros_like(view_b.x)
        if self.lig is not None and self.lig.active:
            f_b = self._lig_force_on_b()
            f_a = -f_b
            lig_b = self._distribute_to_head(1, f_b)
            lig_a = self._distribute_to_head(0, f_a)
        if self.cap is not None and self.cap.active:
            f_b = self._cap_force_on_b()
            f_a = -f_b
            cap_b = self._distribute_to_head(1, f_b)
            cap_a = self._distribute_to_head(0, f_a)
        return {'loads_a': lig_a + cap_a, 'loads_b': lig_b + cap_b,
                'lig_a': lig_a, 'lig_b': lig_b, 'cap_a': cap_a,
                'cap_b': cap_b}

    def _actuator_load(self, tick):
        loads = np.zeros_like(self.views[1].x)
        if tick in asm.PRESS_TICKS:
            loads += (asm.PRESS_FORCE_N / 8.0) * np.array([-1.0, 0.0, 0.0])
        elif tick in asm.PULL_TICKS:
            loads += (asm.PULL_FORCE_N / 8.0) * np.array([1.0, 0.0, 0.0])
        return loads

    def _kinetic_bone(self, b):
        v = self.views[b].v
        m = TABLES.masses[b]
        return float((0.5 * m[:, None] * v ** 2).sum())

    def _kinetic(self):
        ka = self._kinetic_bone(0)
        kb = self._kinetic_bone(1)
        return ka + kb

    def _scaffold_energy(self, b):
        view = self.views[b]
        edges = TABLES.edges[b]
        rest_lengths = TABLES.rest_lengths[b]
        total = 0.0
        for e in range(edges.shape[0]):
            a1, a2 = int(edges[e, 0]), int(edges[e, 1])
            length = float(np.linalg.norm(view.x[a2] - view.x[a1]))
            total += (length - rest_lengths[e]) ** 2 \
                / (2.0 * XPBD_COMPLIANCE)
        return total

    # -- contact stage -------------------------------------------------------
    def _contact_stage(self):
        holders = (self.ports['bone_a'] + self.ports['bone_b']
                   + self.ports['ground'])
        motion = 0.0
        for b in holders:
            motion = max(motion, float(np.linalg.norm(b.velocity)) * H_SUB)
        inflate = motion + THICKNESS_M + lc.MARGIN
        entries = []
        for b in holders:
            lo, hi = lc.tri_aabb(b.verts(), inflate)
            entries.append((b.id.split('/')[0], 0, lo, hi))
        cand = [pair for pair in lc.sweep_prune(entries)
                if not (holders[pair[0]].id.startswith('ground')
                        and holders[pair[1]].id.startswith('ground'))]
        active = []
        for (i, j) in cand:
            ba, bb = holders[i], holders[j]
            if ba.id.split('/')[0] > bb.id.split('/')[0]:
                ba, bb = bb, ba
            tai, tbi = ba.verts(), bb.verts()
            p, q, dist = lc.tri_tri_closest(*tai, *tbi)
            gap = dist - 0.5 * (ba.thickness_m + bb.thickness_m)
            if gap <= lc.MARGIN + lc.CCD_TOL_M:
                if dist > 0.0:
                    normal = lc.vunit(lc.vsub(p, q))
                else:
                    normal = (1.0, 0.0, 0.0) \
                        if ba.id.startswith('bone') \
                        and bb.id.startswith('bone') else (0.0, 0.0, 1.0)
                active.append((ba, bb, gap, normal, (i, j)))
        ke_pre = self._kinetic()
        records = []
        max_jn = 0.0
        iterations = 0
        contact_impulse = {'bone_a': np.zeros(3), 'bone_b': np.zeros(3),
                           'ground': np.zeros(3)}
        recip = (0.0, 0.0, 0.0)
        d_friction = 0.0
        d_impact_physical = 0.0
        jn_applied_total = 0.0
        accum_jn = {}
        for iteration in range(GS_CAP):
            iterations = iteration + 1
            records = []
            pass_max = 0.0
            for (va, vb, gap, normal, key) in active:
                va_pre = np.asarray(va.velocity,
                                    dtype=np.float64).copy()
                vb_pre = np.asarray(vb.velocity,
                                    dtype=np.float64).copy()
                rec = solve_contact_mirror(va, vb, gap, normal, key)
                va_post = np.asarray(va.velocity, dtype=np.float64)
                vb_post = np.asarray(vb.velocity, dtype=np.float64)
                rec['body_a'] = va.id
                rec['body_b'] = vb.id
                rec['tri_a'] = va.tri_index
                rec['tri_b'] = vb.tri_index
                rec['area_a'] = va.tri_area_now(rec['tri_a']) \
                    if isinstance(va, _FlatBonePort) \
                    else lc.tri_area(*va.verts())
                rec['area_b'] = vb.tri_area_now(rec['tri_b']) \
                    if isinstance(vb, _FlatBonePort) \
                    else lc.tri_area(*vb.verts())
                pass_max = max(pass_max, rec['jn_Ns'], abs(rec['jt_Ns']))
                records.append(rec)
                accum_jn[key] = accum_jn.get(key, 0.0) + abs(rec['jn_Ns'])
                ja = np.array(rec['impulse_on_a'])
                jb = np.array(rec['impulse_on_b'])
                contact_impulse[_body_of(rec['body_a'])] += ja
                contact_impulse[_body_of(rec['body_b'])] += jb
                recip = lc.vadd(recip, tuple(rec['impulse_on_a']))
                recip = lc.vadd(recip, tuple(rec['impulse_on_b']))
                d_friction += float(rec.get('w_f_ke_J', 0.0))
                jn_applied_total += abs(rec['jn_Ns'])
                vn_pre = float(np.dot(va_pre - vb_pre,
                                      np.asarray(normal,
                                                 dtype=np.float64)))
                if vn_pre < 0.0:
                    d_impact_physical += 0.5 * rec['m_eff'] * vn_pre \
                        * vn_pre
            max_jn = pass_max
            if pass_max <= GS_TOL_N_S:
                break
        require(max_jn <= GS_TOL_N_S, 'convergence_gate_not_met')
        ke_after = self._kinetic()
        joint_gap = None
        joint_normal = None
        joint_jn = 0.0
        patch = []
        ground_jn = {'bone_a': 0.0, 'bone_b': 0.0}
        bb_impulse_total = np.zeros(3)
        for rec, (va, vb, gap, normal, key) in zip(records, active):
            names = (rec['body_a'], rec['body_b'])
            heads = {n.split('/')[0] for n in names}
            if heads == {'bone_a', 'bone_b'}:
                joint_gap = float(gap)
                joint_normal = [float(c) for c in normal]
                jn_acc = accum_jn.get(key, 0.0)
                joint_jn += jn_acc
                patch.append((rec['body_a'], int(rec['tri_a']), jn_acc))
                patch.append((rec['body_b'], int(rec['tri_b']), jn_acc))
            elif 'ground' in heads:
                other = 'bone_a' if 'bone_a' in heads else 'bone_b'
                ground_jn[other] += accum_jn.get(key, 0.0)
        for rec, (va, vb, gap, normal, key) in zip(records, active):
            heads = {rec['body_a'].split('/')[0],
                     rec['body_b'].split('/')[0]}
            if heads == {'bone_a', 'bone_b'}:
                bb_impulse_total += (np.array(rec['impulse_on_a'])
                                     + np.array(rec['impulse_on_b']))
        return {
            'records_count': len(records), 'iterations': iterations,
            'gs_residual_N_s': max_jn,
            'contact_impulse': contact_impulse,
            'recip_residual': lc.vlen(recip),
            'w_contact_ke_j': -(ke_after - ke_pre),
            'd_friction_j': d_friction,
            'd_impact_physical_j': d_impact_physical,
            'jn_applied_total_N_s': jn_applied_total,
            'active_pairs': len(active),
            'joint_gap_m': joint_gap, 'joint_normal': joint_normal,
            'joint_jn_Ns': joint_jn, 'joint_patch': patch,
            'ground_jn_N_s': ground_jn,
            'bb_impulse': bb_impulse_total,
        }

    # -- XPBD projection ------------------------------------------------------
    def _project(self, b):
        view = self.views[b]
        edges = TABLES.edges[b]
        inv_masses = TABLES.inv_masses[b]
        rest_lengths = TABLES.rest_lengths[b]
        alpha_tilde = XPBD_COMPLIANCE / (H_SUB * H_SUB)
        lam = np.zeros(edges.shape[0])
        for _it in range(XPBD_ITERATIONS_CAP):
            worst = 0.0
            for e in range(edges.shape[0]):
                a1, a2 = int(edges[e, 0]), int(edges[e, 1])
                pa, pb = view.x[a1], view.x[a2]
                d = pb - pa
                length = float(np.linalg.norm(d))
                if length == 0.0:
                    continue
                grad = d / length
                c = length - rest_lengths[e]
                worst = max(worst, abs(c))
                w_sum = inv_masses[a1] + inv_masses[a2]
                dlam = (-c - alpha_tilde * lam[e]) / (w_sum + alpha_tilde)
                lam[e] += dlam
                view.x[a1] -= inv_masses[a1] * dlam * grad
                view.x[a2] += inv_masses[a2] * dlam * grad
            if worst <= XPBD_TOL_M:
                break

    # -- derived restraint (measurement only) ---------------------------------
    def _restraint_matrix(self):
        lig, cap = self.lig, self.cap
        k = np.zeros((3, 3))
        contrib = {}
        eye = np.eye(3)
        if lig is not None and lig.active:
            a = self._lig_axis()
            taut = 1.0 if self._lig_extension() > 0.0 else 0.0
            k_lig = asm.LIG_K_T_N_PER_M * taut * np.outer(a, a) \
                + asm.LIG_K_S_N_PER_M * (eye - np.outer(a, a))
            k = k + k_lig
            contrib['ligament'] = [float(c) for c in k_lig.ravel()]
        if cap is not None and cap.active:
            a = self._cap_axis()
            k_cap = asm.CAP_K_C_N_PER_M * np.outer(a, a) \
                + asm.CAP_K_S_N_PER_M * (eye - np.outer(a, a))
            k = k + k_cap
            contrib['capsule'] = [float(c) for c in k_cap.ravel()]
        return k, contrib

    def _restraint_recomputed(self):
        lig, cap = self.lig, self.cap
        terms = []
        if lig is not None and lig.active:
            a = self._lig_axis()
            outer = np.array([[a[i] * a[j] for j in range(3)]
                              for i in range(3)])
            taut = 1.0 if self._lig_extension() > 0.0 else 0.0
            terms.append(asm.LIG_K_T_N_PER_M * taut * outer
                         + asm.LIG_K_S_N_PER_M * (np.eye(3) - outer))
        if cap is not None and cap.active:
            a = self._cap_axis()
            outer = np.array([[a[i] * a[j] for j in range(3)]
                              for i in range(3)])
            terms.append(asm.CAP_K_C_N_PER_M * outer
                         + asm.CAP_K_S_N_PER_M * (np.eye(3) - outer))
        total = np.zeros((3, 3))
        for t in terms:
            total = total + t
        return total

    # -- one tick --------------------------------------------------------------
    def step_tick(self, tick, cmd=None):
        require(tick == self.tick, E_TICK)
        cmd = cmd or {}
        bind_flag = float(cmd.get('bind', 1.0 if tick == asm.BIND_TICK
                                  else 0.0))
        release_flag = float(cmd.get('release',
                                     1.0 if tick == asm.RELEASE_TICK
                                     else 0.0))
        damping = float(cmd.get('damping', asm.damping_of_tick(tick)))
        self.host_bytes_up += CMD_F64 * 8
        acts = []
        if bind_flag == 1.0 and tick == asm.BIND_TICK:
            self._bind(tick)
            acts.append('bind')
        if release_flag == 1.0 and tick == asm.RELEASE_TICK:
            self._release(tick)
            acts.append('release')
        e_rel_tick = self.e_diss_release if tick == asm.RELEASE_TICK \
            else 0.0
        bones = (0, 1)
        gvec = np.array([0.0, 0.0, -G_M_S2])
        W = {'act': 0.0, 'lig': 0.0, 'cap': 0.0, 'grav': 0.0}
        Q_damp = 0.0
        Q_contact = 0.0
        Q_proj = 0.0
        ledger_worst = {b: 0.0 for b in bones}
        for b in bones:
            self._vstart_tick[b] = self.views[b].v.copy()
        contact_acc = {'bone_a': np.zeros(3), 'bone_b': np.zeros(3),
                       'ground': np.zeros(3)}
        recip_worst = 0.0
        n_active = 0
        joint_gap = None
        joint_normal = None
        joint_jn = 0.0
        gs_worst_tick = 0.0
        patch = {}
        d_friction = d_impact = jn_total = 0.0
        iters = 0
        imp_grav = {b: np.zeros(3) for b in bones}
        imp_damp = {b: np.zeros(3) for b in bones}
        imp_elem = {b: np.zeros(3) for b in bones}
        bb_impulse_tick = np.zeros(3)
        ground_jn_tick = {'bone_a': 0.0, 'bone_b': 0.0}
        self._pass[:, :, :] = 0.0
        self._sys[:, :] = 0.0
        for _sub in range(N_SUB):
            # stage 1: gravity (work recorded), then declared damping (KE)
            v_grav = {}
            v_start_sub = {}
            for b in bones:
                view = self.views[b]
                masses = TABLES.masses[b]
                v0 = view.v.copy()
                vg = v0 + gvec * H_SUB
                dx = 0.5 * (v0 + vg) * H_SUB
                w_grav_p = float((masses[:, None] * gvec * dx).sum())
                kin0 = float((0.5 * masses[:, None] * vg ** 2).sum())
                view.v[:] = vg * (1.0 - damping * H_SUB)
                kin1 = float((0.5 * masses[:, None] * view.v ** 2).sum())
                q_damp_p = kin0 - kin1
                v_start_sub[b] = v0
                v_grav[b] = vg
                imp_grav_p = TABLES.total_mass[b] * gvec * H_SUB
                imp_damp_p = (masses[:, None] * (view.v - vg)).sum(axis=0)
                self._vstart_sub[b, _sub] = v0
                self._vgrav_sub[b, _sub] = vg.copy()
                self._pass[b, _sub, P_WGRAV] = w_grav_p
                self._pass[b, _sub, P_QDAMP] = q_damp_p
                self._pass[b, _sub, P_IMPGX:P_IMPGZ + 1] = imp_grav_p
                self._pass[b, _sub, P_DMPX:P_DMPZ + 1] = imp_damp_p
            # stage 2: connective elements + actuator (trapezoid work)
            el = self._element_loads()
            act_b = self._actuator_load(tick)
            for b in bones:
                view = self.views[b]
                masses = TABLES.masses[b]
                ld = el['loads_a'] if b == 0 else el['loads_b'] + act_b
                v_pre = view.v.copy()
                new_v = view.v + ld * TABLES.inv_masses[b][:, None] * H_SUB
                dx = 0.5 * (v_pre + new_v) * H_SUB
                view.v[:] = new_v
                w_lig_p = float((el['lig_a' if b == 0 else 'lig_b']
                                 * dx).sum())
                w_cap_p = float((el['cap_a' if b == 0 else 'cap_b']
                                 * dx).sum())
                w_act_p = float((act_b * dx).sum()) if b == 1 else 0.0
                imp_elem_p = (masses[:, None]
                              * (view.v - v_pre)).sum(axis=0)
                self._ld_sub[b, _sub] = ld
                self._pass[b, _sub, P_WLIG] = w_lig_p
                self._pass[b, _sub, P_WCAP] = w_cap_p
                self._pass[b, _sub, P_WACT] = w_act_p
                self._pass[b, _sub, P_ELMX:P_ELMZ + 1] = imp_elem_p
            # stage 3: contact (declared sequential order, one solver)
            v_pre_contact = {b: self.views[b].v.copy() for b in bones}
            st = self._contact_stage()
            n_active = st['active_pairs']
            gs_worst_tick = max(gs_worst_tick, st['gs_residual_N_s'])
            iters = st['iterations']
            d_friction += st['d_friction_j']
            d_impact += st['d_impact_physical_j']
            jn_total += st['jn_applied_total_N_s']
            Q_contact += st['w_contact_ke_j']
            recip_worst = max(recip_worst, st['recip_residual'])
            self._sys[_sub, S_QCONTACT] = st['w_contact_ke_j']
            self._sys[_sub, S_DFRIC] = st['d_friction_j']
            self._sys[_sub, S_DIMP] = st['d_impact_physical_j']
            self._sys[_sub, S_JNTOT] = st['jn_applied_total_N_s']
            self._sys[_sub, S_ITERS] = float(st['iterations'])
            self._sys[_sub, S_GSRES] = st['gs_residual_N_s']
            self._sys[_sub, S_ACTIVE] = float(st['active_pairs'])
            if st['joint_gap_m'] is not None:
                joint_gap = st['joint_gap_m']
                joint_normal = st['joint_normal']
                joint_jn = max(joint_jn, st['joint_jn_Ns'])
                self._sys[_sub, S_JGAP] = st['joint_gap_m']
                self._sys[_sub, S_JHAS] = 1.0
                self._sys[_sub, S_JNX:S_JNZ + 1] = st['joint_normal']
                self._sys[_sub, S_JJN] = st['joint_jn_Ns']
                for (pid, ti, jn) in st['joint_patch']:
                    key = (pid, ti)
                    patch[key] = patch.get(key, 0.0) + jn
            for body in contact_acc:
                contact_acc[body] += st['contact_impulse'][body]
            for b in ground_jn_tick:
                ground_jn_tick[b] += st['ground_jn_N_s'][b]
            bb_impulse_tick += st['bb_impulse']
            self._sys[_sub, S_GJNA] = st['ground_jn_N_s']['bone_a']
            self._sys[_sub, S_GJNB] = st['ground_jn_N_s']['bone_b']
            self._sys[_sub, S_BBIX:S_BBIZ + 1] = st['bb_impulse']
            self._sys[_sub, S_CAX:S_CAZ + 1] = \
                st['contact_impulse']['bone_a']
            self._sys[_sub, S_CBX:S_CBZ + 1] = \
                st['contact_impulse']['bone_b']
            self._sys[_sub, S_CGX:S_CGZ + 1] = \
                st['contact_impulse']['ground']
            self._sys[_sub, S_RECX:S_RECZ + 1] = st['recip_residual']
            for b in bones:
                self._pass[b, _sub, P_CIMPX:P_CIMPZ + 1] = \
                    st['contact_impulse'][('bone_a', 'bone_b')[b]]
            # per-substep momentum ledger over stages 1-3 (telescoping
            # recorded deltas; v3 recomputed bitwise from the saved loads)
            for b in bones:
                view = self.views[b]
                masses = TABLES.masses[b]
                v1 = self._vgrav_sub[b, _sub]
                v2 = v1 * (1.0 - damping * H_SUB)
                ld = self._ld_sub[b, _sub]
                v3 = v2 + ld * TABLES.inv_masses[b][:, None] * H_SUB
                v4 = view.v
                v0s = self._vstart_sub[b, _sub]
                lhs = (masses[:, None] * (v4 - v0s)).sum(axis=0)
                rhs = ((masses[:, None] * (gvec * H_SUB)).sum(axis=0)
                       + (masses[:, None] * (v2 - v1)).sum(axis=0)
                       + (masses[:, None] * (v3 - v2)).sum(axis=0)
                       + (masses[:, None]
                          * (v4 - v3)).sum(axis=0))
                err = float(np.abs(lhs - rhs).max())
                require(err <= 1e-12, 'ledger_imbalance')
                ledger_worst[b] = max(ledger_worst[b], err)
                self._pass[b, _sub, P_LEDGER] = err
            # stage 4: position integration + tolerance-driven XPBD
            ke_pre_proj = self._kinetic()
            ke_pre_parts = (self._kinetic_bone(0), self._kinetic_bone(1))
            for b in bones:
                view = self.views[b]
                x_pre = view.x.copy()
                view.x[:] = view.x + view.v * H_SUB
                self._project(b)
                view.v[:] = (view.x - x_pre) / H_SUB
            ke_post_parts = (self._kinetic_bone(0), self._kinetic_bone(1))
            Q_proj += ke_pre_proj - self._kinetic()
            q_proj_sub = (ke_pre_parts[0] + ke_pre_parts[1]) \
                - (ke_post_parts[0] + ke_post_parts[1])
            self._sys[_sub, S_QPROJ] = q_proj_sub
        # ---- declared-order tick fold of the per-substep partials --------
        # (the interleaved sub-then-bone accumulation order the CUDA
        # tick-diag kernel transcribes; on CPU this reproduces the
        # oracle's own accumulators bitwise)
        for _sub in range(N_SUB):
            for b in bones:
                W['grav'] += self._pass[b, _sub, P_WGRAV]
                Q_damp += self._pass[b, _sub, P_QDAMP]
                W['lig'] += self._pass[b, _sub, P_WLIG]
                W['cap'] += self._pass[b, _sub, P_WCAP]
                W['act'] += self._pass[b, _sub, P_WACT]
        require(recip_worst <= 1e-12, 'ledger_imbalance')
        z_min = float(min(self.views[b].x[:, 2].min() for b in bones))
        z_min_parts = [float(self.views[b].x[:, 2].min()) for b in bones]
        require(z_min >= -THICKNESS_M - 2.5e-3, 'support_lost_or_hidden')
        dv_sys = {b: (TABLES.masses[b][:, None]
                      * (self.views[b].v
                         - self._vstart_tick[b])).sum(axis=0)
                  for b in bones}
        pred_anchor = np.zeros(3)
        for b in bones:
            imp_g_t = np.zeros(3)
            imp_d_t = np.zeros(3)
            imp_e_t = np.zeros(3)
            for _sub in range(N_SUB):
                imp_g_t = imp_g_t + self._pass[b, _sub,
                                                P_IMPGX:P_IMPGZ + 1]
                imp_d_t = imp_d_t + self._pass[b, _sub,
                                                P_DMPX:P_DMPZ + 1]
                imp_e_t = imp_e_t + self._pass[b, _sub,
                                                P_ELMX:P_ELMZ + 1]
            pred_anchor += (dv_sys[b] - imp_g_t - imp_d_t - imp_e_t)
        pred_anchor -= bb_impulse_tick
        anchor_err = float(np.abs(pred_anchor
                                  - (-contact_acc['ground'])).max())
        require(anchor_err <= 1e-12, 'ledger_imbalance')
        u_lig = self._lig_stored_energy() if self.lig is not None else 0.0
        u_cap = self._cap_stored_energy() if self.cap is not None else 0.0
        u_scaff_parts = (self._scaffold_energy(0), self._scaffold_energy(1))
        u_scaff = u_scaff_parts[0] + u_scaff_parts[1]
        kin = self._kinetic()
        e_mech = kin + u_lig + u_cap + u_scaff
        q_total = Q_damp + Q_contact + Q_proj + e_rel_tick
        prev = self.ticks[-1] if self.ticks else None
        e_prev = prev['e_mechanical_j'] if prev else 0.0
        w_sum = W['act'] + W['lig'] + W['cap'] + W['grav']
        residual = e_mech - e_prev - w_sum + q_total
        turnover = abs(w_sum) + q_total + kin
        bound = 1e-9 + 5e-2 * turnover
        if prev:
            bound += (prev['u_ligament_j'] + u_lig + prev['u_capsule_j']
                      + u_cap + prev['u_scaffold_j'] + u_scaff)
        if e_rel_tick > 0.0:
            bound = min(bound, max(5e-2 * e_rel_tick, 1e-12))
        require(abs(residual) <= bound, 'unexplained_energy')
        gap_x = float(self._head(1)[0] - self._head(0)[0])
        if joint_gap is None or joint_gap > lc.MARGIN:
            contact_state = 'separated'
        elif joint_jn > 0.0:
            contact_state = 'loaded'
        else:
            contact_state = 'touching'
        k_mat, contrib = self._restraint_matrix()
        k_rec = self._restraint_recomputed()
        scale = max(1.0, float(np.abs(k_mat).max()))
        rel_err = float(np.abs(k_mat - k_rec).max()) / scale
        require(rel_err <= 1e-15, 'restraint_recompute_mismatch')
        patch_report = {}
        if patch:
            by_body = {}
            for (pid, ti), jn in patch.items():
                by_body.setdefault(_body_of(pid), {})[ti] = jn
            for body, tris in by_body.items():
                b = 0 if body == 'bone_a' else 1
                areas = {ti: self.views[b].tri_area_now(ti)
                         for ti in tris}
                total_a = sum(areas.values())
                require(total_a > 0.0, 'zero_area_interface')
                p = sum(tris.values()) / (DT_S * total_a)
                patch_report[body] = {
                    'pressure_pa': p,
                    'per_triangle_area_m2': {str(t): a
                                             for t, a in
                                             sorted(areas.items())},
                    'per_triangle_load_n': {str(t): p * a
                                            for t, a in
                                            sorted(areas.items())},
                }
        # ---- row build ----------------------------------------------------
        row = {
            'tick': tick, 'phase': asm.phase_of(tick), 'acts': acts,
            'gap_head_anchors_m': gap_x,
            'contact_state': contact_state,
            'joint_gap_m': joint_gap,
            'joint_normal': joint_normal,
            'joint_jn_Ns': joint_jn,
            'contact_active_pairs': n_active,
            'contact_iterations': iters,
            'gs_residual_N_s': gs_worst_tick,
            'jn_applied_total_N_s': jn_total,
            'd_friction_j': d_friction, 'd_impact_physical_j': d_impact,
            'lig_bound': bool(self.lig is not None
                              and self.lig.bound_tick is not None
                              and self.lig.released_tick is None),
            'lig_tension_n': self._lig_tension()
            if self.lig is not None
            and self.lig.status != 'planned' else 0.0,
            'lig_force_n': [float(c) for c in
                            (self._lig_force_on_b()
                             if self.lig is not None
                             and self.lig.status != 'planned'
                             else np.zeros(3))],
            'lig_extension_m': (self._lig_extension()
                                if self.lig is not None
                                and self.lig.status != 'planned'
                                else 0.0),
            'cap_bound': bool(self.cap is not None
                              and self.cap.bound_tick is not None
                              and self.cap.released_tick is None),
            'cap_axial_n': self._cap_axial()
            if self.cap is not None
            and self.cap.status != 'planned' else 0.0,
            'cap_force_n': [float(c) for c in
                            (self._cap_force_on_b()
                             if self.cap is not None
                             and self.cap.status != 'planned'
                             else np.zeros(3))],
            'u_ligament_j': u_lig, 'u_capsule_j': u_cap,
            'u_scaffold_j': u_scaff, 'e_kinetic_j': kin,
            'e_mechanical_j': e_mech,
            'w_actuator_j': W['act'], 'w_ligament_j': W['lig'],
            'w_capsule_j': W['cap'], 'w_gravity_j': W['grav'],
            'q_damping_j': Q_damp, 'q_contact_j': Q_contact,
            'q_projection_j': Q_proj,
            'e_diss_release_j': e_rel_tick,
            'residual_r_j': residual, 'residual_bound_j': bound,
            'restraint_matrix': [float(c) for c in k_mat.ravel()],
            'restraint_contrib': contrib,
            'restrained_direction_count':
                self._restrained_direction_count(k_mat),
            'contact_patch_report': patch_report,
            'ground_anchor_impulse_N_s':
                [float(c) for c in (-contact_acc['ground'])],
            'ground_jn_N_s': {b: ground_jn_tick[b]
                              for b in ground_jn_tick},
            'min_vertex_z_m': z_min,
            'anchor_consistency_err_N_s': anchor_err,
            'ledger_residual_worst_N_s': max(ledger_worst.values()),
            'com_a_m': [float(c) for c in self.views[0].x.mean(axis=0)],
            'com_b_m': [float(c) for c in self.views[1].x.mean(axis=0)],
            'max_speed_m_per_s': float(max(np.abs(self.views[0].v).max(),
                                           np.abs(self.views[1].v).max())),
            'state_hash': None,
        }
        row['state_hash'] = asm.digest({k: row[k] for k in sorted(row)
                                        if k != 'state_hash'})
        self.ticks.append(row)
        # block build (system scalars live in component 0's block)
        blocks = np.zeros((N_BONES, DIAG), dtype=np.float64)
        for b in bones:
            blocks[b, D_KE] = self._kinetic_bone(b)
            blocks[b, D_USCAFF] = u_scaff_parts[b]
            blocks[b, D_COMX:D_COMZ + 1] = \
                self.views[b].x.mean(axis=0)
            blocks[b, D_MAXSPD] = float(np.abs(self.views[b].v).max())
            blocks[b, D_MINZ] = z_min_parts[b]
            blocks[b, D_LEDGERW] = ledger_worst[b]
            blocks[b, D_LIGBOUND] = float(bool(row['lig_bound']))
            blocks[b, D_CAPBOUND] = float(bool(row['cap_bound']))
            blocks[b, D_TICK] = float(tick)
            blocks[b, D_STATUS] = STATUS_OK
        blocks[0, D_GAP] = row['gap_head_anchors_m']
        blocks[0, D_JGAP] = (joint_gap if joint_gap is not None else 0.0)
        blocks[0, D_JNX:D_JNZ + 1] = (joint_normal or [0.0, 0.0, 0.0])
        blocks[0, D_JJN] = row['joint_jn_Ns']
        blocks[0, D_ACTIVE] = float(row['contact_active_pairs'])
        blocks[0, D_ITERS] = float(row['contact_iterations'])
        blocks[0, D_GSRES] = row['gs_residual_N_s']
        blocks[0, D_JNTOT] = row['jn_applied_total_N_s']
        blocks[0, D_DFRIC] = row['d_friction_j']
        blocks[0, D_DIMP] = row['d_impact_physical_j']
        blocks[0, D_WCKE] = row['q_contact_j']
        blocks[0, D_WACT] = row['w_actuator_j']
        blocks[0, D_WLIG] = row['w_ligament_j']
        blocks[0, D_WCAP] = row['w_capsule_j']
        blocks[0, D_WGRAV] = row['w_gravity_j']
        blocks[0, D_QDAMP] = row['q_damping_j']
        blocks[0, D_QCONTACT] = row['q_contact_j']
        blocks[0, D_QPROJ] = row['q_projection_j']
        blocks[0, D_EDISS] = row['e_diss_release_j']
        blocks[0, D_RESID] = row['residual_r_j']
        blocks[0, D_BOUND] = row['residual_bound_j']
        blocks[0, D_EMECH] = row['e_mechanical_j']
        blocks[0, D_LIGT] = row['lig_tension_n']
        blocks[0, D_LIGFX:D_LIGFZ + 1] = row['lig_force_n']
        blocks[0, D_LIGEXT] = row['lig_extension_m']
        blocks[0, D_CAPAX] = row['cap_axial_n']
        blocks[0, D_CAPFX:D_CAPFZ + 1] = row['cap_force_n']
        blocks[0, D_ULIG] = row['u_ligament_j']
        blocks[0, D_UCAP] = row['u_capsule_j']
        blocks[0, D_REST00:D_REST22 + 1] = row['restraint_matrix']
        blocks[0, D_ANCHORERR] = row['anchor_consistency_err_N_s']
        blocks[0, D_GIMPX:D_GIMPZ + 1] = row['ground_anchor_impulse_N_s']
        blocks[0, D_GJNA] = row['ground_jn_N_s']['bone_a']
        blocks[0, D_GJNB] = row['ground_jn_N_s']['bone_b']
        blocks[0, D_RECIP] = recip_worst
        for b in bones:
            d = 0.0
            for i in range(DIAG):
                v = 0.0 if i == D_DIGEST else blocks[b, i]
                d = (d * 1.0000000000000002 + v * (i + 1)) % 1000000007.0
            d = (d + float(tick) * 7919.0) % 1000000007.0
            blocks[b, D_DIGEST] = d
            self.digests[b].append(d)
        self.blocks.append(blocks.copy())
        self.host_bytes_down += DIAG * 8 * N_BONES + NV * 3 * 8
        self.tick = tick + 1
        return row

    @staticmethod
    def _restrained_direction_count(k):
        eig = np.linalg.eigvalsh(k)
        return int(sum(1 for v in eig
                       if v > asm.RESTRAINT_THRESHOLD_N_PER_M))

    def run(self, ticks=TICKS):
        for tick in range(ticks):
            self.step_tick(tick)
        return self.ticks
