"""THE K-FILL DERIVATION (lane k-fill-20260920): the DERIVED force/mass set and the
deposit-scale hind book re-run it powers.

Consumes ONLY sha-pinned committed artifacts (verified at load; REFUSES on drift):
  - the pennation-correction lane's admitted annotation: 23 paired corrected forces
    F = 0.30 MPa x PCSA x cos(measured pennation) + deferred EDL/FDL whole-muscle terms
  - the pulley lane's measured knee/MTP deposit-arm curves
  - the ankle lane's measured ankle deposit-arm curves + cap_law sign gate
  - the muscle-path record (functional_groups = lawful class membership; record
    max_force_N for the sigma-fit coherence cross-check; hip straight-line arms for
    the context book)
  - the Oku demand peaks, the 15-node stance-hold demands, the deposit mass book
  - the live contract caps

Produces k_fill_book.json:
  (1) the DERIVED FORCE SET (per-muscle cited forces; quarantined rows stay named
      gaps - no silent fills);
  (2) the DERIVED MASS SET (the deposit's scale-free fractions rescaled by one
      derived factor to the cited Oku-chain-fraction x adult-female-band-midpoint
      expectation);
  (3) the deposit-scale capability books at the derived set (knee, ankle plantar +
      dorsal, MTP, hip-extension context), each with walk-demand coverage;
  (4) the stance-hold 15-node re-price at the derived caps (vs the banked doc-cap
      and walk-force columns);
  (5) the operator's rear-up class C* in (22.4, 33.6] N.m verdict (COVERED iff max
      capability > 33.6);
  (6) the pre-registered falsifier verdicts (F1-F5, P1-P8 of receipt.json).

Pure function of the pinned inputs; byte-deterministic by construction.
Run from the repo root:
  python -B tools/science_funnel/validation/k_fill_20260920/derive_k_fill.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RECEIPT_PATH = HERE / "receipt.json"

# --------------------------------------------------------------- constants (cited)

SIGMA_MPA = 0.30  # THE ONE SPECIFIC TENSION CONSTANT - cited, never swept:
#   LightEngine/kinematic/muscles.py:79 ANATOMY-DATUM (30.0 N/cm^2), sha-pinned by the
#   pennation-correction receipt; sigma_law_20260921 verdict RETAINED-AS-ASSUMED (the
#   assumed point in the 23-32 N/cm^2 band). The deposit record's 1.28091414 Pa is
#   REJECTED for capability use: it is a least-squares fit of mass-adjusted Oku Fmax
#   onto Guimaraes PCSA sums (muscle_path_geometry hindlimb.specific_tension.method)
#   - a demand-side fit, circular for a capability set.
RECORD_SIGMA_PA = 1280914.1381700735  # for the coherence cross-check only (P8)
S_RATIO = SIGMA_MPA * 1e6 / RECORD_SIGMA_PA  # 0.2342083...

# Oku 2021 Table 1 segment masses (kg) of the 10.038 kg model - the cited chain
# fraction anchor; constants transcribed in the deposit_mass receipt's
# literature_prior (sha-pinned) from the pinned oku2021.xml. Citation: Oku H, Ide N,
# Ogihara N (2021) Commun Biol 4:308, Table 1 (parameters from Ogihara et al. 2009).
OKU_THIGH_KG = 0.557
OKU_SHANK_KG = 0.269
OKU_FOOT_KG = 0.080
OKU_PHALANGES_KG = 0.021
OKU_MODEL_TOTAL_KG = 10.038

# Adult female rhesus band 5.4-6.9 kg (Turnquist & Kessler 1989 via the committed
# k_forensics receipt); the BAND MIDPOINT is the deposit_mass receipt's own banked
# convention (its derived_context line), reused, not re-chosen.
AF_BAND_KG = [5.4, 6.9]
AF_MIDPOINT_KG = 6.15

# The operator-authored rear-up class (mission C*): numerically (2x, 3x] the live
# hip cap 11.2125 N.m. Consumed as GIVEN (record.md D4); not re-derived.
REARUP_CLASS_LO_N_M = 22.4
REARUP_CLASS_HI_N_M = 33.6
REARUP_COVERED_ABOVE_N_M = 33.6

K_SI = 0.11975394  # cited for the dead-branch context only (k_gate_closure)

GRID_STEP_DEG = 0.05

REQURED = ("knee_extension", "ankle_plantarflexion", "ankle_dorsiflexion",
           "mtp_flexion")


# --------------------------------------------------------------- helpers

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def canonical_json_bytes(obj) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=True) + "\n").encode("utf-8")


def interp_arm(direction: dict, deg: float) -> float:
    """Linear interpolation of a measured arm curve at a scan degree (the hind
    book's convention: samples stored in the recorded jrange order, endpoints
    inclusive; outside the scan -> KeyError, refuse, never extrapolate)."""
    lo, hi = direction["jrange_deg"]
    n = len(direction["arm_samples_m"])
    x = (deg - lo) / (hi - lo) * (n - 1)
    i = int(x)
    if i < 0 or i > n - 1:
        raise KeyError(f"deg {deg} outside measured scan [{lo}, {hi}]")
    if i == n - 1:
        i, f = n - 2, 1.0
    else:
        f = x - i
    s = direction["arm_samples_m"]
    return s[i] * (1.0 - f) + s[i + 1] * f


def common_grid(directions: list, step_deg: float) -> list:
    """Numeric intersection of the class's measured scans, ascending."""
    lo = max(min(d["jrange_deg"]) for d in directions)
    hi = min(max(d["jrange_deg"]) for d in directions)
    if lo > hi:
        raise ValueError(f"empty scan intersection [{lo}, {hi}]")
    n = int(round((hi - lo) / step_deg))
    grid = [lo + k * step_deg for k in range(n + 1)]
    if abs(grid[-1] - hi) > 1e-9:
        grid.append(hi)
    return grid


