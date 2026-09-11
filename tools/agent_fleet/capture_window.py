"""Bounded Windows owned-client capture contract (window-capture-ownership-01).

Derived from the shutdown verification lesson: a correct PID/HWND did not imply
an unobscured desktop region, and window borders included unrelated
background. This module therefore:

  * only ever captures SELF-CREATED fixture windows (class prefix
    ``ChimeraFixture``) whose process, class, visibility and size are
    verified before any pixel is trusted;
  * captures through the WINDOW-SPECIFIC path (PrintWindow into a memory DC
    sized to the client rect) - never GetDC(NULL)/CreateDC("DISPLAY"), so no
    screen-region or desktop fallback can exist;
  * verifies content by FULL pixel-matrix equality against a deterministic
    computed pattern (point sampling is not a completeness proof);
  * fails CLOSED with named verdicts before anything can be published.

Publication rule: only ``verdict == 'unobscured'`` records may be published,
and they carry no desktop pixels by construction.
"""
import ctypes
import hashlib
import json
import os
import struct
from ctypes import wintypes

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

# 64-bit handle prototypes (default c_int restype truncates handles).
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.GetCurrentProcessId.restype = wintypes.DWORD
kernel32.GetLastError.restype = wintypes.DWORD
user32.RegisterClassW.restype = ctypes.c_ushort
user32.CreateWindowExW.restype = wintypes.HWND
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL
user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.CreateDIBSection.restype = wintypes.HBITMAP
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.SelectObject.argtypes = [wintypes.HGDIOBJ, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.GetStockObject.restype = wintypes.HGDIOBJ
user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
user32.PrintWindow.restype = wintypes.BOOL
LRESULT = ctypes.c_ssize_t
user32.DefWindowProcW.restype = LRESULT
user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT,
                                  ctypes.c_size_t, ctypes.c_ssize_t]
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                wintypes.UINT]
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetClientRect.restype = wintypes.BOOL
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.AdjustWindowRectEx.argtypes = [ctypes.POINTER(wintypes.RECT),
                                      wintypes.DWORD, wintypes.BOOL,
                                      wintypes.DWORD]
user32.SetWindowPos.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UpdateWindow.argtypes = [wintypes.HWND]
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND,
                                            ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
gdi32.StretchDIBits.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                ctypes.c_void_p, ctypes.c_void_p,
                                wintypes.UINT, wintypes.DWORD]
# FRESH-SYSTEM FIX (window-capture-ownership-02): CreateCompatibleDC and
# CreateDIBSection had no declared argtypes in the inherited module, so a
# window DC whose handle value exceeds 2^31 - 1 (GDI hands out such values
# on this system) crashed with OverflowError instead of producing a named
# fail-closed verdict. Declared handle prototypes keep every refusal NAMED.
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateDIBSection.argtypes = [wintypes.HDC,
                                   ctypes.c_void_p,
                                   wintypes.UINT,
                                   ctypes.POINTER(ctypes.c_void_p),
                                   wintypes.HANDLE,
                                   wintypes.DWORD]

CLASS_PREFIX = 'ChimeraFixture'
DEFAULT_WIDTH = 320
DEFAULT_HEIGHT = 200

SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB = 0
PW_CLIENTONLY = 0x00000001
GWL_STYLE = -16
WS_VISIBLE = 0x10000000
COLOR_WINDOW = 5
IDI_APPLICATION = 32512
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [('biSize', wintypes.DWORD),
                ('biWidth', wintypes.LONG),
                ('biHeight', wintypes.LONG),
                ('biPlanes', wintypes.WORD),
                ('biBitCount', wintypes.WORD),
                ('biCompression', wintypes.DWORD),
                ('biSizeImage', wintypes.DWORD),
                ('biXPelsPerMeter', wintypes.LONG),
                ('biYPelsPerMeter', wintypes.LONG),
                ('biClrUsed', wintypes.DWORD),
                ('biClrImportant', wintypes.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [('bmiHeader', BITMAPINFOHEADER),
                ('bmiColors', wintypes.DWORD * 1)]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [('style', ctypes.c_uint),
                ('lpfnWndProc', ctypes.WINFUNCTYPE(
                    ctypes.c_longlong, wintypes.HWND, ctypes.c_uint,
                    ctypes.c_uint, ctypes.c_longlong)),
                ('cbClsExtra', ctypes.c_int),
                ('cbWndExtra', ctypes.c_int),
                ('hInstance', wintypes.HINSTANCE),
                ('hIcon', wintypes.HICON),
                ('hCursor', wintypes.HANDLE),
                ('hbrBackground', wintypes.HBRUSH),
                ('lpszMenuName', wintypes.LPCWSTR),
                ('lpszClassName', wintypes.LPCWSTR)]


class FixtureWindow:
    """A self-created top-level fixture window with deterministic content.

    The window is painted directly into its own DC by :meth:`repaint` - the
    pattern never depends on what else is on the desktop.
    """

    def __init__(self, title, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
                 paint_fn=None):
        self.title = title
        self.width = width
        self.height = height
        self.hwnd = None
        self._atom = None
        self._paint_fn = paint_fn or default_pattern
        self._class_name = CLASS_PREFIX + '_' + \
            hashlib.sha1(title.encode('utf-8')).hexdigest()[:10]
        self._create()

    # ---- creation / teardown ------------------------------------------------
    def _create(self):
        hinst = kernel32.GetModuleHandleW(None)
        wndproc = ctypes.WINFUNCTYPE(
            ctypes.c_longlong, wintypes.HWND, ctypes.c_uint, ctypes.c_uint,
            ctypes.c_longlong)(DefWindowProcW_trampoline)
        wc = WNDCLASSW()
        wc.style = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc = ctypes.cast(wndproc, ctypes.WINFUNCTYPE(
            ctypes.c_longlong, wintypes.HWND, ctypes.c_uint, ctypes.c_uint,
            ctypes.c_longlong))
        wc.hInstance = hinst
        wc.hbrBackground = ctypes.c_void_p(gdi32.GetStockObject(
            5))  # GRAY_BRUSH stock object (5)
        wc.lpszClassName = self._class_name
        self._wc_keepalive = wndproc
        atom = user32.RegisterClassW(ctypes.byref(wc))
        if not atom:
            raise OSError('RegisterClassW failed: %d' % kernel32.GetLastError())
        self._atom = atom
        WS_OVERLAPPEDWINDOW = 0x00CF0000
        # Adjust the OUTER size so the CLIENT area is exactly width x height.
        rect = wintypes.RECT(0, 0, self.width, self.height)
        user32.AdjustWindowRectEx(ctypes.byref(rect), WS_OVERLAPPEDWINDOW,
                                  False, 0)
        outer_w = rect.right - rect.left
        outer_h = rect.bottom - rect.top
        self.hwnd = user32.CreateWindowExW(
            0, self._class_name, self.title, WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            40, 40, outer_w, outer_h, None, None, hinst, None)
        if not self.hwnd:
            raise OSError('CreateWindowExW failed: %d' % kernel32.GetLastError())
        user32.ShowWindow(self.hwnd, 5)  # SW_SHOW
        user32.UpdateWindow(self.hwnd)
        # Pin the MEASURED client size (DPI chrome can skew the adjustment);
        # the deterministic pattern is painted to the pinned size.
        measured = self.client_rect()
        self.width, self.height = measured[2], measured[3]
        self.repaint()

    def close(self):
        """Destroy only this self-created window (never a foreign one)."""
        if self.hwnd and user32.IsWindow(self.hwnd):
            user32.DestroyWindow(self.hwnd)
        if self._class_name:
            user32.UnregisterClassW(self._class_name, None)
        self.hwnd = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ---- geometry / ownership ------------------------------------------------
    def client_rect(self):
        rect = wintypes.RECT()
        if not user32.GetClientRect(self.hwnd, ctypes.byref(rect)):
            return None
        return (rect.left, rect.top, rect.right - rect.left,
                rect.bottom - rect.top)

    def resize_client(self, width, height):
        """Change the real window's client area (the PINNED size stays).

        Ownership-contract semantics: the expected pattern/size are pinned at
        creation; moving the real window away from the pinned size is exactly
        the 'window_resized' fail-closed case.
        """
        rect = wintypes.RECT(0, 0, width, height)
        WS_OVERLAPPEDWINDOW = 0x00CF0000
        user32.AdjustWindowRectEx(ctypes.byref(rect), WS_OVERLAPPEDWINDOW,
                                  False, 0)
        outer_w = rect.right - rect.left
        outer_h = rect.bottom - rect.top
        user32.SetWindowPos(self.hwnd, None, 40, 40, outer_w, outer_h,
                            0x0004)  # SWP_NOZORDER

    # ---- deterministic content ----------------------------------------------
    def expected_pattern(self, width=None, height=None):
        """The pixel matrix the window paints (rows of [r, g, b])."""
        return self._paint_fn(width if width is not None else self.width,
                              height if height is not None else self.height)

    def repaint(self):
        """Paint the deterministic pattern into the window's own DC."""
        dc = user32.GetDC(self.hwnd)
        try:
            _blit_pattern(dc, 0, 0, self.width, self.height,
                          self._paint_fn(self.width, self.height))
        finally:
            user32.ReleaseDC(self.hwnd, dc)


# ---- deterministic pattern ---------------------------------------------------

def default_pattern(width, height):
    """Deterministic RGB matrix derived from coordinates (no time, no OS)."""
    return [[[(x * 7 + y * 13 + ch * 29) % 256 for ch in range(3)]
             for x in range(width)] for y in range(height)]


def solid_pattern(color):
    """Paint-function factory: a deterministic SOLID fill of exactly `color`.

    Every pixel of every row is the same [r, g, b] triple, derived from the
    color alone (no time, no OS state). Gives fixture cases DISTINCT known
    pixel content so a cross-window content mismatch is detectable by full
    matrix equality rather than assumption.
    """
    r, g, b = (int(c) % 256 for c in color)

    def paint(width, height):
        return [[[r, g, b] for _ in range(width)] for _ in range(height)]

    return paint


def window_rect(hwnd):
    """Outer window rect (left, top, right, bottom) incl. nonclient, or None.

    Used to demonstrate the nonclient chrome (caption, borders, DWM shadow /
    rounded-corner region) is strictly larger than the pinned client rect on
    the running system - the captured matrix is sized to the client rect and
    uses PW_CLIENTONLY, so chrome pixels cannot enter a record.
    """
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    return (rect.left, rect.top, rect.right, rect.bottom)


def pattern_sha256(pattern):
    h = hashlib.sha256()
    for row in pattern:
        for px in row:
            h.update(bytes(px))
    return h.hexdigest()


# ---- capture path (window-specific, never screen) ----------------------------

def capture_client_pixels(hwnd, expected_width, expected_height):
    """Capture the CLIENT AREA of one window via PrintWindow.

    Returns (rows, None) on success or (None, named_reason). Refuses before
    touching pixels when the client area is not exactly the pinned size.
    """
    if not user32.IsWindow(hwnd):
        return None, 'stale_or_invalid_handle'
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    width, height = rect.right - rect.left, rect.bottom - rect.top
    if (width, height) != (expected_width, expected_height):
        return None, 'client_size_mismatch'
    hdc_window = user32.GetDC(hwnd)
    if not hdc_window:
        return None, 'no_window_dc'
    mem_dc = gdi32.CreateCompatibleDC(hdc_window)
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height  # top-down rows
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB
    bmi.bmiHeader.biSizeImage = width * height * 4
    bits = ctypes.c_void_p()
    dib = gdi32.CreateDIBSection(hdc_window, ctypes.byref(bmi),
                                 DIB_RGB_COLORS, ctypes.byref(bits), None, 0)
    old = None
    rows = None
    reason = None
    if not dib or not bits:
        reason = 'dib_allocation_failed'
    else:
        old = gdi32.SelectObject(mem_dc, dib)
        ok = user32.PrintWindow(hwnd, mem_dc, PW_CLIENTONLY)
        if not ok:
            reason = 'printwindow_refused'
        else:
            stride = width * 4
            raw = ctypes.string_at(bits, stride * height)
            rows = []
            for y in range(height):
                row = []
                base = y * stride
                for x in range(width):
                    b, g, r = raw[base + x * 4], raw[base + x * 4 + 1], \
                        raw[base + x * 4 + 2]
                    row.append([r, g, b])
                rows.append(row)
        if old:
            gdi32.SelectObject(mem_dc, old)
        gdi32.DeleteObject(dib)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(hwnd, hdc_window)
    return rows, reason


def matrices_equal(a, b):
    return a == b


# ---- the contract ------------------------------------------------------------

def verify_hwnd_capture(hwnd, expected_pattern, pinned_size=None, title=None):
    """Full contract check at the HWND level. Fail-closed, named verdicts.

    Same decision order and verdict vocabulary as the contract has always
    had: destroyed -> foreign_process -> foreign_window_class ->
    not_visible -> resized -> capture -> content. Taking ANY hwnd is what
    lets a REAL foreign-process fixture (a child process of this test's own
    interpreter, never a third-party window) be refused on pid before any
    pixel is trusted. `expected_pattern` is required: content is always
    verified against a known deterministic matrix. Only verdict
    'unobscured' with publishable=True may be published as engine evidence;
    no desktop or screen pixels ever enter the record.
    """
    record = {'contract': 'WINDOW_CAPTURE_OWNERSHIP_V1'}
    if title is not None:
        record['title'] = title
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    my_pid = kernel32.GetCurrentProcessId()
    record['pid'] = pid.value
    record['owns_process'] = pid.value == my_pid

    cls_buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, cls_buf, 256)
    record['window_class'] = cls_buf.value
    record['class_owned'] = cls_buf.value.startswith(CLASS_PREFIX)
    record['is_window'] = bool(user32.IsWindow(hwnd))
    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    record['visible'] = bool(style & WS_VISIBLE)

    if not record['is_window']:
        record['verdict'] = 'window_destroyed'
        record['publishable'] = False
        return record
    if not record['owns_process']:
        record['verdict'] = 'foreign_process'
        record['publishable'] = False
        return record
    if not record['class_owned']:
        record['verdict'] = 'foreign_window_class'
        record['publishable'] = False
        return record
    if not record['visible']:
        record['verdict'] = 'window_not_visible'
        record['publishable'] = False
        return record

    rect = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        record['verdict'] = 'stale_or_invalid_handle'
        record['publishable'] = False
        return record
    measured = (rect.right - rect.left, rect.bottom - rect.top)
    record['client_size'] = list(measured)
    if pinned_size is None:
        pinned_size = measured
    record['pinned_size'] = list(pinned_size)
    if measured != tuple(pinned_size):
        record['verdict'] = 'window_resized'
        record['publishable'] = False
        return record

    rows, reason = capture_client_pixels(hwnd, pinned_size[0], pinned_size[1])
    if rows is None:
        record['verdict'] = 'capture_refused:' + (reason or 'unknown')
        record['publishable'] = False
        return record
    record['capture_sha256'] = pattern_sha256(rows)
    record['expected_sha256'] = pattern_sha256(expected_pattern)
    if not matrices_equal(rows, expected_pattern):
        record['verdict'] = 'occluded_or_foreign_content'
        record['publishable'] = False
        return record
    record['verdict'] = 'unobscured'
    record['publishable'] = True
    return record


def verify_owned_capture(window, expected_pattern=None):
    """Full contract check on a FixtureWindow (delegates to the hwnd level).

    Returns a record; only verdict 'unobscured' with publishable=True may be
    published as engine evidence.
    """
    want = expected_pattern if expected_pattern is not None \
        else window.expected_pattern()
    return verify_hwnd_capture(window.hwnd, want,
                               pinned_size=(window.width, window.height),
                               title=window.title)


def verdict_verdicts():
    """The exhaustive verdict vocabulary (for tests and review)."""
    return {'unobscured', 'window_destroyed', 'foreign_process',
            'foreign_window_class', 'window_not_visible', 'window_resized',
            'occluded_or_foreign_content', 'stale_or_invalid_handle',
            'capture_refused:printwindow_refused',
            'capture_refused:client_size_mismatch',
            'capture_refused:stale_or_invalid_handle',
            'capture_refused:no_window_dc', 'capture_refused:dib_allocation_failed'}


# ---- helpers -----------------------------------------------------------------

def DefWindowProcW_trampoline(hwnd, msg, wparam, lparam):
    return user32.DefWindowProcW(
        wintypes.HWND(hwnd), wintypes.UINT(msg & 0xFFFFFFFF),
        ctypes.c_size_t(wparam & 0xFFFFFFFFFFFFFFFF),
        ctypes.c_ssize_t(lparam & 0xFFFFFFFFFFFFFFFF))


def _blit_pattern(hdc, x, y, width, height, pattern):
    """Paint the pattern rows into hdc (bottom-up safe)."""
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB
    bmi.bmiHeader.biSizeImage = width * height * 4
    pixels = (ctypes.c_ubyte * (width * height * 4))()
    for r, row in enumerate(pattern):
        base = r * width * 4
        for c, px in enumerate(row):
            i = base + c * 4
            pixels[i] = px[2]      # B
            pixels[i + 1] = px[1]  # G
            pixels[i + 2] = px[0]  # R
            pixels[i + 3] = 255
    gdi32.StretchDIBits(hdc, x, y, width, height, 0, 0, width, height,
                        pixels, ctypes.byref(bmi), DIB_RGB_COLORS, SRCCOPY)


def write_evidence(path, record):
    """Write evidence WITHOUT overwriting an existing path."""
    if os.path.exists(path):
        raise FileExistsError('evidence_refuse_overwrite: ' + str(path))
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=1, ensure_ascii=False)
        f.write('\n')
    return path
