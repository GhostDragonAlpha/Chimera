"""R5-forest-review correction evidence, v2 — hardened re-measure (read-only, CPU-only, stdlib-only).

Usage:
  python -B measure_evidence_v2.py <play_worktree> <pinned_revision> <evidence_out_dir>
      [--override-file REL=PATH]

v2 fixes the Finding msg-b935f0d9554d4924aa68f6f4f3872abd defects of v1
(tools/measure_evidence.py, preserved unchanged beside this file):

  1. EVERY git invocation is checked: nonzero exit => the whole run REFUSES
     (exit code 3, named error GIT_COMMAND_FAILED naming the exact command and
     exit code). v1 discarded returncode, so a failed command silently
     produced empty data.
  2. A failed `ls-files` can never count as "no tracked files": empty
     inventory is accepted only when git exited 0 AND the sanity query
     `git rev-parse --verify HEAD` also exited 0 (recorded in the output).
  3. Resolved blob ids are validated: `git rev-parse <pin>:<path>` failure is a
     refusal; every blob id must be 40 hex chars. `git hash-object` of each
     working file is recorded and compared to the blob at the pinned revision.
  4. The reviewed revision is PINNED: the source revision is a REQUIRED CLI
     argument (missing => named refusal). Its full sha and subject are
     recorded, and `git status --porcelain` is run over the cited paths so
     committed bytes are distinguished from dirty worktree bytes.
  5. EXPLICIT line-ending policy: for every cited document the sha256 of the
     working bytes and of the committed blob bytes (via `git cat-file blob`)
     is taken under three declared conventions -- raw, lf-normalized,
     crlf-normalized. Working==committed under >=1 convention proves the cited
     working file corresponds to its committed source. Under NO convention is
     the named FAILURE modified_cited_source (check source_identity_<rel>).

The 13 v1 checks keep their names and semantics; an intact tree must
reproduce them green, plus the new hardening checks (29 total expected).

Control injection (used by run_controls.py, never against a real worktree):
  --override-file REL=PATH  reads that cited document's WORKING bytes from
  PATH instead of the worktree (git operations still run read-only against
  the real repository, so a tampered copy fails its identity check).

Exit codes: 0 all checks green; 1 some check red; 3 refusal (no output file
written on refusal).
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

SCHEMA = "r5.correction.evidence.v2"

CLAIM_COMMIT = "9afbddcd90164b5544a16fd0bc72278d985eb6e3"
REVIEW_COMMIT = "dc7ea81111d98f32a4d88252c59f2fb8cf3c7399"

DOCS = [
    "tools/monkey_campaign/agents/R5_forest_review/report.md",
    "tools/monkey_campaign/agents/R5_forest_review/brief.md",
    "tools/monkey_campaign/agents/R5_forest_review/receipts/identity_receipt.json",
    "tools/monkey_campaign/agents/R5_forest_review/receipts/integrated_receipt.json",
    "tools/monkey_campaign/agents/R5_forest_review/receipts/citations_receipt.json",
    "tools/monkey_campaign/PLAY_BOARD.md",
    "tools/monkey_campaign/MONKEY_COMPLETION_MAP.md",
    "tools/monkey_campaign/agents/F02_terrain/report.md",
    "tools/monkey_campaign/agents/F04_contact/report.md",
    "ChimeraEngine/engine/gait_controller.hpp",
    "ChimeraEngine/engine/earth_environment.hpp",
]

RECEIPTS = {
    "identity_receipt.json": 15,
    "integrated_receipt.json": 36,
    "citations_receipt.json": 19,
}

ENGINE_CITATIONS = [
    ("ChimeraEngine/engine/gait_controller.hpp", 94, "plane_model_y_"),
    ("ChimeraEngine/engine/gait_controller.hpp", 2005, "contact_friction"),
    ("ChimeraEngine/engine/earth_environment.hpp", 67, "dot(x,n_)-r_"),
    ("ChimeraEngine/engine/earth_environment.hpp", 118, "patch_half_width_m"),
]

MAP_ROWS = ["| F05 |", "| F06 |", "| W05 |", "| W10 |"]

LINE_ENDING_POLICY = (
    "work_bytes == committed_bytes is proven when sha256 matches under >=1 of three declared "
    "conventions applied to BOTH sides: raw (no change), lf_normalized (CRLF->LF, lone CR->LF), "
    "crlf_normalized (canonicalize to LF, then LF->CRLF). If no convention matches, the document "
    "is flagged modified_cited_source (check source_identity_<rel> FAILS); it is never a pass. "
    "CAVEAT recorded per document: `git hash-object` WITHOUT --no-filters applies the "
    "attributes/core.autocrlf clean filter, so its equality with the blob id proves "
    "filtered-content equality, NOT raw-byte equality; raw-byte equality is only ever claimed "
    "via the 'raw' convention or the recorded `git hash-object --no-filters` comparison."
)

HEX40 = re.compile(r"\A[0-9a-f]{40}\Z")
MAX_STATUS_LINES = 200


class Refusal(RuntimeError):
    """Named refusal: the run stops with exit 3 and writes no output file."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def to_lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def to_crlf(data: bytes) -> bytes:
    return to_lf(data).replace(b"\n", b"\r\n")


