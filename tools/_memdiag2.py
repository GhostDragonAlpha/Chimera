import sys, time
sys.path.insert(0, r"E:\PythonChimera"); sys.path.insert(0, r"E:\PythonChimera\tools")
os_env = __import__("os").environ.setdefault("NUMBA_NUM_THREADS","24")
import numpy as np
from numba import njit, prange
from ca_triangle import build_lattice, _rss_mb, _dev_mb, _k1_state, _k2_forces, area_grads, NEAR_ZERO_A0
from LightEngine.bh_draw import build_octree
from LightEngine.modifier import compute_forces_mod
import LightEngine.constants as C

Vg,Tg,A0,S,e_med,no,nm = build_lattice()
nV,nT3=len(Vg),len(Tg)
k=C.K_BOND/C.R_BOND**2
degen=A0<NEAR_ZERO_A0; keep=~degen
Tc=np.ascontiguousarray(Tg[keep]); Ac=np.ascontiguousarray(A0[keep],dtype=np.float64)
G,fd=area_grads(Vg,Tc)
nV=len(Vg)
Tg_flat=np.ascontiguousarray(Tc.ravel()); cnt=np.bincount(Tg_flat,minlength=nV)
start=np.empty(nV+1,dtype=np.int64); start[0]=0; np.cumsum(cnt,out=start[1:])
entries=np.empty(3*len(Tc),dtype=np.int64); cursor=start[:-1].copy()
for r in range(Tg_flat.shape[0]):
    v=int(Tg_flat[r]); entries[int(cursor[v])]=r; cursor[v]+=1

pos32=np.ascontiguousarray(Vg,dtype=np.float32); vel32=np.zeros((nV,3),np.float32)
out_buf=np.empty((nV,3),np.float32); dev={}
from numba import cuda as _c; print("cuda",bool(_c.is_available()),flush=True)
N=150
for tick in range(N):
    tree=build_octree(pos32,leaf_size=16)
    acc,power=compute_forces_mod(pos32,vel32,tree=tree,out=out_buf,dev=dev)
    P64=np.ascontiguousarray(pos32,dtype=np.float64)
    sarr,uarr=_k1_state(P64,Tc,Ac,k)
    f_ca=_k2_forces(sarr,G,k,start,entries)
    a_tot=np.asarray(acc,dtype=np.float64)+f_ca
    vel32+=(a_tot*C.DT).astype(np.float32)
    pos32=np.ascontiguousarray(pos32+vel32.astype(np.float64)*C.DT,dtype=np.float32)
    if tick<5 or tick%10==0:
        print(f"tick {tick:3d}: n_cells={tree['n_cells']} rss_gb={_rss_mb()/1000:.3f} dev_mb={_dev_mb():.1f}",flush=True)
print("done",flush=True)
