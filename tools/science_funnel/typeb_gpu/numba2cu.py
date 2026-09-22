"""numba2cu.py v4 -- Python-numba kernels -> CUDA C++.

v4 (finish lane, 2026-09-22) -- closes the four mapped error classes + the
latent defects found while fixing them:
  - FIX(1) int-index inference: two-pass function-scope hoist. Every assigned
    scalar is declared ONCE at function top (double / int / long long). A name
    that appears inside any bracket expression anywhere in the body is an
    index -> int. int_kind() propagates int-ness from literals, int vars,
    (int) casts, comparisons, floordiv; everything else is double. This also
    fixes the `t`-undefined sites (class 3): first-use inside an if-block no
    longer scopes the declaration into that block.
  - FIX(2a) slices: `X = arr[a:b]` -> local array + copy loop. dtype follows
    the base array (mdi/csti/int-ptr args -> int[]; else double[]). Bounds
    must fold to constexpr (OF_/OI_ are static const int).
  - FIX(2b) constants: extracted from walker_numba_split.py itself (the old
    code read walker_numba.py, which defines NBOD/NAXES -- not the OF_/OI_/
    CI_/CF_ blocks the kernels use -- so NOTHING was emitted).
  - FIX(3) `t`: function-scope hoist (see FIX 1).
  - FIX(4) tuple residual: rot_axis's `x = axis[0]; y = axis[1]; z = axis[2]`
    is a SEMICOLON-COMPOUND line, not a tuple. Statements are now split on
    top-level ';' and each sub-statement processed. Real tuples (incl. calls)
    handled per-name; tuple-RETURNING functions (fore_ik_at/hind_ik_at/
    hind_deadline_fn) are desugared to out-params, call sites pass &targets.
  - FIX(5) bare `@cuda.jit` (reset_kernel, the 4th global) was DROPPED by the
    old def-regex, which required parentheses on the decorator.
  - FIX(6) 2- and 3-arg range() (range(a,b), range(a,b,-1)) -- the old regex
    compiled them as range(expr) with a comma-expression bound, silently
    starting loops at 0. Negative steps -> `v > stop; --v`.
  - FIX(7) floordiv `//` -> `/` (all sites positive-operand: shape guards and
    (d-1)//4, (d-9)//2 drive-index math); `X.shape[0]` -> cu_total_q (the
    e >= ne guard is dead by construction: the host launches exactly ne
    threads per kernel).
  - Kept from v3: indent STACK brace emission, elif/else chain pop, math.
    strip, min/max/abs -> fmin/fmax/fabs, cuda.local.array, cuda.grid,
    return-type inference.
"""
import re
from pathlib import Path

SRC = Path(__file__).parent / "walker_numba_split.py"
DST = Path(__file__).parent / "walker_kernels.cuh"

# EXACT dtype tables (membership, NOT prefix) -- derived from the lane's host
# allocation in walker_nb_split_env.py lines 32-64 (z=float64, zi=int32,
# zl=int64). The old prefix lists typed POSITION arrays int (a_hind_to matched
# the a_hind_t prefix; a_swing_from/to hold x/y/z footfall targets) and mistyped
# the int64 clocks -- silent f64 truncation, physics-corrupting.
HOST_INT32_ARGS = ("a_touching", "a_captured", "a_settle", "a_ik_branch",
                   "a_fore_mode", "a_fore_entry", "a_fore_conv", "a_fore_td_plant",
                   "a_fore_clamped", "a_fore_replants", "a_fore_td_count",
                   "a_hind_mode", "a_hind_branch", "a_hind_held", "a_hind_fires",
                   "a_hind_tds", "a_height_latched", "a_cmd_live", "a_cmd_fires",
                   "a_adv_calls", "a_refused", "a_refused_class", "a_collapsed",
                   "a_rc", "rbi", "mdi", "csti", "a_touching0")
