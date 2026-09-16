"""Reproduce readback memory/access controls in owned presenting processes."""
import argparse,base64,hashlib,http.client,json,os,socket,statistics,subprocess,time
from pathlib import Path

SWITCHES=("CHIMERA_RB_UNCACHED_CONTROL","CHIMERA_RB_DIRECT_CONTROL",
          "CHIMERA_RB_MEMCPY_SWIZZLE","CHIMERA_RB_READER")
def run(exe,scene,port,output):
    output.mkdir(parents=True,exist_ok=True)
    expected=json.loads(scene.read_text(encoding="utf-8"))["scene_sha256"]
    cases={}
    def request(path="/thermal_state",value=None):
        c=http.client.HTTPConnection("127.0.0.1",port,timeout=8)
        t=time.perf_counter()
        c.request("GET" if value is None else "POST",path,
                  body=None if value is None else json.dumps(value),
                  headers={"Content-Type":"application/json"})
        response=c.getresponse();r=json.loads(response.read());c.close()
        return r,(time.perf_counter()-t)*1000
    for name,options in (
        ("uncached_direct",{"CHIMERA_RB_UNCACHED_CONTROL":"1","CHIMERA_RB_DIRECT_CONTROL":"1"}),
        ("uncached_bulk",{"CHIMERA_RB_UNCACHED_CONTROL":"1"}),
        ("cached_default",{})):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1",port))  # refuse occupied port, never stop its owner
        env={k:v for k,v in os.environ.items() if k not in SWITCHES};env.update(options)
        startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow=0
        with (output/(name+".log")).open("w",encoding="utf-8") as log:
            proc=subprocess.Popen([str(exe),str(port),"--hidden","1600","900","--no-restore",
                "--thermal-salvage",str(scene)],cwd=exe.parent,env=env,
                stdout=log,stderr=subprocess.STDOUT,startupinfo=startup,
                creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                deadline=time.monotonic()+25
                while True:
                    assert proc.poll() is None,("native_exit",proc.returncode)
                    try:
                        state,_=request()
                        assert state["scene_sha256"]==expected
                        break
                    except (OSError,KeyError):
                        if time.monotonic()>deadline:raise TimeoutError("readiness")
                        time.sleep(.1)
                request(value={"reset":True});request(value={"paused":True})
                captures=[]
                for i in range(5):
                    f,ms=request("/thermal_frame?w=960");assert f["ok"],f
                    image=base64.b64decode(f["image_base64"])
                    (output/(name+"_"+str(i)+".jpg")).write_bytes(image)
                    captures.append({k:v for k,v in f.items() if k not in ("image_base64","state")})
                    captures[-1].update(client_ms=ms,image_sha256=hashlib.sha256(image).hexdigest(),
                        camera=f["state"]["render_camera"],position_m=f["state"]["position_m"])
                chrome,_=request("/studio_chrome")
                cases[name]={"captures":captures,"environment":options,
                    "memory":{k:chrome[k] for k in ("rb_mem_type","rb_mem_flags","gpu")},
                    "warm_median_client_ms":statistics.median(x["client_ms"] for x in captures[1:]),
                    "warm_median_read_phases_us":[statistics.median(x["read_phases_us"][j] for x in captures[1:]) for j in range(5)]}
            finally:
                if proc.poll() is None:proc.terminate()
                proc.wait(timeout=10)  # only the process handle created above
    images={c["image_sha256"] for case in cases.values() for c in case["captures"]}
    assert len(images)==1,("pixel_mismatch",images)
    assert cases["cached_default"]["memory"]["rb_mem_flags"]&8
    assert not cases["uncached_direct"]["memory"]["rb_mem_flags"]&8
    assert not cases["uncached_bulk"]["memory"]["rb_mem_flags"]&8
    result={"schema":"chimera.native_readback_controls.v1","status":"pass",
        "method":"Exploratory controlled comparison; elapsed times reported, not portable pass thresholds.",
        "exe_sha256":hashlib.sha256(exe.read_bytes()).hexdigest(),
        "scene_file_sha256":hashlib.sha256(scene.read_bytes()).hexdigest(),
        "pixel_identity":next(iter(images)),"cases":cases}
    (output/"readback_controls.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({n:{k:v for k,v in c.items() if k!="captures"} for n,c in cases.items()},indent=2))
    return result
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe",type=Path,required=True);p.add_argument("--scene",type=Path,required=True)
    p.add_argument("--port",type=int,default=8118);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();run(a.exe.resolve(),a.scene.resolve(),a.port,a.output.resolve())
if __name__=="__main__":main()
