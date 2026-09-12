"""run_source_checks.py -- read-only R5/R6 measurements of the DEPLOYED law /
decision-record source text at base 62b8e357. NEVER contacts the live service.

Writes checks/r5_source_trace.txt (the card's semantics traced into the
deployed text with exact quoted lines) and checks/r6_deployed_deltas.txt (the
preregistered textual-delta predictions, measured with the exact regexes).
Exit 1 if a preregistered threshold misses.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent.parent
CHECKS = HERE / "checks"
REPO = HERE
# docs/evidence/agent_fleet/HOLODECK/GOV/GOV-03 -> repo root is 6 up
for _ in range(6):
    REPO = REPO.parent

SOURCES = {
    "tools/verdict.py": None,
    "tools/port_registry.py": None,
    "tools/agent_fleet/control.py": None,
    "tools/agent_fleet/review_handoff.py": None,
}


def load(rel):
    text = (REPO / rel).read_text(encoding="utf-8", errors="replace")
    return text.splitlines(), text


def quote(lines, lo, hi):
    out = []
    for n in range(lo, hi + 1):
        if 1 <= n <= len(lines):
            out.append(f"  {rel_line(n)}: {lines[n - 1]}")
    return out


def rel_line(n):  # replaced per-file below
    return str(n)


def write_r5():
    lines_out = ["R5 -- DEPLOYED-SOURCE TRACE (card semantics in the deployed "
                 "text at base 62b8e357)", "=" * 78,
                 "threshold: 5/5 semantics present with exact quoted lines", ""]
    passed = 0
    vlines, _ = load("tools/verdict.py")
    plines, _ = load("tools/port_registry.py")

    def block(n_ok, title, quotes):
        nonlocal passed
        lines_out.append(f"[{'PASS' if n_ok else 'FAIL'}] {title}")
        lines_out.extend(quotes)
        lines_out.append("")
        passed += 1 if n_ok else 0

    # (i) statement+falsifier admission refusal
    q = quote(plines, 32, 39) + ["  ..."] + quote(plines, 61, 62) + ["  ..."] \
        + quote(plines, 97, 101)
    ok = any("needs a STATEMENT and a FALSIFIER" in x for x in q) and \
        any("is missing" in x for x in q) and \
        any("required" in x for x in q)
    block(ok, "(i) statement+falsifier required at admission "
              "(port_registry.py port_test 32-39, primitive 61-62, action 97-101)", q)

    # (ii) close requires an evidence pointer
    q = quote(vlines, 104, 115)
    ok = any("needs an EVIDENCE pointer" in x for x in q)
    block(ok, "(ii) verdict close requires a nonempty evidence pointer "
              "(verdict.py:104-115)", q)

    # (iii) fixed outcome vocabulary
    q = quote(vlines, 34, 34) + quote(vlines, 107, 109)
    ok = any("VALID_RESULTS" in x for x in q) and \
        any("must be one of" in x for x in q)
    block(ok, "(iii) fixed result vocabulary (verdict.py:34, refusal :107-109)", q)

    # (iv) count-assertion refusal
    q = quote(plines, 140, 151)
    ok = any("REFUSING TO RUN" in x for x in q)
    block(ok, "(iv) a missing record is a REFUSAL, not a smaller number "
              "(port_registry.py:140-151 expect)", q)

    # (v) composition requires already-registered parts
    q = quote(plines, 50, 78)
    ok = any("not registered ports" in x for x in q)
    block(ok, "(v) a composition may only name already-registered parts "
              "(port_registry.py:50-78 primitive_test)", q)

    lines_out.append(f"RESULT: {passed} passed, {5 - passed} failed "
                     f"(threshold {'HOLDS' if passed == 5 else 'MISSED'})")
    lines_out.append("falsifier status: "
                     + ("NOT TRIGGERED for this row" if passed == 5
                        else "FIRED -- reported, not patched"))
    (CHECKS / "r5_source_trace.txt").write_text("\n".join(lines_out) + "\n",
                                                encoding="utf-8")
    print(f"r5_source_trace.txt: {passed} passed, {5 - passed} failed")
    return 5 - passed


PREDICTIONS = [
    # (file, marker-regex description, python regex, predicted count)
    ("tools/port_registry.py", r"\bdomain\b (casefold)", r"(?i)\bdomain\b", 0),
    ("tools/port_registry.py", r"\boracle\b (casefold)", r"(?i)\boracle\b", 0),
    ("tools/port_registry.py", r"\blimitation\b (casefold)",
     r"(?i)\blimitation\b", 0),
    ("tools/port_registry.py", r"\borigin\b (casefold, excludes 'original')",
     r"(?i)\borigin\b", 0),
    ("tools/port_registry.py", r"\bdimension\b (casefold)",
     r"(?i)\bdimension\b", 0),
    ("tools/port_registry.py", r"\bassumption\b (casefold)",
     r"(?i)\bassumption\b", 0),
    ("tools/verdict.py", r"\bdomain\b (casefold)", r"(?i)\bdomain\b", 0),
    ("tools/verdict.py", r"\boracle\b (casefold)", r"(?i)\boracle\b", 0),
    ("tools/verdict.py", r"\blimitation\b (casefold)",
     r"(?i)\blimitation\b", 0),
    ("tools/verdict.py", r"\borigin\b (casefold, excludes 'original')",
     r"(?i)\borigin\b", 0),
    ("tools/verdict.py", r"\bdimension\b (casefold)",
     r"(?i)\bdimension\b", 0),
    ("tools/verdict.py", r"\bassumption\b (casefold)",
     r"(?i)\bassumption\b", 0),
    ("tools/agent_fleet/review_handoff.py", r"owner_instance",
     r"owner_instance", 0),
    ("tools/agent_fleet/control.py", r"owner_instance",
     r"owner_instance", 9),
]


def write_r6():
    lines_out = ["R6 -- MEASURED DELTAS vs the preregistered predictions "
                 "(GOV-03 PREREG.md, written before this measurement)",
                 "=" * 78,
                 "threshold: 14/14 measured counts equal the predicted "
                 "counts; any miss is a disclosed surprise", "",
                 "regex form: python re, search across the WHOLE file, "
                 "findall count; casefold where stated; \\b boundaries mean "
                 "re word-boundaries (so 'original' never matches \\borigin\\b).",
                 ""]
    missed = 0
    for rel, desc, rx, predicted in PREDICTIONS:
        _, text = load(rel)
        measured = len(re.findall(rx, text))
        ok = measured == predicted
        missed += 0 if ok else 1
        lines_out.append(f"[{'PASS' if ok else 'SURPRISE'}] {rel} :: {desc}")
        lines_out.append(f"          predicted={predicted} measured={measured}"
                         + ("" if ok else
                            "  <-- DISCLOSED MISS (reported, not reconciled)"))
    sha_rows = []
    for rel in SOURCES:
        _, text = load(rel)
        sha_rows.append(f"  {rel}: sha256 "
                        f"{hashlib.sha256(text.encode('utf-8')).hexdigest()} "
                        f"({len(text.splitlines())} lines)")
    lines_out.append("")
    lines_out.append("SOURCE IDENTITY at measurement time:")
    lines_out.extend(sha_rows)
    lines_out.append("")
    lines_out.append(f"RESULT: {14 - missed} passed, {missed} missed "
                     f"(threshold {'HOLDS' if missed == 0 else 'MISSED'})")
    lines_out.append("falsifier status: "
                     + ("NOT TRIGGERED for this row" if missed == 0
                        else "FIRED -- the miss is the recorded finding"))
    (CHECKS / "r6_deployed_deltas.txt").write_text("\n".join(lines_out) + "\n",
                                                   encoding="utf-8")
    print(f"r6_deployed_deltas.txt: {14 - missed} passed, {missed} missed")
    return missed


def main() -> int:
    total = write_r5() + write_r6()
    print("TOTAL MISSED:", total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