HOST_INT64_ARGS = ("a_hind_last_fire", "a_hind_last_td", "a_cmd_first_tick", "a_ticks")
HOST_INT_SCALARS = ("settle_total",)
# int-valued pointer args beyond the name tables
INT_ARR_ARGS = set()
GLOBAL_INTS = {"cu_total_q"}
SINGLE_INT_ARGS = re.compile(r"^(i|j|k|n|e|leg|hl|hr|h|o|m|ne|E|N|pt|col|row)$")
# EXACT double-scalar overrides, checked BEFORE the heuristic: "h" is the
# substep size in advance/free_step (dt/4 ~ 8.3e-4) but the single-letter
# rule above types it int -- the call truncates 8.3e-4 -> 0, advance returns
# at its h<1e-12 guard on EVERY call, and the whole walk freezes silently
# (rc=0, adv_calls=0, q/v bit-identical to reset; measured via env_dbg_read
# freefall probe, 2026-09-22).
EXACT_DOUBLE_SCALARS = {("advance", "h"), ("free_step", "h")}


def strip_comment(st: str) -> str:
    depth = 0
    for i, ch in enumerate(st):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "#" and depth == 0:
            return st[:i]
    return st


def t_expr(line: str) -> str:
    line = re.sub(r"\bnp\.int64\(", "(long long)(", line)
    line = re.sub(r"\bnp\.float64\(", "(double)(", line)
    line = re.sub(r"\bint32\(", "(int)(", line)
    line = re.sub(r"\bint64\(", "(long long)(", line)
    line = re.sub(r"\bfloat64\(", "(double)(", line)
    line = re.sub(r"\bfloat\(", "(double)(", line)
    line = re.sub(r"\b(\w+)\.shape\[0\]", "cu_total_q", line)
    line = re.sub(r"\bmin\(", "fmin(", line)
    line = re.sub(r"\bmax\(", "fmax(", line)
    line = re.sub(r"\babs\(", "fabs(", line)
    line = re.sub(r"\bmath\.", "", line)
    line = re.sub(r"\bTrue\b", "true", line)
    line = re.sub(r"\bFalse\b", "false", line)
    line = re.sub(r"\bis not\b", "!=", line)
    line = re.sub(r"\bis\b", "==", line)
    line = re.sub(r"(?<![\w])not(?![\w])", "!", line)
    line = re.sub(r"(?<![\w])or(?![\w])", "||", line)
    line = re.sub(r"(?<![\w])and(?![\w])", "&&", line)
    line = line.replace("//", "/")  # floordiv: all sites positive-operand
    line = re.sub(r"\(([();,+*/\-<>=! \w.\[\]]*?)\)\s*%\s*\(double\)\(([^()]*)\)",
                  r"fmod(\1, (double)(\2))", line)  # double modulo -> fmod
    line = py_ternary(line)
    return line


def split_top_word(s: str, word: str) -> int:
    """First index of ' word ' at bracket depth 0, or -1."""
    pat = " " + word + " "
    depth = 0
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif depth == 0 and s.startswith(pat, i):
            return i
        i += 1
    return -1


