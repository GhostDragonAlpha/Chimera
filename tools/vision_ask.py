"""p1vl_ask_one.py — single-question blind vision ask, retry-hardened.

Usage: python .tmp/p1vl_ask_one.py Q1|Q2|Q3 [width]
The trial design (questions + measured answer key) lives in Saved/vision_trial/.
"""
import base64, io, json, os, sys, time, urllib.request
from PIL import Image

BASE = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = sys.argv[3] if len(sys.argv) > 3 else "mradermacher/p1-vl-30b-a3b"  # Q4_K_S
DIR = "Saved/vision_trial"

QS = {
    "Q1": ("Look at this creature. Which direction is it facing — toward you, away from you, or to one side? "
           "Then: the creature has a left arm and a right arm, from ITS OWN perspective. "
           "On which side of the image does its LEFT arm appear — the left side of the image or the right side?",
           ["A_front_rest.png"]),
    "Q2": ("You are looking at this creature from one of its sides. Which side are you seeing — its left side or its right side? "
           "Explain how you can tell.",
           ["B_leftside_rest.png"]),
    "Q3": ("Here are two images of the same creature. Exactly one of the two images shows the creature with "
           "one arm bent at the elbow. Which image is it — the first or the second? "
           "And the bent arm: is it the creature's LEFT arm or its RIGHT arm (its own perspective)?",
           ["A_front_rest.png", "D_front_elbowL50.png"]),
}

def img_b64(path, width):
    im = Image.open(path).convert("RGB")
    h = int(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()

def one_call(text, images, timeout=1200):
    content = [{"type": "text", "text": text}]
    for b in images:
        content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + b}})
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": content}],
                       "temperature": 0.2, "max_tokens": 2500, "stream": False}).encode()
    req = urllib.request.Request(BASE, data=body, headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:300]}") from None
    msg = d["choices"][0]["message"]
    ans = msg.get("content") or ""
    return ans, time.time() - t0

def main():
    qname = sys.argv[1] if len(sys.argv) > 1 else "Q1"
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 640
    text, files = QS[qname]
    images = [img_b64(os.path.join(DIR, f), width) for f in files]
    ans, dt, err = None, 0.0, None
    for attempt in range(4):
        try:
            ans, dt = one_call(text, images)
            break
        except Exception as e:
            err = repr(e)[:250]
            print(f"attempt {attempt}: {err}", flush=True)
            time.sleep(8)
    out = {"q": qname, "width": width, "answer": ans, "seconds": round(dt, 1), "error": err}
    print(json.dumps(out, indent=1), flush=True)
    tag = MODEL.split("/")[-1].replace(".", "_")
    json.dump(out, open(f"{DIR}/{qname}_answer_{tag}.json", "w"), indent=1)

if __name__ == "__main__":
    main()
