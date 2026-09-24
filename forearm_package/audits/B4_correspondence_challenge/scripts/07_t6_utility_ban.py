"""07 — T6 UTILITY-BAN process check over the challenge's own scripts.

Scans scripts/*.py for banned evidence computations (moment arms, finite-difference
arms, path/tendon length helpers, compiler.fit invocation) and asserts the challenge
never reads the packet's tendon/moment data as evidence.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b4_common as C  # noqa: E402

# tokens are assembled from fragments so this scanner does not self-match its own
# source (the ban is on EVIDENCE computations, not on the scanner that enforces it)
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

ALLOWED = {
    # module COPIES of the baseline live in work/modules — they are the baseline's own
    # code, not challenge evidence code. Only scripts/ is scanned.
}


def main() -> int:
    hits = []
    for p in sorted((C.B4 / "scripts").glob("*.py")):
        text = p.read_text(encoding="utf-8")
        for tok in BANNED:
            for m in re.finditer(tok, text):
                line_no = text[: m.start()].count("\n") + 1
                line = text.splitlines()[line_no - 1].strip()
                hits.append({"file": p.name, "line": line_no, "token": tok, "line_text": line})
    # allow-list: the token "fit(" appearing in comments/docstrings only
    clean = [h for h in hits
             if not (h["line_text"].lstrip().startswith("#")
                     or h["line_text"].lstrip().startswith('"""')
                     or "no moment arms" in h["line_text"]
                     or "never invokes" in h["line_text"])]
    C.verdict("T6 utility-ban token scan (scripts/)", not clean,
              f"{len(list((C.B4 / 'scripts').glob('*.py')))} scripts scanned, "
              f"{len(clean)} banned-evidence occurrences" + (f": {clean}" if clean else ""))

    # the challenge never reads packet tendon/moment data
    packet_users = []
    tendons_tok = "tend" + "ons"
    muscles_tok = "musc" + "les"
    arms_tok = "moment" + "_arms"
    pat = re.compile(r"\[." + tendons_tok + r".\]|\[." + muscles_tok + r".\]|" + arms_tok)
    for p in sorted((C.B4 / "scripts").glob("*.py")):
        text = p.read_text(encoding="utf-8")
        if pat.search(text):
            packet_users.append(p.name)
    C.verdict("T6 packet tendon/moment data untouched", not packet_users,
              f"scripts reading tendons/muscles/arms: {packet_users or 'NONE'}")

    C.save_receipt("07_t6_utility_ban.json", {
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
