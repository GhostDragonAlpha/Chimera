"""Qualify the opt-in native scene; requires Pillow for decoded-pixel comparisons."""
import argparse, hashlib, io, json, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageChops

def qualify(port, output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    base=f"http://127.0.0.1:{port}"
    def request(path, body=None):
        data=None if body is None else json.dumps(body).encode()
        return urllib.request.urlopen(urllib.request.Request(base+path,data=data,headers={"Content-Type":"application/json"}),timeout=8).read()
    def state():return json.loads(request("/science_surface"))
    initial=state();graph_hash=initial["graph_hash"]
    results=[];images={}
    for name,control in [("flat",{"material":"Water","reset":True}),("water",{"material":"Water","force_N":.00025}),("ethanol",{"material":"Ethanol","force_N":.00025}),("released",{"force_N":0})]:
        request("/science_surface",control)
        deadline=time.monotonic()+15
        while True:
            before=state()
            assert before["ok"] and before["graph_hash"]==graph_hash,before.get("error")
            if before["converged"] and before["state_revision"]==before["render_revision"]:break
            assert time.monotonic()<deadline,"native equilibrium timeout"
            time.sleep(.05)
        raw=request("/frame");after=state()
        keys=("state_revision","render_revision","material","force_N","graph_hash")
        assert all(before[k]==after[k] for k in keys),"capture crossed physical states"
        assert abs(after["reaction_N"]-after["force_N"])<1e-7,"force balance"
        if name in ("flat","released"):assert abs(after["depth_m"])<1e-7,"release did not flatten"
        im=Image.open(io.BytesIO(raw)).convert("RGB");images[name]=im
        im.save(output/(name+".png"),optimize=True)
        stored=output/(name+".png")
        assert Image.open(stored).convert("RGB").tobytes()==im.tobytes(),"lossless storage changed pixels"
        (output/(name+"_state.json")).write_text(json.dumps(after,indent=2)+"\n",encoding="utf-8")
        results.append({"case":name,"state_revision":after["state_revision"],"material":after["material"],"force_N":after["force_N"],"depth_m":after["depth_m"],"residual_N":after["residual_N"],
                        "source_record_id":after["source_record_id"],"raw_png_sha256":hashlib.sha256(raw).hexdigest(),
                        "stored_png_sha256":hashlib.sha256(stored.read_bytes()).hexdigest(),"pixel_sha256":hashlib.sha256(im.tobytes()).hexdigest()})
    differences=[]
    for a,b in [("flat","water"),("water","ethanol"),("ethanol","released")]:
        diff=ImageChops.difference(images[a],images[b]);hist=diff.convert("L").histogram()
        changed=sum(hist[1:]);pixels=images[a].width*images[a].height
        assert changed>0,"native light did not change with physical shape"
        differences.append({"a":a,"b":b,"changed_pixels":changed,"fraction":changed/pixels})
    assert results[2]["depth_m"]>results[1]["depth_m"]*2,"source coefficient had no expected mechanical effect"
    request("/science_surface",{"material":"Ethanol","force_N":.00025})
    receipt={"captured_utc":datetime.now(timezone.utc).isoformat(),"graph_hash":graph_hash,
             "scope":"native constant-tension height-field equilibrium and rendered response; no inertial fluid or creature claim",
             "cases":results,"decoded_pixel_differences":differences,"pass":True}
    (output/"live_checks.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--port",type=int,default=8107);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();qualify(a.port,a.output)
