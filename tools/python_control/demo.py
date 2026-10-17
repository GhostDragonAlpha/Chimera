"""Launch an owned native construction world controlled from Python.

Default window is hidden. Open the printed /frame URL or pass --visible.
Press Ctrl+C to stop only this private engine; existing worlds are untouched.
"""
import argparse
import json
import shutil
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path
from .client import EngineControl
from tools.construction_packet.b2_scene_gen import make_stack, box_document


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--launch",type=Path,default=Path(".tmp/body-engine/Release/chimera_engine.exe"))
    p.add_argument("--port",type=int,default=8813)
    p.add_argument("--visible",action="store_true")
    p.add_argument("--duration",type=float,default=0,help="0 waits for Ctrl+C; positive seconds for a bounded smoke run")
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    if args.duration < 0: p.error("Duration cannot be negative")
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1",args.port))==0:raise RuntimeError("Port occupied; existing engine preserved")
    output=args.output or Path(".tmp/python-control-demo")/datetime.now().strftime("%Y%m%d-%H%M%S")
    output.mkdir(parents=True,exist_ok=False);native=output/"native";native.mkdir()
    exe=native/args.launch.name;shutil.copy2(args.launch,exe);shutil.copytree(args.launch.parent/"shaders",native/"shaders")
    base=f"http://127.0.0.1:{args.port}"
    command=[str(exe.resolve()),str(args.port)]
    if not args.visible:command.append("--hidden")
    command += ["1280","720","--no-restore"]
    with (output/"native.stdout.log").open("wb") as stdout,(output/"native.stderr.log").open("wb") as stderr:
        proc=subprocess.Popen(command,cwd=native,stdout=stdout,stderr=stderr,
                              creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        try:
            with EngineControl(base) as engine:
                for _ in range(150):
                    if proc.poll() is not None:raise RuntimeError("Private renderer exited; inspect logs")
                    try:engine.matter.state();break
                    except OSError:time.sleep(.2)
                else:raise RuntimeError("Private engine readiness timeout")
                engine.assembly.admit(make_stack())
                engine.assembly.place(box_document("python_block",.34,.40,-.01,.03,.12,.18,600,.3))
                engine.request("POST","/cameras",{"op":"save","name":"python-builder",
                    "v":[1.2,.9,.35,.25,.10,.15,0.,0.]})
                engine.request("POST","/cameras",{"op":"recall","name":"python-builder"})
                time.sleep(.6)
                engine.assembly.pause()
                state=engine.assembly.state()
                part=next(x for x in state["parts"] if x["id"]=="python_block")
                position=part["com_m"]
                projected=engine.request("POST","/project",{"x":position[0],"y":position[1]+.021,"z":position[2]})
                image=engine.frame();(output/"assembly.png").write_bytes(image)
                import struct
                width,height=struct.unpack(">II",image[16:24])
                picked=engine.request("POST","/tick_b2_pick",{"px":projected["sx"]/width,"py":projected["sy"]/height})
                if picked.get("id")!="python_block":raise AssertionError(f"Native render/pick binding failed: {picked}")
                (output/"scene-check.json").write_text(json.dumps({"parts":state,"render_pick":picked,
                    "clock":engine.assembly.clock(),"owned_pid":proc.pid,"base":base},indent=2))
                engine.assembly.pause(False)
                print(f"Python-controlled native world: {base}/frame",flush=True)
                print(f"Four physical parts; native render/pick binding passed. Output: {output}",flush=True)
                start=time.monotonic()
                while proc.poll() is None and (args.duration==0 or time.monotonic()-start<args.duration):time.sleep(.2)
        except KeyboardInterrupt:pass
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=10)
                except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)

if __name__=="__main__":main()
