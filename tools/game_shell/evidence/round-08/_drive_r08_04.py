"""Round-08 08_04: lesson-count-aware keyboard jump map verification.

Fresh-profile headless Chromium (pattern: _drive_r08_03.py). The page fix:
digits 1-9 -> lessons 1-9, '0' -> lesson 10 (unchanged keys), and the free
number-row key '`' -> lesson 11 when the pack has more than ten lessons.

Checks:
  1. Press EVERY mapped key on a fresh page; the #lesson-title DOM text
     must match the expected lesson title from lessons.json (11 keys).
  2. ']' and '[' still step lessons (wrap both ways).
  3. ' ' still presses: on lesson 1 a space keydown lifts the /api/state
     cell pressure readout (and the hand line says "pressing").
  4. Regression: '4' bend_the_knee and '5' raise_the_hand reachable, their
     pose rows present and bound (joint label + angle slider + post button).
  5. pageErrors == 0.
Screenshots: 08_04_keyboard_lesson11.png (lesson 11 card).
Machine record: 08_04_drive.txt. Leaves the body at rest, stack running.
"""
import time, tempfile, json, urllib.request
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"
ENGINE = "http://127.0.0.1:8110"
ROOT = r"E:\PythonChimera"
EV = ROOT + r"\tools\game_shell\evidence\round-08"
log_lines = []

LESSONS = json.load(open(ROOT + r"\tools\game_shell\lessons.json", encoding="utf-8"))["lessons"]
KEYMAP = [str(d) for d in range(1, 10)] + ["0", "`"]      # 11 keys, 11 lessons


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    log_lines.append(s)


def engine_get(path):
    with urllib.request.urlopen(ENGINE + path, timeout=10) as r:
        return r.read()


def diag(page):
    return page.evaluate("""()=>({
        lessonTitle: (document.getElementById('lesson-title')||{textContent:''}).textContent,
        lessonIndex: (document.getElementById('lesson-index')||{textContent:''}).textContent,
        handState: (document.getElementById('hand-state')||{textContent:''}).textContent,
        blood: (document.getElementById('blood')||{textContent:''}).textContent,
        poseVisible: (document.getElementById('pose-btn-wrap')||{style:{display:'none'}}).style.display !== 'none',
        poseJoint: (document.querySelector('.pose-joint')||{textContent:''}).textContent,
        poseSlider: !!document.querySelector('#pose-btn-wrap input[type=range]'),
        posePost: !!document.querySelector('#pose-btn-wrap .pose-post')
    })""")


def press(page, key):
    page.evaluate("(k)=>window.dispatchEvent(new KeyboardEvent('keydown',{key:k,bubbles:true,cancelable:true}))", key)
    time.sleep(0.9)


def release(page, key):
    page.evaluate("(k)=>window.dispatchEvent(new KeyboardEvent('keyup',{key:k,bubbles:true,cancelable:true}))", key)


def max_cell_p():
    s = json.loads(urllib.request.urlopen(URL + "/api/state", timeout=10).read())
    cells = s.get("cells") or []
    return max((abs(float(c.get("P") or 0)) for c in cells), default=0.0)


def dismiss_overlay(page):
    for sel in ("#payoff-continue", "#intro-begin"):
        try:
            page.click(sel, timeout=1200)
            time.sleep(0.5)
        except Exception:
            pass


