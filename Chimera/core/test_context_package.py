"""Standalone smoke test for core/context_package.py (no pytest -- matches this repo's
existing convention, e.g. test_wind_system_integration.py). Run directly:

    python core/test_context_package.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context_package import assemble_context_package

EXPECTED_KEYS = {
    "feature_name", "generated_by", "dsl_block", "graph_context",
    "campus_sources", "reference_images", "required_endpoints",
}


def test_returns_all_five_fields():
    package = assemble_context_package("Ground_Sand_Particles")
    missing = EXPECTED_KEYS - set(package.keys())
    assert not missing, f"missing keys: {missing}"
    assert isinstance(package["graph_context"], dict)
    assert "feature_type" in package["graph_context"]
    print(f"  feature_type={package['graph_context']['feature_type']}  "
          f"campus_sources={list(package['campus_sources'].keys())}")


def test_never_raises_on_unknown_feature():
    package = assemble_context_package("Totally_Unknown_Feature_Xyz")
    missing = EXPECTED_KEYS - set(package.keys())
    assert not missing, f"missing keys: {missing}"
    assert package["dsl_block"]["status"] == "not_found"


if __name__ == "__main__":
    tests = [test_returns_all_five_fields, test_never_raises_on_unknown_feature]
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
