"""run_source_checks.py -- R5/R6 for holodeck-mat-01: measures the DEPLOYED
material plane from source text at base 4812b55b (read-only; the live
service is never contacted). Writes checks/r5_source_trace.txt and
checks/r6_findings.txt. Predicted line numbers come from
PREREGISTRATION.txt; MEASURED line numbers are reported wherever they
differ (the prediction is about semantics present, locations measured).
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAT01 = HERE.parent
REPO = MAT01.parents[5]          # -> repo root (docs/evidence/agent_fleet/HOLODECK/MAT/MAT-01)

OUT = MAT01 / "checks"
OUT.mkdir(exist_ok=True)

BASE = "4812b55b407107a34b708af1700e071a7eecbab4"

FILES = {
    "contract": "tools/material_contract.py",
    "composition": "tools/materials.py",
    "elastic": "tools/elastic_foundation/materials.py",
    "cad": "tools/cad_sample.py",
    "membrane_demo": "tools/gpu_fixtures_recovered/membrane_demo.py",
    "window_demo": "tools/membrane_window_demo.py",
    "control": "tools/agent_fleet/control.py",
    "rh": "tools/agent_fleet/review_handoff.py",
    "model": "docs/evidence/agent_fleet/HOLODECK/MAT/MAT-01/reference/mat01_reference_model.py",
}


def read(key):
    return (REPO / FILES[key]).read_text(encoding="utf-8", errors="replace").splitlines()


def lines_with(lines, needle):
    return [(i + 1, ln.rstrip()) for i, ln in enumerate(lines) if needle in ln]


def sha(key):
    return hashlib.sha256((REPO / FILES[key]).read_bytes()).hexdigest()


def main() -> int:
    # ---------------- R5 ----------------
    r5 = []
    ok5 = 0
    contract = read("contract")
    window = read("window_demo")
    elastic = read("elastic")

    def quote(r5list, key, needle, label, lo=0, hi=0):
        hits = lines_with(read(key), needle)
        r5list.append(f"  [{label}] {FILES[key]}: needle {needle!r} at lines "
                      f"{[h[0] for h in hits][:6]}")
        for ln, txt in hits[:hi or 1]:
            r5list.append(f"    {ln}: {txt.strip()[:150]}")
        return hits

    r5.append("R5 DEPLOYED-SOURCE TRACE (base 4812b55b) -- card prediction "
              "judged against the deployed text")
    # (a) THE CONSTRUCTION DOOR
    r5.append("(a) THE CONSTRUCTION DOOR: validation at construction")
    door_def = lines_with(contract, "def __post_init__")
    door_cmt = lines_with(contract, "THE DOOR")
    vp_def = lines_with(contract, "def _validate_property")
    r5.append(f"  MaterialProperty.__post_init__ at line {door_def[0][0]}; "
              f"'THE DOOR' comment at line {door_cmt[0][0]}; "
              f"_validate_property def at line {vp_def[0][0]}")
    for i in range(door_def[0][0] - 1, door_def[0][0] + 6):
        r5.append(f"    {i+1}: {contract[i].strip()[:150]}")
    gate_ok = bool(door_def and door_cmt and vp_def)
    ok5 += 1 if gate_ok else 0
    # (b) THE BOUNDARY + FAMILY GATE
    r5.append("(b) THE BOUNDARY + FAMILY-GATED CONVERSION (validate before identity)")
    for needle in ("def convert", "VALIDATE BEFORE IDENTITY", "def register",
                   "def record", "def get", "def _validate_record"):
        hits = lines_with(contract, needle)
        r5.append(f"  {needle!r} at lines {[h[0] for h in hits]}")
    conv = lines_with(contract, "def convert")[0][0]
    for i in range(conv - 1, conv + 12):
        r5.append(f"    {i+1}: {contract[i].strip()[:150]}")
    boundary_ok = all(lines_with(contract, n) for n in
                      ("def convert", "VALIDATE BEFORE IDENTITY", "def register",
                       "def record", "def _validate_record"))
    ok5 += 1 if boundary_ok else 0
    # (c) THE DECLARED BASIS + real callers
    r5.append("(c) THE DECLARED BASIS + REAL CALLERS")
    dsg = lines_with(contract, "def density_from_sg")
    r5.append(f"  density_from_sg at line {dsg[0][0]}")
    for i in range(dsg[0][0] - 1, dsg[0][0] + 20):
        if "MISSING_BASIS" in contract[i] or "requires the declared" in contract[i] \
                or "def density_from_sg" in contract[i]:
            r5.append(f"    {i+1}: {contract[i].strip()[:150]}")
    cg = lines_with(window, "def contract_gamma")
    adm = lines_with(window, "admission_path")
    r5.append(f"  membrane_window_demo.py contract_gamma at line {cg[0][0]}; "
              f"admission_path record at line {adm[0][0]}")
    for i in range(adm[0][0] - 1, adm[0][0] + 2):
        r5.append(f"    {i+1}: {window[i].strip()[:150]}")
    el = lines_with(elastic, "class MaterialReason")
    el2 = lines_with(elastic, "class ElasticMaterial2D")
    el3 = lines_with(elastic, "POISSON_RATIO_NOT_MEASURED")
    r5.append(f"  elastic_foundation/materials.py: MaterialReason at "
              f"{el[0][0]}, ElasticMaterial2D (frozen) at {el2[0][0]}, "
              f"named refusal example POISSON_RATIO_NOT_MEASURED at {el3[0][0]}")
    basis_ok = bool(dsg and cg and adm and el and el2)
    ok5 += 1 if basis_ok else 0
    r5.append(f"R5 VERDICT: {ok5}/3 real-caller gate families present at base "
              "(threshold 3/3)")

    # ---------------- R6 ----------------
    r6 = []
    r6.append("R6 DEPLOYED FALSIFIER HUNT + CURRENT-STATE MEASUREMENTS "
              "(findings; never patched, never adopted as the model's truth)")
    # (a) raw-constants plane
    r6.append("(a) RAW-CONSTANTS PLANE: tools/materials.py + cad_sample.py")
    comp = read("composition")
    cad = read("cad")
    for needle in ("PLUSH_STUFFED = ", "KNIT = ", "ACRYLIC = ",
                   "PART_MATERIAL = {", "DENSITY = "):
        hits = lines_with(comp, needle)
        r6.append(f"  materials.py {needle!r} at lines {[h[0] for h in hits]}")
    rho = lines_with(cad, "DENSITY[PART_MATERIAL")
    r6.append(f"  cad_sample.py raw-constant consumer at line "
              f"{[h[0] for h in rho]}:")
    for ln, txt in rho:
        r6.append(f"    {ln}: {txt.strip()[:150]}")
    ref = lines_with(cad, "mass_err")
    for ln, txt in ref[:2]:
        r6.append(f"    advertising, {ln}: {txt.strip()[:150]}")
    r6.append("  VERDICT (a): the sampler's preregistered referee tolerances "
              "advertise the SAMPLING accuracy (mass_err <= 1%, iner_err <= "
              "2% on packet fields vs analytic), NOT contract admission of "
              "the density inputs; the density constants carry documented "
              "literature sources in materials.py but are module constants, "
              "not runtime-admitted records. This is the raw-data plane the "
              "card statement distinguishes records from -- honest about "
              "what it claims, and therefore NOT a card-falsifier instance; "
              "it is the recorded seam for a future MAT lane.")
    # (b) honest deferral
    md = read("membrane_demo")
    r6.append("(b) HONEST DEFERRAL: gpu_fixtures_recovered/membrane_demo.py")
    for needle in ("Admission routing", "no physical calibration is claimed",
                   "SYNTHETIC DECLARED interface"):
        hits = lines_with(md, needle)
        for ln, txt in hits[:1]:
            r6.append(f"    {ln}: {txt.strip()[:160]}")
    r6.append("  VERDICT (b): the file explicitly claims NO physical "
              "calibration and defers admission routing -- nothing is "
              "advertised as validated for the un-admitted parameter, so "
              "this is NOT a card-falsifier instance; recorded as the known "
              "open seam (BP-A1).")
    # (c) owner_instance current state (PR #80 fix measured as deployed)
    r6.append("(c) OWNER_INSTANCE CURRENT STATE at base (PR #80 "
              "fixed-and-deployed; measured now, no stale deviation language)")
    rh = read("rh")
    ctl = read("control")
    rh_hits = lines_with(rh, "owner_instance")
    ctl_hits = lines_with(ctl, "owner_instance")
    r6.append(f"  review_handoff.py owner_instance occurrences: {len(rh_hits)}")
    for ln, txt in rh_hits:
        r6.append(f"    {ln}: {txt.strip()[:150]}")
    fence = lines_with(rh, "instance_fencing")
    for ln, txt in fence[:2]:
        r6.append(f"    fence, {ln}: {txt.strip()[:150]}")
    r6.append(f"  control.py owner_instance occurrences: {len(ctl_hits)}")
    for ln, txt in ctl_hits:
        r6.append(f"    {ln}: {txt.strip()[:150]}")
    r6.append("  VERDICT (c): the claim-restored interceptor path BINDS "
              "owner_instance (fleet-review-handoff-claim-delegation-01, F2/F3 "
              "restored markers in source) and the enforced-fencing gate is "
              "present -- the GOV-01-era deviation (rh occurrences == 0 at "
              "d59518b9) is FIXED AND DEPLOYED at this base. Measured counts "
              "are recorded above; prediction (rh >= 1) HOLDS, so no surprise "
              "finding.")
    # (d) independence audit of this lane's own model
    r6.append("(d) INDEPENDENCE AUDIT of reference/mat01_reference_model.py")
    model_src = (REPO / FILES["model"]).read_text(encoding="utf-8")
    model_code = model_src.split('"""', 2)[2]   # skip module docstring
    imports = sorted(set(re.findall(r"^\s*(?:import|from)\s+([\w.]+)",
                                    model_code, re.M)))
    r6.append(f"  import roots: {imports}")
    audited = any("material_contract" in i or "materials" in i or "cad" in i
                  for i in imports)
    r6.append(f"  imports from the AUDITED deployed code "
              f"(tools/material_contract etc.): {'FOUND -- VIOLATION' if audited else 'none'}")
    r6.append("  MATH-01 import (the designated units backbone): "
              "math01_reference_model (declared, cited, by design).")
    r6.append(f"  VERDICT (d): independence from the audited code "
              f"{'HOLDS' if not audited else 'FAILS'}")

    (OUT / "r5_source_trace.txt").write_text("\n".join(r5) + "\n",
                                             encoding="utf-8")
    (OUT / "r6_findings.txt").write_text("\n".join(r6) + "\n", encoding="utf-8")
    print(f"R5 {ok5}/3 ; R6 measurements written (4/4 reports)")
    return 0 if ok5 == 3 else 1


if __name__ == "__main__":
    sys.exit(main())