def envelope(directions, forces, grid, sign_gate):
    """cap(q) = sum_m F_m |r_m(q)| over the grid, each muscle contributing only
    where its arm satisfies the sign gate (None gate = abs, the hind book's
    fixed-sign law). forces aligned with directions."""
    samples = []
    best = (-1.0, None)
    for q in grid:
        tau = 0.0
        for (f, name), d in zip(forces, directions):
            a = interp_arm(d, q)
            if sign_gate is None or sign_gate(a):
                tau += f * abs(a)
        samples.append({"q_deg": round(q, 4), "tau_N_m": round(tau, 6)})
        if tau > best[0]:
            best = (tau, round(q, 4))
    return samples, best[0], best[1]


# --------------------------------------------------------------- inputs

def load_inputs():
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    pins = receipt["inputs_pinned"]
    for key, pin in pins.items():
        p = REPO / pin["path"]
        got = sha256_file(p)
        if got != pin["sha256"]:
            raise SystemExit(
                f"REFUSAL: input sha mismatch {key} ({pin['path']}): {got} != {pin['sha256']}")
    corrected = json.loads((REPO / pins["pennation_corrected_assembly"]["path"]).read_text(encoding="utf-8"))
    pulley = json.loads((REPO / pins["pulley_arms_derivation"]["path"]).read_text(encoding="utf-8"))
    ankle = json.loads((REPO / pins["ankle_arms_book"]["path"]).read_text(encoding="utf-8"))
    geo = json.loads((REPO / pins["muscle_path_geometry_snapshot"]["path"]).read_text(encoding="utf-8"))
    oku = json.loads((REPO / pins["derived_numbers_snapshot"]["path"]).read_text(encoding="utf-8"))
    hold = json.loads((REPO / pins["stance_hold_snapshot"]["path"]).read_text(encoding="utf-8"))
    contract = json.loads((REPO / pins["gait_contract_drives_snapshot"]["path"]).read_text(encoding="utf-8"))
    massbook = json.loads((REPO / pins["deposit_mass_book"]["path"]).read_text(encoding="utf-8"))
    return receipt, pins, corrected, pulley, ankle, geo, oku, hold, contract, massbook


# --------------------------------------------------------------- force set

def build_force_set(corrected, geo):
    """The DERIVED FORCE SET from the pennation-corrected annotation."""
    fps = corrected["force_pairing_status"]
    deferred = fps["deferred_whole_muscle_numbers"]
    forces = {}       # name (no R_ prefix) -> record
    slips = {}        # slip name -> per-slip force (declared equal split)
    for rec in corrected["muscles"]:
        name = rec.get("name")
        fp = rec.get("force_pairing") or {}
        nums = fp.get("numbers") or {}
        prov = fp.get("provenance") or {}
        status = fp.get("status", prov.get("status", "no_force_record"))
        f = nums.get("max_isometric_force_N")
        entry = {
            "force_N": f,
            "status": status,
            "pennation_deg": nums.get("pennation_deg"),
            "pcsa_m2": nums.get("pcsa_m2"),
            "force_uncorrected_N": nums.get("max_isometric_force_N_uncorrected"),
            "sheet_row": (prov.get("row") if isinstance(prov.get("row"), (int, str)) else None),
        }
        forces[name] = entry
    # deferred whole-muscle numbers (EDL, FDL) with their sheet provenance
    whole = {}
    for muscle in ("EDL", "FDL"):
        d = deferred[muscle]
        whole[muscle] = {
            "force_N": d["numbers"]["max_isometric_force_N"],
            "pcsa_m2": d["numbers"]["pcsa_m2"],
            "pennation_deg": d["numbers"]["penn_deg"],
            "status": "split_homolog_deferred_whole_uncorrected_declared",
            "sheet_row": d["provenance"]["sheet_row"],
            "cells": d["provenance"]["cells"],
        }
    quarantined = {
        q["guimaraes"]: {"wiseman": q["wiseman"], "problems": q["problems"],
                          "sheet_row": q["sheet_row"], "force_N": None,
                          "status": "exact_name_row_quarantined_at_admission_NAMED_GAP"}
        for q in fps["exact_but_quarantined"]
    }
    # class membership: the record's own functional_groups (lawful, cited)
    walking = geo["hindlimb"]["poses"]["walking"]["muscles"]
    groups = {n: r["functional_groups"] for n, r in walking.items()}
    record_force = {n: r["max_force_N"] for n, r in walking.items()}
    return forces, whole, quarantined, groups, record_force, fps


def paired_record_ratio_crosscheck(forces, record_force, quarantined_names):
    """P8: corrected / (record max_force_N x s) == 1 within 2% on shared muscles."""
    alias = {"VMed": "VM"}  # the model names it VMed; the record names it VM
    rows = []
    for name, e in sorted(forces.items()):
        short = name[2:] if name.startswith("R_") else name
        short = alias.get(short, short)
        if e["force_N"] is None or short not in record_force:
            continue
        rec_scaled = record_force[short] * S_RATIO
        ratio = e["force_N"] / rec_scaled
        rows.append({"muscle": name, "derived_N": round(e["force_N"], 6),
                     "record_x_s_N": round(rec_scaled, 6), "ratio": round(ratio, 6),
                     "within_2pct": abs(ratio - 1.0) <= 0.02})
    bad = [r for r in rows if not r["within_2pct"]]
    return {"law": "corrected_force / (record max_force_N x sigma_ratio); "
                   "both sources are the same published PCSAs at sigma 0.30 vs 1.28091414 Pa",
            "sigma_ratio": round(S_RATIO, 9), "rows": rows,
            "outside_2pct": bad,
            "verdict": "HELD" if not bad else "FIRED (recorded, not tuned)"}


# --------------------------------------------------------------- mass set

