import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PY = sys.executable


def run_review(base, candidate, outdir):
    p = subprocess.run(
        [PY, "-B", "tools/science_funnel/review_candidate.py",
         "--base", base, "--candidate", candidate, "--out", outdir],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p


class ReviewCandidate(unittest.TestCase):
    def test_checklist_loads(self):
        import tools.science_funnel.review_candidate as rc
        cfg = rc.load_checklist(os.path.join(ROOT, "tools", "science_funnel", "review_checklist.json"))
        for key in ("physics_paths", "frozen_markers", "receipt_required_keys"):
            self.assertIn(key, cfg)

    def test_friction_reproduces_known_findings(self):
        out = os.path.join(ROOT, "tools", "science_funnel", "validation", "review_e9c7bd5e")
        p = run_review("a6e6acf2", "e9c7bd5e", out)
        self.assertNotEqual(p.returncode, 0, "friction candidate must not PASS clean")
        with open(os.path.join(out, "verdict.json"), encoding="utf-8") as f:
            verdict = json.load(f)
        by_id = {c["id"]: c for c in verdict["checks"]}
        self.assertEqual(by_id["falsifier_as_test"]["status"], "FINDING")
        self.assertIn("F2", by_id["falsifier_as_test"]["detail"])
        self.assertIn("F3", by_id["falsifier_as_test"]["detail"])
        self.assertEqual(by_id["scope_honesty"]["status"], "FINDING")
        self.assertIn("F4", by_id["scope_honesty"]["detail"])
        self.assertIn("F1", json.dumps(by_id["falsifier_as_test"]))

    def test_docs_only_passes_without_false_positives(self):
        out = os.path.join(ROOT, "tools", "science_funnel", "validation", "review_4b047609")
        p = run_review("a4eaf574", "4b047609", out)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        with open(os.path.join(out, "verdict.json"), encoding="utf-8") as f:
            verdict = json.load(f)
        self.assertEqual(verdict["verdict"], "PASS")
        self.assertEqual(verdict["summary_counts"]["FINDING"], 0)


if __name__ == "__main__":
    unittest.main()
