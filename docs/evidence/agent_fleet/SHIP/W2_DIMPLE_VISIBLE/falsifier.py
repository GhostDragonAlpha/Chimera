"""W2 FALSIFIER (stated before the after-state was measured):

PIXEL BAR (derived from the camera geometry): page cam r=26, fov 45deg,
target [0,4.5,0] -> eye-to-belly dist ~25.3 m; canvas 1280x800 ->
px/m = 800/(2*tan(22.5deg)*25.3) = 38.2 px/m.
Default press 20000 N -> delta = 20000/(4*pi*4000) = 0.3979 m ->
projected depth = 15.2 px.
PASS = changed-pixel region (canvas only, delta>12/255):
  (1) bbox width >= 15 px  (a dent at least as wide as its own projected depth;
      the pre-fix slit measured 7 px wide -> FAIL)
  (2) total changed px >= 1000  (pre-fix: 103)
  (3) blob shape: >= 10 distinct rows each with >= 5 changed px (not a line)
  (4) reference: the engine's own /frame of the same press = 1 px at delta 3
TIMING BAR:
  appear:  by +0.7 s after mousedown (130 ms arm + one 333 ms poll)
  disappear: after mouseup the changed-px count decays monotonically and is
  <= 20 % of peak by +2.0 s (tau = 0.5 s).
PARITY BAR: probe sum1 (RG.verts checksum) must equal the same checksum of
the shell's /api/verts DURING the hold (the kernel must live in the shader,
never corrupt the streamed buffer -- H16 parity holds under press).
"""
import json, math, struct, time, urllib.request
from playwright.sync_api import sync_playwright

SHELL = "http://127.0.0.1:8207"
OUT = r"E:\ChimeraWork\slot-01\.tmp\w2_scratch"

def shell_verts():
    with urllib.request.urlopen(SHELL + "/api/verts", timeout=10) as r:
        return r.read()

def w2_checksum(buf):
    n = struct.unpack("<I", buf[:4])[0]
    f = struct.unpack("<" + "f" * (n * 9), buf[4:4 + n * 36])
    s = 0.0
    for i in range(0, n * 9, 3):
        s += f[i] + f[i + 1] + f[i + 2]
    return s, n, f

def dent_at(f, n, hit, rmax=0.5):
    best = 0.0
    for i in range(n):
        d = math.dist(f[i*9:i*9+3], hit)
        if d < rmax:
            # compare against a rest copy is expensive; return min-y drop later
            pass
    return best

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--enable-unsafe-swiftshader","--use-gl=angle","--use-angle=swiftshader"])
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(SHELL + "/?debug=1")
    page.fill("#name-input", "W2probe")
    page.click("#play-btn")
    page.wait_for_timeout(400)
    if page.is_visible("#intro-begin"):
        page.click("#intro-begin")
    for _ in range(120):
        r = page.evaluate("() => (window.__h16pickProbe ? window.__h16pickProbe(640,400) : null)")
        if r and r["triCount"] > 0 and r["vertCount"] > 0:
            break
        page.wait_for_timeout(500)
    print("mesh ready: triCount=%d" % r["triCount"])

    BELLY = [0.0, 4.444, 0.700]
    best = None
    for py in range(200, 700, 25):
        for px in range(300, 1000, 25):
            r = page.evaluate(f"() => window.__h16pickProbe({px},{py})")
            if r["raw"]:
                d = math.dist(r["raw"], BELLY)
                if best is None or d < best[0]:
                    best = (d, px, py)
            if best and best[0] < 0.05: break
        if best and best[0] < 0.05: break
    d, bpx, bpy = best
    print(f"belly pixel: ({bpx},{bpy}) d={d:.3f} m")

    # SETTLE GUARD: the reference must not be taken during the boot pose
    # settle (measured: a reference taken at boot poisons every later diff
    # with the engine's own drift). Wait until the stream is bit-stable
    # across 1.5 s, then take the reference.
    prev = None
    for _ in range(60):
        s, _, _ = w2_checksum(shell_verts())
        if prev is not None and s == prev:
            break
        prev = s
        page.wait_for_timeout(1500)
    print("stream bit-stable across 1.5 s")
    # rest checksums
    ssum, n, fv = w2_checksum(shell_verts())
    pr = page.evaluate(f"() => window.__h16pickProbe({bpx},{bpy})")
    print("REST  parity: page sum1=%.3f server=%.3f diff=%.4f" % (pr["sum1"], ssum, abs(pr["sum1"]-ssum)))
    page.screenshot(path=OUT + r"\f_rest.png")

    t0 = time.time()
    page.mouse.move(bpx, bpy)
    page.mouse.down()
    page.wait_for_timeout(500)          # ~ arm 130ms + 1 poll 333ms
    page.screenshot(path=OUT + r"\f_appear.png")
    ap_t = time.time() - t0
    page.wait_for_timeout(1000)         # hold ~1.5 s total
    page.screenshot(path=OUT + r"\f_hold.png")
    hd = page.text_content("#hand-state")
    ssum2, _, fv2 = w2_checksum(shell_verts())
    pr2 = page.evaluate(f"() => window.__h16pickProbe({bpx},{bpy})")
    sd = max(math.dist(fv2[i*9:i*9+3], fv[i*9:i*9+3]) for i in range(n))
    print("HOLD  hand='%s' server dent=%.4f m  parity diff=%.4f  (t=%.2fs)" % (hd, sd, abs(pr2["sum1"]-ssum2), time.time()-t0))

    page.mouse.up()
    page.wait_for_timeout(400)
    page.screenshot(path=OUT + r"\f_decay1.png")
    page.wait_for_timeout(600)
    page.screenshot(path=OUT + r"\f_decay2.png")
    page.wait_for_timeout(1000)
    page.screenshot(path=OUT + r"\f_gone.png")
    print("sequence captured, appear shot at t=+0.5s")
    print("judge:", page.text_content("#judge-debug"))
    browser.close()

