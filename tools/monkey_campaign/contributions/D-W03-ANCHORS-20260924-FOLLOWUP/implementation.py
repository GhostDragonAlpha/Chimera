"""implementation.py -- D-W03-ANCHORS-20260924-FOLLOWUP: versioned walking-anchor
certificate verifier.

Binds the W03 anchor chain identities from pinned evidence ALONE and decides
certificate completeness:

  source identities   commit + repo path + extraction convention (raw blob bytes,
                      or lf-to-crlf = the on-disk working-tree bytes the shutdown
                      registry hashed) per anchor;
  binary identities   v2 binaries are NOT_IN_GIT by design -> anchored to
                      source commit + build script (hash-verified); on-disk
                      binary hashes, when supplied, are verified and are the only
                      G2-closing evidence;
  input anchors       the 18 git-text anchors of anchor_manifest_v2.proposal;
  output receipts     git blobs or on-disk files, each with a LEG (host/device/cpp)
                      and a NATURE (historical/fresh).

THE DEVICE-PROOF LAW (the card's core): a comparison that requires
"device_leg_fresh" is satisfied ONLY by an output that exists, hash-verifies, has
leg == "device" AND nature == "fresh". A host or historical output is recorded as
an explicit `cpu_evidence_not_device_proof` rejection; a missing receipt stays
`output_missing`. CPU evidence can never close a device-required comparison, and
a real missing qualification is preserved as missing (OPEN gates are legal,
reported, and non-closing).

Verdicts: QUALIFIED (exit 0) — zero findings, every comparison satisfied, every
gate CLOSED with verified evidence, provenance commit reachable when required.
INCOMPLETE (exit 1) — a real verdict naming every finding. Refusals (exit 3):
structural problems (unknown schema, missing repo, unresolvable pin, unparseable
certificate); no verdict file is written on refusal.

Subcommands:
  from-manifest  convert anchor_manifest_v2.proposal.json (parent card D-W03,
                 PR #119) into a chimera.walking_anchor_certificate.v1 JSON.
  verify         verify a certificate against a repo; write verdict JSON.

Read-only against the repo: git rev-parse / cat-file / ls-tree / branch
--contains only. CPU-only, stdlib-only. Fixtures used by the test suite are
synthetic and labeled "fixture"; no output of this tool is native acceptance —
it is a source-identity statement (no engine, GPU or training is involved).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

CERT_SCHEMA = "chimera.walking_anchor_certificate.v1"
MANIFEST_SCHEMA = "chimera.anchor_manifest.v2.proposal"
EXIT_QUALIFIED, EXIT_INCOMPLETE, EXIT_REFUSAL = 0, 1, 3
HEX40 = "0123456789abcdef"


class Refusal(RuntimeError):
    """Structural problem: exit 3, no verdict file."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def to_crlf(data: bytes) -> bytes:
    return data.replace(b"\n", b"\r\n")


def run_git(repo: pathlib.Path, argv, what: str) -> subprocess.CompletedProcess:
    proc = subprocess.run(["git", "-C", str(repo), *argv], capture_output=True)
    if proc.returncode != 0:
        raise Refusal("GIT_FAILED what=%s exit=%d stderr=%r" % (
            what, proc.returncode,
            proc.stderr.decode("utf-8", "replace").strip()[:300]))
    return proc


def require(condition: bool, code: str, detail: str):
    if not condition:
        raise Refusal("%s %s" % (code, detail))


def is_hex40(s) -> bool:
    return isinstance(s, str) and len(s) == 40 and all(c in HEX40 for c in s.lower())


# ── git object access (read-only) ────────────────────────────────────────────
def commit_resolves(repo: pathlib.Path, commit: str) -> bool:
    proc = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify",
                           "--quiet", commit + "^{commit}"], capture_output=True)
    return proc.returncode == 0


def commit_reachable(repo: pathlib.Path, commit: str) -> bool:
    """True iff some local or remote branch contains the commit (the parent's
    orphan test). A commit object may exist yet be unreachable (a62b286e)."""
    proc = subprocess.run(["git", "-C", str(repo), "branch", "-a",
                           "--contains", commit], capture_output=True)
    if proc.returncode != 0:
        return False
    return bool(proc.stdout.decode("utf-8", "replace").strip())


def blob_at(repo: pathlib.Path, commit: str, path: str):
    """(blob_id, bytes) at commit:path, or None when the path is absent."""
    probe = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify",
                            "--quiet", "%s:%s" % (commit, path)], capture_output=True)
    if probe.returncode != 0:
        return None
    blob = probe.stdout.decode().strip()
    data = run_git(repo, ["cat-file", "blob", blob], "cat-file %s" % blob).stdout
    return blob, data


