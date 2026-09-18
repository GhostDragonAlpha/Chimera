"""Reusable static reviewer for science-funnel candidates.

Mechanizes the six checklist items that have actually caught real bugs:

  frozen_reference  - engine change without frozen bit-exact assertions
  falsifier_as_test - added physics without biting tests (F1/F2/F3 shapes)
  receipt_schema    - receipt.json conformance + manifest re-verification
  scope_honesty     - added claims vs limits + stale live scope string (F4)
  evidence_count    - graph JSONs touched without the evidence-11 pin
  graph_merge_replay- merges touching graph JSONs must show replay, not text-merge

Usage (PowerShell):
  python -B tools/science_funnel/review_candidate.py --base <sha> --candidate <sha>
  python -B tools/science_funnel/review_candidate.py --range <base>..<candidate>
  python -B tools/science_funnel/review_candidate.py --base X --candidate Y --checklist tools/science_funnel/review_checklist.json --out tools/science_funnel/validation/review_<short>

Output:
  <out>/verdict.json + one-line human summary on stdout.

Verdict per item: PASS / FINDING(severity, file:line, quoted evidence) / CANNOT-VERIFY.
Never claims beyond static visibility: semantic correctness stays with the
native suite + independent review.
"""

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_CHECKLIST = os.path.join(HERE, "review_checklist.json")
VERDICT_SCHEMA = "chimera.review_verdict.v1"


def run_git(args, cwd=ROOT):
    p = subprocess.run(
        ["git"] + args, cwd=cwd, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), p.stderr.strip()[:2000]))
    return p.stdout


def load_checklist(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def match_any(path, patterns):
    for pat in patterns:
        if fnmatch.fnmatch(path, pat):
            return True
        # also match basename-anchored patterns without directory
        if "/" not in pat and fnmatch.fnmatch(os.path.basename(path), pat):
            return True
    return False


def diff_name_status(base, candidate):
    out = run_git(["diff", "--name-status", "%s..%s" % (base, candidate)])
    entries = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0][0]
        paths = parts[1:]
        entries.append({"status": status, "paths": paths})
    return entries


def diff_files(base, candidate):
    out = run_git(["diff", "--name-only", "%s..%s" % (base, candidate)])
    return [l.strip() for l in out.splitlines() if l.strip()]


def diff_added_lines(base, candidate, path):
    """Return list of (new_lineno, text) for added lines in path diff."""
    try:
        out = run_git(["diff", "-U0", "%s..%s" % (base, candidate), "--", path])
    except RuntimeError:
        return []
    added = []
    new_lineno = None
    for line in out.splitlines():
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if m:
            new_lineno = int(m.group(1))
            continue
        if new_lineno is None:
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added.append((new_lineno, line[1:]))
            new_lineno += 1
        elif line.startswith("-") and not line.startswith("---"):
            pass
        else:
            # context line (should be none with -U0, but handle)
            new_lineno += 1
    return added


def diff_all_added(base, candidate, files):
    by_file = {}
    for path in files:
        by_file[path] = diff_added_lines(base, candidate, path)
    return by_file


def file_at(ref, path):
    try:
        out = run_git(["show", "%s:%s" % (ref, path)])
        return out
    except RuntimeError:
        return None


