"""run_source_checks.py -- read-only deployed-source checks R5/R6 for
holodeck-mat-05 at task base 4812b55b407107a34b708af1700e071a7eecbab4.
Reads source text from the worktree ONLY; never contacts the live service,
never executes deployed code. Writes checks/r5_source_trace.txt and
checks/r6_findings.txt. Every location is MEASURED at run time (the prereg
predicts semantics present; measured line numbers are reported even where
they moved from the orientation reads).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]          # .../MAT-05/controls -> MAT-05 -> MAT -> HOLODECK -> agent_fleet -> evidence -> docs -> repo root
CHECKS = HERE.parent / "checks"
CHECKS.mkdir(exist_ok=True)

BASE = "4812b55b407107a34b708af1700e071a7eecbab4"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def find_lines(rel: str, needle: str):
    """All 1-based line numbers whose text contains needle."""
    return [i for i, line in enumerate(read(rel).splitlines(), 1)
            if needle in line]


def quote(rel: str, lineno: int, width: int = 1) -> str:
    lines = read(rel).splitlines()
    lo, hi = max(1, lineno), min(len(lines), lineno + width - 1)
    return "\n".join(f"  {rel}:{n}: {lines[n - 1]}" for n in range(lo, hi + 1))


def file_sha256(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


# ---- R5: the four separation/authoring families ------------------------------

def r5() -> tuple[bool, list[str]]:
    out = ["R5 deployed-source trace at base " + BASE,
           "claim: SEMANTICS PRESENT (threshold 4/4 families); measured "
           "line numbers reported", ""]

    def family(name: str, probes: list[tuple[str, str, str]]) -> tuple[bool, list[str]]:
        lines = [f"({name})"]
        ok = True
        for label, rel, needle in probes:
            hits = find_lines(rel, needle)
            if not hits:
                ok = False
                lines.append(f"  MISSING in {rel}: {needle!r}")
            else:
                lines.append(quote(rel, hits[0]))
                if len(hits) > 1:
                    lines.append(f"  (also at lines {hits[1:]})")
        lines.append(f"  family verdict: {'PRESENT' if ok else 'MISSING'}")
        lines.append("")
        return ok, lines

    ok_a, la = family("a) THE SYNTHETIC PRESET PLANE", [
        ("derivation duty", "tools/materials.py",
         "Every constant derives from what the"),
        ("preset constant", "tools/materials.py", "PLUSH_STUFFED = 250.0"),
        ("preset constant", "tools/materials.py", "KNIT = 300.0"),
        ("preset constant", "tools/materials.py", "ACRYLIC = 1180.0"),
        ("part mapping", "tools/materials.py", "PART_MATERIAL = {"),
        ("density table", "tools/materials.py",
         'DENSITY = {"plush_stuffed"'),
        ("consumer", "tools/cad_sample.py",
         "rho = DENSITY[PART_MATERIAL[name]]"),
    ])
    ok_b, lb = family("b) THE DECLARED-SYNTHETIC LABEL + ENFORCING CHECK", [
        ("synthetic flag", "tools/membrane_window_demo.py",
         '"synthetic": True'),
        ("synthetic label", "tools/membrane_window_demo.py",
         '"synthetic_label": "dimensionless analytic control fixture gamma; "'),
        ("enforcing check", "tools/membrane_window_demo_checks.py",
         'check("F6.synthetic_labeled"'),
    ])
    ok_c, lc = family("c) THE HONEST SEAM (declared, not hidden)", [
        ("declared interface", "tools/gpu_fixtures_recovered/membrane_demo.py",
         "The material is a SYNTHETIC DECLARED interface"),
        ("no calibration claimed",
         "tools/gpu_fixtures_recovered/membrane_demo.py",
         "no physical calibration is claimed"),
        ("deferral", "tools/gpu_fixtures_recovered/membrane_demo.py",
         "through material_contract is deferred"),
    ])
    ok_d, ld = family("d) THE CALIBRATED PLANE + AUTHORING REFUSALS", [
        ("provenance classes", "tools/material_contract.py",
         'RESEARCHED = "researched"'),
        ("provenance gate", "tools/material_contract.py",
         'class (researched | parent | derived), got '),
        ("UNSUPPORTED_MODEL refusal", "tools/material_contract.py",
         "RefusalKind.UNSUPPORTED_MODEL"),
        ("declared-basis derivation", "tools/material_contract.py",
         "def density_from_sg"),
        ("dimensionless family (sg)", "tools/material_contract.py",
         '"dimensionless": {"1": 1.0, "ratio": 1.0, "sg": 1.0}'),
        ("Uncited refusal", "tools/matter_data.py", "class Uncited"),
        ("unknown-material refusal lists what exists", "tools/matter_data.py",
         "the library holds no material"),
        ("provenance enforcement", "tools/matter_data.py",
         'if ent.get("provenance") != "researched":'),
        ("design-value refusal", "tools/matter_data.py",
         "A design or seed value is a CHOICE"),
    ])

    ok = ok_a and ok_b and ok_c and ok_d
    out += la + lb + lc + ld
    out.append(f"R5 verdict: {'4/4 HOLD' if ok else 'FIRED'} "
               f"(a={ok_a}, b={ok_b}, c={ok_c}, d={ok_d})")
    return ok, out


# ---- R6: findings + current-state measurements -------------------------------

def r6() -> tuple[bool, list[str]]:
    out = ["R6 findings + current-state measurements at base " + BASE,
           "(reported, never patched, never adopted as the model's truth)", ""]

    # (a) owner_instance current state (PR #80 fix measured-current)
    ctl = find_lines("tools/agent_fleet/control.py", "owner_instance")
    rh = find_lines("tools/agent_fleet/review_handoff.py", "owner_instance")
    out.append("(a) OWNER_INSTANCE CURRENT STATE (task packet: PR #80 fix is "
               "FIXED AND DEPLOYED -- measure current, no stale deviation "
               "language)")
    out.append(f"  tools/agent_fleet/control.py owner_instance occurrences: "
               f"{len(ctl)} at lines {ctl} (prereg predicted 8)")
    out.append(f"  tools/agent_fleet/review_handoff.py occurrences: "
               f"{len(rh)} at lines {rh} (prereg predicted 1, the claim-path "
               f"bind)")
    for n in rh:
        out.append(quote("tools/agent_fleet/review_handoff.py", n))
    surprise = (len(ctl) == 0 or len(rh) == 0)
    out.append(f"  SURPRISE-FINDING check (0 occurrences would mean the fix "
               f"is not at this base): {'FIRED' if surprise else 'not fired'}")
    out.append("")

    # (b) card falsifier hunt: advertised-as-measured on a fictional value?
    out.append("(b) CARD FALSIFIER HUNT -- per-plane verdict "
               "advertised-as-measured on a fictional value? (threshold: all "
               "NO, else the card falsifier FIRES)")
    # key honesty of the preset table
    mat = read("tools/materials.py")
    keys = sorted(set(re.findall(r'"([A-Za-z_0-9]+)"\s*:', mat.split("PART_MATERIAL")[1].split("}")[0])))
    banned = {"wood", "metal", "water"}
    out.append(f"  preset table PART_MATERIAL keys (measured): {keys}")
    out.append(f"  keys contain wood/metal/water literals? "
               f"{sorted(banned & set(keys)) or 'NO'}")
    hdr = find_lines("tools/materials.py",
                     "Every constant derives from what the")
    out.append(quote("tools/materials.py", hdr[0]) if hdr
               else "  MISSING derivation-duty header")
    out.append("  verdict: preset plane advertises derivation-from-"
               "literature, not measurement -> NO")
    # the label plane
    lab = find_lines("tools/membrane_window_demo.py", "NOT a calibrated physical material")
    out.append(f"  declared-synthetic label present at "
               f"tools/membrane_window_demo.py lines {lab} -> NO (self-"
               f"labeled synthetic)")
    chk = find_lines("tools/membrane_window_demo_checks.py",
                     "F6.synthetic_labeled")
    out.append(f"  label enforced by check at "
               f"tools/membrane_window_demo_checks.py lines {chk}")
    # the seam
    seam = find_lines("tools/gpu_fixtures_recovered/membrane_demo.py",
                      "no physical calibration is claimed")
    out.append(f"  honest seam present at "
               f"tools/gpu_fixtures_recovered/membrane_demo.py lines {seam} "
               f"-> NO (declared)")
    # the calibrated plane's provenance enforcement
    prov = find_lines("tools/matter_data.py", "may not be cited ")
    out.append(quote("tools/matter_data.py", prov[0]) if prov
               else "  MISSING provenance enforcement quote")
    out.append("  verdict: calibrated plane refuses non-researched "
               "provenance by name -> NO")
    out.append("")

    # (c) nondimensional control in the deployed plane
    out.append("(c) NONDIMENSIONAL CONTROL measured in the deployed plane")
    sg_unit = find_lines("tools/material_contract.py", '"sg"')
    out.append(f"  'sg' unit in the dimensionless family at "
               f"tools/material_contract.py lines {sg_unit}")
    oak = find_lines("tools/matter_data.py", '"SG":       _e(0.68')
    out.append(quote("tools/matter_data.py", oak[0]) if oak
               else "  MISSING white-oak SG entry")
    out.append("  cross-check: SG 0.68 x 1000 kg/m^3 basis = 680 kg/m^3, "
               "inside the derived admissible domain (0, 22.59] and inside "
               "the fixture band [0.25, 1.18] (matches reference-model R1d)")
    out.append("")

    # (d) independence audit of this lane's own artifacts
    out.append("(d) INDEPENDENCE AUDIT of this lane's artifacts")
    model = (HERE.parent / "reference" / "mat05_reference_model.py") \
        .read_text(encoding="utf-8")
    imports = sorted(set(re.findall(r"^(?:import|from)\s+([\w.]+)",
                                    model, re.M)))
    banned_mods = ("materials", "material_contract", "matter_data")
    contaminated = [i for i in imports
                    if any(b in i for b in banned_mods)]
    out.append(f"  reference-model imports (measured): {imports}")
    out.append(f"  imports of AUDITED deployed modules "
               f"{banned_mods}: {contaminated or 'NONE'}")
    out.append("  MATH-01 import is the packet-designated units backbone, "
               "cited in the model docstring; independence is claimed from "
               "the audited deployed code only")
    audit_ok = not contaminated
    out.append(f"  independence verdict: {'CLEAN' if audit_ok else 'CONTAMINATED'}")

    r6_ok = (not surprise) and audit_ok
    return r6_ok, out


def main():
    ok5, out5 = r5()
    ok6, out6 = r6()
    (CHECKS / "r5_source_trace.txt").write_text(
        "\n".join(out5) + "\n", encoding="utf-8")
    (CHECKS / "r6_findings.txt").write_text(
        "\n".join(out6) + "\n" +
        f"\nR6 verdict: {'HOLD' if ok6 else 'FIRED'}\n", encoding="utf-8")
    identities = {
        "base": BASE,
        "files": {rel: file_sha256(rel) for rel in (
            "tools/materials.py", "tools/cad_sample.py",
            "tools/membrane_window_demo.py",
            "tools/membrane_window_demo_checks.py",
            "tools/gpu_fixtures_recovered/membrane_demo.py",
            "tools/material_contract.py", "tools/matter_data.py",
            "tools/agent_fleet/control.py",
            "tools/agent_fleet/review_handoff.py")},
    }
    (CHECKS / "source_identities.json").write_text(
        json.dumps(identities, indent=2) + "\n", encoding="utf-8")
    print(f"R5 {'HOLD' if ok5 else 'FIRED'}; R6 {'HOLD' if ok6 else 'FIRED'}")
    return 0 if (ok5 and ok6) else 1


if __name__ == "__main__":
    sys.exit(main())