def anchor_hash(data: bytes, convention: str) -> str:
    if convention == "raw":
        return sha256_bytes(data)
    if convention == "lf-to-crlf":
        return sha256_bytes(to_crlf(data))
    raise Refusal("CONVENTION_UNKNOWN convention=%r (expected raw|lf-to-crlf)"
                  % convention)


# ── from-manifest: parent proposal -> certificate ────────────────────────────
def build_certificate_from_manifest(manifest: dict, tie2_disk_root: str) -> dict:
    require(manifest.get("schema") == MANIFEST_SCHEMA,
            "MANIFEST_SCHEMA_UNKNOWN", "expected %s" % MANIFEST_SCHEMA)
    entries = manifest["entries"]
    anchors, binaries = [], []
    for e in entries:
        if e.get("status") == "NOT_IN_GIT":
            binaries.append({
                "binary_id": e["anchor_id"],
                "anchoring": "source_build",
                "source_commit": e["commit"],
                "historical_sha256": e.get("registry_sha256"),
                "note": e.get("note", ""),
            })
        else:
            convention = "raw" if e["extraction_convention"] == "raw" else "lf-to-crlf"
            expected = (e["raw_blob_sha256"] if convention == "raw"
                        else e["registry_sha256"])
            anchors.append({
                "anchor_id": e["anchor_id"], "klass": e.get("klass"),
                "commit": e["commit"], "repo_path": e["repo_path"],
                "convention": convention, "expected_sha256": expected,
            })
    tie2 = manifest.get("tie2_battery_on_disk", {})
    outputs = []
    for rel, expected in sorted(tie2.get("files", {}).items()):
        outputs.append({
            "output_id": "tie2-" + rel,
            "leg": "host",                       # GPU legs never executed (parent)
            "nature": "historical",
            "location": {"type": "on_disk",
                         "path": str(pathlib.Path(tie2_disk_root) / rel),
                         "expected_sha256": expected},
        })
    certificate = {
        "schema": CERT_SCHEMA,
        "subject": {
            "card": "W03", "planning_gate": "versioned anchor adoption",
            "manifest_schema": MANIFEST_SCHEMA,
            "ruling": manifest.get("ruling", {}).get("decision"),
        },
        "source": {
            "repo_note": "read-only verification target",
            "provenance_commit": manifest["provenance_commit"]["sha"],
            "required_reachable": True,
        },
        "anchors": anchors,
        "binaries": binaries,
        "outputs": outputs,
        "comparisons": [
            {"comparison_id": "host_device_parity_t1_t43",
             "kind": "host_device_parity",
             "requires": ["device_leg_fresh"],
             "evidence": [o["output_id"] for o in outputs],
             "note": "parent: sole parity on record is HISTORICAL (shutdown "
                     "capture); fresh device replay is gate G3"},
            {"comparison_id": "c3_bars_remeasure",
             "kind": "c3_bars",
             "requires": ["device_leg_fresh"],
             "evidence": [],
             "note": "parent: C3 bars re-measure is gate G4 (unmeasured)"},
        ],
        "gates": [
            {"gate_id": g["id"], "status": g.get("status", "OPEN"),
             "evidence": []}
            for g in manifest.get("adoption_gates", [])
        ],
        "device_proof_required": True,
    }
    return certificate