def py_ternary(e: str) -> str:
    """`val if cond else alt` -> `cond ? val : alt` (right-leaning chains)."""
    iif = split_top_word(e, "if")
    if iif < 0:
        return e
    # keep any `lhs = ` assignment prefix outside the conditional
    ieq = -1
    depth = 0
    for i in range(iif):
        ch = e[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif depth == 0 and ch == "=" and (i + 1 >= len(e) or e[i + 1] != "=") \
                and (i == 0 or e[i - 1] not in "=!<>*+-/%"):
            ieq = i
    if ieq >= 0:
        lhs, rest = e[:ieq + 1], e[ieq + 1:]
    else:
        lhs, rest = "", e
    j = split_top_word(rest, "if")
    if j < 0:
        return e
    val = rest[:j]
    rest2 = rest[j + 4:]
    k = split_top_word(rest2, "else")
    if k < 0:
        return e
    cond = rest2[:k]
    els = rest2[k + 6:]
    return f"{lhs} ({cond.strip()}) ? ({py_ternary(val.strip())}) : ({py_ternary(els.strip())})"


def split_top(s: str, sep: str):
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


def split_stmts(s: str):
    """Split a physical line on top-level ';' statement separators."""
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == ";" and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def find_close(s: str, open_idx: int) -> int:
    """Index of the paren closing the one at open_idx."""
    depth = 0
    for i in range(open_idx, len(s)):
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def bracket_ids(text: str):
    """Identifiers appearing inside ANY bracket expression (index candidates)."""
    ids = set()
    work = text
    while True:
        m = re.search(r"\[([^\[\]]*)\]", work)
        if not m:
            break
        ids |= set(re.findall(r"[A-Za-z_]\w*", m.group(1)))
        work = work[:m.start()] + " " * len(m.group(0)) + work[m.end():]
    return ids


def subscripted(text: str):
    return set(re.findall(r"\b([A-Za-z_]\w*)\s*\[", text))


def int_kind(e: str, ints: set):
    """'int' | 'long long' | None (double). e is already t_expr'd."""
    e = e.strip()
    if re.fullmatch(r"[+-]?\d+", e):
        return "int" if abs(int(e)) < 2 ** 31 else "long long"
    if re.fullmatch(r"true|false", e):
        return "int"
    m = re.match(r"^\((int|long long)\)\s*\(", e)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z_]\w*", e):
        if e in ints:
            return "int"
        return None
    if re.search(r"[A-Za-z_]\w*\s*\(", e):  # function call
        return None
    if "/" in e:
        return None
    if re.search(r"\d+\.\d*|\.\d+|\d[eE]", e):  # float literal
        return None
    # conditional expression (py_ternary already produced `cond ? val : alt`):
    # int only if BOTH result branches are int. The bare comparison rule below
    # otherwise mis-types `store = bat[d-1] if (d-1) < 12 else bat_post` (a
    # double load) as int -- measured: the posture store drained to zero at
    # tick-1 substep-1 in the DLL (closeout-2 lane).
    if "?" in e:
        q = e.index("?")
        depth = 0
        colon = -1
        for i2 in range(q + 1, len(e)):
            ch2 = e[i2]
            if ch2 in "([":
                depth += 1
            elif ch2 in ")]":
                depth -= 1
            elif ch2 == ":" and depth == 0:
                colon = i2
                break
        if colon > 0:
            a = int_kind(e[q + 1:colon], ints)
            b = int_kind(e[colon + 1:], ints)
            if a is not None and b is not None:
                return a if a == "long long" else b
            return None
    if any(op in e for op in ("<=", ">=", "==", "!=", "<", ">")):
        return "int"  # comparison
    toks = re.findall(r"[A-Za-z_]\w*", e)
    if toks and all(t in ints for t in toks):
        return "int"
    return None


def join_continuations(lines):
    """Join physical lines with unbalanced brackets into logical lines."""
    out = []
    buf, depth = "", 0
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("#") and depth == 0:
            out.append(ln)
            continue
        for ch in ln:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
        if buf:
            buf = buf.rstrip() + " " + stripped
        else:
            buf = ln
        if depth <= 0:
            depth = 0
            out.append(buf)
            buf = ""
    if buf.strip():
        out.append(buf)
    return out


def parse_functions(src: str):
    segs = re.split(r"(?=@cuda\.jit)", src)
    out = []
    for seg in segs:
        m = re.match(r"@cuda\.jit(?:\(([^)]*)\))?\s*\ndef\s+(\w+)\(([^)]*)\)\s*:\s*\n(.*?)(?=\n\n@cuda\.jit|\Z)", seg, re.S)
        if not m:
            continue
        deco, name, args, body = m.group(1) or "", m.group(2), m.group(3), m.group(4)
        kind = "global" if "device=True" not in deco else "device"
        body_lines = join_continuations(body.split("\n"))
        while body_lines and not body_lines[0].strip():
            body_lines.pop(0)
        while body_lines and not body_lines[-1].strip():
            body_lines.pop()
        out.append((name, args, body_lines, kind))
    return out


def tuple_arity(body_lines):
    n = None
    for raw in body_lines:
        st = strip_comment(raw).strip()
        m = re.match(r"return\s+(.+)$", st)
        if m and "," in split_top_protect(m.group(1)):
            vals = split_top(m.group(1), ",")
            if n is None:
                n = len(vals)
            assert n == len(vals), f"mixed tuple arity: {n} vs {len(vals)} at: {st}"
    return n


def split_top_protect(s: str):
    """Return s if the commas are top-level (used to detect real tuples)."""
    depth = 0
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            return s
    return ""