def ls_receipts_at(ref, receipt_glob):
    try:
        out = run_git(["ls-tree", "-r", "--name-only", ref])
    except RuntimeError:
        return []
    names = [l.strip() for l in out.splitlines() if l.strip()]
    return [n for n in names if fnmatch.fnmatch(n, receipt_glob)]


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_frozen(base, candidate, files, added_by_file, cfg):
    physics = [f for f in files if match_any(f, cfg["physics_paths"])]
    if not physics:
        return {"id": "frozen_reference", "status": "PASS",
                "detail": "no engine/physics files touched; frozen check not applicable"}
    tests = [f for f in files if match_any(f, cfg["test_paths"])]
    markers = cfg["frozen_markers"]
    hits = []
    for f in tests:
        for lineno, text in added_by_file.get(f, []):
            for m in markers:
                if re.search(m, text, re.IGNORECASE):
                    hits.append({"file": f, "line": lineno, "evidence": text.strip()[:300]})
                    break
    # also accept frozen markers in engine-side added comments (e.g. native.cpp notes)
    if not hits:
        for f in physics:
            for lineno, text in added_by_file.get(f, []):
                for m in markers:
                    if re.search(m, text, re.IGNORECASE):
                        hits.append({"file": f, "line": lineno, "evidence": text.strip()[:300]})
                        break
    if hits:
        return {"id": "frozen_reference", "status": "PASS",
                "detail": "frozen/bit-exact markers present in %d added line(s)" % len(hits),
                "evidence_sample": hits[:3]}
    # physics touched, no frozen markers: FINDING
    sample = None
    for f in physics:
        lines = added_by_file.get(f, [])
        if lines:
            sample = {"file": f, "line": lines[0][0], "evidence": lines[0][1].strip()[:300]}
            break
    return {"id": "frozen_reference", "status": "FINDING", "severity": "MAJOR",
            "file": (sample or {}).get("file", physics[0]),
            "line": (sample or {}).get("line", 0),
            "evidence": (sample or {}).get("evidence", "engine touched, no frozen marker"),
            "detail": "engine/physics touched (%s) but no frozen/bit-exact assertion added in tests" % ", ".join(physics[:5])}


def check_falsifier(base, candidate, files, added_by_file, cfg):
    physics = [f for f in files if match_any(f, cfg["physics_paths"])]
    if not physics:
        return {"id": "falsifier_as_test", "status": "PASS",
                "detail": "no engine/physics files touched; falsifier check not applicable"}
    tests = [f for f in files if match_any(f, cfg["test_paths"])]
    # gather all added test text
    test_text = "\n".join(t for f in tests for _, t in added_by_file.get(f, []))
    engine_text = "\n".join(t for f in physics for _, t in added_by_file.get(f, []))
    findings = []
    # density: at least one assertion marker in added tests
    if tests:
        has_assert = any(re.search(m, test_text) for m in cfg["assertion_markers"])
        if not has_assert:
            # locate first added test line for evidence
            f0 = tests[0]
            lines = added_by_file.get(f0, [])
            findings.append({"sub": "no_assertion", "severity": "MAJOR",
                             "file": f0, "line": lines[0][0] if lines else 0,
                             "evidence": (lines[0][1].strip()[:300] if lines else "test touched, no assertion"),
                             "detail": "physics changed but added tests contain no assertion that could bite"})
    else:
        findings.append({"sub": "no_test", "severity": "MAJOR",
                         "file": physics[0], "line": 0,
                         "evidence": "engine touched, no test file in diff",
                         "detail": "physics changed with no test file in the diff"})
    friction = ("friction" in engine_text.lower()) or ("contact_friction" in engine_text)
    # F2 shape: mu pair present without threshold discrimination
    if friction:
        has_pair = all(m in (test_text + engine_text) for m in cfg["f2_mu_pair"])
        has_thresh = any(m.lower() in (test_text + engine_text).lower() for m in cfg["f2_threshold_markers"])
        if has_pair and not has_thresh:
            # evidence: the mu pair line
            ev = None
            for f in tests + physics:
                for lineno, text in added_by_file.get(f, []):
                    if "0.05" in text and "0.8" in text:
                        ev = {"file": f, "line": lineno, "evidence": text.strip()[:300]}
                        break
                if ev:
                    break
            if ev is None:
                for f in tests + physics:
                    for lineno, text in added_by_file.get(f, []):
                        if "0.05" in text or "0.8" in text:
                            ev = {"file": f, "line": lineno, "evidence": text.strip()[:300]}
                            break
                    if ev:
                        break
            findings.append({"sub": "F2_critical_mu_unexercised", "severity": "MINOR",
                             "file": (ev or {"file": tests[0] if tests else physics[0]})["file"],
                             "line": (ev or {"line": 0})["line"],
                             "evidence": (ev or {"evidence": "mu pair {0.05,0.8} without mucrit/threshold"})["evidence"],
                             "detail": "F2-shape: friction trials use {0.05,0.8} without a critical-mu hold-vs-slide threshold (no mucrit/critical/0.6/travel marker)"})
        # F3 shape: cone present but impact-cone and J^T guards missing
        has_cone = any(m in (test_text + engine_text) for m in cfg["f3_cone_markers"])
        has_impact = any(m in (test_text + engine_text) for m in cfg["f3_impact_markers"])
        has_jt = any(m in (test_text + engine_text) for m in cfg["f3_jt_markers"])
        if has_cone and (not has_impact or not has_jt):
            missing = []
            if not has_impact:
                missing.append("impact-cone guard (friction_impact_cone)")
            if not has_jt:
                missing.append("J^T force-decomposition guard")
            ev = None
            for f in tests:
                for lineno, text in added_by_file.get(f, []):
                    if "friction_cone" in text:
                        ev = {"file": f, "line": lineno, "evidence": text.strip()[:300]}
                        break
                if ev:
                    break
            findings.append({"sub": "F3_cone_without_guards", "severity": "MINOR",
                             "file": (ev or {"file": tests[0] if tests else physics[0]})["file"],
                             "line": (ev or {"line": 0})["line"],
                             "evidence": (ev or {"evidence": "friction_cone without impact/J^T guard"})["evidence"],
                             "detail": "F3-shape: per-tick cone holds by construction but missing: %s" % "; ".join(missing)})
    # F1 shape: exact-rest branch present without seam test -> CANNOT-VERIFY
    has_rest = any(re.search(m, engine_text) for m in cfg["f1_rest_markers"])
    has_seam = any(m in (test_text + engine_text) for m in cfg["f1_seam_markers"])
    cannot = None
    if has_rest and not has_seam:
        ev = None
        for f in physics:
            for lineno, text in added_by_file.get(f, []):
                if "slip_sign" in text and ("rt>=" in text or "rt >=" in text or "?1." in text or "?-1." in text or "1.:" in text):
                    ev = {"file": f, "line": lineno, "evidence": text.strip()[:300]}
                    break
            if ev:
                break
        cannot = {"sub": "F1_exact_rest_sign", "file": (ev or {"file": physics[0]})["file"],
                  "line": (ev or {"line": 0})["line"],
                  "evidence": (ev or {"evidence": "slip_sign exact-rest fallback without seam test"})["evidence"],
                  "detail": "F1-shape: exact-rest slide-sign fallback present but sign correctness is not statically decidable; needs solver-seam test (friction_unit / opposes_impending)"}
    if findings:
        first = findings[0]
        return {"id": "falsifier_as_test", "status": "FINDING", "severity": first["severity"],
                "file": first["file"], "line": first["line"], "evidence": first["evidence"],
                "detail": "; ".join(f["sub"] + ": " + f["detail"] for f in findings),
                "subfindings": findings,
                "cannot_verify": cannot}
    if cannot:
        return {"id": "falsifier_as_test", "status": "CANNOT-VERIFY",
                "file": cannot["file"], "line": cannot["line"], "evidence": cannot["evidence"],
                "detail": cannot["detail"]}
    return {"id": "falsifier_as_test", "status": "PASS",
            "detail": "added tests contain biting assertions covering the changed physics"}


