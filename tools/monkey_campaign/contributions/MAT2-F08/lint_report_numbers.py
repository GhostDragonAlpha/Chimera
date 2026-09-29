"""Numbers lint for MAT2-F08: report.md must be exactly the receipt-derived
rendering (make_report.build_report over the committed evidence), so every
number in it is traceable to a receipt. --selftest proves the linter detects
a tampered receipt number.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
sys.path.insert(0, str(HERE))
import make_report  # noqa: E402


def main(argv):
    committed = (HERE / "report.md").read_text(encoding="utf-8")
    regenerated = make_report.build_report()
    if argv[-1] == "--selftest":
        checks = json.loads((EVIDENCE / "checks.json").read_bytes())
        tampered = json.loads(json.dumps(checks))
        tampered["scene_state"]["bytes"] += 1
        mutated = make_report.build_report(checks=tampered)
        ok = mutated != regenerated and mutated != committed
        print("selftest: tampered receipt changes the report:", ok)
        return 0 if ok else 1
    ok = committed == regenerated
    print("report.md traceable to receipts:", ok)
    if not ok:
        import difflib
        for line in list(difflib.unified_diff(
                regenerated.splitlines(), committed.splitlines(),
                "receipts", "committed", lineterm=""))[:40]:
            print(line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
