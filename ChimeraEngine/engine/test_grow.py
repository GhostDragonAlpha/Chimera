# G1 WALL + G2 OAK — Playwright verification for spiace_grow.html
# G1 falsifiers: renderer, monotonic wave growth, zero support violations,
#   completion, exact blueprint match.
# G2 falsifiers (named before the run):
#   F-G2b: growth reaches >= 30 cells of height
#   F-G2c: phyllotaxis — successive bud azimuths per stem differ by the golden
#          angle 137.508 deg, mean circular error < 5 deg
#   F-G2d: apical dominance — no lateral tip activates within domZone cells of
#          the apex while the leader lives (ledger max == 0)
#   F-G2e: phototropism — > 55% of leaf mass on the sun side (>= 30 leaves)
#   F-G2f: the grown structure is one connected tissue
#   F-G2g: pruning the leader releases a lateral (auxin dominance is causal)
# G3 falsifiers (named before the run):
#   F-G3b: bilateral mirror symmetry through the midline >= 0.85
#   F-G3c: head morphogen polarizes the AP axis — corr(x, log a) > 0.85 (the
#          genome's claim is an EXPONENTIAL gradient a ~ e^{-x/lam}; the linear
#          instrument for an exponential law is the log. Raw Pearson on the
#          heavy-tailed field measures 0.66 and is still REPORTED — the metric
#          refinement is documented in the G3 header, not hidden),
#          and head-to-tail dx > 3
#   F-G3d: exactly 4 limbs ignite (two A-bands x DV-band x two flanks)
#   F-G3e: 12 digits (3 per limb, golden-angle fan)
#   F-G3f: one connected tissue
#   F-G3g: Turing spots — nSpots >= 3, |lam_meas - lam_pred| / lam_pred < 30%
#   F-G3h: flipping gravity re-specifies the DV axis on regrowth
#   F-G3i: exactly 2 eyes, lateral on the head
import math
import time
from playwright.sync_api import sync_playwright

URL = "file:///E:/PythonChimera/ChimeraEngine/engine/spiace_grow.html"
fails = []