class Git:
    """Every git invocation goes through here; returncode is always checked."""

    def __init__(self, play: pathlib.Path):
        self.play = play
        self.log = []

    def run(self, argv, stdin: bytes = None) -> subprocess.CompletedProcess:
        cmd = ["git", "-C", str(self.play), *argv]
        proc = subprocess.run(cmd, capture_output=True, input=stdin)
        self.log.append({"argv": ["git", "-C", "<play>", *argv], "exit": proc.returncode})
        if proc.returncode != 0:
            raise Refusal(
                "GIT_COMMAND_FAILED command=%r exit=%d stderr=%r"
                % (
                    " ".join(["git", "-C", str(self.play), *argv]),
                    proc.returncode,
                    proc.stderr.decode("utf-8", errors="replace").strip()[:500],
                )
            )
        return proc

    def out(self, argv, stdin: bytes = None) -> str:
        return self.run(argv, stdin).stdout.decode("utf-8", errors="replace")

    def out_bytes(self, argv, stdin: bytes = None) -> bytes:
        return self.run(argv, stdin).stdout


def require_hex40(blob_id, what):
    if not HEX40.match(blob_id or ""):
        raise Refusal("BLOB_ID_NOT_40HEX %s got %r" % (what, blob_id))
    return blob_id


def work_bytes_for(rel: str, overrides: dict) -> bytes:
    src = overrides.get(rel)
    if src is not None:
        return src.read_bytes()
    return (PLAY / rel).read_bytes()


PLAY = None  # set in main()


