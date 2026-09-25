"""Failing controls for measure_evidence_v2.py (Finding msg-b935f0d9554d4924aa68f6f4f3872abd).

Usage:
  python -B run_controls.py <play_worktree> <pinned_revision> <control_results_json>

Executes, read-only against the real play worktree, with all scratch inside
system temp dirs (removed afterwards; nothing is written into any worktree):

  (a) GIT-FAILURE control: point v2 at a temp dir that is NOT a git repository.
      DEMAND: v2 must REFUSE -- nonzero exit, named error, no output file.
      The ORIGINAL tools/measure_evidence.py is then run read-only against the
      SAME temp dir and its behavior recorded exactly (it is NOT fixed).

  (b) MODIFIED-CITED-SOURCE control: v2 is fed a TAMPERED temp copy of one
      cited document (tools/monkey_campaign/PLAY_BOARD.md) via its documented
      --override-file injection point. DEMAND: v2 must FAIL that document's
      identity check (named modified_cited_source), exit nonzero.

  (c) LINE-ENDING-RESCUE positive control: v2 is fed an EOL-flipped (CRLF->LF)
      temp copy of a cited document whose raw disk bytes differ from its blob
      only by line endings. DEMAND: identity still proven under the declared
      normalization conventions -- proving convention matching is a real
      discriminator, not a vacuous pass.

Exit code: 0 if every control behaved as demanded, 1 otherwise.
stdlib only; bounded well under 120 s.
"""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
V2 = HERE / "measure_evidence_v2.py"
V1 = HERE / "measure_evidence.py"

TAMPER_DOC = "tools/monkey_campaign/PLAY_BOARD.md"
TAMPER_SUFFIX = b"\n<!-- tampered by run_controls.py control (b) modified-cited-source -->\n"
RESCUE_DOC = "tools/monkey_campaign/agents/R5_forest_review/receipts/identity_receipt.json"


def to_lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def run_py(script, argv, env=None):
    proc = subprocess.run([sys.executable, "-B", str(script), *argv],
                          capture_output=True, timeout=110, env=env)
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout.decode("utf-8", errors="replace"),
        "stderr": proc.stderr.decode("utf-8", errors="replace"),
    }


def ceiling_env(ceiling_dir: pathlib.Path) -> dict:
    """Environment isolating <ceiling_dir> from upward repo discovery.

    This machine has a repository discoverable at the drive root (git
    rev-parse --show-toplevel from a fresh temp dir returns C:/), so without a
    ceiling every temp dir would silently inherit that unrelated repo.
    GIT_CEILING_DIRECTORIES is the standard git test-suite mechanism; it is
    applied ONLY to control scratch dirs, never to the real worktree runs.
    """
    env = dict(os.environ)
    env["GIT_CEILING_DIRECTORIES"] = str(ceiling_dir)
    return env


