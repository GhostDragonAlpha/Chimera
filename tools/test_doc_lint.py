import tempfile
import base64
import hashlib
import json
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


    def archive(self):
        raw = fixture_ref("retired.md").encode()
        return {"kind": "source", "document": {
            "original_path": fixture_ref("removed.md"),
            "authority": "imported_untrusted", "byte_count": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes_base64": base64.b64encode(raw).decode(), "text": raw.decode()}}

    def scan_json(self, value):
        self.src = self.root / "graph.json"
        return self.scan(json.dumps(value))

    def test_valid_archive_is_history_and_input_stays_unchanged(self):
        node = self.archive()
        before = json.dumps(node)
        self.assertEqual(self.scan_json({"objects": [node]}), [])
        self.assertEqual(json.dumps(node), before)

    def test_live_reference_next_to_archive_still_fails(self):
        node = self.archive()
        node["document"]["current_tool"] = fixture_ref("missing.py")
        result = self.scan_json({"objects": {"source.archive": node}})
        self.assertEqual([r["ref"] for r in result], [fixture_ref("missing.py")])

    def test_invalid_archival_bytes_or_text_do_not_hide_references(self):
        for key, value in (("byte_count", 0), ("bytes_base64", "!invalid"),
                           ("text", fixture_ref("forged.md"))):
            with self.subTest(field=key):
                node = self.archive()
                node["document"][key] = value
                self.assertTrue(self.scan_json(node))

    def test_active_or_untyped_prose_is_not_exempt(self):
        for mutation in ("active", "kind", "authority"):
            node = self.archive()
            if mutation == "active":
                node["project_spec"] = {"admission": "active_specification"}
            elif mutation == "kind":
                node["kind"] = "work"
            else:
                node["document"].pop("authority")
            self.assertTrue(self.scan_json(node))

    def test_ordinary_json_references_remain_checked(self):
        result = self.scan_json({"current": fixture_ref("absent.py")})
        self.assertEqual([r["ref"] for r in result], [fixture_ref("absent.py")])


if __name__ == "__main__":
    unittest.main()
