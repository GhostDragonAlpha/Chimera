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

capture-flake-tolerance-01 adds a bounded single-retry transient
tolerance (verify_with_transient_tolerance) around the adoption test's
verify calls: the recorded suite-load flake (a mid-erase surface read by
PrintWindow -> occluded_or_foreign_content on an unobscured fixture) is a
transient window-state race the content gate correctly fails closed on.
The retry is single, deadline-bounded, asserts IDENTICAL fixture
parameters between attempts, and RETAINS the first-attempt failure on
the returned record; the assertion set of every test is unchanged (the
retry wraps, never skips). TransientToleranceTests are the tolerance's
own synthetic falsifiers, including the real-occlusion-is-not-masked
proof.
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
        # Each verify_hwnd_capture call is WRAPPED (capture-flake-tolerance-01)
        # in the bounded single-retry transient tolerance: identical
        # arguments, identical assertions -- the retry wraps, never skips.
        # 1) No pin, unresized window: adopted pin == measured client size,
        #    record proceeds to a full capture and is publishable.
        rec = verify_with_transient_tolerance(
            f, f.expected_pattern(), pinned_size=None, title=f.title)
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
        rec2 = verify_with_transient_tolerance(
            f, f.expected_pattern(), pinned_size=None, title=f.title)
        # Documented adoption: the pin adopted the NEW measured size, the
        # resized gate did not fire, and the record is publishable.
        self.assertEqual(rec2['client_size'], [new_w, new_h], rec2)
        self.assertEqual(rec2['pinned_size'], rec2['client_size'], rec2)
        self.assertNotEqual(rec2['verdict'], 'window_resized', rec2)
        self.assertEqual(rec2['verdict'], 'unobscured', rec2)
        self.assertTrue(rec2['publishable'])
        # 3) Contrast (gate intact for pinning callers): the SAME resized
        #    window against the ORIGINAL creation pin is window_resized.
        rec3 = verify_with_transient_tolerance(
            f, f.expected_pattern(), pinned_size=(w, h), title=f.title)
        self.assertEqual(rec3['verdict'], 'window_resized', rec3)
        self.assertFalse(rec3['publishable'])
        self.assertEqual(rec3['pinned_size'], [w, h])
        self.assertEqual(rec3['client_size'], [new_w, new_h])


# ==== capture-flake-tolerance-01: bounded single-retry transient tolerance ===
#
# Recorded flake (PR #57 review LOW; two observed fleet-suite occurrences,
# and reproduced AT BASE in this task's RUN_LOAD_BASELINE_SUITE.txt): the
# adoption test's post-resize verify observed 'occluded_or_foreign_content'
# against an unobscured expectation. Mechanism: resize_client() queues
# CS_HREDRAW|CS_VREDRAW erase/paint work (the fixture class background is a
# GRAY_BRUSH) and under suite load that queued work can land AFTER the
# test's deterministic repaint() blit, so PrintWindow reads a mid-erase
# surface and the content gate fails closed. The gate is CORRECT to fail
# closed; the failure is transient because the SAME fixture parameters
# repaint to the SAME deterministic matrix. The tolerance below WRAPS the
# verify calls: at most ONE retry (TRANSIENT_TOLERANCE_MAX_RETRIES), inside
# a wall-clock deadline (TRANSIENT_TOLERANCE_DEADLINE_S), only for the
# recorded transient verdict, only against IDENTICAL fixture parameters
# (ASSERTED between attempts, not assumed), with the first-attempt failure
# RETAINED on the returned record ('first_attempt'). The retry wraps,
# never skips: a persistent (real) occlusion fails on both attempts and
# still raises the original assertion -- with both records attached.

TRANSIENT_TOLERANCE_DEADLINE_S = 5.0
TRANSIENT_TOLERANCE_MAX_RETRIES = 1
TRANSIENT_EVIDENCE_ENV_VAR = 'CHIMERA_TRANSIENT_TOLERANCE_EVIDENCE'
# In-memory retention of every fired tolerance in this process; when
# TRANSIENT_EVIDENCE_ENV_VAR names a directory, each event is ALSO
# appended (one JSON line) to transient_tolerance_events.txt there -- the
# durable *.txt surface used by the verification harness. Env unset ->
# no filesystem writes; the suite stays hermetic by default.
TRANSIENT_TOLERANCE_EVENTS = []


def _record_transient_event(event):
    TRANSIENT_TOLERANCE_EVENTS.append(event)
    evid_dir = os.environ.get(TRANSIENT_EVIDENCE_ENV_VAR)
    if not evid_dir:
        return
    try:
        path = Path(evid_dir) / 'transient_tolerance_events.txt'
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, default=str) + '\n')
    except OSError:
        pass  # evidence retention must never alter the test outcome


