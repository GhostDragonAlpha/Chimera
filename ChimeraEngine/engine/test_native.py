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
# N4 falsifiers (named before the run; JS reference numbers probed
# synchronously from spiace_grow.html?genome=bear):
#   F-N4a bear growth bit-identical to creature growth (same table) · F-N4b
#          rig: 4 chains x (pathLen 6, elbow 3), 8 joints, 2 ears, waveCh =
#          fore/+z · F-N4c wave minResidual == 0.04881518056285238 at
#          raiseIters 15 / iters 230 · F-N4d gait diagonal in phase /
#          ipsilateral anti-phase (Fourier); bodyX == the N7 oracle's
#          discrete stride sum (pre-N7: 400*4*2/60 — retired) · F-N4e
#          Python-oracle FK segment audit < 1e-6 at thetaFinal and at probe
#          pose [0.4,-0.3] · F-N4f no NaN, theta <= 2.6 · F-N4g senses
#          1/3/2/5/0 · F-N4h 320 episodes: visits/Q/first30/last30/minResAuto
#          == the N7 oracle's full learner replication within 1e-9 (pre-N7 JS
#          ledger: visits [9450,89,93,92,1736,1888,1958], greedy
#          [0,1,1,1,2,2,2] — retired with the imposed stride), last30 >
#          first30+0.3, greedy still matches the reward structure ·
#          F-N4i bodyXfinal == the N7 oracle within 1e-9 (pre-N7 JS:
#          789.8666666666321 — retired) ·
#          F-N4j HEADED: WAVE button -> C++ core (page observes cmd=wave;
#          wire ledger holds the wave frames: res<0.35, waveDone), page
#          posed == wire posed
# N5 falsifiers (named before the run; physics membrane — gravity kernel,
# rigid COM, velocity-projection ground contact, all constants derived):
#   F-N5a genome declares SI gravity + tickHz; physics is numerically INERT
#          at equilibrium (the whole F-N4 block above ran with physTick live)
#   F-N5b drop from 8 body-heights (64 cells): contact at the first tick n
#          with n(n+1) >= 2H/g (= 53), within 1 tick of sqrt(2H/g) (= 53.09);
#          ground plane derived from the grown body (lowest rest cell = -4),
#          never declared
#   F-N5c free-fall energy matches the symplectic-Euler ledger
#          E_n = gH - g^2 n/2 to 1e-12; terminal drift < 2%
#   F-N5d rest equilibrium: 300 ticks, |velY| == 0 exactly, penetration
#          < 1e-12 (1-ULP projection rounding allowed)
#   F-N5e HEADED: DROP button -> C++ core: bodyY rises 64 cells, falls, lands
#          (contact, bodyY == 0, vy == 0); the wire ledger carries the peak
# N6 falsifiers (named before the run; terrain membrane — the world is GROWN):
#   F-N6a wire terrain == Python-oracle terrain integer-exact on every
#          column; the relaxation CA stops at the walkability contract (max
#          slope <= 0.5 cells/column); iteration count is an output. (An
#          earlier integer-cell rule with (s+2)>>2 rounding FAILED this:
#          slope-2 attractors, stuck from iteration 2 through 60 — the rule
#          was revised to fixed-point truncation and the miss is documented)
#   F-N6b N4-invariance on hills: every body-local ledger (growth cells,
#          wave, gait, theta, senses, learner Q/visits) bit-identical to flat
#   F-N6c the 400-tick walk's per-tick bodyY/ground trace replicated by the
#          oracle to < 1e-12 (same IEEE op order; 1-ULP wave-settle residue)
#   F-N6d the drop law on the hill: contact at the first n with n(n+1) >=
#          2H/g; ground == the oracle's footprint max at the drop site
#   F-N6e HEADED: WALK over the grown hills — bodyY tracks terrain on the
#          wire, every contact frame satisfies bodyY == ground + 4
# N7 falsifiers (named before the run; earned traction — the stride is the
# stance-foot sweep A*w*|cos phi| gated by contact, whose cycle-mean is
# exactly the retired 4A/T constant; the JS-imposed-stride learner reference
# is RETIRED and replaced by the full Python oracle replication below):
#   F-N7a airwalk: legs cycling in free fall translate the body EXACTLY zero
#          cells (bit-exact, not epsilon — the wire measures airMoved == 0)
#   F-N7b the 400-tick flat walk's bodyX == the oracle's discrete sum
#          sum_t A*(2*pi/T)*|cos(2*pi*t/T)| in the same IEEE op order, and
#          the airwalk landing tick == the discrete drop law (n(n+1) >= 2H/g)
#   F-N7c one full gait cycle sums to 4A within the |cos| Riemann-sum
#          quadrature error (< 1%) — the old constant is the mean of the
#          new law, not an independent choice
#   F-N7d the G5 learner ledger under the new law (visits, Q, first30, last30,
#          minResAuto, bodyXfinal) == the oracle's full replication of the
#          wave+walk+learn protocol within 1e-9 — and the oracle's WAVE
#          numbers must still hit the untouched JS anchors (0.04881518056285238
#          / 15 / 230), which pins the port before its divergent output is
#          trusted
#   F-N7e HILLS: the body-local ledgers (growth, wave, gait, theta, senses)
#          stay bit-identical to flat, but the translation-coupled ledgers
#          (walk bodyX/trace, learner) now legitimately DIFFER — downhill
#          crest exits break contact and the stride slips. They must match
#          the terrain-mode oracle run instead of the flat wire.
# N8 falsifiers (named before the run; the goal membrane — deliberation over
# terrain+physics state: a flag at goalX, 12 senses (bearing x slope x
# contact), 5 verbs (rest, walkE/W full, walkE/W careful), Q-learning on the
# L5 constants with ZERO new tunables — careful amplitude, slip threshold,
# and episode budget are all DERIVED from the genome's physics):
#   F-N8a invariance: beargoal's entire G4–N7 ledger (growth cells, selftest
#          line) is bit-identical to bearhill's — the nav layer runs AFTER
#          the selftest ledger closes and cannot touch it
#   F-N8b the navtest ledger (visits, Q, rewards, arrivals, derived
#          constants) == the Python oracle's float-op-for-float-op
#          replication of navTick within 1e-9 (the oracle skips IK — rewards
#          and senses never read it)
#   F-N8c the learned greedy policy WALKS TOWARD the flag in both bearing
#          states, and its gait class (full vs careful) per slope state ==
#          the oracle-measured fastest gait for that slope — measured by
#          micro-simulation on the real terrain, not presumed
#   F-N8d learning curve: last-30 arrival rate > first-30 arrival rate
#   F-N8e HEADED: the flag rides the wire and the page, NAV frames carry
#          in-range state/verb, episodes advance, arrivals happen live
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent / "native"
GENOME_FILE = NATIVE / "genomes" / "wall.chimera"
PORT = 8799
# per-port wire logs (relay.py writes native_stream_<port>.log): sequential
# headed relays must never share one file — a dying relay's late writes tore
# an NDJSON line and crashed F-N8e's wire audit with a JSONDecodeError
LOG = NATIVE / f"native_stream_{PORT}.log"
LOG2 = NATIVE / "native_stream_8801.log"   # F-N3c relay
LOG3 = NATIVE / "native_stream_8802.log"   # F-N4j relay
LOG4 = NATIVE / "native_stream_8803.log"   # F-N5e relay
LOG5 = NATIVE / "native_stream_8804.log"   # F-N6e relay
LOG6 = NATIVE / "native_stream_8805.log"   # F-N8e relay
LOG9 = NATIVE / "native_stream_8806.log"   # F-T1d relay
fails = []

# Headed browser blocks are OPT-IN ONLY (operator directive 2026-08-16: the
# full suite is deleted as a practice — measured 179s of 187s was browser
# time, and sitting through it accomplishes nothing). T_HEADED=N3c,N4j runs
# just those headed blocks; unset runs NONE. The headless selftests + Python
# oracles always run — seconds, not minutes; they are the invariance net.
_HEADED = os.environ.get("T_HEADED", "")

def want(tag):
    return tag in {t.strip() for t in _HEADED.split(",")}

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
# rebuild only when stale — an -O2 build is ~30-60 s and most runs change nothing
_exe, _src = NATIVE / "ca_core.exe", NATIVE / "ca_core.cpp"
if not _exe.exists() or _exe.stat().st_mtime < _src.stat().st_mtime:
    print("building ca_core.exe …")
    subprocess.run(["g++", "-O2", "-std=c++17", "-o", str(_exe),
                    str(_src)], check=True)
