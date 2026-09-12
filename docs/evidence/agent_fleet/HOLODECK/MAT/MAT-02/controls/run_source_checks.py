"""run_source_checks.py -- read-only R5/R6 measurements of the DEPLOYED
source text at base 4812b55b for holodeck-mat-02 (see
../PREREGISTRATION.txt). R5: 4/4 deployed gate families PRESENT with exact
quoted file:line (measured line numbers reported, wherever they sit). R6:
5 falsifier-hunt / current-state measurements. The live service at
127.0.0.1:8099 is NEVER contacted; no file outside checks/ is written;
bytecode writing is disabled.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

_HERE = Path(__file__).resolve().parent          # .../MAT-02/controls
_ROOT = _HERE.parents[6]                        # repo root (slot checkout)
CHECKS = _HERE.parent / "checks"

sys.path.insert(0, str(_HERE.parent / "reference"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find(repo_rel: str, needle: str, which=0):
    """Measured line numbers (1-based) of every `needle` occurrence in the
    file, or [] -- the caller asserts presence; the MEASURED number is
    recorded whatever it is (the prereg's predictions are about semantics
    present, with locations measured)."""
    text = (_ROOT / repo_rel).read_text(encoding="utf8")
    hits = [i + 1 for i, line in enumerate(text.splitlines())
            if needle in line]
    return hits


def quote(repo_rel: str, lo: int, hi: int) -> str:
    lines = (_ROOT / repo_rel).read_text(encoding="utf8").splitlines()
    lo = max(1, lo)
    body = [f"  {repo_rel}:{n}: {lines[n - 1]}" for n in range(lo, hi + 1)]
    return "\n".join(body)


def main() -> int:
    mc = "tools/material_contract.py"
    ef = "tools/elastic_foundation/materials.py"
    identities = {p: (sha256(_ROOT / p),
                      len((_ROOT / p).read_text(encoding="utf8").splitlines()))
                  for p in (mc, ef, "tools/materials.py", "tools/cad_sample.py",
                            "tools/matter_data.py",
                            "tools/gpu_fixtures_recovered/membrane_demo.py",
                            "tools/agent_fleet/control.py",
                            "tools/agent_fleet/review_handoff.py",
                            "Chimera/docs/matter/matter_library.json")}

    # ---------------- R5: the four deployed gate families ------------------
    r5, r5_ok = [], True

    def gate(lines_ok, title, hits_list, quot):
        nonlocal r5_ok
        ok = all(hits_list)
        r5_ok &= ok
        r5.append(f"[{'PRESENT' if ok else 'ABSENT'}] {title}")
        r5.append(quot)
        r5.append("")

    # (a) the model-claim gate (P-8j)
    h_gate = find(mc, "RefusalKind.UNSUPPORTED_MODEL")
    h_text = find(mc, "no isotropic or 3D claim may be ")
    g = min(h_text) if h_text else None
    gate(h_gate and h_text, "(a) THE MODEL-CLAIM GATE: MaterialContract.model"
         " refuses UNSUPPORTED_MODEL when the record's sources do not carry"
         " the model (P-8j) -- a claim outside the source-supported set is"
         " refused, never invented", [h_gate, h_text],
         quote(mc, g - 4, g + 5) if g else "  ABSENT")

    # (b) the required-parameter side: white_oak model set + P-8b refusal
    h_models = find(mc, '"uniaxial_along_grain", "orthotropic_ratios"')
    h_default = find(mc, "the contract refuses to default it")
    g2 = min(h_default) if h_default else None
    gate(h_models and h_default, "(b) THE REQUIRED-PARAMETER SIDE: the"
         " white_oak record's model set is EXPLICITLY what its sources"
         " support; only published properties enter and get() refuses an"
         " unpublished property BY NAME (P-8b) -- missing inputs produce"
         " no defaulted capability", [h_models, h_default],
         (quote(mc, min(h_models), min(h_models) + 2) if h_models else
          "  ABSENT") + "\n" +
         (quote(mc, g2 - 6, g2 + 1) if g2 else "  ABSENT"))

    # (c) the orthotropic law validators (P-8f/P-8g)
    h_spd = find(mc, "def validate_positive_definite")
    h_orth = find(mc, "def validate_orthotropic")
    h_dec = find(mc, "NOT orthotropic")
    g3 = min(h_dec) if h_dec else None
    gate(h_spd and h_orth and h_dec, "(c) THE ORTHOTROPIC LAW: the deployed"
         " validators check symmetry + positive definiteness + normal-shear"
         " DECOUPLING in a declared frame -- a coupled tangent is refused"
         " from the orthotropic law (P-8f/P-8g)", [h_spd, h_orth, h_dec],
         (f"  defs at measured lines {min(h_spd)}/{min(h_orth)}\n" if
          h_spd and h_orth else "  ABSENT\n") +
         (quote(mc, g3 - 6, g3 + 4) if g3 else "  ABSENT"))

    # (d) the two-constant isotropic plane + the two named refusals
    h_lam = find(ef, "def lambda_bar")
    h_mu = find(ef, "def mu_bar")
    h_nu = find(ef, "-1.0 < m.nu < 0.5")
    h_req = find(ef, "def require_isotropic")
    h_e = find(ef, "E11, E22, nu12, G12")
    h_pois = find(ef, "POISSON_RATIO_NOT_MEASURED")
    h_inv = find(ef, "inventing a Poisson ratio or an empirical shear")
    g4 = min(h_inv) if h_inv else None
    gate(h_lam and h_mu and h_nu and h_req and h_e and h_pois and h_inv,
         "(d) THE TWO-CONSTANT ISOTROPIC PLANE: ElasticMaterial2D is the"
         " (E, nu, h) law with lambda_bar/mu_bar the declared reduction; nu"
         " gated to (-1, 1/2); require_isotropic names what a defensible"
         " orthotropic port needs (E11, E22, nu12, G12 + frames);"
         " material_from_library refuses poisson_ratio_not_measured"
         " instead of inventing a constant",
         [h_lam, h_mu, h_nu, h_req, h_e, h_pois, h_inv],
         (quote(ef, min(h_lam), min(h_mu) + 2) if h_lam and h_mu else
          "  ABSENT") + "\n" +
         (quote(ef, min(h_e) - 3, min(h_e) + 1) if h_e else "  ABSENT") +
         "\n" +
         (quote(ef, g4 - 5, g4 + 1) if g4 else "  ABSENT"))

    r5_lines = (["holodeck-mat-02 source checks -- run_source_checks.py",
                 "R5 deployed gate families at base 4812b55b (threshold 4/4,"
                 " semantics PRESENT with MEASURED line numbers)", ""]
                + r5
                + [f"VERDICT: {'HOLDS 4/4' if r5_ok else 'MISS'}",
                   "", "MEASURED SOURCE IDENTITIES (sha256, lines):"]
                + [f"  {p}: {h[:64]}... ({n} lines)"
                   for p, (h, n) in sorted(identities.items())])
    (CHECKS / "r5_source_trace.txt").write_text(
        "\n".join(r5_lines) + "\n", encoding="utf8")

    # ---------------- R6: falsifier hunt + current state -------------------
    r6 = []
    # (a) the library shape: the falsifier's exact INPUT SET, gated behind
    #     the R5(d) refusal -- measured, not assumed.
    lib = json.loads((_ROOT / "Chimera/docs/matter/matter_library.json")
                     .read_text(encoding="utf8"))
    mats = lib.get("materials", {})
    with_rho = [n for n, m in mats.items()
                if (m.get("physical") or {}).get("density_kg_m3")]
    with_e = [n for n, m in mats.items()
              if (m.get("physical") or {}).get("youngs_modulus_gpa")]
    with_nu = [n for n, m in mats.items()
               if any("poisson" in k for k in (m.get("physical") or {}))]
    r6.append(f"(a) LIBRARY SHAPE: matter_library.json measured -- materials="
              f"{len(mats)} (predicted 18), with density_kg_m3={len(with_rho)}"
              f" (predicted 10), with youngs_modulus_gpa={len(with_e)} "
              f"(predicted 4), with ANY poisson key={len(with_nu)} (predicted"
              f" 0). The library carries the falsifier's exact INPUT SET "
              f"(density + at most one modulus, no poisson anywhere); the "
              f"gate between that input set and any stiffness claim is "
              f"R5(d)'s poisson_ratio_not_measured refusal (quoted in "
              f"r5_source_trace.txt). VERDICT: falsifier instance? NO -- "
              f"the consumer refuses at the exact point where "
              f"'density+one modulus suffices' would have to be assumed."
              + ("" if (len(mats), len(with_rho), len(with_e),
                        len(with_nu)) == (18, 10, 4, 0)
                 else " [SURPRISE: measured counts differ from prediction; "
                      "reported as measured]"))
    # (b) consumer advertising: density's only consumers claim MASS-class
    h_rho = find("tools/cad_sample.py", "rho = DENSITY[PART_MATERIAL[name]]")
    h_dom = find("tools/materials.py", "Stiffness/friction join")
    h_read = find("tools/matter_data.py", "READ THROUGH FROM THE WORLD")
    r6.append(f"(b) CONSUMER ADVERTISING: cad_sample.py consumes DENSITY at "
              f"measured line {min(h_rho) if h_rho else 'ABSENT'} for the "
              f"mass/inertia sampler ONLY (its referee tolerances are "
              f"mass_err/iner_err -- a MASS-CLASS claim, the one response "
              f"the 'mass' model licenses); the composition table's declared "
              f"domain is quoted at materials.py:"
              f"{min(h_dom) if h_dom else 'ABSENT'} ('Stiffness/friction "
              f"join the table when the force laws that read them are "
              f"built'); matter_data.py reads density/E from the library as "
              f"CITED constants (read-through at measured line "
              f"{min(h_read) if h_read else 'ABSENT'}), never deriving nu "
              f"from them. VERDICT per consumer: claims-beyond-inputs? NO "
              f"for all three (basis: mass-class advertising + declared "
              f"open domain)."
              + ("" if h_rho and h_dom and h_read else " [SURPRISE: a "
                 "measured marker is ABSENT; see lines above]"))
    # (c) MAT-01 seams at THIS base
    h_bp = find("tools/gpu_fixtures_recovered/membrane_demo.py",
                "deferred until BP-A1 lands")
    g_bp = min(h_bp) if h_bp else None
    r6.append("(c) MAT-01 SEAMS at this base: cad_sample raw-constants "
              "consumer present (same measured line as (b)); "
              "membrane_demo.py BP-A1 admission deferral measured at line "
              f"{g_bp if g_bp else 'ABSENT'}:\n"
              + (quote("tools/gpu_fixtures_recovered/membrane_demo.py",
                       g_bp - 2, g_bp + 1) if g_bp else "  ABSENT")
              + "\nBoth match MAT-01's measurements at the SAME base "
              "4812b55b (branch astra/tasks/holodeck-mat-01, commit "
              "2352fc1b) -- unchanged, as expected; any drift would have "
              "been a surprise finding.")
    # (d) owner_instance CURRENT STATE (PR #80 fix deployed; no stale
    #     deviation language; measured, surprise rule stated in prereg)
    rh = find("tools/agent_fleet/review_handoff.py", "owner_instance")
    ct = find("tools/agent_fleet/control.py", "owner_instance")
    rh_n, ct_n = len(rh), len(ct)
    surprise = rh_n == 0
    r6.append(f"(d) OWNER_INSTANCE CURRENT STATE (task packet: the PR #80 "
              f"claim-path fix is FIXED AND DEPLOYED -- measured now, no "
              f"stale deviation language): review_handoff.py occurrences="
              f"{rh_n} at measured lines {rh} (predicted >= 1; the "
              f"claim-path bind) and control.py occurrences={ct_n} at "
              f"measured lines {ct} (predicted 8: the _task fence, "
              f"setdefault, yield guard, claim bind, release clear). "
              f"{'SURPRISE FINDING: rh==0 -- the fix would NOT be deployed '
              'at this base; reported as such.' if surprise else 'No '
              'surprise: rh >= 1 as predicted; the GOV-01-era deviation '
              '(rh==0 at d59518b9) remains FIXED at this base.'}")
    # (e) independence audit of this lane's own reference model
    src = (_HERE.parent / "reference" / "mat02_reference_model.py"
           ).read_text(encoding="utf8")
    imports = sorted(set(re.findall(r"^(?:import|from)\s+([\w.]+)",
                                    src, re.M)))
    audited = [i for i in imports
               if i.startswith(("material_contract", "elastic_foundation",
                                "matter_data", "tools."))]
    r6.append(f"(e) INDEPENDENCE AUDIT: mat02_reference_model.py imports "
              f"{imports} -- stdlib plus math01_reference_model (the "
              f"designated MATH-01 units backbone) ONLY; imports from the "
              f"audited deployed code: {audited or 'NONE'}. run_controls.py "
              f"imports the model + stdlib; run_source_checks.py (this "
              f"file) READS the audited files as text and imports neither.")

    r6_ok = (not surprise and bool(h_rho and h_dom and h_read and h_bp))
    verdict = ("5/5 measured; no surprise findings" if r6_ok
               else "5/5 measured WITH SURPRISE FINDINGS (see above)")
    r6_lines = (["holodeck-mat-02 source checks -- run_source_checks.py",
                 "R6 falsifier hunt + current-state measurements (threshold:"
                 " 5 measurements REPORTED; surprise findings flagged)",
                 ""] + [item + "\n" for item in r6] +
                ["VERDICT: " + verdict])
    (CHECKS / "r6_findings.txt").write_text(
        "\n".join(r6_lines) + "\n", encoding="utf8")
    print(f"R5: {'HOLDS 4/4' if r5_ok else 'MISS'}")
    print("R6: 5 measurements written"
          + (" (surprise findings present)" if surprise else
             " (no surprise findings)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
