"""Preregistered A1-A5 native thermal-work checks, with independent ODE reference."""
import argparse, copy, hashlib, json, math, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from tools.science_funnel.common import canonical,loads

def execute(exe,scene,commands):
    p=subprocess.run([str(exe),str(scene)],input="\n".join(json.dumps(q) for q in commands)+"\n",
                     text=True,capture_output=True,timeout=90)
    assert p.returncode==0,p.stderr
    out=[json.loads(s) for s in p.stdout.splitlines()]
    assert len(out)==len(commands),(len(out),len(commands))
    return out

def run(exe,path,ct,np,scipy):
    from scipy.integrate import solve_ivp
    bundle=loads(path.read_bytes());scene=bundle["scene"];packet=bundle["models"]
    commands=[{"steps":450,"heater":1,"sample_every":30},
              {"steps":450,"heater":0,"sample_every":30}]
    out=execute(exe,path,commands)
    assert all(o["ok"] for o in out),[o for o in out if not o["ok"]]
    samples=[s for o in out for s in o["samples"]]
    state=out[-1]["state"];d=state["derived"];geom=scene["geometry"]
    native_max_balance=max(abs(s["energy_balance_J"]) for s in samples)
    assert all(abs(s["energy_balance_J"])<=1e-8+1e-8*max(1,s["heat_supplied_J"]) for s in samples)
    n=d["n_mol"];m=geom["moving_mass_kg"];A=geom["piston_area_m2"];V0=geom["volume0_m3"]
    assert all(s["gas"]["n_mol"]==n for s in samples)
    k=d["spring_k_N_m"];c=d["damper_N_s_m"];g=d["gravity_m_s2"]
    reference=ct.Solution(str(ROOT/"tools/science_funnel/data/force_sources/cantera_gri30.yaml"))
    therm=next(s.thermo for s in reference.species() if s.name=="N2")
    R=ct.gas_constant/1000
    def rhs(power):
        def f(t,y):
            x,v,T,loss=y
            p=n*R*T/(V0+A*x)
            cv=therm.cp(T)/1000-R
            return [v,(p*A-m*g-k*x-c*v)/m,(power-p*A*v)/(n*cv),c*v*v]
        return f
    y0=[0,0,scene["initial"]["gas_temperature_K"],0]
    one=solve_ivp(rhs(2),(0,1.5),y0,method="DOP853",rtol=1e-11,atol=1e-12,dense_output=True)
    two=solve_ivp(rhs(0),(1.5,3),one.y[:,-1],method="DOP853",rtol=1e-11,atol=1e-12,dense_output=True)
    assert one.success and two.success
    errors={"position_m":0,"velocity_m_s":0,"temperature_K":0}
    for s in samples:
        t=s["sim_time_s"];ref=(one if t<=1.5 else two).sol(t)
        for key,a,b in (("position_m",s["position_m"],ref[0]),("velocity_m_s",s["velocity_m_s"],ref[1]),
                        ("temperature_K",s["gas"]["temperature_K"],ref[2])):
            errors[key]=max(errors[key],abs(a-b))
    assert errors["position_m"]<=20e-6,errors
    assert errors["velocity_m_s"]<=.0002,errors
    assert errors["temperature_K"]<=.05,errors
    # No drive, invalid drive, restore, exhaustion, and measured goal.
    controls=execute(exe,path,[{"steps":0},{"steps":3000,"heater":0,"sample_every":300},
        {"steps":1,"heater":-1},{"steps":1,"heater":2},{"reset":True},
        {"steps":900,"heater":1,"sample_every":30}])
    assert controls[0]["ok"] and controls[1]["ok"],controls
    assert abs(controls[1]["state"]["position_m"])<=1e-9
    assert all(not q["ok"] and q["failed_step_unchanged"] for q in controls[2:4])
    assert controls[0]["state"]==controls[4]["state"]
    exhausted=controls[-1];assert exhausted["ok"],exhausted
    assert exhausted["state"]["battery_exhausted"] and not exhausted["state"]["won"]
    assert max(s["heat_supplied_J"] for s in exhausted["samples"])<=scene["controls"]["battery_J"]+1e-12
    # A fixed, declared demonstration input sequence, not an automatic pose/goal.
    win=execute(exe,path,[{"steps":450,"heater":1,"sample_every":1},
                          {"steps":750,"heater":0,"sample_every":1}])
    assert all(q["ok"] for q in win),win
    history=win[0]["samples"]+win[1]["samples"]
    won=[i for i,s in enumerate(history) if s["won"]]
    assert won,"Declared 3 J sequence did not satisfy measured goal"
    first=won[0];goal=scene["goal"]
    assert first>=299
    for s in history[first-299:first+1]:
        assert goal["position_min_m"]<=s["position_m"]<=goal["position_max_m"]
        assert abs(s["velocity_m_s"])<=goal["max_speed_m_s"]
    assert history[first-1]["won"] is False
    # Chunking is an observer choice, not an integration timestep.
    batched=execute(exe,path,[{"steps":150,"heater":1},{"steps":300,"heater":1},{"steps":450,"heater":0}])
    assert batched[-1]["state"]==out[-1]["state"]
    # Domain refusal preserves the last successful tick.
    restrictive=copy.deepcopy(bundle)
    restrictive["scene"]["operating_envelope"]["gas_temperature_max_K"]=321
    with tempfile.TemporaryDirectory(prefix="thermal-domain-test-") as temp:
        p=Path(temp)/"scene.json";p.write_bytes(canonical(restrictive))
        domain=execute(exe,p,[{"steps":10,"heater":1}])[0]
    assert not domain["ok"] and domain["failed_step_unchanged"],domain
    assert domain["error"]=="actuator_temperature_out_of_regime"
    timing={name:max(o["timing_ms"][name] for o in out) for name in ("median","p95","p99")}
    assert timing["p95"]<=1000/300,timing
    return {"schema":"chimera.thermal_salvage_validation.v1","status":"pass",
       "preregistered":["A1","A2","A3","A4","A5","A6.render_batching_only"],
       "max_energy_balance_J":native_max_balance,"native_vs_ODE_max_errors":errors,
       "native_step_ms_max_across_driven_and_coast":timing,
       "max_solver_evaluations":max(s["solver_evaluations"] for s in samples),
       "zero_heat_displacement_m":controls[1]["state"]["position_m"],
       "winning_sequence":{"heater_W":2,"on_seconds":1.5,"off_seconds":2.5,
                           "first_won_tick":history[first]["tick"],"final":win[-1]["state"]},
       "exhaustion_final":exhausted["state"],"domain_refusal":domain["error"],
       "reference":{"Cantera":ct.__version__,"numpy":np.__version__,"scipy":scipy.__version__,
                    "method":"DOP853","rtol":1e-11,"atol":1e-12,
                    "equations":"dx=v; m*dv=p*A-m*g-k*x-c*v; n*Cv*dT=power-p*A*v; dLoss=c*v*v"},
       "exe_sha256":hashlib.sha256(exe.read_bytes()).hexdigest(),
       "scene_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
       "packet_sha256":packet["packet_sha256"],
       "scope":"Native coupled-work and game-rule qualification only. Live clock and visible geometry still pending."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--exe",type=Path,required=True);p.add_argument("--scene",type=Path,required=True)
    p.add_argument("--reference-path",type=Path,required=True);p.add_argument("--receipt",type=Path,required=True)
    args=p.parse_args();sys.path.insert(0,str(args.reference_path.resolve()))
    import cantera as ct,numpy as np,scipy
    assert ct.__version__=="3.1.0"
    result=run(args.exe.resolve(),args.scene.resolve(),ct,np,scipy)
    args.receipt.parent.mkdir(parents=True,exist_ok=True);args.receipt.write_bytes(canonical(result))
    print(json.dumps({k:v for k,v in result.items() if k not in ("winning_sequence","exhaustion_final")},indent=2))
if __name__=="__main__":main()
