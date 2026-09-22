"""lead takeover step 1: the opt=False compile experiment + first tick attempt.

Hypothesis (from the continuation lane's measurements + the diag pattern):
the integ kernel's 55+min codegen is LLVM OPTIMIZATION passes exploding on the
huge function; opt=False (which the advance-only diag used, 817s) should bring
the full tick_integ_kernel into the compilable range.
"""
import sys, time
import numpy as np
from numba import cuda

HERE = __import__('pathlib').Path(__file__).parent
sys.path.insert(0, str(HERE))

def say(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

import walker_numba_split as W
say("split module imported")

# re-jit the SAME python functions with optimization disabled
say("integ kernel now opt=False in-module; codegen happens at first call")

from walker_model import load_spec
from walker_nb_split_env import GaitWalkEnv
spec = load_spec(str(HERE.parent.parent / '.tmp' / 'gait-walker' / 'scene.json'))
env = GaitWalkEnv(spec, 2, reflex_level=0, block=32)
q0 = np.tile(spec.defaults, 2)
env.reset(q0=q0, v0=np.zeros(36), touching0=np.zeros(4, np.int32))
say("env ready at E=2")

# warm the plan + post kernels (already fast: 14-16s class)
t0 = time.time()
args = env._args()
grid = env.grid; block = env.block
W.tick_plan_kernel[grid, block](*args)
cuda.synchronize()
say(f"plan kernel first launch+codegen: {time.time()-t0:.1f}s")

t0 = time.time()
W.tick_integ_kernel[grid, block](*args)
say(f"inTEGR opt=False: first launch dispatched at {time.time()-t0:.1f}s -- now synchronizing (codegen+exec) ...")
t0 = time.time()
cuda.synchronize()
dt = time.time() - t0
say(f"integ opt=False READY (codegen+first exec): {dt:.1f}s")

t0 = time.time()
W.tick_post_kernel[grid, block](*args)
cuda.synchronize()
say(f"post kernel first launch: {time.time()-t0:.1f}s")

say("*** FIRST TICK COMPLETE? stepping 300 ticks (the ship horizon) at E=2 ...")
t0 = time.time()
rc = env.step(300)
cuda.synchronize()
dt = time.time() - t0
status = env.status()
print("status after 300:", {k: status[k] for k in list(status)[:6]})
say(f"300 ticks at E=2 took {dt:.1f}s ({300*2/dt:.1f} env-steps/s incl. any recompile)")
say("TAKEOVER STEP 1 VERDICT REACHED")
