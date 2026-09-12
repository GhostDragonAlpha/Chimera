"""run_source_checks.py -- read-only R5/R6 measurements of the DEPLOYED
material-plane source text at base 4812b55b. NEVER contacts the live service.

Writes checks/r5_source_trace.txt (the card's semantics traced into the
deployed text with exact quoted lines at their MEASURED line numbers) and
checks/r6_findings.txt (the preregistered textual-delta predictions, measured
with the exact regexes stated in PREREGISTRATION.txt, plus the owner_instance
current state and the lane's independence audit).
Exit 1 if a preregistered threshold misses.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent.parent
CHECKS = HERE / "checks"
REPO = HERE
# docs/evidence/agent_fleet/HOLODECK/MAT/MAT-03 -> repo root is 6 up
for _ in range(6):
    REPO = REPO.parent

BASE = "4812b55b407107a34b708af1700e071a7eecbab4"
FILES = {
    "matter_data": "tools/matter_data.py",
    "material_contract": "tools/material_contract.py",
    "control": "tools/agent_fleet/control.py",
    "review_handoff": "tools/agent_fleet/review_handoff.py",
    "model": "docs/evidence/agent_fleet/HOLODECK/MAT/MAT-03/reference/"
             "mat03_reference_model.py",
}
LIBRARY = "Chimera/docs/matter/matter_library.json"

TEXT = {}


def load(rel):
    if rel not in TEXT:
        p = REPO / rel
        raw = p.read_bytes()
        TEXT[rel] = raw.decode("utf-8", errors="replace")
    return TEXT[rel]


def sha256(rel):
    return hashlib.sha256((REPO / rel).read_bytes()).hexdigest()


def quote(rel, needle, before=2, after=2, label=""):
    """Quote the MEASURED lines around the first casefold occurrence."""
    lines = load(rel).splitlines()
    idx = None
    for i, ln in enumerate(lines):
        if needle.lower() in ln.lower():
            idx = i
            break
    if idx is None:
        return None, [f"  <{needle!r} NOT FOUND in {rel}>"]
    lo, hi = max(0, idx - before), min(len(lines), idx + after + 1)
    out = [f"  {rel}:{n + 1}: {lines[n]}" for n in range(lo, hi)]
    return idx + 1, out


def count(rel, pattern):
    return len(re.findall(pattern, load(rel).lower()))


def write_r5():
    out = ["R5 -- DEPLOYED-SOURCE TRACE (card semantics in the deployed text "
           f"at base {BASE[:8]})",
           "=" * 78,
           "threshold: 5/5 semantics present, quoted at their MEASURED line "
           "numbers", ""]
    passed = 0

    def block(n_ok, title, quotes):
        nonlocal passed
        passed += n_ok
        out.append(f"[{'PASS' if n_ok else 'FAIL'}] {title}")
        out.extend(quotes)
        out.append("")

    # (i) uncertainty published-or-refused
    n, q = quote(FILES["matter_data"], "cannot set a tolerance")
    block(1 if n else 0,
          f"(i) published-or-refused uncertainty (matter_data.py measured "
          f":{n})", q)

    # (ii) a choice is not a measurement (provenance-class gate)
    n, q = quote(FILES["matter_data"], "may not be cited")
    block(1 if n else 0,
          f"(ii) a choice is not a measurement (matter_data.py measured "
          f":{n})", q)

    # (iii) source identity retained beside the number
    n1, q1 = quote(FILES["matter_data"], "matter_library.json::")
    n2, q2 = quote(FILES["matter_data"], "Every entry: value, unit, spread")
    lib = json.loads(load(LIBRARY))
    notes = sum(1 for m in lib.get("materials", {}).values()
                for e in (m.get("physical") or {}).values()
                if isinstance(e, dict) and e.get("note"))
    ok = n1 and n2 and notes > 0
    block(1 if ok else 0,
          f"(iii) source identity retained beside the number "
          f"(matter_data.py measured :{n1}, :{n2}; {notes} library entries "
          f"carry a note)", q1 + q2)

    # (iv) named refusal on missing context, never a default
    n1, q1 = quote(FILES["matter_data"], "class Uncited")
    n2, q2 = quote(FILES["material_contract"], "MISSING_INPUT")
    n3, q3 = quote(FILES["material_contract"], "class ContractRefusal")
    ok = n1 and n2 and n3
    block(1 if ok else 0,
          f"(iv) named refusal kinds (Uncited at matter_data.py:{n1}; "
          f"refusal table material_contract.py:{n2}; ContractRefusal "
          f":{n3})", q1 + q2 + q3)

    # (v) declared-only unit conversion
    n1, q1 = quote(FILES["material_contract"], "conversions exist ONLY here")
    n2, q2 = quote(FILES["material_contract"],
                   "cross-family conversion is not registered")
    ok = n1 and n2
    block(1 if ok else 0,
          f"(v) declared-only unit conversion (material_contract.py "
          f"measured :{n1}, :{n2})", q1 + q2)

    out.append(f"R5 RESULT: {passed}/5 semantics present")
    (CHECKS / "r5_source_trace.txt").write_text("\n".join(out) + "\n",
                                                encoding="utf-8")
    return passed == 5


def write_r6():
    out = ["R6 -- measured deltas and current state "
           f"(base {BASE[:8]}; regexes exactly as preregistered)",
           "=" * 78,
           "threshold: 17/17 predicted counts match; any miss is a "
           "DISCLOSED SURPRISE, never reconciled", ""]
    mc, md = FILES["material_contract"], FILES["matter_data"]
    rows = []       # (ok, label, detail)

    def row(ok, label, detail=""):
        rows.append((ok, label, detail))

    # (a) condition axes are prose-only (6 predicted counts, one row each)
    for pat, axis in ((r"\btemperature\b", "temperature"),
                      (r"\bmoisture\b", "moisture"),
                      (r"strain[-_ ]rate", "strain-rate")):
        c_mc, c_md = count(mc, pat), count(md, pat)
        pred = {"temperature": (0, 1), "moisture": (1, 3),
                "strain-rate": (0, 0)}[axis]
        row(c_mc == pred[0], f"(a) {axis} in material_contract == {pred[0]}",
            f"measured {c_mc}")
        row(c_md == pred[1], f"(a) {axis} in matter_data == {pred[1]}",
            f"measured {c_md}")

    # (b) the card's contribution gap (4 predicted counts)
    for pat, what in ((r"\binterpolat", "interpolation machinery"),
                      (r"\bversion", "dataset versioning")):
        c_mc, c_md = count(mc, pat), count(md, pat)
        row(c_mc == 0, f"(b) {what} in material_contract == 0",
            f"measured {c_mc}")
        row(c_md == 0, f"(b) {what} in matter_data == 0", f"measured {c_md}")

    # (c) the card's mathematics partially deployed (4 predicted counts)
    for pat, what, pred in ((r"\buncertainty\b", "uncertainty", (0, 3)),
                            (r"\bcitation\b", "citation", (0, 3))):
        c_mc, c_md = count(mc, pat), count(md, pat)
        row(c_mc == pred[0],
            f"(c) \\b{what}\\b in material_contract == {pred[0]}",
            f"measured {c_mc}")
        row(c_md == pred[1], f"(c) \\b{what}\\b in matter_data == {pred[1]}",
            f"measured {c_md}")

    # (d) OWNER_INSTANCE CURRENT STATE (PR #80 fix DEPLOYED; measure now)
    c_ctl = count(FILES["control"], r"owner_instance")
    c_rh = count(FILES["review_handoff"], r"owner_instance")
    row(c_ctl == 8, "(d) owner_instance in control.py == 8 (fence :121-123, "
        "setdefault :323, yield guard :499-501, claim bind :554, release "
        "clear :697)", f"measured {c_ctl}; sites:")
    for n, ln in enumerate(load(FILES["control"]).splitlines(), 1):
        if "owner_instance" in ln:
            out.append(f"    control.py:{n}: {ln.strip()}")
    row(c_rh >= 1, "(d) owner_instance in review_handoff.py >= 1 (the "
        "claim-path bind; predicted == 1 at :113; GOV-01 measured 0 at "
        "d59518b9 pre-fix -- the PR #80 fix is present iff >= 1)",
        f"measured {c_rh}; sites:")
    for n, ln in enumerate(load(FILES["review_handoff"]).splitlines(), 1):
        if "owner_instance" in ln:
            out.append(f"    review_handoff.py:{n}: {ln.strip()}")

    # (e) independence audit of this lane's model (1 row)
    imports = []
    for n, ln in enumerate(load(FILES["model"]).splitlines(), 1):
        m = re.match(r"\s*(?:import|from)\s+([A-Za-z_][\w.]*)", ln)
        if m:
            imports.append(f"{m.group(1)} (:{n})")
    banned = ("material_contract", "matter_data", "tools.")
    clean = not any(b in i for i in imports for b in banned)
    row(clean, "(e) model imports stdlib + MATH-01 backbone ONLY; nothing "
        "from the audited deployed plane",
        f"imports: {', '.join(imports)}")

    passed = sum(1 for ok, _, _ in rows if ok)
    out.append("")
    for ok, label, detail in rows:
        out.append(f"[{'PASS' if ok else 'FAIL'}] {label}")
        if detail:
            out.append(f"        {detail}")
    out.append("")
    out.append("SOURCE IDENTITY (sha256 at base):")
    for rel in list(FILES.values()) + [LIBRARY]:
        out.append(f"  {rel}  {sha256(rel)}  "
                   f"{len(load(rel).splitlines())} lines")
    out.append("")
    out.append(f"R6 RESULT: {passed}/17 predicted counts match")
    (CHECKS / "r6_findings.txt").write_text("\n".join(out) + "\n",
                                            encoding="utf-8")
    return passed == 17


def main():
    ok5 = write_r5()
    ok6 = write_r6()
    print(f"R5 {'5/5' if ok5 else 'MISSED'}; R6 "
          f"{'17/17' if ok6 else 'MISSED'} -- see checks/r5_source_trace.txt, "
          f"checks/r6_findings.txt")
    return 0 if (ok5 and ok6) else 1


if __name__ == "__main__":
    sys.exit(main())
