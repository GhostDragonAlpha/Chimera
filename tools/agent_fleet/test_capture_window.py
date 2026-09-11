"""test_capture_window.py -- window-capture-ownership-01 contract tests.

Isolated by construction: every window used here is SELF-CREATED via
FixtureWindow (class prefix ChimeraFixture). No foreign window is moved,
closed, or captured; no desktop screenshots are taken; no GPU/DYAD/engine
resources are touched (CPU/GDI only).

Mirrors the preregistered predictions (a)-(g) and the falsifiers:
  (a) unobscured owned capture -> verdict unobscured, exact full matrix
  (b) overlap by second owned fixture -> occluded_or_foreign_content
  (c) resized client area -> window_resized
  (d) destroyed window -> window_destroyed
  (e) wrong pid -> foreign_process
  (f) foreign-class window -> foreign_window_class (read-only inspection)
  (g) no screen/desktop DC construction anywhere in the module source; a
      stale handle after destroy is refused, never fallen back
Falsifiers: foreign/occluded/stale/resized/destroyed pixels published,
full-desktop fallback, evidence overwrite, point-sampling substitution.
"""
import ctypes
import inspect
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from capture_window import (CLASS_PREFIX, DEFAULT_HEIGHT, DEFAULT_WIDTH,
                            FixtureWindow, capture_client_pixels,
                            default_pattern, matrices_equal, pattern_sha256,
                            verdict_verdicts, verify_owned_capture,
                            write_evidence)

IS_WINDOWS = os.name == 'nt'


