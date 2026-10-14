"""VTRANS prep: S2 -> RGB, per-panel ruling-line detection, overlapping pinned tiles.

Deterministic pipeline (F4): fixed constants derived from the stage-1 measurement method;
no sweeps; 3-run byte-identical outputs (crops_manifest.json + tile PNGs).
Inputs:  tools/science_funnel/data/vanhoof_forearm/JOA-238-321-s002.tif (sha-pinned)
Outputs: E:/ChimeraWork/vanhoof2-staging/s2_rgb.png, s2_tiles/*.png
         <lane>/crops_manifest.json  (panel bounds, tile geometry, tile sha256s, pass orders)
Constants:
  INK_MAX      = 100   (gray <= 100 is ink; intake measured ink~10, bg~158)
  H_LINE_FRAC  = 0.40  (horizontal line: dark fraction of panel width)
  V_LINE_FRAC  = 0.40  (vertical line: dark fraction of panel height)
  STRONG_FRAC  = 0.85  (strong full-width line: dark fraction of page width)
  PANEL_MIN_H  = 1000  (min band height to call a panel; rows/headers <= ~120 px)
  UPSCALE      = 2     (LANCZOS, for the agent's visual read; fixed, not tuned)
  TILE_OVERLAP = 40    (source px overlap between adjacent tiles)
  TILE_MAX_DIM = 900   (max source-px extent of a tile on either axis)
"""
import hashlib, json, os, sys
from PIL import Image

TIFF = "E:/ChimeraWork/vanhoof2-agent/tools/science_funnel/data/vanhoof_forearm/JOA-238-321-s002.tif"
EXPECT_SHA = "cb9e91be3d2345182b6d2b956245b76905243d4bbf37fff79c3d96a802e5debe"
LANE = "E:/ChimeraWork/vanhoof2-agent/tools/science_funnel/validation/vanhoof_transcription_20260920"
STAGE = "E:/ChimeraWork/vanhoof2-staging"
TILEDIR = STAGE + "/s2_tiles"
INK_MAX = 100
H_LINE_FRAC = 0.40
V_LINE_FRAC = 0.40
PANEL_BANDS = None  # set in main() as measured constants
UPSCALE = 2
TILE_OVERLAP = 40
TILE_MAX_DIM = 900

def sha_bytes(b): return hashlib.sha256(b).hexdigest()

def groups(idxs, gap=2):
    out = []
    for i in idxs:
        if out and i - out[-1][1] <= gap:
            out[-1][1] = i
        else:
            out.append([i, i])
    return out

