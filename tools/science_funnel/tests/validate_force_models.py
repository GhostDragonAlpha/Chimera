"""Independent, required native model qualification (no silent missing-tool skip)."""
import argparse
import copy
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.science_funnel.common import canonical, loads
from tools.science_funnel.force_models import compile_packet

class Validation:
    def __init__(self, exe, packet):
        self.exe, self.packet = exe, packet
        self.checks, self.maxima = [], {}
    def query(self, queries, raw=False):
        text = "\n".join(q if raw else json.dumps(q, allow_nan=False) for q in queries)+"\n"
        p = subprocess.run([str(self.exe), str(self.packet)], input=text, text=True,
                           capture_output=True, timeout=90)
        assert p.returncode == 0, p.stderr
        result = [json.loads(line) for line in p.stdout.splitlines()]
        assert len(result)==len(queries), (len(result),len(queries))
        return result
    def ok(self, queries):
        out = self.query(queries)
        assert all(q["ok"] for q in out), [q for q in out if not q["ok"]][:5]
        return [q["result"] for q in out]
    def close(self, name, actual, expected, absolute, relative):
        error=abs(actual-expected)
        self.maxima[name]=max(self.maxima.get(name,0),error/max(1e-300,abs(expected)))
        assert error <= absolute+relative*abs(expected), (name,actual,expected,error)
        self.checks.append(name)
    def refuse(self, query, code):
        out=self.query([query])[0]
        assert not out["ok"] and out["error"]==code, out
        self.checks.append("refusal:"+code)

