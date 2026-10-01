"""postgen.py -- post-process walker_numba_gen.py:
(1) pack fk_eval; (2) restore decorators; (3) needs-based mdi/csti threading;
(4) out-param conversion for local-array returns; (5) pt_radius slices.
Trailer Agent: GLM 5.3."""
import re

p = 'walker_numba_gen.py'
src = open(p, encoding='utf-8').read()

DEVICE_FUNCS = ['mm', 'rot_axis', 'eye16', 'axial3', 'apply_point', 'transpose_rot',
                'load16', 'inverse_spd18', 'mat_vec', 'row_dot', 'gap_of_k',
                'gram_factor10', 'project_rows', 'friction_solve', 'rate',
                'free_step', 'gram_factor4', 'impact', 'advance',
                'fore_ik_at', 'fore_D_at', 'hind_ik_at', 'tables_at', 'vault_at',
                'fore_target_headroom', 'fore_follow', 'fore_env',
                'hind_deadline_fn', 'paw_leg', 'fk_eval']

# ── 1) pack fk_eval ──
pat = re.compile(r'fk_eval\(\w+, \w+, mdl\.ax_rot,[^)]*?cst\[CF_gy\],', re.S)
src, n = pat.subn(lambda m: 'fk_eval(' + ', '.join(
    m.group(0)[len('fk_eval('):].split(',')[:2]) + ', mdl, mdi, cst,', src)
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
    '    gy = cst[CF_gy]')
if old_def in src:
    src = src.replace(old_def, new_def)
    print('fk_eval def packed')
else:
    print('WARN: fk_eval def pattern not found')

# ── 2) needs-based mdi/csti threading ──
spans = []
for m in re.finditer(r'^def (\w+)\(', src, re.M):
    spans.append((m.group(1), m.start()))
spans.append((None, len(src)))
FUNC_SPANS = [(spans[i][0], spans[i][1], spans[i + 1][1]) for i in range(len(spans) - 1)]
needs = {}
for name, a, b in FUNC_SPANS:
    fsrc = src[a:b]
    needs[name] = set()
    if re.search(r'\bmdi\[', fsrc):
        needs[name].add('mdi')
    if re.search(r'\bcsti\[', fsrc):
        needs[name].add('csti')
changed = True
while changed:
    changed = False
    for name, a, b in FUNC_SPANS:
        fsrc = src[a:b]
        for callee in list(needs):
            if callee == name or callee in needs[name]:
                continue
            if re.search(r'(?<!def )\b' + callee + r'\(', fsrc):
                before = len(needs[name])
                needs[name] |= needs[callee]
                if len(needs[name]) != before:
                    changed = True

out_lines = []
i = 0
lines = src.splitlines(keepends=True)
while i < len(lines):
    line = lines[i]
    m = re.match(r'^def (\w+)\((.*)\):\s*$', line, re.S)
    if m and m.group(1) in needs:
        name = m.group(1)
        params = m.group(2)
        have = [x.strip() for x in params.split(',')]
        add = [g for g in ('mdi', 'csti') if g in needs[name] and g not in have]
        if add:
            if not params.strip():
                params = ', '.join(add)
            else:
                params = params + ', ' + ', '.join(add)
            out_lines.append(f'def {name}({params}):\n')
            i += 1
            continue
    out_lines.append(line)
    i += 1
src = ''.join(out_lines)

NEED_SETS = {name: needs[name] for name, a, b in FUNC_SPANS}
ALLN = set(NEED_SETS)
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
        if name in ALLN and j < n and src[j] == '(' and src[max(0, i - 4):i] != 'def ':
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
            d2 = 0
            toks = []
            cur = ''
            for ch2 in args:
                if ch2 in '([':
                    d2 += 1
                elif ch2 in ')]':
                    d2 -= 1
                if ch2 == ',' and d2 == 0:
                    toks.append(cur)
                    cur = ''
                else:
                    cur += ch2
            toks.append(cur)
            toks = [t.strip() for t in toks]
            add = [g for g in sorted(NEED_SETS[name]) if g not in toks]
            if add:
                res.append(src[i:k] + ', ' + ', '.join(add) + ')')
                i = k + 1
                continue
        res.append(src[i:j])
        i = j
        continue
    res.append(ch)
    i += 1
src = ''.join(res)
print('needs-based threading done')

