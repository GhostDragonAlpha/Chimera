"""MAT2-M09 local rehearsal: MirrorWorld vs the sealed CPU oracle (X3 CPU-FIRST).

Validates the kernel-mirror transcription BITWISE against assembly.AssemblyRun
on the frozen 90-tick fixture BEFORE any GPU job: every row value, both
state_hash chains, the full vertex trajectories and the declared-order
diagnostic block fold. Run: python -B mirror_rehearsal.py [ticks]

Exit 0 = AGREED (bitwise), 1 = DISAGREED. Writes nothing.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
CONTRIB = HERE.parent
for _p in (str(HERE), str(CONTRIB / 'MAT2-M01'), str(CONTRIB / 'MAT2-M03'),
           str(CONTRIB / 'MAT2-M05'), str(CONTRIB / 'MAT2-M06')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import assembly as asm  # noqa: E402
import kernel_mirror as km  # noqa: E402

TICKS = asm.TICKS                   # overridable: python mirror_rehearsal.py N

# block comparables: (row field, component, slot or None-for-derived)
SCALAR_COMPARABLES = [
    ('gap_head_anchors_m', 0, km.D_GAP),
    ('joint_jn_Ns', 0, km.D_JJN),
    ('contact_active_pairs', 0, km.D_ACTIVE),
    ('contact_iterations', 0, km.D_ITERS),
    ('gs_residual_N_s', 0, km.D_GSRES),
    ('jn_applied_total_N_s', 0, km.D_JNTOT),
    ('d_friction_j', 0, km.D_DFRIC),
    ('d_impact_physical_j', 0, km.D_DIMP),
    ('lig_tension_n', 0, km.D_LIGT),
    ('lig_extension_m', 0, km.D_LIGEXT),
    ('cap_axial_n', 0, km.D_CAPAX),
    ('u_ligament_j', 0, km.D_ULIG),
    ('u_capsule_j', 0, km.D_UCAP),
    ('e_mechanical_j', 0, km.D_EMECH),
    ('w_actuator_j', 0, km.D_WACT),
    ('w_ligament_j', 0, km.D_WLIG),
    ('w_capsule_j', 0, km.D_WCAP),
    ('w_gravity_j', 0, km.D_WGRAV),
    ('q_damping_j', 0, km.D_QDAMP),
    ('q_contact_j', 0, km.D_QCONTACT),
    ('q_projection_j', 0, km.D_QPROJ),
    ('e_diss_release_j', 0, km.D_EDISS),
    ('residual_r_j', 0, km.D_RESID),
    ('residual_bound_j', 0, km.D_BOUND),
    ('anchor_consistency_err_N_s', 0, km.D_ANCHORERR),
    ('ground_jn_a', 0, km.D_GJNA),
    ('ground_jn_b', 0, km.D_GJNB),
]


def bitwise_equal(a, b, path, bad):
    """Exact equality walk: floats compared BITWISE (float.hex), ints,
    bools, strings exact. NaN never expected in a row."""
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            bad.append(f'{path}: key mismatch')
            return
        for k in a:
            bitwise_equal(a[k], b[k], f'{path}.{k}', bad)
        return
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            bad.append(f'{path}: length {len(a)} vs {len(b)}')
            return
        for i, (x, y) in enumerate(zip(a, b)):
            bitwise_equal(x, y, f'{path}[{i}]', bad)
        return
    if isinstance(a, bool) or isinstance(b, bool):
        if bool(a) != bool(b):
            bad.append(f'{path}: {a!r} vs {b!r}')
        return
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) \
            and not isinstance(a, bool) and not isinstance(b, bool):
        fa, fb = float(a), float(b)
        if math.isnan(fa) or math.isnan(fb):
            bad.append(f'{path}: NaN present ({fa!r} vs {fb!r})')
        elif fa.hex() != fb.hex():
            bad.append(f'{path}: {fa!r} vs {fb!r}')
        return
    if a != b:
        bad.append(f'{path}: {a!r} vs {b!r}')


def run_rehearsal(ticks=None):
    """The full bitwise rehearsal; returns the structured verdict fields
    (shared by main() and run_experiments.mode_mirror)."""
    ticks = asm.TICKS if ticks is None else ticks
    oracle = asm.AssemblyRun()
    mirror = km.MirrorWorld()
    assert asm.DECLARATION['order'] == mirror.declaration['order']
    bad = []
    worst_scalar = 0.0
    worst_pos = 0.0
    hashes_bitwise = True
    for tick in range(ticks):
        orow = oracle.step(tick)
        mrow = mirror.step_tick(tick)
        bitwise_equal(orow, mrow, f'tick{tick}', bad)
        # positions bitwise
        for b in (0, 1):
            ox = oracle.bone_a.x if b == 0 else oracle.bone_b.x
            d = float(np.abs(np.asarray(ox) - mirror.views[b].x).max())
            worst_pos = max(worst_pos, d)
            if d != 0.0:
                bad.append(f'tick{tick}: bone{b} position diff {d!r}')
            ov = oracle.bone_a.v if b == 0 else oracle.bone_b.v
            dv = float(np.abs(np.asarray(ov) - mirror.views[b].v).max())
            if dv != 0.0:
                bad.append(f'tick{tick}: bone{b} velocity diff {dv!r}')
        # block fold vs row (bitwise on CPU)
        block = mirror.blocks[-1]
        for name, comp, slot in SCALAR_COMPARABLES:
            if name == 'ground_jn_a':
                rv = orow['ground_jn_N_s']['bone_a']
            elif name == 'ground_jn_b':
                rv = orow['ground_jn_N_s']['bone_b']
            else:
                rv = orow[name]
            bv = float(block[comp, slot])
            d = abs(float(rv) - bv)
            worst_scalar = max(worst_scalar, d)
            if float(rv).hex() != bv.hex():
                bad.append(f'tick{tick}: block {name} {rv!r} vs {bv!r}')
        for name, comp, slots in (('com_a_m', 0, (km.D_COMX, km.D_COMY,
                                                   km.D_COMZ)),
                                  ('com_b_m', 1, (km.D_COMX, km.D_COMY,
                                                  km.D_COMZ)),
                                  ('lig_force_n', 0, (km.D_LIGFX,
                                                      km.D_LIGFY,
                                                      km.D_LIGFZ)),
                                  ('cap_force_n', 0, (km.D_CAPFX,
                                                      km.D_CAPFY,
                                                      km.D_CAPFZ)),
                                  ('ground_anchor_impulse_N_s', 0,
                                   (km.D_GIMPX, km.D_GIMPY, km.D_GIMPZ))):
            for k, slot in enumerate(slots):
                rv = float(orow[name][k])
                bv = float(block[comp, slot])
                d = abs(rv - bv)
                worst_scalar = max(worst_scalar, d)
                if rv.hex() != bv.hex():
                    bad.append(f'tick{tick}: block {name}[{k}] '
                               f'{rv!r} vs {bv!r}')
        # derived scalars from the block (the GPU-agreement harness's own
        # folds — sums/max over components in the declared order)
        ke_fold = float(block[0, km.D_KE]) + float(block[1, km.D_KE])
        if ke_fold != orow['e_kinetic_j']:
            bad.append(f"tick{tick}: KE fold {orow['e_kinetic_j']!r} "
                       f'vs {ke_fold!r}')
        us_fold = float(block[0, km.D_USCAFF]) + float(block[1, km.D_USCAFF])
        if us_fold != orow['u_scaffold_j']:
            bad.append(f"tick{tick}: U_scaff fold "
                       f"{orow['u_scaffold_j']!r} vs {us_fold!r}")
        spd_fold = max(float(block[0, km.D_MAXSPD]),
                       float(block[1, km.D_MAXSPD]))
        if spd_fold != orow['max_speed_m_per_s']:
            bad.append(f"tick{tick}: max_speed fold "
                       f"{orow['max_speed_m_per_s']!r} vs {spd_fold!r}")
        mz_fold = min(float(block[0, km.D_MINZ]), float(block[1, km.D_MINZ]))
        if mz_fold != orow['min_vertex_z_m']:
            bad.append(f"tick{tick}: min_z fold "
                       f"{orow['min_vertex_z_m']!r} vs {mz_fold!r}")
        lw_fold = max(float(block[0, km.D_LEDGERW]),
                      float(block[1, km.D_LEDGERW]))
        if lw_fold != orow['ledger_residual_worst_N_s']:
            bad.append(f"tick{tick}: ledger fold "
                       f"{orow['ledger_residual_worst_N_s']!r} "
                       f'vs {lw_fold!r}')
        mat = np.array(orow['restraint_matrix']).reshape(3, 3)
        bm = block[0, km.D_REST00:km.D_REST22 + 1].reshape(3, 3)
        if not np.array_equal(mat, bm):
            bad.append(f'tick{tick}: restraint matrix block mismatch')
        cnt = km.MirrorWorld._restrained_direction_count(bm)
        if cnt != orow['restrained_direction_count']:
            bad.append(f"tick{tick}: restrained count "
                       f"{orow['restrained_direction_count']} vs {cnt}")
        # digest chain: host recompute matches the device slot (stale guard)
        for b in (0, 1):
            want = km.block_digest(block[b], tick)
            got = float(block[b, km.D_DIGEST])
            if want != got:
                bad.append(f'tick{tick}: digest chain comp{b} stale')
        if orow['state_hash'] != mrow['state_hash']:
            hashes_bitwise = False
    return {
        'ticks': ticks,
        'findings': bad,
        'worst_position_diff_m': worst_pos,
        'worst_block_scalar_diff': worst_scalar,
        'rows_bitwise_identical': not bad,
        'state_hash_chains_identical': hashes_bitwise,
        'mirror_digest_chains': (list(mirror.digests[0]),
                                 list(mirror.digests[1])),
    }


def main():
    ticks = int(sys.argv[1]) if len(sys.argv) > 1 else asm.TICKS
    res = run_rehearsal(ticks)
    bad = res['findings']
    worst_pos = res['worst_position_diff_m']
    worst_scalar = res['worst_block_scalar_diff']
    print(f"ticks={ticks} worst_position_diff={worst_pos!r} "
          f'worst_block_scalar_diff={worst_scalar!r}')
    if bad:
        print(f'BITWISE: DISAGREED ({len(bad)} findings; first 12):')
        for line in bad[:12]:
            print('  ' + line)
        print('RESULT: DISAGREED')
        return 1
    print('BITWISE: every row value, state_hash, vertex trajectory and '
          'block fold identical')
    print('RESULT: AGREED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