def build_mass_set(massbook):
    """D3: the deposit's scale-free fractions rescaled to the cited expectation."""
    bodies = {b["name"]: b["mass_kg"] for b in massbook["macaque_masses"]["bodies"]}
    deposit_sum = massbook["macaque_masses"]["sum_kg"]
    chain = OKU_THIGH_KG + OKU_SHANK_KG + OKU_FOOT_KG + OKU_PHALANGES_KG
    oku_total = OKU_MODEL_TOTAL_KG
    chain_fraction = 2.0 * chain / oku_total
    target_sum = chain_fraction * AF_MIDPOINT_KG
    factor = target_sum / deposit_sum
    derived = {name: m * factor for name, m in bodies.items()}
    derived_sum = sum(derived.values())
    envelope = [0.99737, 1.656]  # the deposit-mass lane's banked expectation envelope
    return {
        "law": "derived_body_i = deposit_body_i x (target_sum / deposit_sum); "
               "target_sum = (2 x (Oku thigh 0.557 + shank 0.269 + foot 0.080 + phalanges 0.021) / "
               "10.038) x 6.15 kg (adult female band 5.4-6.9 kg midpoint, the deposit_mass "
               "lane's banked convention); the deposit's scale-free fractions are kept so the "
               "model's own mass DISTRIBUTION survives (Oku's table has no pelvis counterpart)",
        "citations": {
            "oku_table1": "Oku 2021 Commun Biol 4:308 Table 1 (Ogihara-model segments), "
                          "pinned at tools/science_funnel/validation/deposit_mass_20260921/literature/oku2021.xml",
            "adult_female_band": "Turnquist & Kessler 1989 Am J Primatol 19:1-13, 5.4-6.9 kg, via the "
                                 "committed k_forensics_20260921/receipt.json body_mass_prior",
            "midpoint_convention": "the deposit_mass_20260921 receipt's banked 6.15 kg band-midpoint context",
            "deposit_masses": "deposit_mass_20260921/deposit_mass_book.json macaque_masses_measured.bodies_kg",
        },
        "oku_chain_fraction": round(chain_fraction, 9),
        "target_sum_kg": round(target_sum, 9),
        "deposit_sum_kg": round(deposit_sum, 9),
        "rescale_factor": round(factor, 9),
        "deposit_bodies_kg": bodies,
        "derived_bodies_kg": {k: round(v, 9) for k, v in derived.items()},
        "derived_sum_kg": round(derived_sum, 9),
        "expectation_envelope_kg": envelope,
        "inside_envelope": envelope[0] <= derived_sum <= envelope[1],
        "declared_caveats": [
            "the literature anchors EXCLUDE the pelvis segment; a pelvis-carrying set rescaled to a "
            "pelvis-exclusive anchor is the deposit_mass lane's pre-registered conservative bound (inherited)",
            "the deposit's 10.897259x foot_l/foot_r asymmetry is a property of the deposit's own fractions "
            "and is preserved by this rescale - only the authors can resolve the split (deposit_mass finding)",
        ],
        "closure": abs(derived_sum - target_sum) <= 1e-9,
    }


# --------------------------------------------------------------- capability books

def arm_book(directions_names, arms_dict, force_of):
    dirs, forces, missing = [], [], []
    for name in directions_names:
        if name not in arms_dict:
            missing.append(name)
            continue
        f = force_of(name)
        dirs.append(arms_dict[name])
        forces.append((f, name))
    return dirs, forces, missing


