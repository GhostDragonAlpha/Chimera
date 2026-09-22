"""lead takeover step 2: drive the env's own step() (correct arg plumbing);
the first step pays the opt=False integ codegen; then the 300-tick horizon."""
import sys, time
import numpy as np
from numba import cuda
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

def say(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

from walker_model import load_spec
from walker_nb_split_env import GaitWalkEnv
spec = load_spec(str(HERE.parent.parent / '.tmp' / 'gait-walker' / 'scene.json'))
E = 2
env = GaitWalkEnv(spec, E, reflex_level=0, block=32)
q0 = np.tile(spec.defaults, E)
env.reset(q0=q0, v0=np.zeros(E * 18), touching0=np.zeros(E * 2, np.int32))
say("env ready at E=2 — stepping 1 tick (pays plan+integ(opt=False)+post codegen) ...")

t0 = time.time()
env.step(1)
cuda.synchronize()
say(f"FIRST TICK COMPLETE: codegen+exec {time.time()-t0:.1f}s")

t0 = time.time()
env.step(99)
cuda.synchronize()
say(f"ticks 2-100: {time.time()-t0:.2f}s")

t0 = time.time()
rc = env.step(200)
cuda.synchronize()
dt = time.time() - t0
st = env.status()
refused = np.asarray(st.get('refused', st.get('a_refused', [-1] * E))).reshape(-1)
say(f"ticks 101-300 done; total 300-tick horizon REACHED")
print("refused ticks:", refused[:E].tolist())
print("status keys:", list(st)[:8])
say(f"steady-state: {300*E/(dt+0.001):.1f} env-steps/s (last 200 ticks, E={E})")
say("TAKEOVER STEP 2 VERDICT REACHED")
