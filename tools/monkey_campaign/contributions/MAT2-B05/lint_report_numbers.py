"""Prose-from-receipt lint: every numeric literal in report.md must be traceable.

Review correction round (MAT2-B05, blockers H1+H2): a report prose number that
exists in no bound artifact is untraceable and must not ship. This script scans
report.md for numeric literals and accepts each one only if it is

  1. whitelisted below with a recorded reason (dates are stripped by pattern;
     section-number-style identifiers are not matched at all), or
  2. equal as a float to some number in a bound artifact (the emitted document,
     receipts, falsifier log, replay trace, capture manifest/context/validation
     receipt, pinned data inputs, bound PREREGISTRATION) within the literal's
     own stated precision (half unit of its last stated digit), with an added
     1e-15 relative floor that only covers float-repr last-ulp drift, or
  3. an exact substring of a bound artifact's text.

Hex identifiers (sha256s, arrival/attempt ids) are stripped before scanning;
digits glued into identifiers (MAT2-B05, P1-P10, frame_010.png, h264) are not
matched as literals.

Run:  python -B lint_report_numbers.py           # exit 0 = all traceable
      python -B lint_report_numbers.py --selftest  # must flag H1/H2 originals
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "report.md"

# Bound artifacts a report number may cite. data/ files are pinned by sha in
# the emitted document; PREREGISTRATION.md is bound by its sha256 in it.
ARTIFACT_PATHS = [
    HERE / "mechanical_port_requirements.json",
    HERE / "derivation_receipt.json",
    HERE / "work" / "runs" / "verification_receipt.json",
    HERE / "work" / "runs" / "falsifier_log.json",
    HERE / "replay_trace.json",
    HERE / "capture_manifest.json",
    HERE / "capture_context.json",
    HERE / "capture_validation_receipt.json",
    HERE / "PREREGISTRATION.md",
] + sorted((HERE / "data").glob("*.json"))

# (literal, reason) explicitly exempted from artifact matching.
WHITELIST = {
    "44.2": (
        "1-decimal mm rendering of trace replay_trace.json ticks[10]"
        ".approach_gap_m = 0.044172774818681794 m (44.17 mm); the rendered "
        "gap label on frame_010.png reads 44.2 mm (review blocker H2)"
    ),
    "2.179": (
        "implementer-side decode measurement (ffmpeg mean abs pixel diff, "
        "encoded frame 262 vs source frame_262.png; lossy yuv420 only); "
        "measured during capture validation and not stored in a committed "
        "artifact, which must stay byte-identical; independently reproduced "
        "by review at 2.154-2.191 across sampled ticks (sgt-pr251 CAPTURE)"
    ),
}

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
HEX_RE = re.compile(r"[0-9a-f]{16,}")
DIM_X_RE = re.compile(r"(\d+)\s*[xX]\s*(\d+)")
NUM_RE = re.compile(r"(?<![A-Za-z0-9_.])(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")

# Minimum length for the substring tier (short tokens go through the float
# tier, which is value-based and stricter for them).
SUBSTRING_MIN = 3
REL_FLOOR = 1e-15  # relative floor covering float-repr last-ulp drift only


def strip_non_literals(text):
    text = DIM_X_RE.sub(r"\1 \2", text)  # 2560x840, 40x20, 3x3 -> tokens
    text = DATE_RE.sub(" ", text)  # dates whitelisted by pattern
    text = HEX_RE.sub(" ", text)  # sha256/attempt/arrival hex ids
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
        originals = [
            "detail does NOT meet the declared couple requirement "
            "(6.14e-06 << 0.8; sizing to meet it would\n"
            "need r = 4.766e-02 m) — recorded as `admitted: false`.",
            "tick 10 approach (gap 44.7 mm\n"
            "  label, support `hook+carriage`), tick 100 hold A.",
        ]
        caught = [check_text(t, texts, floats) for t in originals]
        assert all(caught), f"selftest failed: {caught!r}"
        assert any(lit == "4.766e-02" for _, lit in caught[0]), caught
        assert any(lit == "44.7" for _, lit in caught[1]), caught
        print(
            "selftest: OK — original H1 (r = 4.766e-02 m) and H2 "
            "(gap 44.7 mm) literals are flagged as untraceable"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