def analyze_calls(name, argnames, body_lines, fnset):
    """Call sites with bare-name args, for the cross-function type fixpoint."""
    scan = "\n".join(strip_comment(r) for r in body_lines)
    calls = []
    for m in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", scan):
        fname = m.group(1)
        if fname not in fnset:
            continue
        ci = find_close(scan, m.end() - 1)
        if ci < 0:
            continue
        inner = scan[m.end():ci]
        aargs = []
        for a in split_top(inner, ","):
            a = a.strip()
            aargs.append(a if re.fullmatch(r"[A-Za-z_]\w*", a) else None)
        calls.append((fname, aargs))
    return calls


def range_bound_ids(body_lines):
    """Identifiers used as range() bounds: integer-valued by construction."""
    out = set()
    for raw in body_lines:
        for st0 in split_stmts(strip_comment(raw)):
            m = re.search(r"range\(", st0)
            if m:
                oi = st0.index("range(")
                ci = find_close(st0, oi + len("range(") - 1)
                if ci > 0:
                    out |= set(re.findall(r"[A-Za-z_]\w*", st0[oi + len("range("):ci]))
    return out


def local_ptr_seeds(body_lines):
    """Local names that are arrays with known ctype: cuda.local.array only."""
    out = {}
    for raw in body_lines:
        for st0 in split_stmts(strip_comment(raw)):
            m = re.match(r"\s*(\w+)\s*=\s*cuda\.local\.array\(([^,]+),\s*dtype=(float64|int32|int64)\)", st0)
            if m:
                out[m.group(1)] = {"float64": "double*", "int32": "int*", "int64": "long long*"}[m.group(3)]
    return out


def local_aliases(body_lines):
    """nm = base array aliasing: nm -> base."""
    out = {}
    for raw in body_lines:
        for st0 in split_stmts(strip_comment(raw)):
            m = re.match(r"\s*(\w+)\s*=\s*(\w+)\s*$", st0)
            if m and m.group(1) != m.group(2):
                out[m.group(1)] = m.group(2)
    return out


