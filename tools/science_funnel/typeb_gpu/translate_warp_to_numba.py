"""translate_warp_to_numba.py -- mechanical warp->numba translation of the
walker port. The equations are the checked-in walker_gpu.py form; this tool
only re-targets the toolchain after the Warp JIT wall (receipt documents it).
Trailer Agent: GLM 5.3."""
import re
from walker_model import WalkerSpec

INT_FIELDS = {'ax_rot', 'ax_slot', 'body_axoff', 'body_parent', 'chain_off',
              'chain_ax', 'pt_body', 'drive_coord', 'fore_coord', 'hind_coord',
              'hind_drive', 'fore_drive', 'fore_heel_pt', 'hind_heel_pt'}
CST_INT = {'nbod', 'naxes', 'settle_total', 'contact', 'power', 'gait_enabled', 'capture_enabled',
           'posture_drive', 'drive_en', 'reflex_level', 'fold_budget',
           'unload_ticks', 'tair', 'pelvis_row', 'upperarm_body', 'forearm_body'}
CST_FLOAT = {'plane_y', 'gy', 'dt', 'mu', 'k_touch', 'k_slip', 'k_release',
             't_cycle', 'duty', 'toe_off', 'capture_phi', 'kp_post', 'kd_post',
             'store_post', 'height_crit', 'height_floor', 'fore_L1', 'fore_rho',
             'fore_beta', 'hind_L1', 'hind_L2', 'hind_xm', 'fore_pose_sh',
             'fore_pose_el'}

ZN = re.compile(r'wp\.zeros\(shape=(\w+), dtype=wp\.float64\)')
ZI = re.compile(r'wp\.zeros\(shape=(\w+), dtype=wp\.int32\)')
ZL = re.compile(r'wp\.zeros\(shape=(\w+), dtype=wp\.int64\)')
ANN = re.compile(r':\s*(?:Q18|M324|F16|F3|F224|F24|F54|F216|F12|F8|F180|F10|F100|'
                 r'I10|F13|I1|F1|I4|H16|I16|F576|F36|float64|int32|int64|wp\.float64|'
                 r'wp\.int32|wp\.int64|wp\.array\(dtype=wp\.\w+\)|wp\.fixedarray\([^)]*\)|'
                 r'ModelIn|ModelConst)(\[[^\]]*\])?')
ARRANN = re.compile(r'wp\.array\(dtype=wp\.(float64|int32|int64)\)')


