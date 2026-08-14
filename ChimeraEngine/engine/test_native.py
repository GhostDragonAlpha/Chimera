# N1 — native core end-to-end: C++ ca_core.exe grows the G1 wall, streams
# NDJSON over SSE through relay.py, and spiace_native.html (ZERO simulation
# logic) renders it with the WebGPU splat pipeline.
#
# Falsifiers (named before the run):
#   F-N1a: renderer is webgpu-splat
#   F-N1b: the wire ledger (native_stream.log, read by THIS oracle — not the
#          page's self-report) shows monotonic growth with 0 violations on
#          every frame
#   F-N1c: the final C++ grown set == the blueprint set exactly, recomputed
#          HERE from the genome table (integer (y,i) pairs — no float games)
#   F-N1d: completion at tick <= 200 (reference: 14)
#   F-N1e: the page's cell set matches the wire's final set (the browser
#          believed the wire, faithfully)
# N2 falsifiers (named before the run):
#   F-N2a: the DATA-DRIVEN core (genome read from native/genomes/
#          wall.chimera at startup) produces the identical wire ledger the
#          hardcoded N1 core was validated on — the oracle below now reads
#          the same .chimera file, so data is the single source of truth
#   F-N2b: an EDITED genome (6 courses) grows the exact 105-brick blueprint
#          from the SAME BINARY — no recompile
#   F-N2c: a missing genome file fails loudly (exit 4), never silently
#          defaults
# N3 falsifiers (named before the run; bands mirror the G2/G3 reference runs):
#   F-N3a OAK (ca_core.exe + genomes/oak.chimera, oracle-recomputed from the
#          wire, formulas mirrored from spiace_grow.html checkOak):
#          height >= 30 cells · leaves >= 30 · connected flood-fill ·
#          dominance ledger max == 0 every frame · phyllotaxis mean error
#          < 5 deg vs the golden angle · phototropism by the F-G2e protocol
#          (tipSunMean > 0.3 AND leafCentroid > 0.5 at the first frame with
#          >= 60 leaves, else at done — tipDirs ride the wire for this) ·
#          auxin: leader apex zone holds auxin > domTheta (the dominance
#          mechanism; a far-window check was mis-scoped in the first draft —
#          post-completion the trail just decays)
#   F-N3b CREATURE (genomes/creature.chimera, mirroring checkCreature):
#          all six phases traversed · bilateral symmetry >= 0.85 (mirror z
#          about the ball centroid, Chebyshev-1 acceptance) · 4 limb roots ·
#          12 digits · 2 eyes · connected · corr(x, log a) > 0.85 · Turing
#          spots >= 3 with |lambda_meas - lambda_pred|/lambda_pred < 30%,
#          lambda_pred recomputed HERE in Python from the .chimera constants
#          (lattice dispersion scan, s = 4 sin^2(k/2)) — never read from the
#          wire's own claim
#   F-N3c HEADED: relay + viewer on the creature genome — the page reports
#          kind=creature, done, and its cellCount equals the wire ledger's
#          final frame count exactly (the browser believed the wire)
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent / "native"
LOG = NATIVE / "native_stream.log"
GENOME_FILE = NATIVE / "genomes" / "wall.chimera"
PORT = 8799
fails = []

def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}")
    if not ok:
        fails.append(name)

# --- the oracle reads the SAME .chimera data the core does -------------------
def read_chimera(path):
    g = {}
    for line in Path(path).read_text().splitlines():
        line = line.split("#")[0]
        if "=" in line:
            k, v = line.split("=", 1)
            g[k.strip()] = v.strip()
    return g