def main():
    global PLAY
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("play_worktree")
    ap.add_argument("pinned_revision", nargs="?")
    ap.add_argument("evidence_out_dir")
    ap.add_argument("--override-file", action="append", default=[], metavar="REL=PATH")
    args = ap.parse_args()

    if not args.pinned_revision:
        print("REFUSAL PINNED_REVISION_REQUIRED: the source revision must be passed "
              "explicitly as argv[2]; refusing to measure an unpinned tree.", file=sys.stderr)
        return 3

    play = pathlib.Path(args.play_worktree)
    if not play.is_dir():
        print("REFUSAL PLAY_WORKTREE_NOT_DIRECTORY: %r is not a directory." % str(play),
              file=sys.stderr)
        return 3
    PLAY = play
    pin_arg = args.pinned_revision

    overrides = {}
    for spec in args.override_file:
        if "=" not in spec:
            print("REFUSAL OVERRIDE_BAD_SPEC %r (expected REL=PATH)" % spec, file=sys.stderr)
            return 3
        rel, path = spec.split("=", 1)
        if rel not in DOCS:
            print("REFUSAL OVERRIDE_UNKNOWN_PATH %r is not a cited document." % rel,
                  file=sys.stderr)
            return 3
        opath = pathlib.Path(path)
        if not opath.is_file():
            print("REFUSAL OVERRIDE_MISSING_FILE %r is not a file." % path, file=sys.stderr)
            return 3
        overrides[rel] = opath

    git = Git(play)
    result = {
        "schema": SCHEMA,
        "play_worktree": str(play),
        "pinned_revision": {},
        "line_ending_policy": LINE_ENDING_POLICY,
        "worktree": {},
        "claims": {},
        "documents": {},
        "r5_receipts": {},
        "f05_f06_absence": {},
        "engine_citations": {},
        "map_rows": {},
        "notes": [],
        "checks": [],
    }

    def check(name, ok, detail):
        result["checks"].append({"check": name, "ok": bool(ok), "detail": detail})

    # 0a. Pin the reviewed revision -------------------------------------------
    pin_full = git.out(["rev-parse", "--verify", pin_arg + "^{commit}"]).strip()
    require_hex40(pin_full, "pinned_revision")
    log_line = git.out(["log", "--format=%H%x00%s", "-1", pin_full])
    pin_sha, _, pin_subject = log_line.partition("\0")
    head_sha = git.out(["rev-parse", "--verify", "HEAD"]).strip()  # also the ls-files sanity query
    sanity_ok = bool(HEX40.match(head_sha))
    result["pinned_revision"] = {
        "argument": pin_arg,
        "full_sha": pin_sha,
        "subject": pin_subject,
        "is_head_of_worktree": pin_sha == head_sha,
        "head_sha": head_sha,
    }
    check("pinned_revision_resolved", True,
          "pin %r resolved to %s (%.72s...); is_head=%s"
          % (pin_arg, pin_sha, pin_subject, pin_sha == head_sha))
    check("sanity_query_head_ok", sanity_ok,
          "git rev-parse --verify HEAD exit 0 -> %s" % head_sha[:12])

    # 0b. Worktree cleanliness at the cited paths (committed vs dirty bytes) ---
    cited_status = [ln for ln in git.out(["status", "--porcelain", "--", *DOCS]).splitlines() if ln]
    full_status = [ln for ln in git.out(["status", "--porcelain"]).splitlines() if ln]
    result["worktree"] = {
        "clean_at_cited_paths": not cited_status,
        "status_porcelain_cited_paths": cited_status,
        "status_porcelain_all_paths_count": len(full_status),
        "status_porcelain_all_paths_first_%d" % MAX_STATUS_LINES: full_status[:MAX_STATUS_LINES],
        "cited_paths_status_argv": ["git", "-C", "<play>", "status", "--porcelain", "--", *DOCS],
    }
    result["notes"].append(
        "tools/monkey_campaign/contributions/ shows as untracked (??) in the play worktree: "
        "expected -- it is a worker contribution directory, not part of the reviewed tree."
    )
    check("cited_paths_clean", not cited_status,
          "git status --porcelain over the %d cited paths: %s"
          % (len(DOCS), cited_status if cited_status else "empty (clean)"))

    # 0c. ls-files inventory (Finding-1 rule: never empty-on-failure) ----------
    tracked_raw = git.out(["ls-files", "--", "tools/monkey_campaign"])
    tracked = [ln for ln in tracked_raw.splitlines() if ln]
    empty_accepted = (not tracked) and sanity_ok
    result["worktree"]["ls_files_inventory"] = {
        "argv": ["git", "-C", "<play>", "ls-files", "--", "tools/monkey_campaign"],
        "exit": 0,
        "path_count": len(tracked),
        "empty_result": not tracked,
        "empty_accepted_only_because_sanity_ok": empty_accepted,
        "sanity_query": "git rev-parse --verify HEAD",
        "sanity_ok": sanity_ok,
    }
    if not tracked and not sanity_ok:
        raise Refusal("EMPTY_INVENTORY_WITHOUT_SANITY: ls-files returned nothing and the "
                      "HEAD sanity query did not succeed; refusing to treat a failed or "
                      "unverified inventory as 'no tracked files'.")
    check("ls_files_inventory_sanitized", True,
          "ls-files exit 0, %d tracked paths, sanity query ok; empty-on-failure impossible"
          % len(tracked))

    # 1. Claim commits ---------------------------------------------------------
    for label, rev, needle in [
        ("front_complete_claim", CLAIM_COMMIT, "FOREST FRONT F01-F08 COMPLETE; W10 scene-ready"),
        ("r5_w10_scene_ready_claim", REVIEW_COMMIT, "W10 SCENE-READY"),
    ]:
        subject = git.out(["log", "--format=%s", "-1", rev]).strip()
        result["claims"][label] = {"commit": rev, "subject": subject}
        check(f"claim_{label}", needle in subject, f"subject contains {needle!r}: {needle in subject}")

    # 2. Document identities -----------------------------------------------------
    claim_blob_valid = True
    for rel in DOCS:
        wbytes = work_bytes_for(rel, overrides)
        pin_blob = require_hex40(
            git.out(["rev-parse", "%s:%s" % (pin_sha, rel)]).strip(),
            "rev-parse %s:%s" % (pin_sha, rel),
        )

        # Blob at the claim commit: ls-tree-guarded (R5 files landed AFTER 9afbddcd,
        # so absence there is data, not a git failure; any present-but-unresolvable
        # entry is still a refusal).
        claim_entry = git.out(["ls-tree", CLAIM_COMMIT, "--", rel]).strip()
        if claim_entry:
            claim_blob = git.out(["rev-parse", "%s:%s" % (CLAIM_COMMIT, rel)]).strip()
            require_hex40(claim_blob, "rev-parse %s:%s" % (CLAIM_COMMIT, rel))
            claim_record = {"blob_id": claim_blob, "present_at_claim_commit": True}
            claim_blob_valid = claim_blob_valid and bool(HEX40.match(claim_blob))
        else:
            claim_record = {
                "blob_id": None,
                "present_at_claim_commit": False,
                "reason": "absent_at_claim_commit (git ls-tree empty, exit 0)",
            }

        if rel in overrides:
            ho_blob = git.out(["hash-object", "--stdin"], stdin=wbytes).strip()
            ho_raw = git.out(["hash-object", "--no-filters", "--stdin"], stdin=wbytes).strip()
            ho_method = "git hash-object [--no-filters] --stdin (override bytes)"
        else:
            ho_blob = git.out(["hash-object", "--", rel]).strip()
            ho_raw = git.out(["hash-object", "--no-filters", "--", rel]).strip()
            ho_method = "git hash-object [--no-filters] -- <worktree path>"
        require_hex40(ho_blob, "hash-object %s" % rel)
        require_hex40(ho_raw, "hash-object --no-filters %s" % rel)

        bblob = git.out_bytes(["cat-file", "blob", pin_blob])
        conv_work = {"raw": sha256(wbytes), "lf_normalized": sha256(to_lf(wbytes)),
                     "crlf_normalized": sha256(to_crlf(wbytes))}
        conv_blob = {"raw": sha256(bblob), "lf_normalized": sha256(to_lf(bblob)),
                     "crlf_normalized": sha256(to_crlf(bblob))}
        matching = sorted(k for k in conv_work if conv_work[k] == conv_blob[k])
        result["documents"][rel] = {
            "bytes": len(wbytes),
            "override_source": str(overrides[rel]) if rel in overrides else None,
            "work_sha256": conv_work,
            "blob_at_pin": {
                "blob_id": pin_blob,
                "bytes": len(bblob),
                "sha256": conv_blob,
            },
            "blob_at_claim_commit": claim_record,
            "git_hash_object": {
                "filtered_blob_id": ho_blob,
                "filtered_equals_blob_at_pin": ho_blob == pin_blob,
                "raw_disk_blob_id_no_filters": ho_raw,
                "raw_disk_bytes_equal_blob_at_pin": ho_raw == pin_blob,
                "method": ho_method,
                "note": "filtered hash applies attributes/core.autocrlf clean filter; "
                        "raw_disk_bytes_equal_blob_at_pin is the raw-byte claim",
            },
            "identity_conventions_matching": matching,
            "identity_ok": bool(matching),
        }
        check(
            "source_identity_%s" % rel,
            bool(matching),
            ("identity OK under convention(s) %s (raw disk bytes == blob: %s)"
             % (matching, ho_raw == pin_blob)) if matching else
            ("MODIFIED_CITED_SOURCE: work bytes match committed blob %s under NO declared "
             "line-ending convention" % pin_blob[:12]),
        )

    check("blob_ids_valid_at_pin", True, "all %d rev-parse <pin>:<path> ids are 40 hex" % len(DOCS))
    check("claim_blob_ids_valid", claim_blob_valid,
          "every blob resolved at claim commit %s is 40 hex" % CLAIM_COMMIT[:12])
    check("doc_identities_measured", len(result["documents"]) == len(DOCS),
          f"{len(result['documents'])}/{len(DOCS)} documents hashed")

    # 3. R5 receipt pass counts -----------------------------------------------
    for name, expected in RECEIPTS.items():
        rel = f"tools/monkey_campaign/agents/R5_forest_review/receipts/{name}"
        data = json.loads(work_bytes_for(rel, overrides).decode("utf-8"))
        checks = data["checks"]
        passed = sum(1 for c in checks if c.get("ok") is True or c.get("pass") is True)
        result["r5_receipts"][name] = {"total": len(checks), "pass_flagged": passed}
        check(
            f"receipt_{name}",
            passed == expected and len(checks) == expected,
            f"{passed}/{len(checks)} pass-flagged (report claims {expected})",
        )

    # 4. F05/F06 artifact absence ----------------------------------------------
    agents_dir = play / "tools/monkey_campaign/agents"
    dirs = sorted(d.name for d in agents_dir.iterdir() if d.is_dir())
    f05_dirs = [d for d in dirs if d.upper().startswith(("F05", "F06"))]
    f05_tracked = [ln for ln in tracked if re.search(r"/F0[56]|F0[56][_/.]", ln)]
    board_bytes = work_bytes_for("tools/monkey_campaign/PLAY_BOARD.md", overrides)
    board = board_bytes.decode("utf-8")
    forest_row = next(ln for ln in board.splitlines() if ln.startswith("| Forest |"))
    result["f05_f06_absence"] = {
        "agent_dirs_present": dirs,
        "f05_f06_dirs": f05_dirs,
        "f05_f06_tracked_files": f05_tracked,
        "f05_f06_tracked_source": "git ls-files exit 0 inventory (%d paths)" % len(tracked),
        "forest_row": forest_row,
        "forest_row_names_f05_or_f06": ("F05" in forest_row) or ("F06" in forest_row),
    }
    check("f05_f06_no_agent_dirs", not f05_dirs, f"agent dirs matching F05/F06: {f05_dirs}")
    check("f05_f06_no_tracked_files", not f05_tracked,
          f"tracked files matching (verified-exit ls-files): {f05_tracked}")
    check(
        "f05_f06_not_on_board",
        not result["f05_f06_absence"]["forest_row_names_f05_or_f06"],
        "Forest front row of PLAY_BOARD.md names no F05/F06 state",
    )

    # 5. Engine citations (working line AND pinned-blob line recorded) ----------
    for rel, line_no, needle in ENGINE_CITATIONS:
        wlines = work_bytes_for(rel, overrides).decode("utf-8", errors="replace").splitlines()
        blines = git.out_bytes(["cat-file", "blob",
                                result["documents"][rel]["blob_at_pin"]["blob_id"]]
                               ).decode("utf-8", errors="replace").splitlines()
        wline = wlines[line_no - 1]
        bline = blines[line_no - 1]
        result["engine_citations"][f"{rel}:{line_no}"] = {
            "work_line": wline.strip(),
            "work_contains": needle in wline,
            "blob_at_pin_line": bline.strip(),
            "blob_contains": needle in bline,
            "work_line_equals_blob_line": wline == bline,
        }
        check(f"engine_{rel.split('/')[-1]}:{line_no}", needle in wline,
              f"expected {needle!r} in line {line_no}")

    # 6. Map rows verbatim -------------------------------------------------------
    map_text = work_bytes_for("tools/monkey_campaign/MONKEY_COMPLETION_MAP.md",
                              overrides).decode("utf-8")
    for prefix in MAP_ROWS:
        row = next(ln for ln in map_text.splitlines() if ln.startswith(prefix))
        result["map_rows"][prefix.strip("| ").split()[0]] = row

    result["git_command_log"] = git.log
    passed = sum(1 for c in result["checks"] if c["ok"])
    result["summary"] = f"{passed}/{len(result['checks'])} evidence checks green"

    out = pathlib.Path(args.evidence_out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "identities_v2.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(result["summary"])
    for c in result["checks"]:
        print(("PASS" if c["ok"] else "FAIL"), c["check"], "-", c["detail"][:110])
    return 0 if passed == len(result["checks"]) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as r:
        print("REFUSAL %s" % r, file=sys.stderr)
        sys.exit(3)
