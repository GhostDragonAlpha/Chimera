"""06 — T6 UTILITY-BAN process check over the diagnostic's own scripts.

Same process law as the B4 gate (B4 scripts/07_t6_utility_ban.py), scanned over the
I7 scripts directory: no moment-arm / finite-difference / path-length helper /
compiler-fit invocation may appear as an evidence computation, and the gate scripts
must never read the packet's tendon/moment data as evidence.
(The coverage table of the report cites B2's receipts; script 10 verifies CHAIN
TOPOLOGY from the source XML only — site ownership facts, no lengths.)
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i7_common as IC  # noqa: E402

# tokens assembled from fragments so this scanner does not self-match its own source
_B = ["_analytic", "_arm", "_fd", r"\b_pl\s*\(", "rest_" + "length",
      "moment", "compiler\\.fit\\(", r"\bfit\\s*\\(", "finite_" + "difference"]
BANNED = [
    _B[0] + _B[1],
    _B[2] + _B[1],
    _B[3],
    _B[4],
    _B[5] + "_arm",
    _B[6],
    _B[7].replace("\\\\", "\\"),
    _B[5] + "_arms",
    _B[8],
]


def main() -> int:
    hits = []
    for p in sorted((IC.I7 / "scripts").glob("*.py")):
        text = p.read_text(encoding="utf-8")
        for tok in BANNED:
            for m in re.finditer(tok, text):
                line_no = text[: m.start()].count("\n") + 1
                line = text.splitlines()[line_no - 1].strip()
                hits.append({"file": p.name, "line": line_no, "token": tok, "line_text": line})
    clean = [h for h in hits
             if not (h["line_text"].lstrip().startswith("#")
                     or h["line_text"].lstrip().startswith('"""')
                     or "no moment arms" in h["line_text"]
                     or "no moment-arm" in h["line_text"]
                     or "never invokes" in h["line_text"])]
    IC.verdict("T6 utility-ban token scan (scripts/)", not clean,
               f"{len(list((IC.I7 / 'scripts').glob('*.py')))} scripts scanned, "
               f"{len(clean)} banned-evidence occurrences" + (f": {clean}" if clean else ""))

    # the gate never reads packet tendon/moment data
    packet_users = []
    tendons_tok = "tend" + "ons"
    muscles_tok = "musc" + "les"
    arms_tok = "moment" + "_arms"
    pat = re.compile(r"\[." + tendons_tok + r".\]|\[." + muscles_tok + r".\]|" + arms_tok)
    for p in sorted((IC.I7 / "scripts").glob("*.py")):
        text = p.read_text(encoding="utf-8")
        if pat.search(text):
            packet_users.append(p.name)
    IC.verdict("T6 packet tendon/moment data untouched", not packet_users,
               f"scripts reading tendons/muscles/arms: {packet_users or 'NONE'}")

    IC.save_receipt("06_t6_utility_ban.json", {
        "ok": not clean and not packet_users,
        "banned_tokens": BANNED,
        "hits": hits,
        "clean_hits": clean,
        "packet_tendon_readers": packet_users,
    })
    print("T6 VERDICT:", "PASS" if (not clean and not packet_users) else "FAIL")
    return 0 if (not clean and not packet_users) else 1


if __name__ == "__main__":
    raise SystemExit(main())
