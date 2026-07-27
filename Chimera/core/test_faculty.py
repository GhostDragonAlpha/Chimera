"""Standalone assert-script for core/faculty.py (repo non-pytest convention).
Run: python core/test_faculty.py

A fake constitution and a temp curriculum copy are env-redirected BEFORE import,
so propose/promote are exercised against controlled scars and a writable
curriculum without touching the real ones.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="chimera_faculty_test_"))
_fake_claude = _tmp / "CLAUDE.md"
_fake_curr = _tmp / "curriculum.json"
_pending = _tmp / "pending.json"
os.environ["CHIMERA_CONSTITUTION"] = str(_fake_claude)
os.environ["CHIMERA_CURRICULUM_PATH"] = str(_fake_curr)
os.environ["CHIMERA_FACULTY_PENDING"] = str(_pending)

# A constitution with three scars, one already an exam in the curriculum below.
_fake_claude.write_text(
    "## Heuristics\n"
    "- **[H-91, auto-promoted]** A C2039 missing-member error means template drift; "
    "emit the accessor in the same change.\n"
    "- **[H-92, auto-promoted]** Never verify from desktop screenshots — capture via "
    "control_editor screenshot mode=editor_viewport.\n"
    "- **[H-93, auto-promoted]** Telemetry commands that fall back to hardcoded "
    "defaults indicate missing SandSoundComponent integration at runtime.\n",
    encoding="utf-8")

# Minimal curriculum: bachelor + master bands; H-91 already pinned in an existing
# checkpoint so the Faculty must NOT re-propose it. Pristine copy is restored
# before every test because promote() mutates the file on disk.
PRISTINE_CURRICULUM = {"bands": [
    {"band": "bachelor", "min_role": "initiate", "courses": [
        {"discipline": "eng", "title": "Eng", "checkpoints": [
            {"id": "ba.x", "prompt": "For <feature>, apply H-91 to its build.",
             "artifact": "ba_x.md", "verify": [{"type": "artifact", "min_chars": 10}]}]}]},
    {"band": "master", "min_role": "journeyman", "courses": [
        {"discipline": "vision", "title": "Vision", "checkpoints": [
            {"id": "ma.x", "prompt": "<feature> vision.", "artifact": "ma_x.md",
             "verify": [{"type": "artifact", "min_chars": 10}]}]}]},
]}
_fake_curr.write_text(json.dumps(PRISTINE_CURRICULUM), encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import faculty as fac   # noqa: E402
from core import curriculum as cu  # noqa: E402


def _reset_pending():
    """Restore pristine state: promote() mutates BOTH the pending file and the
    curriculum file on disk, so both must reset for cross-test isolation."""
    if _pending.exists():
        _pending.unlink()
    _fake_curr.write_text(json.dumps(PRISTINE_CURRICULUM), encoding="utf-8")


def test_proposes_only_uncovered_scars():
    _reset_pending()
    added = fac.propose()
    ids = {a["checkpoint"]["id"] for a in added}
    # H-91 is already pinned in ba.x -> must NOT be proposed; H-92, H-93 must be.
    assert "fac.h-91" not in ids, "already-pinned scar must not be re-proposed"
    assert {"fac.h-92", "fac.h-93"} <= ids, f"uncovered scars missing: {ids}"
    # H-92 mentions the viewport/screenshot -> routed to master (vision band).
    h92 = next(a for a in added if a["checkpoint"]["id"] == "fac.h-92")
    assert h92["band"] == "master", f"screenshot scar should route to master: {h92['band']}"


def test_word_boundary_pinning():
    # The must_match for H-9 must not be satisfiable by H-91/H-92 substrings.
    _reset_pending()
    fac.propose()
    h93 = next(p for p in fac._read_pending()["proposed"]
               if p["checkpoint"]["id"] == "fac.h-93")
    pats = h93["checkpoint"]["verify"][0]["must_match"]
    # re.escape renders the dash as \- ; the point is the \b...\b word boundary
    assert any(p.startswith(r"\b") and "93" in p and p.endswith(r"\b") for p in pats), \
        f"H-93 must be word-boundary pinned: {pats}"
    import re as _re
    h93_pat = next(p for p in pats if "93" in p)
    assert _re.search(h93_pat, "applies H-93 here") and not _re.search(h93_pat, "H-931"), \
        "boundary must match H-93 but not H-931"
    # a distinctive token from the rule (SandSoundComponent) became a required cite
    assert any("SandSoundComponent" in p for p in pats), pats


def test_propose_is_idempotent():
    _reset_pending()
    first = fac.propose()
    second = fac.propose()
    assert first and second == [], "second propose must add nothing"


def test_every_proposal_is_engine_gradable():
    _reset_pending()
    fac.propose(from_surprises=False)
    rows = fac.lint()
    assert rows and all(ok for _, ok, _ in rows), f"ungradable proposals: {rows}"


def test_promote_is_the_gate_and_lands_in_curriculum():
    _reset_pending()
    fac.propose()
    cp = fac.promote("fac.h-92")
    # it now lives in the master band under a faculty course, and lints clean
    real = json.loads(_fake_curr.read_text(encoding="utf-8"))
    master = next(b for b in real["bands"] if b["band"] == "master")
    fac_course = next(c for c in master["courses"] if c["discipline"] == "faculty")
    got = next(c for c in fac_course["checkpoints"] if c["id"] == "fac.h-92")
    assert got["provenance"]["source_id"] == "H-92", "promoted exam must remember its scar"
    # curriculum still lints (unique ids, artifact, verify, <feature> in prompt)
    ids = [c["id"] for b in real["bands"] for co in b["courses"] for c in co["checkpoints"]]
    assert len(ids) == len(set(ids)), "promotion must not create duplicate ids"
    # double promote refused
    try:
        fac.promote("fac.h-92")
        assert False, "double promote must refuse"
    except ValueError:
        pass


def test_veto_blocks_promotion_until_forced():
    _reset_pending()
    fac.propose()
    fac.veto("fac.h-93", note="too vague")
    try:
        fac.promote("fac.h-93")
        assert False, "vetoed proposal must not promote"
    except ValueError as e:
        assert "vetoed" in str(e)
    forced = fac.promote("fac.h-93", force=True)
    assert forced["id"] == "fac.h-93", "force overrides the veto"


def test_stats_reports_the_coverage_gap():
    _reset_pending()
    s = fac.stats()
    assert s["h_rules_total"] == 3
    assert "H-92" in s["uncovered_ids"] and "H-91" not in s["uncovered_ids"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        _reset_pending()
        fn()
        print(f"  PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} faculty tests passed")
