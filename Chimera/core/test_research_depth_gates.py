"""Standalone smoke test for the Research Depth Protocol gates added to scholar.py and
spiral_forks.py (no pytest -- matches this repo's existing convention). Run directly:

    python core/test_research_depth_gates.py

Read-only: every check here queries the DNA graph but never mutates it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scholar import classify_source_type, check_domain_diversity
from core.spiral_forks import is_reference_recognized, score_brief

FAKE_CITATION = "JPL Planetary Science Archive: Regolith Rheology Datasets v2.1"
REAL_CITATION = "NASA Technical Reports"


def test_classify_source_type():
    assert classify_source_type("https://www.reddit.com/r/unrealengine/x") == "community"
    assert classify_source_type("https://www.youtube.com/watch?v=x") == "video"
    assert classify_source_type("https://data.nasa.gov/report.pdf") == "technical_docs"
    assert classify_source_type("Some Campus Seed Source Name") == "technical_docs"


def test_check_domain_diversity():
    one = check_domain_diversity(["https://a.com/1", "https://a.com/2"])
    assert one["passed"] is False and len(one["distinct_domains"]) == 1
    three = check_domain_diversity(["https://a.com/1", "https://b.org/2", "https://c.net/3"])
    assert three["passed"] is True and len(three["distinct_domains"]) == 3


def test_fake_citation_not_recognized():
    """Direct regression test for the incident that motivated this change: a fabricated
    citation previously scored a full 20/20 in score_brief() unchecked."""
    assert is_reference_recognized(FAKE_CITATION) is False


def test_real_citation_recognized():
    assert is_reference_recognized(REAL_CITATION) is True


def test_score_brief_downgrades_unrecognized_reference():
    base = {"parameters": {"a": 1}, "campus_sources": ["x", "y"], "principles": ["p"],
            "emotional_anchor": "anchor", "acceptance_criteria": ["c"]}
    fake_score, fake_note = score_brief({**base, "canonical_reference": FAKE_CITATION})
    real_score, real_note = score_brief({**base, "canonical_reference": REAL_CITATION})
    assert "NOT recognized" in fake_note
    assert real_score - fake_score == 15  # +5 vs +20 on the canonical_reference gate
    print(f"  fake={fake_score}/100  real={real_score}/100  (delta {real_score - fake_score})")


if __name__ == "__main__":
    tests = [test_classify_source_type, test_check_domain_diversity,
             test_fake_citation_not_recognized, test_real_citation_recognized,
             test_score_brief_downgrades_unrecognized_reference]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL  {test.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