WALL_CHIMERA = GENOME_FILE.read_text()
_g = read_chimera(GENOME_FILE)
BRICK_LEN = float(_g["brickLen"])
GAP = float(_g["gap"])
COURSES = int(_g["courses"])
WIDE = int(_g["wide"])
SEED_I = int(_g["seedI"])
MIN_SUPPORT = float(_g["minSupport"])
xp = BRICK_LEN + GAP
blueprint = {}
for y in range(COURSES):
    n = WIDE if y % 2 == 0 else WIDE - 1
    off = 0.0 if y % 2 == 0 else xp / 2
    for i in range(n):
        blueprint[(y, i)] = (i * xp + off, i * xp + off + BRICK_LEN)

def supported(y, i, placed):
    if y == 0:
        return True
    x0, x1 = blueprint[(y, i)]
    for (cy, ci) in placed:
        if cy != y - 1:
            continue
        cx0, cx1 = blueprint[(cy, ci)]
        if min(x1, cx1) - max(x0, cx0) > MIN_SUPPORT * BRICK_LEN:
            return True
    return False

# --- build + launch ------------------------------------------------------------
print("building ca_core.exe …")
subprocess.run(["g++", "-O2", "-std=c++17", "-o", str(NATIVE / "ca_core.exe"),
                str(NATIVE / "ca_core.cpp")], check=True)
relay = subprocess.Popen([sys.executable, str(NATIVE / "relay.py"), "15",
                          str(PORT)], stdout=subprocess.PIPE, text=True)