def translate_function(name, args_str, body_lines, kind, tarity, warn, arg_kind_ext=None):
    argnames = [a.strip().split("=")[0].strip() for a in args_str.split(",") if a.strip()]
    scan = "\n".join(strip_comment(r) for r in body_lines)
    arrays = subscripted(scan)
    idx_ids = bracket_ids(scan) | range_bound_ids(body_lines)
    grid_vars, la_names, slice_names, loop_vars = set(), set(), set(), set()
    slice_dtype = {}

    # --- scan pass: find loop vars, local arrays, slices, array ctypes ---
    arr_ctype = {}
    for raw in body_lines:
        for st0 in split_stmts(strip_comment(raw)):
            st = st0.strip()
            if not st:
                continue
            m = re.match(r"for\s+(\w+)\s+in\s+range\(", st)
            if m:
                loop_vars.add(m.group(1))
            m = re.match(r"(\w+)\s*=\s*cuda\.local\.array\(([^,]+),\s*dtype=(float64|int32|int64)\)", st)
            if m:
                la_names.add(m.group(1))
                arr_ctype[m.group(1)] = {"float64": "double", "int32": "int", "int64": "long long"}[m.group(3)]
            m = re.match(r"(\w+)\s*=\s*(\w+)\[[^:\]]+:[^:\]]+\]$", st)
            if m:
                slice_names.add(m.group(1))
                slice_dtype[m.group(1)] = m.group(2)
                arr_ctype[m.group(1)] = None  # filled after arg kinds known
            m = re.match(r"(\w+)\s*=\s*cuda\.grid\(1\)$", st)
            if m:
                grid_vars.add(m.group(1))

    # --- arg typing ---
    cargs = []
    arg_kind = {}
    for an in argnames:
        if an in HOST_INT32_ARGS:
            arg_kind[an] = "int*"
        elif an in HOST_INT64_ARGS:
            arg_kind[an] = "long long*"
        elif an in HOST_INT_SCALARS:
            arg_kind[an] = "int"
        elif an in INT_ARR_ARGS:
            arg_kind[an] = "int*"
        elif an in arrays and an in idx_ids:
            arg_kind[an] = "int*"  # subscripted AND its contents used as an index
        elif an in arrays:
            arg_kind[an] = "double*"
        elif an in idx_ids:
            arg_kind[an] = "int"
        elif SINGLE_INT_ARGS.match(an):
            arg_kind[an] = "int"
        else:
            arg_kind[an] = "double"
    if arg_kind_ext:
        for an, k in arg_kind_ext.items():
            arg_kind[an] = k
    for an in argnames:
        cargs.append(f"{arg_kind[an]} {an}")

    # finish array ctypes: slices follow their base arg; pointer args too
    ptr_base = {"int*": "int", "long long*": "long long", "double*": "double"}
    for sl, base in slice_dtype.items():
        arr_ctype[sl] = ptr_base.get(arg_kind.get(base), "double")
    for an, k in arg_kind.items():
        if k in ptr_base:
            arr_ctype[an] = ptr_base[k]

    # --- hoist pass (ordered) ---
    # loop vars ARE hoisted (Python rebinds them across loops; C++ for-scopes
    # would kill them) -> for-headers emit without `int` when hoisted.
    skip = set(argnames) | grid_vars
    kinds = {}

    def ctx_ints():
        s = set(GLOBAL_INTS) | idx_ids | loop_vars | grid_vars
        s |= {nm for nm, k in kinds.items() if k in ("int", "long long")}
        return s

    for raw in body_lines:
        for st0 in split_stmts(strip_comment(raw)):
            st = st0.strip()
            if not st or st.startswith("#"):
                continue
            m = re.match(r"(\w+)\s*=\s*cuda\.local\.array\(", st)
            if m:
                continue
            m = re.match(r"(\w+)\s*=\s*cuda\.grid\(1\)$", st)
            if m:
                continue
            m = re.match(r"(\w+)\s*=\s*(\w+)\[[^:\]]+:[^:\]]+\]$", st)
            if m:
                continue
            m = re.match(r"for\s+(\w+)\s+in\s+range\(", st)
            if m:
                v = m.group(1)
                if v not in skip and v not in la_names and v not in slice_names:
                    kinds.setdefault(v, "int")
                continue
            if re.match(r"while\s+", st) \
               or re.match(r"if\s+", st) or re.match(r"elif\s+", st) or st == "else:" \
               or st in ("break", "continue", "pass") or re.match(r"return\b", st):
                continue
            if "=" in st and not st.startswith("="):
                lhs, rhs = st.split("=", 1)
                if "," in lhs:
                    for nm in [x.strip() for x in lhs.split(",")]:
                        if nm and nm not in skip and nm not in kinds:
                            kinds[nm] = "int" if nm in idx_ids else "double"
                            if kinds[nm] == "double" and nm in idx_ids:
                                warn.append(f"{name}: tuple target {nm} is index-used but forced double")
                    continue
                m2 = re.match(r"^(\w+)$", lhs.strip())
                if m2:
                    nm = m2.group(1)
                    if nm in skip:
                        continue
                    base = rhs.strip()
                    if base in arr_ctype and nm not in la_names and nm not in slice_names:
                        kinds[nm] = arr_ctype[base] + "*"  # alias of an array
                        continue
                    if nm in idx_ids:
                        kinds[nm] = "int"
                    elif nm not in kinds:
                        k = int_kind(t_expr(rhs), ctx_ints())
                        kinds[nm] = k or "double"
                    continue
                m2 = re.match(r"^(\w+)\s*(\+=|-=|\*=|/=)$", lhs.strip())
                if m2:
                    nm = m2.group(1)
                    if nm in skip:
                        continue
                    if nm not in kinds:
                        kinds[nm] = "int" if nm in idx_ids else "double"
                    continue

    # out params for tuple-returning functions
    outps = []
    if tarity:
        for i in range(tarity):
            outps.append(f"double* __o{i}")
        cargs += outps

    # names that ARE arrays (a `return <name>` of one is a void return)
    arrayish = (arrays - set(argnames)) | la_names | slice_names | {a for a in argnames if arg_kind.get(a) in PTRS}

    def value_returns():
        found = []
        for raw in body_lines:
            for st0 in split_stmts(strip_comment(raw)):
                st = st0.strip()
                m = re.match(r"return\s+(\S.*)$", st)
                if m:
                    tok = m.group(1).strip()
                    if not re.fullmatch(r"[A-Za-z_]\w*", tok) or tok not in arrayish:
                        found.append(tok)
        return found

    rtype = "void"
    if not tarity and kind == "device":
        vrets = value_returns()
        has_ret = bool(vrets)
        ret_int = any(re.match(r"^\(?(\(int\)|\(long long\)|0|1|-1)", v) for v in vrets)
        rtype = ("long long" if ret_int else "double") if has_ret else "void"
    prefix = "__global__ void" if kind == "global" else f"__device__ inline {rtype}"

    out = [f"{prefix} {name}({', '.join(cargs)}) {{"]
    for nm, k in kinds.items():
        out.append(f"    {k} {nm};")

    open_blocks = []
    slice_ctr = [0]

    def emit_slice(indent, nm, base, bounds):
        sl = slice_ctr[0]
        slice_ctr[0] += 1
        a, b = bounds
        size = f"(({b}) - ({a}))"
        base_is_int = arg_kind.get(base) in ("int*",)
        dt = "int" if base_is_int else "double"
        out.append(f"{' ' * indent}{dt} {nm}[{size}];")
        out.append(f"{' ' * indent}for (int _si{sl} = 0; _si{sl} < {size}; ++_si{sl}) {nm}[_si{sl}] = {base}[({a}) + _si{sl}];")

    for raw in body_lines:
        st_first = strip_comment(raw)
        indent = len(raw) - len(raw.lstrip(" "))
        for st0 in split_top(st_first, ";"):
            st = st0.strip()
            if not st:
                continue
            if st.startswith("#"):
                out.append("    //" + st[1:])
                continue
            while open_blocks and indent < open_blocks[-1]:
                out.append("}")
                open_blocks.pop()
            is_chain = bool(re.match(r"^(elif\b|else\b)", st))
            if is_chain and open_blocks and indent == open_blocks[-1] - 4:
                out.append("}")  # close the previous arm
                open_blocks.pop()

            m = re.match(r"for\s+(\w+)\s+in\s+range\(", st)
            if m:
                v = m.group(1)
                oi = st.index("range(")
                ci = find_close(st, oi + len("range(") - 1)
                inner = st[oi + len("range("):ci]
                parts = split_top(inner, ",")
                vdecl = f"int {v}" if v not in kinds else v
                if len(parts) == 1:
                    out.append(f"{' ' * indent}for ({vdecl} = 0; {v} < ({t_expr(parts[0])}); ++{v}) {{")
                elif len(parts) == 2:
                    out.append(f"{' ' * indent}for ({vdecl} = ({t_expr(parts[0])}); {v} < ({t_expr(parts[1])}); ++{v}) {{")
                else:
                    step = t_expr(parts[2]).strip()
                    if step.startswith("-"):
                        op, inc = ">", step
                    else:
                        op, inc = "<", step
                    if inc in ("1", "+1"):
                        inc_s = f"++{v}"
                    elif inc == "-1":
                        inc_s = f"--{v}"
                    else:
                        inc_s = f"{v} += ({inc})"
                    out.append(f"{' ' * indent}for ({vdecl} = ({t_expr(parts[0])}); {v} {op} ({t_expr(parts[1])}); {inc_s}) {{")
                open_blocks.append(indent + 4)
                continue
            m = re.match(r"while\s+(.+)\s*:$", st)
            if m:
                out.append(f"{' ' * indent}while ({t_expr(m.group(1))}) {{")
                open_blocks.append(indent + 4)
                continue
            m = re.match(r"if\s+(.+)\s*:$", st)
            if m:
                out.append(f"{' ' * indent}if ({t_expr(m.group(1))}) {{")
                open_blocks.append(indent + 4)
                continue
            m = re.match(r"elif\s+(.+)\s*:$", st)
            if m:
                out.append(f"{' ' * indent}else if ({t_expr(m.group(1))}) {{")
                open_blocks.append(indent + 4)
                continue
            if st == "else:":
                out.append(f"{' ' * indent}else {{")
                open_blocks.append(indent + 4)
                continue
            if st in ("break", "continue"):
                out.append(f"{' ' * indent}{st};")
                continue
            if st == "pass":
                out.append(f"{' ' * indent};")
                continue
            m = re.match(r"return\s+(.+)$", st)
            if m and tarity and "," in split_top_protect(m.group(1)):
                vals = split_top(m.group(1), ",")
                for i, rv in enumerate(vals):
                    out.append(f"{' ' * indent}(*__o{i}) = {t_expr(rv)};")
                out.append(f"{' ' * indent}return;")
                continue
            if st == "return":
                out.append(f"{' ' * indent}return;")
                continue
            m = re.match(r"return\s+(.+)$", st)
            if m:
                tok = m.group(1).strip()
                if re.fullmatch(r"[A-Za-z_]\w*", tok) and tok in arrayish:
                    out.append(f"{' ' * indent}return;")  # returning the out array
                else:
                    out.append(f"{' ' * indent}return {t_expr(m.group(1))};")
                continue
            if re.match(r"print\(", st):
                continue  # device print: dropped (numba prints do not exist on device)
            m = re.match(r"(\w+)\s*=\s*cuda\.local\.array\(([^,]+),\s*dtype=(float64|int32|int64)\)$", st)
            if m:
                nm, size = m.group(1), m.group(2).strip()
                ty = {"float64": "double", "int32": "int", "int64": "long long"}[m.group(3)]
                out.append(f"{' ' * indent}{ty} {nm}[{size if size.isdigit() else '/*CU_SIZE*/' + size}];")
                continue
            m = re.match(r"(\w+)\s*=\s*cuda\.grid\(1\)$", st)
            if m:
                out.append(f"{' ' * indent}int {m.group(1)} = blockIdx.x * blockDim.x + threadIdx.x;")
                continue
            m = re.match(r"(\w+)\s*=\s*(\w+)\[([^:\]]+)\s*:\s*([^:\]]+)\]$", st)
            if m:
                emit_slice(indent, m.group(1), m.group(2), (m.group(3), m.group(4)))
                continue
            if "=" in st and not st.startswith("="):
                lhs, rhs = st.split("=", 1)
                if "," in lhs:
                    names = [n.strip() for n in lhs.split(",")]
                    vals = split_top(rhs, ",")
                    if len(names) == len(vals):
                        for nm, rv in zip(names, vals):
                            out.append(f"{' ' * indent}{nm} = {t_expr(rv)};")
                        continue
                # tuple-call assign: a, b, c = f(...) -> f(..., &a, &b, &c)
                if "," in lhs:
                    fn = rhs.strip().split("(")[0].strip()
                    names_n = len([x for x in lhs.split(",") if x.strip()])
                    if fn in TUPLE_FNS and names_n == TUPLE_FNS[fn]:
                        refs = ", ".join("&" + x.strip() for x in lhs.split(",") if x.strip())
                        call = rhs.strip()
                        ci = call.rfind(")")
                        out.append(f"{' ' * indent}{call[:ci]}, {refs});")
                        continue
                m2 = re.match(r"^(\w+)$", lhs.strip())
                if m2:
                    nm, op = m2.group(1), "="
                    out.append(f"{' ' * indent}{nm} = {t_expr(rhs)};")
                    continue
                m2 = re.match(r"^(\w+)\s*(\+=|-=|\*=|/=)$", lhs.strip())
                if m2:
                    nm, op = m2.group(1), m2.group(2)
                    out.append(f"{' ' * indent}{nm} {op} {t_expr(rhs)};")
                    continue
            # augmented shorthand (didn't split on '=' cleanly)
            m = re.match(r"(\w+)\s*(\+=|-=|\*=|/=)\s*(.+)$", st)
            if m:
                out.append(f"{' ' * indent}{m.group(1)} {m.group(2)} {t_expr(m.group(3))};")
                continue
            # fallback: expression statement
            out.append(f"{' ' * indent}{t_expr(st)};")

    while open_blocks:
        out.append("}")
        open_blocks.pop()
    out.append("}")
    return "\n".join(out)