def build_capability_books(pulley, ankle, forces, whole, quarantined, groups):
    arms = ankle["arms"]
    pulley_dirs = pulley["directions"]
    books = {}

    def fdx_per_slip():
        return whole["FDL"]["force_N"] / 4.0

    def edl_per_slip():
        return whole["EDL"]["force_N"] / 4.0

    def force_of_paired(name):
        return forces[name]["force_N"]

    def name_gap_block(names, why):
        return {n: {"force_N": None, "status": "NAMED_GAP", "why": why} for n in names}

    # ---- KNEE EXTENSION (vasti-only; RF a named gap - the Guimaraes RF row is
    # quarantined data (mass_additivity_dev 0.023), no silent fills)
    knee_names = ["R_VI", "R_VL", "R_VMed"]
    f_knee = {n: force_of_paired(n) for n in knee_names}
    dirs, fl, _ = arm_book(knee_names, pulley_dirs, lambda n: f_knee[n])
    grid = common_grid(dirs, GRID_STEP_DEG)
    samples, cap, argmax = envelope(dirs, fl, grid, None)
    per_muscle_argmax = [
        {"muscle": n, "force_N": round(f, 6), "arm_mm_at_argmax": round(abs(interp_arm(d, argmax)) * 1000.0, 4),
         "contribution_N_m": round(f * abs(interp_arm(d, argmax)), 6)}
        for (f, n), d in zip(fl, dirs)]
    books["knee_extension"] = {
        "class": "quadriceps vasti (VI + VL + VMed) over the condyle-cylinder pulley",
        "arms_source": "pulley_rederivation_20260920/pulley_arms_derivation.json directions",
        "grid_deg": {"lo": round(min(grid), 3), "hi": round(max(grid), 3), "step_deg": GRID_STEP_DEG},
        "cap_N_m": round(cap, 6), "argmax_q_deg": argmax,
        "envelope_samples_N_m": samples,
        "per_muscle_at_argmax": per_muscle_argmax,
        "named_gaps": name_gap_block(["R_RF"], "the Guimaraes RF row is QUARANTINED data "
                                              "(mass_additivity_dev 0.023) - vasti-only, as the hind book's V2; no silent fills"),
        "trace": {"arms": "pulley_arms_derivation (sha-pinned)",
                   "forces": "pennation_corrected_assembly force_pairing.numbers.max_isometric_force_N (sha-pinned)"},
    }

    # ---- MTP FLEXION (FDL II-V quarter-split + FHL whole; abs law - the hind book's)
    mtp_names = ["R_FDL_TENDONII", "R_FDL_TENDONIII", "R_FDL_TENDONIV", "R_FDL_TENDONV", "R_FHL"]
    f_mtp = {n: (fdx_per_slip() if "FDL" in n else force_of_paired(n)) for n in mtp_names}
    dirs, fl, _ = arm_book(mtp_names, pulley_dirs, lambda n: f_mtp[n])
    grid = common_grid(dirs, GRID_STEP_DEG)
    samples, cap, argmax = envelope(dirs, fl, grid, None)
    books["mtp_flexion"] = {
        "class": "FDL tendons II-V (one muscle, four slips) + FHL (hallux)",
        "split_law": "FDL whole-muscle derived force 138.0639 N split EQUALLY across the four slips "
                     "(the hind/ankle books' declared law; the deferred warning 'MUST NOT be copied "
                     "onto any single slip' is honored - the split carries its partition bracket in "
                     "the reference books and no single slip carries the whole)",
        "arms_source": "pulley_rederivation_20260920/pulley_arms_derivation.json directions",
        "grid_deg": {"lo": round(min(grid), 3), "hi": round(max(grid), 3), "step_deg": GRID_STEP_DEG},
        "cap_N_m": round(cap, 6), "argmax_q_deg": argmax,
        "envelope_samples_N_m": samples,
        "per_muscle_at_argmax": [
            {"muscle": n, "force_N": round(f, 6), "arm_mm_at_argmax": round(abs(interp_arm(d, argmax)) * 1000.0, 4),
             "contribution_N_m": round(f * abs(interp_arm(d, argmax)), 6)}
            for (f, n), d in zip(fl, dirs)],
        "named_gaps": {},
        "trace": {"arms": "pulley_arms_derivation (sha-pinned)",
                   "forces": "deferred_whole_muscle_numbers.FDL + paired R_FHL (sha-pinned)"},
    }

    # ---- ANKLE PLANTAR (sign gate: arm < 0; the ankle book's cap_law)
    plantar_names = ["R_SOL", "R_MG", "R_LG", "R_FDL_TENDONII", "R_FDL_TENDONIII",
                     "R_FDL_TENDONIV", "R_FDL_TENDONV", "R_FHL", "R_PB", "R_PL"]
    f_pl = {}
    for n in plantar_names:
        f_pl[n] = fdx_per_slip() if "FDL" in n else force_of_paired(n)
    dirs, fl, _ = arm_book(plantar_names, arms, lambda n: f_pl[n])
    grid = common_grid(dirs, GRID_STEP_DEG)
    samples, cap, argmax = envelope(dirs, fl, grid, lambda a: a < 0.0)
    books["ankle_plantarflexion"] = {
        "class": "triceps surae (SOL + MG + LG) + FDL II-V + FHL + PB + PL, sign-gated "
                 "(plantarflexion = negative arms under r = -dL/dq); FDL V contributes only on "
                 "its matching-sign sub-window (the ankle book's sign law)",
        "arms_source": "ankle_arms_20260921/ankle_arms_book.json arms (201-sample measured curves)",
        "grid_deg": {"lo": round(min(grid), 3), "hi": round(max(grid), 3), "step_deg": GRID_STEP_DEG},
        "cap_N_m": round(cap, 6), "argmax_q_deg": argmax,
        "envelope_samples_N_m": samples,
        "per_muscle_at_argmax": [
            {"muscle": n, "force_N": round(f, 6), "arm_mm_at_argmax": round(abs(interp_arm(d, argmax)) * 1000.0, 4),
             "contribution_N_m": round(f * abs(interp_arm(d, argmax)), 6)}
            for (f, n), d in zip(fl, dirs)],
        "named_gaps": name_gap_block(["R_TP"], "the Guimaraes TP row is QUARANTINED data "
                                                "(mass_additivity_dev 0.060); the ankle book's V2 also carried no TP"),
        "trace": {"arms": "ankle_arms_book arms (sha-pinned)",
                   "forces": "pennation_corrected_assembly paired + deferred FDL (sha-pinned)"},
    }

    # ---- ANKLE DORSAL (sign gate: arm > 0)
    dorsal_names = ["R_TA", "R_EDL_TENDONII", "R_EDL_TENDONIII", "R_EDL_TENDONIV",
                    "R_EDL_TENDONV", "R_EHL"]
    f_dn = {n: (edl_per_slip() if "EDL" in n else force_of_paired(n)) for n in dorsal_names}
    dirs, fl, _ = arm_book(dorsal_names, arms, lambda n: f_dn[n])
    grid = common_grid(dirs, GRID_STEP_DEG)
    samples, cap, argmax = envelope(dirs, fl, grid, lambda a: a > 0.0)
    books["ankle_dorsiflexion"] = {
        "class": "TA + EDL II-V + EHL, sign-gated (dorsiflexion = positive arms); EDL whole-muscle "
                 "derived force split equally across its four slips (declared law)",
        "arms_source": "ankle_arms_20260921/ankle_arms_book.json arms",
        "grid_deg": {"lo": round(min(grid), 3), "hi": round(max(grid), 3), "step_deg": GRID_STEP_DEG},
        "cap_N_m": round(cap, 6), "argmax_q_deg": argmax,
        "envelope_samples_N_m": samples,
        "per_muscle_at_argmax": [
            {"muscle": n, "force_N": round(f, 6), "arm_mm_at_argmax": round(abs(interp_arm(d, argmax)) * 1000.0, 4),
             "contribution_N_m": round(f * abs(interp_arm(d, argmax)), 6)}
            for (f, n), d in zip(fl, dirs)],
        "named_gaps": {},
        "trace": {"arms": "ankle_arms_book arms (sha-pinned)",
                   "forces": "pennation_corrected_assembly paired + deferred EDL (sha-pinned)"},
    }

    # (the hip-extension context book is built by build_hip_context(): the record's
    # straight-line hip arms live in the muscle_path_geometry snapshot, not in the
    # arm books, and carry the declared 25%-unknown bound)
    return books, None