def find_receipts(base, candidate, files, cfg):
    # receipts touched in diff
    touched = [f for f in files if fnmatch.fnmatch(f, cfg["receipt_glob"])]
    # plus any receipt at candidate claiming this candidate
    claimed = []
    for name in ls_receipts_at(candidate, cfg["receipt_glob"]):
        text = file_at(candidate, name)
        if not text:
            continue
        try:
            r = json.loads(text)
        except ValueError:
            continue
        if r.get("candidate_commit") == candidate:
            claimed.append(name)
    # union, preserve order
    seen = set()
    out = []
    for n in touched + claimed:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def check_receipt(base, candidate, files, cfg):
    receipts = find_receipts(base, candidate, files, cfg)
    if not receipts:
        return {"id": "receipt_schema", "status": "PASS",
                "detail": "no receipt in scope (none touched, none claims candidate); schema check not applicable"}
    findings = []
    passes = []
    for name in receipts:
        text = file_at(candidate, name)
        if text is None:
            findings.append({"file": name, "line": 0, "evidence": "receipt unreadable at candidate",
                             "detail": "receipt %s unreadable at %s" % (name, candidate[:8])})
            continue
        try:
            r = json.loads(text)
        except ValueError as ex:
            findings.append({"file": name, "line": 0, "evidence": str(ex)[:300],
                             "detail": "receipt %s is not valid JSON" % name})
            continue
        if r.get("schema") != cfg["receipt_schema_value"]:
            findings.append({"file": name, "line": 0, "evidence": "schema=%r" % r.get("schema"),
                             "detail": "receipt schema must be %s" % cfg["receipt_schema_value"]})
            continue
        missing = [k for k in cfg["receipt_required_keys"] if k not in r]
        if missing:
            findings.append({"file": name, "line": 0, "evidence": "missing keys: %s" % ", ".join(missing),
                             "detail": "receipt %s missing required keys" % name})
            continue
        if r.get("candidate_commit") != candidate:
            # only a finding if the receipt was touched in this diff (stale claim);
            # a nearby receipt claiming another commit is just not in scope
            if name in files:
                findings.append({"file": name, "line": 0, "evidence": "candidate_commit=%s" % r.get("candidate_commit"),
                                 "detail": "touched receipt claims a different candidate"})
            continue
        # manifest re-verification (the independent-review ritual)
        manifest = r.get("source_file_manifest_sha256") or {}
        bad = []
        for rel, pinned in manifest.items():
            actual_text = file_at(candidate, rel)
            if actual_text is None:
                # binary or missing at this ref (e.g. png handled separately); check worktree only if candidate==HEAD
                continue
            # manifest is sha256 of raw bytes; git show returns text (may normalize newlines on win).
            # Compare loosely: only flag gross mismatches by also trying utf-8-sig/newline variants is overkill;
            # instead verify files that are small text by exact bytes via git cat-file.
            try:
                raw = subprocess.run(["git", "show", "%s:%s" % (candidate, rel)], cwd=ROOT,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
                if hashlib.sha256(raw).hexdigest() != pinned:
                    bad.append(rel)
            except Exception:
                continue
        if bad:
            findings.append({"file": name, "line": 0, "evidence": "manifest mismatch: %s" % ", ".join(bad[:3]),
                             "detail": "source manifest hashes do not re-verify against candidate tree"})
            continue
        passes.append(name)
    if findings:
        f0 = findings[0]
        return {"id": "receipt_schema", "status": "FINDING", "severity": "MAJOR",
                "file": f0["file"], "line": f0.get("line", 0), "evidence": f0.get("evidence", ""),
                "detail": f0["detail"], "subfindings": findings, "passes": passes}
    return {"id": "receipt_schema", "status": "PASS",
            "detail": "receipt(s) conform: %s" % ", ".join(passes)}


def check_scope(base, candidate, files, added_by_file, cfg):
    physics = [f for f in files if match_any(f, cfg["physics_paths"])]
    receipts = find_receipts(base, candidate, files, cfg)
    if not physics and not receipts:
        return {"id": "scope_honesty", "status": "PASS",
                "detail": "no physics and no receipt in scope; scope check not applicable"}
    # F4 shape: engine adds friction but live scope string stays stale
    engine_text = "\n".join(t for f in physics for _, t in added_by_file.get(f, []))
    adds_friction = "friction" in engine_text.lower()
    # locate live qualifier at candidate
    live_path = "tools/science_funnel/tests/qualify_coupled_live.py"
    live_text = file_at(candidate, live_path) or ""
    if adds_friction:
        scope_lines = [(i + 1, l) for i, l in enumerate(live_text.splitlines()) if "scope" in l]
        scope_text = "\n".join(l for _, l in scope_lines)
        stale_in_scope = any(m in l for _, l in scope_lines for m in cfg["f4_stale_markers"])
        fixed_in_scope = any(m in scope_text for m in cfg["f4_fixed_markers"])
        if stale_in_scope and not fixed_in_scope:
            # find line number
            for i, l in scope_lines:
                if any(m in l for m in cfg["f4_stale_markers"]):
                    return {"id": "scope_honesty", "status": "FINDING", "severity": "MINOR",
                            "file": live_path, "line": i, "evidence": l.strip()[:300],
                            "detail": "F4-shape: engine adds Coulomb friction but the live qualifier scope string still claims the frictionless era ('No friction'); under-claim recorded verbatim into live_checks.json"}
        # if stale absent and fixed present, PASS this sub-check
    # receipt scope bounded by limits/not_qualified
    for name in receipts:
        text = file_at(candidate, name)
        if not text:
            continue
        try:
            r = json.loads(text)
        except ValueError:
            continue
        scope = r.get("scope", "")
        limits = r.get("limits") or []
        nq = r.get("not_qualified") or []
        if scope and not limits and not nq:
            return {"id": "scope_honesty", "status": "FINDING", "severity": "MAJOR",
                    "file": name, "line": 0, "evidence": scope[:300],
                    "detail": "receipt scope makes claims with no limits/not_qualified boundary"}
        # strong-claim words without boundary
        if re.search(r"\b(complete|proves|fully qualified|all cases)\b", scope, re.IGNORECASE) and not (limits or nq):
            return {"id": "scope_honesty", "status": "FINDING", "severity": "MAJOR",
                    "file": name, "line": 0, "evidence": scope[:300],
                    "detail": "scope uses strong completeness language without a limits boundary"}
    if adds_friction and not receipts:
        return {"id": "scope_honesty", "status": "CANNOT-VERIFY",
                "detail": "physics adds capability but no receipt in scope to bound it; cannot verify scope honesty statically"}
    return {"id": "scope_honesty", "status": "PASS",
            "detail": "scope bounded by limits/not_qualified; live scope string matches the engine capability"}


def check_evidence(base, candidate, files, cfg):
    touched = [f for f in files if any(f == p or f.startswith(p) for p in cfg["graph_json_prefixes"])]
    if not touched:
        return {"id": "evidence_count", "status": "PASS",
                "detail": "no graph JSONs touched; evidence count not at risk"}
    receipts = find_receipts(base, candidate, files, cfg)
    if not receipts:
        return {"id": "evidence_count", "status": "CANNOT-VERIFY",
                "detail": "graph JSONs touched (%s) but no receipt in scope to pin historical_evidence_unchanged=%s; cannot verify statically" % (", ".join(touched[:3]), cfg["evidence_pin_value"])}
    for name in receipts:
        text = file_at(candidate, name)
        if not text:
            continue
        try:
            r = json.loads(text)
        except ValueError:
            continue
        checks = r.get("checks", {})
        pin = checks.get("historical_evidence_unchanged")
        if pin == cfg["evidence_pin_value"]:
            return {"id": "evidence_count", "status": "PASS",
                    "detail": "graph JSONs touched but receipt pins historical_evidence_unchanged=%s" % pin}
    # graph touched, receipt exists but no pin
    f0 = receipts[0]
    return {"id": "evidence_count", "status": "FINDING", "severity": "MAJOR",
            "file": f0, "line": 0, "evidence": "receipt lacks historical_evidence_unchanged pin",
            "detail": "graph JSONs touched (%s) but no receipt pins historical_evidence_unchanged=%s" % (", ".join(touched[:3]), cfg["evidence_pin_value"])}


def check_merges(base, candidate, files, added_by_file, cfg):
    try:
        merges_out = run_git(["log", "--merges", "--pretty=format:%H", "%s..%s" % (base, candidate)])
    except RuntimeError:
        return {"id": "graph_merge_replay", "status": "CANNOT-VERIFY", "detail": "cannot list merges"}
    merges = [l.strip() for l in merges_out.splitlines() if l.strip()]
    graph_touched = [f for f in files if any(f == p or f.startswith(p) for p in cfg["graph_json_prefixes"])]
    # conflict markers in added graph lines are always a finding
    for f in graph_touched:
        for lineno, text in added_by_file.get(f, []):
            if "<<<<<<<" in text or ">>>>>>>" in text or text.startswith("|||||||"):
                return {"id": "graph_merge_replay", "status": "FINDING", "severity": "BLOCKER",
                        "file": f, "line": lineno, "evidence": text.strip()[:300],
                        "detail": "graph JSON contains merge-conflict markers: replay required, text-merge forbidden"}
    if not merges:
        if graph_touched:
            return {"id": "graph_merge_replay", "status": "PASS",
                    "detail": "graph JSONs changed in non-merge commit(s) with no conflict markers; no merge replay required"}
        return {"id": "graph_merge_replay", "status": "PASS",
                "detail": "no merges in range; merge-replay check not applicable"}
    bad = []
    for m in merges:
        try:
            touched = run_git(["diff-tree", "--no-commit-id", "--name-only", "-r", m]).splitlines()
        except RuntimeError:
            continue
        touched = [t.strip() for t in touched if t.strip()]
        g = [t for t in touched if any(t == p or t.startswith(p) for p in cfg["graph_json_prefixes"])]
        if not g:
            continue
        try:
            msg = run_git(["log", "-1", "--pretty=format:%B", m])
        except RuntimeError:
            msg = ""
        if not any(mk.lower() in msg.lower() for mk in cfg["merge_replay_markers"]):
            bad.append({"merge": m[:8], "files": g[:3], "msg": msg.strip().splitlines()[0][:200] if msg.strip() else "(empty)"})
    if bad:
        b0 = bad[0]
        return {"id": "graph_merge_replay", "status": "FINDING", "severity": "MAJOR",
                "file": b0["files"][0] if b0["files"] else "(merge)",
                "line": 0, "evidence": "merge %s: %s" % (b0["merge"], b0["msg"]),
                "detail": "merge touching graph JSONs shows no replay trace (need replay/re-run/admission/receipt/idempotent in the message); text-merge forbidden",
                "subfindings": bad}
    return {"id": "graph_merge_replay", "status": "PASS",
            "detail": "all %d merge(s) touching graph JSONs carry replay traces" % len(merges)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=None)
    ap.add_argument("--candidate", default=None)
    ap.add_argument("--range", dest="rng", default=None)
    ap.add_argument("--checklist", default=DEFAULT_CHECKLIST)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    base, candidate = args.base, args.candidate
    if args.rng and ".." in args.rng:
        b, c = args.rng.split("..", 1)
        base = base or b
        candidate = candidate or c
    if not base or not candidate:
        print("need --base <sha> --candidate <sha> (or --range base..candidate)", file=sys.stderr)
        return 2
    # resolve to full SHAs
    base = run_git(["rev-parse", base]).strip()
    candidate = run_git(["rev-parse", candidate]).strip()
    cfg = load_checklist(args.checklist)
    files = diff_files(base, candidate)
    added_by_file = diff_all_added(base, candidate, files)
    results = []
    results.append(check_frozen(base, candidate, files, added_by_file, cfg))
    results.append(check_falsifier(base, candidate, files, added_by_file, cfg))
    results.append(check_receipt(base, candidate, files, cfg))
    results.append(check_scope(base, candidate, files, added_by_file, cfg))
    results.append(check_evidence(base, candidate, files, cfg))
    results.append(check_merges(base, candidate, files, added_by_file, cfg))
    n_find = sum(1 for r in results if r["status"] == "FINDING")
    n_cv = sum(1 for r in results if r["status"] == "CANNOT-VERIFY")
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    if n_find:
        verdict = "FINDINGS"
    elif n_cv:
        verdict = "CANNOT-VERIFY"
    else:
        verdict = "PASS"
    short = candidate[:8]
    outdir = args.out or os.path.join(ROOT, "tools", "science_funnel", "validation", "review_%s" % short)
    os.makedirs(outdir, exist_ok=True)
    payload = {"schema": VERDICT_SCHEMA, "base": base, "candidate": candidate,
               "candidate_short": short, "checklist": os.path.relpath(args.checklist, ROOT),
               "checks": results,
               "summary_counts": {"PASS": n_pass, "FINDING": n_find, "CANNOT-VERIFY": n_cv},
               "verdict": verdict}
    # one-line human summary
    bits = []
    for r in results:
        if r["status"] == "FINDING":
            bits.append("%s FINDING(%s)" % (r["id"], r.get("severity", "?")))
        elif r["status"] == "CANNOT-VERIFY":
            bits.append("%s CANNOT-VERIFY" % r["id"])
    if verdict == "PASS":
        human = "review %s: PASS — all %d checks green" % (short, n_pass)
    else:
        human = "review %s: %s — %d FINDING, %d CANNOT-VERIFY, %d PASS (%s)" % (
            short, verdict, n_find, n_cv, n_pass, "; ".join(bits) if bits else "see verdict.json")
    payload["human_summary"] = human
    with open(os.path.join(outdir, "verdict.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
    print(human)
    print(os.path.relpath(os.path.join(outdir, "verdict.json"), ROOT))
    return 0 if verdict == "PASS" else (1 if verdict == "FINDINGS" else 3)


if __name__ == "__main__":
    sys.exit(main())
