"""Round-10 STEP 3+4: SHARED stack (:8110/:8210, rebuilt engine) playable.

Lesson 6 feel_the_muscle end-to-end with REAL UI interaction (mouse drag on
#effort-u, click on #effort-sever-btn), screenshots before/contracted/severed,
selection by 'q' AND by the lesson list (prev/next buttons), disarm-on-switch
via bend_the_knee's own slider+post, 12-lesson keyboard card scan (real
keyboard.press), and end-to-end passes of wake_the_cell + bend_the_knee.
All state reads ride the page's own path (fetch /api/state on :8210).
Never kills anything; shared stack stays up.
Evidence: 10_before_contract.png / 10_contracted.png / 10_severed_passed.png,
10_regression.txt.
"""
import time, tempfile, json, math, re, urllib.request
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"
EV = r"E:\PythonChimera\tools\game_shell\evidence\round-10"
CAM = dict(r=26, theta=-0.55, phi=0.42, target=[0.0, 4.5, 0.0], fov=45.0)
BELLY = (0.0, 4.5, 0.35)
log_lines = []
RESULT = {}
CARDS = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    log_lines.append(s)


def proxy_get(path):
    with urllib.request.urlopen(URL + path, timeout=10) as r:
        return json.loads(r.read())


def proxy_post(path, obj):
    req = urllib.request.Request(URL + path, data=json.dumps(obj).encode(),
                                 method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def tstate():
    st = proxy_get("/api/state")
    return {k: st.get(k) for k in ("tendon_armed", "tendon_q_deg", "tendon_F_n",
                                   "tendon_battery_J", "tendon_severed")}


def preset_tendon():
    """q -> ~0 and severed -> false through the proxy: arm, sever, micro-arm."""
    proxy_post("/api/effort", {"joint_index": 15, "u": 1}); time.sleep(1.5)
    proxy_post("/api/sever", {"joint_index": 15}); time.sleep(3.0)
    proxy_post("/api/effort", {"joint_index": 15, "u": -1}); time.sleep(0.4)
    proxy_post("/api/effort", {"joint_index": 15, "u": 0.05}); time.sleep(0.35)
    proxy_post("/api/effort", {"joint_index": 15, "u": -1}); time.sleep(0.5)
    return tstate()


def diag(page):
    return page.evaluate("""()=>{
        var v=document.getElementById('verdict');
        var ro=document.getElementById('effort-readout');
        return {
            verdict: v ? v.textContent : '',
            lessonTitle: (document.getElementById('lesson-title')||{textContent:''}).textContent,
            lessonBody: (document.getElementById('lesson-body')||{textContent:''}).textContent,
            lessonIndex: (document.getElementById('lesson-index')||{textContent:''}).textContent,
            readout: ro ? ro.textContent : '',
            passed: !!v && v.textContent.indexOf('PASSED')>=0,
            playOn: document.getElementById('screen-play').classList.contains('on'),
        };
    }""")


def wait_for(pred, secs=25.0, interval=0.3):
    t = time.time()
    while time.time() - t < secs:
        if pred():
            return True
        time.sleep(interval)
    return False


def project(page, wx, wy, wz):
    rect = page.evaluate("""()=>{var c=document.getElementById('gl');
        var r=c.getBoundingClientRect();
        return {left:r.left, top:r.top, width:r.width, height:r.height,
                aspect:r.width/r.height};}""")
    r, th, ph = CAM['r'], CAM['theta'], CAM['phi']
    ch = math.cos(ph)
    eye = [CAM['target'][0] + r * ch * math.sin(th),
           CAM['target'][1] + r * math.sin(ph),
           CAM['target'][2] + r * ch * math.cos(th)]
    tgt = CAM['target']
    sub = lambda a, b: [a[0]-b[0], a[1]-b[1], a[2]-b[2]]
    dot = lambda a, b: a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
    crs = lambda a, b: [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    nrm = lambda a: [x/(math.hypot(*a) or 1) for x in a]
    tanF = math.tan(math.radians(CAM['fov'])/2)
    fwd = nrm(sub(tgt, eye))
    right = nrm(crs(fwd, [0, 1, 0]))
    up = crs(right, fwd)
    d = sub([wx, wy, wz], eye)
    depth = dot(d, fwd)
    ndcX = (dot(d, right)/depth) / (tanF*rect['aspect'])
    ndcY = (dot(d, up)/depth) / tanF
    return (rect['left'] + (ndcX+1)/2*rect['width'],
            rect['top'] + (1-ndcY)/2*rect['height'])


def cells_p(page):
    try:
        s = page.evaluate("()=>fetch('/api/state').then(r=>r.json())")
        return [float(c.get('P') or 0) for c in (s.get('cells') or [])]
    except Exception:
        return []


def set_force(page, v):
    page.evaluate("""(v)=>{var e=document.getElementById('force');
        e.value=String(v); e.dispatchEvent(new Event('input',{bubbles:true}));}""", v)


def drag_slider(page, sel, val=None, vmin=0, vmax=100, steps=12):
    """REAL mouse drag: press mid-track, sweep toward the pixel matching
    `val` (default: right edge), release there. Fires the input-event ramp
    a player drag makes. Exact value is then pinned with native keys
    (End / arrows) — still real UI."""
    box = page.locator(sel).bounding_box()
    cy = box['y'] + box['height'] / 2
    frac = 1.0 if val is None else (val - vmin) / (vmax - vmin)
    x0 = box['x'] + box['width'] * 0.5
    x1 = box['x'] + box['width'] * min(0.985, max(0.015, frac)) - 1
    page.mouse.move(x0, cy)
    page.mouse.down()
    for i in range(1, steps + 1):
        page.mouse.move(x0 + (x1 - x0) * i / steps, cy)
        time.sleep(0.03)
    page.mouse.up()
    time.sleep(0.3)


def set_slider_exact(page, sel, val, from_max, vmin, vmax):
    """Real keyboard interaction on the focused range input: End pins the
    native max, ArrowLeft steps down to val (step=1)."""
    page.click(sel)                       # focus (real click)
    page.keyboard.press("End")
    time.sleep(0.15)
    n = int(round(from_max - val))
    for _ in range(n):
        page.keyboard.press("ArrowLeft")
    time.sleep(0.3)
    got = page.evaluate(f"()=>document.getElementById('{sel[1:]}').value")
    return int(got)


def press_adaptive(page, target, cell_idx, bar_pa, force0, tag,
                   attempts=6, hold=0.45, force_max=None, grow=1.6):
    bx, by = project(page, *target)
    force = force0
    for a in range(1, attempts + 1):
        set_force(page, force)
        page.mouse.move(bx, by, steps=8)
        time.sleep(0.15)
        page.mouse.down()
        t0 = time.time()
        pmax = 0.0
        while time.time() - t0 < hold:
            ps = cells_p(page)
            if ps:
                v = (max(abs(x) for x in ps) if cell_idx is None
                     else (ps[cell_idx] if len(ps) > cell_idx else 0.0))
                pmax = max(pmax, v)
            time.sleep(0.1)
        page.mouse.up()
        try:
            page.click("#letgo-btn", timeout=1200)
        except Exception:
            pass
        d = diag(page)
        log(f"  {tag} attempt {a}: force={force} N pmax={pmax:.0f} Pa "
            f"verdict={d['verdict'][:56]!r}")
        if 'ruptured' in d['verdict']:
            try:
                page.click("#try-again-btn", timeout=2000)
            except Exception:
                pass
            time.sleep(1.2)
            force = max(500, int(force * 0.6))
            continue
        if pmax >= bar_pa:
            return True, force, pmax
        nf = min(force_max or 50000, int(force * grow))
        force = nf if nf > force else min(50000, force + 500)
        time.sleep(1.0)
    return False, force, pmax


def wait_passed(page, tag, secs=30.0):
    ok = wait_for(lambda: diag(page)['passed'], secs=secs)
    d = diag(page)
    log(f"LESSON {tag} PASSED: {ok} | verdict: {d['verdict'][:110]!r}")
    RESULT[tag] = ok
    return ok, d['verdict']


def main():
    page_errors = []
    fresh_dir = tempfile.mkdtemp(prefix="chimera-r10-")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            fresh_dir, headless=False, viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        log("fresh profile:", fresh_dir)
        page.goto(URL + "/?debug=1", wait_until="load", timeout=30000)
        time.sleep(2.0)
        page.fill("#name-input", "R10-Qwen")
        page.click("#play-btn")
        time.sleep(1.5)
        RESULT["gameplay_started"] = bool(diag(page)["playOn"])
        log("gameplay started (#screen-play.on):", RESULT["gameplay_started"])
        try:
            page.click("#intro-begin", timeout=1500)
        except Exception:
            pass
        time.sleep(0.8)

        # ---- preset the tendon BEFORE any lesson 6 exposure ----
        # Boot shows lesson 1, whose judge ignores the tendon. Leaving an
        # armed/severed/high-q tendon from a previous session would let the
        # lesson 6 judge latch during the card scan (a state a fresh engine
        # boot never shows); limp the tendon first so every later step is
        # honest.
        pre = preset_tendon()
        log("preset:", json.dumps({k: round(v, 2) if isinstance(v, float) else v
                                   for k, v in pre.items()}))

        # ---- 12-lesson keyboard card scan (real key presses) ----
        lessons_json = proxy_get("/lessons.json")
        lmap = {l["title"]: l for l in lessons_json["lessons"]}
        plan = [("1", "WAKE THE CELL"), ("2", "THE GENTLE HAND"),
                ("3", "THE HEALING"), ("4", "BEND THE KNEE"),
                ("5", "RAISE THE HAND"), ("6", "FEEL THE MUSCLE"),
                ("7", "THE WHOLE BODY"), ("8", "THE BALANCE"),
                ("9", "THE HEAVY HAND"), ("0", "THE CASCADE"),
                ("]", "THE STAND"), ("`", "THE GRADUATION"),
                ("q", "FEEL THE MUSCLE")]
        for k, want in plan:
            page.keyboard.press(k)
            time.sleep(0.9)
            d = diag(page)
            lj = lmap.get(d["lessonTitle"], {})
            card = {"key": k, "want": want, "title": d["lessonTitle"],
                    "index": d["lessonIndex"],
                    "title_ok": d["lessonTitle"] == want,
                    "body_len": len(d["lessonBody"]),
                    "hint_present": bool(lj.get("hint")),
                    "hint_len": len(lj.get("hint") or "")}
            CARDS.append(card)
            log("CARD", json.dumps(card))
        RESULT["cards_all_ok"] = all(
            c["title_ok"] and c["body_len"] > 10 and c["hint_present"]
            for c in CARDS)
        RESULT["q_key_reached_6"] = CARDS[-1]["title_ok"]

        # ---- lesson 6 via the LESSON LIST (prev/next buttons) ----
        page.keyboard.press("1"); time.sleep(0.8)
        for _ in range(5):
            page.click("#lesson-next"); time.sleep(0.45)
        d = diag(page)
        RESULT["list_reached_6"] = d["lessonTitle"] == "FEEL THE MUSCLE"
        log("lesson list (next x5) reached:", d["lessonIndex"], d["lessonTitle"])

        # ---- lesson 6 gameplay: before shot, real drag, sever ----
        log("preset:", json.dumps({k: round(v, 2) if isinstance(v, float) else v
                                   for k, v in pre.items()}))
        time.sleep(1.2)
        d = diag(page)
        RESULT["before_readout"] = d["readout"]
        page.screenshot(path=f"{EV}/10_before_contract.png")
        batt_before = tstate()["tendon_battery_J"]
        drag_slider(page, "#effort-u", 100, 0, 100)
        # real drag lands near the right edge; pin to exactly 100% with the
        # native End key on the still-focused slider (real UI interaction)
        page.keyboard.press("End")
        time.sleep(0.3)
        RESULT["slider_value_after_drag"] = page.evaluate(
            "()=>document.getElementById('effort-u').value")
        flexed = wait_for(lambda: (tstate()["tendon_q_deg"] or 0) >= 40
                          and re.search(r"knee (4[0-9]|[5-9][0-9]|[1-9][0-9]{2,})\.?\d*°",
                                        diag(page)["readout"]) is not None,
                          secs=20)
        flex_t = tstate()
        d = diag(page)
        RESULT["flexed"] = flexed
        RESULT["flex_state"] = flex_t
        RESULT["contracted_readout"] = d["readout"]
        RESULT["battery_before_J"] = batt_before
        page.screenshot(path=f"{EV}/10_contracted.png")
        log(f"FLEX: {flexed} q={flex_t['tendon_q_deg']:.2f} "
            f"F={flex_t['tendon_F_n']:.1f} batt {batt_before:.1f}->"
            f"{flex_t['tendon_battery_J']:.1f} readout={d['readout']!r}")
        page.click("#effort-sever-btn")
        # The judge latches PASSED on the measured q < 5 dip; the leg then
        # OSCILLATES (swings past zero). Wait for PASSED, then for the leg
        # to SETTLE near 0, and screenshot the honest limp frame: readout
        # SEVERED + |knee| < 5 + PASSED banner, all on screen together.
        passed, verdict = wait_passed(page, "feel_the_muscle", secs=30)
        RESULT["passed_verdict_first"] = verdict
        t0 = time.time()
        stable = 0
        last_q = None
        while time.time() - t0 < 15.0:
            q = tstate()["tendon_q_deg"] or 99.0
            if abs(q) < 5.0 and (last_q is None or abs(q - last_q) < 2.0):
                stable += 1
                if stable >= 2:
                    break
            else:
                stable = 0
            last_q = q
            time.sleep(0.35)
        limp_t = tstate()
        d = diag(page)
        page.screenshot(path=f"{EV}/10_severed_passed.png")
        m = re.search(r"knee (-?\d+(?:\.\d+)?)°", d["readout"])
        RESULT["severed_shot_caught"] = bool(
            "SEVERED" in d["readout"] and m and abs(float(m.group(1))) < 5.0
            and "PASSED" in d["verdict"])
        RESULT["severed_readout"] = d["readout"]
        RESULT["limp_state"] = limp_t
        RESULT["pass_line_shown"] = (lessons_json["lessons"][5]["pass_line"]
                                     in verdict)
        log(f"LIMP: q={limp_t['tendon_q_deg']:.2f} sev={limp_t['tendon_severed']} "
            f"pass_line_in_verdict={RESULT['pass_line_shown']} readout={d['readout']!r}")

        # ---- disarm-on-switch: bend_the_knee via its OWN slider+post ----
        page.keyboard.press("4"); time.sleep(1.5)
        RESULT["disarm_armed_after_switch"] = tstate()["tendon_armed"]
        # pose_reach passes only within POSE_TOL_DEG of 40: real click+End+
        # ArrowLeft interaction pins the slider at exactly 40
        RESULT["pose_slider_value"] = set_slider_exact(page, "#pose-angle", 40, 90, -90, 90)
        page.click("#pose-post")
        bk_ok, _ = wait_passed(page, "bend_the_knee", secs=20)
        RESULT["bend_knee_post_accepted"] = bk_ok

        # ---- wake_the_cell end-to-end (press past 0.02 MPa, let go, calm) ----
        page.keyboard.press("1"); time.sleep(1.0)
        wc_ok = False
        okp, force, pmax = press_adaptive(page, BELLY, 1, 20000, 9000,
                                          "wake_the_cell")
        if okp:
            wc_ok, _ = wait_passed(page, "wake_the_cell", secs=35)
        RESULT["wake_the_cell"] = wc_ok

        RESULT["page_errors"] = len(page_errors)
        for e in page_errors:
            log("PAGEERROR:", e)
        ctx.close()

    with open(f"{EV}/10_regression.txt", "w") as f:
        f.write(f"fresh_profile={fresh_dir}\n")
        f.write(f"gameplay_started={RESULT.get('gameplay_started')}\n")
        f.write(f"q_key_reached_6={RESULT.get('q_key_reached_6')}\n")
        f.write(f"list_reached_6={RESULT.get('list_reached_6')}\n")
        f.write(f"cards_all_ok={RESULT.get('cards_all_ok')}\n")
        for i, c in enumerate(CARDS):
            f.write(f"card {i+1:02d} key={c['key']!r} title_ok={c['title_ok']} "
                    f"body_len={c['body_len']} hint_len={c['hint_len']} "
                    f"title={c['title']!r}\n")
        for k in ("slider_value_after_drag", "pose_slider_value", "flexed",
                  "before_readout",
                  "contracted_readout", "severed_shot_caught",
                  "severed_readout", "battery_before_J",
                  "pass_line_shown", "disarm_armed_after_switch",
                  "bend_the_knee", "wake_the_cell", "page_errors"):
            f.write(f"{k}={RESULT.get(k)}\n")
        f.write(f"flex={json.dumps(RESULT.get('flex_state'))}\n")
        f.write(f"limp={json.dumps(RESULT.get('limp_state'))}\n")
        f.write("---- session log ----\n")
        f.write("\n".join(log_lines) + "\n")
    order = ["gameplay_started", "q_key_reached_6", "list_reached_6",
             "cards_all_ok", "flexed", "feel_the_muscle", "severed_shot_caught",
             "pass_line_shown", "bend_the_knee", "wake_the_cell"]
    allpass = all(RESULT.get(k) for k in order) and RESULT.get("page_errors") == 0
    log("OVERALL:", "PASS" if allpass else "FAIL")


main()