def run(exe, packet_path, ct):
    packet=loads(packet_path.read_bytes())
    v=Validation(exe,packet_path)
    source=ROOT/"tools/science_funnel/data/force_sources/cantera_gri30.yaml"
    reference=ct.Solution(str(source))
    assert ct.__version__=="3.1.0", ct.__version__
    species={s.name:s for s in reference.species()}
    assert len(packet["gas_species"])==53
    requests, expected=[], []
    for name,d in packet["gas_species"].items():
        lo,mid,hi=d["temperature_ranges_K"]
        for T in (lo,lo+10,(lo+mid)/2,mid-1e-4,mid,mid+1e-4,(mid+hi)/2,hi-10,hi):
            ref=species[name].thermo
            h,s,cp=ref.h(T)/1000,ref.s(T)/1000,ref.cp(T)/1000
            requests.append({"op":"species","species":name,"T":T})
            expected.append({"h":h,"s":s,"cp":cp,"u":h-ct.gas_constant*T/1000,
                             "cv":cp-ct.gas_constant/1000})
    for actual,ref in zip(v.ok(requests),expected):
        for k in ref:
            v.close("M1."+k,actual[k],ref[k],1e-5 if k in ("h","u") else 1e-7,2e-11)
    derivatives=[]
    for name,d in packet["gas_species"].items():
        lo,mid,hi=d["temperature_ranges_K"]
        for T in ((lo+mid)/2,(mid+hi)/2):
            derivatives += [{"op":"species","species":name,"T":T+x} for x in (-.001,0,.001)]
    data=v.ok(derivatives)
    for i in range(0,len(data),3):
        a,b,c=data[i:i+3]
        v.close("M2.dh_dT",(c["h"]-a["h"])/.002,b["cp"],0,1e-6)
        v.close("M2.du_dT",(c["u"]-a["u"])/.002,b["cv"],0,1e-6)

    # Independent mole-basis mixture thermodynamics, including formation offsets.
    mixtures=[
        ({"N2":.2},320,.004),({"CO2":.4,"H2O":.3,"O2":.1},800,.02),
        ({"H2":.25,"O2":.125,"AR":.6},1800,.03),
        ({"N2":1e-12,"CO2":3e-12},550,1e-12),
        ({"N2":1.0,"O2":1e-14},450,.003)]
    states=v.ok([{"op":"mixture","n":n,"T":t,"V":vol} for n,t,vol in mixtures])
    for (n,T,V),state in zip(mixtures,states):
        total=sum(n.values()); p=total*ct.gas_constant/1000*T/V
        reference.TPX=T,p,n
        for key,ref in (("internal_energy_J",reference.int_energy_mole/1000*total),
                        ("enthalpy_J",reference.enthalpy_mole/1000*total),
                        ("entropy_J_K",reference.entropy_mole/1000*total)):
            v.close("M3.cantera."+key,state[key],ref,1e-9,2e-11)
        recovered=v.ok([{"op":"energy","n":n,"U":state["internal_energy_J"],"V":V}])[0]
        v.close("M3.invert_T",recovered["temperature_K"],T,1e-6,0)
        v.close("M3.energy",recovered["internal_energy_J"],state["internal_energy_J"],1e-10,1e-10)
        entropy=v.ok([{"op":"entropy","n":n,"S":state["entropy_J_K"],"V":V}])[0]
        v.close("M3.entropy_invert_T",entropy["temperature_K"],T,1e-6,0)

    n1,n2={"N2":.1},{"CO2":.2}
    initial=v.ok([{"op":"mixture","n":n1,"T":400,"V":.001},
                  {"op":"mixture","n":n2,"T":700,"V":.003}])
    target=sum(s["internal_energy_J"] for s in initial)
    mixed=v.ok([{"op":"energy","n":{"N2":.1,"CO2":.2},"U":target,"V":.004}])[0]
    v.close("M3.mixing_energy",mixed["internal_energy_J"],target,1e-10,1e-10)
    assert 400 < mixed["temperature_K"] < 700
    assert mixed["entropy_J_K"]>=sum(s["entropy_J_K"] for s in initial)
    v.checks.append("M3.mixing_entropy")
    v.refuse({"op":"energy","n":{"N2":1},"U":1e9,"V":1},"gas_energy_out_of_range_or_fit_gap")
    v.refuse({"op":"mixture","n":{"N2":-1},"T":400,"V":1},"negative_gas_inventory")
    v.refuse({"op":"mixture","n":{"N2":0},"T":400,"V":1},"empty_gas_inventory")
    v.refuse({"op":"species","species":"N2","T":299},"gas_temperature_out_of_range")
    v.refuse({"op":"mixture","n":{"N2":True},"T":400,"V":1},"invalid_model_number")

    # Exercise discontinuous source fits, without silently rebiasing their energy.
    atmid=v.ok([{"op":"species","species":"N2","T":1000}])[0]["u"]
    for delta, target_offset, expected_code in (
            (100,400,"gas_energy_out_of_range_or_fit_gap"),
            (-100,-400,"gas_fit_inverse_ambiguous")):
        mutant=copy.deepcopy(packet)
        mutant["gas_species"]["N2"]["coefficients"][1][5]+=delta
        out=v.query([{"op":"reload","packet":mutant},
                     {"op":"energy","n":{"N2":1},"U":atmid+target_offset,"V":1}])
        assert out[0]["ok"] and not out[1]["ok"] and out[1]["error"]==expected_code,out
        v.checks.append("M3."+expected_code)
    earth=v.ok([{"op":"gravity","body":"399","r":[r,0,0],"mass":2.5}
                for r in (7e6-10,7e6,7e6+10)])
    gradient=-(earth[2]["potential_energy_J"]-earth[0]["potential_energy_J"])/20
    v.close("M4.gradient",gradient,earth[1]["force_N"][0],0,1e-7)
    assert earth[1]["mass_scope"]=="body"
    assert v.ok([{"op":"gravity","body":"5","r":[1e8,0,0],"mass":1}])[0]["mass_scope"]=="planetary_system"
    v.checks.append("M4.body_system_identity")
    v.refuse({"op":"gravity","body":"399","r":[0,0,0],"mass":1},"gravity_center_singularity")
    v.refuse({"op":"gravity","body":"399","r":[1,0,0],"mass":-1},"negative_test_mass")
    for name,d in packet["solid_curves"].items():
        lo,hi=d["temperature_range_K"]
        temperatures=sorted({lo,hi,(lo+hi)/2,18.0-1e-7,18.,18.+1e-7})
        for T in temperatures:
            with localcontext() as ctx:
                ctx.prec=65
                t=Decimal(str(T));model=d["model"]
                if model=="polynomial_low_constant" and T<d["low_temperature_K"]:
                    ref=Decimal(str(d["low_constant"]))
                else:
                    x=t.log10() if model=="log10_polynomial" else t
                    ref=sum(Decimal(str(a))*x**i for i,a in enumerate(d["coefficients"]))
                    if model=="log10_polynomial": ref=Decimal(10)**ref
                ref *= Decimal(str(d["output_scale_to_SI"]))
            actual=v.ok([{"op":"solid","quantity":name,"T":T}])[0]
            v.close("M5."+name,actual["value_si"],float(ref),0,1e-8)
            assert actual["curve_fit_error_percent"]==d["curve_fit_relative_error_percent"]
        for T in (lo-.01,hi+.01):
            v.refuse({"op":"solid","quantity":name,"T":T},"solid_temperature_out_of_range")
    isotope="6:8";half=packet["nuclides"][isotope]["half_life"]["seconds"]
    decay=v.ok([{"op":"decay","isotope":isotope,"dt":dt} for dt in (0,half,.3*half,.7*half)])
    v.close("M6.half_life",decay[1]["remaining_fraction"],.5,1e-12,0)
    v.close("M6.semigroup",decay[2]["remaining_fraction"]*decay[3]["remaining_fraction"],.5,1e-12,0)
    for d in decay:
        v.close("M6.parent_counter",d["remaining_fraction"]+d["decayed_fraction"],1,1e-12,0)
        assert d["deposited_heat_J"] is None
    stable=v.ok([{"op":"decay","isotope":"8:8","dt":1e30}])[0]
    assert stable["remaining_fraction"]==1 and stable["decayed_fraction"]==0
    v.checks.append("M6.stable")
    for kind in ("unknown","bound","approximate"):
        mutant=copy.deepcopy(packet)
        mutant["nuclides"][isotope]["half_life"]["kind"]=kind
        out=v.query([{"op":"reload","packet":mutant},{"op":"decay","isotope":isotope,"dt":1}])
        assert not out[1]["ok"] and out[1]["error"]=="decay_half_life_not_scalar",out
        v.checks.append("M6.refuse_"+kind)
    mutant=copy.deepcopy(packet)
    mutant["nuclides"][isotope]["level"]["resolved_ground_state"]=False
    out=v.query([{"op":"reload","packet":mutant},{"op":"decay","isotope":isotope,"dt":1}])
    assert not out[1]["ok"] and out[1]["error"]=="decay_level_unresolved",out
    v.checks.append("M6.refuse_unresolved")
    bind=v.ok([{"op":"binding","isotope":isotope}])[0]
    e=packet["constants"]["elementary charge"]["value_si"]
    v.close("M6.binding",bind["total_binding_J"],
            packet["nuclides"][isotope]["binding_energy_per_nucleon_keV"]*1000*e*14,0,1e-14)
    assert bind["available_heat_J"] is None
    # Invalid reload cannot partially mutate the previously valid library.
    mutant=copy.deepcopy(packet)
    mutant["R_J_per_mol_K"]*=2
    out=v.query([{"op":"species","species":"N2","T":320},
                 {"op":"reload","packet":mutant},
                 {"op":"species","species":"N2","T":320}])
    assert out[0]==out[2] and not out[1]["ok"] and out[1]["error"]=="derived_gas_constant_mismatch"
    v.checks.append("native_reload_atomicity")
    duplicate=v.query(['{"op":"species","species":"N2","T":320,"T":999}'],raw=True)[0]
    assert not duplicate["ok"] and duplicate["error"]=="duplicate_json_key"
    v.checks.append("native_duplicate_key")
    return {"status":"pass","checks":len(v.checks),"check_categories":sorted(set(v.checks)),
            "max_relative_errors":v.maxima,"reference":{"Cantera":ct.__version__,
            "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "basis":"Molar SI; mixture/species thermodynamics independent Cantera evaluator",
            "solid_reference":"65-decimal direct power sums and log10"},
            "native_exe_sha256":hashlib.sha256(exe.read_bytes()).hexdigest(),
            "packet_sha256":packet["packet_sha256"],
            "scope":"Numerical implementation qualification; not experimental fit accuracy or dynamic gameplay acceptance."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--exe",type=Path,required=True)
    p.add_argument("--packet",type=Path,required=True)
    p.add_argument("--reference-path",type=Path)
    p.add_argument("--receipt",type=Path,required=True)
    args=p.parse_args()
    if args.reference_path: sys.path.insert(0,str(args.reference_path.resolve()))
    import cantera as ct
    result=run(args.exe.resolve(),args.packet.resolve(),ct)
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_bytes(canonical(result))
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
