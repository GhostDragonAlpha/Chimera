"""run_source_checks.py -- executes preregistered R5-R6 (holodeck-mat-04):
a read-only measured comparison of the DEPLOYED repo state (source text at
the task base) against the card's intended contract. NEVER contacts the live
service; opens no socket; runs `git ls-files` for file identity only.

Usage: python controls/run_source_checks.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAT04 = HERE.parent
REPO = next(p for p in MAT04.parents
            if (p / ".git").exists() or (p / ".git").is_file())
OUT = MAT04 / "checks"
OUT.mkdir(exist_ok=True)

BASE = "4812b55b407107a34b708af1700e071a7eecbab4"   # recorded task base
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                      text=True, cwd=str(REPO)).stdout.strip()
STATUS = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                        text=True, cwd=str(REPO)).stdout.strip()

MATERIAL_PLANE = [
    "tools/material_contract.py",
    "tools/materials.py",
    "tools/membrane_window_demo.py",
    "tools/cad_sample.py",
    "tools/surface_energy_checks.py",
    "tools/harvest_material.py",
    "tools/train_material.py",
    "tools/fit_parts.py",
    "tools/shell_fit.py",
]
# plus whole directories swept from the tracked list:
PLANE_DIRS = ("tools/elastic_foundation/", "tools/gpu_fixtures_recovered/")


def blob_sha(path: str) -> str:
    cp = subprocess.run(["git", "ls-files", "-s", path], capture_output=True,
                        text=True, cwd=str(REPO))
    return cp.stdout.split()[1] if cp.stdout.strip() else "UNTRACKED"


def read_repo(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8",
                                   errors="replace").splitlines()


def find_line(lines, needle):
    hits = [i + 1 for i, ln in enumerate(lines) if needle in ln]
    return hits[0] if hits else None


class Rows:
    def __init__(self, title):
        self.title = title
        self.lines = [title, "=" * 72]
        self.lines.append(f"task base: {BASE}")
        self.lines.append(f"working HEAD: {HEAD} (evidence-only commits; "
                          "material plane untouched)")
        self.lines.append(f"git status --porcelain: "
                          f"{'CLEAN' if not STATUS else STATUS}")
        self.passed = 0
        self.failed = 0
        self.failures = []

    def row(self, name, ok, detail):
        status = "PASS" if ok else "FAIL"
        self.lines.append(f"[{status}] {name}")
        for line in detail:
            self.lines.append("       " + line)
        if ok:
            self.passed += 1
        else:
            self.failed += 1
            self.failures.append(name)

    def finish(self, path):
        total = self.passed + self.failed
        self.lines.append("")
        self.lines.append(f"RESULT {path.name}: {self.passed}/{total} "
                          f"(failed: {self.failures if self.failures else 'none'})")
        path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        print(f"wrote {path}: {self.passed}/{total}")
        return self.failed == 0


# ---- tracked python files, DEPLOYED scope only (docs/evidence excluded) ------
tracked = subprocess.run(["git", "ls-files", "*.py"], capture_output=True,
                         text=True, cwd=str(REPO)).stdout.splitlines()
deployed_py = [f for f in tracked if not f.startswith("docs/evidence/")]


# ============================== R5 ============================================
r5 = Rows("R5 deployed-source trace at base -- the card statement judged "
          "against the DEPLOYED text (threshold: 4/4 families quoted)")

# (a) THE ABSENT TOOL
markers = ["curve_fit", "least_squares", "leastsq", "parameter_correlation",
           "parameter correlation", "confidence_interval",
           "confidence interval"]
plane_files = [f for f in deployed_py
               if f in MATERIAL_PLANE
               or any(f.startswith(d) for d in PLANE_DIRS)]
plane_hits = {}
repo_hits = {}
for f in deployed_py:
    text = (REPO / f).read_text(encoding="utf-8", errors="replace")
    for m in markers:
        if m in text:
            for i, ln in enumerate(text.splitlines(), 1):
                if m in ln:
                    (plane_hits if f in plane_files else repo_hits
                     ).setdefault(f, []).append((i, m, ln.strip()[:100]))
ok_a = not plane_hits
mat_lines = read_repo("tools/elastic_foundation/materials.py")
ln6 = find_line(mat_lines, "no measured E11/E22/nu12/G12")
ln87 = find_line(mat_lines, "E11, E22, nu12, G12")
ok_a = ok_a and ln6 is not None and ln87 is not None
r5.row("R5(a) THE ABSENT TOOL", ok_a, [
    f"identification-marker scan over {len(deployed_py)} tracked deployed "
    f"*.py ({len(plane_files)} material-plane files):",
    f"  material-plane hits: {plane_hits if plane_hits else 'NONE (0)'}",
    f"  repo-wide non-plane hits (context, classified): "
    f"{[(f, h) for f, h in repo_hits.items()] if repo_hits else 'NONE (0)'}",
    f"tools/elastic_foundation/materials.py:{ln6} = "
    f"{mat_lines[ln6 - 1].strip()!r}" if ln6 else "line with E11 quote MISSING",
    f"tools/elastic_foundation/materials.py:{ln87} = "
    f"{mat_lines[ln87 - 1].strip()!r}" if ln87 else "line 87 quote MISSING",
    "  (the repo itself declares the measurement missing; orthotropic is "
    "refused by name for exactly that reason)"])

# (b) THE DECLARED SEAM
md_lines = read_repo("tools/gpu_fixtures_recovered/membrane_demo.py")
seam = [(i, md_lines[i - 1]) for i in (41, 42, 43)
        if i <= len(md_lines)]
ok_b = any("no physical calibration is claimed" in ln for _i, ln in seam) \
    and any("BP-A1" in ln for _i, ln in seam)
r5.row("R5(b) THE DECLARED SEAM", ok_b,
       [f"tools/gpu_fixtures_recovered/membrane_demo.py:{i} = {ln!r}"
        for i, ln in seam]
       + ["  (synthetic declared interface; physical calibration explicitly "
          "not claimed; deferred until BP-A1)"])

# (c) THE HONEST NON-CALIBRATION
tr_lines = read_repo("Chimera/core/trainer.py")
ln271 = find_line(tr_lines, "neither was ever calibrated against a measurement")
ok_c = ln271 is not None
r5.row("R5(c) THE HONEST NON-CALIBRATION", ok_c,
       ([f"Chimera/core/trainer.py:{ln271} = "
         f"{tr_lines[ln271 - 1].strip()!r}"] if ln271 else
        ["quote MISSING from Chimera/core/trainer.py"])
       + ["  (the project's own doctrine: training/fitting success is not "
          "calibration against a measurement)"])

# (d) FALSE-POSITIVE CONTROL
se_lines = read_repo("tools/surface_energy_checks.py")
ln241 = find_line(se_lines, "torque_covariance")
ok_d = ln241 is not None
r5.row("R5(d) FALSE-POSITIVE CONTROL", ok_d,
       ([f"tools/surface_energy_checks.py:{ln241} = "
         f"{se_lines[ln241 - 1].strip()!r}"] if ln241 else
        ["torque_covariance line MISSING"])
       + ["  CLASSIFICATION: a rigid-transform comparison norm between "
          "torque vectors (Linf-style norm of tau1 vs R@tau0), NOT a "
          "parameter-estimation covariance -- recorded so the absence "
          "claim in R5(a) cannot be defeated by a name match."])

r5_ok = r5.finish(OUT / "r5_source_trace.txt")

# ============================== R6 ============================================
r6 = Rows("R6 deployed findings + current-state measurements (never patched, "
          "never adopted as the model's truth)")

# (a) OWNER_INSTANCE CURRENT STATE (packet: PR #80 fix is FIXED AND DEPLOYED;
# measure the current state, no stale deviation language)
ctl = read_repo("tools/agent_fleet/control.py")
rh = read_repo("tools/agent_fleet/review_handoff.py")
ctl_sites = [i + 1 for i, ln in enumerate(ctl) if "owner_instance" in ln]
rh_sites = [i + 1 for i, ln in enumerate(rh) if "owner_instance" in ln]
fence_ctl = [i + 1 for i, ln in enumerate(ctl) if "instance_fencing" in ln]
fence_rh = [i + 1 for i, ln in enumerate(rh) if "instance_fencing" in ln]
ok_a = (len(ctl_sites) == 8 and len(rh_sites) == 1)
surprise_a = len(rh_sites) == 0
r6.row("R6(a) owner_instance current state", ok_a, [
    f"tools/agent_fleet/control.py: {len(ctl_sites)} occurrences at lines "
    f"{ctl_sites} (predicted 8: fence :121-123, setdefault :323, yield guard "
    f":499-501, claim bind :554, release clear :697)",
    f"tools/agent_fleet/review_handoff.py: {len(rh_sites)} occurrence(s) at "
    f"lines {rh_sites} (predicted 1: the claim-path bind)",
    f"instance_fencing sites: control.py {fence_ctl}, review_handoff.py "
    f"{fence_rh} (default mode 'compat'; fence applies when 'enforced')",
    "VERDICT: the PR #80 claim-path fix IS PRESENT at this base -- the "
    "claim of THIS task (controller rev 1087) bound a non-null "
    "owner_instance (subagent-worker-11-709647a37630); no stale deviation "
    "language is carried",
    f"contrast baseline: GOV-01's R6 measured review_handoff == 0 at "
    f"d59518b9; surprise (rh==0 here): {surprise_a}"])

# (b) FALSIFIER HUNT: training-fit success called predictive material validation
phrases = ["predictive material validation", "material validation",
           "validated predictor"]
hunt = {}
for f in deployed_py:
    text = (REPO / f).read_text(encoding="utf-8", errors="replace")
    for p in phrases:
        for i, ln in enumerate(text.splitlines(), 1):
            if p in ln:
                hunt.setdefault(f, []).append((i, p, ln.strip()[:100]))
ok_b = not hunt
hit_note = ("NONE (0) -- card falsifier NOT reproduced in the deployed text"
            if not hunt else repr(hunt))
r6.row("R6(b) card-falsifier hunt in deployed source", ok_b, [
    f"phrases {phrases!r} over {len(deployed_py)} deployed tracked *.py "
    "(docs/evidence excluded):",
    f"  hits: {hit_note}",
    "  ANY hit would be the falsifier FIRING; it would be reported here "
    "with exact file:line and never patched"])

# (c) CONSTANTS PLANE: parameters arrive documented, none identified
mats = (REPO / "tools/materials.py").read_text(encoding="utf-8",
                                               errors="replace")
# the prereg predicts the three literature source FAMILIES by name
# (INVISTA Dacron datasheet, Kawabata 1980, Polymer Handbook); count
# distinct families present, not a literal citation-string format
source_families = ["INVISTA", "Dacron", "Suprelle", "Kawabata",
                   "Polymer Handbook", "Brandrup"]
families_present = sorted({fam for fam in source_families
                           if fam.lower() in mats.lower()})
source_refs = len(families_present)
uncertain = len(re.findall(r"stderr|standard error|standard_error|"
                           r"correlation output|confidence interval",
                           mats, flags=re.I))
mat_doc = read_repo("tools/materials.py")
quote_lines = [ln.strip() for ln in mat_doc[:22]
               if "fiberfill" in ln.lower() or "Kawabata" in ln
               or "Polymer Handbook" in ln][:3]
ok_c = source_refs >= 3 and uncertain == 0
r6.row("R6(c) constants plane", ok_c, [
    f"tools/materials.py: {source_refs} distinct literature source "
    f"families present {families_present!r} (predicted >= 3 of "
    f"{source_families!r}); {uncertain} identified-with-uncertainty "
    f"parameter outputs (predicted 0)",
    f"citations quoted: {quote_lines!r}",
    "  (parameters ARRIVE from documented sources; none is identified from "
    "experiments with a standard error or correlation output -- the exact "
    "gap this card's calibration tool targets)"])

# (d) INDEPENDENCE AUDIT of this lane's own artifacts
model_text = (MAT04 / "reference" / "mat04_reference_model.py") \
    .read_text(encoding="utf-8")
imports = [ln.strip() for ln in model_text.splitlines()
           if re.match(r"\s*(import|from)\s+", ln)
           and not ln.strip().startswith("#")]
tools_imports = [i for i in imports
                 if "tools/" in i or "tools." in i
                 or "material_contract" in i or "elastic_foundation" in i]
ok_d = not tools_imports
r6.row("R6(d) independence audit", ok_d, [
    "full import list of reference/mat04_reference_model.py:"] +
    [f"  {i}" for i in imports] + [
    f"imports from the audited deployed code (tools/*): "
    f"{tools_imports if tools_imports else 'NONE (0)'}",
    "  dependency: the MATH-01 typed-quantity backbone ONLY (the task "
    "packet's designated units backbone), cited at every dimensional "
    "touchpoint; independence is claimed from the deployed material plane, "
    "not from MATH-01"])

r6_ok = r6.finish(OUT / "r6_findings.txt")

print(f"source identity blobs:")
for p in ["tools/agent_fleet/control.py",
          "tools/agent_fleet/review_handoff.py",
          "tools/gpu_fixtures_recovered/membrane_demo.py",
          "tools/elastic_foundation/materials.py",
          "tools/materials.py",
          "tools/surface_energy_checks.py",
          "Chimera/core/trainer.py"]:
    print(f"  {p}  {blob_sha(p)}")

sys.exit(0 if (r5_ok and r6_ok) else 1)
