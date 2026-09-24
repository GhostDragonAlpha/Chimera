#!/usr/bin/env python3
"""A6 probative-claim scan.

Scope: baseline runs/*.json, session_reports/*.md, code/DERIVATION.md,
MANIFEST.json, source_xml/chimanoid.xml (doc-strings only, not geometry).
Terms: language that could claim more than XML+fit support.
Every hit is classified: CLAIM (falsifier), DISCLAIMER (negation),
GEOMETRIC (measurement of geometry/envelope, not anatomy), NEUTRAL.
"""
import json, re
from pathlib import Path

BASE = Path("E:/PythonChimera/forearm_package/baseline_snapshot")
OUT = Path("E:/PythonChimera/forearm_package/audits/A6_evidence/receipts/a6_claim_scan.json")

FILES = sorted(BASE.glob("runs/*.json")) + sorted(BASE.glob("session_reports/*.md")) + \
        [BASE / "code/DERIVATION.md", BASE / "MANIFEST.json"]

TERMS = ["measured", "measur", "qualified", "qualification", "verified", "verify",
         "anatom", "validated", "validation", "confirmed", "proven", "evidence",
         "attachment", "attach"]

hits = []
for f in FILES:
    if not f.exists():
        continue
    text = f.read_text(errors="replace")
    rel = f.relative_to(BASE).as_posix()
    for i, ln in enumerate(text.splitlines(), 1):
        low = ln.lower()
        found = sorted({t for t in TERMS if t in low})
        if found:
            hits.append(dict(file=rel, line=i, terms=found, text=ln.strip()[:400]))

# classification: keyword heuristics applied manually below in report; the scan
# only collects. Auto-tag the obvious negations to help triage.
NEG_MARKERS = ["not ", "no body", "never", "refus", "does not", "cannot", "unresolved",
               "requires_", "false", "not_cla", "NOT claimed", "do NOT", "never fabricated",
               "NOT evidence", "NOT scaled", "NOT internal"]
for h in hits:
    low = h["text"].lower()
    h["has_negation_marker"] = any(m.lower() in low for m in NEG_MARKERS)

OUT.write_text(json.dumps(hits, indent=1))
print(f"{len(hits)} raw hits -> {OUT}")
from collections import Counter
c = Counter(h["file"] for h in hits)
for k, v in c.most_common():
    print(f"  {k}: {v}")