def main():
    page_errors = []
    fresh_dir = tempfile.mkdtemp(prefix="chimera-r08-04-")
    results = {}          # key -> (expected, observed, ok)
    bracket_ok = space_ok = False
    space_delta = None
    regress = {}
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            fresh_dir, headless=True,
            viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        log("fresh profile:", fresh_dir)

        page.goto(URL, wait_until="load", timeout=30000)
        time.sleep(2.0)
        page.fill("#name-input", "Tiel-R08-04")
        page.click("#play-btn")
        time.sleep(1.5)
        dismiss_overlay(page)
        d = diag(page)
        log("start lesson:", repr(d['lessonTitle']), "|", d['lessonIndex'])

        # ---- 1. every mapped digit key -> expected lesson title ----
        assert len(KEYMAP) == len(LESSONS), "keymap/lesson count mismatch"
        for ki, key in enumerate(KEYMAP):
            press(page, key)
            d = diag(page)
            exp = LESSONS[ki]["title"]
            ok = d['lessonTitle'].strip().upper() == exp.strip().upper()
            results[key] = (exp, d['lessonTitle'], ok, d['lessonIndex'])
            log(f"key {key!r:4} -> {d['lessonIndex']} title={d['lessonTitle']!r} expected={exp!r} ok={ok}")

        # ---- 2. [ ] still step lessons ----
        press(page, '`')                       # lesson 11
        t11 = diag(page)['lessonTitle']
        press(page, ']')                       # wrap -> lesson 1
        d = diag(page)
        wrap_fwd = d['lessonTitle'].strip().upper() == LESSONS[0]['title'].upper()
        press(page, '[')                       # wrap back -> lesson 11
        d = diag(page)
        wrap_back = d['lessonTitle'].strip().upper() == LESSONS[10]['title'].upper()
        press(page, ']')                       # step to lesson 1
        step_fwd = diag(page)['lessonTitle'].strip().upper() == LESSONS[0]['title'].upper()
        bracket_ok = wrap_fwd and wrap_back and step_fwd
        log(f"brackets: ] from 11 -> {LESSONS[0]['title']!r} ok={wrap_fwd} | "
            f"[ -> {LESSONS[10]['title']!r} ok={wrap_back} | ] -> lesson 1 ok={step_fwd} "
            f"(lesson 11 title was {t11!r})")

        # ---- 3. SPACE still presses: pressure readout lifts on lesson 1 ----
        press(page, '1')
        page.evaluate("()=>{var e=document.getElementById('force'); e.value='12000';"
                      " e.dispatchEvent(new Event('input',{bubbles:true}));}")
        time.sleep(1.0)
        p0 = max_cell_p()
        press(page, ' ')                       # keydown starts the press
        hand_mid = None
        t0 = time.time()
        while time.time() - t0 < 4.0:
            time.sleep(0.4)
            hand_mid = diag(page)['handState']
            pv = max_cell_p()
            if pv > p0 + 2000:
                break
        p1 = max_cell_p()
        release(page, ' ')                     # keyup ends the press
        time.sleep(1.0)
        try:
            page.click("#letgo-btn", timeout=1200)
        except Exception:
            pass
        space_delta = p1 - p0
        space_ok = space_delta > 2000 and 'pressing' in (hand_mid or '').lower()
        log(f"space press: p0={p0:.0f} Pa p1={p1:.0f} Pa delta={space_delta:.0f} Pa "
            f"hand={hand_mid!r} ok={space_ok}")
        dismiss_overlay(page)                  # a wake pass may raise the payoff

        # ---- 4. regression: lessons 4 and 5 reachable, pose rows bound ----
        for key, idx, want_joint in (('4', 3, 'knee_L'), ('5', 4, 'wrist_L')):
            press(page, key)
            d = diag(page)
            ok = d['lessonTitle'].strip().upper() == LESSONS[idx]['title'].upper()
            bound = d['poseVisible'] and d['poseSlider'] and d['posePost'] and d['poseJoint'] == want_joint
            regress[key] = dict(title=d['lessonTitle'], joint=d['poseJoint'],
                                pose_visible=d['poseVisible'], slider=d['poseSlider'],
                                post=d['posePost'], title_ok=ok, bound=bound)
            log(f"regression key {key!r}: title={d['lessonTitle']!r} joint={d['poseJoint']!r} "
                f"pose_visible={d['poseVisible']} slider={d['poseSlider']} "
                f"post={d['posePost']} bound={bound}")

        # ---- 5. lesson 11 card screenshot ----
        press(page, '`')
        d = diag(page)
        l11_ok = d['lessonTitle'].strip().upper() == LESSONS[10]['title'].upper()
        log(f"lesson 11 via '`': {d['lessonIndex']} title={d['lessonTitle']!r} ok={l11_ok}")
        page.screenshot(path=f"{EV}/08_04_keyboard_lesson11.png")
        log("screenshot: 08_04_keyboard_lesson11.png (lesson 11 card)")

        # leave at rest: stand, let go
        press(page, 'r')
        time.sleep(1.0)
        try:
            page.click("#letgo-btn", timeout=1000)
        except Exception:
            pass
        ctx.close()

    log(f"PAGE ERRORS: {len(page_errors)}")
    for e in page_errors:
        log("  PAGEERROR:", e)

    all_digits = all(v[2] for v in results.values())
    regress_ok = all(v['title_ok'] and v['bound'] for v in regress.values())
    ok = all_digits and bracket_ok and space_ok and l11_ok and regress_ok and not page_errors

    with open(f"{EV}/08_04_drive.txt", "w") as f:
        f.write("tag=08_04 keyboard lesson-jump map (count-aware, ` -> lesson 11)\n")
        f.write(f"fresh_profile={fresh_dir}\n")
        for key, (exp, obs, k, idx) in results.items():
            f.write(f"key={key!r} idx={idx!r} expected={exp!r} observed={obs!r} ok={k}\n")
        f.write(f"all_digits_ok={all_digits}\nbrackets_ok={bracket_ok}\n")
        f.write(f"space_ok={space_ok} space_delta_pa={space_delta:.0f}\n")
        for key, v in regress.items():
            f.write(f"regress key={key} {json.dumps(v)}\n")
        f.write(f"lesson11_screenshot_ok={l11_ok}\n")
        f.write(f"page_errors={len(page_errors)}\n")
        for e in page_errors:
            f.write("PAGEERROR: %s\n" % e)
        f.write(f"OVERALL: {'PASS' if ok else 'FAIL'}\n")
        f.write("---- session log ----\n")
        f.write("\n".join(log_lines) + "\n")
    log(f"wrote {EV}\\08_04_drive.txt")
    log("OVERALL:", "PASS" if ok else "FAIL")


main()
