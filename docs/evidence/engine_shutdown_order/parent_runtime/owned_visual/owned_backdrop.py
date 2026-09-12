"""One test-owned Win32/GDI backdrop and HWND-specific client capture.

This module never captures the desktop. ``capture_client`` asks the target
window to paint into a private memory bitmap using PrintWindow(PW_CLIENTONLY).
"""
from __future__ import annotations

import ctypes as c
from ctypes import wintypes as w
import hashlib
import os
from pathlib import Path
import threading

from PIL import Image


if os.name != "nt":
    raise RuntimeError("owned_backdrop requires Win32")


user = c.WinDLL("user32", use_last_error=True)
gdi = c.WinDLL("gdi32", use_last_error=True)
kernel = c.WinDLL("kernel32", use_last_error=True)

LRESULT = c.c_ssize_t
WNDPROC = c.WINFUNCTYPE(LRESULT, w.HWND, w.UINT, w.WPARAM, w.LPARAM)


class WNDCLASSW(c.Structure):
    _fields_ = [
        ("style", w.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", c.c_int),
        ("cbWndExtra", c.c_int),
        ("hInstance", w.HINSTANCE),
        ("hIcon", w.HICON),
        ("hCursor", w.HANDLE),
        ("hbrBackground", w.HBRUSH),
        ("lpszMenuName", w.LPCWSTR),
        ("lpszClassName", w.LPCWSTR),
    ]


class PAINTSTRUCT(c.Structure):
    _fields_ = [
        ("hdc", w.HDC),
        ("fErase", w.BOOL),
        ("rcPaint", w.RECT),
        ("fRestore", w.BOOL),
        ("fIncUpdate", w.BOOL),
        ("rgbReserved", c.c_byte * 32),
    ]


class BITMAPINFOHEADER(c.Structure):
    _fields_ = [
        ("biSize", w.DWORD),
        ("biWidth", c.c_long),
        ("biHeight", c.c_long),
        ("biPlanes", w.WORD),
        ("biBitCount", w.WORD),
        ("biCompression", w.DWORD),
        ("biSizeImage", w.DWORD),
        ("biXPelsPerMeter", c.c_long),
        ("biYPelsPerMeter", c.c_long),
        ("biClrUsed", w.DWORD),
        ("biClrImportant", w.DWORD),
    ]


class BITMAPINFO(c.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", w.DWORD * 3)]


WM_PAINT = 0x000F
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
WM_PRINTCLIENT = 0x0318
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_VISIBLE = 0x10000000
SW_SHOW = 5
PW_CLIENTONLY = 0x00000001
DIB_RGB_COLORS = 0
BI_RGB = 0
TRANSPARENT = 1
DT_CENTER = 0x00000001
DT_VCENTER = 0x00000004
DT_WORDBREAK = 0x00000010
DT_SINGLELINE = 0x00000020
PAINT_REVISION = "chimera-owned-backdrop-v1"
TITLE = "CHIMERA OWNED SHUTDOWN TEST BACKDROP - VISUAL OBSERVATION ONLY"


def _rgb(red: int, green: int, blue: int) -> int:
    return red | (green << 8) | (blue << 16)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _win_error(action: str) -> OSError:
    return c.WinError(c.get_last_error(), action)


user.DefWindowProcW.restype = LRESULT
user.DefWindowProcW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
user.RegisterClassW.argtypes = [c.POINTER(WNDCLASSW)]
user.RegisterClassW.restype = w.ATOM
user.CreateWindowExW.restype = w.HWND
user.CreateWindowExW.argtypes = [w.DWORD, w.LPCWSTR, w.LPCWSTR, w.DWORD,
                                 c.c_int, c.c_int, c.c_int, c.c_int,
                                 w.HWND, w.HMENU, w.HINSTANCE, w.LPVOID]
user.BeginPaint.restype = w.HDC
user.BeginPaint.argtypes = [w.HWND, c.POINTER(PAINTSTRUCT)]
user.EndPaint.argtypes = [w.HWND, c.POINTER(PAINTSTRUCT)]
user.GetClientRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
user.GetWindowRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
user.IsWindow.argtypes = [w.HWND]
user.IsWindow.restype = w.BOOL
user.IsWindowVisible.argtypes = [w.HWND]
user.IsWindowVisible.restype = w.BOOL
user.PrintWindow.argtypes = [w.HWND, w.HDC, w.UINT]
user.PrintWindow.restype = w.BOOL
user.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
user.PostMessageW.restype = w.BOOL
user.GetDC.argtypes = [w.HWND]
user.GetDC.restype = w.HDC
user.ReleaseDC.argtypes = [w.HWND, w.HDC]
user.DestroyWindow.argtypes = [w.HWND]
user.PostQuitMessage.argtypes = [c.c_int]
user.ShowWindow.argtypes = [w.HWND, c.c_int]
user.UpdateWindow.argtypes = [w.HWND]
user.GetMessageW.argtypes = [c.POINTER(w.MSG), w.HWND, w.UINT, w.UINT]
user.TranslateMessage.argtypes = [c.POINTER(w.MSG)]
user.DispatchMessageW.argtypes = [c.POINTER(w.MSG)]
user.DispatchMessageW.restype = LRESULT
user.LoadCursorW.argtypes = [w.HINSTANCE, w.LPCWSTR]
user.LoadCursorW.restype = w.HANDLE
user.FillRect.argtypes = [w.HDC, c.POINTER(w.RECT), w.HBRUSH]
user.DrawTextW.argtypes = [w.HDC, w.LPCWSTR, c.c_int, c.POINTER(w.RECT), w.UINT]
kernel.GetModuleHandleW.argtypes = [w.LPCWSTR]
kernel.GetModuleHandleW.restype = w.HMODULE
gdi.CreateCompatibleDC.restype = w.HDC
gdi.CreateCompatibleDC.argtypes = [w.HDC]
gdi.CreateCompatibleBitmap.restype = w.HBITMAP
gdi.CreateCompatibleBitmap.argtypes = [w.HDC, c.c_int, c.c_int]
gdi.SelectObject.restype = w.HGDIOBJ
gdi.SelectObject.argtypes = [w.HDC, w.HGDIOBJ]
gdi.CreateSolidBrush.argtypes = [w.COLORREF]
gdi.CreateSolidBrush.restype = w.HBRUSH
gdi.DeleteObject.argtypes = [w.HGDIOBJ]
gdi.DeleteDC.argtypes = [w.HDC]
gdi.SetBkMode.argtypes = [w.HDC, c.c_int]
gdi.SetTextColor.argtypes = [w.HDC, w.COLORREF]
gdi.GetDIBits.argtypes = [w.HDC, w.HBITMAP, w.UINT, w.UINT, w.LPVOID,
                          c.POINTER(BITMAPINFO), w.UINT]


def hwnd_owner(hwnd: int) -> int:
    owner = w.DWORD()
    user.GetWindowThreadProcessId(w.HWND(hwnd), c.byref(owner))
    return int(owner.value)


def require_owned_hwnd(hwnd: int, pid: int, label: str) -> None:
    if not hwnd or not user.IsWindow(w.HWND(hwnd)):
        raise AssertionError(f"{label} HWND does not exist: {hwnd}")
    actual = hwnd_owner(hwnd)
    if actual != pid:
        raise AssertionError(f"{label} HWND owner mismatch: expected {pid}, got {actual}")


def post_owned_close(hwnd: int, pid: int, label: str) -> None:
    """Post WM_CLOSE only after an immediate ownership check."""
    require_owned_hwnd(hwnd, pid, label)
    if not user.PostMessageW(w.HWND(hwnd), WM_CLOSE, 0, 0):
        raise _win_error(f"PostMessageW(WM_CLOSE) for {label}")


def window_rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = w.RECT()
    if not user.GetWindowRect(w.HWND(hwnd), c.byref(rect)):
        raise _win_error("GetWindowRect")
    return rect.left, rect.top, rect.right, rect.bottom


def capture_client(hwnd: int, pid: int, output: Path, label: str) -> dict:
    """Capture only ``hwnd``'s client paint; no screen or desktop DC is read."""
    require_owned_hwnd(hwnd, pid, label)
    rect = w.RECT()
    if not user.GetClientRect(w.HWND(hwnd), c.byref(rect)):
        raise _win_error("GetClientRect")
    width, height = int(rect.right), int(rect.bottom)
    if width <= 0 or height <= 0:
        raise AssertionError(f"{label} has an empty client rectangle")

    window_dc = user.GetDC(w.HWND(hwnd))
    if not window_dc:
        raise _win_error("GetDC(window)")
    memory_dc = gdi.CreateCompatibleDC(window_dc)
    bitmap = gdi.CreateCompatibleBitmap(window_dc, width, height) if memory_dc else None
    old = None
    try:
        if not memory_dc or not bitmap:
            raise _win_error("create capture bitmap")
        old = gdi.SelectObject(memory_dc, bitmap)
        if not old:
            raise _win_error("SelectObject(capture bitmap)")
        if not user.PrintWindow(w.HWND(hwnd), memory_dc, PW_CLIENTONLY):
            raise _win_error(f"PrintWindow(PW_CLIENTONLY) for {label}")
        # GetDIBits requires the bitmap not to be selected into a DC.
        gdi.SelectObject(memory_dc, old)
        old = None
        info = BITMAPINFO()
        info.bmiHeader.biSize = c.sizeof(BITMAPINFOHEADER)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = -height  # request top-down pixels
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        info.bmiHeader.biCompression = BI_RGB
        pixels = (c.c_ubyte * (width * height * 4))()
        rows = gdi.GetDIBits(memory_dc, bitmap, 0, height, pixels,
                             c.byref(info), DIB_RGB_COLORS)
        if rows != height:
            raise _win_error(f"GetDIBits for {label}: {rows}/{height} rows")
        image = Image.frombuffer("RGBA", (width, height), bytes(pixels), "raw", "BGRA", 0, 1)
        output.parent.mkdir(parents=True, exist_ok=True)
        image = image.convert("RGB")  # GDI reserved alpha bytes are not image transparency.
        image.save(output, format="PNG")
    finally:
        if old:
            gdi.SelectObject(memory_dc, old)
        if bitmap:
            gdi.DeleteObject(bitmap)
        if memory_dc:
            gdi.DeleteDC(memory_dc)
        user.ReleaseDC(w.HWND(hwnd), window_dc)

    extrema = image.getextrema()
    return {
        "path": str(output),
        "sha256": sha256_file(output),
        "width": width,
        "height": height,
        "rgba_extrema": extrema,
        "capture_api": "PrintWindow(PW_CLIENTONLY)",
        "captured_hwnd": int(hwnd),
        "captured_pid": int(pid),
    }


def _draw_backdrop(dc: w.HDC, client: w.RECT) -> None:
    brushes = []
    try:
        navy = gdi.CreateSolidBrush(_rgb(20, 36, 62))
        cyan = gdi.CreateSolidBrush(_rgb(35, 120, 146))
        amber = gdi.CreateSolidBrush(_rgb(224, 160, 48))
        brushes.extend([navy, cyan, amber])
        user.FillRect(dc, c.byref(client), navy)
        stripe = w.RECT(0, 0, client.right, max(80, client.bottom // 6))
        user.FillRect(dc, c.byref(stripe), cyan)
        footer = w.RECT(0, max(0, client.bottom - 56), client.right, client.bottom)
        user.FillRect(dc, c.byref(footer), amber)
        gdi.SetBkMode(dc, TRANSPARENT)
        gdi.SetTextColor(dc, _rgb(255, 255, 255))
        title_rect = w.RECT(20, 8, max(21, client.right - 20), stripe.bottom)
        user.DrawTextW(dc, TITLE, -1, c.byref(title_rect), DT_CENTER | DT_VCENTER | DT_SINGLELINE)
        body = "CONTROLLED TEST BACKGROUND\nThis image is not desktop-absence proof."
        body_rect = w.RECT(20, stripe.bottom, max(21, client.right - 20), footer.top)
        user.DrawTextW(dc, body, -1, c.byref(body_rect),
                       DT_CENTER | DT_VCENTER | DT_WORDBREAK)
    finally:
        for brush in brushes:
            if brush:
                gdi.DeleteObject(brush)


def _paint(hwnd: w.HWND) -> None:
    ps = PAINTSTRUCT()
    dc = user.BeginPaint(hwnd, c.byref(ps))
    if not dc:
        return
    try:
        client = w.RECT()
        user.GetClientRect(hwnd, c.byref(client))
        _draw_backdrop(dc, client)
    finally:
        user.EndPaint(hwnd, c.byref(ps))


@WNDPROC
def _wndproc(hwnd, message, wparam, lparam):
    if message == WM_PAINT:
        _paint(hwnd)
        return 0
    if message == WM_PRINTCLIENT:
        client = w.RECT()
        user.GetClientRect(hwnd, c.byref(client))
        _draw_backdrop(w.HDC(wparam), client)
        return 0
    if message == WM_CLOSE:
        user.DestroyWindow(hwnd)
        return 0
    if message == WM_DESTROY:
        user.PostQuitMessage(0)
        return 0
    return user.DefWindowProcW(hwnd, message, wparam, lparam)


class OwnedBackdrop:
    """A single visible window owned by this harness process."""

    def __init__(self, rect: tuple[int, int, int, int]):
        self.rect = rect
        self.pid = os.getpid()
        self.hwnd: int | None = None
        self.class_name = f"ChimeraOwnedBackdrop_{self.pid}_{id(self):x}"
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._error: BaseException | None = None

    def start(self) -> "OwnedBackdrop":
        self._thread = threading.Thread(target=self._run, name="owned-backdrop", daemon=True)
        self._thread.start()
        if not self._ready.wait(5):
            raise TimeoutError("owned backdrop did not create its HWND")
        if self._error:
            raise RuntimeError("owned backdrop creation failed") from self._error
        require_owned_hwnd(self.hwnd or 0, self.pid, "backdrop")
        return self

    def _run(self) -> None:
        try:
            instance = kernel.GetModuleHandleW(None)
            wc = WNDCLASSW()
            wc.lpfnWndProc = _wndproc
            wc.hInstance = instance
            wc.lpszClassName = self.class_name
            wc.hCursor = user.LoadCursorW(
                None, c.cast(c.c_void_p(32512), w.LPCWSTR)
            )
            if not user.RegisterClassW(c.byref(wc)):
                raise _win_error("RegisterClassW")
            x, y, width, height = self.rect
            hwnd = user.CreateWindowExW(0, self.class_name, TITLE,
                                        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
                                        x, y, width, height,
                                        None, None, instance, None)
            if not hwnd:
                raise _win_error("CreateWindowExW")
            self.hwnd = int(hwnd)
            user.ShowWindow(hwnd, SW_SHOW)
            user.UpdateWindow(hwnd)
        except BaseException as exc:
            self._error = exc
            self._ready.set()
            return
        self._ready.set()
        message = w.MSG()
        while user.GetMessageW(c.byref(message), None, 0, 0) > 0:
            user.TranslateMessage(c.byref(message))
            user.DispatchMessageW(c.byref(message))

    def identity(self) -> dict:
        require_owned_hwnd(self.hwnd or 0, self.pid, "backdrop")
        return {
            "pid": self.pid,
            "hwnd": self.hwnd,
            "title": TITLE,
            "class_name": self.class_name,
            "paint_revision": PAINT_REVISION,
            "declared_outer_rect_xywh": self.rect,
            "actual_outer_rect_ltrb": window_rect(self.hwnd or 0),
        }

    def close(self) -> None:
        if self.hwnd and user.IsWindow(w.HWND(self.hwnd)):
            post_owned_close(self.hwnd, self.pid, "backdrop")
        if self._thread:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                raise TimeoutError("owned backdrop thread did not stop")
