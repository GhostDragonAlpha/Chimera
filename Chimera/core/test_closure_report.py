"""Standalone assert-script for core/closure_report.py (repo non-pytest convention).
Run: python core/test_closure_report.py

Exercises the MECHANICAL layer (layer 1: could_not_verify / build-evidence /
witness resolution) plus the 2026-07-18 FOOTPRINT SCOPING fix (tb-0182): a
CONCURRENT session's sibling Source/ dirt must never trigger THIS task's
build-evidence demand (or pollute the Coin's tails), while the task's OWN
footprint changes still must.

Git ops are redirected to a REAL throwaway repo (closure_report.REPO is
monkeypatched) so `_git()`'s subprocess calls exercise real git plumbing
without ever touching the live E:\\PythonChimera checkout — this is a fixture
for the deterministic mechanical layer + the log shape it hands the Coin, not
a test of git itself or of LM Studio (the Coin's `judge()` is stubbed; the
LIVE `_capcom` is stubbed so a test run never writes to the real capcom.db).
"""
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import closure_report as cr  # noqa: E402

_ORIG_REPO = cr.REPO
_ORIG_CAPCOM = cr._capcom
_ORIG_RESOLVE = cr._resolve


def _run(*args, cwd):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, f"git {args} failed: {r.stdout}\n{r.stderr}"
    return r.stdout


def _write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="seconds")


def _new_repo() -> Path:
    """A throwaway REPO (E:\\PythonChimera-shaped) with a Chimera/ subdir
    (ROOT-shaped) and one baseline commit, so pathspecs like 'Chimera/Source/'
    and footprint globs like 'core/a.py' resolve exactly as they do live."""
    tmp = Path(tempfile.mkdtemp(prefix="chimera_closure_report_test_"))
    _run("init", "-q", cwd=tmp)
    _run("config", "user.email", "test@test", cwd=tmp)
    _run("config", "user.name", "test", cwd=tmp)
    _run("config", "commit.gpgsign", "false", cwd=tmp)
    _write(tmp / "Chimera" / "core" / "a.py", "print('a v1')\n")
    _write(tmp / "Chimera" / "Source" / "Chimera" / "Foo" / "Foo.cpp", "// v1\n")
    _run("add", "-A", cwd=tmp)
    _run("commit", "-q", "-m", "baseline", cwd=tmp)
    return tmp


def _patch_repo(tmp: Path):
    cr.REPO = tmp


def _reset():
    cr._capcom = lambda *a, **k: None  # never touch the live capcom.db from a fixture
    cr._resolve = _ORIG_RESOLVE


def test_no_footprint_declared_preserves_old_behavior():
    """No resources.files at all -> everything under Source/ counts (the
    conservative default: unscoped tasks keep the OLD, stricter behavior)."""
    _reset()
    tmp = _new_repo()
    _patch_repo(tmp)
    sha = cr.head_sha()
    _write(tmp / "Chimera" / "Source" / "Chimera" / "Foo" / "Foo.cpp", "// v2 dirty\n")
    session = {"head_sha": sha, "entered_at": None, "baseline_dirty": []}
    changes = cr.source_changes(session, task=None)
    assert changes["files"] == ["Chimera/Source/Chimera/Foo/Foo.cpp"], changes
    assert changes["outside_footprint"] == []


def test_sibling_source_dirt_outside_footprint_does_not_demand():
    """The recipe's own example: footprint core/a.py, sibling dirt in
    Source/b.cpp (a CONCURRENT session's file) -> zero files, no demand."""
    _reset()
    tmp = _new_repo()
    _patch_repo(tmp)
    sha = cr.head_sha()
    task = {"id": "tb-X", "resources": {"files": ["core/a.py"]}}
    # a SIBLING task's concurrent, uncommitted edit under Source/ — not X's:
    _write(tmp / "Chimera" / "Source" / "b.cpp", "// sibling wrote this\n")
    session = {"head_sha": sha, "entered_at": None, "baseline_dirty": []}
    changes = cr.source_changes(session, task)
    assert changes["files"] == [], f"sibling dirt must not count as X's own: {changes}"
    assert changes["outside_footprint"] == ["Chimera/Source/b.cpp"], changes
    assert changes["newest_ts"] == 0.0, "no in-footprint change -> no demand-driving stamp"


def test_own_footprint_source_change_still_demands():
    """A touching Source/** itself (inside its OWN declared footprint) still
    demands build evidence — the fix narrows the net, it does not empty it."""
    _reset()
    tmp = _new_repo()
    _patch_repo(tmp)
    sha = cr.head_sha()
    task = {"id": "tb-X", "resources": {"files": ["Source/Chimera/Foo/**"]}}
    _write(tmp / "Chimera" / "Source" / "Chimera" / "Foo" / "Foo.cpp", "// v2 own change\n")
    session = {"head_sha": sha, "entered_at": None, "baseline_dirty": []}
    changes = cr.source_changes(session, task)
    assert changes["files"] == ["Chimera/Source/Chimera/Foo/Foo.cpp"], changes
    assert changes["newest_ts"] > 0.0


