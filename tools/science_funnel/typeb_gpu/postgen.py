"""postgen.py -- post-process walker_numba_gen.py:
(1) pack fk_eval; (2) thread mdi/csti through every device function and call
site (numba cannot capture module device arrays as globals).
Trailer Agent: GLM 5.3."""
import re

p = 'walker_numba_gen.py'
src = open(p, encoding='utf-8').read()

pat = re.compile(
    r'fk_eval\(q, v, mdl\.ax_rot, mdl\.ax_axis, mdl\.ax_slot, mdl\.ax_slope, mdl\.ax_const,\s*'
    r'mdl\.body_axoff, mdl\.body_parent, mdl\.body_mass, mdl\.body_com, mdl\.body_inertia,\s*'
    r'mdl\.body_fp, mdl\.body_fc, mdl\.chain_off, mdl\.chain_ax, mdl\.pt_body, mdl\.pt_local,\s*'
    r'mdl\.pt_radius, csti\[CI_nbod\], csti\[CI_naxes\], cst\[CF_plane_y\], cst\[CF_gy\],')
src, n = pat.subn('fk_eval(q, v, mdl, mdi, cst,', src)
print('fk_eval call sites packed:', n)

old_def = ('def fk_eval(q, v, ax_rot, ax_axis, ax_slot, ax_slope, ax_const, body_axoff, body_parent, '
           'body_mass, body_com, body_inertia, body_fp, body_fc, chain_off, chain_ax, pt_body, '
           'pt_local, pt_radius, nbod, naxes, plane_y, gy, M, gv, bv, fr, frd, frdd, axw, axpiv, '
           'axdir, ptp, ptJ, ptcop, ptbias):')
new_def = (
    'def fk_eval(q, v, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias):\n'
    '    ax_rot = mdi[OI_ax_rot:OI_ax_rot + 18]\n'
    '    ax_axis = mdl[OF_ax_axis:OF_ax_axis + 54]\n'
    '    ax_slot = mdi[OI_ax_slot:OI_ax_slot + 18]\n'
    '    ax_slope = mdl[OF_ax_slope:OF_ax_slope + 18]\n'
    '    ax_const = mdl[OF_ax_const:OF_ax_const + 18]\n'
    '    body_axoff = mdi[OI_body_axoff:OI_body_axoff + 15]\n'
    '    body_parent = mdi[OI_body_parent:OI_body_parent + 14]\n'
    '    body_mass = mdl[OF_body_mass:OF_body_mass + 14]\n'
    '    body_com = mdl[OF_body_com:OF_body_com + 42]\n'
    '    body_inertia = mdl[OF_body_inertia:OF_body_inertia + 42]\n'
    '    body_fp = mdl[OF_body_fp:OF_body_fp + 224]\n'
    '    body_fc = mdl[OF_body_fc:OF_body_fc + 224]\n'
    '    chain_off = mdi[OI_chain_off:OI_chain_off + 15]\n'
    '    chain_ax = mdi[OI_chain_ax:OI_chain_ax + 60]\n'
    '    pt_body = mdi[OI_pt_body:OI_pt_body + 8]\n'
    '    pt_local = mdl[OF_pt_local:OF_pt_local + 24]\n'
    '    pt_radius = mdl[OF_pt_radius:OF_pt_radius + 8]\n'
    '    nbod = 14\n'
    '    naxes = 18\n'
    '    plane_y = cst[CF_plane_y]\n'
    '    gy = cst[CF_gy]\n'
)
if old_def in src:
    src = src.replace(old_def, new_def)
    print('fk_eval def packed')
else:
    print('WARN: fk_eval def pattern not found')

DEVICE_FUNCS = ['mm', 'rot_axis', 'eye16', 'axial3', 'apply_point', 'transpose_rot',
                'load16', 'inverse_spd18', 'mat_vec', 'row_dot', 'gap_of_k',
                'gram_factor10', 'project_rows', 'friction_solve', 'rate',
                'free_step', 'gram_factor4', 'impact', 'advance',
                'fore_ik_at', 'fore_D_at', 'hind_ik_at', 'tables_at', 'vault_at',
                'fore_target_headroom', 'fore_follow', 'fore_env',
                'hind_deadline_fn', 'paw_leg', 'fk_eval']

lines = src.splitlines(keepends=True)
out = []
i = 0
while i < len(lines):
    line = lines[i]
    m = re.match(r'^def (\w+)\((.*)\):\s*$', line, re.S)
    if m and m.group(1) in DEVICE_FUNCS:
        params = m.group(2)
        if not params.strip():
            params = 'mdi, csti'
        else:
            params = params + ', mdi, csti'
        out.append('def ' + m.group(1) + '(' + params + '):
')
        i += 1
        continue
    out.append(line)
    i += 1
src = ''.join(out)

needs = set(DEVICE_FUNCS)
res = []
i = 0
n = len(src)
while i < n:
    ch = src[i]
    if ch.isalpha() or ch == '_':
        j = i
        while j < n and (src[j].isalnum() or src[j] == '_'):
            j += 1
        name = src[i:j]
        if name in needs and j < n and src[j] == '(':
            depth = 0
            k = j
            while k < n:
                if src[k] == '(':
                    depth += 1
                elif src[k] == ')':
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            args = src[j + 1:k]
            last = args.split(',')[-1]
            if 'mdi' not in last and args.strip():
                res.append(src[i:k] + ', mdi, csti)')
                i = k + 1
                continue
        res.append(src[i:j])
        i = j
        continue
    res.append(ch)
    i += 1
src = ''.join(res)

open(p, 'w', encoding='utf-8').write(src)
print('mdi/csti threading done')
