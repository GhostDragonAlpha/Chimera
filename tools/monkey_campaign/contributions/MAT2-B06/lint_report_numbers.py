"""Prose-from-receipt lint for the MAT2-B06 report (B05 pattern, adapted).

Every numeric literal in report.md must be traceable:
  1. whitelisted below with a recorded reason (dates are stripped by pattern;
     dimension "WxH" tokens and hex identifiers are not matched at all), or
  2. equal as a float to some number in a bound artifact (the emitted
     readiness document, derivation receipt, verification receipt, falsifier
     log, capture manifest/context/validation receipt, bound
     PREREGISTRATION) within the literal's own stated precision (half unit of
     its last stated digit) plus a 1e-15 relative floor for float-repr drift, or
  3. an exact substring of a bound artifact's text.

Run:  python -B lint_report_numbers.py           # exit 0 = all traceable
      python -B lint_report_numbers.py --selftest  # must flag planted fakes
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "report.md"

ARTIFACT_PATHS = [
    HERE / "assembly_readiness.json",
    HERE / "derivation_receipt.json",
    HERE / "work" / "runs" / "verification_receipt.json",
    HERE / "work" / "runs" / "falsifier_log.json",
    HERE / "evidence" / "capture_manifest.json",
    HERE / "evidence" / "capture_context.json",
    HERE / "evidence" / "validation_receipt.json",
    HERE / "PREREGISTRATION.md",
]

# (literal, reason) explicitly exempted from artifact matching.
WHITELIST = {
    "78856821": (
        "preregistration commit id (all-digit hex, not strippable by the "
        "hex rule); git-provable on this branch: the frozen prereg commit "
        "that contains ONLY PREREGISTRATION.md"
    ),
}

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
# Hex ids incl. 7-8 char commit abbreviations: must contain at least one
# digit AND at least one [a-f] so scientific literals (1.6e-05) never match.
HEX_RE = re.compile(
    r"(?=(?:[0-9a-f]*[0-9]))(?=(?:[0-9a-f]*[a-f]))[0-9a-f]{6,}")
DIM_X_RE = re.compile(r"(\d+)\s*[xX]\s*(\d+)")
NUM_RE = re.compile(r"(?<![A-Za-z0-9_.])(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")
SUBSTRING_MIN = 3
REL_FLOOR = 1e-15


def strip_non_literals(text):
    text = DIM_X_RE.sub(r"\1 \2", text)
    text = DATE_RE.sub(" ", text)
    text = HEX_RE.sub(" ", text)
    return text


def stated_precision(literal):
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
                float(m) for m in NUM_RE.findall(strip_non_literals(raw)))
    return texts, floats


def traceable(literal, texts, floats):
    if literal in WHITELIST:
        return "whitelist"
    value = float(literal)
    tol = max(stated_precision(literal), REL_FLOOR * abs(value))
    if any(abs(value - w) <= tol + 1e-300 for w in floats):
        return "value"
    if len(literal) >= SUBSTRING_MIN and any(
            literal in t for t in texts.values()):
        return "substring"
    return None


def check_text(text, texts, floats):
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
        for line in report.splitlines())
    print(
        f"lint_report_numbers: OK — {total} numeric literals in report.md, "
        f"all traceable to bound artifacts "
        f"(whitelist entries: {len(WHITELIST)})")
    if "--selftest" in argv:
        planted = [
            "the implied body weight is 5.3 kg and the ratio is 4.1, "
            "so the ports qualify",
            "a substituted stand-in mass of 5.9 kg closes the weights gap",
        ]
        caught = [check_text(t, texts, floats) for t in planted]
        assert all(caught), f"selftest failed: {caught!r}"
        assert any(lit == "5.3" for _, lit in caught[0]), caught
        assert any(lit == "5.9" for _, lit in caught[1]), caught
        print(
            "selftest: OK — planted fake literals (5.3/4.1 implied-BW slip, "
            "5.9 stand-in substitution) are flagged as untraceable")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