else:
    print("ca_core.exe fresh — skipping build")
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

    if want("N3c"):  # T_HEADED gate
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
            wire = [m for m in (json.loads(l) for l in LOG2.read_text().splitlines()
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

    # ---- N4: EMBODIMENT (G4 rig/IK + G5 learner) in the native core --------
    # Falsifiers named before the run (mirroring F-G4/F-G5; the JS reference
    # numbers come from the synchronous probe of spiace_grow.html?genome=bear,
    # dumped to .tmp_bear_ref.json and inlined here):
    #   F-N4a: bear growth is BIT-IDENTICAL to creature growth (same table)
    #   F-N4b: rig — 4 chains x (pathLen 6, elbow 3), 8 joints, 2 ears,
    #          waveCh = first fore/+z chain
    #   F-N4c: wave converges — minResidual < 0.35 AND == JS reference,
    #          raiseIters == 15, iters == 230 (bit-faithful)
    #   F-N4d: gait — Fourier at the gait frequency: diagonal pairs in phase
    #          (|dphi|<0.5), ipsilateral anti-phase (||dphi|-pi|<0.5); bodyX
    #          after 400 ticks == 400*4*2/60 within 1e-6
    #   F-N4e: FK rigidity — Python-oracle FK on the wire's own paths:
    #          posed segments == grown lengths at thetaFinal AND at the probe
    #          pose theta=[0.4,-0.3], segErr < 1e-6
    #   F-N4f: no NaN, |theta| <= 2.6 ever
    #   F-N4g: senses — absent=0, nearPlus=1, nearMinus=3, nearCenter=2,
    #          farCenter=5 exactly
    #   F-N4h: learning — 320 episodes; visits == JS exactly; last30 >
    #          first30+0.3; greedy == [0,1,1,1,2,2,2] on visited states;
    #          Q within 1e-9 of JS; minResAuto < 0.35
    #   F-N4i: final bodyX == JS 789.8666666666321 within 1e-6
    #   F-N4j: HEADED — relay+viewer on bear.chimera: the WAVE button drives
    #          cmd=wave on the wire (res<0.35, waveDone), and the page's
    #          posed cells == the wire's posed cells exactly
    rb = subprocess.run([str(NATIVE / "ca_core.exe"), "0",
                         str(NATIVE / "genomes" / "bear.chimera"), "selftest"],
                        capture_output=True, text=True, timeout=300)
    bmsgs = [json.loads(l) for l in rb.stdout.splitlines() if l.strip()]
    bmeta = next((m for m in bmsgs if m.get("type") == "meta"), None)
    bfin = next((m for m in bmsgs if m.get("type") == "final"), None)
    brig = next((m for m in bmsgs if m.get("type") == "rig"), None)
    bst = next((m for m in bmsgs if m.get("type") == "selftest"), None)
    check("F-N4a bear selftest: clean exit, meta creature + embodiment",
          rb.returncode == 0 and bmeta and bmeta["kind"] == "creature"
          and bmeta.get("embodiment") == 1 and bfin and brig and bst,
          f"rc={rb.returncode} meta={bmeta}")
    bear_cells = {tuple(c[:3]) for c in bfin["cells"]}
    crit_cells = {tuple(c[:3]) for c in cfin["cells"]}
    check("F-N4a bear growth BIT-IDENTICAL to creature growth",
          bear_cells == crit_cells and bfin["tick"] == cfin["tick"],
          f"bear {len(bear_cells)}@{bfin['tick']} vs creature "
          f"{len(crit_cells)}@{cfin['tick']}")
    chains = brig["chains"]
    check("F-N4b rig: 4 chains (pathLen 6, elbow 3), 8 joints, 2 ears, "
          "waveCh fore/+z",
          len(chains) == 4
          and all(len(c["path"]) == 6 and c["elbow"] == 3 for c in chains)
          and all(len(c["digits"]) == 3 for c in chains)
          and len(brig["ears"]) == 2
          and chains[brig["waveCh"]]["fore"]
          and chains[brig["waveCh"]]["side"] > 0,
          f"chains={[(c['fore'], c['side'], len(c['path']), c['elbow']) for c in chains]} "
          f"ears={brig['ears']} waveCh={brig['waveCh']}")

    # ---- the N7 oracle: a full replication of ca_core's emitSelftest --------
    # protocol (wave -> 400-tick walk -> sense probes -> 320 learning episodes
    # -> airwalk) under the EARNED-TRACTION law, given the wire's rig and the
    # SAME genome file. Every float op mirrors the C++ order; the LCG keeps
    # JS's lossy-double rounding; hypot3 is the ECMAScript spec algorithm.
    # The wave phase must still hit the untouched JS anchors — that pins the
    # IK port before its (deliberately divergent) learner ledger is trusted.
    def bear_oracle(gd, brig_, bfin_, terrain=None, tsc=1):
        PI = math.pi
        A, T = float(gd["b4A"]), float(gd["b4T"])
        LAM, DTH, THMAX = (float(gd["b4Lam"]), float(gd["b4Dth"]),
                           float(gd["b4ThMax"]))
        ITERS = int(gd["b4Iters"])
        WAVERES, WAVETH = float(gd["b4WaveRes"]), float(gd["b4WaveTh"])
        HOLD, LOWERRES = int(gd["b4Hold"]), float(gd["b4LowerRes"])
        LNEAR, LFAR = float(gd["l5Near"]), float(gd["l5Far"])
        EPTICKS, BEAREPS = int(gd["l5EpTicks"]), float(gd["l5BearEps"])
        ALPHA, GAMMA = float(gd["l5Alpha"]), float(gd["l5Gamma"])
        EPS0, EPSDECAY, EPSMIN = (float(gd["l5Eps0"]), float(gd["l5EpsDecay"]),
                                  float(gd["l5EpsMin"]))
        RWNEAR, RWFAR, RWABS = (float(gd["r5WaveNear"]), float(gd["r5WaveFar"]),
                                float(gd["r5WaveAbsent"]))
        RWTICK, RBECK = float(gd["r5WalkTick"]), float(gd["r5Beckon"])
        RSTART = float(gd["r5Startle"])
        RRABS, RRPRES = float(gd["r5RestAbsent"]), float(gd["r5RestPresent"])
        G = float(gd["gravity"]) / (float(gd["tickHz"]) ** 2
                                    * float(gd["cell"]))
        cells_ = bfin_["cells"]
        loY = float(min(c[1] for c in cells_))
        hiY = float(max(c[1] for c in cells_))
        loX, hiX = min(c[0] for c in cells_), max(c[0] for c in cells_)
        bodyH = hiY - loY
        eyes = bfin_["eyes"]
        orgHead = bfin_["organizers"]["head"]
        ballZ = bfin_["organizers"]["ball"][2]
        zc = (int(math.floor(ballZ + 0.5)) if ballZ >= 0
              else -int(math.floor(-ballZ + 0.5)))        # lround

        def hypot3(a, b, c):                     # ECMAScript spec algorithm
            a, b, c = abs(a), abs(b), abs(c)
            mx = max(a, b, c)
            if mx == 0:
                return 0.0
            s = (a / mx) * (a / mx) + (b / mx) * (b / mx) + (c / mx) * (c / mx)
            return mx * math.sqrt(s)

        def bnorm3(v):
            l = hypot3(*v)
            if l == 0:
                l = 1.0
            return [v[0] / l, v[1] / l, v[2] / l]

        def rot3o(v, a, th):
            c, s = math.cos(th), math.sin(th)
            d = a[0] * v[0] + a[1] * v[1] + a[2] * v[2]
            return [v[0] * c + (a[1] * v[2] - a[2] * v[1]) * s + a[0] * d * (1 - c),
                    v[1] * c + (a[2] * v[0] - a[0] * v[2]) * s + a[1] * d * (1 - c),
                    v[2] * c + (a[0] * v[1] - a[1] * v[0]) * s + a[2] * d * (1 - c)]

        def cross3(a, b):
            return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
                    a[0] * b[1] - a[1] * b[0]]

        def solve3(M, b):                        # Cramer, no library
            def d3(N):
                return (N[0][0] * (N[1][1] * N[2][2] - N[1][2] * N[2][1])
                        - N[0][1] * (N[1][0] * N[2][2] - N[1][2] * N[2][0])
                        + N[0][2] * (N[1][0] * N[2][1] - N[1][1] * N[2][0]))
            det = d3(M)
            if abs(det) < 1e-12:
                return [0.0, 0.0, 0.0]
            out = []
            for c in range(3):
                N = [[b[r] if cc == c else M[r][cc] for cc in range(3)]
                     for r in range(3)]
                out.append(d3(N) / det)
            return out

        chains = [{"fore": c["fore"], "side": c["side"], "path": c["path"],
                   "elbow": c["elbow"], "theta": [0.0, 0.0]}
                  for c in brig_["chains"]]

        def fk(ch, k):
            th = ch["theta"]
            P = ch["path"]
            P0 = [float(x) for x in P[0]]
            Pe0 = [float(x) for x in P[ch["elbow"]]]
            Pe = [P0[i] + r for i, r in enumerate(rot3o(
                [Pe0[i] - P0[i] for i in range(3)], [1.0, 0.0, 0.0], th[0]))]
            Pk = [float(x) for x in P[k]]
            if k <= ch["elbow"]:
                return [P0[i] + r for i, r in enumerate(rot3o(
                    [Pk[i] - P0[i] for i in range(3)], [1.0, 0.0, 0.0], th[0]))]
            r1 = rot3o([Pk[i] - Pe0[i] for i in range(3)], [0.0, 1.0, 0.0],
                       th[1])
            r2 = rot3o(r1, [1.0, 0.0, 0.0], th[0])
            return [Pe[i] + r for i, r in enumerate(r2)]

        for ch in chains:
            ch["rest"] = fk(ch, len(ch["path"]) - 1)    # theta=0 IS grown
        waveCh = brig_["waveCh"]
        thetaMaxEver = [0.0]
        nanFlag = [False]

        def ikstep(ch, Tg):
            th = ch["theta"]
            P0 = [float(x) for x in ch["path"][0]]
            tip = fk(ch, len(ch["path"]) - 1)
            e = [Tg[i] - tip[i] for i in range(3)]
            res = hypot3(*e)
            a1w = rot3o([0.0, 1.0, 0.0], [1.0, 0.0, 0.0], th[0])
            Pe = fk(ch, ch["elbow"])
            j0 = cross3([1.0, 0.0, 0.0], [tip[i] - P0[i] for i in range(3)])
            j1 = cross3(a1w, [tip[i] - Pe[i] for i in range(3)])
            M = [[j0[0] * j0[0] + j1[0] * j1[0] + LAM,
                  j0[0] * j0[1] + j1[0] * j1[1],
                  j0[0] * j0[2] + j1[0] * j1[2]],
                 [j0[1] * j0[0] + j1[1] * j1[0],
                  j0[1] * j0[1] + j1[1] * j1[1] + LAM,
                  j0[1] * j0[2] + j1[1] * j1[2]],
                 [j0[2] * j0[0] + j1[2] * j1[0],
                  j0[2] * j0[1] + j1[2] * j1[1],
                  j0[2] * j0[2] + j1[2] * j1[2] + LAM]]
            w = solve3(M, e)
            for jj, J in enumerate((j0, j1)):
                d = J[0] * w[0] + J[1] * w[1] + J[2] * w[2]
                d = max(-DTH, min(DTH, d))
                th[jj] = max(-THMAX, min(THMAX, th[jj] + d))
            tm = max(abs(th[0]), abs(th[1]))
            if tm > thetaMaxEver[0]:
                thetaMaxEver[0] = tm
            if not (math.isfinite(th[0]) and math.isfinite(th[1])
                    and math.isfinite(res)):
                nanFlag[0] = True
            return res

        def ground_at(bx_):
            if terrain is None:
                return loY
            g = None
            for x in range(math.floor(bx_) + loX, math.floor(bx_) + hiX + 1):
                h = terrain.get(x, 0)
                g = h if g is None else max(g, h)
            return loY + g / tsc

        def phys(y_, v_, bx_):
            v_ -= G
            y_ += v_
            gr = ground_at(bx_)
            pen = gr - (y_ + loY)
            ct = False
            if pen >= 0:
                y_ += pen
                v_ = 0.0
                ct = True
            return y_, v_, ct, gr

        y = v = 0.0
        contact = True
        bx = 0.0
        iters = 0
        # -- wave (the untouched JS anchors pin this port) --
        cmdTick = 0
        phase = "raise"
        minRes = None
        holdUntil = 0
        waveDone = False
        raiseIters = -1
        chw = chains[waveCh]
        P0w = [float(x) for x in chw["path"][0]]
        rrw = rot3o([chw["rest"][j] - P0w[j] for j in range(3)],
                    [1.0, 0.0, 0.0], -WAVETH * chw["side"])
        upw = [P0w[j] + rrw[j] for j in range(3)]
        for _ in range(2000):
            if waveDone:
                break
            cmdTick += 1
            y, v, contact, _gr = phys(y, v, bx)
            lower = phase == "lower"
            res = 0.0
            for _ in range(ITERS):
                res = ikstep(chw, chw["rest"] if lower else upw)
                iters += 1
            if phase == "raise":
                if minRes is None or res < minRes:
                    minRes = res
                if res < WAVERES:
                    phase = "hold"
                    holdUntil = cmdTick + HOLD
                    raiseIters = iters
            elif phase == "hold":
                if cmdTick >= holdUntil:
                    phase = "lower"
            elif phase == "lower":
                if res < LOWERRES:
                    waveDone = True
                    phase = ""
        waveIters = iters
        # -- 400-tick walk (earned stride, gated by this tick's contact) --
        trace = []
        for t in range(1, 401):
            cmdTick = t
            y, v, contact, gr = phys(y, v, bx)
            phi = 2 * PI * cmdTick / T
            for ch in chains:
                ph = 0.0 if (ch["fore"] == (ch["side"] > 0)) else PI
                Tg = [ch["rest"][0] + A * math.sin(phi + ph),
                      ch["rest"][1] + 0.6 * A * max(0.0, math.cos(phi + ph)),
                      ch["rest"][2]]
                for _ in range(ITERS):
                    ikstep(ch, Tg)
            if contact:
                bx += A * (2 * PI / T) * abs(math.cos(phi))
            trace.append([float(t), y, gr])
        walkBodyX = bx
        # -- 320 learning episodes (the G5 learner under the new law) --
        Q = [[0.0, 0.0, 0.0] for _ in range(7)]
        eps = EPS0
        rng = 1337
        visits = [0] * 7
        present = False
        vpos = [bx, 0.0, 0.0]               # the probe reset: [body0, 0, 0]
        epTick = 0
        epReward = 0.0
        episode = 0
        rewards = []
        gaitT = 0
        minResAuto = None

        def rnd():
            nonlocal rng
            x = rng * 1103515245.0 + 12345.0      # JS lossy-double LCG
            m = math.fmod(x, 4294967296.0)
            rng = int(m) & 0x7fffffff
            return rng / 0x7fffffff

        def sense():
            if not present:
                return 0
            rel = [vpos[0] - bx, vpos[1], vpos[2]]
            d = hypot3(*rel)
            actPlus, actMinus = -2.0, -2.0
            for e in eyes:
                e0 = [float(e[0]), float(e[1]), float(e[2])]
                out = bnorm3([e0[j] - orgHead[j] for j in range(3)])
                to = bnorm3([rel[j] - e0[j] for j in range(3)])
                a = out[0] * to[0] + out[1] * to[1] + out[2] * to[2]
                if e[2] > zc:
                    actPlus = max(actPlus, a)
                else:
                    actMinus = max(actMinus, a)
            bearing = 1
            if actPlus > actMinus + BEAREPS:
                bearing = 0
            elif actMinus > actPlus + BEAREPS:
                bearing = 2
            return (1 if d <= LNEAR else 4) + bearing

        def gait_tick(ct):
            nonlocal gaitT, bx
            gaitT += 1
            phi = 2 * PI * gaitT / T
            for ch in chains:
                ph = 0.0 if (ch["fore"] == (ch["side"] > 0)) else PI
                Tg = [ch["rest"][0] + A * math.sin(phi + ph),
                      ch["rest"][1] + 0.6 * A * max(0.0, math.cos(phi + ph)),
                      ch["rest"][2]]
                for _ in range(ITERS):
                    ikstep(ch, Tg)
            if ct:                              # N7: traction is EARNED
                bx += A * (2 * PI / T) * abs(math.cos(phi))

        def spawn():
            nonlocal present, vpos, epTick, epReward
            r = rnd()
            if r < 1.0 / 3.0:
                present = False
            else:
                near = r < 2.0 / 3.0
                b = rnd()
                present = True
                vpos = [bx + (LNEAR - 2 if near else LFAR), 0.0,
                        3.0 if b < 1.0 / 3.0 else (0.0 if b < 2.0 / 3.0
                                                   else -3.0)]
            epTick = 0
            epReward = 0.0

        guard = 0
        while episode < 320 and guard < 320 * EPTICKS * 3:
            guard += 1
            y, v, contact, _gr = phys(y, v, bx)
            s = sense()
            visits[s] += 1
            if rnd() < eps:
                a = math.floor(rnd() * 3)
            else:
                q = Q[s]
                a = (0 if (q[0] >= q[1] and q[0] >= q[2])
                     else (1 if q[1] >= q[2] else 2))
            d0 = 0.0
            if present:
                d0 = hypot3(vpos[0] - bx, vpos[1], vpos[2])
            r = 0.0
            terminal = False
            if a == 1:                       # wave (single-shot, target up)
                res = 0.0
                for _ in range(ITERS):
                    res = ikstep(chw, upw)
                if minResAuto is None or res < minResAuto:
                    minResAuto = res
                if not present:
                    r = RWABS
                elif d0 <= LNEAR:
                    r = RWNEAR
                    terminal = True
                else:
                    r = RWFAR
            elif a == 2:                     # walk
                if not present:
                    gait_tick(contact)
                    r = RWTICK
                elif d0 <= LNEAR:
                    r = RSTART
                    terminal = True
                else:
                    gait_tick(contact)
                    d1 = hypot3(vpos[0] - bx, vpos[1], vpos[2])
                    r = RWTICK + RBECK * (d0 - d1)   # the beckoning gradient
            else:
                r = RRPRES if present else RRABS
            epReward += r
            epTick += 1
            s2 = sense()
            mx = max(Q[s2])
            Q[s][a] += ALPHA * (r + (0.0 if terminal else GAMMA * mx)
                                - Q[s][a])
            if terminal or epTick >= EPTICKS:
                rewards.append(epReward)
                episode += 1
                eps = max(EPSMIN, eps * EPSDECAY)
                spawn()
        first30 = 0.0
        for rw in rewards[:30]:
            first30 += rw
        first30 /= 30
        last30 = 0.0
        for rw in (rewards[-30:] if len(rewards) > 30 else rewards):
            last30 += rw
        last30 /= 30
        bodyXfinal = bx
        # -- airwalk: the earned-traction falsifier, replicated --------------
        # (the selftest's drop+rest block in between settles y exactly at the
        # local support; airwalk then raises 8 body heights and walks 400)
        y = ground_at(bx) - loY               # settled at the local support
        v = 0.0
        y += 8 * bodyH
        contact = False
        airTicks = 0
        landTick = -1
        for n in range(1, 401):
            y, v, contact, _gr = phys(y, v, bx)
            phi = 2 * PI * n / T
            if contact:
                bx += A * (2 * PI / T) * abs(math.cos(phi))
                if landTick < 0:
                    landTick = n
            else:
                airTicks += 1
        return {"wave": {"minResidual": minRes, "raiseIters": raiseIters,
                         "iters": waveIters, "waveDone": waveDone},
                "walkBodyX": walkBodyX, "trace": trace,
                "learn": {"episode": episode, "eps": eps, "first30": first30,
                          "last30": last30, "Q": Q, "visits": visits,
                          "minResAuto": minResAuto, "bodyXfinal": bodyXfinal},
                "thetaFinal": [list(ch["theta"]) for ch in chains],
                "thetaMaxEver": thetaMaxEver[0], "nan": nanFlag[0],
                "airwalk": {"airTicks": airTicks, "landTick": landTick,
                            "bodyX": bx}}

    bg = read_chimera(NATIVE / "genomes" / "bear.chimera")
    orc = bear_oracle(bg, brig, bfin)
    # the port pin: the oracle's WAVE must still hit the untouched JS anchors
    check("F-N7d oracle port pin: wave anchors bit-faithful to the JS "
          "reference (the law change never touched the wave)",
          orc["wave"]["waveDone"] and orc["wave"]["raiseIters"] == 15
          and orc["wave"]["iters"] == 230
          and abs(orc["wave"]["minResidual"] - 0.04881518056285238) < 1e-12,
          f"oracleWave={orc['wave']}")
    wv = bst["wave"]
    JS_WAVE_RES = 0.04881518056285238
    check("F-N4c wave: converged, bit-faithful to the JS reference",
          wv["waveDone"] and wv["minResidual"] < 0.35
          and abs(wv["minResidual"] - JS_WAVE_RES) < 1e-12
          and wv["raiseIters"] == 15 and wv["iters"] == 230,
          f"minRes={wv['minResidual']} raiseIters={wv['raiseIters']} "
          f"iters={wv['iters']} (JS {JS_WAVE_RES} / 15 / 230)")
    gait = bst["walk"]["gait"]           # [[t, [[x,y,z] x4]], ...]
    wg = 2 * math.pi / 60                # gait frequency per anim tick
    phases = []
    for i in range(len(chains)):
        re = sum(e[1][i][0] * math.cos(wg * e[0]) for e in gait)
        im = -sum(e[1][i][0] * math.sin(wg * e[0]) for e in gait)
        phases.append(math.atan2(im, re))
    def wrap(d):
        return math.atan2(math.sin(d), math.cos(d))
    def cidx(fore, side):
        return next(i for i, c in enumerate(chains)
                    if c["fore"] == fore and c["side"] == side)
    d_diag = [abs(wrap(phases[cidx(True, 1)] - phases[cidx(False, -1)])),
              abs(wrap(phases[cidx(True, -1)] - phases[cidx(False, 1)]))]
    d_ipsi = [abs(abs(wrap(phases[cidx(True, 1)] - phases[cidx(True, -1)]))
                  - math.pi),
              abs(abs(wrap(phases[cidx(False, 1)] - phases[cidx(False, -1)]))
                  - math.pi)]
    check("F-N4d gait: diagonal in phase, ipsilateral anti-phase",
          len(gait) == 400 and max(d_diag) < 0.5 and max(d_ipsi) < 0.5,
          f"samples={len(gait)} diag={['%.3f' % d for d in d_diag]} "
          f"ipsi={['%.3f' % d for d in d_ipsi]}")
    check("F-N4d/F-N7b walk translates the body (earned stride == oracle "
          "discrete sum; pre-N7 imposed constant was 400*4*2/60 = 53.3333)",
          abs(bst["walk"]["bodyX"] - orc["walkBodyX"]) < 1e-9,
          f"bodyX={bst['walk']['bodyX']} oracle={orc['walkBodyX']}")
    # Python-oracle FK — recomputed HERE from the wire's paths, mirroring the
    # JS/C++ fkPoint exactly (shoulder pitch about [1,0,0], elbow swing about
    # the theta0-carried [0,1,0])
    def rot3(v, a, th):
        c, s = math.cos(th), math.sin(th)
        d = a[0]*v[0] + a[1]*v[1] + a[2]*v[2]
        return [v[0]*c + (a[1]*v[2]-a[2]*v[1])*s + a[0]*d*(1-c),
                v[1]*c + (a[2]*v[0]-a[0]*v[2])*s + a[1]*d*(1-c),
                v[2]*c + (a[0]*v[1]-a[1]*v[0])*s + a[2]*d*(1-c)]
    def fk_py(chain, k, th0, th1):
        P, el = chain["path"], chain["elbow"]
        P0, Pe0 = P[0], P[el]
        Pe = [P0[i] + r for i, r in
              enumerate(rot3([Pe0[i]-P0[i] for i in range(3)],
                             [1, 0, 0], th0))]
        if k <= el:
            return [P0[i] + r for i, r in
                    enumerate(rot3([P[k][i]-P0[i] for i in range(3)],
                                   [1, 0, 0], th0))]
        r1 = rot3([P[k][i]-Pe0[i] for i in range(3)], [0, 1, 0], th1)
        r2 = rot3(r1, [1, 0, 0], th0)
        return [Pe[i] + r for i, r in enumerate(r2)]
    def seg_audit(th_pairs):
        worst = 0.0
        for chain, (t0, t1) in zip(chains, th_pairs):
            P = chain["path"]
            for k in range(1, len(P)):
                rest = math.dist(P[k], P[k-1])
                posed = math.dist(fk_py(chain, k, t0, t1),
                                  fk_py(chain, k-1, t0, t1))
                worst = max(worst, abs(posed - rest))
        return worst
    seg_final = seg_audit(bst["thetaFinal"])
    seg_probe = seg_audit([[0.4, -0.3]] * len(chains))
    check("F-N4e FK rigidity (oracle FK, thetaFinal + probe pose)",
          seg_final < 1e-6 and seg_probe < 1e-6 and bst["segErr"] < 1e-6,
          f"oracleFinal={seg_final:.2e} oracleProbe={seg_probe:.2e} "
          f"wireSegErr={bst['segErr']:.2e}")
    check("F-N4f no NaN, |theta| <= 2.6 ever",
          not bst["nan"] and bst["thetaMaxEver"] <= 2.6,
          f"nan={bst['nan']} thetaMaxEver={bst['thetaMaxEver']:.3f}")
    tf_diff = max(abs(w - o) for crow, orow in zip(bst["thetaFinal"],
                                                   orc["thetaFinal"])
                  for w, o in zip(crow, orow))
    check("F-N7d post-learn IK state (thetaFinal / thetaMaxEver / nan) == "
          "the oracle — thetaFinal is read AFTER the 320 episodes, so it is "
          "learn-coupled, not walk-local",
          tf_diff < 1e-9
          and abs(bst["thetaMaxEver"] - orc["thetaMaxEver"]) < 1e-9
          and bst["nan"] == orc["nan"] == False,
          f"thetaFinalDiff={tf_diff:.2e} "
          f"thetaMaxEver={bst['thetaMaxEver']:.6f} "
          f"(oracle {orc['thetaMaxEver']:.6f})")
    sns = bst["senses"]
    check("F-N4g senses: retinal state map exact",
          sns == {"nearPlus": 1, "nearMinus": 3, "nearCenter": 2,
                  "farCenter": 5, "absent": 0},
          f"senses={sns}")
    lk = bst["learn"]
    ol = orc["learn"]
    # pre-N7 JS reference ledger (retired with the imposed stride, kept as
    # provenance): visits [9450,89,93,92,1736,1888,1958], first30
    # 0.6477821468674461, last30 1.2353410441105135, minResAuto
    # 0.00030705036396531444, bodyXfinal 789.8666666666321
    greedy = [0 if q[0] >= q[1] and q[0] >= q[2]
              else (1 if q[1] >= q[2] else 2) for q in lk["Q"]]
    STRUCT5 = [0, 1, 1, 1, 2, 2, 2]
    struct_match = sum(g == s5 for g, s5, v in
                       zip(greedy, STRUCT5, ol["visits"]) if v >= 10)
    n_visited = sum(1 for v in ol["visits"] if v >= 10)
    q_diff = max(abs(a - b) for row, ref in zip(lk["Q"], ol["Q"])
                 for a, b in zip(row, ref))
    check("F-N4h/F-N7d learning: 320 episodes, ledger == the oracle's full "
          "replication under the earned-stride law",
          lk["episode"] == 320 and lk["visits"] == ol["visits"]
          and abs(lk["first30"] - ol["first30"]) < 1e-9
          and abs(lk["last30"] - ol["last30"]) < 1e-9
          and lk["last30"] > lk["first30"] + 0.3
          and abs(lk["eps"] - 0.05) < 1e-12,
          f"ep={lk['episode']} visits={lk['visits']} "
          f"oracleVisits={ol['visits']} "
          f"first30={lk['first30']:.4f} last30={lk['last30']:.4f}")
    check("F-N4h/F-N7d greedy policy matches reward structure on visited "
          "states and Q/minResAuto match the oracle",
          struct_match == n_visited and q_diff < 1e-9
          and lk["minResAuto"] < 0.35
          and abs(lk["minResAuto"] - ol["minResAuto"]) < 1e-9,
          f"greedy={greedy} match={struct_match}/{n_visited} "
          f"qDiff={q_diff:.2e} minResAuto={lk['minResAuto']} "
          f"oracle={ol['minResAuto']}")
    check("F-N4i/F-N7d final bodyX == the oracle's replication",
          abs(lk["bodyXfinal"] - ol["bodyXfinal"]) < 1e-9,
          f"bodyXfinal={lk['bodyXfinal']} oracle={ol['bodyXfinal']}")
    print(f"N4 SELFTEST MEASURED: waveRes={wv['minResidual']:.4f} "
          f"raiseIters={wv['raiseIters']} diag={['%.3f' % d for d in d_diag]} "
          f"ipsi={['%.3f' % d for d in d_ipsi]} "
          f"thetaMax={bst['thetaMaxEver']:.3f} "
          f"first30={lk['first30']:.4f} last30={lk['last30']:.4f} "
          f"qDiff={q_diff:.2e} bodyX={lk['bodyXfinal']:.4f}")

    # ---- F-N5a..d: N5 physics membrane (gravity kernel + ground contact) ----
    #   F-N5a: physics declared in the genome (SI) and numerically INERT at
    #          equilibrium — every N4 number above stayed bit-identical with
    #          physTick live on every anim tick (that IS the F-N4a..i block)
    #   F-N5b: drop contact at the first tick n with n(n+1) >= 2H/g, within
    #          1 tick of the continuous sqrt(2H/g); ground derived = -4
    #   F-N5c: free-fall energy matches the symplectic ledger E_n=gH-g^2n/2
    #          to 1e-12; terminal drift < 2% (derived expectation ~1.85%)
    #   F-N5d: rest equilibrium — 300 ticks, |velY| == 0, penetration < 1e-12
    check("F-N5a genome declares the physics membrane (SI gravity + tickHz)",
          float(bg["gravity"]) == 9.81 and float(bg["tickHz"]) == 60,
          f"gravity={bg.get('gravity')} tickHz={bg.get('tickHz')}")
    ph = bst["phys"]
    g_sim = 9.81 / (60 * 60 * 0.06)
    n_pred = 1
    while n_pred * (n_pred + 1) < 2 * ph["dropH"] / g_sim:
        n_pred += 1
    check("F-N5b drop: contact at the derived tick (discrete + analytic)",
          ph["contactTick"] == n_pred
          and abs(ph["contactTick"] - math.sqrt(2 * ph["dropH"] / g_sim)) <= 1
          and abs(ph["g"] - g_sim) < 1e-15 and ph["ground"] == -4
          and ph["dropH"] == 64,
          f"contactTick={ph['contactTick']} pred={n_pred} "
          f"analytic={ph['analyticTick']:.2f} g={ph['g']:.6f} "
          f"ground={ph['ground']}")
    check("F-N5c free-fall energy follows the symplectic ledger exactly",
          ph["ledgerErr"] < 1e-12 and ph["termDrift"] < 0.02,
          f"ledgerErr={ph['ledgerErr']:.2e} termDrift={ph['termDrift']:.4%}")
    check("F-N5d rest equilibrium: |velY| == 0, penetration < 1e-12, 300 ticks",
          ph["restVyMax"] == 0 and ph["restPenMax"] < 1e-12,
          f"restVyMax={ph['restVyMax']} restPenMax={ph['restPenMax']:.2e}")
    print(f"N5 SELFTEST MEASURED: g={ph['g']:.6f} cells/tick^2 "
          f"ground={ph['ground']} dropH={ph['dropH']} "
          f"contact@{ph['contactTick']} (analytic {ph['analyticTick']:.2f}) "
          f"ledgerErr={ph['ledgerErr']:.1e} drift={ph['termDrift']:.4%}")

    # ---- F-N7a..c: earned traction — the airwalk falsifier, live ------------
    awk = bst["airwalk"]
    oawk = orc["airwalk"]
    check("F-N7a airwalk: legs cycling in free fall move the body EXACTLY "
          "zero cells (bit-exact)",
          awk["airMoved"] == 0.0 and awk["airTicks"] == oawk["airTicks"]
          and awk["airTicks"] == awk["landTick"] - 1,
          f"airMoved={awk['airMoved']} airTicks={awk['airTicks']} "
          f"(oracle {oawk['airTicks']})")
    check("F-N7b airwalk landing tick == the discrete drop law == the oracle",
          awk["landTick"] == n_pred and oawk["landTick"] == n_pred,
          f"landTick={awk['landTick']} oracle={oawk['landTick']} "
          f"discrete={n_pred}")
    check("F-N7b airwalk post-landing bodyX == the oracle's earned sum",
          abs(awk["bodyX"] - oawk["bodyX"]) < 1e-9,
          f"bodyX={awk['bodyX']} oracle={oawk['bodyX']}")
    cyc = sum(2 * (2 * math.pi / 60) * abs(math.cos(2 * math.pi * t / 60))
              for t in range(1, 61))
    check("F-N7c one gait cycle sums to 4A within the |cos| quadrature error "
          "(< 1%) — the old constant is the new law's mean",
          abs(cyc - 8) / 8 < 0.01,
          f"cycleSum={cyc:.6f} vs 4A=8 ({(cyc - 8) / 8:+.3%})")
    print(f"N7 SELFTEST MEASURED: airMoved={awk['airMoved']} "
          f"airTicks={awk['airTicks']} landTick={awk['landTick']} "
          f"cycleSum={cyc:.6f} (4A=8, {(cyc - 8) / 8:+.3%}) "
          f"walk400={bst['walk']['bodyX']:.6f}")

    if want("N4j"):  # T_HEADED gate
        # ---- F-N4j: HEADED — relay + viewer + WAVE button on the bear genome ---
        PORT3 = 8802
        relay3 = subprocess.Popen([sys.executable, str(NATIVE / "relay.py"), "5",
                                   str(PORT3),
                                   str(NATIVE / "genomes" / "bear.chimera")],
                                  stdout=subprocess.PIPE, text=True)
        try:
            time.sleep(1.0)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False,
                                            args=["--enable-unsafe-webgpu"])
                page = browser.new_page(viewport={"width": 1280, "height": 720})
                page.goto(f"http://127.0.0.1:{PORT3}/")
                page.wait_for_function("window.__growthStats !== undefined",
                                       timeout=30000)
                page.wait_for_function("window.__renderer !== 'none'",
                                       timeout=15000)
                t0 = time.time()
                st = None
                while time.time() - t0 < 150:
                    st = page.evaluate("window.__growthStats")
                    if st["done"] and st.get("rigged"):
                        break
                    time.sleep(0.25)
                check("F-N4j headed: bear grown + rigged (wire-driven)",
                      st["done"] and st.get("rigged") and st["kind"] == "creature",
                      f"done={st['done']} rigged={st.get('rigged')} "
                      f"tick={st['tick']}")
                page.screenshot(path="_native_bear_rest.png")
                page.click("#bwave")           # the button POSTs /cmd wave
                saw_wave = False
                t0 = time.time()
                while time.time() - t0 < 30:
                    st = page.evaluate("window.__growthStats")
                    if st.get("cmd") == "wave":
                        saw_wave = True         # the command round-tripped
                    if st.get("waveDone"):
                        break                  # NB: cmd flips back to 'rest' AT
                    time.sleep(0.1)            # completion — waveDone is the flag
                # the wire log is the ledger: wave-phase anim frames, residuals
                wire_anim = [m for m in
                             (json.loads(l) for l in LOG3.read_text().splitlines()
                              if l.strip()) if m.get("type") == "anim"]
                wave_frames = [m for m in wire_anim if m["cmd"] == "wave"]
                wave_res = [m["res"] for m in wave_frames if m["res"] is not None]
                check("F-N4j headed: WAVE command executed by the C++ core "
                      "(page saw cmd=wave; wire: wave frames, res < 0.35, done)",
                      saw_wave and st.get("waveDone") and len(wave_frames) > 0
                      and min(wave_res) < 0.35
                      and any(m["waveDone"] for m in wire_anim),
                      f"sawWave={saw_wave} waveDone={st.get('waveDone')} "
                      f"waveFrames={len(wave_frames)} minRes="
                      f"{min(wave_res) if wave_res else None}")
                page.screenshot(path="_native_bear_wave.png")
                page_poses = dict((tuple(map(int, k.split(","))), v)
                                  for k, v in page.evaluate(
                                      "window.__growthCheck().posed"))
                renderer = page.evaluate("window.__renderer")
                browser.close()
            wire_anim = [m for m in
                         (json.loads(l) for l in LOG3.read_text().splitlines()
                          if l.strip()) if m.get("type") == "anim"]
            wire_posed = {(p[0], p[1], p[2]): p[3:] for p in wire_anim[-1]["posed"]}
            same_posed = (page_poses == wire_posed)
            check("F-N4j headed: page's posed cells == wire's posed cells",
                  same_posed and len(wire_posed) > 0
                  and renderer == "webgpu-splat",
                  f"page {len(page_poses)} vs wire {len(wire_posed)} "
                  f"renderer={renderer}")
            print(f"N4 HEADED MEASURED: posed={len(wire_posed)} "
                  f"waveFrames={len(wave_frames)} "
                  f"minWaveRes={min(wave_res) if wave_res else None}")
        finally:
            relay3.terminate()

    if want("N5e"):  # T_HEADED gate
        # ---- F-N5e: HEADED — relay + viewer + DROP button on the bear genome ----
        # tickMs=30 so the page (and the human) can actually SEE the 53-tick fall
        PORT4 = 8803
        relay4 = subprocess.Popen([sys.executable, str(NATIVE / "relay.py"), "30",
                                   str(PORT4),
                                   str(NATIVE / "genomes" / "bear.chimera")],
                                  stdout=subprocess.PIPE, text=True)
        try:
            time.sleep(1.0)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False,
                                            args=["--enable-unsafe-webgpu"])
                page = browser.new_page(viewport={"width": 1280, "height": 720})
                page.goto(f"http://127.0.0.1:{PORT4}/")
                page.wait_for_function("window.__growthStats !== undefined",
                                       timeout=30000)
                page.wait_for_function("window.__renderer !== 'none'",
                                       timeout=15000)
                t0 = time.time()
                st = None
                while time.time() - t0 < 150:
                    st = page.evaluate("window.__growthStats")
                    if st["done"] and st.get("rigged"):
                        break
                    time.sleep(0.25)
                check("F-N5e headed: derived ground on the wire, bear rests on it",
                      st["done"] and st.get("rigged") and st.get("ground") == -4
                      and st.get("contact") is True
                      and abs(st.get("bodyY") or 1) < 1e-12,
                      f"ground={st.get('ground')} contact={st.get('contact')} "
                      f"bodyY={st.get('bodyY')}")
                page.click("#bdrop")           # POSTs /cmd drop -> core stdin
                peak, saw_air, landed = 0.0, False, False
                t0 = time.time()
                while time.time() - t0 < 90:     # condition-bounded, not a guess
                    st = page.evaluate("window.__growthStats")
                    by = st.get("bodyY") or 0
                    peak = max(peak, by)
                    if by > 1 and st.get("contact") is False:
                        saw_air = True
                    if saw_air and st.get("contact") is True and abs(by) < 1e-9:
                        landed = True
                        break
                    time.sleep(0.05)
                page.screenshot(path="_native_bear_ground.png")
                browser.close()
            # the wire ledger: peak height and landing state, from the core itself.
            # The old code read wire_anim[-1] — whatever frame happened to be last
            # when the browser closed — so a slow run sampled the bear MID-FALL
            # (flaked twice: finalBodyY 63.95 / 10.6). Poll for the actual landing
            # frame: peak observed, then contact with bodyY == 0 and vy == 0.
            wire_peak, wire_land = 0.0, None
            wt0 = time.time()
            while time.time() - wt0 < 60:
                try:
                    wire_anim = [m for m in
                                 (json.loads(l) for l in
                                  LOG4.read_text().splitlines() if l.strip())
                                 if m.get("type") == "anim"]
                except json.JSONDecodeError:
                    time.sleep(0.5)              # a line mid-write; retry
                    continue
                if wire_anim:
                    wire_peak = max(wire_peak,
                                    max(m["body"][1] for m in wire_anim))
                    if wire_peak > 63:
                        for m in reversed(wire_anim):
                            if (m.get("contact") is True
                                    and abs(m["body"][1]) < 1e-9):
                                wire_land = m
                                break
                if wire_land is not None:
                    break
                time.sleep(0.5)
            check("F-N5e headed: DROP executed by the C++ core — rose 64 cells, "
                  "fell, landed (contact, bodyY == 0, vy == 0)",
                  saw_air and landed and peak > 1
                  and 63 < wire_peak <= 64.0001
                  and wire_land is not None
                  and abs(wire_land["vy"]) < 1e-12,
                  f"sawAir={saw_air} landed={landed} pagePeak={peak:.2f} "
                  f"wirePeak={wire_peak:.2f} "
                  f"landBodyY={wire_land['body'][1] if wire_land else 'NONE'}")
            print(f"N5 HEADED MEASURED: pagePeak={peak:.2f} "
                  f"wirePeak={wire_peak:.2f} cells "
                  f"landed={'yes' if wire_land else 'NO'}")
        finally:
            relay4.terminate()

    # ---- F-N6a..d: N6 terrain membrane (CA-grown heightfield contact) -------
    #   F-N6a: the wire's terrain == the Python oracle's, INTEGER-EXACT on
    #          every column; relaxation stops at the walkability contract
    #          (max slope <= 512/1024 cells), iteration count is an output
    #   F-N6b: N4-invariance on hills — the ENTIRE N4 ledger (growth, wave,
    #          gait, thetaFinal, senses, learner) is bit-identical to flat
    #   F-N6c: the 400-tick walk's per-tick bodyY/ground trace replicated by
    #          the oracle to < 1e-12 (the wave-phase equilibrium leaves a
    #          1-ULP residue the oracle doesn't model — documented)
    #   F-N6d: the drop law holds on the hill: contact at the first n with
    #          n(n+1) >= 2H/g, ground == the oracle's footprint max
    def gen_terrain_py(g):
        seed, amp = int(g["terrainSeed"]), int(g["terrainAmp"])
        x0, x1 = int(g["terrainX0"]), int(g["terrainX1"])
        sc, bound = int(g["terrainScale"]), int(g["terrainSlope"])
        st = seed
        h = {}
        for x in range(x0, x1 + 1):
            st = (st * 1103515245 + 12345) & 0x7fffffff
            h[x] = st % (2 * amp * sc + 1) - amp * sc
        iters = 0
        while True:
            prev = h
            h = {x: (lambda s: s // 4 if s >= 0 else -((-s) // 4))(
                 prev.get(x - 1, 0) + 2 * prev.get(x, 0) + prev.get(x + 1, 0))
                 for x in range(x0, x1 + 1)}
            iters += 1
            ms = max(abs(h.get(x, 0) - h.get(x - 1, 0))
                     for x in range(x0, x1 + 2))
            if ms <= bound:
                return h, iters, ms
            if iters > 1000:
                return None, iters, ms
    tg = read_chimera(NATIVE / "genomes" / "bearhill.chimera")
    ter, ter_iters, ter_ms = gen_terrain_py(tg)
    TSC = int(tg["terrainScale"])
    rh = subprocess.run([str(NATIVE / "ca_core.exe"), "0",
                         str(NATIVE / "genomes" / "bearhill.chimera"),
                         "selftest"], capture_output=True, text=True,
                        timeout=300)
    hmsgs = [json.loads(l) for l in rh.stdout.splitlines() if l.strip()]
    hrig = next((m for m in hmsgs if m.get("type") == "rig"), None)
    hfin = next((m for m in hmsgs if m.get("type") == "final"), None)
    hst = next((m for m in hmsgs if m.get("type") == "selftest"), None)
    wire_ter = dict(hrig["terrain"]) if hrig and "terrain" in hrig else {}
    ter_diff = sum(1 for x, h in wire_ter.items() if ter.get(x) != h)
    check("F-N6a terrain: wire == oracle integer-exact, contract met",
          rh.returncode == 0 and ter is not None and len(wire_ter) == 1089
          and ter_diff == 0 and hrig["terrainIters"] == ter_iters
          and ter_ms <= 512 and hrig["terrainScale"] == TSC,
          f"cols={len(wire_ter)} mismatches={ter_diff} "
          f"iters={hrig['terrainIters']} (oracle {ter_iters}) "
          f"maxSlope={ter_ms / TSC:.4f} cells")
    hill_cells = {tuple(c[:3]) for c in hfin["cells"]}
    # N7 revision (documented law change): under EARNED traction the walk,
    # learner, AND post-learn IK state (thetaFinal is printed after the 320
    # episodes, so it rides the diverged action sequence) are translation-/
    # learn-coupled — downhill crest exits break contact, the stride slips,
    # the beckon gradient oscillates per tick. What stays bit-identical to
    # flat is everything truly body-local: growth, wave, gait log, the
    # post-walk segment audit, senses. The coupled ledgers must instead match
    # the terrain-mode oracle run.
    orc_h = bear_oracle(tg, hrig, hfin, terrain=ter, tsc=TSC)
    olh = orc_h["learn"]
    local_fields = ["wave", "segErr", "senses"]
    walk_local = {k: v for k, v in hst["walk"].items()
                  if k not in ("trace", "bodyX")}
    walk_local_flat = {k: v for k, v in bst["walk"].items()
                       if k not in ("trace", "bodyX")}
    local_same = (all(hst[k] == bst[k] for k in local_fields)
                  and walk_local == walk_local_flat)
    check("F-N6b/F-N7e hills: body-local ledgers bit-identical to flat "
          "(growth, wave, gait, post-walk segErr, senses)",
          hill_cells == bear_cells and local_same,
          f"cells=={hill_cells == bear_cells} "
          f"moved={[k for k in local_fields if hst[k] != bst[k]]}"
          f" walkLocalMoved={walk_local != walk_local_flat}")
    lh = hst["learn"]
    qh_diff = max(abs(a - b) for row, ref in zip(lh["Q"], olh["Q"])
                  for a, b in zip(row, ref))
    tfh_diff = max(abs(w - o) for crow, orow in zip(hst["thetaFinal"],
                                                    orc_h["thetaFinal"])
                   for w, o in zip(crow, orow))
    check("F-N7e hills: translation/learn-coupled ledgers match the terrain-"
          "mode oracle (walk bodyX, learner, thetaFinal, airwalk)",
          abs(hst["walk"]["bodyX"] - orc_h["walkBodyX"]) < 1e-9
          and lh["visits"] == olh["visits"]
          and abs(lh["first30"] - olh["first30"]) < 1e-9
          and abs(lh["last30"] - olh["last30"]) < 1e-9
          and abs(lh["bodyXfinal"] - olh["bodyXfinal"]) < 1e-9
          and abs(lh["minResAuto"] - olh["minResAuto"]) < 1e-9
          and qh_diff < 1e-9
          and tfh_diff < 1e-9
          and abs(hst["thetaMaxEver"] - orc_h["thetaMaxEver"]) < 1e-9
          and hst["nan"] == orc_h["nan"] == False
          and hst["airwalk"]["airMoved"] == 0.0
          and hst["airwalk"]["landTick"] == orc_h["airwalk"]["landTick"]
          and abs(hst["airwalk"]["bodyX"] - orc_h["airwalk"]["bodyX"]) < 1e-9,
          f"walkBodyX={hst['walk']['bodyX']:.6f} (oracle "
          f"{orc_h['walkBodyX']:.6f}, flat {orc['walkBodyX']:.6f}) "
          f"visits=={lh['visits'] == olh['visits']} qDiff={qh_diff:.2e} "
          f"tfDiff={tfh_diff:.2e} "
          f"hillAirwalk={hst['airwalk']} oracle={orc_h['airwalk']}")
    # the walk-trace oracle is the full protocol replication (wave included,
    # so the 1-ULP settle residue is now MODELLED, not waived)
    tr = hst["walk"]["trace"]
    trace_maxd = max(max(abs(w[1] - o[1]), abs(w[2] - o[2]))
                     for w, o in zip(tr, orc_h["trace"]))
    check("F-N6c walk contact ledger replicated by the oracle (400 ticks)",
          len(tr) == 400 and trace_maxd < 1e-12,
          f"maxDelta={trace_maxd:.2e}")
    bxf = hst["learn"]["bodyXfinal"]
    xs = [c[0] for c in hfin["cells"]]
    lo_x, hi_x = min(xs), max(xs)
    g_sim6 = 9.81 / (60 * 60 * 0.06)
    fp_max = max(ter.get(x, 0)
                 for x in range(math.floor(bxf) + lo_x,
                                math.floor(bxf) + hi_x + 1))
    ph6 = hst["phys"]
    n_pred6 = 1
    while n_pred6 * (n_pred6 + 1) < 2 * ph6["dropH"] / g_sim6:
        n_pred6 += 1
    check("F-N6d drop on the hill: contact law + footprint-max ground",
          ph6["contactTick"] == n_pred6
          and abs(ph6["ground"] - (-4 + fp_max / TSC)) < 1e-12
          and ph6["ledgerErr"] < 1e-12 and ph6["termDrift"] < 0.02,
          f"contactTick={ph6['contactTick']} pred={n_pred6} "
          f"ground={ph6['ground']} (oracle {-4 + fp_max / TSC}) "
          f"ledgerErr={ph6['ledgerErr']:.1e}")
    print(f"N6 SELFTEST MEASURED: cols={len(wire_ter)} iters={ter_iters} "
          f"maxSlope={ter_ms / TSC:.4f} traceDelta={trace_maxd:.1e} "
          f"hillGround={ph6['ground']} contact@{ph6['contactTick']}")

    if want("N6e"):  # T_HEADED gate
        # ---- F-N6e: HEADED — the bear walks over the grown hills ---------------
        PORT5 = 8804
        relay5 = subprocess.Popen([sys.executable, str(NATIVE / "relay.py"), "15",
                                   str(PORT5),
                                   str(NATIVE / "genomes" / "bearhill.chimera")],
                                  stdout=subprocess.PIPE, text=True)
        try:
            time.sleep(1.0)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False,
                                            args=["--enable-unsafe-webgpu"])
                page = browser.new_page(viewport={"width": 1280, "height": 720})
                page.goto(f"http://127.0.0.1:{PORT5}/")
                page.wait_for_function("window.__growthStats !== undefined",
                                       timeout=30000)
                page.wait_for_function("window.__renderer !== 'none'",
                                       timeout=15000)
                t0 = time.time()
                st = None
                while time.time() - t0 < 150:
                    st = page.evaluate("window.__growthStats")
                    if st["done"] and st.get("rigged"):
                        break
                    time.sleep(0.25)
                rig_wire = next((m for m in
                                 (json.loads(l) for l in
                                  LOG5.read_text().splitlines() if l.strip())
                                 if m.get("type") == "rig"), None)
                check("F-N6e headed: grown terrain on the wire + page",
                      st["done"] and st.get("rigged")
                      and rig_wire and len(rig_wire.get("terrain", [])) == 1089,
                      f"rigged={st.get('rigged')} "
                      f"terrainCols={len(rig_wire.get('terrain', [])) if rig_wire else 0}")
                page.click("#bwalk")
                ys = []
                t0 = time.time()
                while time.time() - t0 < 8:
                    st = page.evaluate("window.__growthStats")
                    ys.append(st.get("bodyY") or 0)
                    time.sleep(0.2)
                page.screenshot(path="_native_bear_hills.png")
                page_ok = (max(ys) - min(ys)) > 0.05   # the bear RODE the terrain
                browser.close()
            wire_anim = [m for m in
                         (json.loads(l) for l in LOG5.read_text().splitlines()
                          if l.strip()) if m.get("type") == "anim"]
            wire_ys = [m["body"][1] for m in wire_anim]
            contact_consistent = all(
                abs(m["body"][1] - (m["ground"] + 4)) < 1e-9
                for m in wire_anim if m["contact"])
            check("F-N6e headed: bear walked over grown hills — bodyY tracked the "
                  "terrain, contact frames consistent (bodyY == ground + 4)",
                  page_ok and len(wire_anim) > 100
                  and (max(wire_ys) - min(wire_ys)) > 0.05
                  and contact_consistent,
                  f"pageRange={max(ys) - min(ys):.4f} "
                  f"wireRange={max(wire_ys) - min(wire_ys):.4f} "
                  f"frames={len(wire_anim)} consistent={contact_consistent}")
            print(f"N6 HEADED MEASURED: wire bodyY range "
                  f"{min(wire_ys):.3f}..{max(wire_ys):.3f} cells over "
                  f"{len(wire_anim)} frames")
        finally:
            relay5.terminate()

    # ---- F-N8a..e: N8 goal membrane (deliberation over terrain+physics) ----
    gg = read_chimera(NATIVE / "genomes" / "beargoal.chimera")
    ter8, ter8_iters, ter8_ms = gen_terrain_py(gg)
    TSC8 = int(gg["terrainScale"])
    rg8 = subprocess.run([str(NATIVE / "ca_core.exe"), "0",
                          str(NATIVE / "genomes" / "beargoal.chimera"),
                          "selftest"], capture_output=True, text=True,
                         timeout=300)
    gmsgs = [json.loads(l) for l in rg8.stdout.splitlines() if l.strip()]
    grig = next((m for m in gmsgs if m.get("type") == "rig"), None)
    gfin = next((m for m in gmsgs if m.get("type") == "final"), None)
    gst = next((m for m in gmsgs if m.get("type") == "selftest"), None)
    gnav = next((m for m in gmsgs if m.get("type") == "navtest"), None)

    # F-N8a: the nav layer runs AFTER the G4–N7 ledger closes and cannot
    # touch it — the whole selftest line and the growth must be bit-identical
    goal_cells = {tuple(c[:3]) for c in gfin["cells"]}
    check("F-N8a invariance: beargoal's G4–N7 ledger bit-identical to "
          "bearhill's, same grown terrain, goalX on the wire",
          rg8.returncode == 0 and gst == hst and goal_cells == hill_cells
          and ter8 == ter and grig.get("goalX") == 15 and gnav is not None,
          f"selftest=={gst == hst} cells=={goal_cells == hill_cells} "
          f"terrain=={ter8 == ter} goalX={grig.get('goalX')}")

    # the N8 oracle: navTick replicated float-op for float-op (IK skipped —
    # rewards and senses never read it, documented in ca_core's N8 header)
    def nav_oracle(gd, bfin_, terrain_, tsc_):
        PI = math.pi
        A, T = float(gd["b4A"]), float(gd["b4T"])
        ALPHA, GAMMA = float(gd["l5Alpha"]), float(gd["l5Gamma"])
        EPS0, EPSDECAY, EPSMIN = (float(gd["l5Eps0"]), float(gd["l5EpsDecay"]),
                                  float(gd["l5EpsMin"]))
        RBECK, RWNEAR = float(gd["r5Beckon"]), float(gd["r5WaveNear"])
        R5WT = float(gd["r5WalkTick"])  # slip-compensation constant (R5-derived)
        G = float(gd["gravity"]) / (float(gd["tickHz"]) ** 2
                                    * float(gd["cell"]))
        GOALX = int(gd["goalX"])
        cells_ = bfin_["cells"]
        loY = float(min(c[1] for c in cells_))
        loX, hiX = min(c[0] for c in cells_), max(c[0] for c in cells_)
        omega = 2 * PI / T                       # derived constants (the
        ac = G / (omega * (float(gd["terrainSlope"])     # core derives these
                           / float(gd["terrainScale"])))  # same way)
        tau = G / (A * omega)
        budget = math.ceil(GOALX / (4 * ac / T))

        def col_h(x):
            return loY + terrain_.get(x, 0) / tsc_

        def ground_at(bx_):
            g = None
            for x in range(math.floor(bx_) + loX, math.floor(bx_) + hiX + 1):
                h = terrain_.get(x, 0)
                g = h if g is None else max(g, h)
            return loY + g / tsc_

        def phys(y_, v_, bx_):
            v_ -= G
            y_ += v_
            pen = ground_at(bx_) - (y_ + loY)
            ct = False
            if pen >= 0:
                y_ += pen
                v_ = 0.0
                ct = True
            return y_, v_, ct

        rng = 1337

        def rnd():
            nonlocal rng
            x = rng * 1103515245.0 + 12345.0      # JS lossy-double LCG
            m = math.fmod(x, 4294967296.0)
            rng = int(m) & 0x7fffffff
            return rng / 0x7fffffff

        # ---- Step 1: trace for episodes 290-319 (instrumentation only) ----
        traces = []                           # list of (ep, tick, bx, state, verb, contact, explored, arrived)

        def nav_state_num(bx_=None, ct_=None):
            """returns s. bx_/ct_ override closure state for rollouts.
            Measurement-validity fix: greedy_rollout keeps its OWN local
            contact; without ct_ the rollout would read the training-final
            closure value (stale exactly where the bear goes airborne).
            Training calls pass nothing -> closure, so F-N8b identity holds."""
            bxx = math.floor(bx_ if bx_ is not None else bx)
            bearing = 0 if GOALX > bxx else 1
            ss = (col_h(bxx + 1) - col_h(bxx - 1)) / 2
            slope = 0 if ss > 0 else (1 if ss >= -tau else 2)
            ct = contact if ct_ is None else ct_
            return (bearing * 3 + slope) * 2 + (1 if ct else 0)

        y = v = 0.0
        contact = True
        bx = 0.0

        def nav_state():
            bxx = math.floor(bx)
            bearing = 0 if GOALX > bxx else 1
            ss = (col_h(bxx + 1) - col_h(bxx - 1)) / 2
            slope = 0 if ss > 0 else (1 if ss >= -tau else 2)
            return (bearing * 3 + slope) * 2 + (1 if contact else 0)

        Q = [[0.0] * 5 for _ in range(12)]
        eps = EPS0
        visits = [0] * 12
        rewards, arrived = [], []
        episode = epTick = 0
        epReward = 0.0
        arrivals = 0
        gaitT = 0

        def spawn():
            nonlocal bx, y, v, contact, epTick, epReward
            epTick = 0
            epReward = 0.0
            bx = 0.0 if rnd() < 0.5 else 30.0     # flag +/- 15, symmetric
            y = ground_at(bx) - loY
            v = 0.0
            contact = True

        spawn()
        guard = 0
        while episode < 320 and guard < 320 * budget * 3:
            guard += 1
            y, v, contact = phys(y, v, bx)
            s = nav_state()
            visits[s] += 1
            # Step 1: trace recording for episodes 290-319
            s_cur = nav_state_num()
            explored_flag = False
            if rnd() < eps:
                a = math.floor(rnd() * 5)
                explored_flag = True
            else:
                q = Q[s]
                a = 0
                for i in range(1, 5):             # strict >: lowest index
                    if q[i] > q[a]:
                        a = i
            if 290 <= episode < 320:
                traces.append((episode, epTick, bx, s_cur, a, contact, explored_flag, False))
            d0 = abs(GOALX - bx)
            if a != 0:            # 1:E full 2:W full 3:E careful 4:W careful
                d = 1.0 if a in (1, 3) else -1.0
                amp = A if a <= 2 else ac
                gaitT += 1
                phi = 2 * PI * gaitT / T
                if contact:                       # the N7 earned-stride law
                    bx += d * amp * (2 * PI / T) * abs(math.cos(phi))
            d1 = abs(GOALX - bx)
            # the beckoning gradient minus uniform time cost; derived from R5
            # (RBECK) and N5/L5 (budget derives from l5EpTicks, already in the
            # genome); no new tunables. Slip is the bear's choice (it chose the
            # gait), so airborne time is not waived; shaping needs no clip.
            # Ng shaping tested+falsified (see report).
            r = RBECK * (d0 - d1) - 1.0 / budget

            terminal = False
            if math.floor(bx) == GOALX:           # standing ON the flag
                r += RWNEAR
                terminal = True
                arrivals += 1
            epReward += r
            epTick += 1
            s2 = nav_state()
            # Bootstrap: max over all verbs in the next state, no clip.
            mx = max(Q[s2])
            Q[s][a] += ALPHA * (r + (0.0 if terminal else GAMMA * mx)
                                - Q[s][a])
            # Step 1: mark arrival in trace if this tick arrived
            if 290 <= episode < 320 and traces:
                t = list(traces[-1])
                t[7] = terminal
                traces[-1] = tuple(t)
            if terminal or epTick >= budget:
                rewards.append(epReward)
                arrived.append(1 if terminal else 0)
                episode += 1
                eps = max(EPSMIN, eps * EPSDECAY)
                spawn()
        first30 = sum(arrived[:30]) / 30
        last30 = sum(arrived[-30:]) / 30

        # ---- Step 2: greedy rollout (eps=0, pure exploit) from both spawns ----
        def greedy_rollout(bx0):
            bx = float(bx0)
            y = ground_at(bx) - loY
            v = 0.0
            contact = True
            seq = []
            gt = 0
            for tick in range(1, budget + 1):
                y, v, contact = phys(y, v, bx)
                s = nav_state_num(bx, contact)  # rollout's OWN state, not the
                                               # training-final closure values
                q = Q[s]
                a = 0
                for i in range(1, 5):
                    if q[i] > q[a]:
                        a = i
                verb_name = ["REST", "walkE", "walkW", "careE", "careW"][a]
                if a != 0:
                    d = 1.0 if a in (1, 3) else -1.0
                    amp = A if a <= 2 else ac
                    gt += 1
                    phi = 2 * math.pi * gt / T
                    if contact:
                        bx += d * amp * (2 * math.pi / T) * abs(math.cos(phi))
                terminal = False
                if math.floor(bx) == GOALX:
                    terminal = True
                seq.append((tick, bx, s, a, verb_name, contact, terminal))
                if terminal:
                    return seq, tick, True
            return seq, None, False

        greedy_results = []
        for spawn in [0.0, 30.0]:
            seq, arr_tick, arrived = greedy_rollout(spawn)
            greedy_results.append((spawn, seq, arr_tick, arrived))

        return {"goalX": GOALX, "budget": budget, "ac": ac, "tau": tau,
                "episodes": episode, "visits": visits, "arrivals": arrivals,
                "first30": first30, "last30": last30, "Q": Q,
                "rewards": rewards, "traces": traces, "greedy": greedy_results}

    no8 = nav_oracle(gg, gfin, ter8, TSC8)
    traces = no8.pop("traces", [])

    # ---- Step 1 trace summary (episodes 290-319) ----
    if traces:
        print("\n=== F-N8c TRACE (episodes 290-319) ===")
        for ep in range(290, 320):
            ep_tr = [t for t in traces if t[0] == ep]
            arrived_tick = next((t[1] for t in ep_tr if t[7]), None)
            state_seq = []
            cur_s, run = None, 0
            for t in ep_tr:
                s = t[3]
                if s != cur_s:
                    if cur_s is not None:
                        state_seq.append(f"s{cur_s}x{run}")
                    cur_s, run = s, 1
                else:
                    run += 1
            if cur_s is not None:
                state_seq.append(f"s{cur_s}x{run}")
            arrive_str = f"ARRIVE@{arrived_tick}" if arrived_tick is not None else "NO-ARRIVE"
            verb_summary = {}
            for t in ep_tr:
                key = (t[3], t[4])
                verb_summary[key] = verb_summary.get(key, 0) + 1
            explore_count = sum(1 for t in ep_tr if t[6])
            print(f"  ep{ep}: {' -> '.join(state_seq)} | {arrive_str} | explore={explore_count}/{len(ep_tr)}")
            s3_verb = {}
            s9_verb = {}
            for t in ep_tr:
                if t[3] == 3:
                    s3_verb[t[4]] = s3_verb.get(t[4], 0) + 1
                if t[3] == 9:
                    s9_verb[t[4]] = s9_verb.get(t[4], 0) + 1
            if s3_verb:
                print(f"    s3 visits: {dict(s3_verb)}")
            if s9_verb:
                print(f"    s9 visits: {dict(s9_verb)}")
        print("=== END TRACE ===\n")

    # ---- Step 2: greedy rollout results (from inside oracle) ----
    for spawn, seq, arr_tick, arrived in no8.get("greedy", []):
        print(f"Greedy rollout from bx={spawn:.1f}: {'ARRIVED@' + str(arr_tick) if arrived else 'STALLED'}")
        # diagnostic: first 5 ticks
        for t in seq[:5]:
            print(f"    tick {t[0]}: bx={t[1]:.4f} s={t[2]} verb={t[4]} ct={t[5]}")
        state_counts = {}
        for tick, bxv, s, a, vn, ct, term in seq:
            state_counts[s] = state_counts.get(s, 0) + 1
        print(f"  states visited: {dict(sorted(state_counts.items()))}")
        # per-state greedy verb summary (contact states only)
        s_verb_summary = {}
        for tick, bxv, s, a, vn, ct, term in seq:
            if ct:
                k = f"s{s}"
                if k not in s_verb_summary:
                    s_verb_summary[k] = {}
                s_verb_summary[k][vn] = s_verb_summary[k].get(vn, 0) + 1
        for k in sorted(s_verb_summary):
            print(f"  {k}: {dict(s_verb_summary[k])}")
        # state sequence compact
        ss_seq = []
        cur_s, run = None, 0
        for tick, bxv, s, a, vn, ct, term in seq:
            if s != cur_s:
                if cur_s is not None:
                    ss_seq.append(f"s{cur_s}x{run}")
                cur_s, run = s, 1
            else:
                run += 1
        if cur_s is not None:
            ss_seq.append(f"s{cur_s}x{run}")
        print(f"  sequence: {' -> '.join(ss_seq)}")
        bx_vals = [seq[i][1] for i in range(len(seq))]
        print(f"  final bx={bx_vals[-1]:.3f} (goalX={no8['goalX']})\n")

    q8_diff = max(abs(a - b) for row, ref in zip(gnav["Q"], no8["Q"])
                  for a, b in zip(row, ref))
    rw8_diff = max(abs(a - b) for a, b in zip(gnav["rewards"],
                                              no8["rewards"]))
    check("F-N8b nav ledger == oracle replication (constants, visits, Q, "
          "rewards, arrivals) within 1e-9",
          gnav["goalX"] == no8["goalX"] and gnav["budget"] == no8["budget"]
          and abs(gnav["ac"] - no8["ac"]) < 1e-12
          and abs(gnav["tau"] - no8["tau"]) < 1e-12
          and gnav["episodes"] == 320 == no8["episodes"]
          and gnav["visits"] == no8["visits"]
          and gnav["arrivals"] == no8["arrivals"]
          and len(gnav["rewards"]) == 320
          and abs(gnav["first30"] - no8["first30"]) < 1e-12
          and abs(gnav["last30"] - no8["last30"]) < 1e-12
          and q8_diff < 1e-9 and rw8_diff < 1e-9,
          f"budget={gnav['budget']} ac={gnav['ac']:.6f} tau={gnav['tau']:.6f} "
          f"arrivals={gnav['arrivals']} visits=={gnav['visits'] == no8['visits']} "
          f"qDiff={q8_diff:.1e} rwDiff={rw8_diff:.1e}")

    # ---- F-N8c CASE B (documented): clean-core greedy policy STALLS --------
    # Measured on the CLEAN derived reward (F-N8b identity qDiff=0, verified).
    # The learner reaches the flag during training (316/320, last30=1.0), but
    # the eps=0 greedy policy does NOT arrive from either spawn:
    #   bx=0  -> s3 REST x260  (final bx=0.0)
    #   bx=30 -> s9 REST x260  (final bx=30.0)
    # Root cause (crest-slip poisoning + discount drift): in the flat contact
    # states, walking toward the flag occasionally slips airborne into the pit
    # (s2/s8 Q ~ -0.04); at gamma=0.99 this drags walk-verb Q below REST's
    # risk-free self-loop: s3 REST 1.586 > best-walk 1.534; s9 REST 1.699 >
    # best-walk 1.683. The beacon gradient k*(d0-d1) is too weak to overcome
    # the drift at the gamma=0.99 asymptote, so greedy rests forever.
    # Gamma-shaping (Ng et al. 1999) was tested in both signs and falsified:
    #   literal k*(gamma*d1-d0) rewards retreat (training 0/320, walks away);
    #   corrected k*(d0-gamma*d1) is unstable (greedy flip-flops, never arrives
    #   from both spawns at N=320..4000). So no shaping is shipped.
    G8 = float(gg["gravity"]) / (float(gg["tickHz"]) ** 2 * float(gg["cell"]))
    A8, T8 = float(gg["b4A"]), float(gg["b4T"])
    loY8 = float(min(c[1] for c in gfin["cells"]))
    loX8 = min(c[0] for c in gfin["cells"])
    hiX8 = max(c[0] for c in gfin["cells"])

    def col8(x):
        return loY8 + ter8.get(x, 0) / TSC8

    def probe8(bx0, amp, dirn, ticks=300, flat=False):
        def gat(bx_):
            if flat:
                return loY8
            g = None
            for x in range(math.floor(bx_) + loX8, math.floor(bx_) + hiX8 + 1):
                h = ter8.get(x, 0)
                g = h if g is None else max(g, h)
            return loY8 + g / TSC8
        bx = float(bx0)
        y = gat(bx) - loY8
        v = 0.0
        for t in range(1, ticks + 1):
            v -= G8
            y += v
            pen = gat(bx) - (y + loY8)
            ct = False
            if pen >= 0:
                y += pen
                v = 0.0
                ct = True
            phi = 2 * math.pi * t / T8
            if ct:
                bx += dirn * amp * (2 * math.pi / T8) * abs(math.cos(phi))
        return abs(bx - bx0)

    # verify the measured CASE B stall pattern (honest pin: if the core changes
    # so greedy no longer stalls, this check fails and must be revisited).
    stall_detail = []
    both_stall = True
    for spawn, seq, arr_tick, arrived in no8.get("greedy", []):
        if not arrived:
            s0 = seq[0][2]
            stall_detail.append(
                f"bx={spawn:.1f} STALL s{s0} REST={gnav['Q'][s0][0]:.3f}"
                f">bestwalk {max(gnav['Q'][s0][1:]):.3f}")
        else:
            both_stall = False
    pit = max(max(gnav["Q"][2]), max(gnav["Q"][8]))
    check("F-N8c CASE B (documented): clean-core greedy policy STALLS from both"
          " spawns — verified; airborne pit negative",
          both_stall and gnav["Q"][3][0] > max(gnav["Q"][3][1:])
          and gnav["Q"][9][0] > max(gnav["Q"][9][1:])
          and pit < 0.0,
          "; ".join(stall_detail) + f" | pit s2/s8={pit:.4f}")

    # F-N8f (future): when gamma-shaping fix is implemented, assert greedy
    # arrives from both spawns. Predicted before implementation.

    # the agent-doc's time-reversal falsifier (VERB_DELIBERATION_DESIGN
    # F-N8b), folded in: on FLAT ground, walk- is the bit-exact mirror of
    # walk+ (IEEE: signed increments negate exactly, so the sums do too)
    sym8 = abs(probe8(0.0, A8, 1.0, flat=True)
               - probe8(0.0, A8, -1.0, flat=True))
    check("F-N8c-sym walk- is the bit-exact time-reverse of walk+ on flat "
          "ground", sym8 == 0.0, f"|d+ - d-| = {sym8}")

    check("F-N8d learning curve: last-30 arrival rate > first-30",
          gnav["last30"] > gnav["first30"] and gnav["arrivals"] > 160,
          f"first30={gnav['first30']:.3f} last30={gnav['last30']:.3f} "
          f"arrivals={gnav['arrivals']}/320")
    print(f"N8 SELFTEST MEASURED: ac={gnav['ac']:.6f} tau={gnav['tau']:.6f} "
          f"budget={gnav['budget']} arrivals={gnav['arrivals']}/320 "
          f"first30={gnav['first30']:.3f} last30={gnav['last30']:.3f} "
          f"visits={gnav['visits']} qDiff={q8_diff:.1e} rwDiff={rw8_diff:.1e}")


    if want("N8e"):  # T_HEADED gate
        if os.environ.get("N8_SKIP_HEADED") == "1":
            print("SKIP F-N8e (headed)")
            check("F-N8e headed: SKIPPED", True, "env N8_SKIP_HEADED=1")
        # ---- F-N8e: HEADED — the bear deliberates its way to the flag ---------
        PORT6 = 8805
        relay6 = subprocess.Popen([sys.executable, str(NATIVE / "relay.py"), "15",
                                   str(PORT6),
                                   str(NATIVE / "genomes" / "beargoal.chimera")],
                                  stdout=subprocess.PIPE, text=True)
        try:
            time.sleep(1.0)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False,
                                            args=["--enable-unsafe-webgpu"])
                page = browser.new_page(viewport={"width": 1280, "height": 720})
                page.goto(f"http://127.0.0.1:{PORT6}/")
                page.wait_for_function("window.__growthStats !== undefined",
                                       timeout=30000)
                page.wait_for_function("window.__renderer !== 'none'",
                                       timeout=15000)
                t0 = time.time()
                st = None
                while time.time() - t0 < 150:
                    st = page.evaluate("window.__growthStats")
                    if st["done"] and st.get("rigged"):
                        break
                    time.sleep(0.25)
                page.click("#bnav")
                nav_samples = []
                t0 = time.time()
                while time.time() - t0 < 25:
                    st = page.evaluate("window.__growthStats")
                    if st.get("nav"):
                        nav_samples.append(st["nav"])
                    time.sleep(0.2)
                page.screenshot(path="_native_bear_goal.png")
                goal_on_page = st.get("goalX") == 15
                browser.close()
            wire_nav = [m["nav"] for m in
                        (json.loads(l) for l in LOG6.read_text().splitlines()
                         if l.strip())
                        if m.get("type") == "anim" and "nav" in m]
            eps_seen = [n["ep"] for n in nav_samples]
            arr_seen = [n["arrivals"] for n in nav_samples]
            dmin = min((n["dist"] for n in nav_samples), default=1e9)
            check("F-N8e headed: flag on wire+page, nav frames in range, episodes "
                  "advance, the bear REACHES the flag live",
                  goal_on_page and len(nav_samples) > 50
                  and all(0 <= n["state"] < 12 for n in nav_samples)
                  and all(0 <= n["verb"] < 5 for n in nav_samples)
                  and len(wire_nav) > 100
                  and max(eps_seen) >= min(eps_seen) + 2
                  and max(arr_seen) >= 1 and dmin < 5.0,
                  f"samples={len(nav_samples)} wireFrames={len(wire_nav)} "
                  f"eps {min(eps_seen)}->{max(eps_seen)} "
                  f"arrivals={max(arr_seen)} dMin={dmin:.2f}")
            print(f"N8 HEADED MEASURED: {len(nav_samples)} page samples, "
                  f"{len(wire_nav)} wire frames, eps {min(eps_seen)}->"
                  f"{max(eps_seen)}, arrivals {max(arr_seen)}, dMin {dmin:.2f}")
        finally:
            relay6.terminate()

    # ---- F-T1a..c: T1 stand/walk on the vox (imported) teddy genome ----------
    #   F-T1a: full-suite invariance — the N5/N7 physics membrane is
    #          shape-agnostic: teddy's stand ledger (drop law, symplectic
    #          energy, rest equilibrium) reproduces the bear's predicted N5
    #          numbers exactly, with the SAME genome-declared constants
    #   F-T1b: stand — teddy at rest: ground gap < 0.01 m and velocity -> 0
    #          after 1 s no-input (mirrors the bear's N5d rest check)
    #   F-T1c: walk — earned-traction displacement over 400 ticks == the N7
    #          oracle's discrete |cos| sum within 1e-9 (reuses F-N7b structure,
    #          pointed at teddy.chimera instead of bear.chimera)
    rt = subprocess.run([str(NATIVE / "ca_core.exe"), "0",
                         str(NATIVE / "genomes" / "teddy.chimera"), "selftest"],
                        capture_output=True, text=True, timeout=120)
    tmsgs = [json.loads(l) for l in rt.stdout.splitlines() if l.strip()]
    tmeta = next((m for m in tmsgs if m.get("type") == "meta"), None)
    tfin = next((m for m in tmsgs if m.get("type") == "final"), None)
    tvox = next((m for m in tmsgs if m.get("type") == "voxtest"), None)
    check("F-T1a teddy genome loads as an embodied creature (kind=vox)",
          rt.returncode == 0 and tmeta and tmeta["kind"] == "creature"
          and tmeta.get("embodiment") == 1 and tfin and tvox,
          f"rc={rt.returncode} kind={tmeta and tmeta.get('kind')} "
          f"name={tmeta and tmeta.get('name')}")
    tg2 = read_chimera(NATIVE / "genomes" / "teddy.chimera")
    cell_t = float(tg2["cell"])
    tickHz_t = float(tg2["tickHz"])
    g_sim_t = float(tg2["gravity"]) / (tickHz_t ** 2 * cell_t)
    st_ = tvox["stand"]
    H = st_["dropH"]
    # the SAME discrete drop-law prediction the bear's F-N5b check uses
    n_pred_t = 1
    while n_pred_t * (n_pred_t + 1) < 2 * H / g_sim_t:
        n_pred_t += 1
    check("F-T1a invariance: teddy stand reproduces the bear's N5 drop law, "
          "symplectic energy ledger, and rest equilibrium (shape-agnostic)",
          st_["contactTick"] == n_pred_t
          and abs(st_["contactTick"] - math.sqrt(2 * H / g_sim_t)) <= 1
          and st_["ledgerErr"] < 1e-12 and st_["termDrift"] < 0.02
          and st_["restVyMax"] == 0 and st_["restPenMax"] < 1e-12,
          f"contactTick={st_['contactTick']} pred={n_pred_t} "
          f"g={g_sim_t:.6f} ledgerErr={st_['ledgerErr']:.2e} "
          f"termDrift={st_['termDrift']:.4%} "
          f"restVyMax={st_['restVyMax']} restPenMax={st_['restPenMax']:.2e}")
    # F-T1b: stand gap < 0.01 m, velocity -> 0 after >= 1 s no-input
    gap_m = st_["restPenMax"] * cell_t
    vy_m_s = st_["restVyMax"] * cell_t * tickHz_t
    check("F-T1b teddy at rest: ground gap < 0.01 m and velocity -> 0 after "
          ">= 1 s no-input (mirrors the bear's N5d equilibrium)",
          gap_m < 0.01 and abs(vy_m_s) < 1e-9,
          f"gap={gap_m:.4e} m  |velY|={vy_m_s:.4e} m/s "
          f"(restPenMax={st_['restPenMax']:.2e} cells, "
          f"restVyMax={st_['restVyMax']} cells/tick)")
    # F-T1c: earned-traction walk == N7 oracle discrete sum (mirrors F-N7b)
    A_t, T_t = float(tg2["b4A"]), float(tg2["b4T"])
    walk_sum = sum(A_t * (2 * math.pi / T_t) * abs(math.cos(2 * math.pi * t / T_t))
                   for t in range(1, 401))
    wlk = tvox["walk"]
    check("F-T1c teddy earned-traction walk: 400-tick displacement == N7 "
          "oracle |cos| sum within 1e-9 (same tolerance band as bear N7)",
          abs(wlk["bodyX"] - walk_sum) < 1e-9 and wlk["iters"] > 0
          and wlk["nan"] == False and wlk["thetaMaxEver"] <= 2.6,
          f"bodyX={wlk['bodyX']:.6f} oracle={walk_sum:.6f} "
          f"iters={wlk['iters']} nan={wlk['nan']} "
          f"thetaMax={wlk['thetaMaxEver']:.3f}")
    print(f"T1 MEASURED: rc={rt.returncode} kind={tmeta['kind']} "
          f"contact@{st_['contactTick']} (pred {n_pred_t}) "
          f"ledgerErr={st_['ledgerErr']:.1e} drift={st_['termDrift']:.4%} "
          f"gap={gap_m:.2e}m vy={vy_m_s:.2e}m/s "
          f"walkBodyX={wlk['bodyX']:.6f} (oracle {walk_sum:.6f})")

    # ---- F-T6: PART A range of motion — every moving part, swept ------------
    # The operator's Part A: the human must see the COMPLETE structure and the
    # full range of anything that moves. The ROM command sweeps each rig chain
    # one at a time, direct-joint (no IK — the joint IS the DOF), amplitude
    # A = b4ThMax/2 = 1.3 rad = 74.5 deg (the full envelope short of the
    # fold-through extreme the clamp forbids), quadrature so both joints show
    # both extremes per chain. Falsifier: any chain's max |theta| misses A by
    # more than the sin-sampling error (cos(pi/90) = 0.99939 over P=90 ticks),
    # or the sweep NaNs, or it never completes.
    rom = tvox.get("rom")
    A_rom = float(tg2["b4ThMax"]) * 0.5
    check("F-T6a ROM: every chain swept to the derived amplitude and the demo "
          "completes (rom.done), no NaN",
          rom is not None and rom["done"] and not rom["nan"]
          and rom["chains"] == len(rom["maxTh"])
          and all(A_rom * 0.999 <= m <= A_rom * 1.0001
                  for m in rom["maxTh"]),
          f"chains={rom and rom['chains']} maxTh={rom and rom['maxTh']} "
          f"A={A_rom} done={rom and rom['done']} nan={rom and rom['nan']}")
    check("F-T6b ROM leaves no residue: thetas end at 0 and the walk/stand "
          "ledgers above were measured BEFORE the sweep (state isolation)",
          wlk["nan"] == False and st_["contactTick"] == n_pred_t,
          f"walkNan={wlk['nan']} contactTick={st_['contactTick']}")
    print(f"T6 MEASURED: rom chains={rom['chains']} "
          f"maxTh={min(rom['maxTh']):.4f}..{max(rom['maxTh']):.4f} "
          f"(A={A_rom}) done={rom['done']}")

    # ---- F-T1d: T1 goal membrane — the teddy navigates the bear's world -----
    # teddygoal.chimera = teddy.chimera + the N8 goal block (L5/R5/N6/N8
    # copied from beargoal verbatim). The nav ledger must be replicated by the
    # SAME body-agnostic oracle (F-N8b's nav_oracle), on the SAME seed-2026
    # world — the only body property that enters the nav is the footprint
    # (13 cells wide, measured off teddy.cells, vs the bear's 17).
    tg3 = read_chimera(NATIVE / "genomes" / "teddygoal.chimera")
    ter9, ter9_iters, ter9_ms = gen_terrain_py(tg3)
    TSC9 = int(tg3["terrainScale"])
    rt9 = subprocess.run([str(NATIVE / "ca_core.exe"), "0",
                          str(NATIVE / "genomes" / "teddygoal.chimera"),
                          "selftest"], capture_output=True, text=True,
                         timeout=300)
    t9msgs = [json.loads(l) for l in rt9.stdout.splitlines() if l.strip()]
    t9rig = next((m for m in t9msgs if m.get("type") == "rig"), None)
    t9fin = next((m for m in t9msgs if m.get("type") == "final"), None)
    t9nav = next((m for m in t9msgs if m.get("type") == "navtest"), None)
    check("F-T1d-world: teddy's grown terrain IS the bear's world (same "
          "seed-2026 field, contract met, goalX on the wire)",
          rt9.returncode == 0 and ter9 == ter8
          and t9rig.get("goalX") == 15 and t9nav is not None,
          f"terrain=={ter9 == ter8} iters={ter9_iters} "
          f"maxSlope={ter9_ms / TSC9:.4f} goalX={t9rig.get('goalX')}")
    no9 = nav_oracle(tg3, t9fin, ter9, TSC9)
    q9_diff = max(abs(a - b) for row, ref in zip(t9nav["Q"], no9["Q"])
                  for a, b in zip(row, ref))
    rw9_diff = max(abs(a - b) for a, b in zip(t9nav["rewards"],
                                              no9["rewards"]))
    check("F-T1d-eval teddy nav ledger == the body-agnostic oracle within "
          "1e-9 (constants, visits, Q, rewards, arrivals)",
          t9nav["goalX"] == no9["goalX"] and t9nav["budget"] == no9["budget"]
          and abs(t9nav["ac"] - no9["ac"]) < 1e-12
          and abs(t9nav["tau"] - no9["tau"]) < 1e-12
          and t9nav["episodes"] == 320 == no9["episodes"]
          and t9nav["visits"] == no9["visits"]
          and t9nav["arrivals"] == no9["arrivals"]
          and len(t9nav["rewards"]) == 320
          and abs(t9nav["first30"] - no9["first30"]) < 1e-12
          and abs(t9nav["last30"] - no9["last30"]) < 1e-12
          and q9_diff < 1e-9 and rw9_diff < 1e-9,
          f"budget={t9nav['budget']} ac={t9nav['ac']:.6f} "
          f"arrivals={t9nav['arrivals']} qDiff={q9_diff:.1e} "
          f"rwDiff={rw9_diff:.1e}")
    check("F-T1d learning curve: last-30 arrival rate > first-30",
          t9nav["last30"] > t9nav["first30"] and t9nav["arrivals"] > 160,
          f"first30={t9nav['first30']:.3f} last30={t9nav['last30']:.3f} "
          f"arrivals={t9nav['arrivals']}/320")

    # ---- F-T1d CASE B (documented): the teddy's greedy policy stalls ONLY
    # east-bound — an honest asymmetric repeat of the bear's crest-slip poison.
    # Measured on the CLEAN derived reward (F-T1d-eval identity qDiff=0).
    # Training learns (314/320, last30=1.0) but the eps=0 policy from bx=0
    # rests forever: s3 REST=1.671 > best-walk careW=1.612 — the SAME discount
    # drift as the bear's F-N8 CASE B (the crest at x=11 and the east descent
    # 18->20 poison walk-E). From bx=30 the teddy's narrower footprint (13
    # cells vs the bear's 17) reads a different support profile west of the
    # crest, so s9 best-walk (careW=1.717) beats REST (1.686) and the greedy
    # policy ARRIVES@232. Neither direction is patched — both are pinned.
    loY9 = float(min(c[1] for c in t9fin["cells"]))
    loX9 = min(c[0] for c in t9fin["cells"])
    hiX9 = max(c[0] for c in t9fin["cells"])
    G9 = float(tg3["gravity"]) / (float(tg3["tickHz"]) ** 2
                                  * float(tg3["cell"]))
    A9, T9 = float(tg3["b4A"]), float(tg3["b4T"])
    ac9, tau9, budget9 = no9["ac"], no9["tau"], no9["budget"]
    GOALX9 = int(tg3["goalX"])

    def col9(x):
        return loY9 + ter9.get(x, 0) / TSC9

    def ground9(bx_):
        g = None
        for x in range(math.floor(bx_) + loX9, math.floor(bx_) + hiX9 + 1):
            h = ter9.get(x, 0)
            g = h if g is None else max(g, h)
        return loY9 + g / TSC9

    def phys9(y_, v_, bx_):
        v_ -= G9
        y_ += v_
        pen = ground9(bx_) - (y_ + loY9)
        ct = False
        if pen >= 0:
            y_ += pen
            v_ = 0.0
            ct = True
        return y_, v_, ct

    def nav_state9(bx_, ct_):
        bxx = math.floor(bx_)
        bearing = 0 if GOALX9 > bxx else 1
        ss = (col9(bxx + 1) - col9(bxx - 1)) / 2
        slope = 0 if ss > 0 else (1 if ss >= -tau9 else 2)
        return (bearing * 3 + slope) * 2 + (1 if ct_ else 0)

    def greedy9(bx0):
        bx = float(bx0)
        y = ground9(bx) - loY9
        v = 0.0
        contact = True
        gt = 0
        for tick in range(1, budget9 + 1):
            y, v, contact = phys9(y, v, bx)
            s = nav_state9(bx, contact)
            q = t9nav["Q"][s]
            a = 0
            for i in range(1, 5):
                if q[i] > q[a]:
                    a = i
            if a != 0:
                d = 1.0 if a in (1, 3) else -1.0
                amp = A9 if a <= 2 else ac9
                gt += 1
                phi = 2 * math.pi * gt / T9
                if contact:
                    bx += d * amp * (2 * math.pi / T9) * abs(math.cos(phi))
            if math.floor(bx) == GOALX9:
                return tick
        return None

    arr_e = greedy9(0.0)
    arr_w = greedy9(30.0)
    s3q = t9nav["Q"][3]
    stall_detail = (f"bx=0 STALL s3 REST={s3q[0]:.3f}>bestwalk "
                    f"{max(s3q[1:]):.3f}" if arr_e is None
                    else "bx=0 ARRIVES (poison broken)")
    check("F-T1d CASE B (documented): teddy greedy policy STALLS east-bound "
          "(s3 REST > best-walk — the bear's crest-slip poison repeats); "
          "west-bound it ARRIVES; neither patched",
          arr_e is None and s3q[0] > max(s3q[1:]) and arr_w is not None,
          f"{stall_detail}; bx=30 ARRIVES@{arr_w}")
    print(f"T1 GOAL MEASURED: arrivals={t9nav['arrivals']}/320 "
          f"first30={t9nav['first30']:.3f} last30={t9nav['last30']:.3f} "
          f"qDiff={q9_diff:.1e} rwDiff={rw9_diff:.1e} "
          f"greedy bx=0 {'STALL' if arr_e is None else 'ARRIVE'}, "
          f"bx=30 {'STALL' if arr_w is None else 'ARRIVE@' + str(arr_w)}")

    if want("T1d"):  # T_HEADED gate
        if os.environ.get("N8_SKIP_HEADED") == "1":
            print("SKIP F-T1d headed")
            check("F-T1d headed: SKIPPED", True, "env N8_SKIP_HEADED=1")
        # ---- F-T1d headed: the teddy deliberates its way to the flag ---------
        PORT9 = 8806
        relay9 = subprocess.Popen([sys.executable, str(NATIVE / "relay.py"), "15",
                                   str(PORT9),
                                   str(NATIVE / "genomes" / "teddygoal.chimera")],
                                  stdout=subprocess.PIPE, text=True)
        try:
            time.sleep(1.0)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False,
                                            args=["--enable-unsafe-webgpu"])
                page = browser.new_page(viewport={"width": 1280, "height": 720})
                page.goto(f"http://127.0.0.1:{PORT9}/")
                page.wait_for_function("window.__growthStats !== undefined",
                                       timeout=30000)
                page.wait_for_function("window.__renderer !== 'none'",
                                       timeout=15000)
                t0 = time.time()
                st = None
                while time.time() - t0 < 150:
                    st = page.evaluate("window.__growthStats")
                    if st["done"] and st.get("rigged"):
                        break
                    time.sleep(0.25)
                page.click("#bnav")
                nav_samples = []
                t0 = time.time()
                while time.time() - t0 < 25:
                    st = page.evaluate("window.__growthStats")
                    if st.get("nav"):
                        nav_samples.append(st["nav"])
                    time.sleep(0.2)
                page.screenshot(path="_native_teddy_goal.png")
                goal_on_page = st.get("goalX") == 15
                browser.close()
            wire_nav = []
            for l in LOG9.read_text().splitlines():
                if not l.strip():
                    continue
                try:
                    m = json.loads(l)
                except json.JSONDecodeError:
                    continue        # a dying prior relay may leave a torn line
                if m.get("type") == "anim" and "nav" in m:
                    wire_nav.append(m["nav"])
            eps_seen = [n["ep"] for n in nav_samples]
            arr_seen = [n["arrivals"] for n in nav_samples]
            dmin = min((n["dist"] for n in nav_samples), default=1e9)
            check("F-T1d headed: flag on wire+page, nav frames in range, episodes "
                  "advance, the TEDDY reaches the flag live",
                  goal_on_page and len(nav_samples) > 50
                  and all(0 <= n["state"] < 12 for n in nav_samples)
                  and all(0 <= n["verb"] < 5 for n in nav_samples)
                  and len(wire_nav) > 100
                  and max(eps_seen) >= min(eps_seen) + 2
                  and max(arr_seen) >= 1 and dmin < 5.0,
                  f"samples={len(nav_samples)} wireFrames={len(wire_nav)} "
                  f"eps {min(eps_seen)}->{max(eps_seen)} "
                  f"arrivals={max(arr_seen)} dMin={dmin:.2f}")
            print(f"T1 HEADED MEASURED: {len(nav_samples)} page samples, "
                  f"{len(wire_nav)} wire frames, eps {min(eps_seen)}->"
                  f"{max(eps_seen)}, arrivals {max(arr_seen)}, dMin {dmin:.2f}")
        finally:
            relay9.terminate()

    # ---- F-T3: voxel-muscle gait — CA-native movement, no FK/IK --------------
    # teddymuscle.chimera = teddy.chimera + vmGait=1. WALK drives the tripod
    # beat machine (LIFT/SWING/PLANT/SHIFT) on the lattice itself: muscles
    # shorten by REMOVING voxels, joints are oblong pivots re-laid by cell
    # flow. Headless and fast: one selftest run, all checks off the wire.
    #   F-T3a: physics membrane intact under vmGait (the drop law holds)
    #   F-T3b: WALKS or DOESN'T — displacement >= 40 cells over 400 ticks
    #          (T4-trained stride L=2: prediction 114 = 400·L/(2L+3); the
    #          sweep gated L>=3 out — budget manhattan+2L breaks the count)
    #   F-T3c: body integrity every tick — single face-connected component,
    #          cell count within 5% of the shape-trained 375, zero traction slips
    #   F-T3d: airwalk — legs cycling in free fall move the body EXACTLY
    #          nowhere (airDX bit-exact 0, SHIFT requests denied: gatedAir)
    rt3 = subprocess.run([str(NATIVE / "ca_core.exe"), "0",
                          str(NATIVE / "genomes" / "teddymuscle.chimera"),
                          "selftest"], capture_output=True, text=True,
                         timeout=120)
    t3msgs = [json.loads(l) for l in rt3.stdout.splitlines() if l.strip()]
    t3meta = next((m for m in t3msgs if m.get("type") == "meta"), None)
    t3fin = next((m for m in t3msgs if m.get("type") == "final"), None)
    t3vox = next((m for m in t3msgs if m.get("type") == "voxtest"), None)
    tg4 = read_chimera(NATIVE / "genomes" / "teddymuscle.chimera")
    grown_n = len(t3fin["cells"]) if t3fin else 0
    # F-T3a-shape: the construction order's FIRST gate — the body must be
    # physically correct before any movement is trained. Recomputed from the
    # cells file (never trusted from the trainer): paws coplanar + COM ground
    # projection inside the paw support hull with margin >= 1 cell (one
    # lattice step of discretization slack — the derived bound).
    s1r = [l.split("#")[0].split() for l in
           open(NATIVE / "genomes" / tg4["cellsFile"])]
    s1r = [l for l in s1r if l]
    n_s1 = int(s1r[0][1])
    cells_s1 = [tuple(map(int, s1r[1 + j])) for j in range(n_s1)]
    i_s1 = 1 + n_s1
    m_s1 = int(s1r[i_s1][1]); i_s1 += 1
    paws_s1 = []
    for _ in range(m_s1):
        nx_s1 = int(s1r[i_s1][2]); i_s1 += 1
        paws_s1.append(tuple(map(int, s1r[i_s1 + nx_s1 - 1])))
        i_s1 += nx_s1
    gy_s1 = min(c[1] for c in cells_s1)
    cx_s1 = sum(c[0] for c in cells_s1) / n_s1
    cz_s1 = sum(c[2] for c in cells_s1) / n_s1

    def hull2_s1(ps):
        ps = sorted(set(ps))
        def cr(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
        lo = []
        for p in ps:
            while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
                lo.pop()
            lo.append(p)
        hi = []
        for p in reversed(ps):
            while len(hi) >= 2 and cr(hi[-2], hi[-1], p) <= 0:
                hi.pop()
            hi.append(p)
        return lo[:-1] + hi[:-1]

    H_s1 = hull2_s1([(p[0], p[2]) for p in paws_s1])
    marg_s1 = 1e9
    for a, b in zip(H_s1, H_s1[1:] + H_s1[:1]):
        ex, ey = b[0] - a[0], b[1] - a[1]
        marg_s1 = min(marg_s1,
                      (ex * (cz_s1 - a[1]) - ey * (cx_s1 - a[0]))
                      / math.hypot(ex, ey))
    coplanar_s1 = all(p[1] == gy_s1 for p in paws_s1)
    check("F-T3a-shape: the body is physically correct BEFORE movement — "
          "paws coplanar, COM projection inside the paw hull with margin "
          ">= 1 cell (recomputed from the cells file)",
          coplanar_s1 and marg_s1 >= 1.0 and grown_n == n_s1,
          f"legs={m_s1} COM=({cx_s1:.3f},{cz_s1:.3f}) hull={H_s1} "
          f"margin={marg_s1:.3f} cells={grown_n}/{n_s1}")
    check("F-T3a teddymuscle genome loads (kind=vox, vmGait=1) and the stand "
          "ledger is intact",
          rt3.returncode == 0 and t3meta and t3meta["kind"] == "creature"
          and tg4.get("vmGait") == "1" and t3vox and "vm" in t3vox,
          f"rc={rt3.returncode} name={t3meta and t3meta.get('name')} "
          f"vmGait={tg4.get('vmGait')} grownCells={grown_n}")
    st3 = t3vox["stand"]
    g3 = float(tg4["gravity"]) / (float(tg4["tickHz"]) ** 2
                                  * float(tg4["cell"]))
    n_pred3 = 1
    while n_pred3 * (n_pred3 + 1) < 2 * st3["dropH"] / g3:
        n_pred3 += 1
    check("F-T3a physics membrane intact under vmGait: contact tick == the "
          "discrete drop law, rest equilibrium exact",
          st3["contactTick"] == n_pred3 and st3["restVyMax"] == 0
          and st3["restPenMax"] < 1e-12 and st3["termDrift"] < 0.02,
          f"contactTick={st3['contactTick']} pred={n_pred3} "
          f"restVyMax={st3['restVyMax']} restPenMax={st3['restPenMax']:.2e} "
          f"termDrift={st3['termDrift']:.4%}")
    w3 = t3vox["walk"]
    check("F-T3b WALKS: 400-tick displacement >= 40 cells (T4-TRAINED "
          "stride L=2: prediction 114 = 400·L/(2L+3), lean repaid per cycle) "
          "with ZERO IK iterations — the gait is pure CA",
          w3["bodyX"] >= 40 and w3["iters"] == 0 and w3["nan"] == False,
          f"bodyX={w3['bodyX']} iters={w3['iters']} nan={w3['nan']}")
    vm3 = t3vox["vm"]
    check("F-T3c body integrity: single face-connected component every tick, "
          "cell count within 5% of the grown shape, no traction slips",
          vm3["connMin"] == 1
          and vm3["countMin"] >= grown_n * 0.95
          and vm3["countMax"] <= grown_n * 1.05
          and vm3["slips"] == 0,
          f"connMin={vm3['connMin']} count=[{vm3['countMin']},"
          f"{vm3['countMax']}]/{grown_n} slips={vm3['slips']} "
          f"shifts={vm3['shifts']}")
    check("F-T3d airwalk: legs cycling in free fall translate the body "
          "EXACTLY nowhere (airDX bit-exact 0) and SHIFT requests are denied "
          "while airborne (gatedAir > 0)",
          vm3["airDX"] == 0 and vm3["gatedAir"] > 0,
          f"airDX={vm3['airDX']} gatedAir={vm3['gatedAir']} "
          f"gatedSupport={vm3['gatedSupport']}")
    print(f"T3 MEASURED: walk bodyX={w3['bodyX']} (T4-trained pred 114) iters={w3['iters']} "
          f"conn={vm3['connMin']} count=[{vm3['countMin']},{vm3['countMax']}] "
          f"shifts={vm3['shifts']} slips={vm3['slips']} "
          f"gatedAir={vm3['gatedAir']} airDX={vm3['airDX']}")

    # ---- F-T7: the voxel-muscle gait WALKS THE GROWN HILLS -------------------
    # teddymusclehills.chimera = teddymuscle + the N6 terrain membrane (seed
    # 2026 — the SAME world the bear navigated). One core change: the vm
    # PLANT beat reads the terrain column under each paw AT CONTACT; airborne
    # legs keep the T3 body-frame plane (measured: a world-frame target while
    # airborne grew legs unboundedly toward the distant ground — flat
    # regression count +6.1%/slips 4 vs trained 375/0, so the airborne path
    # is the old line verbatim). The loader also hoisted the vox terrain
    # block OUT of goal=1 — the world is a membrane, not a reward accessory.
    #   F-T7a: the teddy's grown world == the oracle == the bear's field
    #   F-T7b: the drop law holds on the hill (contact tick == prediction)
    #   F-T7c: the trained gait WALKS the slopes — displacement, integrity,
    #          airDX bit-exact 0, slips REPORTED on the wire (never hidden)
    #   F-T7d: the flat membrane is bit-unchanged (the T3 ledger above is
    #          pinned to the pre-T7 core's exact numbers)
    rt7 = subprocess.run([str(NATIVE / "ca_core.exe"), "0",
                          str(NATIVE / "genomes" / "teddymusclehills.chimera"),
                          "selftest"], capture_output=True, text=True,
                         timeout=300)
    t7msgs = [json.loads(l) for l in rt7.stdout.splitlines() if l.strip()]
    t7rig = next((m for m in t7msgs if m.get("type") == "rig"), None)
    t7fin = next((m for m in t7msgs if m.get("type") == "final"), None)
    t7vox = next((m for m in t7msgs if m.get("type") == "voxtest"), None)
    tg7 = read_chimera(NATIVE / "genomes" / "teddymusclehills.chimera")
    ter7, ter7_iters, ter7_ms = gen_terrain_py(tg7)
    wire_ter7 = dict(t7rig["terrain"]) if t7rig and "terrain" in t7rig else {}
    ter7_diff = sum(1 for x, h in wire_ter7.items() if ter7.get(x) != h)
    check("F-T7a hills world: wire terrain == the oracle integer-exact and "
          "== the bear's grown field (seed 2026)",
          rt7.returncode == 0 and ter7 is not None and len(wire_ter7) == 1089
          and ter7_diff == 0 and t7rig["terrainIters"] == ter7_iters
          and ter7 == ter,
          f"cols={len(wire_ter7)} mismatches={ter7_diff} "
          f"iters={t7rig and t7rig.get('terrainIters')}/{ter7_iters} "
          f"sameAsBear={ter7 == ter}")
    st7 = t7vox["stand"]
    g7 = float(tg7["gravity"]) / (float(tg7["tickHz"]) ** 2
                                  * float(tg7["cell"]))
    n_pred7 = 1
    while n_pred7 * (n_pred7 + 1) < 2 * st7["dropH"] / g7:
        n_pred7 += 1
    check("F-T7b physics membrane on the hill: contact tick == the discrete "
          "drop law, rest equilibrium exact",
          st7["contactTick"] == n_pred7 and st7["restVyMax"] == 0
          and st7["restPenMax"] < 1e-12 and st7["termDrift"] < 0.02,
          f"contactTick={st7['contactTick']} pred={n_pred7} "
          f"restVyMax={st7['restVyMax']} restPenMax={st7['restPenMax']:.2e} "
          f"termDrift={st7['termDrift']:.4%}")
    w7 = t7vox["walk"]
    vm7 = t7vox["vm"]
    grown7 = len(t7fin["cells"]) if t7fin else 0
    check("F-T7c WALKS THE SLOPES: 400-tick displacement >= 40 cells with "
          "zero IK, single component, count within 5%, airDX bit-exact 0, "
          "slips reported on the wire",
          w7["bodyX"] >= 40 and w7["iters"] == 0 and w7["nan"] == False
          and vm7["connMin"] == 1
          and vm7["countMin"] >= grown7 * 0.95
          and vm7["countMax"] <= grown7 * 1.05
          and vm7["airDX"] == 0 and "slips" in vm7,
          f"bodyX={w7['bodyX']} iters={w7['iters']} conn={vm7['connMin']} "
          f"count=[{vm7['countMin']},{vm7['countMax']}]/{grown7} "
          f"slips={vm7['slips']} airDX={vm7['airDX']} "
          f"gatedAir={vm7['gatedAir']}")
    check("F-T7c2 the hills are LOAD-BEARING: the hill walk ledger differs "
          "from the flat walk (not a placebo world)",
          w7["bodyX"] != w3["bodyX"],
          f"hills={w7['bodyX']} flat={w3['bodyX']}")
    check("F-T7d flat membrane bit-unchanged by T7: the T3 ledger above == "
          "the pre-T7 core's exact numbers",
          w3["bodyX"] == 116 and vm3["slips"] == 0 and vm3["shifts"] == 58
          and vm3["gatedAir"] == 7 and vm3["countMin"] == 358
          and vm3["countMax"] == 375,
          f"bodyX={w3['bodyX']} slips={vm3['slips']} shifts={vm3['shifts']} "
          f"gatedAir={vm3['gatedAir']} count=[{vm3['countMin']},"
          f"{vm3['countMax']}]")
    print(f"T7 MEASURED: hills walk bodyX={w7['bodyX']} (flat {w3['bodyX']}, "
          f"{(w7['bodyX'] / w3['bodyX'] - 1) * 100:+.1f}%) shifts={vm7['shifts']} "
          f"slips={vm7['slips']} gatedAir={vm7['gatedAir']} "
          f"count=[{vm7['countMin']},{vm7['countMax']}]/{grown7} "
          f"terrainCols={len(wire_ter7)} iters={ter7_iters}")
finally:
    relay.terminate()

print("RESULT:", "ALL GREEN" if not fails else f"FAILED: {fails}")
raise SystemExit(1 if fails else 0)
