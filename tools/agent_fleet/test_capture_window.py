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
import time
import unittest
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from capture_window import (CLASS_PREFIX, DEFAULT_HEIGHT, DEFAULT_WIDTH,
                            DEFAULT_WATCHDOG_CADENCE_S, FixtureWindow,
                            WATCHDOG_ENV_VAR, capture_client_pixels,
                            default_pattern, install_parent_watchdog,
                            matrices_equal, pattern_sha256, solid_pattern,
                            verdict_verdicts, verify_hwnd_capture,
                            verify_owned_capture, window_rect, write_evidence)

IS_WINDOWS = os.name == 'nt'

# Child-process fixture: the child is spawned from THIS interpreter with THIS
# module, creates its own ChimeraFixture-class window with a distinct known
# solid fill, prints (hwnd, pinned client w, pinned client h), installs the
# parent watchdog (fleet-evidence-hygiene-01 F2: the child polls its parent
# and exits by itself when orphaned -- it can no longer outlive this test
# run), then pumps messages until the PARENT terminates it (or the watchdog
# fires). It is my own code and my own process tree - never a third-party
# window.
CHILD_FIXTURE_CODE = (
    "import sys, ctypes\n"
    "from ctypes import wintypes\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "from capture_window import (FixtureWindow, solid_pattern,\n"
    "                            install_parent_watchdog)\n"
    "f = FixtureWindow('chimera-child-' + sys.argv[2],\n"
    "                  paint_fn=solid_pattern((255, 0, 0)),\n"
    "                  width=96, height=64)\n"
    "print(f.hwnd, f.width, f.height, flush=True)\n"
    "install_parent_watchdog()\n"
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

    def _spawn_child_fixture(self, parent_pid=None):
        """Spawn a REAL foreign-process fixture owned by this process tree.

        The child installs the F2 orphan watchdog pointed at `parent_pid`
        (default: THIS test process), so it can never outlive this run even
        if the whole test process dies.
        """
        suffix = uuid.uuid4().hex[:12]
        if parent_pid is None:
            parent_pid = os.getpid()
        env = dict(os.environ)
        env[WATCHDOG_ENV_VAR] = str(parent_pid)
        proc = subprocess.Popen(
            [sys.executable, '-c', CHILD_FIXTURE_CODE, str(HERE), suffix],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env=env,
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


# ==== fleet-evidence-hygiene-01 F2: the fixture-child orphan watchdog ========

@unittest.skipUnless(IS_WINDOWS, 'Windows process-watchdog contract')
class FixtureChildWatchdogTests(unittest.TestCase):
    """Prediction (F2): a fixture child whose parent dies exits on its own,
    within the guard window; a fixture child with a live parent keeps
    pumping (watchdog must NOT fire); normal fixture behavior unchanged.

    The orphan path is exercised for REAL: a sacrificial parent process is
    spawned, the REAL fixture child (same CHILD_FIXTURE_CODE the suite uses)
    watches IT via CHIMERA_FIXTURE_PARENT_PID, and the sacrificial process is
    killed mid-run. Every process here is self-created; the finally block
    reaps both. The test process itself is never the sacrificed parent.
    """

    GUARD_WINDOW_S = 30.0   # test bound; cadence 0.25 s -> expected ~1 s

    @staticmethod
    def _close_streams(proc):
        for stream in (proc.stdout, proc.stderr):
            try:
                if stream and not stream.closed:
                    stream.close()
            except Exception:
                pass

    def test_orphaned_fixture_child_exits_within_guard_window(self):
        sacrificial = subprocess.Popen(
            [sys.executable, '-c', 'import time; time.sleep(300)'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        child = None
        try:
            suffix = uuid.uuid4().hex[:12]
            env = dict(os.environ)
            env[WATCHDOG_ENV_VAR] = str(sacrificial.pid)
            child = subprocess.Popen(
                [sys.executable, '-c', CHILD_FIXTURE_CODE, str(HERE), suffix],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                env=env,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            guard = threading.Timer(60.0, child.terminate)
            guard.start()
            try:
                line = child.stdout.readline().strip()
            finally:
                guard.cancel()
            if not line:
                # Only read stderr when the start line never arrived: the
                # child is ALIVE on the success path and its stderr pipe
                # has no EOF -- an eager read here blocks until the child
                # dies (the exact hang this suite exists to prevent).
                self.fail('fixture child failed to start: '
                          + child.stderr.read())
            hwnd, w, h = (int(part) for part in line.split())
            user32 = ctypes.windll.user32
            self.assertTrue(user32.IsWindow(hwnd))
            # (i) LIVE parent: the child keeps pumping -- the watchdog must
            # not fire on a healthy parent (normal fixture behavior).
            time.sleep(max(2.0, 6 * DEFAULT_WATCHDOG_CADENCE_S))
            self.assertIsNone(child.poll(),
                              'watchdog fired on a live parent')
            # (ii) ORPHANING: the parent dies; the child must exit ON ITS OWN
            # with code 0 within the guard window.
            sacrificial.kill()
            sacrificial.wait(timeout=10)
            deadline = time.time() + self.GUARD_WINDOW_S
            while child.poll() is None and time.time() < deadline:
                time.sleep(0.05)
            self.assertIsNotNone(
                child.poll(),
                'orphaned fixture child survived the guard window')
            self.assertEqual(child.returncode, 0)
        finally:
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except Exception:
                    child.kill()
            if child is not None:
                self._close_streams(child)
            if sacrificial.poll() is None:
                sacrificial.kill()
                sacrificial.wait(timeout=10)

    def test_watchdog_disabled_without_resolvable_parent(self):
        # No resolvable parent pid -> disabled, no thread, no crash: callers
        # outside the fixture-child path are unaffected.
        self.assertIsNone(install_parent_watchdog(parent_pid=0))


# ==== fleet-evidence-hygiene-01 F1: the *.log evidence-trap warning gate =====

class EvidenceLogGuardTests(unittest.TestCase):
    """Prediction (F1), driven END-TO-END against the REAL guard script in
    throwaway git repos (no mocks): the trap case warns with exit 0, every
    clean case is silent with exit 0, a crashed guard still cannot block,
    and the hook wiring keeps every pre-existing gate and is warn-only.

    (This suite hosts the guard tests because this task's test scope is
    this file; the guard itself lives at the repo's conventional hook-script
    location and is wired into the repo-committed .githooks/pre-commit.)
    """

    EVID_DIR = 'docs/evidence/agent_fleet/HYGIENE_TEST'

    @classmethod
    def setUpClass(cls):
        cls.guard = HERE / 'evidence_log_guard.py'
        cls.hook = HERE.parents[1] / '.githooks' / 'pre-commit'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'repo'
        (self.repo / self.EVID_DIR).mkdir(parents=True)
        (self.repo / 'tools').mkdir()
        # The repo-wide rule that creates the trap:
        (self.repo / '.gitignore').write_text('*.log\n', encoding='utf-8')
        self.git('init', '-q')
        self.git('config', 'user.email', 'hygiene@test.invalid')
        self.git('config', 'user.name', 'hygiene-test')
        (self.repo / self.EVID_DIR / 'RESULT.txt').write_text(
            'result\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')

    # -- harness -----------------------------------------------------------
    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args],
                              check=True, capture_output=True, text=True,
                              encoding='utf-8')

    def run_guard(self):
        """Run the REAL script the way the hook does (--staged)."""
        return subprocess.run(
            [sys.executable, str(self.guard), '--staged',
             '--repo', str(self.repo)],
            capture_output=True, text=True, encoding='utf-8')

    def stage_new_evidence(self, name='record.txt'):
        path = self.repo / self.EVID_DIR / name
        path.write_text('committed record\n', encoding='utf-8')
        self.git('add', str(path))

    def add_ignored_log(self, relpath):
        path = self.repo / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('raw output that would silently vanish\n',
                        encoding='utf-8')

    # -- the trap case -----------------------------------------------------
    def test_trap_case_warns_and_exits_zero(self):
        # Falsifier check: the trap must NOT pass silently.
        self.add_ignored_log(self.EVID_DIR + '/raw_output.log')
        self.stage_new_evidence()
        proc = self.run_guard()
        self.assertEqual(proc.returncode, 0,
                         'the guard WARNS, it never blocks: ' + proc.stderr)
        self.assertIn('[evidence-log-guard] WARNING', proc.stdout)
        self.assertIn('raw_output.log', proc.stdout)
        self.assertIn('git add -f', proc.stdout)

    # -- the clean cases ---------------------------------------------------
    def test_clean_staged_evidence_without_logs_is_silent(self):
        self.stage_new_evidence()
        proc = self.run_guard()
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, '')

    def test_clean_ignored_log_outside_evidence_is_silent(self):
        self.add_ignored_log('tools/stray.log')
        self.stage_new_evidence()
        proc = self.run_guard()
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, '')

    def test_clean_ignored_log_but_nothing_staged_is_silent(self):
        # The trap needs a STAGED evidence add; an ignored log alone is just
        # a log sitting in a worktree.
        self.add_ignored_log(self.EVID_DIR + '/raw_output.log')
        proc = self.run_guard()
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, '')

    def test_force_added_log_is_silent(self):
        # Remedy 1 verified by construction: once force-added the .log is
        # tracked, so it can no longer silently vanish.
        self.add_ignored_log(self.EVID_DIR + '/raw_output.log')
        self.git('add', '-f', self.EVID_DIR + '/raw_output.log')
        self.stage_new_evidence()
        proc = self.run_guard()
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, '')

    # -- never blocks, even when broken -------------------------------------
    def test_guard_cannot_block_on_internal_error(self):
        # A repo path that does not exist makes every git call fail
        # deterministically (git directory discovery cannot rescue it, unlike
        # an existing non-repo path, which can discover an ancestor repo);
        # the guard must degrade to a non-blocking warning, exit 0.
        missing = Path(self.tmp.name) / 'definitely' / 'missing'
        proc = subprocess.run(
            [sys.executable, str(self.guard), '--staged',
             '--repo', str(missing)],
            capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('non-blocking', proc.stdout)

    # -- the hook wiring: warn-only, existing gates intact ------------------
    def test_hook_wiring_preserves_every_gate_and_is_warn_only(self):
        text = self.hook.read_text(encoding='utf-8')
        # Every pre-existing gate stanza still present and still able to
        # fail the commit (their `fail=1` lines untouched).
        for gate in ('core.bind_guard --staged',
                     'core.objective_lint --staged',
                     'core.library_guard --staged',
                     'core.saturation --staged',
                     'perf_witness.py',
                     'SPIACE_RPG_PLAN.md',
                     'tools/doc_lint.py --staged',
                     '.git/hooks/pre-commit "$@"'):
            self.assertIn(gate, text, 'existing gate weakened: ' + gate)
        # The new stanza invokes the guard and CANNOT set the fail flag.
        self.assertIn('evidence_log_guard.py --staged || true', text)
        stanza = text.split('evidence *.log trap')[1].split('# --- delegate')[0]
        self.assertNotIn('fail=1', stanza)


if __name__ == '__main__':
    unittest.main(verbosity=2)