def bands(line_groups):
    """intervals between consecutive line centers"""
    centers = [ (a+b)//2 for a,b in line_groups ]
    return [ (centers[i], centers[i+1]) for i in range(len(centers)-1) ]

def main():
    h = hashlib.sha256()
    with open(TIFF, "rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    if h.hexdigest() != EXPECT_SHA:
        sys.exit("SHA MISMATCH: " + h.hexdigest())

    im = Image.open(TIFF)
    rgb = im.convert("RGB")
    os.makedirs(STAGE, exist_ok=True)
    os.makedirs(TILEDIR, exist_ok=True)
    # clear old tiles so the manifest pins only current bytes
    for name in os.listdir(TILEDIR):
        os.remove(os.path.join(TILEDIR, name))
    g = rgb.convert("L")
    w, hgt = g.size
    px = g.load()

    # full-width horizontal lines (both panels' borders + long row lines)
    hrows = []
    step = 3
    for y in range(hgt):
        ink = sum(1 for x in range(0, w, step) if px[x, y] <= INK_MAX)
        if ink / (w/step) >= H_LINE_FRAC:
            hrows.append(y)
    hgroups = groups(hrows)
    hcenters = [ (a+b)//2 for a,b in hgroups ]
    # panel bands: MEASURED CONSTANTS, not searched -- from the full-width ruling-line
    # list of these pinned bytes (stage-1 method: INK<=100, dark-frac>=0.55, sample /3):
    # P1 y 14..1651, P2 y 1733..3076; the y=3273 group is a page-edge artifact, the
    # 1891->2009 gap is a merged-cell region (partial lines), not a panel boundary.
    # The script ASSERTS the detected line list still contains these bounds (+/-3 px):
    # a check, never a search.
    PANEL_BANDS = [(14, 1651), (1733, 3076)]
    for lo, hi in PANEL_BANDS:
        near = [c for c in hcenters if abs(c-lo) <= 3 or abs(c-hi) <= 3]
        if len(near) < 2:
            sys.exit(f"panel band ({lo},{hi}) not confirmed by detected lines: {near}")
    panels_y = PANEL_BANDS

    manifest = {"source": {"path": TIFF, "sha256": EXPECT_SHA, "mode_source": im.mode,
                           "width": w, "height": hgt},
                "constants": {"INK_MAX": INK_MAX, "H_LINE_FRAC": H_LINE_FRAC,
                              "V_LINE_FRAC": V_LINE_FRAC, "PANEL_BANDS": PANEL_BANDS,
                              "UPSCALE": UPSCALE, "TILE_OVERLAP": TILE_OVERLAP,
                              "TILE_MAX_DIM": TILE_MAX_DIM},
                "full_width_h_lines": hcenters,
                "panels": []}

    for pi, (y0, y1) in enumerate(panels_y, start=1):
        # vertical lines within this panel band
        vcols = []
        span = (y1 - y0) / 3.0
        for x in range(w):
            ink = sum(1 for y in range(y0, y1, 3) if px[x, y] <= INK_MAX)
            if ink / span >= V_LINE_FRAC:
                vcols.append(x)
        vg = groups(vcols)
        vcenters = [ (a+b)//2 for a,b in vg ]
        px0, px1 = vcenters[0], vcenters[-1]
        # row lines within panel (span the panel's table width)
        rlines = []
        tspan = (px1 - px0) / 3.0
        for y in range(y0, y1+1):
            ink = sum(1 for x in range(px0, px1, 3) if px[x, y] <= INK_MAX)
            if ink / tspan >= H_LINE_FRAC:
                rlines.append(y)
        rg = groups(rlines)
        rcenters = [ (a+b)//2 for a,b in rg ]
        panel = {"panel": f"P{pi}", "y0": y0, "y1": y1,
                 "x0": px0, "x1": px1,
                 "v_lines": vcenters, "row_lines": rcenters}
        manifest["panels"].append(panel)

    # tile grid per panel (fixed rule: TILE_MAX_DIM with TILE_OVERLAP)
    tiles = []
    for panel in manifest["panels"]:
        pi = panel["panel"]
        tx0, tx1 = max(0, panel["x0"]-4), min(w, panel["x1"]+12)
        ty0, ty1 = max(0, panel["y0"]-4), min(hgt, panel["y1"]+8)
        def band_starts(lo, hi):
            if hi - lo <= TILE_MAX_DIM:
                return [lo]
            starts = []
            s = lo
            while True:
                starts.append(s)
                if s + TILE_MAX_DIM >= hi:
                    break
                s = s + TILE_MAX_DIM - TILE_OVERLAP
            return starts
        xs = band_starts(tx0, tx1)
        ys = band_starts(ty0, ty1)
        for yi, sy in enumerate(ys, start=1):
            for xi, sx in enumerate(xs, start=1):
                ex = min(sx + TILE_MAX_DIM, tx1)
                ey = min(sy + TILE_MAX_DIM, ty1)
                name = f"{pi}_x{xi}_y{yi}.png"
                crop = rgb.crop((sx, sy, ex, ey))
                crop = crop.resize(((ex-sx)*UPSCALE, (ey-sy)*UPSCALE), Image.LANCZOS)
                path = os.path.join(TILEDIR, name)
                crop.save(path, format="PNG")
                with open(path, "rb") as f:
                    digest = sha_bytes(f.read())
                tiles.append({"tile": name, "panel": pi,
                              "x0": sx, "y0": sy, "x1": ex, "y1": ey,
                              "w_px": (ex-sx)*UPSCALE, "h_px": (ey-sy)*UPSCALE,
                              "sha256": digest})
    manifest["tiles"] = tiles
    manifest["passA_order"] = [t["tile"] for t in tiles]  # forward, row-major
    manifest["passB_order"] = [t["tile"] for t in reversed(tiles)]  # reverse
    with open(os.path.join(LANE, "crops_manifest.json"), "w", newline="\n") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
    print("panels:", [(p["panel"], p["y0"], p["y1"], p["x0"], p["x1"]) for p in manifest["panels"]])
    print("tiles:", len(tiles))
    for t in tiles:
        print(t["tile"], (t["x0"], t["y0"], t["x1"], t["y1"]), t["sha256"][:12])

if __name__ == "__main__":
    main()
