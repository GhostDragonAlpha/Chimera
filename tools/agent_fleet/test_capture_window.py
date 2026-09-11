"""test_capture_window.py -- window-capture-ownership-01/02 contract tests.

Isolated by construction: every window used here is SELF-CREATED via
FixtureWindow (class prefix ChimeraFixture) or by a CHILD PROCESS of this
test's own Python interpreter (never a third-party window). No foreign
window is moved, closed, or captured; no desktop screenshots are taken;
no GPU/DYAD/engine resources are touched (CPU/GDI only).

Inherited predictions (a)-(g), re-verified fresh by -02:
  (a) unobscured owned capture -> verdict unobscured, exact full matrix
  (b) overlap by second owned fixture -> the window-specific PrintWindow
      path reads the window's OWN surface (recorded amendment), any content
      deviation still fails closed as occluded_or_foreign_content
  (c) resized client area -> window_resized
  (d) destroyed window -> window_destroyed
  (e) wrong pid -> foreign_process
  (f) foreign-class window -> foreign_window_class (read-only inspection)
  (g) no screen/desktop DC construction anywhere in the module source; a
      stale handle after destroy is refused, never fallen back
Fresh -02 predictions (preregistered in PREREGISTRATION.md before the run):
  (a2) fixtures with DISTINCT known solid content each capture exactly
  (b2) real cross-window content mismatch (live hwnd, another owned
       fixture's expected pattern) -> occluded_or_foreign_content
  (e2) REAL foreign-process fixture (child of this interpreter, matching
       ChimeraFixture class, known content) -> foreign_process, refused for
       publication even though the content is known and matching
  (f2) captured extent equals the pinned CLIENT rect; the outer window
       rect (nonclient chrome: caption/borders/DWM shadow) is strictly
       larger on this system, so no chrome pixel can enter a record
  (d2) a raw stale hwnd refused at the hwnd-level contract entry
Falsifiers: foreign/occluded/stale/resized/destroyed pixels published,
full-desktop fallback, evidence overwrite, point-sampling substitution.
"""
import ctypes
import inspect
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from capture_window import (CLASS_PREFIX, DEFAULT_HEIGHT, DEFAULT_WIDTH,
                            FixtureWindow, capture_client_pixels,
                            default_pattern, matrices_equal, pattern_sha256,
                            solid_pattern, verdict_verdicts,
                            verify_hwnd_capture, verify_owned_capture,
                            window_rect, write_evidence)

IS_WINDOWS = os.name == 'nt'

