"""Live thermal scene checks; uses only its intent API and tagged native captures."""
import argparse,base64,hashlib,http.client,json,time
from pathlib import Path

def run(port,outdir):
    outdir.mkdir(parents=True,exist_ok=True)
    observations=[]
    def request(path="/thermal_state",value=None,raw=None):
        c=http.client.HTTPConnection("127.0.0.1",port,timeout=5)
        payload=raw if raw is not None else json.dumps(value) if value is not None else None
        t=time.perf_counter()
        c.request("POST" if payload is not None else "GET",path,body=payload,
                  headers={"Content-Type":"application/json"} if payload is not None else {})
        r=c.getresponse();data=r.read();typ=r.getheader("Content-Type");c.close()
        return (json.loads(data) if "json" in typ else data),(time.perf_counter()-t)*1000
    def state():return request()[0]
    def physical(s):
        return {k:s[k] for k in ("tick","position_m","velocity_m_s","gas","heat_supplied_J",
              "battery_remaining_J","damper_heat_J","dwell_s","won","battery_exhausted")}
    initial,_=request(value={"reset":True})
    paused,_=request(value={"paused":True})
    for raw,code in [ ('{"heater_fraction":true}',"invalid_model_number"),
                      ('{"heater_fraction":2}',"heater_fraction_out_of_range"),
                      ('{"position_m":1}',"unknown_thermal_control"),
                      ('{"heater_fraction":0,"heater_fraction":1}',"duplicate_json_key")]:
        before=physical(state());r,_=request(raw=raw)
        assert r=={"ok":False,"error":code},r
        assert physical(state())==before
        observations.append(code)
    def capture(name):
        f,ms=request("/thermal_frame?w=960")
        assert f["ok"],f
        s=f["state"]
        assert s["scene_revision"]==s["render_revision"]
        assert abs(s["render_chamber_volume_m3"]-s["gas"]["volume_m3"])<=1e-10*s["gas"]["volume_m3"]
        image=base64.b64decode(f["image_base64"]);(outdir/(name+".jpg")).write_bytes(image)
        return {"state":s,"capture_sequence":f["capture_sequence"],"client_ms":ms,
                "image_sha256":hashlib.sha256(image).hexdigest(),
                "timing_ms":f["timing_ms"],"read_phases_us":f["read_phases_us"]}
    cold=capture("live_initial")
    old_image,_=request("/frame?w=960&fmt=jpg&q=88")
    assert isinstance(old_image,bytes) and hashlib.sha256(old_image).hexdigest()==cold["image_sha256"]
    observations.append("legacy_frame_pixels_match")
    # Resume and observe an actual 300 Hz clock while requesting rendered frames.
    request(value={"paused":False})
    start=state();t0=time.perf_counter()
    captures=[capture("clock_"+str(i)) for i in range(8)]
    time.sleep(.3)
    end=state();elapsed=time.perf_counter()-t0
    observed_hz=(end["tick"]-start["tick"])/elapsed
    assert 280<=observed_hz<=320,(observed_hz,elapsed)
    assert end["position_m"]==0 and end["heat_supplied_J"]==0
    observations.append("clock_continues_during_native_captures")
    # The heater's lease must expire without additional browser messages.
    request(value={"reset":True});request(value={"heater_fraction":1})
    time.sleep(.8);lease=state()
    assert lease["heater_fraction"]==0 and .85<=lease["heat_supplied_J"]<=1.10,lease
    observations.append("unrenewed_heater_lease_expires")
    # Drive long enough to spend the cartridge, maintaining only heater intent.
    request(value={"reset":True});deadline=time.perf_counter()+2.4
    trace=[]
    while time.perf_counter()<deadline:
        s,ms=request(value={"heater_fraction":1});trace.append(s)
        time.sleep(.12)
    request(value={"heater_fraction":0});spent=state()
    assert spent["battery_exhausted"] and not spent["won"],spent
    assert spent["heat_supplied_J"]<=4+1e-12 and spent["battery_remaining_J"]==0
    hot=capture("live_charge_spent")
    assert hot["image_sha256"]!=cold["image_sha256"]
    assert hot["state"]["position_m"]>.01
    observations.append("finite_charge_failure_and_native_pixel_change")
    # Restore a fresh, ready-to-play native scene.
    reset,_=request(value={"reset":True})
    for key in ("position_m","velocity_m_s","heat_supplied_J","battery_remaining_J","dwell_s","won"):
        assert reset[key]==initial[key],(key,reset[key],initial[key])
    assert reset["gas"]==initial["gas"]
    observations.append("reset_reproducible")
    max_balance=max(abs(s["energy_balance_J"]) for s in trace)
    assert max_balance<=1e-8+4e-8
    result={"schema":"chimera.thermal_live_validation.v1","status":"pass",
       "observations":observations,"observed_clock_hz_under_capture":observed_hz,
       "clock_elapsed_s":elapsed,"lease_heat_J":lease["heat_supplied_J"],
       "max_driven_energy_residual_J":max_balance,"cold":cold,"hot":hot,
       "capture_ms":[s["client_ms"] for s in captures],
       "scene_sha256":reset["scene_sha256"],"packet_sha256":reset["packet_sha256"],
       "final_state":reset,"scope":"This executable and host; native live intent/control/render/clock checks. Not a commercial RPG qualification."}
    (outdir/"live_qualification.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port",type=int,default=8108);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();r=run(a.port,a.output)
    print(json.dumps({k:r[k] for k in ("status","observations","observed_clock_hz_under_capture","lease_heat_J",
                     "max_driven_energy_residual_J","capture_ms")},indent=2))
if __name__=="__main__":main()
