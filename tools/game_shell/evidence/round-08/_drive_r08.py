"""Round-08 driver: reproduce / verify the knee-bend foot behaviour.

Usage: python _drive_r08.py <tag> [deg]
  screenshots: <tag>_knee_<deg>.png etc; prints a machine-readable log.
"""
import sys, time, tempfile, json, urllib.request
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"
ENGINE = "http://127.0.0.1:8110"
EV = r"E:\PythonChimera\tools\game_shell\evidence\round-08"

TAG = sys.argv[1] if len(sys.argv) > 1 else "08_01"
DEG = int(sys.argv[2]) if len(sys.argv) > 2 else 40


def engine_get(path):
    with urllib.request.urlopen(ENGINE + path, timeout=5) as r:
        return json.load(r)


def diag(page):
    return page.evaluate("""()=>{
        return {
            verdict: document.getElementById('verdict').textContent,
            lessonTitle: document.getElementById('lesson-title').textContent,
            playScreenOn: document.getElementById('screen-play').classList.contains('on'),
            poseVal: (document.getElementById('pose-val')||{textContent:''}).textContent,
            passLineVisible: (function(){var v=document.getElementById('verdict');
                return !!v && v.textContent.indexOf('PASSED')>=0;})()
        };
    }""")


def wait_for(pred, secs=8.0, interval=0.15):
    t = time.time()
    while time.time() - t < secs:
        if pred():
            return True
        time.sleep(interval)
    return False


def main():
    page_errors = []
    console_msgs = []
    fresh_dir = tempfile.mkdtemp(prefix="chimera-r08-")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            fresh_dir, headless=True,
            viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("console", lambda e: console_msgs.append(f"[{e.type}] {e.text}"))
        print("fresh profile:", fresh_dir)

        print("=== LOAD ===")
        page.goto(URL, wait_until="load", timeout=30000)
        time.sleep(1.5)
        page.fill("#name-input", "Tiel-R08")
        page.click("#play-btn")
        time.sleep(1.5)
        page.evaluate("()=>{var o=document.getElementById('intro-overlay'); if(o) o.classList.add('hidden');}")
        d = diag(page)
        print("lesson:", repr(d['lessonTitle']), "| play:", d['playScreenOn'])

        print("=== NAVIGATE to BEND THE KNEE (key '4' -> lesson idx 3) ===")
        page.evaluate("()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'4',bubbles:true,cancelable:true}))")
        time.sleep(1.0)
        d = diag(page)
        print("lesson:", repr(d['lessonTitle']), "| verdict:", d['verdict'][:70])
        assert 'KNEE' in d['lessonTitle'].upper(), "not on the knee lesson"

        print(f"=== SET knee_L slider to {DEG} deg + POST ===")
        page.evaluate("""(a)=>{var e=document.getElementById('pose-angle');
            e.value=String(a[0]); e.dispatchEvent(new Event('input',{bubbles:true}));}""", [DEG])
        time.sleep(0.2)
        page.click("#pose-post")
        latched = wait_for(lambda: DEG and ('PASSED' in diag(page)['verdict']), 8)
        time.sleep(1.2)  # let the engine settle the pose
        d = diag(page)
        print("pass_line visible:", latched, "| verdict:", d['verdict'][:90])
        st = engine_get("/tick_state")
        print("engine ticks:", st['ticks'], "| body_model:", st['body_model'])

        page.screenshot(path=f"{EV}/{TAG}_knee_{DEG}.png")
        print(f"screenshot: {EV}\\{TAG}_knee_{DEG}.png")

        print("=== RESET pose (post 0) ===")
        page.evaluate("""()=>{var e=document.getElementById('pose-angle');
            e.value='0'; e.dispatchEvent(new Event('input',{bubbles:true}));}""")
        time.sleep(0.2)
        page.click("#pose-post")
        time.sleep(1.0)
        page.screenshot(path=f"{EV}/{TAG}_knee_0.png")

        print("PAGE ERRORS (%d)" % len(page_errors))
        for e in page_errors:
            print("  PAGEERROR:", e)
        ctx.close()

    with open(f"{EV}/{TAG}_drive.txt", "w") as f:
        f.write(f"tag={TAG} deg={DEG}\nfresh_profile={fresh_dir}\n")
        f.write(f"page_errors={len(page_errors)}\n")
        for e in page_errors:
            f.write("PAGEERROR: %s\n" % e)
        f.write(f"console_messages={len(console_msgs)}\n")
        for m in console_msgs:
            f.write("CONSOLE: %s\n" % m)
    print(f"wrote {TAG}_drive.txt")


main()