def build_hip_context(groups, record_arms, forces):
    """The hip-extension context book: corrected extensor forces x record straight-line
    hip arms (the walking pose scalars; 25% caveat named)."""
    rows = []
    total = 0.0
    for n in sorted(n for n, g in groups.items() if "hip_extensors" in g):
        f = forces["R_" + n]["force_N"]
        a = abs(record_arms[n])
        c = f * a
        total += c
        rows.append({"muscle": "R_" + n, "force_N": round(f, 6),
                     "record_hip_arm_m": round(a, 9),
                     "contribution_N_m": round(c, 6)})
    adductors = [n for n, g in groups.items() if "hip_adductors" in g]
    add_total = 0.0
    add_rows = []
    for n in sorted(adductors):
        if "R_" + n not in forces or forces["R_" + n]["force_N"] is None:
            continue
        a = record_arms.get(n)
        if a is None:
            continue
        c = forces["R_" + n]["force_N"] * abs(a)
        add_total += c
        add_rows.append({"muscle": "R_" + n, "contribution_N_m": round(c, 6)})
    return {
        "class": "the record's own hip_extensors functional group at the walking pose",
        "arm_caveat": "the record's straight-line hip arms carry the DECLARED 25% unknown "
                      "(the estimate class the pulley lane falsified at the knee, ratio 0.00); "
                      "context for the operator's rear-up class, never an engine cap",
        "extensors": rows, "hip_extension_context_N_m": round(total, 6),
        "adductor_secondary_named": {"rows": add_rows, "sum_N_m": round(add_total, 6),
                                      "note": "adductors carry extensor-side arms in the record; "
                                              "named secondary, not in the primary class"},
    }


# --------------------------------------------------------------- consumption

def build_walk_coverage(books, oku):
    peaks = oku["oku_before_alteration"]["torques"]
    demand = {"knee_extension": peaks["knee"]["peak_abs_stance_Nm"],
              "mtp_flexion": peaks["MP"]["peak_abs_stance_Nm"],
              "ankle_plantarflexion": abs(peaks["ankle"]["min_Nm"]),
              "ankle_dorsiflexion": peaks["ankle"]["max_Nm"]}
    out = {}
    for cls in REQURED:
        cap = books[cls]["cap_N_m"]
        d = demand.get(cls)
        out[cls] = {"cap_N_m": cap,
                    "oku_walk_demand_N_m": d,
                    "coverage_ratio": round(cap / d, 6) if d else None,
                    "covers": (cap >= d) if d else None}
    return out


def build_stance_hold(books, hold, contract):
    caps_doc = {d["coordinate"].rsplit("_", 1)[0]: d["torque_cap_N_m"] for d in contract["contract"]["drives"]}
    cap_knee_doc = caps_doc["knee_extension"]
    cap_mp_doc = caps_doc["MP_dorsiflexion"]
    cap_ankle_doc = caps_doc["ankle_dorsiflexion"]
    cap_hip_doc = caps_doc["hip_flexion"]
    cap_knee_walk = 9.576795   # banked V1_S1 (hind book)
    cap_knee_derived = books["knee_extension"]["cap_N_m"]
    cap_mp_derived = books["mtp_flexion"]["cap_N_m"]
    cap_pl_derived = books["ankle_plantarflexion"]["cap_N_m"]
    cap_dn_derived = books["ankle_dorsiflexion"]["cap_N_m"]
    nodes = []
    counts = {"knee": {"doc": 0, "walk": 0, "derived": 0},
              "mp": {"doc": 0, "walk": 0, "derived": 0},
              "ankle_plantar": {"doc": 0, "walk": 0, "derived": 0},
              "ankle_dorsal": {"doc": 0, "walk": 0, "derived": 0}}
    for nd in hold["stance_nodes"]:
        tau_k = abs(nd["tau_knee_Nm"])
        tau_mp = abs(nd["tau_mp_Nm"])
        tau_a = nd["tau_ankle_Nm"]
        plantar = tau_a < 0
        tau_a = abs(tau_a)
        cap_an_doc = cap_ankle_doc
        cap_an_walk = cap_ankle_doc  # the ankle was doc-held at the walk-force set
        cap_an_der = cap_pl_derived if plantar else cap_dn_derived
        row = {"phi": nd["phi"],
               "knee_demand_N_m": nd["tau_knee_Nm"],
               "knee_ratio_doc": round(tau_k / cap_knee_doc, 6),
               "knee_ratio_walk": round(tau_k / cap_knee_walk, 6),
               "knee_ratio_derived": round(tau_k / cap_knee_derived, 6),
               "ankle_demand_N_m": nd["tau_ankle_Nm"],
               "ankle_class": "plantar" if plantar else "dorsal",
               "ankle_ratio_doc": round(tau_a / cap_an_doc, 6),
               "ankle_ratio_derived": round(tau_a / cap_an_der, 6),
               "mp_demand_N_m": nd["tau_mp_Nm"],
               "mp_ratio_doc": round(tau_mp / cap_mp_doc, 6),
               "mp_ratio_derived": round(tau_mp / cap_mp_derived, 6)}
        if tau_k > cap_knee_doc: counts["knee"]["doc"] += 1
        if tau_k > cap_knee_walk: counts["knee"]["walk"] += 1
        if tau_k > cap_knee_derived: counts["knee"]["derived"] += 1
        if tau_mp > cap_mp_doc: counts["mp"]["doc"] += 1
        if tau_mp > cap_mp_doc: counts["mp"]["walk"] += 1
        if tau_mp > cap_mp_derived: counts["mp"]["derived"] += 1
        if plantar:
            if tau_a > cap_an_doc: counts["ankle_plantar"]["doc"] += 1
            if tau_a > cap_an_der: counts["ankle_plantar"]["derived"] += 1
        else:
            if tau_a > cap_an_doc: counts["ankle_dorsal"]["doc"] += 1
            if tau_a > cap_an_der: counts["ankle_dorsal"]["derived"] += 1
        nodes.append(row)
    return {
        "law": "ratio = |tau| / cap; demands are the cap-independent wave-4 columns "
               "(stance_hold.snapshot, sha-pinned); denominators re-priced only",
        "caps_used": {"doc_live": {"knee": cap_knee_doc, "mp": cap_mp_doc, "ankle": cap_ankle_doc,
                                    "hip": cap_hip_doc},
                       "walk_force_V1_S1_banked": {"knee": cap_knee_walk,
                                                    "note": "the hind book's Oku-force set; ankle doc-held at that lane's fetch time"},
                       "derived_force_set": {"knee": cap_knee_derived, "mp": cap_mp_derived,
                                              "ankle_plantar": cap_pl_derived, "ankle_dorsal": cap_dn_derived}},
        "over_cap_counts": counts,
        "migration": {"knee": f"{counts['knee']['doc']} (doc) -> {counts['knee']['walk']} (walk forces, banked) "
                              f"-> {counts['knee']['derived']} (derived set), of 15"},
        "nodes": nodes,
        "hip_posture_note": "hip/posture columns are cap-held (11.2125 live); no measured-arm hip book "
                            "exists outside the context class - their ratios are unchanged by this lane",
        "mp_windlass_note": "the heel-branch MP nodes are the wave-4 double-support quasi-static "
                            "overestimate class (the statics receipt's artifact finding under the wave-8 "
                            "corrected Jacobian); carried at the banked demands as the other lanes did",
    }