# ── verify ───────────────────────────────────────────────────────────────────
def verify_certificate(cert: dict, repo: pathlib.Path) -> dict:
    require(isinstance(cert, dict), "CERT_NOT_OBJECT", "certificate must be an object")
    require(cert.get("schema") == CERT_SCHEMA, "CERT_SCHEMA_UNKNOWN",
            "expected %s, found %r" % (CERT_SCHEMA, cert.get("schema")))
    for section in ("anchors", "binaries", "outputs", "comparisons", "gates"):
        require(isinstance(cert.get(section), list), "CERT_SECTION_MISSING",
                "section %r missing or not a list" % section)
    src = cert.get("source") or {}
    prov = src.get("provenance_commit")
    require(is_hex40(prov), "PROVENANCE_PIN_INVALID", "found %r" % (prov,))
    require(repo.is_dir(), "REPO_MISSING", "%s is not a directory" % repo)
    require(commit_resolves(repo, prov), "PIN_UNRESOLVABLE",
            "provenance commit %s does not resolve in %s" % (prov, repo))

    findings = []
    checked = {"anchors": 0, "binaries": 0, "outputs": 0}
    reachable_commits = {}

    def note(code, subject, detail):
        findings.append({"code": code, "subject": subject, "detail": detail})

    def commit_reachable_cached(commit):
        if commit not in reachable_commits:
            reachable_commits[commit] = commit_reachable(repo, commit)
        return reachable_commits[commit]

    # provenance reachability (G1 law)
    if src.get("required_reachable", True) and not commit_reachable_cached(prov):
        note("provenance_commit_unreachable", prov[:12],
             "commit object resolves but NO local/remote branch contains it "
             "(parent G1: bring onto a reachable ref before adoption)")

    # anchors
    for a in cert["anchors"]:
        aid = a.get("anchor_id", "<unnamed>")
        commit, path = a.get("commit"), a.get("repo_path")
        require(is_hex40(commit), "ANCHOR_PIN_INVALID", "%s commit %r" % (aid, commit))
        require(commit_resolves(repo, commit), "PIN_UNRESOLVABLE",
                "anchor %s commit %s does not resolve" % (aid, commit))
        got = blob_at(repo, commit, path)
        if got is None:
            note("anchor_path_missing", aid,
                 "%s absent at %s" % (path, commit[:12]))
            continue
        actual = anchor_hash(got[1], a.get("convention", "raw"))
        checked["anchors"] += 1
        if actual != a.get("expected_sha256"):
            note("anchor_hash_mismatch", aid,
                 "expected %s, measured %s (%s at %s:%s)"
                 % (a.get("expected_sha256"), actual, a.get("convention"),
                    commit[:12], path))
        if not commit_reachable_cached(commit):
            note("anchor_commit_unreachable", aid,
                 "commit %s is on no branch (orphan evidence)" % commit[:12])

    # binaries (source+build-script anchoring; on-disk hash = only G2 closer)
    for b in cert["binaries"]:
        bid = b.get("binary_id", "<unnamed>")
        require(b.get("anchoring") == "source_build", "BINARY_ANCHORING_UNKNOWN",
                "%s anchoring %r" % (bid, b.get("anchoring")))
        commit = b.get("source_commit")
        require(is_hex40(commit), "BINARY_PIN_INVALID", "%s commit %r" % (bid, commit))
        require(commit_resolves(repo, commit), "PIN_UNRESOLVABLE",
                "binary %s source commit %s does not resolve" % (bid, commit))
        script = b.get("build_script")
        if script:
            got = blob_at(repo, commit, script["repo_path"])
            if got is None:
                note("binary_build_script_missing", bid,
                     "%s absent at %s" % (script["repo_path"], commit[:12]))
            else:
                checked["binaries"] += 1
                actual = anchor_hash(got[1], script.get("convention", "raw"))
                if actual != script.get("expected_sha256"):
                    note("binary_build_script_mismatch", bid,
                         "expected %s, measured %s" % (script.get("expected_sha256"),
                                                       actual))
        disk = b.get("on_disk")
        if disk:
            p = pathlib.Path(disk["path"])
            if not p.is_file():
                note("binary_on_disk_missing", bid, "%s absent" % p)
            else:
                actual = sha256_bytes(p.read_bytes())
                if actual != disk.get("expected_sha256"):
                    note("binary_on_disk_mismatch", bid,
                         "expected %s, measured %s" % (disk.get("expected_sha256"),
                                                       actual))
                else:
                    checked["binaries"] += 1
        else:
            note("binary_not_rebuilt", bid,
                 "anchored to source only; no rebuilt on-disk hash supplied "
                 "(parent G2: rebuild or retire binary hashes)")

    # outputs (receipts)
    verified_outputs = {}
    for o in cert["outputs"]:
        oid = o.get("output_id", "<unnamed>")
        loc = o.get("location") or {}
        if loc.get("type") == "on_disk":
            p = pathlib.Path(loc["path"])
            if not p.is_file():
                note("output_missing", oid, "on-disk receipt %s absent" % p)
                continue
            actual = sha256_bytes(p.read_bytes())
        elif loc.get("type") == "git_blob":
            require(is_hex40(loc.get("commit")), "OUTPUT_PIN_INVALID",
                    "%s commit %r" % (oid, loc.get("commit")))
            require(commit_resolves(repo, loc["commit"]), "PIN_UNRESOLVABLE",
                    "output %s commit %s does not resolve" % (oid, loc["commit"]))
            got = blob_at(repo, loc["commit"], loc["path"])
            if got is None:
                note("output_path_missing", oid,
                     "%s absent at %s" % (loc["path"], loc["commit"][:12]))
                continue
            actual = anchor_hash(got[1], loc.get("convention", "raw"))
        else:
            raise Refusal("OUTPUT_LOCATION_UNKNOWN %s location type %r"
                          % (oid, loc.get("type")))
        checked["outputs"] += 1
        if actual != loc.get("expected_sha256"):
            note("output_hash_mismatch", oid,
                 "expected %s, measured %s" % (loc.get("expected_sha256"), actual))
            continue
        verified_outputs[oid] = o

    # comparisons (the device-proof law)
    comparisons_ok = {}
    for c in cert["comparisons"]:
        cid = c.get("comparison_id", "<unnamed>")
        needs_device = "device_leg_fresh" in c.get("requires", [])
        evidence = [verified_outputs.get(e) for e in c.get("evidence", [])]
        resolved = [e for e in evidence if e is not None]
        fresh_device = [e for e in resolved if e.get("leg") == "device"
                        and e.get("nature") == "fresh"]
        satisfied = not any(e is None for e in evidence)
        if needs_device and not fresh_device:
            satisfied = False
            if resolved:
                # CPU substitution: host/historical output offered where only a
                # fresh device receipt can close the comparison. Supporting host
                # evidence NEXT TO a verified fresh device receipt is fine.
                note("cpu_evidence_not_device_proof", cid,
                     "evidence offers %d verified output(s), all host/historical "
                     "(CPU); a device-required comparison accepts ONLY "
                     "leg=device nature=fresh" % len(resolved))
            else:
                note("output_missing", cid,
                     "comparison has no verifiable evidence (fresh device "
                     "receipt absent)")
        comparisons_ok[cid] = satisfied

    # gates: CLOSED requires all referenced evidence verified + its comparisons ok
    gates_report = []
    for g in cert["gates"]:
        gid = g.get("gate_id", "<unnamed>")
        status = g.get("status", "OPEN")
        ev_refs = g.get("evidence", [])
        if status == "CLOSED":
            ok = bool(ev_refs)
            for ref in ev_refs:
                if ref not in verified_outputs:
                    note("gate_evidence_missing", gid,
                         "CLOSED gate references unverified evidence %r" % ref)
                    ok = False
            for c in cert["comparisons"]:
                if ref in c.get("evidence", []) and not comparisons_ok[c["comparison_id"]]:
                    ok = False
        else:
            ok = False
        gates_report.append({"gate_id": gid, "declared": status,
                             "effective": "CLOSED" if (status == "CLOSED" and ok)
                                          else "OPEN"})

    device_required = cert.get("device_proof_required", False)
    all_comparisons = all(comparisons_ok.values())
    all_gates_closed = all(gr["effective"] == "CLOSED" for gr in gates_report)
    qualified = (not findings and all_comparisons and all_gates_closed
                 and (all_gates_closed or not device_required))
    verdict = "QUALIFIED" if qualified else "INCOMPLETE"
    return {
        "schema": CERT_SCHEMA + ".verdict",
        "certificate_subject": cert.get("subject"),
        "repo": str(repo),
        "checked": checked,
        "findings": findings,
        "comparisons": [{"comparison_id": c["comparison_id"],
                         "satisfied": comparisons_ok[c["comparison_id"]]}
                        for c in cert["comparisons"]],
        "gates": gates_report,
        "verdict": verdict,
        "notes": [
            "Source-identity verification only: no engine, GPU or training "
            "process is involved; nothing here is native acceptance.",
            "CPU/host evidence can never satisfy a device-required comparison "
            "(device-proof law); missing qualifications are preserved as "
            "findings, never smoothed over.",
        ],
    }


