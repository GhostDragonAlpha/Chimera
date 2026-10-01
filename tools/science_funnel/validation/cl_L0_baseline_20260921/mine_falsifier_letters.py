"""Mine the ORIGINAL falsifier-letter table from the pinned baseline gait_unit.cpp.

The ship state's letters are operational definitions IN THE SOURCE at the pin:
  - every ck(cond,"name") is one registered check (a red on failure; `checks` counts both ways)
  - every note("F-GX ...") literal is a measured letter line carried in stdout's "measured"
This script extracts both from a given source text and emits the letter table JSON.
The 40e63035 ship stdout carries 38 red / 137 checks; this table is what those counts mean.

Usage: python mine_falsifier_letters.py <gait_unit.cpp> <out.json>
"""
import json, re, sys, hashlib

src_path, out_path = sys.argv[1], sys.argv[2]
src = open(src_path, "r", encoding="utf-8", errors="replace").read()

checks = []
# ck(<anything>,"name") -- single line captures; multiline conditions folded first
folded = re.sub(r"\s+", " ", src)
for m in re.finditer(r'\bck\((.*?),\s*"([a-z0-9_]+)"\s*\)', folded):
    checks.append({"check": m.group(2), "condition_src": m.group(1).strip()})

letters = {}
for m in re.finditer(r'"(F-G\d+[A-Za-z0-9_]*)\s([^"\\]*(?:\\.[^"\\]*)*)"', folded):
    letter, body = m.group(1), m.group(2)
    letters.setdefault(letter, [])
    if body not in letters[letter]:
        letters[letter].append(body)

# also the NOT-MEASURED guard forms (else-branches: note("F-GX ... NOT MEASURED ..."))
# are covered by the same literal scan above.

out = {
    "source": src_path,
    "source_sha256": hashlib.sha256(open(src_path, "rb").read()).hexdigest(),
    "n_checks": len(checks),
    "checks": checks,
    "n_letters": len(letters),
    "letters": {k: letters[k] for k in sorted(letters)},
}
json.dump(out, open(out_path, "w", encoding="utf-8"), indent=1, ensure_ascii=True)
print(f"checks={len(checks)} letters={len(letters)}")
for k in sorted(letters):
    print(f"  {k}: {len(letters[k])} literal form(s)")