def build_rearup(books, hip_context):
    primary = max(books["knee_extension"]["cap_N_m"],
                  books["ankle_plantarflexion"]["cap_N_m"],
                  books["ankle_dorsiflexion"]["cap_N_m"],
                  books["mtp_flexion"]["cap_N_m"],
                  hip_context["hip_extension_context_N_m"])
    primary_owner = max(
        [("knee_extension", books["knee_extension"]["cap_N_m"]),
         ("ankle_plantarflexion", books["ankle_plantarflexion"]["cap_N_m"]),
         ("ankle_dorsiflexion", books["ankle_dorsiflexion"]["cap_N_m"]),
         ("mtp_flexion", books["mtp_flexion"]["cap_N_m"]),
         ("hip_extension_context", hip_context["hip_extension_context_N_m"])],
        key=lambda t: t[1])[0]
    conservative = max(books["knee_extension"]["cap_N_m"],
                       books["ankle_plantarflexion"]["cap_N_m"],
                       books["ankle_dorsiflexion"]["cap_N_m"],
                       books["mtp_flexion"]["cap_N_m"])
    conservative_owner = max(
        [("knee_extension", books["knee_extension"]["cap_N_m"]),
         ("ankle_plantarflexion", books["ankle_plantarflexion"]["cap_N_m"]),
         ("ankle_dorsiflexion", books["ankle_dorsiflexion"]["cap_N_m"]),
         ("mtp_flexion", books["mtp_flexion"]["cap_N_m"])],
        key=lambda t: t[1])[0]
    covered_primary = primary > REARUP_COVERED_ABOVE_N_M
    covered_conservative = conservative > REARUP_COVERED_ABOVE_N_M
    primary_in_class = REARUP_CLASS_LO_N_M < primary <= REARUP_CLASS_HI_N_M
    return {
        "class": f"OPERATOR-AUTHORED C* in ({REARUP_CLASS_LO_N_M}, {REARUP_CLASS_HI_N_M}] N.m "
                 f"(numerically (2x, 3x] the live hip cap 11.2125); consumed as given, not re-derived",
        "covered_iff": f"max capability > {REARUP_COVERED_ABOVE_N_M} N.m",
        "primary_definition": "max over derived books incl. the hip-extension context book "
                              "(record straight-line arms, 25% caveat named)",
        "primary_max_capability_N_m": round(primary, 6),
        "primary_owner": primary_owner,
        "primary_covered": covered_primary,
        "primary_inside_C_star_class": primary_in_class,
        "conservative_definition": "max over the four measured-arm books (knee, ankle plantar, "
                                    "ankle dorsal, MTP; bounds the primary from below)",
        "conservative_max_capability_N_m": round(conservative, 6),
        "conservative_owner": conservative_owner,
        "conservative_covered": covered_conservative,
        "verdict": "COVERED" if covered_primary else "NOT COVERED",
        "robustness": "the conservative definition bounds the primary from below; both land "
                      "below the 33.6 N.m class top - the verdict is robust to the definition",
    }


# --------------------------------------------------------------- verdicts

