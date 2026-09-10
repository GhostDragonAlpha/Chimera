"""CPU-only structural tests. These tests create no HWND and launch no engine."""
import ast
import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock

import owned_backdrop


HERE = Path(__file__).resolve().parent


def load_runner():
    spec = importlib.util.spec_from_file_location("native_visual_run_test", HERE / "native_visual_run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_runner()

    def test_declared_layout_and_watchdog_are_inherited(self):
        self.assertEqual(self.runner.LAYOUT_RECT, (64, 64, 1280, 720))
        self.assertEqual(self.runner.WATCHDOG_SECONDS, 10)

    def test_shutdown_order_requires_every_marker_in_order(self):
        good = "\n".join(self.runner.SHUTDOWN_MARKERS)
        self.assertTrue(self.runner.ordered_shutdown(good)[0])
        self.assertFalse(self.runner.ordered_shutdown("\n".join(reversed(self.runner.SHUTDOWN_MARKERS)))[0])
        self.assertFalse(self.runner.ordered_shutdown("\n".join(self.runner.SHUTDOWN_MARKERS[:-1]))[0])

    def test_capture_binding_names_both_owned_windows_and_artifacts(self):
        capture = {"sha256": "image", "captured_pid": 10, "captured_hwnd": 20}
        source = {"main_cpp_sha256": "main", "shader_manifest_sha256": "shaders"}
        engine = {"pid": 10, "hwnd": 20, "exe_sha256": "exe"}
        backdrop = {"pid": 30, "hwnd": 40, "title": "owned",
                    "class_name": "owned-class", "paint_revision": "v1"}
        bound = self.runner.bind_capture(capture, role="before", source=source,
                                         engine=engine, backdrop=backdrop)
        self.assertEqual(bound["engine"], engine)
        self.assertEqual(bound["backdrop"], backdrop)
        self.assertIs(bound["source"], source)

    def test_helper_has_window_specific_capture_and_no_desktop_capture(self):
        text = (HERE / "owned_backdrop.py").read_text(encoding="utf-8")
        ast.parse(text)
        self.assertIn("PrintWindow", text)
        self.assertIn("PW_CLIENTONLY", text)
        self.assertNotIn("ImageGrab", text)
        self.assertNotIn("BitBlt", text)
        self.assertNotIn("GetDesktopWindow", text)

    def test_close_refuses_an_hwnd_owned_by_another_process(self):
        with mock.patch.object(owned_backdrop.user, "IsWindow", return_value=True), \
                mock.patch.object(owned_backdrop, "hwnd_owner", return_value=999), \
                mock.patch.object(owned_backdrop.user, "PostMessageW") as post:
            with self.assertRaisesRegex(AssertionError, "owner mismatch"):
                owned_backdrop.post_owned_close(123, 456, "engine")
        post.assert_not_called()

    def test_runner_has_no_dyad_or_build_side_effect(self):
        text = (HERE / "native_visual_run.py").read_text(encoding="utf-8")
        ast.parse(text)
        self.assertIn('/glass', text)
        self.assertNotIn('capture_client(hwnd, proc.pid', text)
        for forbidden in ("senses.can_see", "watch_one", "cmake", "msbuild", "lms "):
            self.assertNotIn(forbidden, text.lower())

    def test_policy_correction_is_rule_zero_complete(self):
        text = (HERE / "PREREGISTRATION_CORRECTION.md").read_text(encoding="utf-8")
        for heading in ("**STATEMENT:**", "**PREDICTION:**", "**FALSIFIERS:**"):
            self.assertIn(heading, text)


if __name__ == "__main__":
    unittest.main()
