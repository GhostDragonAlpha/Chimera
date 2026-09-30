#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MAT2-A09 report-numbers lint (house P2/G2).

Every numeric literal in report.md must be traceable, at its printed
precision, to a bound artifact (emitted package document, receipts, evidence
snapshots, PREREGISTRATION.md) by exact repr match, printed-precision match
(half unit of the last stated digit + 1e-15 relative floor), or exact
substring of an artifact's raw text - or be a whitelisted entry with an
honest, load-bearing reason.

--selftest proves the lint still flags planted phantom literals (the original
B05 defect class) and that the real report is clean.
"""

import json
import re
import sys
from pathlib import Path

CARD_DIR = Path(__file__).resolve().parent

ARTIFACT_PATHS = [
    CARD_DIR / "grasp_package.json",
    CARD_DIR / "qualification_receipt.json",
    CARD_DIR / "evidence" / "falsifier_receipt.json",
    CARD_DIR / "evidence" / "registry_verification_profile.json",
    CARD_DIR / "evidence" / "registry_profile_provenance.json",
    CARD_DIR / "evidence" / "capture_manifest.json",
    CARD_DIR / "evidence" / "capture_context.json",
    CARD_DIR / "evidence" / "validation_receipt.json",
    CARD_DIR / "evidence" / "cameras.json",
    CARD_DIR / "PREREGISTRATION.md",
]

NUMBER_RE = re.compile(r"(?<![\w.])[-+]?\d[\d_]*(?:\.\d+)?(?:[eE][-+]?\d+)?")

# Whitelist: entry -> honest, load-bearing reason.  Intentionally EMPTY for
# this card: every printed literal must trace to a bound artifact (repr,
# printed-precision, or substring).  Add an entry only with a true reason.
WHITELIST = {}


def load_artifacts():
    texts = {}
    floats = []
    for p in ARTIFACT_PATHS:
        if not p.exists():
            continue
        raw = p.read_bytes().decode("utf-8")
        texts[str(p.relative_to(CARD_DIR)).replace("\\", "/")] = raw
        if p.suffix == ".json":
            def walk(o):
                if isinstance(o, bool):
                    return
                if isinstance(o, (int, float)):
                    floats.append((o, p.name))
                elif isinstance(o, dict):
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(json.loads(raw))
    return texts, floats


def traceable(lit, texts, floats):
    if lit in WHITELIST:
        return "whitelist"
    # exact substring of any bound artifact text
    for name, raw in texts.items():
        if lit in raw:
            return "substring:" + name
    # printed-precision match against an artifact numeric value
    val = float(lit.replace("_", ""))
    if "e" in lit or "E" in lit:
        mant_d = len(lit.lower().split("e")[0].split(".")[1]) if "." in lit else 0
    else:
        mant_d = len(lit.split(".")[1]) if "." in lit else 0
    tol = 0.5 * (10 ** -mant_d)
    for v, name in floats:
        if isinstance(v, int):
            if not lit.isdigit():
                continue
            if int(lit) == v:
                return "int:" + name
            continue
        if repr(v) == lit or json.dumps(v) == lit:
            return "repr:" + name
        if abs(float(lit) - v) <= tol + 1e-15 * max(1.0, abs(v)):
            return "precision:%s" % name
    return None


def check_text(text, texts, floats):
    defects = []
    for m in NUMBER_RE.finditer(text):
        lit = m.group(0)
        if traceable(lit, texts, floats) is None:
            alt = lit.lstrip("+").lstrip("0") or "0"
            if traceable(alt, texts, floats) is not None:
                continue
            defects.append((m.start(), lit))
    return defects


def selftest(texts, floats):
    planted = [
        "phantom sizing radius r = 4.766e-02 m (the original B05 defect class)",
        "stale gap 44.7 mm from an earlier build era",
        "untraceable 123.456789 claim",
    ]
    blob = "\n".join(planted)
    hits = check_text(blob, {k: v for k, v in texts.items()}, floats)
    found = {h[1] for h in hits}
    need = {"4.766e-02", "44.7", "123.456789"}
    if not need.issubset(found):
        raise ValueError("lint_selftest_planted_literals_not_flagged:%s"
                         % sorted(need - found))
    return {"planted": sorted(need), "flagged": sorted(found)}


def main(argv):
    report = CARD_DIR / "report.md"
    if not report.exists():
        print("report.md missing")
        return 2
    texts, floats = load_artifacts()
    if "--selftest" in argv:
        st = selftest(texts, floats)
        print("selftest OK: planted phantom literals flagged:", st["flagged"])
    text = report.read_bytes().decode("utf-8")
    defects = check_text(text, texts, floats)
    if defects:
        for pos, lit in defects:
            line = text.count("\n", 0, pos) + 1
            print("LINT defect line %d: untraceable literal %r" % (line, lit))
        print("LINT FAIL: %d untraceable literals" % len(defects))
        return 1
    print("LINT OK: every report number traceable to bound artifacts")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