# ── CLI ──────────────────────────────────────────────────────────────────────
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="implementation.py")
    sub = ap.add_subparsers(dest="command", required=True)
    fm = sub.add_parser("from-manifest")
    fm.add_argument("--manifest", required=True)
    fm.add_argument("--tie2-disk-root", required=True)
    fm.add_argument("--out", required=True)
    vf = sub.add_parser("verify")
    vf.add_argument("--certificate", required=True)
    vf.add_argument("--repo", required=True)
    vf.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    if args.command == "from-manifest":
        manifest = json.loads(pathlib.Path(args.manifest).read_text(encoding="utf-8"))
        cert = build_certificate_from_manifest(manifest, args.tie2_disk_root)
        out = pathlib.Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(cert, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8", newline="\n")
        print("certificate written: %s (%d anchors, %d binaries, %d outputs)"
              % (out, len(cert["anchors"]), len(cert["binaries"]),
                 len(cert["outputs"])))
        return 0

    cert = json.loads(pathlib.Path(args.certificate).read_text(encoding="utf-8"))
    verdict = verify_certificate(cert, pathlib.Path(args.repo))
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "verdict.json").write_text(
        json.dumps(verdict, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    print("VERDICT:", verdict["verdict"])
    print("checked:", verdict["checked"])
    for f in verdict["findings"]:
        print("FINDING", f["code"], "-", f["subject"], "-", f["detail"][:100])
    for gr in verdict["gates"]:
        if gr["effective"] != gr["declared"]:
            print("GATE", gr["gate_id"], "declared", gr["declared"],
                  "-> effective", gr["effective"])
    return EXIT_QUALIFIED if verdict["verdict"] == "QUALIFIED" else EXIT_INCOMPLETE


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as r:
        print("REFUSAL %s" % r, file=sys.stderr)
        sys.exit(EXIT_REFUSAL)
