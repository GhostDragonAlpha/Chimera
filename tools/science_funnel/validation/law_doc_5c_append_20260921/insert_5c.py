# insert_5c.py - surgical insertion of the 5C block before section 6 of the law doc.
# Verifies: pre hash, single contiguous insertion, every pre-existing byte preserved,
# everything after the insertion point byte-identical.
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DOC = ROOT / "docs" / "THE_ARTICULATION_LAW.md"
BLOCK = Path(__file__).resolve().parent / "section_5c.md"
PRE_SHA = "97585c4e7b5781d3e776d7cdaa7b4d19ce8b33772f239178cbd60be7f6410e4c"
MARKER = "## 6. WHY THIS LANE DID NOT BUILD THE PROOF"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    pre = DOC.read_bytes()
    assert sha(pre) == PRE_SHA, "law doc is not at the banked stage-5B hash"
    block = BLOCK.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    marker = MARKER.encode("utf-8")
    i = pre.find(marker)
    assert i != -1 and pre.find(marker, i + 1) == -1, "section 6 marker not unique"
    post = pre[:i] + block + pre[i:]
    DOC.write_bytes(post)
    # verification from disk
    back = DOC.read_bytes()
    ok_shape = back == pre[:i] + block + pre[i:]
    ok_tail = back[i + len(block):] == pre[i:]
    ok_prefix = back[:i] == pre[:i]
    print("pre  sha256:", PRE_SHA)
    print("post sha256:", sha(back))
    print("inserted bytes:", len(block), "at offset", i)
    print("prefix byte-identical:", ok_prefix)
    print("tail byte-identical:", ok_tail)
    print("single contiguous insertion:", ok_shape)
    return 0 if (ok_shape and ok_tail and ok_prefix) else 1


if __name__ == "__main__":
    sys.exit(main())