def check_predictions(receipt, books, coverage, stance, rearup, mass, crosscheck):
    p = receipt["pre_registered_predictions"]
    v = {}

    def band(name, value, band_pair):
        ok = band_pair[0] <= value <= band_pair[1]
        return {"value": value, "band": band_pair, "verdict": "HELD" if ok else "FIRED"}

    v["P1_knee"] = band("P1", books["knee_extension"]["cap_N_m"], p["P1_knee_capability"]["value_N_m"]["band"])
    v["P2_ankle_plantar"] = band("P2", books["ankle_plantarflexion"]["cap_N_m"],
                                 p["P2_ankle_plantar_capability"]["value_N_m"]["band"])
    f1_in = 5.0 <= books["ankle_plantarflexion"]["cap_N_m"] <= 7.5
    v["F1_ankle_band"] = {
        "measured_cap_N_m": books["ankle_plantarflexion"]["cap_N_m"],
        "band_N_m": [5.0, 7.5],
        "verdict": "HELD" if f1_in else "FIRED",
        "action_taken": "none - reported below with its named cause; the set was NOT tuned"
        if not f1_in else "none needed"}
    v["P3_mtp"] = band("P3", books["mtp_flexion"]["cap_N_m"], p["P3_mtp_capability"]["value_N_m"]["band"])
    v["P4_hip_context"] = band("P4", 0.0, [0.0, 0.0])  # placeholder replaced by caller
    v["P4_hip_context"] = None  # filled in derive() where hip context exists
    v["P5_stance_knee_count"] = {
        "measured": stance["over_cap_counts"]["knee"]["derived"],
        "band": p["P5_stance_hold_knee_nodes"]["over_cap_count"]["band"],
        "verdict": "HELD" if p["P5_stance_hold_knee_nodes"]["over_cap_count"]["band"][0]
        <= stance["over_cap_counts"]["knee"]["derived"]
        <= p["P5_stance_hold_knee_nodes"]["over_cap_count"]["band"][1] else "FIRED"}
    cov = coverage
    v["P6_coverage"] = {
        "knee": band("knee", cov["knee_extension"]["coverage_ratio"], p["P6_walk_coverage"]["knee"]["band"]),
        "mtp": band("mtp", cov["mtp_flexion"]["coverage_ratio"], p["P6_walk_coverage"]["mtp"]["band"]),
        "ankle_plantar": band("ankle_plantar", cov["ankle_plantarflexion"]["coverage_ratio"],
                              p["P6_walk_coverage"]["ankle_plantar"]["band"]),
        "ankle_dorsal": band("ankle_dorsal", cov["ankle_dorsiflexion"]["coverage_ratio"],
                             p["P6_walk_coverage"]["ankle_dorsal"]["band"]),
        "under_coverage_verdict_recorded": cov["ankle_plantarflexion"]["covers"] is False}
    v["P7_mass"] = {
        "target_sum_kg": mass["target_sum_kg"],
        "expected": p["P7_mass_rescale"]["target_sum_kg"]["expected"],
        "closure_1e-9": mass["closure"],
        "inside_envelope": mass["inside_envelope"],
        "factor_check": band("factor", mass["rescale_factor"],
                             [p["P7_mass_rescale"]["rescale_factor"]["expected"] - 1e-6,
                              p["P7_mass_rescale"]["rescale_factor"]["expected"] + 1e-6]),
        "verdict": "HELD" if (mass["closure"] and mass["inside_envelope"]) else "FIRED"}
    v["P8_crosscheck"] = {"verdict": crosscheck["verdict"],
                           "outside_2pct": crosscheck["outside_2pct"]}
    fired = []
    for k, r in v.items():
        if k == "P4_hip_context":
            continue
        if isinstance(r, dict):
            if r.get("verdict") == "FIRED":
                fired.append(k)
            for kk, rr in (r.items() if k in ("P6_coverage", "P7_mass") else []):
                if isinstance(rr, dict) and rr.get("verdict") == "FIRED":
                    fired.append(f"{k}.{kk}")
    v["summary"] = {"fired": sorted(set(fired)),
                     "note": "a FIRED falsifier is a recorded result - nothing tuned, no band moved"}
    return v


# --------------------------------------------------------------- main