src = SRC.read_text(encoding="utf-8")
fns = parse_functions(src)
FNSET = {nm for (nm, a, b, k) in fns}
TUPLE_FNS = {}
for (nm0, args0, body0, kind0) in fns:
    ar = tuple_arity(body0)
    if ar:
        TUPLE_FNS[nm0] = ar

# ---- cross-function pointer-type fixpoint ----
# Seeds: name-lists (int/ll ptrs), direct subscripting (double*), contents-as-
# index (int*), index-use (int scalar). Then propagate pointer-ness across
# call sites both directions until stable (pass-through args like `rows` in
# project_rows never appear subscripted in their own body but ARE arrays).
INFO = {}
for (nm0, args0, body0, kind0) in fns:
    argnames0 = [a.strip().split("=")[0].strip() for a in args0.split(",") if a.strip()]
    scan0 = "\n".join(strip_comment(r) for r in body0)
    INFO[nm0] = {
        "argnames": argnames0,
        "subd": subscripted(scan0),
        "idx": bracket_ids(scan0) | range_bound_ids(body0),
        "calls": analyze_calls(nm0, argnames0, body0, FNSET),
        "la_ptr": local_ptr_seeds(body0),
        "alias": local_aliases(body0),
    }

PTRS = ("double*", "int*", "long long*")