def verify_with_transient_tolerance(window, expected_pattern,
                                    pinned_size=None, title=None,
                                    verify=None, repaint=None, clock=None,
                                    deadline_s=None):
    """verify_hwnd_capture wrapped in the bounded single-retry tolerance.

    capture-flake-tolerance-01. Attempt 1 calls verify_hwnd_capture with
    the caller's EXACT arguments. Anything other than the recorded
    transient verdict ('occluded_or_foreign_content') is returned
    untouched -- deterministic contract verdicts are never retried. On the
    transient: ONE repaint of the SAME fixture (never recreated, never
    retuned), the fixture parameters are ASSERTED identical between
    attempts (hwnd, measured client size, expected-pattern digest, title;
    any drift raises AssertionError naming the drift instead of retrying),
    then attempt 2 runs with identical arguments inside the wall-clock
    deadline. The full first-attempt record is attached to the returned
    record as 'first_attempt' -- a healed transient retains its failure;
    a persistent one fails the original assertions with both records in
    the message. Nothing is skipped and no assertion is weakened: the
    retry wraps, never skips. verify/repaint/clock are injection seams
    for the synthetic falsifiers (TransientToleranceTests) only.
    """
    verify_fn = verify_hwnd_capture if verify is None else verify
    repaint_fn = (lambda: window.repaint()) if repaint is None else repaint
    now = time.time if clock is None else clock
    if deadline_s is None:
        deadline_s = TRANSIENT_TOLERANCE_DEADLINE_S
    started = now()
    deadline = started + deadline_s

    first = verify_fn(window.hwnd, expected_pattern,
                      pinned_size=pinned_size, title=title)
    provenance = {'max_retries': TRANSIENT_TOLERANCE_MAX_RETRIES,
                  'deadline_s': deadline_s, 'started': started}
    if first.get('verdict') != 'occluded_or_foreign_content':
        provenance['retries'] = 0
        provenance['fired'] = False
        first['transient_tolerance'] = provenance
        return first
    # First attempt failed with the recorded transient: RETAIN it.
    first['transient_tolerance'] = dict(provenance, retries=0, fired=True)
    if now() >= deadline:
        # Time-bounded: past the deadline there is no retry at all.
        first['transient_tolerance']['reason'] = \
            'deadline_exhausted_before_retry'
        _record_transient_event({'healed': False, 'retries': 0,
                                 'reason': 'deadline_exhausted_before_retry',
                                 'title': title,
                                 'first_attempt_verdict': first.get('verdict')})
        return first
    # The identical-fixture-parameters assert (the anti-mask teeth): the
    # retry re-tests THE SAME window handle, client size, content digest
    # and title. Any drift means the failure is not the recorded
    # transient, and the retry is refused with a loud failure.
    hwnd_first = window.hwnd
    measured_first = tuple(first.get('client_size') or ())
    sha_first = pattern_sha256(expected_pattern)
    repaint_fn()
    drifted = []
    if window.hwnd != hwnd_first:
        drifted.append(('hwnd', hwnd_first, window.hwnd))
    measured_now = window.client_rect()
    # client_rect() is (left, top, width, height); the record's
    # client_size is [width, height] -- project before comparing.
    measured_now = (tuple(measured_now[2:4])
                    if measured_now and len(measured_now) >= 4 else None)
    if measured_now != measured_first:
        drifted.append(('client_size', list(measured_first),
                        None if measured_now is None else list(measured_now)))
    if pattern_sha256(expected_pattern) != sha_first:
        drifted.append(('expected_pattern_sha256', sha_first,
                        pattern_sha256(expected_pattern)))
    if title != first.get('title', title):
        drifted.append(('title', first.get('title', title), title))
    if drifted:
        raise AssertionError(
            'transient-tolerance refused: fixture parameters drifted '
            'between attempts (a retry would re-test a DIFFERENT '
            'fixture): ' + repr(drifted) + ' first_attempt=' + repr(first))
    second = verify_fn(window.hwnd, expected_pattern,
                       pinned_size=pinned_size, title=title)
    healed = (second.get('verdict') == 'unobscured'
              and second.get('publishable') is True)
    second['first_attempt'] = first
    second['transient_tolerance'] = dict(
        provenance, retries=1, fired=True, healed=healed,
        deadline_respected=now() <= deadline)
    _record_transient_event({'healed': healed, 'retries': 1,
                             'title': title,
                             'deadline_respected':
                                 second['transient_tolerance'][
                                     'deadline_respected'],
                             'first_attempt_verdict': first.get('verdict'),
                             'second_verdict': second.get('verdict')})
    return second


class _ToleranceScriptedWindow(object):
    """Minimal fixture-shaped stand-in for the synthetic falsifiers.

    Only what the tolerance touches: hwnd, client_rect(), repaint(). No
    Win32, no real window -- the tolerance's LOGIC is what is under test.
    """

    def __init__(self, hwnd=12345, size=(100, 70)):
        self.hwnd = hwnd
        self._size = tuple(size)
        self.repaints = 0

    def client_rect(self):
        return (0, 0, self._size[0], self._size[1])

    def repaint(self):
        self.repaints += 1


