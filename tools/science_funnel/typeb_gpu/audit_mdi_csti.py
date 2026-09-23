"""audit_mdi_csti.py -- the (mdi,csti) argument-order firing assertion.

The (mdi, csti) swap class has struck TWICE in this codebase (the fore_follow
call sites, closeout-5; before that the rate/impact threading). Per the closeout
standing order: after any fix in the class, EVERY call site of EVERY function
taking either table is verified by signature position. This script is the
standing artifact: parse walker_numba_split.py's AST, collect defs whose
signature names mdi or csti, then verify each call site passes each table as a
positional Name at the def's index. Functions whose signature carries only ONE
of the two tables are checked on the table they carry.

Usage: python audit_mdi_csti.py [source.py]
Exit 0 = all sites verified; exit 1 = any defect (printed).

Trailer Agent: GLM 5.3.
"""
import ast
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "walker_numba_split.py"
tree = ast.parse(open(path, encoding="utf-8").read())

defs = {}
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        params = [a.arg for a in node.args.args]
        for tab in ("mdi", "csti"):
            if tab in params:
                defs.setdefault(node.name, params)
                break

checked = 0
defects = 0


def visit(node):
    global checked, defects
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in defs:
        params = defs[node.func.id]
        pos = {a.id: i for i, a in enumerate(node.args) if isinstance(a, ast.Name)}
        for tab in ("mdi", "csti"):
            if tab not in params:
                continue
            if tab not in pos:
                print(f"L{node.lineno}: {node.func.id}: {tab} not a positional Name argument")
                defects += 1
            elif pos[tab] != params.index(tab):
                print(f"L{node.lineno}: {node.func.id} ARG-ORDER DEFECT: {tab} at arg "
                      f"{pos[tab]}, declaration wants {params.index(tab)}")
                defects += 1
            else:
                checked += 1
    for ch in ast.iter_child_nodes(node):
        visit(ch)


visit(tree)
print(f"verified call sites: {checked}  defects: {defs and 0 or 0}+{defects}")
sys.exit(1 if defects else 0)
