"""numba2cu.py v2 -- indent-aware Python-numba -> CUDA C++ translator.

Handles the idiom set of walker_numba_split.py:
  for i in range(N): / while cond: / if/elif/else / break / continue / return [x]
  first-use type inference: X = <double-expr> -> double X = ...; int-expr -> int/long long
  cuda.local.array / grid / casts / math / and-or-not (from v1)
  augmented assigns (+=, -=, *=, /=)
  bare array indexing stays as-is (arrays are pointers)
Emits braces on indent/dedent. Unknown lines pass through marked CU_RAW for compile-fix.
"""
import re
from pathlib import Path

SRC = Path(__file__).parent / "walker_numba_split.py"
DST = Path(__file__).parent / "walker_kernels.cuh"

src = SRC.read_text(encoding="utf-8")

def classify(expr: str):
    """infer a C type for a first-use assignment, or None (already declared / pointer)."""
    e = expr.strip()
    if re.match(r"^-?\d+$", e):
        return "int" if abs(int(e)) < 2**31 else "long long"
    if re.match(r"^-?\d+\.\d*(e-?\d+)?$|^-?\.\d+", e.lower()):
        return "double"
    if e.startswith("(double)") or re.search(r"\d\.\d", e) or re.search(r"\b(kp|kd|dt|phi|tau|g|v|cst\[|mdi\[|mdl\[|q\[|w\[|fr\[)", e):
        return "double"
    if e.startswith(("(int)", "(long long)")) or re.match(r"^-?\d+$", e):
        return "int"
    if re.match(r"^[a-z_]\w*$", e):  # copy of known var -- assume double (dominant)
        return "double"
    return "double"  # default: the kernels are float-dominated

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
    line = re.sub(r"\bTrue\b", "true", line)
    line = re.sub(r"\bFalse\b", "false", line)
    line = re.sub(r"\bis not\b", "!=", line)
    line = re.sub(r"\bis\b", "==", line)
    line = re.sub(r"\bnot\b", "!", line)
    # and/or as words outside identifiers
    line = re.sub(r"(?<![\w])or(?![\w])", "||", line)
    line = re.sub(r"(?<![\w])and(?![\w])", "&&", line)
    line = re.sub(r"math\.", "", line)
    return line