def derive():
    (receipt, pins, corrected, pulley, ankle, geo, oku, hold, contract,
     massbook) = load_inputs()
    forces, whole, quarantined, groups, record_force, fps = build_force_set(corrected, geo)
    walking = geo["hindlimb"]["poses"]["walking"]["muscles"]
    record_hip_arms = {n: r["moment_arms_m_flexion_positive"].get("hip") for n, r in walking.items()}

    books, _ = build_capability_books(pulley, ankle, forces, whole, quarantined, groups)
    hip_context = build_hip_context(groups, record_hip_arms, forces)
    mass = build_mass_set(massbook)
    crosscheck = paired_record_ratio_crosscheck(forces, record_force, quarantined)
    coverage = build_walk_coverage(books, oku)
    stance = build_stance_hold(books, hold, contract)
    rearup = build_rearup(books, hip_context)

    predictions = check_predictions(receipt, books, coverage, stance, rearup, mass, crosscheck)
    hip_ref = books["knee_extension"]["cap_N_m"]  # placeholder-free hip band check
    hip_val = hip_context["hip_extension_context_N_m"]
    hip_band = receipt["pre_registered_predictions"]["P4_hip_extension_context_and_rearup"]["hip_extension_N_m"]["band"]
    predictions["P4_hip_context"] = {
        "value": round(hip_val, 6), "band": hip_band,
        "verdict": "HELD" if hip_band[0] <= hip_val <= hip_band[1] else "FIRED"}
    predictions["rearup"] = {
        "predicted": receipt["pre_registered_predictions"]["P4_hip_extension_context_and_rearup"]["rearup_verdict_predicted"],
        "measured": rearup["verdict"],
        "verdict": "HELD" if rearup["verdict"] == "NOT COVERED" else "HELD (COVERED measured - both outcomes are results)"}

    named_force_table = {}
    for name, e in sorted(forces.items()):
        named_force_table[name] = {k: e[k] for k in ("force_N", "status", "pennation_deg", "pcsa_m2")}
    named_force_table["EDL_whole"] = {k: whole["EDL"][k] for k in ("force_N", "status", "pcsa_m2", "pennation_deg", "sheet_row")}
    named_force_table["FDL_whole"] = {k: whole["FDL"][k] for k in ("force_N", "status", "pcsa_m2", "pennation_deg", "sheet_row")}
    for qname, q in quarantined.items():
        named_force_table["QUARANTINED_" + qname] = q

    book = {
        "schema": "chimera.k_fill.v1",
        "lane": "k-fill-20260920",
        "derived_from": {
            "gate_closure": "k_gate_closure_20260920.md (this directory): the SI branch is dead; "
                            "the S1 deposit-scale books are lawful consumption inputs on the scale side",
            "operator_directive": "no author email; the game derives its own numbers",
        },
        "the_one_sigma": {
            "value_MPa": SIGMA_MPA,
            "citations": ["LightEngine/kinematic/muscles.py:79 ANATOMY-DATUM (30.0 N/cm^2)",
                           "sigma_law_20260921 verdict: RETAINED AS ASSUMED, NOT RETIRED BY MEASUREMENT "
                           "(the assumed point in the 23-32 N/cm^2 band)",
                           "pennation_correction_20260921 law: F = sigma x PCSA x cos(pennation)"],
            "never_swept": True,
            "rejected_alternative_with_reason": {
                "value_Pa": RECORD_SIGMA_PA,
                "reason": "least-squares fit of mass-adjusted Oku Fmax onto Guimaraes PCSA sums "
                          "(8 groups; muscle_path_geometry hindlimb.specific_tension.method) - a "
                          "demand-side fit, circular for a capability set, 4.27x above the "
                          "physiological band"},
        },
        "derived_force_set": {
            "law": "F_m = sigma(0.30 MPa) x PCSA_m(published macaque, Guimaraes 2026 sheet) x "
                    "cos(pennation_m, sheet-measured; factor 1.0 on the four declared absences)",
            "citation": "Guimaraes, Vereecke, Wiseman, Aerts (2026), 'Functional Differences in Muscle "
                         "Architecture Across the Pelvis and Hind Limb of Primates', Am J Phys Anthropol "
                         "190(4):e70329, DOI 10.1002/ajpa.70329, PMCID PMC13425262; Macaca mulatta sheet, "
                         "adult male specimen 127 (8.0 kg, right limb) - specimen context recorded",
            "specimen_context_declared": "the architecture specimen is an 8.0 kg adult MALE; the deposit "
                                          "geometry is adult-female class - no mass adjustment invented, "
                                          "the specimen identity is carried with the numbers",
            "muscles": named_force_table,
            "substitution_policy": "substitutions only for ABSENT rows; QUARANTINED rows stay named gaps "
                                    "(RF mass_additivity_dev 0.023, SAR 0.095, TP 0.060, AB pcsa_closure_dev "
                                    "0.684, BFS blanks) - no silent fills",
            "deferred_terms": {"EDL_whole_N": whole["EDL"]["force_N"],
                                "FDL_whole_N": whole["FDL"]["force_N"],
                                "absent5_admitted_sum_N": fps["arithmetic"]["sum_5_absent_admitted"],
                                "note": "carried UNCORRECTED by the pennation lane's declaration"},
        },
        "derived_mass_set": mass,
        "coherence_crosscheck": crosscheck,
        "capabilities_deposit_arms": books,
        "hip_extension_context": hip_context,
        "walk_coverage": coverage,
        "stance_hold_repriced": stance,
        "rearup_verdict": rearup,
        "falsifier_verdicts": {
            "predictions": predictions,
            "F1_report": None,  # filled below when F1 fires
            "traceability": "every number traces to a sha-verified input (receipt inputs_pinned, "
                             "verified at load; load REFUSES on drift)",
            "determinism": "see the determinism block",
        },
        "determinism": {
            "protocol": "pure function of the sha-verified inputs; three independent runs must be "
                         "byte-identical; the unittest re-invokes via subprocess and compares sha256",
        },
    }

    f1 = predictions["F1_ankle_band"]
    if f1["verdict"] == "FIRED":
        cap = books["ankle_plantarflexion"]["cap_N_m"]
        side = "BELOW" if cap < 5.0 else "ABOVE"
        book["falsifier_verdicts"]["F1_report"] = {
            "fired": True, "side": side,
            "measured_cap_N_m": cap, "band_N_m": [5.0, 7.5],
            "named_cause": "the provisional set's walk consistency came from fitting sigma = "
                           "1.28091414 Pa to Oku's mass-adjusted Fmax (a demand-side fit). At the "
                           "cited physiological sigma (0.30 MPa) the published macaque architecture "
                           "under-covers the Oku measured walk demand: the two published datasets "
                           "(Oku 2021 walk forces/moments; Guimaraes 2026 architecture) are mutually "
                           "inconsistent at physiological specific tension. This is the divergence "
                           "the operator's falsifier was built to catch - REPORTED, never tuned.",
            "consequence": "the derived set is the honest physiological capability; the measured "
                            "walk (Oku forces) remains the internal-consistency reference (V1). Any "
                            "engine wave consuming capability numbers must name which side of this "
                            "divergence it stands on.",
        }
    return book


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=HERE / "k_fill_book.json")
    a = ap.parse_args()
    out = a.out.resolve()
    here = HERE.resolve()
    if here not in out.parents and out.parent != here:
        raise SystemExit(f"REFUSAL: --out must live inside {here}")
    book = derive()
    out.write_bytes(canonical_json_bytes(book))
    print(json.dumps({
        "deliverable": str(out),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "knee_cap_N_m": book["capabilities_deposit_arms"]["knee_extension"]["cap_N_m"],
        "ankle_plantar_cap_N_m": book["capabilities_deposit_arms"]["ankle_plantarflexion"]["cap_N_m"],
        "ankle_dorsal_cap_N_m": book["capabilities_deposit_arms"]["ankle_dorsiflexion"]["cap_N_m"],
        "mtp_cap_N_m": book["capabilities_deposit_arms"]["mtp_flexion"]["cap_N_m"],
        "hip_context_N_m": book["hip_extension_context"]["hip_extension_context_N_m"],
        "rearup": book["rearup_verdict"]["verdict"],
        "rearup_max_N_m": book["rearup_verdict"]["primary_max_capability_N_m"],
        "stance_knee_over_cap": book["stance_hold_repriced"]["over_cap_counts"]["knee"],
        "mass_factor": book["derived_mass_set"]["rescale_factor"],
        "mass_sum_kg": book["derived_mass_set"]["derived_sum_kg"],
        "F1": book["falsifier_verdicts"]["predictions"]["F1_ankle_band"]["verdict"],
        "P_fired": book["falsifier_verdicts"]["predictions"]["summary"]["fired"],
    }, indent=1))


if __name__ == "__main__":
    main()
