"""W1 SOURCE-BOUND REGENERATION VERIFIER (Astra decision MV-VALUE; M01-F1).

Authenticate a delivered `chimera.rigid_body_mass_export.v1` report beyond
diagnostic inspection: require the exact source manifest, partition and
authored groups; pin the exporter revision; recompute admission AND every
input hash with the PINNED producer's own code; regenerate the complete report
and compare it to the delivered artifact under the exporter's OWN documented
identity rule (its canonical JSON serialization).

Verdicts (mutually exclusive, priority order):
  UNAVAILABLE-SOURCE  missing/unusable source triple, missing delivered report,
                      unresolvable revision pin, or pinned producer modules
                      absent/underivable at that pin. Verification is
                      UNAVAILABLE — this is never an acceptance, never a pass.
  PRODUCER-ERROR      the pinned producer itself failed to regenerate a
                      parseable report. Not a pass; not blamed on the report.
  MISMATCH            verification ran and at least one frozen check failed;
                      every differing JSON path is itemized.
  VERIFIED            every input hash recomputed and matching; admission
                      recomputed and matching; the complete report regenerated
                      by the pinned producer and equal under the exporter's
                      canonical identity. The output STILL carries the caveat:
                      regeneration proves agreement with the producer, not
                      correctness of the physical inputs or producer.

Identity layers (B4 law): comparisons use ONLY the exporter's canonical JSON
layer (sha256 over `json.dumps(report, sort_keys=True, separators=(",", ":"),
ensure_ascii=True, allow_nan=False) + "\\n"`, ASCII). Disk/materialized bytes
and git blob bytes are never used as verification identity; blob bytes are used
only to materialize and byte-verify the pinned producer's code.

Exit codes: 0 VERIFIED · 1 MISMATCH · 2 UNAVAILABLE-SOURCE · 3 PRODUCER-ERROR ·
4 usage/internal error.

Run:
    python material_volume_source_verify.py --report REPORT.json \\
        --manifest M.json --partition P.json --groups G.json \\
        --revision 1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

W1_DIR = Path(__file__).resolve().parent
RUNNER = W1_DIR / "pinned_runner.py"
PINNED_MODULES = ("material_volume.py",
                  "material_volume_admission.py",
                  "material_volume_body_export.py")

CAVEAT = ("Regeneration proves agreement with the producer, not correctness of "
          "the physical inputs or producer.")
INDEPENDENT_CHECKS_NOTE = (
    "Independent analytic checks are retained: the legacy suites, proof "
    "batteries, and admission/compiler refusals remain the correctness layer "
    "for the physical inputs and the producer; this verifier adds source-bound "
    "producer agreement only.")
IDENTITY = {
    "report_identity_layer":
        "exporter canonical JSON: sha256 over json.dumps(report, sort_keys=True, "
        "separators=(',',':'), ensure_ascii=True, allow_nan=False) + newline "
        "(ASCII). NOT disk bytes, NOT git blob bytes.",
    "input_hash_definition":
        "exporter._hashes / exporter._canonical_hash: sha256 of UTF-8 canonical "
        "JSON (sorted object keys; array order preserved), computed by the "
        "pinned revision's own code.",
    "producer_materialization_layer":
        "git blob bytes (LF) at the pinned revision via git cat-file, "
        "byte-verified with git hash-object against git ls-tree OIDs; disk and "
        "git-archive forms are checkout materializations (B4 law).",
}
HASH_KEYS = ("manifest_sha256", "partition_sha256", "body_groups_sha256")

EXIT = {"VERIFIED": 0, "MISMATCH": 1, "UNAVAILABLE-SOURCE": 2,
        "PRODUCER-ERROR": 3}


def _base(verdict: str) -> dict:
    return {"verifier": "W1 source-bound regeneration verification "
                        "(Astra decision MV-VALUE; battery decision M01-F1)",
            "verdict": verdict,
            "caveat": CAVEAT,
            "independent_checks_note": INDEPENDENT_CHECKS_NOTE,
            "identity": IDENTITY,
            "checks": [],
            "mismatches": []}


def _check(checks: list, name: str, passed: bool, detail: str) -> bool:
    checks.append({"name": name, "status": "pass" if passed else "FAIL",
                   "detail": detail})
    return passed


def _git(repo: str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True,
                          check=check)


def _resolve_pin(args, unavailable: dict) -> str | None:
    repo = args.repo
    if not repo:
        try:
            proc = _git(str(W1_DIR), "rev-parse", "--show-toplevel")
            repo = proc.stdout.decode("utf-8", "replace").strip()
        except (OSError, subprocess.CalledProcessError):
            unavailable["detail"] = "cannot resolve a git repository root"
            return None
        args.repo = repo
    try:
        proc = _git(repo, "rev-parse", "--verify", args.revision)
        full = proc.stdout.decode("ascii", "replace").strip()
        if not full:
            raise subprocess.CalledProcessError(1, "rev-parse")
        return full
    except (OSError, subprocess.CalledProcessError) as error:
        unavailable["detail"] = (f"revision pin {args.revision!r} does not "
                                 f"resolve in repo {repo!r}: {error!r}")
        return None


def _materialize(repo: str, full_rev: str, work_dir: Path,
                 unavailable: dict) -> str | None:
    """Extract the pinned producer's modules from git blob bytes and
    byte-verify each against the ls-tree OID. Any failure is UNAVAILABLE-SOURCE
    (the pinned producer's source material is not available)."""
    try:
        ls = _git(repo, "ls-tree", "-r", full_rev, "tools/")
        oids = {}
        for line in ls.stdout.decode("ascii", "replace").splitlines():
            meta, path = line.split("\t", 1)
            oids[path] = meta.split()[2]
        needed = {f"tools/{name}": oids.get(f"tools/{name}")
                  for name in PINNED_MODULES}
        missing = [path for path, oid in needed.items() if not oid]
        if missing:
            unavailable["detail"] = (f"pinned revision {full_rev} lacks producer "
                                     f"modules: {missing}")
            return None
        target = work_dir / "tools"
        target.mkdir(parents=True, exist_ok=True)
        for path, oid in needed.items():
            blob = _git(repo, "cat-file", "blob", oid).stdout
            out = target / Path(path).name
            out.write_bytes(blob)
            actual = _git(repo, "hash-object", "--", str(out)).stdout
            actual = actual.decode("ascii", "replace").strip()
            if actual != oid:
                unavailable["detail"] = (f"blob extraction byte-verification "
                                         f"failed for {path}: ls-tree {oid} != "
                                         f"hash-object {actual}")
                return None
        return str(target)
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        unavailable["detail"] = f"blob materialization failed: {error!r}"
        return None


def _diff_paths(a, b, prefix="", limit=20):
    diffs, truncated = [], False
    if type(a) is not type(b) and not (isinstance(a, (int, float))
                                      and isinstance(b, (int, float))
                                      and not isinstance(a, bool)
                                      and not isinstance(b, bool)):
        return [prefix or "$"], False
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                diffs.append(f"{prefix}.{key}" if prefix else f"${key}")
            else:
                sub, trunc = _diff_paths(a[key], b[key],
                                         f"{prefix}.{key}" if prefix else f"${key}",
                                         limit)
                diffs.extend(sub)
                truncated = truncated or trunc
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f"{prefix}[len={len(a)}!={len(b)}]")
        for i in range(min(len(a), len(b))):
            sub, trunc = _diff_paths(a[i], b[i], f"{prefix}[{i}]", limit)
            diffs.extend(sub)
            truncated = truncated or trunc
    elif a != b:
        diffs.append(prefix or "$")
    if len(diffs) > limit:
        return diffs[:limit], True
    return diffs, truncated


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--partition", required=True)
    parser.add_argument("--groups", required=True)
    parser.add_argument("--revision", required=True,
                        help="exporter revision pin (never altered)")
    parser.add_argument("--repo", default=None, help="repo root (default: "
                        "auto-discover from this file's location)")
    parser.add_argument("--work-dir", default=None, help="pinned materialization "
                        "root (default: <this dir>/work/pinned/<rev>)")
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--max-paths", type=int, default=20)
    args = parser.parse_args(argv)
    # Resolve caller paths to ABSOLUTE before any subprocess: the pinned
    # runner executes with a different cwd (the materialization root), so a
    # relative path from the caller would not resolve there.
    for field in ("report", "manifest", "partition", "groups",
                  "output_json", "work_dir", "repo"):
        value = getattr(args, field, None)
        if value is not None:
            setattr(args, field, str(Path(value).resolve()))

    def finish(verdict: str, extra: dict) -> int:
        out = _base(verdict)
        out.update(extra)
        text = json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True,
                          allow_nan=False) + "\n"
        sys.stdout.write(text)
        if args.output_json:
            Path(args.output_json).write_text(text, encoding="utf-8",
                                              newline="\n")
        return EXIT[verdict]

    sources = {"manifest": args.manifest, "partition": args.partition,
               "groups": args.groups, "report": args.report}
    missing = [label for label, path in sources.items()
               if not os.path.isfile(path)]
    if missing:
        return finish("UNAVAILABLE-SOURCE", {
            "detail": f"missing source material (verification unavailable, "
                      f"never accepted): {missing}",
            "producer_revision_pin": args.revision, "sources": sources})

    unavailable = {}
    full_rev = _resolve_pin(args, unavailable)
    if full_rev is None:
        return finish("UNAVAILABLE-SOURCE", {
            "detail": unavailable["detail"],
            "producer_revision_pin": args.revision, "sources": sources})

    work_dir = (Path(args.work_dir) if args.work_dir
                else W1_DIR / "work" / "pinned" / full_rev[:12])
    pinned_tools = _materialize(args.repo, full_rev, work_dir, unavailable)
    if pinned_tools is None:
        return finish("UNAVAILABLE-SOURCE", {
            "detail": unavailable["detail"],
            "producer_revision_pin": args.revision,
            "producer_revision_resolved": full_rev, "sources": sources})

    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        proc = subprocess.run(
            [sys.executable, str(RUNNER), pinned_tools,
             args.manifest, args.partition, args.groups, args.report],
            cwd=str(work_dir), capture_output=True, env=env, timeout=600)
    except (OSError, subprocess.TimeoutExpired) as error:
        return finish("PRODUCER-ERROR", {
            "detail": f"pinned runner could not execute: {error!r}",
            "producer_revision_resolved": full_rev, "sources": sources})
    try:
        result = json.loads(proc.stdout.decode("utf-8", "replace"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        result = None
    if result is None or result.get("status") == "producer_error" \
            or proc.returncode not in (0,):
        detail = (result.get("detail", "") if isinstance(result, dict) else "")
        tail = (proc.stderr or b"").decode("utf-8", "replace")[-800:]
        return finish("PRODUCER-ERROR", {
            "detail": f"pinned producer failed to regenerate a parseable "
                      f"report: {detail}; runner exit {proc.returncode}; "
                      f"stderr tail: {tail}",
            "producer_revision_resolved": full_rev, "sources": sources})
    if result.get("status") == "source_unusable":
        return finish("UNAVAILABLE-SOURCE", {
            "detail": f"source material unusable by the pinned producer's own "
                      f"strict reader: {result.get('reason')}: "
                      f"{result.get('detail')} (verification unavailable, "
                      f"never accepted)",
            "producer_revision_resolved": full_rev, "sources": sources})

    # ---- structured comparison (hashes above came from the pinned code) ----
    checks: list = []
    mismatches: list = []
    delivered_present = result.get("delivered_canonical_json") is not None
    if not delivered_present:
        parse_error = result.get("delivered_parse_error", {})
        _check(checks, "delivered_report_parse", False,
               f"the delivered artifact has no canonical identity under the "
               f"pinned strict reader: {parse_error.get('reason')}: "
               f"{parse_error.get('detail')}")
        mismatches.append("delivered_report_parse")
    else:
        _check(checks, "delivered_report_parse", True,
               "delivered artifact parses under the pinned strict reader "
               "(duplicate-key / NaN-literal rejecting)")

    recomputed = result["input_hashes_recomputed"]
    try:
        delivered_report = json.loads(result["delivered_canonical_json"] or "null")
    except json.JSONDecodeError:
        delivered_report = None
    delivered_hashes = (delivered_report or {}).get("input_hashes") \
        if isinstance(delivered_report, dict) else None
    for key in HASH_KEYS:
        recomputed_value = recomputed.get(key)
        if not delivered_present or not isinstance(delivered_hashes, dict):
            detail = f"delivered report unavailable for comparison; recomputed {key}={recomputed_value}"
            _check(checks, f"input_hash_{key}", False, detail)
            mismatches.append(f"input_hashes.{key}")
            continue
        delivered_value = delivered_hashes.get(key)
        passed = _check(checks, f"input_hash_{key}",
                        delivered_value == recomputed_value,
                        f"delivered {delivered_value} vs recomputed from the "
                        f"supplied source {recomputed_value}")
        if not passed:
            mismatches.append(f"input_hashes.{key}")
    if isinstance(delivered_hashes, dict):
        for field in ("algorithm", "serialization"):
            delivered_field = delivered_hashes.get(field)
            passed = _check(checks, f"input_hashes_declaration_{field}",
                            delivered_field == recomputed.get(field),
                            f"delivered {delivered_field!r} vs pinned producer "
                            f"declaration {recomputed.get(field)!r}")
            if not passed:
                mismatches.append(f"input_hashes.{field}")

    delivered_admission = (delivered_report or {}).get("admission_report_sha256") \
        if isinstance(delivered_report, dict) else None
    recomputed_admission = result["admission_report_sha256_recomputed"]
    passed = _check(checks, "admission_report_sha256_recomputed",
                    delivered_admission == recomputed_admission,
                    f"delivered {delivered_admission} vs recomputed from the "
                    f"supplied manifest+partition {recomputed_admission}")
    if not passed:
        mismatches.append("admission_report_sha256")

    diff_truncated = False
    if delivered_present:
        same_identity = (result["delivered_canonical_json"]
                         == result["regenerated_canonical_json"])
        _check(checks, "report_canonical_identity", same_identity,
               f"delivered canonical sha256 {result['delivered_canonical_sha256']} "
               f"vs pinned regeneration canonical sha256 "
               f"{result['regenerated_canonical_sha256']} (exporter canonical "
               f"JSON layer; raw file bytes are not identity)")
        if not same_identity:
            mismatches.append("$report")
            diffs, diff_truncated = _diff_paths(
                delivered_report,
                json.loads(result["regenerated_canonical_json"]),
                limit=args.max_paths)
            mismatches.extend(f"{path}" for path in diffs)

    verdict = "MISMATCH" if mismatches else "VERIFIED"
    return finish(verdict, {
        "producer_revision_pin": args.revision,
        "producer_revision_resolved": full_rev,
        "pinned_materialization": {"tools_dir": pinned_tools,
                                   "layer": "git blob bytes (LF), "
                                            "hash-object verified"},
        "sources": {**sources,
                    "materialized_receipts":
                        result.get("source_materialized_receipts", [])},
        "delivered_export_status": result.get("delivered_export_status"),
        "delivered_admission_status": result.get("delivered_admission_status"),
        "regenerated_export_status": result.get("regenerated_export_status"),
        "regenerated_admission_status": result.get("regenerated_admission_status"),
        "admission_decision_recomputed": result.get("admission_decision_recomputed"),
        "checks": checks,
        "mismatches": mismatches,
        "mismatches_truncated": diff_truncated,
    })


if __name__ == "__main__":
    raise SystemExit(main())
