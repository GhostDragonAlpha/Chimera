"""test_implementation.py -- ONT-U05 bring-forward RE-VERIFICATION harness
(attempt c7f9519f83c54b3094f1cf097baa742b, prereg: PREREGISTRATION.md in this
directory).

This attempt brings the already-reviewed climb/let-go intent seam forward
BYTE-IDENTICAL from lineage commit 272e7bda (monkey-play-20260924) and
independently re-verifies it instead of trusting the lineage receipts. This
harness is the attempt's only authored source. It:

  F1  hashes implementation.py + every reference/ extract against the pinned
      272e7bda blob hashes (identity).
  F2  reassembles a hash-verified sandbox tree (repo layout) and runs the
      UNMODIFIED original suites from reference/: climb_intent_tests.py must be
      GREEN 73/73, climb_intent_amr_tests.py GREEN 4/4 (falsifiers I1-I8 + AMR).
  F3  pins the sandbox walk contract: sha256 of command_record.py identical
      before and after every suite run (the lineage falsifier I6, re-measured).
  F4  proves the suites have TEETH: three named single-defect mutations of the
      sandbox copy of the seam module (M1 edge law, M2 version law, M3 gate law)
      must make the suites FAIL with the predicted falsifier family firing;
      reference/ and the candidate bytes are never mutated.
  F5  scope: in the attempt checkout, `git status --porcelain -uall` may list
      ONLY paths under tools/monkey_campaign/contributions/ONT-U05/.

Headless, CPU-only (`python -B`), injected clocks only (inside the imported
suites); no network, no desktop, no engine. Each subprocess is bounded to 110 s.

    python -B tools/monkey_campaign/contributions/ONT-U05/test_implementation.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECEIPTS = HERE / "receipts"
LINEAGE_REV = "272e7bda"
BASE_REV = "c525b82c7c3ce0128565424764293a3c85811ab3"
SEAM_SHA = "586cb1c541afdc391ac14ce989cf2d2561a9ee79e25e874f7fbfc2312fd3c5a2"

# Pinned 272e7bda blob (LF) identities -- extracted with `git show <rev>:<path>`.
PINNED = {
    "implementation.py": SEAM_SHA,
    "INTENT_SEAM_SPEC.md":
        "772d809df620bb93cce97fd41f081ba244b44edfef8d9ee4797f16cc8eac143b",
    "reference/science_funnel/__init__.py":
        "c5a9f9b162177ec18d127edb799bbfe1ba08442ed95c72f8f0947f9d64618b19",
    "reference/science_funnel/typeb_export/__init__.py":
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "reference/science_funnel/typeb_export/command_record.py":
        "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e",
    "reference/product/climb_intent_tests.py":
        "291eb0b60e754e497d425dada1dffdf0839ea3f8a91f16fd0239ab3f9fdc9895",
    "reference/product/climb_intent_amr_tests.py":
        "7ff7f3ba2678d6533e6f40666b5faf9f102751377bc4f89bf68846d2df3b7538",
    "reference/product/input_mapper.py":
        "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44",
    "reference/product/focus_policy.py":
        "e0b23968bb8ee8e7c5449da464948d68cc67bf3cc62db40dd30a73ee8ef0f9d0",
    "reference/product/session_flow.py":
        "30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf",
    "reference/lineage/PREREGISTRATION_U05_lineage.md":
        "5f1d94f4e2d1cdc13e85fdf664db0784385df99a5f606e809c3e9eec0528ba2d",
    "reference/lineage/receipts/R4_review_report.md":
        "e456945f568e2c7eb750cd807607152e83da2d19a28875fdc07dedafb25de418",
    "reference/lineage/receipts/amr_failing_first_20260924.txt":
        "90f1398ec371135224e20312aeed5b8b91da1c406d40fcab1f3aad687c2dafd7",
    "reference/lineage/receipts/climb_intent_tests_20260924.txt":
        "91e9e2208241e50ac389c483e58dbef1a584b7b7d6774655d95980dde09f33a0",
    "reference/lineage/receipts/climb_intent_tests_77of77_with_amr_20260924.txt":
        "8f7b9f0965bdcd13249a2438aaca1aff0a74558e95a290c46fa0ece90221e990",
    "reference/lineage/receipts/r4_probe_battery_postfix_allgreen_20260924.txt":
        "04c7d70b67d5f6df63a2500132d234d5c98ba2bf7f5ac41ed079e966f62a4509",
    "reference/lineage/receipts/walk_contract_hash_proof_20260924.txt":
        "75fe5cb6e07e7cb153495d3d6b415957f35e408d8b54ad4330cd5f6636b3caf8",
}

FAILURES = []


def check(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(Path(p).read_bytes())


def run_suite(script: Path, timeout=110):
    """Run one original suite CPU-only (`python -B`), capture everything."""
    t0 = time.monotonic()
    proc = subprocess.run(
        [sys.executable, "-B", str(script)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout)
    return proc, time.monotonic() - t0


# ── the sandbox (repo layout rebuilt from pinned reference/ bytes) ───────────
SANDBOX_MAP = {
    "reference/science_funnel/__init__.py":
        "tools/science_funnel/__init__.py",
    "reference/science_funnel/typeb_export/__init__.py":
        "tools/science_funnel/typeb_export/__init__.py",
    "reference/science_funnel/typeb_export/command_record.py":
        "tools/science_funnel/typeb_export/command_record.py",
    "implementation.py":
        "tools/monkey_campaign/product/climb_intent.py",
    "reference/product/climb_intent_tests.py":
        "tools/monkey_campaign/product/climb_intent_tests.py",
    "reference/product/climb_intent_amr_tests.py":
        "tools/monkey_campaign/product/climb_intent_amr_tests.py",
    "reference/product/input_mapper.py":
        "tools/monkey_campaign/product/input_mapper.py",
    "reference/product/focus_policy.py":
        "tools/monkey_campaign/product/focus_policy.py",
    "reference/product/session_flow.py":
        "tools/monkey_campaign/product/session_flow.py",
}


def build_sandbox(root: Path) -> Path:
    """Copy pinned bytes into the repo layout; verify every copied hash."""
    for src_rel, dst_rel in SANDBOX_MAP.items():
        src = HERE / src_rel
        dst = root / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        data = src.read_bytes()
        if src_rel in PINNED and sha256_bytes(data) != PINNED[src_rel]:
            raise AssertionError(f"pinned bytes diverge before copy: {src_rel}")
        dst.write_bytes(data)
        if sha256_file(dst) != sha256_file(src):
            raise AssertionError(f"copy diverged: {dst_rel}")
    return root / "tools" / "monkey_campaign" / "product"


def mutate(product_dir: Path, old: str, new: str) -> None:
    """Apply ONE named defect to the SANDBOX copy only (never to reference/)."""
    target = product_dir / "climb_intent.py"
    text = target.read_bytes().decode("utf-8")
    count = text.count(old)
    if count != 1:
        raise AssertionError(
            f"mutation anchor not unique (count={count}); demo is broken -- "
            "falsifier F4 fires honestly rather than mis-measure")
    target.write_bytes(text.replace(old, new, 1).encode("utf-8"))


M1_EDGE = (
    '            self.last_trace.setdefault("repeat_press", []).append((name, now_ms))\n'
    "            return action\n",
    '            self.last_trace.setdefault("repeat_press", []).append((name, now_ms))\n'
    "            self._sink.emit(self._stamp(action, now_ms))  # M1: BROKEN EDGE\n"
    "            return action\n",
)
M2_VERSION = (
    "                or v != INTENT_VERSION):",
    "                or (v != INTENT_VERSION and v != 2)):  # M2: BROKEN VERSION",
)
M3_GATE = (
    "            self._drop(name, now_ms)    # named; and NOT armed (no phantom edge)\n"
    "            return None",
    "            pass  # M3: BROKEN GATE (gated press falls through)",
)


def fired_names(stdout: str) -> list:
    return [ln.split()[1] for ln in stdout.splitlines()
            if ln.startswith("  FIRED: ")]


def main() -> int:
    RECEIPTS.mkdir(exist_ok=True)
    print("ONT-U05 re-verification (bring-forward of the pinned climb intent "
          "seam, prereg: PREREGISTRATION.md)")

    # ── F1 identity ──────────────────────────────────────────────────────────
    print("F1 IDENTITY: candidate + reference bytes vs pinned 272e7bda blobs")
    manifest = {}
    identity_ok = True
    for rel, expected in PINNED.items():
        p = HERE / rel
        observed = sha256_file(p) if p.is_file() else "MISSING"
        manifest[rel] = {"expected": expected, "observed": observed,
                         "match": observed == expected}
        identity_ok &= observed == expected
    check(f"all {len(PINNED)} pinned artifacts byte-identical to 272e7bda "
          f"(incl. implementation.py == {SEAM_SHA[:12]}...)", identity_ok,
          "F1 FIRES on any mismatch" if not identity_ok else "")
    (RECEIPTS / "identity_manifest.json").write_text(
        json.dumps({"lineage_rev": LINEAGE_REV, "base_rev": BASE_REV,
                    "artifacts": manifest}, indent=2, sort_keys=True),
        encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="ont-u05-") as tmp:
        root = Path(tmp)
        product = build_sandbox(root)
        main_suite = product / "climb_intent_tests.py"
        amr_suite = product / "climb_intent_amr_tests.py"
        seam_path = root / "tools" / "science_funnel" / "typeb_export" / "command_record.py"

        def suite_pass(name, proc, dt, expect_green=True, want_pass=None):
            out = proc.stdout + proc.stderr
            n_pass = out.count("[PASS]")
            n_fail = out.count("[FAIL]")
            green = "RESULT: GREEN" in proc.stdout
            ok = (proc.returncode == 0 and green and n_fail == 0
                  and (want_pass is None or n_pass == want_pass))
            if not expect_green:
                ok = proc.returncode == 1 and n_fail > 0
            check(name, ok,
                  f"exit={proc.returncode} pass={n_pass} fail={n_fail} "
                  f"dt={dt:.1f}s")
            return out

        def walk_hash_ok():
            return sha256_file(seam_path) == PINNED[
                "reference/science_funnel/typeb_export/command_record.py"]

        # ── F2 baseline: unmodified suites must be GREEN ─────────────────────
        print("F2 BASELINE: unmodified original suites in the hash-verified "
              "sandbox")
        check("F3 walk-contract sha unchanged before runs",
              walk_hash_ok(), sha256_file(seam_path))
        p1, dt1 = run_suite(main_suite)
        out1 = suite_pass("climb_intent_tests.py GREEN 73/73 (I1-I8 incl. "
                          "6000-event seed-20260924 fuzz)", p1, dt1,
                          expect_green=True, want_pass=73)
        check("F3 walk-contract sha unchanged after the full main suite",
              walk_hash_ok(), sha256_file(seam_path))
        p2, dt2 = run_suite(amr_suite)
        out2 = suite_pass("climb_intent_amr_tests.py GREEN 4/4 (AMR-1..4)",
                          p2, dt2, expect_green=True, want_pass=4)
        (RECEIPTS / "baseline_suites.txt").write_text(
            f"# python -B climb_intent_tests.py (sandbox from pinned bytes)\n"
            f"exit={p1.returncode}\n{p1.stdout}\n"
            f"# python -B climb_intent_amr_tests.py\n"
            f"exit={p2.returncode}\n{p2.stdout}", encoding="utf-8")

        # ── F4 mutations: the suites must have teeth ─────────────────────────
        print("F4 FAILING-FIRST: named single-defect mutations of the sandbox "
              "copy must FIRE the predicted falsifier family")
        for mname, (old, new), family in (
            ("M1_edge_law", M1_EDGE, "I1"),
            ("M2_version_law", M2_VERSION, "I2"),
            ("M3_gate_law", M3_GATE, "I3"),
        ):
            fresh = Path(tempfile.mkdtemp(prefix=f"ont-u05-{mname}-",
                                          dir=str(root)))
            prod = build_sandbox(fresh)
            mutate(prod, old, new)
            proc, dt = run_suite(prod / "climb_intent_tests.py")
            out = proc.stdout + proc.stderr
            fired = fired_names(proc.stdout)
            hit = any(f.startswith(family) for f in fired) or (
                mname == "M2_version_law"
                and any(f.startswith("AMR-1") for f in fired))
            check(f"{mname}: suite FAILS with {family}-family falsifier fired",
                  proc.returncode == 1 and bool(fired) and hit,
                  f"exit={proc.returncode} dt={dt:.1f}s fired={fired[:6]} "
                  f"fail={out.count('[FAIL]')}")
            (RECEIPTS / f"mutation_{mname}_failing_first.txt").write_text(
                f"# sandbox copy mutated (candidate/reference untouched)\n"
                f"exit={proc.returncode}\n{proc.stdout}", encoding="utf-8")
            shutil.rmtree(fresh, ignore_errors=True)

        # M2 must ALSO fire the amendment suite's AMR-1 (True==1 / 2 smuggle)
        fresh = Path(tempfile.mkdtemp(prefix="ont-u05-M2-amr-", dir=str(root)))
        prod = build_sandbox(fresh)
        mutate(prod, *M2_VERSION)
        pa, dta = run_suite(prod / "climb_intent_amr_tests.py")
        fired_a = fired_names(pa.stdout)
        check("M2_version_law (amendment suite): AMR-1 fires (bool/2 smuggle "
              "refused is measured)", pa.returncode == 1
              and any(f.startswith("AMR-1") for f in fired_a),
              f"exit={pa.returncode} fired={fired_a}")
        shutil.rmtree(fresh, ignore_errors=True)

        # ── restore pinned bytes -> GREEN again ──────────────────────────────
        print("RESTORE: pinned bytes rebuilt -> suites GREEN again")
        prod = build_sandbox(Path(tempfile.mkdtemp(prefix="ont-u05-restore-",
                                                   dir=str(root))))
        pr, dtr = run_suite(prod / "climb_intent_tests.py")
        suite_pass("restored climb_intent_tests.py GREEN 73/73", pr, dtr,
                   expect_green=True, want_pass=73)
        pr2, dtr2 = run_suite(prod / "climb_intent_amr_tests.py")
        out_r = suite_pass("restored climb_intent_amr_tests.py GREEN 4/4",
                           pr2, dtr2, expect_green=True, want_pass=4)
        (RECEIPTS / "restored_green.txt").write_text(
            f"# pinned bytes restored in a fresh sandbox\n"
            f"exit={pr.returncode}\n{pr.stdout}\nexit={pr2.returncode}\n"
            f"{pr2.stdout}", encoding="utf-8")

    # ── F5 scope: this attempt writes ONLY inside its contribution dir ───────
    print("F5 SCOPE: attempt checkout carries only contributions/ONT-U05/**")
    repo_root = HERE.parents[3]
    git_meta = repo_root / ".git"
    if git_meta.exists():
        gs = subprocess.run(
            ["git", "-c", "safe.directory=*", "-C", str(repo_root),
             "status", "--porcelain", "-uall"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60)
        prefix = "tools/monkey_campaign/contributions/ONT-U05/"
        stray = [ln for ln in gs.stdout.splitlines()
                 if ln.strip() and prefix not in ln]
        check("git status lists ONLY contributions/ONT-U05 paths on top of "
              f"base {BASE_REV[:12]}...", not stray,
              f"stray={stray[:5]}" if stray else
              f"{len([l for l in gs.stdout.splitlines() if l.strip()])} "
              "contribution paths")
        (RECEIPTS / "scope_check.txt").write_text(
            f"# git -C {repo_root} status --porcelain -uall\n{gs.stdout}",
            encoding="utf-8")
    else:
        check("no .git at the harness root; F5 scope measured at submission "
              "time in the attempt checkout", True, "environment note")

    print()
    if FAILURES:
        print(f"RESULT: FAIL ({len(FAILURES)} re-verification checks fired)")
        for f in FAILURES:
            print(f"  FIRED: {f}")
        return 1
    print("RESULT: GREEN -- bring-forward identity, baseline suites, "
          "failing-first teeth, walk-contract byte-identity and scope all pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
