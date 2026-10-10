import re, time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"
NAME = "Tiel-Probe"

def blood(page):
    return page.evaluate("()=>document.getElementById('blood').textContent.replace(/\\s+/g,' ')")

def set_force(page, v):
    page.evaluate("(a)=>{var e=document.getElementById('force');e.value=String(a[0]);e.dispatchEvent(new Event('input',{bubbles:true}));}", [v])

def down(page, px, py):
    page.evaluate("(a)=>{var c=document.getElementById('gl');var o={type:'pointerdown',clientX:a[0],clientY:a[1],button:0,buttons:1,pointerId:1,pointerType:'mouse',isPrimary:true,pressure:0.6};c.dispatchEvent(new PointerEvent(o.type,o));}", [px, py])

def up(page, px, py):
    page.evaluate("(a)=>{var c=document.getElementById('gl');var o={type:'pointerup',clientX:a[0],clientY:a[1],button:0,buttons:0,pointerId:1,pointerType:'mouse',isPrimary:true,pressure:0};c.dispatchEvent(new PointerEvent(o.type,o));}", [px, py])

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=['--use-gl=angle','--use-angle=swiftshader'])
        page = b.new_context(viewport={'width':1280,'height':900}).new_page()
        page.goto(URL, wait_until="load", timeout=30000)
        time.sleep(1.5)
        page.fill("#name-input", NAME); page.click("#play-btn"); time.sleep(1.0)
        box = page.evaluate("()=>{var r=document.getElementById('gl').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2,w:r.width,h:r.height};}")
        cx, cy, w, h = box['x'], box['y'], box['w'], box['h']
        print("canvas center", round(cx,1), round(cy,1), "size", round(w,1), round(h,1))
        for frac in [ -0.30, -0.15, 0.0, 0.20, 0.35 ]:
            set_force(page, 2000)
            time.sleep(0.15)
            px, py = cx, cy + frac*h
            down(page, px, py)
            time.sleep(0.45)
            bd = blood(page)
            m = re.search(r'torso \(cell 1\):.*?P=([0-9.]+)\s*MPa', bd)
            f2 = re.search(r'feet \(cell 0\):.*?P=([0-9.]+)\s*MPa', bd)
            up(page, px, py)
            print(f"frac={frac:+.2f} pt({px:.0f},{py:.0f}) torsoP={m.group(1) if m else '?'} feetP={f2.group(1) if f2 else '?'} :: {bd[:70]}")
            time.sleep(0.8)
        b.close()

main()