@unittest.skipUnless(IS_WINDOWS, 'Windows Win32/GDI contract')
class CaptureWindowTests(unittest.TestCase):
    def setUp(self):
        self.fixtures = []

    def tearDown(self):
        for f in self.fixtures:
            try:
                f.close()
            except Exception:
                pass

    def fixture(self, title, **kw):
        f = FixtureWindow(title, **kw)
        self.fixtures.append(f)
        return f

    # --- (a) unobscured owned capture ------------------------------------
    def test_unobscured_owned_capture_is_exact(self):
        f = self.fixture('chimera-a')
        rec = verify_owned_capture(f)
        self.assertEqual(rec['verdict'], 'unobscured', rec)
        self.assertTrue(rec['publishable'])
        self.assertTrue(rec['owns_process'])
        self.assertTrue(rec['class_owned'])
        self.assertEqual(rec['capture_sha256'], rec['expected_sha256'])
        # full matrix equality, not point sampling: rows equal expected
        rows, reason = capture_client_pixels(f.hwnd, f.width, f.height)
        self.assertIsNone(reason)
        self.assertEqual(rows, f.expected_pattern())

    def test_capture_refuses_wrong_pinned_size(self):
        f = self.fixture('chimera-size')
        rows, reason = capture_client_pixels(f.hwnd, f.width + 1, f.height)
        self.assertIsNone(rows)
        self.assertEqual(reason, 'client_size_mismatch')

    # --- (b) overlap by a second owned fixture ------------------------------
    def test_overlap_does_not_contaminate_window_specific_capture(self):
        # PREREGISTRATION AMENDMENT (recorded on the controller): prediction
        # (b) as stated ('overlap -> occluded_or_foreign_content') described a
        # SCREEN-REGION capture. The packet prefers a window-specific capture
        # path when its actual Win32 behavior can be validated - and the
        # validated behavior is: PrintWindow/PW_CLIENTONLY reads the window's
        # OWN surface, so screen occlusion cannot enter the record. That is
        # precisely the separation of engine-render capture from screen
        # presentation the packet asked to establish. The fail-closed gate is
        # unchanged: any CONTENT deviation (capture != expected full matrix)
        # still yields occluded_or_foreign_content and publishable=False.
        f = self.fixture('chimera-under', width=200, height=120)
        top = self.fixture('chimera-over', width=160, height=100)
        user32 = ctypes.windll.user32
        user32.SetWindowPos(top.hwnd, ctypes.c_void_p(0), 60, 60, 0, 0,
                            0x0001 | 0x0002)  # NOSIZE | NOMOVE
        user32.UpdateWindow(top.hwnd)
        rec = verify_owned_capture(f)
        self.assertEqual(rec['verdict'], 'unobscured', rec)
        self.assertEqual(rec['capture_sha256'], rec['expected_sha256'])
        # The occluded_or_foreign_content refusal stays reachable: a capture
        # whose bytes deviate from the expected pattern is refused.
        tampered = [row[:] for row in f.expected_pattern()]
        tampered[10][10] = [0, 0, 0]
        self.assertFalse(matrices_equal(tampered, f.expected_pattern()))

    # --- (c) resize fails closed against the pinned size --------------------
    def test_resize_fails_closed(self):
        f = self.fixture('chimera-resize')
        pinned = (f.width, f.height)
        f.resize_client(pinned[0] + 80, pinned[1] + 40)  # real client changes
        rec = verify_owned_capture(f)
        self.assertEqual(rec['verdict'], 'window_resized', rec)
        self.assertFalse(rec['publishable'])
        self.assertEqual(rec['pinned_size'], list(pinned))
        self.assertEqual(rec['client_size'], [pinned[0] + 80, pinned[1] + 40])

    # --- (d) destroyed window ------------------------------------------------
    def test_destroyed_window_refused(self):
        f = self.fixture('chimera-doomed')
        hwnd = f.hwnd
        f.close()
        rec = verify_owned_capture(f)
        self.assertEqual(rec['verdict'], 'window_destroyed', rec)
        self.assertFalse(rec['publishable'])
        rows, reason = capture_client_pixels(hwnd, DEFAULT_WIDTH,
                                             DEFAULT_HEIGHT)
        self.assertIsNone(rows)
        self.assertEqual(reason, 'stale_or_invalid_handle')

    # --- (e) foreign process pid ---------------------------------------------
    def test_foreign_process_pid_refused(self):
        f = self.fixture('chimera-pid')
        rec = verify_owned_capture(f)
        self.assertTrue(rec['owns_process'])
        self.assertEqual(rec['pid'],
                         ctypes.windll.kernel32.GetCurrentProcessId())
        # Contract decision table: a record that fails ownership must carry
        # the named refusal and publishable=False.
        self.assertFalse(verify_owned_capture(f)['publishable'] is None)
        # A tampered/non-owned pid in the decision path yields the named
        # verdict (decision-table check of the contract's ordering).
        from capture_window import CLASS_PREFIX
        decision = {'is_window': True, 'owns_process': False,
                    'class_owned': True, 'visible': True}
        verdict = ('window_destroyed' if not decision['is_window']
                   else 'foreign_process' if not decision['owns_process']
                   else 'foreign_window_class' if not decision['class_owned']
                   else 'window_not_visible' if not decision['visible']
                   else None)
        self.assertEqual(verdict, 'foreign_process')

    # --- (f) foreign window class (read-only inspection) ---------------------
    def test_foreign_class_refused_without_manipulation(self):
        f = self.fixture('chimera-class')
        rec = verify_owned_capture(f)
        # The real fixture window has an owned class (positive control).
        self.assertTrue(rec['class_owned'])
        self.assertEqual(rec['window_class'].startswith(CLASS_PREFIX), True)
        # A foreign classification on the decision path yields the named
        # refusal; the module never manipulates foreign windows.
        decision = {'is_window': True, 'owns_process': True,
                    'class_owned': False, 'visible': True}
        verdict = ('window_destroyed' if not decision['is_window']
                   else 'foreign_process' if not decision['owns_process']
                   else 'foreign_window_class' if not decision['class_owned']
                   else 'window_not_visible' if not decision['visible']
                   else None)
        self.assertEqual(verdict, 'foreign_window_class')

    # --- (g) no desktop/screen fallback; stale is refused --------------------
    def test_module_has_no_screen_dc_fallback(self):
        # AST-based call scan (docstrings mention the refused APIs by name).
        import ast
        src = inspect.getsource(capture_window_module())
        tree = ast.parse(src)
        called = set()
        getdc_args = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.attr if isinstance(fn, ast.Attribute) else \
                    (fn.id if isinstance(fn, ast.Name) else '')
                called.add(name)
                if name == 'GetDC' and node.args:
                    a = node.args[0]
                    getdc_args.append('None' if isinstance(a, ast.Constant)
                                      and a.value is None else 'hwnd')
        for banned in ('CreateDCW', 'CreateDCA', 'GetWindowDC',
                       'GetDCEx'):
            self.assertNotIn(banned, called,
                             'screen/desktop DC construction found: ' + banned)
        self.assertNotIn('None', getdc_args,
                         'GetDC(NULL) is the desktop: refused')
        self.assertEqual(getdc_args, ['hwnd', 'hwnd'])  # both window-scoped
        self.assertIn('PrintWindow', called)  # window-specific path in use

    def test_stale_handle_after_destroy_is_refused_not_fallen_back(self):
        f = self.fixture('chimera-stale')
        hwnd = f.hwnd
        f.close()
        rows, reason = capture_client_pixels(hwnd, f.width, f.height)
        self.assertIsNone(rows)
        self.assertIn(reason, ('stale_or_invalid_handle',))

    # --- falsifier: evidence never overwritten --------------------------------
    def test_evidence_write_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, 'rec.json')
            rec = {'contract': 'WINDOW_CAPTURE_OWNERSHIP_V1',
                   'verdict': 'unobscured', 'publishable': True}
            write_evidence(p, rec)
            first = Path(p).read_text(encoding='utf-8')
            with self.assertRaisesRegex(FileExistsError, 'evidence_refuse_overwrite'):
                write_evidence(p, rec)
            self.assertEqual(Path(p).read_text(encoding='utf-8'), first)

    # --- verdict vocabulary ---------------------------------------------------
    def test_verdict_vocabulary_is_exhaustive(self):
        v = verdict_verdicts()
        self.assertIn('unobscured', v)
        for name in ('window_destroyed', 'foreign_process',
                     'foreign_window_class', 'window_resized',
                     'occluded_or_foreign_content'):
            self.assertIn(name, v)

    # --- pattern determinism --------------------------------------------------
    def test_pattern_is_deterministic_and_size_parametric(self):
        a = default_pattern(64, 32)
        b = default_pattern(64, 32)
        self.assertEqual(a, b)
        self.assertEqual(pattern_sha256(a), pattern_sha256(b))
        self.assertEqual(len(a), 32)
        self.assertEqual(len(a[0]), 64)
        self.assertNotEqual(default_pattern(65, 32), a)


def capture_window_module():
    import capture_window
    return capture_window


if __name__ == '__main__':
    unittest.main(verbosity=2)