def seed_kind(fn, p):
    i = INFO[fn]
    if (fn, p) in EXACT_DOUBLE_SCALARS:
        return "double"
    if p in HOST_INT32_ARGS:
        return "int*"
    if p in HOST_INT64_ARGS:
        return "long long*"
    if p in i["subd"] and p in i["idx"]:
        return "int*"
    if p in i["subd"]:
        return "double*"
    if p in i["idx"]:
        return "int"
    if SINGLE_INT_ARGS.match(p):
        return "int"
    return None


FTYPES = {}
for fn in INFO:
    for p in INFO[fn]["argnames"]:
        FTYPES[(fn, p)] = seed_kind(fn, p)


def side_type(fn, a):
    """Pointer type of name a as seen from caller fn, or None."""
    if a in INFO[fn]["argnames"]:
        return FTYPES.get((fn, a))
    if a in INFO[fn]["la_ptr"]:
        return INFO[fn]["la_ptr"][a]
    base = INFO[fn]["alias"].get(a)
    seen = 0
    while base is not None and seen < 8:
        seen += 1
        t = side_type(fn, base)
        if t:
            return t
        base = INFO[fn]["alias"].get(base)
    return None


for _ in range(64):
    changed = False
    for fn in INFO:
        for (callee, aargs) in INFO[fn]["calls"]:
            if callee not in INFO:
                continue
            cparams = INFO[callee]["argnames"]
            for j, a in enumerate(aargs):
                if a is None or j >= len(cparams):
                    continue
                q = cparams[j]
                tq = FTYPES.get((callee, q))
                ta = side_type(fn, a)
                if ta in PTRS and tq is None:
                    FTYPES[(callee, q)] = ta
                    changed = True
                elif ta in PTRS and tq == "double*" and ta != "double*":
                    FTYPES[(callee, q)] = ta  # int contents win on unification
                    changed = True
                elif tq in PTRS and ta is None and a in INFO[fn]["argnames"]:
                    FTYPES[(fn, a)] = tq
                    changed = True
    if not changed:
        break

