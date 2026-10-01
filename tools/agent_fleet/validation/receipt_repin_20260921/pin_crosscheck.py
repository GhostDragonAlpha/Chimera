"""pin_crosscheck: catch repair-lane x downstream-receipt pin collisions BEFORE merge.

Rehearsal-2 top risk #1: a repair lane rewrites data blobs (or the checkout
rules over them) on its own branch; downstream lanes' receipts pin those
paths' bytes as their own worktrees held them. The collision is git-invisible
(the receipts live on other branches) and text-clean (merges apply cleanly);
only the receipts' own hash checks catch it - after merge, in the funnel's
loud refusals. This tool moves the catch BEFORE the merge.

Method (pure git, no worktree state, deterministic):
  1. Scan every candidate receipt/deliverable/code file on --own for sha pins:
     JSON dicts with a repo-relative `path` + a 64-hex `*sha256*` value,
     plus 64-hex constants in .py resolved to their pinned file by a small
     assignment walk (NAME = parts / joined / with / slashes).
  2. A pin is LINEAGE-CONSISTENT if it matches the raw blob bytes OR the
     autocrlf=true smudged (LF->CRLF) bytes of its file on --own - i.e. some
     checkout flavor in which the lane's verification passed.
  3. The pin is then checked at --target under the TARGET's checkout
     semantics: the target root .gitattributes decides per path whether the
     checked-out bytes are the raw blob only (-text) or may be smudged.
  4. Verdicts:
       collision          verified on --own, fails at --target (THE class)
       stale_on_own       already fails on --own under every flavor (a pin the
                          repair lane itself is expected to fix - the manifest
                          entries the instance-3 repair restored are here)
       repinned_at_target the target copy of the same receipt carries a
                          repin_20260921 section superseding exactly this pin
       hold               consistent at both refs
     Delivered artifacts (books: files whose name carries neither `receipt`
     nor `manifest`) have their recorded shas classified `record` - historical
     provenance, never enforced - so the tool never demands hand-editing a
     deliverable.

Usage:
  python -B pin_crosscheck.py --own <ref> --target <ref> [--out report.json]

Determinism: the output is a pure function of the two refs (commit hashes in,
no clocks, sort_keys everywhere). Two runs on the same refs are byte-identical.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from fnmatch import fnmatchcase

HEX64 = re.compile(r"^[0-9a-f]{64}$")
SCAN_ROOTS = ("tools", "docs/evidence", "docs/research")
TEXT_EXT = (".json", ".py", ".md", ".txt")
MAX_BLOB = 8 << 20  # skip blobs over 8 MB


def git(*args, binary=False):
    r = subprocess.run(["git", *args], capture_output=True)
    if r.returncode != 0:
        raise SystemExit("git failed: %s\n%s" % (" ".join(args), r.stderr.decode("utf-8", "replace")))
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


def resolve(ref):
    return git("rev-parse", ref).strip()


def blob_sha_at(ref, path):
    """Blob sha of path at ref; None if missing; ('tree', sha) tuples never
    returned - directories are not files."""
    out = git("ls-tree", ref, "--", path).strip()
    if not out:
        return None
    meta = out.split()[0]
    if not meta.startswith("100"):
        return None
    return out.split()[2]


def list_candidates(ref):
    keep = []
    for p in git("ls-tree", "-r", "--name-only", ref, "--", *SCAN_ROOTS).splitlines():
        p = p.strip()
        if not p.endswith(TEXT_EXT):
            continue
        base = p.rsplit("/", 1)[-1]
        in_data = "/data/" in p
        named = ("receipt" in base or "manifest" in base or "PREREG" in base
                 or "prereg" in base or "RULE0" in base)
        if ("/validation/" in p or p.startswith("docs/research/")
                or p.startswith("docs/evidence/") or (in_data and named)):
            keep.append(p)
    return sorted(keep)


class BatchBlobs:
    """One `git cat-file --batch` session; promisor misses fetch in batches."""

    def __init__(self):
        self.p = subprocess.Popen(["git", "cat-file", "--batch"],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def get(self, sha):
        if sha is None:
            return None
        self.p.stdin.write((sha + "\n").encode())
        self.p.stdin.flush()
        header = self.p.stdout.readline().decode().strip()
        if header.endswith("missing"):
            return None
        size = int(header.rsplit(" ", 1)[1])
        data = self.p.stdout.read(size)
        self.p.stdout.read(1)
        return data

    def close(self):
        self.p.stdin.close()
        self.p.wait()


def smudge(data):
    """The autocrlf=true checkout transform for text (CR never doubles)."""
    return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


def is_binary(data):
    return b"\x00" in data[:8192]


def sha_of(data):
    return hashlib.sha256(data).hexdigest()


def parse_gitattributes(ref):
    if blob_sha_at(ref, ".gitattributes") is None:
        return []
    rules = []
    for ln in git("show", ref + ":.gitattributes").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        parts = ln.split()
        if len(parts) >= 2:
            rules.append((parts[0], parts[1:]))
    return rules


def text_free_at(rules, path):
    """True if a -text rule covers path at target (last matching rule wins)."""
    hit = []
    for pattern, r in rules:
        if fnmatchcase(path, pattern) or fnmatchcase(path.rsplit("/", 1)[-1], pattern):
            hit = r
    return "-text" in (hit or [])


def walk_json_pins(node, prefix="", enforced=False, in_repin=False):
    """(path, sha, key, enforced, from_repin) for dicts holding a path + sha.

    Enforced pins: dicts under `inputs_pinned`, data-manifest entries, and
    `new_sha256` values of repin sections. `old_sha256` values of repin
    sections are superseded-in-place (history, kept verbatim by design).
    Everything else (measured/results sections of receipts, books) is a
    record - historical provenance, never enforced.
    """
    if isinstance(node, dict):
        path = node.get("path")
        if isinstance(path, str):
            rp = (prefix + path) if (prefix and not path.startswith(("tools/", "docs/"))
                                     and not path.startswith("/")) else path
            if rp.startswith(("tools/", "docs/")):
                for k, v in node.items():
                    if (isinstance(v, str) and HEX64.match(v)
                            and (k == "sha256" or k.startswith("sha256") or k.endswith("sha256"))):
                        is_old_repin = (k == "old_sha256")
                        is_new_repin = (k == "new_sha256")
                        yield (rp, v, k,
                               enforced or is_new_repin or (in_repin and is_old_repin),
                               in_repin and is_old_repin)
        for k, v in node.items():
            yield from walk_json_pins(v, prefix,
                                      enforced or k == "inputs_pinned",
                                      in_repin or k == "re_pins")
    elif isinstance(node, list):
        for v in node:
            yield from walk_json_pins(v, prefix, enforced, in_repin)


def make_resolver(txt_norm, file_dir):
    """Resolve NAME constants and inline `a / b / c` exprs to repo paths.
    `__file__`-based bases (REPO/LANE) resolve from the .py file's own dir."""
    assigns = {}
    for m in re.finditer(r"^(\w+)\s*=\s*(.+)$", txt_norm, re.M):
        assigns[m.group(1)] = m.group(2).strip()

    def resolve_expr(expr, depth=0):
        if depth > 10 or expr is None:
            return None
        expr = expr.strip().rstrip(",").strip()
        if "__file__" in expr:
            cur = file_dir
            m = re.search(r"parents\[(\d+)\]", expr)
            up = int(m.group(1)) if m else 1
            for _ in range(up):
                cur = cur.rsplit("/", 1)[0] if "/" in cur else ""
            return cur.strip("/")
        parts = [p.strip().strip("\"'") for p in expr.split("/")]
        parts = [p for p in parts if p and p not in (".", "Path", "Path(", ")")]
        if not parts:
            return None
        out = []
        for p in parts:
            if re.fullmatch(r"[A-Z_][A-Z0-9_]*", p) and p in assigns:
                sub = resolve_expr(assigns[p], depth + 1)
                if sub is None:
                    return None
                out.append(sub)
            elif re.fullmatch(r"[A-Za-z0-9_.\-]+", p):
                out.append(p.strip("/"))
            else:
                return None
        joined = "/".join(out)
        return joined.strip("/") or None

    # var -> expr of sha256_file(...) assignments (book_on_disk = sha256_file(K_LANE / "x"))
    fileof = {}
    for m in re.finditer(r"(\w+)\s*=\s*sha256_file\(([^()]*)\)", txt_norm):
        fileof[m.group(1)] = m.group(2)
    # const -> resolved pinned path (book_on_disk == K_BOOK_SHA, sha256_file(MANIFEST) == MANIFEST_SHA)
    cmp_map = {}
    for left, const in re.findall(r"(\w+)\s*==\s*([A-Z_][A-Z0-9_]*)", txt_norm):
        if left in fileof and const not in cmp_map:
            cmp_map[const] = resolve_expr(fileof[left])
    for pathvar, const in re.findall(r"sha256_file\((\w+)\)\s*==\s*([A-Z_][A-Z0-9_]*)", txt_norm):
        if const not in cmp_map:
            cmp_map[const] = resolve_expr(pathvar)
    return assigns, resolve_expr, cmp_map


