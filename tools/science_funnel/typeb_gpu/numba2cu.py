"""numba2cu.py v3 -- clean rewrite. Python-numba kernels -> CUDA C++.

All fixes from the takeover iterations inline:
  - open-block indent STACK (not -4 arithmetic) for brace emission
  - elif/else chains: pop one block, emit "} else ... {", re-push
  - math. stripped; min/max/abs -> fmin/fmax/fabs
  - tuple assigns (x, y, z = a, b, c) -> per-name declarations
  - return-type inference (double/int/long long) per function body
  - cuda.local.array -> fixed C arrays; cuda.grid -> thread index
  - first-use type inference for plain assigns
"""
import re
from pathlib import Path

SRC = Path(__file__).parent / "walker_numba_split.py"
DST = Path(__file__).parent / "walker_kernels.cuh"

INT_PTR_ARGS = ("a_touching", "a_captured", "a_settle", "a_ik_branch",
                "a_fore_mode", "a_fore_td_count", "a_hind_mode", "a_hind_held",
                "a_fore_clamped", "a_fore_replants", "a_cmd_live", "a_cmd_first_tick",
                "a_refused_class", "a_collapsed", "a_swing_from", "a_swing_to",
                "a_fore_t", "a_fore_cycle", "a_fore_entry", "a_fore_conv",
                "a_hind_t", "a_hind_fires", "a_hind_tds", "a_hind_last_fire",
                "a_hind_last_td", "a_cmd_fires", "rbi")
LL_PTR_ARGS = ("a_ticks", "a_refused", "a_adv_calls")

def t_expr(line: str) -> str:
    line = re.sub(r"\bint32\(", "(int)(", line)
    line = re.sub(r"\bint64\(", "(long long)(", line)
    line = re.sub(r"\bnp\.int64\(", "(long long)(", line)
    line = re.sub(r"\bfloat64\(", "(double)(", line)
    line = re.sub(r"\bnp\.float64\(", "(double)(", line)
    line = re.sub(r"\bfloat\(", "(double)(", line)
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
    return line

def split_top_commas(s: str):
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts

def classify(expr: str) -> str:
    e = expr.strip()
    if re.match(r"^-?\d+$", e):
        return "long long" if abs(int(e)) >= 2**31 else "int"
    if re.match(r"^-?(\d+\.\d*|\.\d+)", e):
        return "double"
    if e.startswith("(int)"):
        return "int"
    if e.startswith("(long long)"):
        return "long long"
    return "double"