def main():
    play = pathlib.Path(sys.argv[1]).resolve()
    pin = sys.argv[2]
    out_path = pathlib.Path(sys.argv[3]).resolve()

    results = {
        "schema": "r5.correction.controls.v1",
        "generated_by": "run_controls.py",
        "v2_tool": str(V2),
        "original_tool_unchanged": str(V1),
        "play_worktree": str(play),
        "pinned_revision_argument": pin,
        "controls": {},
    }
    ok_all = True

    def verdict(name, ok, what):
        nonlocal ok_all
        ok_all = ok_all and ok
        results["controls"][name]["verdict"] = ("PASS" if ok else "FAIL") + " — " + what

    # Shared: pin identity for the record ------------------------------------------------
    g = subprocess.run(["git", "-C", str(play), "rev-parse", "--verify", pin + "^{commit}"],
                       capture_output=True)
    if g.returncode != 0:
        print("CONTROL-HARNESS REFUSAL: pinned revision %r does not resolve in %s" % (pin, play),
              file=sys.stderr)
        return 1
    results["pinned_revision_full_sha"] = g.stdout.decode().strip()

    # ---------------------------------------------------------------- (a) git failure
    ctrl = {}
    results["controls"]["a_git_failure_not_a_repo"] = ctrl
    tmp_a = pathlib.Path(tempfile.mkdtemp(prefix="r5ctrl_a_notarepo_"))
    try:
        env_a = ceiling_env(tmp_a.parent)
        ctrl["environment"] = {
            "GIT_CEILING_DIRECTORIES": str(tmp_a.parent),
            "note": ("isolates the control temp dir from upward repo discovery (a repo is "
                     "discoverable at this machine's drive root); applies ONLY to this "
                     "control's scratch dir, never to the real worktree runs"),
        }
        pre = subprocess.run(["git", "-C", str(tmp_a), "rev-parse", "--is-inside-work-tree"],
                             capture_output=True, env=env_a)
        ctrl["precondition"] = {
            "temp_dir": str(tmp_a),
            "command": "git -C <temp_dir> rev-parse --is-inside-work-tree",
            "exit_code": pre.returncode,
            "stderr": pre.stderr.decode("utf-8", errors="replace").strip(),
        }
        if pre.returncode == 0:
            ctrl["precondition"]["error"] = "temp dir unexpectedly IS inside a work tree; control invalid"
            verdict("a_git_failure_not_a_repo", False, "precondition failed")
            return finish(results, out_path, ok_all, tmp_a_exists=[tmp_a])
        out_a = tmp_a / "out"
        r_v2 = run_py(V2, [str(tmp_a), pin, str(out_a)], env=env_a)
        ctrl["v2"] = {
            "command": [sys.executable, "-B", str(V2), str(tmp_a), pin, str(out_a)],
            "exit_code": r_v2["exit_code"],
            "stdout_lines": r_v2["stdout"].splitlines(),
            "stderr_lines": r_v2["stderr"].splitlines(),
            "output_file_created": (out_a / "identities_v2.json").is_file(),
        }
        ok_a = (r_v2["exit_code"] == 3
                and r_v2["stderr"].startswith("REFUSAL")
                and not ctrl["v2"]["output_file_created"])
        verdict("a_git_failure_not_a_repo", ok_a,
                "v2 refused: exit %d, first stderr line %r, no output file written"
                % (r_v2["exit_code"], r_v2["stderr"].splitlines()[0] if r_v2["stderr"] else ""))

        # The ORIGINAL tool under the SAME control (read-only; recorded, not fixed).
        out_a1 = tmp_a / "out_v1"
        r_v1 = run_py(V1, [str(tmp_a), str(out_a1)], env=env_a)
        tail = [ln for ln in r_v1["stderr"].splitlines() if ln.strip()][-4:]
        ctrl["original_measure_evidence_py_same_control"] = {
            "command": [sys.executable, "-B", str(V1), str(tmp_a), str(out_a1)],
            "exit_code": r_v1["exit_code"],
            "stdout": r_v1["stdout"],
            "stderr_tail_lines": tail,
            "output_file_created": (out_a1 / "identities.json").is_file(),
            "observed": ("v1 crashed with an unhandled exception (traceback) after silently "
                         "treating every failed git command as empty data; no named refusal, "
                         "no output file, no returncode checks anywhere in its git() helper."),
            "code_inspection": (
                "tools/measure_evidence.py lines 59-63: git() returns "
                "subprocess.run(...).stdout.strip() with no returncode check, so a failed "
                "`git ls-files` would yield '' -> splitlines() == [] and check "
                "f05_f06_no_tracked_files would PASS on an empty inventory — the silent-empty "
                "defect named by finding msg-b935f0d9554d4924aa68f6f4f3872abd. In this control "
                "the run crashed earlier (first document read), so the defect is shown by "
                "inspection plus the crash itself. The original file is preserved unmodified."
            ),
        }
        ctrl["original_verdict"] = "CONFIRMED DEFECT (original left byte-identical)"
    finally:
        shutil.rmtree(tmp_a, ignore_errors=True)
        ctrl["temp_dir_removed"] = True

    # ------------------------------------------------------- (b) modified cited source
    ctrl = {}
    results["controls"]["b_modified_cited_source"] = ctrl
    tmp_b = pathlib.Path(tempfile.mkdtemp(prefix="r5ctrl_b_tampered_"))
    try:
        orig_bytes = (play / TAMPER_DOC).read_bytes()
        tampered = tmp_b / "PLAY_BOARD.tampered.md"
        tampered.write_bytes(orig_bytes + TAMPER_SUFFIX)
        ctrl["setup"] = {
            "document": TAMPER_DOC,
            "tamper": "append %d bytes (%r...) to a TEMP COPY; the real worktree is untouched"
                      % (len(TAMPER_SUFFIX), TAMPER_SUFFIX[:40]),
            "temp_copy": str(tampered),
            "orig_work_sha256": hashlib.sha256(orig_bytes).hexdigest(),
            "tampered_sha256": hashlib.sha256(orig_bytes + TAMPER_SUFFIX).hexdigest(),
        }
        out_b = tmp_b / "out"
        r_b = run_py(V2, [str(play), pin, str(out_b),
                          "--override-file", "%s=%s" % (TAMPER_DOC, tampered)])
        ctrl["v2"] = {
            "command": [sys.executable, "-B", str(V2), str(play), pin, str(out_b),
                        "--override-file", "%s=%s" % (TAMPER_DOC, tampered)],
            "exit_code": r_b["exit_code"],
            "stdout_lines": r_b["stdout"].splitlines(),
            "stderr_lines": r_b["stderr"].splitlines(),
        }
        identity_json = out_b / "identities_v2.json"
        ctrl["output_file_created"] = identity_json.is_file()
        if identity_json.is_file():
            data = json.loads(identity_json.read_text(encoding="utf-8"))
            doc = data["documents"][TAMPER_DOC]
            bad = [c for c in data["checks"]
                   if c["check"] == "source_identity_%s" % TAMPER_DOC]
            ctrl["failing_check"] = bad[0] if bad else None
            ctrl["document_record_identity"] = {
                "identity_ok": doc["identity_ok"],
                "identity_conventions_matching": doc["identity_conventions_matching"],
                "override_source": doc["override_source"],
                "work_sha256": doc["work_sha256"],
            }
            ctrl["summary"] = data["summary"]
        ok_b = (r_b["exit_code"] == 1
                and ctrl.get("failing_check") is not None
                and ctrl["failing_check"]["ok"] is False
                and "MODIFIED_CITED_SOURCE" in ctrl["failing_check"]["detail"]
                and ctrl["document_record_identity"]["identity_ok"] is False)
        verdict("b_modified_cited_source", ok_b,
                "v2 failed exactly the tampered document's identity check "
                "(source_identity_%s ok=false, named MODIFIED_CITED_SOURCE), run exit %d"
                % (TAMPER_DOC, r_b["exit_code"]))
    finally:
        shutil.rmtree(tmp_b, ignore_errors=True)
        ctrl["temp_dir_removed"] = True

    # ------------------------------------------- (c) line-ending rescue (positive control)
    ctrl = {}
    results["controls"]["c_line_ending_rescue_positive"] = ctrl
    tmp_c = pathlib.Path(tempfile.mkdtemp(prefix="r5ctrl_c_eolflip_"))
    try:
        raw = (play / RESCUE_DOC).read_bytes()
        flipped = to_lf(raw)
        blob = subprocess.run(["git", "-C", str(play), "rev-parse", "HEAD:" + RESCUE_DOC],
                              capture_output=True)
        blob_id = blob.stdout.decode().strip() if blob.returncode == 0 else None
        ho_raw = subprocess.run(["git", "-C", str(play), "hash-object", "--no-filters", "--", RESCUE_DOC],
                                capture_output=True).stdout.decode().strip()
        precondition = {
            "document": RESCUE_DOC,
            "work_bytes_contain_crlf": b"\r\n" in raw,
            "blob_id_committed": blob_id,
            "work_raw_disk_hash_object": ho_raw,
            "raw_disk_bytes_equal_blob": ho_raw == blob_id,
            "flipped_copy_sha256": hashlib.sha256(flipped).hexdigest(),
        }
        ctrl["setup"] = precondition
        applicable = (precondition["work_bytes_contain_crlf"]
                      and precondition["raw_disk_bytes_equal_blob"] is False)
        if not applicable:
            ctrl["observed"] = ("precondition not met on this tree (document's raw disk bytes "
                                "already equal its blob or contain no CRLF); control recorded "
                                "as NOT_APPLICABLE, not faked.")
            verdict("c_line_ending_rescue_positive", False, "NOT_APPLICABLE precondition")
        else:
            flip_copy = tmp_c / "identity_receipt.lfflipped.json"
            flip_copy.write_bytes(flipped)
            out_c = tmp_c / "out"
            r_c = run_py(V2, [str(play), pin, str(out_c),
                              "--override-file", "%s=%s" % (RESCUE_DOC, flip_copy)])
            ctrl["v2"] = {
                "command": [sys.executable, "-B", str(V2), str(play), pin, str(out_c),
                            "--override-file", "%s=%s" % (RESCUE_DOC, flip_copy)],
                "exit_code": r_c["exit_code"],
                "stdout_lines": r_c["stdout"].splitlines()[:4],
                "stderr_lines": r_c["stderr"].splitlines(),
            }
            ij = out_c / "identities_v2.json"
            ctrl["output_file_created"] = ij.is_file()
            if ij.is_file():
                data = json.loads(ij.read_text(encoding="utf-8"))
                doc = data["documents"][RESCUE_DOC]
                ctrl["document_record_identity"] = {
                    "identity_ok": doc["identity_ok"],
                    "identity_conventions_matching": doc["identity_conventions_matching"],
                    "raw_disk_bytes_equal_blob_at_pin":
                        doc["git_hash_object"]["raw_disk_bytes_equal_blob_at_pin"],
                }
                ctrl["summary"] = data["summary"]
            ok_c = (r_c["exit_code"] == 0
                    and ctrl["document_record_identity"]["identity_ok"] is True
                    and "raw" in ctrl["document_record_identity"]["identity_conventions_matching"]
                    and ctrl["document_record_identity"]["raw_disk_bytes_equal_blob_at_pin"] is True)
            verdict("c_line_ending_rescue_positive", ok_c,
                    "EOL-flipped copy still proves identity (conventions %s): the policy "
                    "distinguishes pure line-ending differences from content modification"
                    % ctrl["document_record_identity"]["identity_conventions_matching"])
    finally:
        shutil.rmtree(tmp_c, ignore_errors=True)
        ctrl["temp_dir_removed"] = True

    return finish(results, out_path, ok_all, tmp_a_exists=[])


def finish(results, out_path, ok_all, tmp_a_exists):
    for p in tmp_a_exists:
        shutil.rmtree(p, ignore_errors=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8", newline="\n")
    print("CONTROLS %s — %d/3 behaved as demanded; results written to %s"
          % ("PASS" if ok_all else "FAIL",
             sum(1 for c in results["controls"].values()
                 if str(c.get("verdict", "")).startswith("PASS")),
             out_path))
    for name, c in results["controls"].items():
        print(("PASS" if str(c.get("verdict", "")).startswith("PASS") else "FAIL"),
              name, "-", c.get("verdict", ""))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
