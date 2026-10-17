"""Independent scalar analytic checks; no call to the triangle force or fitting code.

Numerical verification is distinct from controller/reviewer release authority.
Budgets are frozen in PREREGISTRATION.md before measurements.
"""
from __future__ import annotations
import math
import numpy as np
from .core import Refusal, require

LIMITS={"cpu":2e-11,"gpu":3e-5,"table":5e-4,"assembly_m":2e-4,"recursive_m":5e-4,"residual_n":1e-10}

def analytic(r,h,scale=1.,gamma=1.):
    # Triangle area = half base length * hypotenuse(planar altitude, port height).
    rim=np.asarray(r['rim_xy'],dtype=float)*scale
    edge=np.roll(rim,-1,axis=0)-rim
    lengths=np.sqrt(np.sum(edge*edge,axis=1))
    distance=(rim[:,0]*np.roll(rim,-1,axis=0)[:,1]-rim[:,1]*np.roll(rim,-1,axis=0)[:,0])/lengths
    slant=np.sqrt(distance*distance+h*h)
    return {"energy":float(gamma*np.sum(.5*lengths*slant)),
            "reaction":float(gamma*np.sum(.5*lengths*h/slant))}

def minimum_energy(parts,load,interval):
    # Independent golden-section energy minimization, not production force bisection.
    lo,hi=interval;ratio=(math.sqrt(5)-1)/2
    def potential(q):return sum(analytic(r,q-anchor)['energy'] for r,anchor in parts)-load*q
    for _ in range(90):
        a=hi-ratio*(hi-lo);b=lo+ratio*(hi-lo)
        if potential(a)<potential(b):hi=b
        else:lo=a
    return (lo+hi)/2

def verify_samples(cases, values, mode):
    require(len(cases)==len(values) and len(cases)>0,'missing_cases')
    energy_error=force_error=0.
    for c,v in zip(cases,values):
        ref=analytic(c['recipe'],c['h'],c['scale'],c['gamma'])
        e=abs(v['energy']-ref['energy'])/max(c['gamma']*c['scale']**2,1e-30)
        f=abs(v['reaction']-ref['reaction'])/max(c['gamma']*c['scale'],1e-30)
        if c['gamma']==0:
            require(v['energy']==0 and v['reaction']==0,'zero_gamma_failure');e=f=0.
        require(math.isfinite(e) and math.isfinite(f),'nonfinite_measurement')
        energy_error=max(energy_error,e);force_error=max(force_error,f)
    limit=LIMITS[mode]
    require(energy_error<=limit and force_error<=limit,f'{mode}_reference_mismatch')
    return {'cases':len(cases),'max_energy_error_normalized':energy_error,'max_force_error_normalized':force_error,'limit':limit}

def verify_assembly(parts, load, interval, measured, *, recursive=False):
    reference=minimum_energy(parts,load,interval)
    error=abs(measured['q']-reference)
    balance=sum(analytic(r,measured['q']-anchor)['reaction'] for r,anchor in parts)-load
    require(math.isfinite(error) and error<=LIMITS['recursive_m' if recursive else 'assembly_m'],'assembly_position_mismatch')
    require(abs(measured['residual_n'])<=LIMITS['residual_n'],'assembly_not_converged')
    return {'independent_q_m':reference,'q_error_m':error,'reference_balance_residual_n':balance}
