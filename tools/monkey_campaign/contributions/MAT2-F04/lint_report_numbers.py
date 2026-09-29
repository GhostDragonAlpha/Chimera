"""Prose-from-receipt lint: every numeric literal in report.md must be traceable.

Correction round (MAT2-F04, review blockers F1-F3; pattern adopted from
MAT2-B05's lint_report_numbers): a report prose number that exists in no
bound artifact is untraceable and must not ship (the falsifier class
"inconsistent numeric evidence"). This script scans report.md for numeric
literals and accepts each one only if it is

  1. whitelisted below with a recorded reason (dates are stripped by pattern;
     section-number-style identifiers are not matched at all), or
  2. equal as a float to some number in a bound artifact (the emitted
     receipts, replay trace, capture manifest/context/validation receipt,
     camera manifest, bound PREREGISTRATION) within the literal's own stated
     precision (half unit of its last stated digit), with an added 1e-15
     relative floor that only covers float-repr last-ulp drift, or
  3. an exact substring of a bound artifact's text.

Hex identifiers (sha256s, attempt/arrival/commit ids) are stripped before
scanning; digits glued into identifiers (MAT2-F04, FB1-FB7, P0-P8, V1-V3)
are not matched as literals.

Run:  python -B lint_report_numbers.py            # exit 0 = all traceable
      python -B lint_report_numbers.py --selftest # must flag crafted literals
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "report.md"

# Bound artifacts a report number may cite. Every JSON artifact here is
# emitted by implementation.py/make_report.py from the pinned inputs;
# PREREGISTRATION.md is bound by its recorded commit in the receipt.
ARTIFACT_PATHS = [
    HERE / "evidence" / "checks.json",
    HERE / "evidence" / "determinism.json",
    HERE / "evidence" / "contact_trace.json",
    HERE / "evidence" / "capture_manifest.json",
    HERE / "evidence" / "capture_context.json",
    HERE / "evidence" / "validation_receipt.json",
    HERE / "evidence" / "camera_manifest.json",
    HERE / "PREREGISTRATION.md",
]

# (literal, reason) explicitly exempted from artifact matching.
WHITELIST = {}

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
HEX_RE = re.compile(r"[0-9a-f]{16,}")
DIM_X_RE = re.compile(r"(\d+)\s*[xX]\s*(\d+)")
NUM_RE = re.compile(r"(?<![A-Za-z0-9_.])(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")

# Minimum length for the substring tier (short tokens go through the float
# tier, which is value-based and stricter for them).
SUBSTRING_MIN = 3
REL_FLOOR = 1e-15  # relative floor covering float-repr last-ulp drift only


def strip_non_literals(text):
    text = DIM_X_RE.sub(r"\1 \2", text)  # 960x540, 30x30 -> tokens
    text = DATE_RE.sub(" ", text)  # dates whitelisted by pattern
    text = HEX_RE.sub(" ", text)  # sha256/attempt/arrival/commit hex ids
    return text


def stated_precision(literal):
    """Half unit of the last stated digit, in the literal's own scale."""
    mant, _, exp = literal.lower().partition("e")
    exponent = int(exp) if exp else 0
    decimals = len(mant.split(".")[1]) if "." in mant else 0
    return 0.5 * (10.0 ** (-decimals)) * (10.0 ** exponent)


def collect_json_numbers(obj, out):
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        out.append(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            collect_json_numbers(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_json_numbers(v, out)


def load_artifacts():
    texts = {}
    floats = []
    for path in ARTIFACT_PATHS:
        if not path.exists():
            raise SystemExit(f"bound artifact missing: {path}")
        raw = path.read_text(encoding="utf-8")
        texts[path.name] = raw
        if path.suffix == ".json":
            collect_json_numbers(json.loads(raw), floats)
        else:
            floats.extend(
                float(m) for m in NUM_RE.findall(strip_non_literals(raw))
            )
    return texts, floats


def traceable(literal, texts, floats):
    if literal in WHITELIST:
        return "whitelist"
    value = float(literal)
    tol = max(stated_precision(literal), REL_FLOOR * abs(value))
    if any(abs(value - w) <= tol + 1e-300 for w in floats):
        return "value"
    if len(literal) >= SUBSTRING_MIN and any(
        literal in t for t in texts.values()
    ):
        return "substring"
    return None


def check_text(text, texts, floats):
    """Return list of (line_no, literal) that no tier can trace."""
    bad = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for literal in NUM_RE.findall(strip_non_literals(line)):
            if traceable(literal, texts, floats) is None:
                bad.append((line_no, literal))
    return bad


def main(argv):
    texts, floats = load_artifacts()
    report = REPORT.read_text(encoding="utf-8")
    bad = check_text(report, texts, floats)
    if bad:
        print(f"lint_report_numbers: FAIL — {len(bad)} untraceable number(s)")
        for line_no, literal in bad:
            line = report.splitlines()[line_no - 1].strip()
            print(f"  line {line_no}: {literal!r}  in: {line[:80]}")
        return 1
    total = sum(
        len(NUM_RE.findall(strip_non_literals(line)))
        for line in report.splitlines()
    )
    print(
        f"lint_report_numbers: OK — {total} numeric literals in report.md, "
        f"all traceable to bound artifacts "
        f"(whitelist entries: {len(WHITELIST)})"
    )
    if "--selftest" in argv:
        # Both crafted literals must be FLAGGED: a fabricated radial gap in
        # the FB4 row's shape (0.0337 matches no bound artifact; the honest
        # clean baseline 3.671e-07 and ghost gap 0.01 DO) and a fabricated
        # tail clearance (0.0123457). Proves the lint has teeth.
        originals = [
            "a fabricated FB4 row recorded a worst vertex radial gap of "
            "0.0337 m.",
            "a fabricated tail clearance of 0.0123457 m would fail here.",
        ]
        caught = [check_text(t, texts, floats) for t in originals]
        assert all(caught), f"selftest failed: {caught!r}"
        assert any(lit == "0.0337" for _, lit in caught[0]), caught
        assert any(lit == "0.0123457" for _, lit in caught[1]), caught
        print(
            "selftest: OK — crafted untraceable literals (0.0337, "
            "0.0123457) are flagged"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