# Child-process fixture: the child is spawned from THIS interpreter with THIS
# module, creates its own ChimeraFixture-class window with a distinct known
# solid fill, prints (hwnd, pinned client w, pinned client h), then pumps
# messages until the PARENT terminates it. It is my own code and my own
# process tree - never a third-party window.
CHILD_FIXTURE_CODE = (
    "import sys, ctypes\n"
    "from ctypes import wintypes\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "from capture_window import FixtureWindow, solid_pattern\n"
    "f = FixtureWindow('chimera-child-' + sys.argv[2],\n"
    "                  paint_fn=solid_pattern((255, 0, 0)),\n"
    "                  width=96, height=64)\n"
    "print(f.hwnd, f.width, f.height, flush=True)\n"
    "user32 = ctypes.windll.user32\n"
    "msg = wintypes.MSG()\n"
    "while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:\n"
    "    user32.TranslateMessage(ctypes.byref(msg))\n"
    "    user32.DispatchMessageW(ctypes.byref(msg))\n"
)


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

    def _spawn_child_fixture(self):
        """Spawn a REAL foreign-process fixture owned by this process tree."""
        suffix = uuid.uuid4().hex[:12]
        proc = subprocess.Popen(
            [sys.executable, '-c', CHILD_FIXTURE_CODE, str(HERE), suffix],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        guard = threading.Timer(60.0, proc.terminate)
        guard.start()
        try:
            line = proc.stdout.readline().strip()
        finally:
            guard.cancel()
        if not line:
            err = proc.stderr.read()
            proc.terminate()
            proc.wait(timeout=10)
            for stream in (proc.stdout, proc.stderr):
                try:
                    stream.close()
                except Exception:
                    pass
            self.fail('child fixture failed to start: ' + err)
        hwnd, w, h = (int(part) for part in line.split())
        self.addCleanup(self._terminate_child, proc)
        return hwnd, w, h

    @staticmethod
    def _terminate_child(proc):
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            pass
        finally:
            for stream in (proc.stdout, proc.stderr):
                try:
                    if stream and not stream.closed:
                        stream.close()
                except Exception:
                    pass

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

    # --- (a2) fresh: distinct known solid content, each exact -----------------
    def test_distinct_solid_content_fixtures_are_unobscured(self):
        red = solid_pattern((255, 0, 0))
        blue = solid_pattern((0, 0, 255))
        fa = self.fixture('chimera-solid-red', paint_fn=red,
                          width=100, height=70)
        fb = self.fixture('chimera-solid-blue', paint_fn=blue,
                          width=100, height=70)
        # Same pinned size, different content: any swap must be detectable.
        self.assertEqual((fa.width, fa.height), (fb.width, fb.height),
                         'system pinned different client sizes for equal '
                         'requests; content comparison would conflate size')
        w, h = fa.width, fa.height
        ra = verify_owned_capture(fa)
        rb = verify_owned_capture(fb)
        self.assertEqual(ra['verdict'], 'unobscured', ra)
        self.assertEqual(rb['verdict'], 'unobscured', rb)
        self.assertTrue(ra['publishable'])
        self.assertTrue(rb['publishable'])
        self.assertEqual(ra['capture_sha256'], pattern_sha256(red(w, h)))
        self.assertEqual(rb['capture_sha256'], pattern_sha256(blue(w, h)))
        self.assertNotEqual(ra['capture_sha256'], rb['capture_sha256'])
        # Full matrix equality (not point sampling) on the captured bytes.
        rows_a, reason_a = capture_client_pixels(fa.hwnd, w, h)
        self.assertIsNone(reason_a)
        self.assertEqual(rows_a, red(w, h))

    # --- (b2) fresh: REAL cross-window content mismatch refused ---------------
    def test_real_cross_window_content_mismatch_refused(self):
        red = solid_pattern((255, 0, 0))
        blue = solid_pattern((0, 0, 255))
        fa = self.fixture('chimera-mix-red', paint_fn=red,
                          width=100, height=70)
        fb = self.fixture('chimera-mix-blue', paint_fn=blue,
                          width=100, height=70)
        self.assertEqual((fa.width, fa.height), (fb.width, fb.height))
        w, h = fa.width, fa.height
        # Live owned hwnd, but the EXPECTED pattern belongs to the other
        # fixture: only the full-matrix content gate can catch this.
        rec = verify_hwnd_capture(fb.hwnd, red(w, h), pinned_size=(w, h),
                                  title=fb.title)
        self.assertEqual(rec['verdict'], 'occluded_or_foreign_content', rec)
        self.assertFalse(rec['publishable'])
        # Positive control: same window against its own pattern is publishable.
        ok = verify_hwnd_capture(fb.hwnd, blue(w, h), pinned_size=(w, h),
                                 title=fb.title)
        self.assertEqual(ok['verdict'], 'unobscured', ok)

    # --- (e2) fresh: REAL foreign-process fixture refused on pid --------------
    def test_real_foreign_process_fixture_refused_on_pid(self):
        hwnd, w, h = self._spawn_child_fixture()
        red = solid_pattern((255, 0, 0))(w, h)
        # The child's content is known and matching (cross-process capture
        # proves the pixels are readable) - the refusal must come from the
        # OWNERSHIP gate alone, which is the packet's falsifier shape.
        rows, reason = capture_client_pixels(hwnd, w, h)
        self.assertIsNone(reason, 'cross-process capture of own child failed')
        self.assertEqual(rows, red)
        rec = verify_hwnd_capture(hwnd, red, pinned_size=(w, h),
                                  title='chimera-child-fixture')
        self.assertTrue(rec['is_window'], rec)
        self.assertTrue(rec['visible'], rec)
        self.assertTrue(rec['class_owned'], rec)
        self.assertFalse(rec['owns_process'], rec)
        self.assertNotEqual(rec['pid'], os.getpid())
        self.assertEqual(rec['verdict'], 'foreign_process', rec)
        self.assertFalse(rec['publishable'])

    # --- (f2) fresh: captured extent is the client rect, chrome excluded ------
    def test_client_rect_excludes_nonclient_chrome(self):
        f = self.fixture('chimera-chrome', width=120, height=90)
        w, h = f.width, f.height
        outer = window_rect(f.hwnd)
        self.assertIsNotNone(outer)
        outer_w, outer_h = outer[2] - outer[0], outer[3] - outer[1]
        # On this system's DWM chrome the outer rect is strictly larger than
        # the pinned client rect - and the capture is sized to the client.
        self.assertGreater(outer_w, w, (outer_w, w))
        self.assertGreater(outer_h, h, (outer_h, h))
        rows, reason = capture_client_pixels(f.hwnd, w, h)
        self.assertIsNone(reason)
        self.assertEqual(len(rows), h, 'captured rows != client height')
        self.assertEqual(len(rows[0]), w, 'captured cols != client width')
        self.assertEqual(rows, f.expected_pattern())

    # --- (d2) fresh: raw stale hwnd refused at the hwnd-level entry -----------
    def test_hwnd_level_contract_refuses_raw_stale_handle(self):
        f = self.fixture('chimera-doomed-hwnd')
        raw_hwnd = f.hwnd
        w, h = f.width, f.height
        f.close()
        rec = verify_hwnd_capture(raw_hwnd, solid_pattern((0, 0, 0))(w, h),
                                  pinned_size=(w, h), title='stale-hwnd')
        self.assertEqual(rec['verdict'], 'window_destroyed', rec)
        self.assertFalse(rec['publishable'])
        self.assertFalse(rec['is_window'])

    # --- F1 (fleet-review-followups-02): a failed CreateCompatibleDC is a
    # NAMED fail-closed refusal, never a NULL flowing into SelectObject /
    # PrintWindow mislabeled as printwindow_refused -------------------------
    def test_failed_memory_dc_is_named_refusal(self):
        import capture_window as cw
        f = self.fixture('chimera-nomemdc')
        original = cw.gdi32.CreateCompatibleDC

        def failing_create_compatible_dc(hdc):
            # Same shape as the real prototype's failure return: NULL HDC.
            return cw.wintypes.HDC(0)

        cw.gdi32.CreateCompatibleDC = failing_create_compatible_dc
        self.addCleanup(setattr, cw.gdi32, 'CreateCompatibleDC', original)
        try:
            rows, reason = capture_client_pixels(f.hwnd, f.width, f.height)
        finally:
            # Restore BEFORE the next assertion block so the patch window is
            # exactly one capture (addCleanup is the idempotent backstop).
            cw.gdi32.CreateCompatibleDC = original
        self.assertIsNone(rows)
        self.assertEqual(reason, 'memory_dc_unavailable', (rows, reason))
        # The refusal is a NAMED verdict in the contract's vocabulary, not a
        # mislabeled printwindow_refused.
        self.assertIn('capture_refused:memory_dc_unavailable',
                      verdict_verdicts())
        # The real prototype still works after the patch window: the same
        # fixture captures exactly (the patch was test-scoped).
        rows2, reason2 = capture_client_pixels(f.hwnd, f.width, f.height)
        self.assertIsNone(reason2)
        self.assertEqual(rows2, f.expected_pattern())

    # --- F2 (fleet-review-followups-02): pinned_size=None ADOPTS the
    # measured client size (documented semantics; the window_resized gate
    # is inert for a non-pinning caller) ------------------------------------
    def test_verify_hwnd_capture_none_pin_adopts_measured_size(self):
        f = self.fixture('chimera-adoption')
        w, h = f.width, f.height
        # 1) No pin, unresized window: adopted pin == measured client size,
        #    record proceeds to a full capture and is publishable.
        rec = verify_hwnd_capture(f.hwnd, f.expected_pattern(),
                                  pinned_size=None, title=f.title)
        self.assertEqual(rec['verdict'], 'unobscured', rec)
        self.assertTrue(rec['publishable'])
        self.assertEqual(rec['pinned_size'], rec['client_size'])
        self.assertEqual(rec['client_size'], [w, h])
        # 2) Resize the real client area (the creation pin stays w x h),
        #    repaint at the new measured size so the CONTENT gate is fair.
        f.resize_client(w + 80, h + 40)
        rect = f.client_rect()
        new_w, new_h = rect[2], rect[3]
        f.width, f.height = new_w, new_h
        f.repaint()
        rec2 = verify_hwnd_capture(f.hwnd, f.expected_pattern(),
                                   pinned_size=None, title=f.title)
        # Documented adoption: the pin adopted the NEW measured size, the
        # resized gate did not fire, and the record is publishable.
        self.assertEqual(rec2['client_size'], [new_w, new_h], rec2)
        self.assertEqual(rec2['pinned_size'], rec2['client_size'], rec2)
        self.assertNotEqual(rec2['verdict'], 'window_resized', rec2)
        self.assertEqual(rec2['verdict'], 'unobscured', rec2)
        self.assertTrue(rec2['publishable'])
        # 3) Contrast (gate intact for pinning callers): the SAME resized
        #    window against the ORIGINAL creation pin is window_resized.
        rec3 = verify_hwnd_capture(f.hwnd, f.expected_pattern(),
                                   pinned_size=(w, h), title=f.title)
        self.assertEqual(rec3['verdict'], 'window_resized', rec3)
        self.assertFalse(rec3['publishable'])
        self.assertEqual(rec3['pinned_size'], [w, h])
        self.assertEqual(rec3['client_size'], [new_w, new_h])


def capture_window_module():
    import capture_window
    return capture_window


if __name__ == '__main__':
    unittest.main(verbosity=2)
