import json

p = json.load(open(r"E:\PythonChimera\.tmp\anatomy_compiler\runs\actual_monkey_fit.json", encoding="utf-8"))
print("top-level keys:", sorted(p.keys()))
print()
print("residuals keys:", sorted(p["residuals"].keys()))
print()
print("audit:", p["audit"])
print("flagged:", [k for k in p["residuals"] if k.startswith("aspect_flag")])
tot = 0.0
src = 0.0
flagged = [k.split(".")[1] for k in p["residuals"] if k.startswith("aspect_flag")]
flagged = [b for b in (p["segments"] + p["physiology"]) and []]
for s in p["physiology"]:
    tot += s["mass"]
    src += s.get("mass_src", 0) or 0.0
    tag = " FLAG" if s["body"] in flagged else ""
    print(f"  {s['body']:13s} mass {s['mass']:9.3f} kg  src {s['mass_src']:7.3f}  detS {s['det_scale']:8.3f}{tag}")
print(f"TOTAL fitted {tot:.3f} vs src-effective {src:.3f} kg")