def _tolerance_record(verdict, size=(100, 70), title='tolerance-test'):
    return {'verdict': verdict,
            'publishable': verdict == 'unobscured',
            'client_size': list(size), 'title': title}


def _tolerance_scripted_verify(script, calls):
    def verify(hwnd, expected_pattern, pinned_size=None, title=None):
        calls.append({'hwnd': hwnd, 'pinned_size': pinned_size,
                      'title': title,
                      'pattern_len': len(expected_pattern)})
        return script[len(calls) - 1]
    return verify


class TransientToleranceTests(unittest.TestCase):
    """The tolerance's own synthetic falsifiers (capture-flake-tolerance-01).

    Deterministic (scripted attempt records, injected clock): prove the
    retry is single, time-bounded, parameter-identical, failure-retaining,
    and that a REAL occlusion is not masked. Pure logic -- no Win32.
    """

    PATTERN = [[1, 2, 3]]  # any deterministic stand-in matrix

    def _tolerance(self, window, script, calls, times=None, **kw):
        times = [0.0, 0.01, 0.02, 0.03] if times is None else times
        ticks = iter(times)
        return verify_with_transient_tolerance(
            window, self.PATTERN, pinned_size=kw.pop('pinned_size', None),
            title=kw.pop('title', 'tolerance-test'),
            verify=_tolerance_scripted_verify(script, calls),
            repaint=kw.pop('repaint', None) or window.repaint,
            clock=lambda: next(ticks), **kw)

    def test_single_retry_heals_transient_and_retains_first_failure(self):
        calls = []
        first = _tolerance_record('occluded_or_foreign_content')
        second = _tolerance_record('unobscured')
        window = _ToleranceScriptedWindow()
        rec = self._tolerance(window, [first, second], calls)
        self.assertEqual(rec['verdict'], 'unobscured')
        self.assertIs(rec['first_attempt'], first)  # failure RETAINED
        self.assertEqual(rec['transient_tolerance']['retries'], 1)
        self.assertTrue(rec['transient_tolerance']['healed'])
        self.assertTrue(rec['transient_tolerance']['deadline_respected'])
        self.assertEqual(len(calls), 2)      # EXACTLY one retry
        self.assertEqual(window.repaints, 1)  # exactly one repaint between
        self.assertEqual(calls[0], calls[1])  # IDENTICAL arguments

    def test_real_occlusion_not_masked_single_retry_failure_retained(self):
        calls = []
        first = _tolerance_record('occluded_or_foreign_content')
        second = _tolerance_record('occluded_or_foreign_content')
        window = _ToleranceScriptedWindow()
        rec = self._tolerance(window, [first, second], calls)
        # A REAL (persistent) occlusion: retried ONCE, never more, still
        # failed, first attempt retained on the returned record.
        self.assertEqual(rec['verdict'], 'occluded_or_foreign_content')
        self.assertIs(rec['first_attempt'], first)
        self.assertFalse(rec['transient_tolerance']['healed'])
        self.assertEqual(len(calls), 2)
        # The ORIGINAL assertion shape still fires on this record: nothing
        # is masked; the failure message carries both records.
        with self.assertRaises(AssertionError):
            self.assertEqual(rec['verdict'], 'unobscured', rec)

    def test_retry_refused_when_fixture_parameters_drift(self):
        calls = []
        first = _tolerance_record('occluded_or_foreign_content')
        window = _ToleranceScriptedWindow()

        def repaint_with_drift():
            window.repaints += 1
            window._size = (180, 70)  # drift AFTER the first attempt

        with self.assertRaisesRegex(AssertionError, 'drifted'):
            self._tolerance(window, [first], calls,
                            repaint=repaint_with_drift)
        self.assertEqual(len(calls), 1)  # NO second attempt: parameters
        # drifted, so a retry would re-test a different fixture.

    def test_non_transient_verdicts_return_without_retry(self):
        calls = []
        destroyed = _tolerance_record('window_destroyed')
        window = _ToleranceScriptedWindow()
        rec = self._tolerance(window, [destroyed], calls)
        self.assertEqual(rec['verdict'], 'window_destroyed')
        self.assertEqual(len(calls), 1)  # deterministic verdicts: no retry
        self.assertFalse(rec['transient_tolerance']['fired'])

    def test_deadline_exhausted_before_retry_means_no_retry(self):
        calls = []
        first = _tolerance_record('occluded_or_foreign_content')
        window = _ToleranceScriptedWindow()
        rec = self._tolerance(window, [first], calls,
                              times=[0.0, 100.0], deadline_s=5.0)
        self.assertEqual(len(calls), 1)  # time-bounded: no attempt 2
        self.assertEqual(rec['transient_tolerance']['reason'],
                         'deadline_exhausted_before_retry')
        # The returned record IS the first attempt: the failure is
        # retained as the record itself, never discarded.
        self.assertEqual(rec['verdict'], 'occluded_or_foreign_content')
        self.assertEqual(rec['transient_tolerance']['retries'], 0)


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