def translate_function(name, args, body_lines, kind):
    argnames = [a.strip().split("=")[0].strip() for a in args.split(",") if a.strip()]
    body_joined0 = chr(10).join(body_lines)
    cargs = []
    for an in argnames:
        indexed = bool(re.search(r"" + re.escape(an) + r"\s*\[", body_joined0))
        if an.startswith(INT_PTR_ARGS):
            cargs.append(f"int* {an}")
        elif an.startswith(LL_PTR_ARGS):
            cargs.append(f"long long* {an}")
        elif an.startswith(("a_", "mdl", "cst", "mdi")) or indexed:
            cargs.append(f"double* {an}")
        elif re.match(r"^(i|j|k|n|e|leg|hl|hr|h|o|m|ne|E|N|pt|col|row)$", an):
            cargs.append(f"int {an}")
        else:
            cargs.append(f"double {an}")
    body_joined = chr(10).join(body_lines)
    has_ret = bool(re.search(r"^\s*return\s+\S", body_joined, re.M))
    ret_int = bool(re.search(r"^\s*return\s+\(?(int\)|0|1|-1|\(?long long)", body_joined, re.M))
    rtype = ("long long" if ret_int else "double") if has_ret else "void"
    prefix = "__global__ void" if kind == "global" else f"__device__ inline {rtype}"

    out = [f"{prefix} {name}({', '.join(cargs)}) {{"]
    declared = set(argnames)
    open_blocks = []

    for raw in body_lines:
        st = raw.strip()
        if not st:
            out.append("")
            continue
        if st.startswith("#"):
            out.append("    //" + st[1:])
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        # close blocks on dedent
        while open_blocks and indent < open_blocks[-1]:
            out.append("}")
            open_blocks.pop()

        is_chain = bool(re.match(r"^(elif\b|else\b)", st))
        if is_chain and open_blocks and indent == open_blocks[-1] - 4:
            out.append("}")  # close the previous arm
            open_blocks.pop()

        # structurals
        m = re.match(r"for\s+(\w+)\s+in\s+range\(([^)]+)\)\s*:$", st)
        if m:
            out.append(f"{' ' * indent}for (int {m.group(1)} = 0; {m.group(1)} < ({t_expr(m.group(2))}); ++{m.group(1)}) {{")
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
        if st == "return":
            out.append(f"{' ' * indent}return;")
            continue
        m = re.match(r"return\s+(.+)$", st)
        if m:
            out.append(f"{' ' * indent}return {t_expr(m.group(1))};")
            continue
        m = re.match(r"(\w+)\s*=\s*cuda\.local\.array\(([^,]+),\s*dtype=(float64|int32|int64)\)$", st)
        if m:
            nm, size, ty = m.group(1), m.group(2).strip(), {"float64": "double", "int32": "int", "int64": "long long"}[m.group(3)]
            out.append(f"{' ' * indent}{ty} {nm}[{size if size.isdigit() else '/*CU_SIZE*/' + size}];")
            declared.add(nm)
            continue
        m = re.match(r"(\w+)\s*=\s*cuda\.grid\(1\)$", st)
        if m:
            out.append(f"{' ' * indent}int {m.group(1)} = blockIdx.x * blockDim.x + threadIdx.x;")
            declared.add(m.group(1))
            continue
        # tuple assignment
        if "=" in st and not st.startswith("="):
            lhs, rhs = st.split("=", 1)
            if "," in lhs:
                names = [n.strip() for n in lhs.split(",")]
                vals = split_top_commas(rhs)
                if len(names) == len(vals):
                    for nm, rv in zip(names, vals):
                        nm = nm.strip()
                        if nm and nm not in declared:
                            out.append(f"{' ' * indent}{classify(rv)} {nm} = {t_expr(rv)};")
                            declared.add(nm)
                        else:
                            out.append(f"{' ' * indent}{nm} = {t_expr(rv)};")
                    continue
        # plain assignment (augmented or first-use)
        m = re.match(r"(\w+)\s*(\+=|-=|\*=|/=|=)\s*(.+)$", st)
        if m:
            nm, op, expr = m.group(1), m.group(2), t_expr(m.group(3))
            if op == "=" and nm not in declared:
                out.append(f"{' ' * indent}{classify(expr)} {nm} = {expr};")
                declared.add(nm)
            else:
                out.append(f"{' ' * indent}{st.replace('=', op + '=', 1) if False else nm + ' ' + op + ' ' + expr};")
            continue
        # fallback: expression statement
        out.append(f"{' ' * indent}{t_expr(st)};")

    while open_blocks:
        out.append("}")
        open_blocks.pop()
    out.append("}")
    return "\n".join(out)

src = SRC.read_text(encoding="utf-8")
segs = re.split(r"(?=@cuda\.jit)", src)
funcs = []
for seg in segs:
    m = re.match(r"@cuda\.jit\(([^)]*)\)\s*\ndef\s+(\w+)\(([^)]*)\)\s*:\s*\n(.*?)(?=\n\n@cuda\.jit|\Z)", seg, re.S)
    if not m:
        continue
    deco, name, args, body = m.group(1), m.group(2), m.group(3), m.group(4)
    kind = "global" if "device=True" not in deco else "device"
    body_lines = body.split("\n")
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    funcs.append(translate_function(name, args, body_lines, kind))

WN = Path(__file__).parent / "walker_numba.py"
consts = []
for line in WN.read_text(encoding="utf-8").splitlines():
    m = re.match(r"^(OF_[A-Za-z_0-9]+|OI_[A-Za-z_0-9]+|CI_[A-Za-z_0-9]+|CF_[A-Za-z_0-9]+|NB|NDRIVE|NPTS|NA|NI|NM)\s*=\s*(-?\d+)", line.strip())
    if m:
        consts.append(f"static const int {m.group(1)} = {m.group(2)};")
header = """// AUTO-TRANSLATED by numba2cu.py v3.1. Hand-fix CU_SIZE and scalar args.
#pragma once
#include <cuda_runtime.h>
#include <math.h>
""" + chr(10).join(consts)
DST.write_text(header + "\n\n".join(funcs) + "\n", encoding="utf-8")
print(f"v3 translated {len(funcs)} functions -> {DST}")