# ---- pixel analysis (png decode reused) ----
import zlib
def png_pixels(path):
    data = open(path, 'rb').read()
    pos = 8; w = h = None; idat = b''
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        if typ == b'IHDR':
            w, h, bd, ct = struct.unpack('>IIBB', data[pos+8:pos+18])
        elif typ == b'IDAT':
            idat += data[pos+8:pos+8+ln]
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = 3 if ct == 2 else 4
    prev = bytearray(w*ch); rows = []; i = 0
    for y in range(h):
        ft = raw[i]; i += 1
        row = bytearray(raw[i:i+w*ch]); i += w*ch
        if ft == 1:
            for x in range(ch, len(row)): row[x] = (row[x]+row[x-ch]) & 255
        elif ft == 2:
            for x in range(len(row)): row[x] = (row[x]+prev[x]) & 255
        elif ft == 3:
            for x in range(len(row)):
                a = row[x-ch] if x >= ch else 0
                row[x] = (row[x]+((a+prev[x]) >> 1)) & 255
        elif ft == 4:
            for x in range(len(row)):
                a = row[x-ch] if x >= ch else 0
                b2 = prev[x]; c = prev[x-ch] if x >= ch else 0
                pp = a+b2-c
                pa, pb, pc = abs(pp-a), abs(pp-b2), abs(pp-c)
                prr = a if (pa <= pb and pa <= pc) else (b2 if pb <= pc else c)
                row[x] = (row[x]+prr) & 255
        rows.append(bytes(row)); prev = row
    return w, h, ch, rows

def diff_map(p1, p2):
    w, h, ch, r1 = png_pixels(p1)
    _, _, _, r2 = png_pixels(p2)
    xs = []; ys = []
    for y in range(h):
        a = r1[y]; b = r2[y]
        for x in range(min(w, 920)):      # canvas only (sidebar = HUD numbers)
            s = 0
            for c in range(3):
                dd = abs(a[x*ch+c]-b[x*ch+c])
                if dd > s: s = dd
            if s > 12: xs.append(x); ys.append(y)
    return xs, ys, w, h

def report(tag, xs, ys):
    if not xs:
        print(f"{tag}: NO changed px"); return 0
    bw = max(xs)-min(xs)+1; bh = max(ys)-min(ys)+1
    from collections import Counter
    rc = Counter(ys)
    blob_rows = sum(1 for y, c in rc.items() if c >= 5)
    print(f"{tag}: px={len(xs)} bbox={bw}x{bh} rows>=5px:{blob_rows} maxdelta-loc=({min(xs)}..{max(xs)},{min(ys)}..{max(ys)})")
    return len(xs)

xs0, ys0, _, _ = diff_map(OUT + r"\f_rest.png", OUT + r"\f_rest.png")
xa, ya, _, _ = diff_map(OUT + r"\f_rest.png", OUT + r"\f_appear.png")
xh, yh, _, _ = diff_map(OUT + r"\f_rest.png", OUT + r"\f_hold.png")
x1, y1, _, _ = diff_map(OUT + r"\f_rest.png", OUT + r"\f_decay1.png")
x2, y2, _, _ = diff_map(OUT + r"\f_rest.png", OUT + r"\f_decay2.png")
xg, yg, _, _ = diff_map(OUT + r"\f_rest.png", OUT + r"\f_gone.png")
print("--- falsifier numbers (canvas only, delta>12) ---")
report("appear(+0.5s)", xa, ya)
peak = report("hold(+1.5s)", xh, yh)
report("decay+0.4s", x1, y1)
report("decay+1.0s", x2, y2)
gone = report("gone+2.0s", xg, yg)
print("--- bars ---")
print("bbox width bar >= 15px, total bar >= 1000px, blob rows bar >= 10, gone <= 20% of peak")