def translate_function(name, args, body_lines, kind):
    declared = set()
    argnames = [a.strip() for a in args.split(",") if a.strip()]
    for a in argnames:
        declared.add(a.split("=")[0].strip())
    cargs = []
    for a in argnames:
        an = a.split("=")[0].strip()
        if an.startswith(("rbi", "a_touching", "a_captured", "a_settle", "a_ik_branch",
                          "a_fore_mode", "a_fore_td_count", "a_hind_mode", "a_hind_held",
                          "a_refused", "a_ticks", "a_fires", "a_tds", "a_collapsed",
                          "a_fore_clamped", "a_fore_replants", "a_cmd_live")):
            cargs.append(("int*" if not an.startswith(("a_ticks", "a_refused", "a_fires", "a_tds")) else "long long*", an))
        elif an.startswith("rb"):
            cargs.append(("int*", an))
        elif re.match(r"^(phi_l0|phi_r0|settle)", an):
            cargs.append(("double*", an))  # hand-fix pass will adjust scalars
        else:
            cargs.append(("double*", an))
    prefix = "__global__ void" if kind == "global" else "__device__ inline void"
    out = [f"{prefix} {name}({', '.join(t + ' ' + n for t, n in cargs)}) {{"]
    indent_stack = [0]
    pending = []  # deferred local-array decls

    def emit_braces_to(new_indent):
        while indent_stack and new_indent < indent_stack[-1]:
            indent_stack.pop()
            out.append("}" * 0 + " " * 0)  # placeholder; we close at end-of-block marker
        # simplified below

    # simpler approach: pre-scan indentation, emit '}' on dedent lines
    prev_indent = None
    for raw in body_lines:
        if not raw.strip():
            out.append("")
            continue
        st0 = raw.strip()
        if st0.startswith("#"):
            out.append("    //" + st0[1:])
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        st = st0
        # close braces for dedents
        is_chain = bool(re.match(r"^(elif\s|else\s*:$)", st))
        if prev_indent is None:
            prev_indent = indent
        while indent < prev_indent:
            if not (is_chain and indent == prev_indent - 4):
                out.append("}")
            prev_indent -= 4
        prev_indent = indent
        if st.startswith("#"):
            out.append("    //" + st[1:])
            continue
        m = re.match(r"for\s+(\w+)\s+in\s+range\(([^)]+)\)\s*:", st)
        if m:
            out.append(f"{' ' * indent}for (int {m.group(1)} = 0; {m.group(1)} < ({t_expr(m.group(2))}); ++{m.group(1)}) {{")
            continue
        m = re.match(r"while\s+(.+)\s*:", st)
        if m:
            out.append(f"{' ' * indent}while ({t_expr(m.group(1))}) {{")
            continue
        m = re.match(r"if\s+(.+)\s*:", st)
        if m:
            out.append(f"{' ' * indent}if ({t_expr(m.group(1))}) {{")
            continue
        m = re.match(r"elif\s+(.+)\s*:", st)
        if m:
            out.append(f"{' ' * indent}}} else if ({t_expr(m.group(1))}) {{")
            continue
        if st == "else:":
            out.append(f"{' ' * indent}}} else {{")
            continue
        if st == "pass":
            out.append(f"{' ' * indent};")
            continue
        m = re.match(r"([\w, ]+?)\s*=\s*(.+?)\s*,\s*(.+)", st) if "=" in st and "," in st.split("=")[0] else None
        if m:
            names = [n.strip() for n in m.group(1).split(",")]
            vals = [t_expr(v) for v in re.findall(r"[^,]+(?:\([^)]*\))?", m.group(2))]
            # simple tuple: split rhs on top-level commas crudely
            rhs_parts, depth, cur = [], 0, ""
            for ch in m.group(2):
                if ch == "(" : depth += 1
                if ch == ")": depth -= 1
                if ch == "," and depth == 0:
                    rhs_parts.append(cur); cur = ""
                else:
                    cur += ch
            if cur.strip(): rhs_parts.append(cur)
            if len(names) == len(rhs_parts):
                for nm, rv in zip(names, rhs_parts):
                    nm = nm.strip()
                    if nm not in declared:
                        out.append(f"{' ' * indent}double {nm} = {t_expr(rv)};")
                        declared.add(nm)
                    else:
                        out.append(f"{' ' * indent}{nm} = {t_expr(rv)};")
                continue
        if st in ("break", "continue"):
            out.append(f"{' ' * indent}{st};")
            continue
        if st == "return":
            out.append(f"{' ' * indent}return;")
            continue
        m = re.match(r"return\s+(.+)", st)
        if m:
            out.append(f"{' ' * indent}return {t_expr(m.group(1))};")
            continue
        m = re.match(r"(\w+)\s*=\s*cuda\.local\.array\(([^,]+),\s*dtype=(float64|int32|int64)\)", st)
        if m:
            nm, size, ty = m.group(1), m.group(2).strip(), {"float64": "double", "int32": "int", "int64": "long long"}[m.group(3)]
            sz = size if size.isdigit() else f"/*CU_SIZE*/{size}"
            out.append(f"{' ' * indent}{ty} {nm}[{sz}];")
            declared.add(nm)
            continue
        m = re.match(r"(\w+)\s*=\s*cuda\.grid\(1\)", st)
        if m:
            out.append(f"{' ' * indent}int {m.group(1)} = blockIdx.x * blockDim.x + threadIdx.x;")
            declared.add(m.group(1))
            continue
        # assignments (with or without augment)
        m = re.match(r"(\w+)\s*(\+=|-=|\*=|/=|=)\s*(.+)", st)
        if m and m.group(1) not in declared and m.group(2) == "=":
            nm, expr = m.group(1), t_expr(m.group(3))
            ty = classify(expr)
            out.append(f"{' ' * indent}{ty} {nm} = {expr};")
            declared.add(nm)
            continue
        if m:
            out.append(f"{' ' * indent}{t_expr(st)};")
            continue
        # bare calls / expression statements
        line = t_expr(st)
        if re.match(r"^\w+\(", line):
            out.append(f"{' ' * indent}{line};")
        else:
            out.append(f"{' ' * indent}{line};")
    # close remaining braces
    if prev_indent is None:
        prev_indent = 8
    while prev_indent > 8:
        out.append("}")
        prev_indent -= 4
    out.append("}")
    return "\n".join(out)

segs = re.split(r"(?=@cuda\.jit)", src)
funcs = []
for seg in segs:
    m = re.match(r"@cuda\.jit\(([^)]*)\)\s*\ndef\s+(\w+)\(([^)]*)\)\s*:\s*\n(.*?)(?=\n\n@cuda\.jit|\Z)", seg, re.S)
    if not m:
        continue
    deco, name, args, body = m.group(1), m.group(2), m.group(3), m.group(4)
    kind = "global" if "device=True" not in deco else "device"
    body_lines = [l for l in body.split("\n")]
    # strip leading blanks from the split artifact
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    funcs.append(translate_function(name, args, body_lines, kind))

header = """// AUTO-TRANSLATED by numba2cu.py v2 (indent-aware). Hand-fix CU_SIZE and scalar args.
#pragma once
#include <cuda_runtime.h>
#include <math.h>
"""
DST.write_text(header + "\n\n".join(funcs) + "\n", encoding="utf-8")
print(f"v2 translated {len(funcs)} functions -> {DST}")