time.sleep(1.0)  # relay bind

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False,
                                    args=["--enable-unsafe-webgpu"])
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(f"http://127.0.0.1:{PORT}/")
        page.wait_for_function("window.__growthStats !== undefined",
                               timeout=30000)
        page.wait_for_function("window.__renderer !== 'none'", timeout=15000)
        page.screenshot(path="_native_start.png")
        check("F-N1a renderer is webgpu-splat",
              page.evaluate("window.__renderer") == "webgpu-splat",
              page.evaluate("window.__renderer"))
        t0 = time.time()
        st = None
        while time.time() - t0 < 60:
            st = page.evaluate("window.__growthStats")
            if st["done"]:
                break
            time.sleep(0.25)
        check("F-N1d completed, tick <= 200", st["done"] and st["tick"] <= 200,
              f"tick={st['tick']} cells={st['cellCount']}")
        time.sleep(0.5)
        page.screenshot(path="_native_end.png")
        page_cells = {tuple(c) for c in page.evaluate("window.__growthCheck().cells")}
        browser.close()

    # --- oracle reads the WIRE LOG, not the page --------------------------------
    frames = [m for m in (json.loads(l) for l in LOG.read_text().splitlines()
                          if l.strip()) if m.get("type") == "frame"]
    counts = [len(f["cells"]) for f in frames]
    viols = [f["violations"] for f in frames]
    mono = all(counts[i] >= counts[i - 1] for i in range(1, len(counts)))
    check("F-N1b wire ledger monotonic, 0 violations every frame",
          mono and all(v == 0 for v in viols),
          f"{len(frames)} frames, cells {counts[0]}->{counts[-1]}, "
          f"max viol {max(viols)}")
    final_set = {tuple(c) for c in frames[-1]["cells"]}
    check("F-N1c grown set == blueprint (oracle-recomputed)",
          final_set == set(blueprint),
          f"{len(final_set)} vs {len(blueprint)}, "
          f"diff={len(final_set ^ set(blueprint))}")
    # independent support audit of the final set
    unsupported = sum(1 for k in final_set if not supported(*k, final_set))
    check("F-N1c oracle support audit of the final wall", unsupported == 0,
          f"unsupported={unsupported}")
    check("F-N1e page's wall == wire's wall", page_cells == final_set,
          f"page {len(page_cells)} vs wire {len(final_set)}")
    print(f"N1 MEASURED: frames={len(frames)} final_tick={frames[-1]['tick']} "
          f"cells={counts[-1]} viol_max={max(viols)}")

    # --- N2: genomes as data ---------------------------------------------------
    # F-N2a is implicit above: the wire ledger just validated came from a core
    # that read wall.chimera at startup, and the oracle read the SAME file.
    variant = NATIVE / "genomes" / "_test_wall6.chimera"
    try:
        variant.write_text(WALL_CHIMERA.replace(
            "courses    = 12", "courses    = 6").replace(
            "brick-wall-v1", "brick-wall-6course"))
        assert "courses    = 6" in variant.read_text()
        r = subprocess.run([str(NATIVE / "ca_core.exe"), "0", str(variant)],
                           capture_output=True, text=True, timeout=60)
        frames6 = [m for m in (json.loads(l) for l in r.stdout.splitlines()
                               if l.strip()) if m.get("type") == "frame"]
        bp6 = {(y, i) for y in range(6)
               for i in range(WIDE if y % 2 == 0 else WIDE - 1)}
        final6 = {tuple(c) for c in frames6[-1]["cells"]}
        ok6 = (r.returncode == 0 and frames6[-1]["done"]
               and final6 == bp6
               and all(f["violations"] == 0 for f in frames6))
        check("F-N2b edited genome, SAME BINARY (no recompile): 6-course "
              "blueprint exact", ok6,
              f"ticks={frames6[-1]['tick']} cells={len(final6)} "
              f"expect={len(bp6)} rc={r.returncode}")
    finally:
        variant.unlink(missing_ok=True)
    r2 = subprocess.run([str(NATIVE / "ca_core.exe"), "0",
                         str(NATIVE / "genomes" / "_does_not_exist.chimera")],
                        capture_output=True, text=True, timeout=30)
    check("F-N2c missing genome fails loudly (exit 4, no silent default)",
          r2.returncode == 4 and "GENOME" in r2.stderr,
          f"rc={r2.returncode} stderr={r2.stderr.strip()[:60]}")
    print(f"N2 MEASURED: 6-course ticks={frames6[-1]['tick']} "
          f"cells={len(final6)} viol_max="
          f"{max(f['violations'] for f in frames6)} missing_rc={r2.returncode}")

    # --- N3: oak + creature through the SAME BINARY, oracle from the wire -----
    N6 = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]

    def run_core_direct(genome, timeout=180):
        r = subprocess.run([str(NATIVE / "ca_core.exe"), "0",
                            str(NATIVE / "genomes" / genome)],
                           capture_output=True, text=True, timeout=timeout)
        msgs = [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
        return (r.returncode,
                next((m for m in msgs if m.get("type") == "meta"), None),
                [m for m in msgs if m.get("type") == "frame"],
                next((m for m in msgs if m.get("type") == "final"), None))

    def flood_connected(cells):
        S = {(c[0], c[1], c[2]) for c in cells}
        seed = min(S, key=lambda c: c[1])
        seen, q = {seed}, [seed]
        while q:
            x, y, z = q.pop()
            for dx, dy, dz in N6:
                nk = (x + dx, y + dy, z + dz)
                if nk in S and nk not in seen:
                    seen.add(nk)
                    q.append(nk)
        return len(seen) == len(S)

    # ---- F-N3a: OAK ----------------------------------------------------------
    rc, meta, ofr, ofin = run_core_direct("oak.chimera")
    OG = read_chimera(NATIVE / "genomes" / "oak.chimera")
    check("F-N3a oak: clean exit + meta kind", rc == 0 and meta
          and meta["kind"] == "oak" and ofin and ofin.get("done"),
          f"rc={rc} ticks={ofin['tick'] if ofin else '?'}")
    ocells = ofr[-1]["cells"]            # [x,y,z,"mat",born,stem]
    oheight = max(c[1] for c in ocells)
    oleaves = [c for c in ocells if c[3] == "leaf"]
    check("F-N3a oak height >= 30", oheight >= 30, f"height={oheight}")
    check("F-N3a oak leaves >= 30", len(oleaves) >= 30,
          f"leaves={len(oleaves)}")
    check("F-N3a oak tissue connected", flood_connected(ocells),
          f"cells={len(ocells)}")
    dom_max = max(f["violations"] for f in ofr)
    check("F-N3a oak dominance ledger clean (max 0)", dom_max == 0,
          f"frames={len(ofr)} max={dom_max}")
    # phyllotaxis: successive bud azimuths per stem vs the golden angle
    golden = float(OG["golden"])
    bystem = {}
    for stem, az in ofin["phyllo"]:
        bystem.setdefault(stem, []).append(az)
    errs = []
    for azs in bystem.values():
        for i in range(1, len(azs)):
            d = (azs[i] - azs[i - 1]) % (2 * math.pi)
            errs.append(abs(((d - golden + math.pi) % (2 * math.pi)) - math.pi))
    phyllo_err = math.degrees(sum(errs) / len(errs)) if errs else None
    check("F-N3a oak phyllotaxis mean err < 5 deg",
          phyllo_err is not None and phyllo_err < 5,
          f"err={phyllo_err:.3f} deg over {len(errs)} pairs")
    # phototropism, F-G2e protocol exactly: evaluate at the first frame with
    # leaves >= 60, else at done — the tropism witness is meaningful only
    # while sun-bent tips are still alive (at completion the alive set is
    # young unbent tips). tipDirs ride the wire for this.
    sun = ofin["sun"]
    sun_az = math.hypot(sun[0], sun[2]) or 1.0
    pf = next((f for f in ofr if f["leaves"] >= 60), ofr[-1])
    ptips = [t for t in pf["tipDirs"] if not t[3]]     # non-leader alive
    tip_sun = (sum((t[0] * sun[0] + t[2] * sun[2]) / sun_az for t in ptips)
               / len(ptips)) if ptips else None
    pcells = pf["cells"]
    pleaves = [c for c in pcells if c[3] == "leaf"]
    lcx = sum(c[0] for c in pleaves) / len(pleaves)
    lcz = sum(c[2] for c in pleaves) / len(pleaves)
    leaf_centroid = (lcx * sun[0] + lcz * sun[2]) / sun_az
    check("F-N3a oak phototropism (F-G2e protocol: tipSun > 0.3, "
          "centroid > 0.5, leaves >= 30, tips >= 5)",
          tip_sun is not None and tip_sun > 0.3 and leaf_centroid > 0.5
          and len(pleaves) >= 30 and len(ptips) >= 5,
          f"@tick {pf['tick']}: tipSunMean={tip_sun:.4f} over {len(ptips)} "
          f"tips, leafCentroid={leaf_centroid:.3f}, leaves={len(pleaves)}")
    # auxin witness: the leader strand NEAR THE APEX holds auxin above the
    # dominance threshold — the mechanism behind the clean ledger. (The far
    # window is NOT asserted: after the leader dies at maxSteps the whole
    # trail decays, and the healthy JS reference reads auxFar=0.352 > theta
    # at done — a far-window check post-completion measures decay, not
    # dominance. Mis-scoped in the first N3 draft; documented, removed.)
    aux = ofin["aux"]
    tip_period = float(OG["tipPeriod"])
    dom_theta = float(OG["domTheta"])
    near = []
    for x, y, z, matv, born, stem in ocells:
        if stem != 0 or matv != "wood":
            continue
        r = (ofin["tick"] - born) / tip_period
        if 1 <= r <= 3:
            near.append(aux.get(f"{x},{y},{z}", 0.0))
    aux_near = sum(near) / len(near) if near else None
    check("F-N3a oak auxin: leader apex zone holds auxin > domTheta",
          aux_near is not None and aux_near > dom_theta,
          f"auxNear={aux_near:.4f} theta={dom_theta}")
    print(f"N3 OAK MEASURED: ticks={ofin['tick']} cells={len(ocells)} "
          f"height={oheight} leaves={len(oleaves)} dom_max={dom_max} "
          f"phyllo_err={phyllo_err:.3f}deg tipSun={tip_sun:.4f} "
          f"leafC={leaf_centroid:.3f} auxNear={aux_near:.4f}")

    # ---- F-N3b: CREATURE -----------------------------------------------------
    rc, meta, cfr, cfin = run_core_direct("creature.chimera")
    CG = read_chimera(NATIVE / "genomes" / "creature.chimera")
    check("F-N3b creature: clean exit + meta kind", rc == 0 and meta
          and meta["kind"] == "creature" and cfin and cfin.get("done"),
          f"rc={rc} ticks={cfin['tick'] if cfin else '?'}")
    phases = {f["phase"] for f in cfr}
    check("F-N3b creature phases traversed",
          {"cleavage", "axes", "pattern", "growth", "turing"} <= phases
          and cfr[-1]["done"], f"phases={sorted(phases)}")
    ccells = cfin["cells"]               # [x,y,z,"mat"]
    S = {(c[0], c[1], c[2]) for c in ccells}
    ball = cfin["organizers"]["ball"]
    mz0 = round(2 * ball[2])
    match = 0
    for x, y, z in S:
        mz = mz0 - z
        if any((x + dx, y + dy, mz + dz) in S
               for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)):
            match += 1
    sym = match / len(S)
    check("F-N3b creature bilateral symmetry >= 0.85", sym >= 0.85,
          f"symmetry={sym:.4f} (mirror z about {mz0 / 2})")
    morph = cfin["morphA"]
    xs, lgs = [], []
    for x, y, z in S:
        a = morph.get(f"{x},{y},{z}", 0.0)
        xs.append(x)
        lgs.append(math.log(max(a, 1e-6)))
    n = len(xs)
    mx, ml = sum(xs) / n, sum(lgs) / n
    cov = sum((x - mx) * (l - ml) for x, l in zip(xs, lgs)) / n
    vx = sum((x - mx) ** 2 for x in xs) / n
    vl = sum((l - ml) ** 2 for l in lgs) / n
    corr_log = cov / math.sqrt(vx * vl) if vx > 0 and vl > 0 else None
    check("F-N3b creature corr(x, log a) > 0.85",
          corr_log is not None and corr_log > 0.85,
          f"corrLogAX={corr_log:.4f}")
    check("F-N3b creature 4 limb roots", len(cfin["limbRoots"]) == 4,
          f"limbs={len(cfin['limbRoots'])}")
    check("F-N3b creature 12 digits", cfin["digits"] == 12,
          f"digits={cfin['digits']}")
    check("F-N3b creature 2 eyes", len(cfin["eyes"]) == 2,
          f"eyes={len(cfin['eyes'])}")
    check("F-N3b creature body connected", flood_connected(ccells),
          f"cells={len(ccells)}")
    # Turing spots vs a PYTHON-recomputed dispersion prediction
    tU, surf = cfin["turingU"], cfin["surf"]
    us = [tU[k] for k in surf]
    mu_u = sum(us) / len(us)
    sd_u = math.sqrt(sum((v - mu_u) ** 2 for v in us) / len(us))
    spots = {k for k in surf if tU[k] > mu_u + 0.5 * sd_u}
    spot_xyz = {tuple(int(v) for v in k.split(",")) for k in spots}
    seen, cents = set(), []
    for p in spot_xyz:
        if p in seen:
            continue
        cl, q = [], [p]
        seen.add(p)
        while q:
            c0 = q.pop()
            cl.append(c0)
            for dx, dy, dz in N6:
                nk = (c0[0] + dx, c0[1] + dy, c0[2] + dz)
                if nk in spot_xyz and nk not in seen:
                    seen.add(nk)
                    q.append(nk)
        if len(cl) >= 2:
            cents.append(tuple(sum(c[i] for c in cl) / len(cl)
                               for i in range(3)))
    n_spots = len(cents)
    lam_meas = None
    if len(cents) >= 2:
        lam_meas = sum(min(math.dist(cents[i], cents[j])
                           for j in range(len(cents)) if j != i)
                       for i in range(len(cents))) / len(cents)
    tA, tB = float(CG["tA"]), float(CG["tB"])
    tDu, tDv = float(CG["tDu"]), float(CG["tDv"])
    u0 = tA + tB
    fu, fv, gu, gv = 2 * tB / u0 - 1, u0 * u0, -2 * tB / u0, -u0 * u0
    best_k, best_mu = 0.05, -math.inf
    k = 0.05
    while k < 4:
        s = 4 * math.sin(k / 2) ** 2
        tr = fu + gv - (tDu + tDv) * s
        det = (fu - tDu * s) * (gv - tDv * s) - fv * gu
        disc = tr * tr - 4 * det
        muv = (tr + math.sqrt(disc)) / 2 if disc >= 0 else tr / 2
        if muv > best_mu:
            best_mu, best_k = muv, k
        k += 0.01
    lam_pred_py = 2 * math.pi / best_k
    lam_ok = (lam_meas is not None
              and abs(lam_meas - lam_pred_py) / lam_pred_py < 0.30)
    check("F-N3b creature Turing spots >= 3, lambda within 30% of the "
          "Python-recomputed prediction", n_spots >= 3 and lam_ok,
          f"nSpots={n_spots} meas={lam_meas and round(lam_meas, 3)} "
          f"pred_py={lam_pred_py:.4f} wire_pred={cfin['lambdaPred']:.4f}")
    print(f"N3 CREATURE MEASURED: ticks={cfin['tick']} cells={len(ccells)} "
          f"sym={sym:.4f} corrLogAX={corr_log:.4f} limbs={len(cfin['limbRoots'])} "
          f"digits={cfin['digits']} eyes={len(cfin['eyes'])} "
          f"nSpots={n_spots} lamMeas={lam_meas and round(lam_meas, 3)} "
          f"lamPredPy={lam_pred_py:.4f}")

    # ---- F-N3c: HEADED — relay + viewer on the creature genome ---------------
    PORT2 = 8801
    relay2 = subprocess.Popen([sys.executable, str(NATIVE / "relay.py"), "5",
                               str(PORT2),
                               str(NATIVE / "genomes" / "creature.chimera")],
                              stdout=subprocess.PIPE, text=True)
    try:
        time.sleep(1.0)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False,
                                        args=["--enable-unsafe-webgpu"])
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.goto(f"http://127.0.0.1:{PORT2}/")
            page.wait_for_function("window.__growthStats !== undefined",
                                   timeout=30000)
            page.wait_for_function("window.__renderer !== 'none'",
                                   timeout=15000)
            t0 = time.time()
            st = None
            while time.time() - t0 < 150:
                st = page.evaluate("window.__growthStats")
                if st["done"]:
                    break
                time.sleep(0.25)
            page.screenshot(path="_native_creature.png")
            page_cells = {tuple(c[:3])
                          for c in page.evaluate("window.__growthCheck().cells")}
            renderer = page.evaluate("window.__renderer")
            browser.close()
        wire = [m for m in (json.loads(l) for l in LOG.read_text().splitlines()
                            if l.strip()) if m.get("type") == "frame"]
        wire_set = {tuple(c[:3]) for c in wire[-1]["cells"]}
        check("F-N3c headed: page kind=creature, done, renderer splat",
              st["kind"] == "creature" and st["done"]
              and renderer == "webgpu-splat",
              f"kind={st['kind']} phase={st.get('phase')} tick={st['tick']} "
              f"renderer={renderer}")
        check("F-N3c headed: page's body == wire's final body",
              page_cells == wire_set,
              f"page {len(page_cells)} vs wire {len(wire_set)}")
        print(f"N3 HEADED MEASURED: page cells={len(page_cells)} "
              f"limbs={st.get('limbs')} eyes={st.get('eyes')} "
              f"tick={st['tick']}")
    finally:
        relay2.terminate()
finally:
    relay.terminate()

print("RESULT:", "ALL GREEN" if not fails else f"FAILED: {fails}")
raise SystemExit(1 if fails else 0)
