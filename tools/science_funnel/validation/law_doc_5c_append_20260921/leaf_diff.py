# leaf_diff.py - leaf-level diff of two battery.json files, classifying each differing leaf.
# An ECHO leaf is one whose BOTH values are sha256-shaped strings (64 hex) OR whose value is a
# copy of a watched/banked file hash; anything else is a VERDICT leaf (falsifier if it differs).
import hashlib
import json
import sys
from pathlib import Path


def flatten(o, prefix=""):
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            out.update(flatten(v, prefix + "/" + str(k)))
    elif isinstance(o, list):
        for idx, v in enumerate(o):
            out.update(flatten(v, prefix + "/" + str(idx)))
    else:
        out[prefix] = o
    return out


def is_sha(v):
    return isinstance(v, str) and len(v) == 64 and all(c in "0123456789abcdef" for c in v)


def main():
    old_p, new_p = sys.argv[1], sys.argv[2]
    old = flatten(json.loads(Path(old_p).read_text(encoding="utf-8")))
    new = flatten(json.loads(Path(new_p).read_text(encoding="utf-8")))
    keys = sorted(set(old) | set(new))
    echoes, verdicts, added = [], [], []
    for k in keys:
        a, b = old.get(k, "<ABSENT>"), new.get(k, "<ABSENT>")
        if a == b:
            continue
        if a == "<ABSENT>" or b == "<ABSENT>":
            added.append((k, a, b))
        elif is_sha(a) and is_sha(b):
            echoes.append((k, a, b))
        else:
            verdicts.append((k, a, b))
    print("ECHO leaves (sha256-shaped value changed):", len(echoes))
    for k, a, b in echoes:
        print("  %s\n    %s -> %s" % (k, a[:16], b[:16]))
    print("ADDED/REMOVED leaves:", len(added))
    for k, a, b in added:
        print("  %s %s -> %s" % (k, str(a)[:20], str(b)[:20]))
    print("VERDICT leaves changed (MUST be zero):", len(verdicts))
    for k, a, b in verdicts:
        print("  %s\n    %r ->\n    %r" % (k, a, b))
    print("LEAF COUNT old/new:", len(old), len(new))
    return 0 if not verdicts and not added else 1


if __name__ == "__main__":
    sys.exit(main())