def extract_pins(path, ext, raw):
    """[(pin_path_or_None, sha, cls, key)] with cls: receipt|record|code."""
    base = path.rsplit("/", 1)[-1]
    file_dir = path.rsplit("/", 1)[0] if "/" in path else ""
    cls = ("receipt" if ("receipt" in base or "manifest" in base
                         or "PREREG" in base or "RULE0" in base)
           else "record")
    if ext == ".json":
        try:
            prefix = ""
            if "/data/" in path:
                d = path.rsplit("/", 1)[0]
                if base in ("sha256_manifest.json", "inventory.json",
                            "download_receipt.json", "acquisition_preregistration.json"):
                    prefix = d + "/"
            root_enforced = (base == "sha256_manifest.json")
            out = []
            for (p, s, k, enforced, from_repin) in walk_json_pins(
                    json.loads(raw.decode("utf-8")), prefix, root_enforced):
                bucket = "record" if (not enforced and cls != "code") else cls
                out.append((p, s, bucket, k, from_repin))
            return out
        except Exception:
            return []
    if ext == ".py":
        txt = raw.decode("utf-8", "replace")
        norm = re.sub(r"[\"']\s*/\s*[\"']", "/", txt)  # "a" / "b" -> a/b
        assigns, resolve_expr, cmp_map = make_resolver(norm, file_dir)
        out = []
        for m in re.finditer(r"[0-9a-f]{64}", norm):
            sha = m.group(0)
            line_start = norm.rfind("\n", 0, m.start()) + 1
            lhs = re.match(r"\s*(\w+)\s*=", norm[line_start:m.end()])
            pp = cmp_map.get(lhs.group(1)) if lhs else None
            if pp is None and lhs:
                pp = resolve_expr(assigns.get(lhs.group(1)))
            if pp and not pp.startswith(("tools/", "docs/")):
                pp = None
            out.append((pp, sha, "code", "constant", False))
        return out
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--own", required=True, help="the lane branch (ref) whose receipts are pinned")
    ap.add_argument("--target", required=True, help="the integration state (ref) to expect")
    ap.add_argument("--out", help="also write the JSON report here")
    a = ap.parse_args()

    own, target = resolve(a.own), resolve(a.target)
    rules_t = parse_gitattributes(target)
    files = list_candidates(own)
    own_blob = {p: blob_sha_at(own, p) for p in files}
    target_blob = {p: blob_sha_at(target, p) for p in files}

    batch = BatchBlobs()
    pins = []
    for p in files:
        raw = batch.get(own_blob[p])
        if raw is None or len(raw) > MAX_BLOB:
            continue
        pins.extend((p,) + t for t in extract_pins(p, "." + p.rsplit(".", 1)[-1], raw))
    pins = sorted(set(pins), key=repr)

    need = sorted({pp for (_, pp, _, _, _, _) in pins if pp})
    obytes, tbytes = {}, {}
    for pp in need:
        ob, tb = blob_sha_at(own, pp), blob_sha_at(target, pp)
        obytes[pp] = batch.get(ob) if ob else None
        tbytes[pp] = batch.get(tb) if tb else None
    treceipt_txt = {}
    for f in sorted({pin[0] for pin in pins}):
        if target_blob.get(f):
            treceipt_txt[f] = batch.get(target_blob[f])
    batch.close()

    repin_map = {}  # (target_receipt_file, old_sha) -> re-pinned path
    for f, txt in treceipt_txt.items():
        if not txt:
            continue
        try:
            d = json.loads(txt.decode("utf-8"))
        except Exception:
            continue
        for r in d.get("repin_20260921", {}).get("re_pins", []):
            if r.get("old_sha256"):
                repin_map[(f, r["old_sha256"])] = r.get("path")

    def repin_lookup(f, sha):
        """A code pin's re-pin lives in its lane's receipt.json, not in the .py."""
        if (f, sha) in repin_map:
            return repin_map[(f, sha)]
        if f.endswith(".py"):
            lane_receipt = f.rsplit("/", 1)[0] + "/receipt.json"
            return repin_map.get((lane_receipt, sha))
        return None

    def variants(data):
        if data is None:
            return set()
        if is_binary(data):
            return {sha_of(data)}
        return {sha_of(data), sha_of(smudge(data))}

    buckets = {k: [] for k in ("collisions", "repinned_at_target", "superseded_in_place",
                               "stale_on_own", "hold", "records", "unmoved_by_target",
                               "code_pins_unresolved", "unresolvable")}
    seen = set()
    for (f, pp, sha, cls, key, from_repin) in pins:
        kk = (f, pp or "", sha, cls, from_repin)
        if kk in seen:
            continue
        seen.add(kk)
        entry = {"receipt": f, "pin_class": cls, "pin_key": key,
                 "pinned_path": pp, "sha256": sha}
        if from_repin:
            entry["note"] = "superseded pre-repair pin, retained verbatim by the repin section"
            buckets["superseded_in_place"].append(entry)
            continue
        if pp is None:
            buckets["code_pins_unresolved" if cls == "code" else "unresolvable"].append(entry)
            continue
        if pp not in obytes or obytes[pp] is None:
            buckets["unresolvable"].append(entry)
            continue
        own_v = variants(obytes[pp])
        tgt = tbytes[pp]
        if cls not in ("receipt", "code"):
            entry["verdict_at_target"] = ("absent_at_target" if tgt is None else
                                          "hold" if sha in variants(tgt) else "moved")
            buckets["records"].append(entry)
            continue
        if tgt is None:
            # the target branch does not carry the pinned file at all: the
            # integration merge takes --own's bytes, so nothing collides here
            entry["verdict"] = "unmoved_by_target"
            buckets["unmoved_by_target"].append(entry)
            continue
        allowed_t = ({sha_of(tgt)} if (text_free_at(rules_t, pp) or is_binary(tgt))
                     else variants(tgt))
        if sha in allowed_t:
            entry["verdict"] = "hold"
            buckets["hold"].append(entry)
        elif repin_lookup(f, sha):
            entry["verdict"] = "repinned_at_target"
            entry["repinned_to_path"] = repin_lookup(f, sha)
            buckets["repinned_at_target"].append(entry)
        elif sha in own_v:
            entry["verdict"] = "collision"
            buckets["collisions"].append(entry)
        else:
            entry["verdict"] = "stale_on_own"
            buckets["stale_on_own"].append(entry)

    report = {
        "schema": "chimera.pin_crosscheck.v1",
        "own_arg": a.own, "target_arg": a.target,
        "own_ref": own, "target_ref": target,
        "files_scanned": len(files), "pins_scanned": len(seen),
        "collisions": buckets["collisions"],
        "repinned_at_target": buckets["repinned_at_target"],
        "superseded_in_place": buckets["superseded_in_place"],
        "stale_on_own": buckets["stale_on_own"],
        "hold": buckets["hold"],
        "records": buckets["records"],
        "unmoved_by_target": buckets["unmoved_by_target"],
        "code_pins_unresolved": buckets["code_pins_unresolved"],
        "unresolvable": buckets["unresolvable"][:10],
    }
    if len(buckets["unresolvable"]) > 10:
        report["unresolvable_truncated_count"] = len(buckets["unresolvable"]) - 10
    report["summary"] = {k: len(buckets[k]) for k in
                         ("collisions", "repinned_at_target", "superseded_in_place",
                          "stale_on_own", "hold", "records", "unmoved_by_target",
                          "code_pins_unresolved", "unresolvable")}
    out = json.dumps(report, indent=1, sort_keys=True) + "\n"
    if a.out:
        open(a.out, "wb").write(out.encode("utf-8"))
    sys.stdout.write(out)


if __name__ == "__main__":
    main()