# ── 3) restore lost device decorators ──
lines = src.splitlines(keepends=True)
for i, ln in enumerate(lines):
    m = re.match(r'^def (\w+)\(', ln)
    if m and m.group(1) in DEVICE_FUNCS:
        j = i - 1
        decorated = False
        while j >= 0:
            s = lines[j].strip()
            if s:
                decorated = s.startswith('@')
                break
            j -= 1
        if not decorated:
            lines[i] = '@cuda.jit(device=True)\n' + ln
            print('decorator restored for', m.group(1))
src = ''.join(lines)

# ── 4) out-param conversion for local-array returns ──
src = src.replace('def paw_leg(paw_t, leg):', 'def paw_leg(paw_t, leg, out):')
a = src.index('def paw_leg(paw_t, leg, out):')
b = src.index('out[2] = paw_t[leg * 3 + 2]', a)
seg = src[a:b]
seg = seg.replace('    out = cuda.local.array(3, dtype=float64)\n', '')
src = src[:a] + seg + src[b:]

src = src.replace('def tables_at(mdl, phi):', 'def tables_at(mdl, phi, out):')
a = src.index('def tables_at(mdl, phi, out):')
b = src.index('def vault_at(', a)
seg = src[a:b]
seg = seg.replace('    out = cuda.local.array(18, dtype=float64)\n', '')
src = src[:a] + seg + src[b:]

src = src.replace('def fore_follow(mdl, cst, fr, leg, paw_t, branch, mdi, csti):',
                  'def fore_follow(mdl, cst, fr, leg, paw_t, branch, mdi, csti, result):')
a = src.index('def fore_follow(mdl, cst, fr, leg, paw_t, branch, mdi, csti, result):')
b = src.index('def fore_env(', a)
seg = src[a:b]
seg = seg.replace('        return te\n',
                  '        result[0] = te[0]\n        result[1] = te[1]\n'
                  '        result[2] = te[2]\n        return result\n')
seg = seg.replace('    return out\n',
                  '    result[0] = out[0]\n    result[1] = out[1]\n'
                  '    result[2] = out[2]\n    return result\n')
src = src[:a] + seg + src[b:]


def expand_assign(src, old_assign, alloc, new_call):
    out = []
    for line in src.splitlines(keepends=True):
        stripped = line.lstrip(' ')
        if stripped.startswith(old_assign):
            indent = line[:len(line) - len(stripped)]
            out.append(indent + alloc + '\n')
            out.append(indent + new_call + '\n')
        else:
            out.append(line)
    return ''.join(out)


src = expand_assign(src, 'plt = paw_leg(paw_t, leg)',
                    'plt = cuda.local.array(3, dtype=float64)',
                    'paw_leg(paw_t, leg, plt)')
src = expand_assign(src, 'plt = paw_leg(paw_t, fl)',
                    'plt = cuda.local.array(3, dtype=float64)',
                    'paw_leg(paw_t, fl, plt)')
src = expand_assign(src, 'seat = fore_follow(mdl, cst, fr, leg, paw_t, ikb[leg], csti, mdi)',
                    'seat = cuda.local.array(3, dtype=float64)',
                    'fore_follow(mdl, cst, fr, leg, paw_t, ikb[leg], csti, mdi, seat)')
src = expand_assign(src, 'qstar = tables_at(mdl, phi[hl])',
                    'qstar = cuda.local.array(18, dtype=float64)',
                    'tables_at(mdl, phi[hl], qstar)')
print('out-param conversions done')

# ── 5) pt_radius whole-array references ──
spans = []
for m in re.finditer(r'^def (\w+)\(', src, re.M):
    spans.append((m.group(1), m.start()))
spans.append((None, len(src)))
for i in range(len(spans) - 2, -1, -1):
    name, a, b = spans[i][0], spans[i][1], spans[i + 1][1]
    body = src[a:b]
    if 'mdl.pt_radius' in body:
        nl = body.index('\n') + 1
        body = (body[:nl] + '    pt_radius_g = mdl[OF_pt_radius:OF_pt_radius + 8]\n'
                + body[nl:].replace('mdl.pt_radius', 'pt_radius_g'))
        src = src[:a] + body + src[b:]
        print('pt_radius_g injected into', name)

open(p, 'w', encoding='utf-8').write(src)
print('postgen done')