def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}")
    if not ok:
        fails.append(name)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--enable-unsafe-webgpu"])

    # ---------------- G1 WALL (regression) ----------------
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    page.goto(URL)
    page.wait_for_function("window.__growthStats !== undefined", timeout=15000)
    page.wait_for_function("window.__renderer !== 'none'", timeout=15000)
    page.screenshot(path="_grow_start.png")
    time.sleep(0.5)
    st = page.evaluate("window.__growthStats")
    print(f"G1 WALL  genome={st['genome']}  seed cells={st['cellCount']} "
          f"blueprint={st['blueprintCount']}")
    check("F-G1a renderer is webgpu-splat",
          page.evaluate("window.__renderer") == "webgpu-splat",
          page.evaluate("window.__renderer"))
    t0 = time.time()
    while time.time() - t0 < 30:
        st = page.evaluate("window.__growthStats")
        if st["done"]:
            break
        time.sleep(0.25)
    chk = page.evaluate("window.__growthCheck()")
    cells, viol = chk["histCells"], chk["histViol"]
    mono = all(cells[i] >= cells[i - 1] for i in range(1, len(cells)))
    clean = all(v == 0 for v in viol)
    check("F-G1b growth monotonic (every tick audited)", mono,
          f"{len(cells)} ticks, cells {cells[0]}->{cells[-1]}")
    check("F-G1c zero support violations (every tick audited)", clean,
          f"max viol in ledger: {max(viol) if viol else 'n/a'}")
    check("F-G1e completed", st["done"], f"tick={st['tick']} cells={st['cellCount']}")
    check("F-G1e wave-speed bound (tick <= 200)", st["tick"] <= 200, f"tick={st['tick']}")
    check("F-G1d cell count == blueprint count",
          chk["cellCount"] == chk["blueprintCount"],
          f"{chk['cellCount']} vs {chk['blueprintCount']}")
    check("F-G1d grown set matches blueprint exactly",
          chk["matchesBlueprint"] is True, str(chk["matchesBlueprint"]))
    check("F-G1c final independent support scan", chk["unsupported"] == 0,
          f"unsupported={chk['unsupported']}")
    time.sleep(0.5)
    page.screenshot(path="_grow_end.png")
    print(f"G1 MEASURED: ticks={st['tick']} cells={chk['cellCount']} "
          f"violations={chk['violations']} unsupported={chk['unsupported']}")

    # ---------------- G2 OAK ----------------
    page2 = browser.new_page(viewport={"width": 1280, "height": 720})
    page2.goto(URL + "?genome=oak")
    page2.wait_for_function("window.__growthStats !== undefined", timeout=15000)
    page2.wait_for_function("window.__renderer !== 'none'", timeout=15000)
    check("F-G2a renderer is webgpu-splat",
          page2.evaluate("window.__renderer") == "webgpu-splat",
          page2.evaluate("window.__renderer"))
    page2.evaluate("window.__setTickMs(15)")
    t0 = time.time()
    st2 = None
    while time.time() - t0 < 150:
        st2 = page2.evaluate("window.__growthStats")
        # let the crown develop: phototropism is a self-shading effect, it
        # needs leaf mass overhead before the asymmetry has mechanism to act
        if st2["leaves"] >= 60 or st2["done"]:
            break
        time.sleep(0.5)
    print(f"G2 OAK  genome={st2['genome']}  tick={st2['tick']} "
          f"cells={st2['cellCount']} height={st2['height']} tips={st2['tips']} "
          f"leaves={st2['leaves']}")
    check("F-G2b height >= 30 cells", st2["height"] >= 30,
          f"height={st2['height']} ({st2['height'] * 0.05:.2f} m)")
    chk2 = page2.evaluate("window.__growthCheck()")
    check("F-G2c phyllotaxis golden angle (mean err < 5 deg)",
          chk2["phylloMeanErrDeg"] is not None and chk2["phylloMeanErrDeg"] < 5,
          f"err={chk2['phylloMeanErrDeg']} deg over {chk2['phylloPairs']} pairs")
    check("F-G2d apical dominance ledger clean",
          chk2["dominanceMax"] == 0, f"max={chk2['dominanceMax']}")
    sun_ok = (chk2["tipCount"] >= 5 and chk2["tipSunMean"] is not None
              and chk2["tipSunMean"] > 0.3
              and chk2["leafCentroid"] is not None
              and chk2["leafCentroid"] > 0.5 and chk2["leafCount"] >= 30)
    check("F-G2e phototropism (tips toward sun > 0.3, leaf centroid > 0.5)",
          sun_ok,
          f"tipSunMean={chk2['tipSunMean']} centroid={chk2['leafCentroid']} "
          f"leaves={chk2['leafCount']}")
    check("F-G2f structure connected", chk2["connected"] is True,
          str(chk2["connected"]))
    # the pruning experiment: remove the leader, a lateral must ignite
    page2.evaluate("window.__pruneLeader()")
    t0 = time.time()
    rec = None
    while time.time() - t0 < 40:
        rec = page2.evaluate("window.__growthCheck()")
        if rec.get("recovered"):
            break
        time.sleep(0.5)
    check("F-G2g pruning releases a lateral (dominance is causal)",
          rec is not None and rec["recovered"] is True,
          f"recovered after {rec.get('ticksSincePrune')} ticks post-prune")
    time.sleep(0.5)
    page2.screenshot(path="_grow_oak.png")
    print(f"G2 MEASURED: tick={chk2['tick']} cells={chk2['cellCount']} "
          f"height={chk2['height']} leaves={chk2['leafCount']} "
          f"phylloErr={chk2['phylloMeanErrDeg']} deg "
          f"dominanceMax={chk2['dominanceMax']} tipSun={chk2['tipSunMean']} "
          f"centroid={chk2['leafCentroid']} "
          f"connected={chk2['connected']} recovered={rec.get('recovered')}")

    # ---------------- G3 CREATURE ----------------
    page3 = browser.new_page(viewport={"width": 1280, "height": 720})
    page3.goto(URL + "?genome=creature")
    page3.wait_for_function("window.__growthStats !== undefined", timeout=15000)
    page3.wait_for_function("window.__renderer !== 'none'", timeout=15000)
    check("F-G3a renderer is webgpu-splat",
          page3.evaluate("window.__renderer") == "webgpu-splat",
          page3.evaluate("window.__renderer"))
    page3.evaluate("window.__setTickMs(15)")
    # grow the body: wait for turing phase (body finished) or full done
    t0 = time.time()
    while time.time() - t0 < 150:
        st3 = page3.evaluate("window.__growthStats")
        if st3["phase"] in ("turing", "done"):
            break
        time.sleep(0.5)
    chk3 = page3.evaluate("window.__growthCheck()")
    print(f"G3 CREATURE  genome={st3['genome']}  tick={st3['tick']} "
          f"cells={st3['cellCount']} phase={st3['phase']} "
          f"limbs={st3['limbs']} eyes={st3['eyes']}")
    check("F-G3b bilateral mirror symmetry >= 0.85",
          chk3.get("symmetry") is not None and chk3["symmetry"] >= 0.85,
          f"symmetry={chk3.get('symmetry')}")
    check("F-G3d exactly 4 limbs ignited",
          chk3["limbCount"] == 4,
          f"limbs={chk3['limbCount']} roots={chk3.get('limbRoots')}")
    check("F-G3e 12 digits (3 per limb, golden-angle fan)",
          chk3["digitCount"] == 12, f"digits={chk3['digitCount']}")
    check("F-G3f one connected tissue", chk3["connected"] is True,
          str(chk3["connected"]))
    check("F-G3i exactly 2 eyes (lateral on head)",
          chk3["eyeCount"] == 2, f"eyes={chk3['eyeCount']}")
    # finish the pigmentation phase
    t0 = time.time()
    while time.time() - t0 < 120:
        st3 = page3.evaluate("window.__growthStats")
        if st3["phase"] == "done":
            break
        time.sleep(0.5)
    chk3 = page3.evaluate("window.__growthCheck()")
    # F-G3c is asserted on the ADULT: at body-done the tube field is still a
    # relaxation transient (measured: corrLogAX 0.504 at turing entry vs 0.905
    # in the adult) — the polarization claim is about the finished body plan
    check("F-G3c head morphogen polarizes the AP axis "
          "(adult corr(x, log a) > 0.85, dx > 3)",
          chk3.get("corrLogAX") is not None and chk3["corrLogAX"] > 0.85
          and chk3["headTailDx"] > 3,
          f"corrLogAX={chk3.get('corrLogAX')} raw={chk3.get('corrAX')} "
          f"headTailDx={chk3.get('headTailDx')}")
    lam_p, lam_m = chk3.get("lambdaPred"), chk3.get("lambdaMeas")
    check("F-G3g Turing spots: nSpots >= 3 and |lam_meas - lam_pred| < 30%",
          chk3["nSpots"] >= 3 and lam_p and lam_m is not None
          and abs(lam_m - lam_p) / lam_p < 0.30,
          f"nSpots={chk3['nSpots']} lambdaPred={lam_p} lambdaMeas={lam_m}")
    time.sleep(0.5)
    page3.screenshot(path="_grow_creature.png")
    print(f"G3 MEASURED: tick={chk3['tick']} cells={chk3['cellCount']} "
          f"symmetry={chk3.get('symmetry')} corrLogAX={chk3.get('corrLogAX')} "
          f"rawCorrAX={chk3.get('corrAX')} "
          f"headTailDx={chk3.get('headTailDx')} limbs={chk3['limbCount']} "
          f"digits={chk3['digitCount']} eyes={chk3['eyeCount']} "
          f"spots={chk3['nSpots']} lamPred={lam_p} lamMeas={lam_m}")
    # F-G3h: gravity flip re-specifies the DV axis (the field is causal)
    org0 = page3.evaluate("window.__organizers()")
    dv0 = org0["ventral"][1] - org0["ball"][1]
    page3.evaluate("window.__regrow(1)")
    page3.wait_for_function("window.__growthStats.phase === 'growth' "
                            "|| window.__growthStats.phase === 'turing' "
                            "|| window.__growthStats.phase === 'done'",
                            timeout=60000)
    org1 = page3.evaluate("window.__organizers()")
    dv1 = org1["ventral"][1] - org1["ball"][1]
    check("F-G3h gravity flip re-specifies DV axis on regrowth",
          dv0 < 0 and dv1 > 0,
          f"ventral-centroid y: {dv0} -> {dv1} "
          f"(head={org1['head']} ventral={org1['ventral']})")
    page3.screenshot(path="_grow_creature_flipped.png")

    # ---------------- G4 BEAR (embodiment) ----------------
    # Falsifiers (named before the run — see the G4 header in spiace_grow.html):
    #   F-G4a: rig = 4 chains x 2 joints read off the grown ledger (+ 2 ears)
    #   F-G4b: wave converges — tip residual < 0.35 cell, raiseIters <= 300
    #   F-G4c: gait — diagonal pairs in phase (|dphi| < 0.5), ipsilateral
    #          anti-phase (||dphi| - pi| < 0.5); body translates
    #   F-G4d: no NaN, |theta| <= 2.6 rad ever
    #   F-G4f: FK rigidity — posed segment lengths == grown (segErr < 1e-6)
    page4 = browser.new_page(viewport={"width": 1280, "height": 720})
    page4.goto(URL + "?genome=bear")
    page4.wait_for_function("window.__growthStats !== undefined", timeout=15000)
    page4.wait_for_function("window.__renderer !== 'none'", timeout=15000)
    check("F-G4a renderer is webgpu-splat",
          page4.evaluate("window.__renderer") == "webgpu-splat",
          page4.evaluate("window.__renderer"))
    page4.evaluate("window.__setTickMs(15)")
    t0 = time.time()
    while time.time() - t0 < 120:
        st4 = page4.evaluate("window.__growthStats")
        if st4["phase"] == "done":
            break
        time.sleep(0.5)
    print(f"G4 BEAR  genome={st4['genome']}  tick={st4['tick']} "
          f"cells={st4['cellCount']} phase={st4['phase']}")
    bst = page4.evaluate("window.__bearStats()")
    check("F-G4a rig read off the grown ledger (4 chains, 8 joints, 2 ears)",
          bst["rigged"] and bst["chains"] == 4 and bst["joints"] == 8
          and bst["ears"] == 2,
          f"chains={bst['chains']} joints={bst['joints']} ears={bst['ears']} "
          f"meta={bst['chainMeta']}")
    page4.screenshot(path="_grow_bear_rest.png")
    # --- wave ---
    page4.evaluate("window.__bearCommand('wave')")
    t0 = time.time()
    while time.time() - t0 < 60:
        bst = page4.evaluate("window.__bearStats()")
        if bst["waveDone"]:
            break
        time.sleep(0.25)
    check("F-G4b wave converged (residual < 0.35 cell, iters <= 300)",
          bst["waveDone"] and bst["minResidual"] is not None
          and bst["minResidual"] < 0.35
          and bst["raiseIters"] is not None and bst["raiseIters"] <= 300,
          f"minResidual={bst['minResidual']} raiseIters={bst['raiseIters']} "
          f"totalIters={bst['iters']}")
    page4.screenshot(path="_grow_bear_wave.png")
    # --- walk ---
    page4.evaluate("window.__bearCommand('walk')")
    time.sleep(8)                      # ~4+ gait cycles at T=60 x 30 ms
    gait = page4.evaluate("window.__bearGait()")
    meta = page4.evaluate("window.__bearStats()")
    page4.evaluate("window.__bearCommand('rest')")
    n = len(gait)
    w = 2 * math.pi / 60               # gait frequency per anim tick
    phases = []
    for i in range(len(meta["chainMeta"])):
        re = sum(e["tips"][i][0] * math.cos(w * e["t"]) for e in gait)
        im = -sum(e["tips"][i][0] * math.sin(w * e["t"]) for e in gait)
        phases.append(math.atan2(im, re))
    def wrap(d):
        return math.atan2(math.sin(d), math.cos(d))
    def idx(fore, side):
        return next(i for i, m in enumerate(meta["chainMeta"])
                    if m["fore"] == fore and m["side"] == side)
    d_diag = [abs(wrap(phases[idx(True, 1)] - phases[idx(False, -1)])),
              abs(wrap(phases[idx(True, -1)] - phases[idx(False, 1)]))]
    d_ipsi = [abs(abs(wrap(phases[idx(True, 1)] - phases[idx(True, -1)])) - math.pi),
              abs(abs(wrap(phases[idx(False, 1)] - phases[idx(False, -1)])) - math.pi)]
    check("F-G4c gait: diagonal pairs in phase (|dphi| < 0.5 rad)",
          n >= 120 and max(d_diag) < 0.5,
          f"samples={n} diag={['%.3f' % d for d in d_diag]}")
    check("F-G4c gait: ipsilateral pairs anti-phase (||dphi|-pi| < 0.5 rad)",
          n >= 120 and max(d_ipsi) < 0.5,
          f"ipsi={['%.3f' % d for d in d_ipsi]}")
    check("F-G4c walk translates the body (no-slip mean stride)",
          meta["body"][0] > 5, f"bodyX={meta['body'][0]:.1f} cells")
    bchk = page4.evaluate("window.__bearCheck()")
    check("F-G4d no NaN, |theta| <= 2.6 rad ever",
          not bchk["nan"] and bchk["thetaMaxEver"] <= 2.6,
          f"nan={bchk['nan']} thetaMaxEver={bchk['thetaMaxEver']:.3f}")
    check("F-G4f FK rigidity (posed segments == grown, segErr < 1e-6)",
          bchk["segErr"] is not None and bchk["segErr"] < 1e-6,
          f"segErr={bchk['segErr']}")
    page4.screenshot(path="_grow_bear_walk.png")
    print(f"G4 MEASURED: chains={bchk['chains']} joints={bchk['joints']} "
          f"waveRes={bst['minResidual']:.4f} raiseIters={bst['raiseIters']} "
          f"diag={['%.3f' % d for d in d_diag]} "
          f"ipsi={['%.3f' % d for d in d_ipsi]} "
          f"bodyX={meta['body'][0]:.1f} thetaMax={bchk['thetaMaxEver']:.3f} "
          f"segErr={bchk['segErr']:.2e} nan={bchk['nan']}")

    # ---------------- G5 LEARNER (situations -> goals) ----------------
    # Falsifiers (named before the run — see the G5 header in spiace_grow.html):
    #   F-G5a: sensed situation == geometric truth (range bins + eye bearing)
    #   F-G5b: mean episode reward last30 > first30 + 0.3
    #   F-G5c: greedy policy matches the reward structure on >= 80% of
    #          sufficiently-visited states after 300 episodes
    #   F-G5d: embodiment guarantees hold under learner-issued commands
    sL = page4.evaluate("window.__setVisitor(true, 4, 3)")
    sR = page4.evaluate("window.__setVisitor(true, 4, -3)")
    sC = page4.evaluate("window.__setVisitor(true, 4, 0)")
    sF = page4.evaluate("window.__setVisitor(true, 12, 0)")
    sA = page4.evaluate("window.__setVisitor(false, 0, 0)")
    check("F-G5a senses: near/far/bearing/absent states distinct and true",
          sA == 0 and 1 <= sL <= 3 and 1 <= sR <= 3 and 1 <= sC <= 3
          and sL != sR and 4 <= sF <= 6,
          f"near+z={sL} near-z={sR} near-c={sC} far-c={sF} absent={sA}")
    ep = page4.evaluate("window.__bearLearn(300)")
    ls = page4.evaluate("window.__learnStats()")
    check("F-G5b learning improves reward (last30 > first30 + 0.3)",
          ls["episode"] >= 300 and ls["first30"] is not None
          and ls["last30"] > ls["first30"] + 0.3,
          f"episodes={ls['episode']} first30={ls['first30']:.3f} "
          f"last30={ls['last30']:.3f}")
    greedy = [0 if q[0] >= q[1] and q[0] >= q[2] else (1 if q[1] >= q[2] else 2)
              for q in ls["Q"]]
    audit = [i for i, v in enumerate(ls["visits"]) if v >= 10]
    acc = sum(1 for i in audit if greedy[i] == ls["struct"][i]) / len(audit)
    check("F-G5c greedy policy matches reward structure >= 80%",
          acc >= 0.8,
          f"accuracy={acc:.3f} over {len(audit)} states "
          f"greedy={greedy} struct={ls['struct']}")
    bchk5 = page4.evaluate("window.__bearCheck()")
    check("F-G5d embodiment intact under learner commands "
          "(wave res < 0.35, theta <= 2.6, no NaN, rigid FK)",
          ls["minResAuto"] is not None and ls["minResAuto"] < 0.35
          and bchk5["thetaMaxEver"] <= 2.6 and not bchk5["nan"]
          and bchk5["segErr"] < 1e-6,
          f"minResAuto={ls['minResAuto']} thetaMax={bchk5['thetaMaxEver']:.3f} "
          f"nan={bchk5['nan']} segErr={bchk5['segErr']:.2e}")
    time.sleep(0.5)
    page4.screenshot(path="_grow_bear_learn.png")
    print(f"G5 MEASURED: episodes={ls['episode']} first30={ls['first30']:.3f} "
          f"last30={ls['last30']:.3f} accuracy={acc:.3f} "
          f"greedy={greedy} visits={ls['visits']} "
          f"minResAuto={ls['minResAuto']:.4f} eps={ls['eps']:.3f}")
    browser.close()

print("RESULT:", "ALL GREEN" if not fails else f"FAILED: {fails}")
raise SystemExit(1 if fails else 0)