for (fnq, p), t in sorted(FTYPES.items()):
    if t is None:
        print(f"NOTE: {fnq}:{p} type unresolved -> double")

warn = []
funcs = []
for (nm, a, b, k) in fns:
    ext = {p: t for (f2, p), t in FTYPES.items() if f2 == nm and t is not None}
    funcs.append(translate_function(nm, a, b, k, TUPLE_FNS.get(nm), warn, ext))

consts = []
for line in src.splitlines():
    m = re.match(r"^((?:OF|OI|CI|CF)_[A-Za-z_0-9]+)\s*=\s*(-?\d+)\s*(?:#.*)?$", line.strip())
    if m:
        consts.append(f"static const int {m.group(1)} = {m.group(2)};")
header = """// AUTO-TRANSLATED by numba2cu.py v4. Hand-fix scalar args where the compiler
// names stragglers. Floordiv sites are positive-operand by inspection.
// cu_total_q stands in for a_q.shape[0]: a __device__ symbol the host sets to
// E*18 at env_create (cudaMemcpyToSymbol), so the `e >= ne` tail-thread guards
// fire exactly like numba's shape-based guards.
#pragma once
#include <cuda_runtime.h>
#include <math.h>
__device__ long long cu_total_q = 1073741824LL;
#define PI 3.141592653589793
""" + "\n".join(consts)
DST.write_text(header + "\n\n" + "\n\n".join(funcs) + "\n", encoding="utf-8")
print(f"v4 translated {len(funcs)} functions -> {DST}")
print(f"tuple-returning (desugared to out-params): {TUPLE_FNS}")
for w in warn:
    print("WARN:", w)