def test_mixed_own_and_sibling_change_splits_both_ways():
    """Both an in-footprint AND a sibling out-of-footprint file are dirty at
    once: the demand must be driven ONLY by the in-footprint one."""
    _reset()
    tmp = _new_repo()
    _patch_repo(tmp)
    sha = cr.head_sha()
    task = {"id": "tb-X", "resources": {"files": ["Source/Chimera/Foo/**"]}}
    _write(tmp / "Chimera" / "Source" / "Chimera" / "Foo" / "Foo.cpp", "// mine\n")
    # NB: a brand-new subdirectory (e.g. a never-before-seen 'Bar/') collapses
    # to one directory line under default `git status --porcelain` (pre-
    # existing git behavior, unrelated to this fix) — use a file directly
    # inside the ALREADY-tracked Source/Chimera/ dir so it reports per-file.
    _write(tmp / "Chimera" / "Source" / "Chimera" / "Bar.cpp", "// sibling's\n")
    session = {"head_sha": sha, "entered_at": None, "baseline_dirty": []}
    changes = cr.source_changes(session, task)
    assert changes["files"] == ["Chimera/Source/Chimera/Foo/Foo.cpp"], changes
    assert changes["outside_footprint"] == ["Chimera/Source/Chimera/Bar.cpp"], changes


def test_baseline_dirty_still_excluded_within_footprint():
    """Pre-existing dirt (untouched again this session) stays excluded even
    when it IS inside the footprint — regression: the baseline-dirt check
    must survive the footprint-scoping rewrite."""
    _reset()
    tmp = _new_repo()
    _patch_repo(tmp)
    sha = cr.head_sha()
    task = {"id": "tb-X", "resources": {"files": ["Source/Chimera/Foo/**"]}}
    _write(tmp / "Chimera" / "Source" / "Chimera" / "Foo" / "Foo.cpp",
           "// pre-existing dirt, not touched again by this session\n")
    entered = _iso(time.time() + 5)  # session "entered" AFTER this dirt appeared
    session = {"head_sha": sha, "entered_at": entered,
               "baseline_dirty": ["Chimera/Source/Chimera/Foo/Foo.cpp"]}
    changes = cr.source_changes(session, task)
    assert changes["files"] == [], f"baseline dirt must stay excluded: {changes}"
    assert changes["outside_footprint"] == [], changes


def test_action_log_segregates_outside_footprint_section():
    """action_log()'s text must show the in-footprint stat under its normal
    label AND the sibling under a distinct 'outside footprint (concurrent
    sessions)' section — nothing hidden, but clearly split."""
    _reset()
    tmp = _new_repo()
    _patch_repo(tmp)
    sha = cr.head_sha()
    task = {"id": "tb-X", "resources": {"files": ["core/a.py"]}}
    _write(tmp / "Chimera" / "core" / "a.py", "print('a v2 - mine')\n")
    _write(tmp / "Chimera" / "Source" / "b.cpp", "// sibling's concurrent edit\n")
    session = {"head_sha": sha, "entered_at": None, "baseline_dirty": []}
    log = cr.action_log(session, task)
    assert "outside footprint (concurrent sessions)" in log, log
    assert "Chimera/Source/b.cpp" in log, log
    assert "core/a.py" in log, log
    working_idx = log.index("working tree")
    outside_idx = log.index("outside footprint")
    assert outside_idx > working_idx, log
    assert "Chimera/Source/b.cpp" not in log[:outside_idx], \
        "sibling path leaked into the in-footprint section:\n" + log


def test_validate_no_longer_demands_build_for_sibling_only_dirt():
    """End-to-end through validate(): a task whose OWN footprint never
    touches Source/ must pass with no build-evidence citation even while a
    concurrent sibling's Source/ file sits dirty on disk."""
    _reset()
    tmp = _new_repo()
    _patch_repo(tmp)
    sha = cr.head_sha()
    task = {"id": "tb-X", "title": "docs-only task", "recipe": "edit core/a.py",
            "resources": {"files": ["core/a.py"]}}
    _write(tmp / "Chimera" / "core" / "a.py", "print('mine')\n")
    _write(tmp / "Chimera" / "Source" / "b.cpp", "// sibling concurrent session\n")
    session = {"head_sha": sha, "entered_at": None, "baseline_dirty": []}
    status, detail, report = cr.validate(task, session, result="edited core/a.py",
                                          could_not_verify="none")
    assert status == "pass", f"must pass without build evidence: {detail}"
    assert report["validated"]["build"] == "n/a (no Source changes)"
    assert report["source_changes_outside_footprint"] == ["Chimera/Source/b.cpp"]


