# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prove Windows closes the private native child when its owning Python dies."""
import ctypes,json,subprocess,sys,time,uuid,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'python'))
if '--child' in sys.argv:
    from chimera_studio.gpu_native import PrivateEngine
    engine=PrivateEngine()
    Path(sys.argv[-1]).write_text(json.dumps({'token':sys.argv[-2],'parent':os.getpid(),'child':engine.proc.pid}))
    time.sleep(60)
else:
    token=uuid.uuid4().hex;record=ROOT/'evidence/owned-child-test.json'
    p=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--child',token,str(record)],cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW)
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];k.OpenProcess.restype=ctypes.c_void_p
    k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.CloseHandle.argtypes=[ctypes.c_void_p];k.TerminateProcess.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    parent=child=None
    try:
        deadline=time.monotonic()+35
        while time.monotonic()<deadline:
            if record.exists():
                data=json.loads(record.read_text())
                if data.get('token')==token:break
            if p.poll() is not None:raise RuntimeError('Owned test parent exited during startup')
            time.sleep(.1)
        else:raise TimeoutError('Test startup')
        # On Windows a venv python.exe may be a redirector. The fresh random token
        # identifies our actual child Python; never infer an unrelated PID from a name.
        parent=k.OpenProcess(0x100001,0,data['parent']);child=k.OpenProcess(0x100000,0,data['child']);assert parent and child
        assert k.TerminateProcess(parent,73);assert k.WaitForSingleObject(child,5000)==0,'Owned GPU engine survived parent termination'
        p.wait(timeout=5);data.pop('token');data['pass']=True;data['scope']='Only this test parent and its owned GPU child were terminated';record.write_text(json.dumps(data,indent=2));print(json.dumps(data))
    finally:
        if parent:k.CloseHandle(parent)
        if child:k.CloseHandle(child)
        if p.poll() is None:p.terminate();p.wait(timeout=5)