def translate(src):
    # drop the warp preamble (everything before the first device function)
    start = src.index('# ───────────────────────── small linear algebra')
    body = src[start:]
    # drop the warp env class (the numba env wrapper owns it)
    if '# ───────────────────────── the batched environment' in body:
        body = body[:body.index('# ───────────────────────── the batched environment')]
    # drop the warp struct definitions (numba uses flat packed arrays);
    # keep the I4 typedef line that lives inside that block
    mb = body.index('# ───────────────────────── model bundles')
    rate_def = body.index('def rate(')
    decl = body[mb:rate_def]
    keep = [ln for ln in decl.splitlines() if 'I4 = wp.fixedarray' in ln]
    body = body[:mb] + '\n'.join(keep) + '\n\n\n' + body[rate_def:]
    out = []
    skip_preamble_map = True
    for line in body.splitlines():
        ls = line
        if ls.strip().startswith('F = wp.float64') or ls.strip().startswith('PI = F('):
            continue
        # constant-block removal: the Q18 = wp.fixedarray... lines
        if re.match(r'^[A-Z0-9_]+ = wp\.fixedarray', ls):
            continue
        out.append(ls)
    src = '\n'.join(out)

    # decorators
    src = src.replace('@wp.func', '@cuda.jit(device=True)')
    src = src.replace('@wp.kernel', '@cuda.jit')

    # zeros -> local arrays
    src = ZN.sub(r'cuda.local.array(\1, dtype=float64)', src)
    src = ZI.sub(r'cuda.local.array(\1, dtype=int32)', src)
    src = ZL.sub(r'cuda.local.array(\1, dtype=int64)', src)

    # scalar casts / literals
    src = re.sub(r'wp\.float64\(([^()]*)\)', r'float(\1)', src)
    src = re.sub(r'wp\.int64\(([^()]*)\)', r'np.int64(\1)', src)
    src = re.sub(r'wp\.int32\(([^()]*)\)', r'int32(\1)', src)
    src = src.replace('wp.tid()', 'cuda.grid(1)')
    src = re.sub(r'\bwp\.min\(', 'min(', src)
    src = re.sub(r'\bwp\.max\(', 'max(', src)
    src = re.sub(r'\bwp\.abs\(', 'abs(', src)
    src = re.sub(r'\bwp\.sqrt\(', 'math.sqrt(', src)
    src = re.sub(r'\bwp\.sin\(', 'math.sin(', src)
    src = re.sub(r'\bwp\.cos\(', 'math.cos(', src)
    src = re.sub(r'\bwp\.atan2\(', 'math.atan2(', src)
    src = re.sub(r'\bwp\.acos\(', 'math.acos(', src)
    src = re.sub(r'\bwp\.floor\(', 'math.floor(', src)
    src = re.sub(r'\bwp\.isnan\(', 'math.isnan(', src)
    src = re.sub(r'\bwp\.isinf\(', 'math.isinf(', src)

    # F(...) literal casts -> float(...)
    src = re.sub(r'\bF\(([^()]*)\)', r'float(\1)', src)

    # model bundle accesses (offset constants; numba cannot index dicts)
    for f in INT_FIELDS:
        src = re.sub(r'\bmdl\.' + f + r'\[', 'mdi[OI_' + f + ' + ', src)
    for f in CST_INT:
        src = re.sub(r'\bcst\.' + f + r'\b', 'csti[CI_' + f + ']', src)
    for f in CST_FLOAT:
        src = re.sub(r'\bcst\.' + f + r'\b', 'cst[CF_' + f + ']', src)
    for f in ['ax_axis', 'ax_slope', 'ax_const', 'body_mass', 'body_com',
              'body_inertia', 'body_fp', 'body_fc', 'pt_local', 'pt_radius',
              'lower', 'upper', 'drive_cap', 'drive_damping', 'kp', 'kd',
              'tab_hip', 'tab_knee', 'tab_ankle', 'tab_mp', 'zeros4', 'vault',
              'fore_mount_local', 'hind_mount']:
        src = re.sub(r'\bmdl\.' + f + r'\[', 'mdl[OF_' + f + ' + ', src)

    # strip function annotations (numba infers) -- full-source span pass
    out_lines = []
    i = 0
    lines = src.splitlines(keepends=True)
    n = len(lines)
    while i < n:
        line = lines[i]
        m = re.match(r'^(\s*)def\s+\w+\(', line)
        if not m:
            out_lines.append(line)
            i += 1
            continue
        # collect the full signature (may span lines) and the trailing ':'
        j = i
        joined = ''
        while j < n:
            joined += lines[j]
            if re.search(r'\)\s*(->\s*[^:#]*)?:\s*(#.*)?$', joined):
                break
            j += 1
        # find the parameter span: first '(' to its matching ')'
        start = joined.index('(')
        depth = 0
        end = start
        for kk, ch in enumerate(joined[start:], start):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    end = kk
                    break
        params_src = joined[start + 1:end]
        params = []
        depth = 0
        cur = ''
        for ch in params_src:
            if ch in '([':
                depth += 1
            elif ch in ')]':
                depth -= 1
            if ch == ',' and depth == 0:
                params.append(cur)
                cur = ''
            else:
                cur += ch
        if cur.strip():
            params.append(cur)
        names = []
        for p in params:
            p = p.strip()
            if not p:
                continue
            name = p.split(':')[0].split('=')[0].strip()
            names.append(name)
        params = names
        tail = joined[end + 1:]
        tail = re.sub(r'^\s*->\s*[^:]*:', ':', tail)
        out_lines.append(joined[:start] + '(' + ', '.join(params) + ')' + tail)
        i = j + 1
    src = '\n'.join(out_lines)
    return src