def test_validate_still_blocks_when_footprint_source_change_unevidenced():
    """Regression: a task whose OWN footprint DOES include Source/ and DOES
    touch it must still be refused without build evidence — the fix must not
    have widened the exemption."""
    _reset()
    tmp = _new_repo()
    _patch_repo(tmp)
    sha = cr.head_sha()
    task = {"id": "tb-X", "title": "engine change",
            "resources": {"files": ["Source/Chimera/Foo/**"]}}
    _write(tmp / "Chimera" / "Source" / "Chimera" / "Foo" / "Foo.cpp", "// change\n")
    session = {"head_sha": sha, "entered_at": None, "baseline_dirty": []}
    status, detail, report = cr.validate(task, session, result="changed Foo.cpp",
                                          could_not_verify="none")
    assert status == "missing", f"must refuse without build evidence: {detail}"
    assert "build_evidence names no graph node" in detail


def test_validate_passes_with_fresh_passing_build_scoped_to_footprint():
    """A real fresh, passing build_evidence resolves the demand even while a
    concurrent sibling's Source/ dirt sits outside the footprint."""
    _reset()
    tmp = _new_repo()
    _patch_repo(tmp)
    sha = cr.head_sha()
    task = {"id": "tb-X", "resources": {"files": ["Source/Chimera/Foo/**"]}}
    _write(tmp / "Chimera" / "Source" / "Chimera" / "Foo" / "Foo.cpp", "// change\n")
    _write(tmp / "Chimera" / "Source" / "Sibling.cpp", "// concurrent sibling\n")
    session = {"head_sha": sha, "entered_at": None, "baseline_dirty": []}
    future_iso = _iso(time.time() + 3600)
    cr._resolve = lambda nid: ({"id": nid, "error_signature": "success_no_error",
                                "timestamp": future_iso} if nid == "mut_good" else None)
    status, detail, report = cr.validate(task, session, result="built + verified",
                                          build_evidence="mut_good",
                                          could_not_verify="none")
    assert status == "pass", detail
    assert report["validated"]["build"] == "ok"


def test_could_not_verify_mandatory_regression():
    _reset()
    tmp = _new_repo()
    _patch_repo(tmp)
    sha = cr.head_sha()
    task = {"id": "tb-X", "resources": {"files": ["core/a.py"]}}
    session = {"head_sha": sha, "entered_at": None, "baseline_dirty": []}
    status, detail, report = cr.validate(task, session, result="did stuff")
    assert status == "missing" and "could_not_verify is required" in detail


def test_witness_demand_regression():
    _reset()
    tmp = _new_repo()
    _patch_repo(tmp)
    sha = cr.head_sha()
    task = {"id": "tb-X", "title": "run beats for X", "recipe": "dispatch beats.json",
            "resources": {"files": ["core/a.py"]}}
    session = {"head_sha": sha, "entered_at": None, "baseline_dirty": []}
    status, detail, report = cr.validate(task, session, result="ran the beats",
                                          could_not_verify="none")
    assert status == "missing" and "demands a witness" in detail


def test_brain_judgment_tails_carries_footprint_scoped_log():
    """The Coin's tails face must be built from the SCOPED action_log, not a
    raw repo-wide diff — stub the LM call and inspect what it was handed."""
    _reset()
    tmp = _new_repo()
    _patch_repo(tmp)
    sha = cr.head_sha()
    task = {"id": "tb-X", "resources": {"files": ["core/a.py"]}}
    _write(tmp / "Chimera" / "core" / "a.py", "print('mine')\n")
    _write(tmp / "Chimera" / "Source" / "b.cpp", "// sibling\n")
    session = {"head_sha": sha, "entered_at": None, "baseline_dirty": []}
    _, _, report = cr.validate(task, session, result="edited core/a.py",
                                could_not_verify="none")
    import core.coin_verifier as cv
    orig_judge = cv.judge
    captured = {}

    def _fake_judge(heads, tails, *a, **k):
        captured["tails"] = tails
        return {"verdict": "MATCH"}

    cv.judge = _fake_judge
    try:
        out = cr.brain_judgment(report, task)
        assert out == {"verdict": "MATCH"}
        assert "outside footprint (concurrent sessions)" in captured["tails"]
        assert "Chimera/Source/b.cpp" in captured["tails"]
    finally:
        cv.judge = orig_judge


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  PASS {fn.__name__}")
    cr.REPO = _ORIG_REPO
    cr._capcom = _ORIG_CAPCOM
    cr._resolve = _ORIG_RESOLVE
    print(f"\n{len(fns)}/{len(fns)} closure_report tests passed")
