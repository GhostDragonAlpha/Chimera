"""gen_device_header.py v2 -- device-compilable copy of the walker physics.

Annotates function signatures with __host__ __device__ using brace-depth
tracking: only lines at depth 0 (free functions) or depth 1 (class members)
that look like definitions get annotated. Local declarations (depth >= 2)
never do.
"""
import re
from pathlib import Path

SRC = Path(__file__).parent / "gait_controller_ref.hpp"
DST = Path(__file__).parent / "walker_device.hpp"
HDR = "__host__ __device__ "

s = SRC.read_text(encoding="utf-8", errors="replace")
lines = s.split("\n")
out = []
depth = 0
KEYWORDS = ("//", "#", "else", "return", "if", "for", "while", "switch", "throw",
            "operator", "case", "do", "goto", "try", "catch", "using", "namespace",
            "typedef", "static_assert", "extern", "friend", "template", "public:",
            "private:", "protected:")

def count_braces(line):
    l = re.sub(r'"(?:[^"\\]|\\.)*"', '""', line)
    l = re.sub(r"'(?:[^'\\]|\\.)*'", "''", l)
    l = re.sub(r"//.*", "", l)
    return l.count("{") - l.count("}")

for line in lines:
    stripped = line.strip()
    annotate = False
    if depth in (0, 1) and stripped and not stripped.startswith(KEYWORDS):
        m = re.match(r"^[A-Za-z_][\w:<>,\s\*&~\[\]]*?\s+[A-Za-z_~][\w:~]*\s*\(", stripped)
        if m and "(" in stripped and not stripped.endswith(","):
            annotate = True
    out.append((HDR + line) if annotate else line)
    depth += count_braces(line)
    if depth < 0:
        depth = 0

DST.write_text("\n".join(out), encoding="utf-8")
print(f"annotated copy written: {DST} ({len(out)} lines, final depth {depth})")
