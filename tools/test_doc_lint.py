import tempfile
import unittest
from pathlib import Path

import doc_lint as dl


def fixture_ref(name):
    # These paths are inputs rooted in each temporary fixture, not pointers
    # to files in the production checkout.
    return "/".join(("ChimeraEngine", "engine", name))


class HeaderPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_root = dl.ROOT
        dl.ROOT = self.root
        (self.root / "ChimeraEngine" / "engine").mkdir(parents=True)
        (self.root / "tools").mkdir()
        for name in ("http_server.hpp", "good.cpp", "good.py", "good.md"):
            (self.root / "ChimeraEngine" / "engine" / name).write_text("", encoding="utf-8")
        (self.root / "tools" / "good.py").write_text("", encoding="utf-8")
        self.src = self.root / "doc.md"

    def tearDown(self):
        dl.ROOT = self.old_root
        self.tmp.cleanup()

    def scan(self, text):
        broken = []
        dl.scan_text(text, self.src, [], broken)
        return broken

    def test_existing_hpp_and_supported_files_pass(self):
        text = " ".join(fixture_ref(n) for n in
                        ("http_server.hpp.", "good.cpp", "good.py", "good.md"))
        self.assertEqual(self.scan(text), [])

    def test_missing_headers_and_full_path_prefix_fail(self):
        broken = self.scan(" ".join(fixture_ref(n) for n in
                                   ("http_server.h;", "missing.hpp.", "missing.cpp")))
        self.assertEqual({x["ref"] for x in broken}, {
            fixture_ref("http_server.h"),
            fixture_ref("missing.hpp"),
            fixture_ref("missing.cpp"),
        })

    def test_extension_prefix_is_not_truncated(self):
        self.assertEqual(self.scan(fixture_ref("http_server.hxx")), [])
        self.assertEqual(self.scan(fixture_ref("missing.py.")),
                         [{"file": "doc.md", "ref": fixture_ref("missing.py"), "kind": "path"}])

    def test_relative_markdown_links_still_apply(self):
        (self.root / "linked.md").write_text("", encoding="utf-8")
        self.assertEqual(self.scan("](linked.md)"), [])
        self.assertEqual(self.scan("](missing.md)"),
                         [{"file": "doc.md", "ref": "missing.md", "kind": "md-link"}])


if __name__ == "__main__":
    unittest.main()
