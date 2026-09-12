"""One-to-one engine window capture (Python only, no engine change).

Finds the engine's native window by PID, captures it with PrintWindow
(PW_RENDERFULLCONTENT - works for hardware-rendered swapchains), downscales,
JPEG-encodes. Served as MJPEG by the viewer: the web becomes a true mirror
of the engine window at capture pace.
"""
import ctypes
import ctypes.wintypes as wt
from pathlib import Path

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

PW_RENDERFULLCONTENT = 0x00000002


def _callback_factory(pid, found):
    def cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        wpid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
        if wpid.value == pid:
            found.append(hwnd)
        return True
    return cb


def find_window(pid: int):
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    found = []
    user32.EnumWindows(EnumWindowsProc(_callback_factory(pid, found)), 0)
    return found[0] if found else None


def capture_hwnd_jpeg(hwnd, max_width=1280, quality=72):
    rect = wt.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w, h = max(1, rect.right - rect.left), max(1, rect.bottom - rect.top)

    hdc_window = user32.GetDC(hwnd)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_window)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_window, w, h)
    gdi32.SelectObject(hdc_mem, hbmp)

    ok = user32.PrintWindow(hwnd, hdc_mem, PW_RENDERFULLCONTENT)
    if not ok:
        gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_window, 0, 0, 0x00CC0020)

    # BMP extraction via GetDIBits
    class BMIH(ctypes.Structure):
        _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                    ("biPlanes", wt.WORD), ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                    ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", wt.LONG),
                    ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD),
                    ("biClrImportant", wt.DWORD)]

    bmi = BMIH()
    bmi.biSize = ctypes.sizeof(BMIH)
    bmi.biWidth, bmi.biHeight = w, -h          # top-down
    bmi.biPlanes, bmi.biBitCount = 1, 32
    bmi.biCompression = 0                      # BI_RGB
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbmp, 0, h, buf, ctypes.byref(bmi), 0)

    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(hwnd, hdc_window)

    import io
    import numpy as np
    from PIL import Image
    img = Image.frombytes("RGBA", (w, h), buf.raw, "raw", "BGRA", 0, 1)
    if w > max_width:
        img = img.resize((max_width, int(h * max_width / w)), Image.BILINEAR)
    out = io.BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=quality)
    return ok, out.getvalue()


if __name__ == "__main__":
    import sys, time
    pid = int(sys.argv[1])
    hwnd = find_window(pid)
    print("hwnd:", hwnd)
    if hwnd:
        length = wt.DWORD(256)
        title = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title, 256)
        print("title:", title.value)
        for attempt in range(3):
            ok, jpg = capture_hwnd_jpeg(hwnd)
            import numpy as np
            from PIL import Image
            import io
            arr = np.asarray(Image.open(io.BytesIO(jpg)).convert("L"))
            print(f"attempt {attempt}: printwindow={ok} jpeg={len(jpg)}B "
                  f"mean={arr.mean():.1f} std={arr.std():.1f}")
            p = Path(r"E:\ChimeraWork\concept_proof\window_test.jpg")
            p.write_bytes(jpg)
            time.sleep(0.5)
