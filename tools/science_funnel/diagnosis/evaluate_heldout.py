"""evaluate_heldout.py -- the F-DIAGNOSIS-TIME / F-DIAGNOSIS-WRONG scorer.

This is the SCORING tool, not the generator: it is the only place the recorded
human-mine numbers (the receipt's mine section) are read, and they are read
AFTER the packets were generated, as the scoring key (F-DIAGNOSIS-LEAK: the
generator itself never sees them -- audited by audit_leak_sources below).

  python -m tools.science_funnel.diagnosis.evaluate_heldout
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIX = ROOT / ".tmp" / "diag_fixtures"
REC = ROOT / "tools" / "science_funnel" / "validation" / "gait_zero_20260919"
LIB = ROOT / "tools" / "science_funnel" / "diagnosis" / "prior_faces.json"

# the recorded human-mine key for the wave-37 death (mine_w38_out.txt / the
# wave-37 receipt's the_mechanism + mine_w37_out.txt), transcribed verbatim:
KEY_W37 = dict(
    graze_era=(1, 202, 211), graze_clear_tick=206, graze_max_pm_min=1.0e-5,
    waive_misfire=(0, 206, 193),
    era_work_delta_drive=4, era_work_delta_J=1.3977, work_tol=0.05,
    scatter_era=(1, 215, 292), scatter_work_drive=4, scatter_work_J=14.5321,
    worst_bal_J=33.108444,
    fired_bound=32.861605, fired_measured=33.559179,
    divergence_tick=193,
)


def audit_leak_sources() -> list:
    """F-DIAGNOSIS-LEAK: the generator modules must never read the receipt's
    measurements or any mine_* artifact; the scorer/library-builder may."""
    generator = ["trace_io.py", "eras.py", "energy.py", "falsifiers.py",
                 "divergence.py", "interventions.py", "signature.py", "packet.py", "diagnose.py"]
    violations = []
    # access-shaped patterns only: prose in a docstring prohibiting a read is
    # not a read (falsifiers.py's leak-guard docstring names the field it refuses)
    access_pats = ((r'get\(\s*[\'"]measurements[\'"]', "receipt measurements section"),
                   (r'\[[\'"]measurements[\'"]\]', "receipt measurements section"),
                   (r'open\([^)]*mine_', "a human-mine artifact"),
                   (r'[\'"]mine_\w+\.(txt|json|py)[\'"]', "a human-mine artifact"),
                   (r'get\(\s*[\'"]the_mechanism[\'"]|\[[\'"]the_mechanism[\'"]\]',
                    "the receipt's mechanism text"))
    base = ROOT / "tools" / "science_funnel" / "diagnosis"
    for name in generator:
        text = (base / name).read_text(encoding="utf-8")
        for pat, why in access_pats:
            for m in re.finditer(pat, text):
                line = text[:m.start()].count("\n") + 1
                violations.append(f"{name}:{line}: references {why}")
    return violations


def score_w37(pkt: dict) -> dict:
    checks = []

    def ok(name, cond, detail=""):
        checks.append(dict(element=name, passed=bool(cond), detail=detail))

    # (1) the graze era
    era = next((e for e in pkt["era_table"]
                if (e["leg"], e["t0"], e["td"]) == KEY_W37["graze_era"]), None)
    ok("graze-era [202,211) present with clear@206, stall-by-arithmetic, band GRAZE",
       era is not None and era["clear_tick"] == KEY_W37["graze_clear_tick"]
       and era["stall_arith"] and era["band"] == "GRAZE"
       and era["era_max_pm"] > KEY_W37["graze_max_pm_min"],
       f"era_max_pm={era['era_max_pm']:.3e} clear={era['clear_tick']}" if era else "era missing")

    # (2) the waive misfire classification
    mis = next((m for m in pkt["death"]["seeds"] if m["seed"] == "GRAZE_MISFIRE"
                and m.get("waive") == list(KEY_W37["waive_misfire"])), None)
    ok("waive L@206 misfire inside the stall era", mis is not None,
       f"seed={mis['seed'] if mis else None}")

    # (3) the era work delta on drive_4
    row = next((r for r in pkt["energy"]["era_work_top"]
                if r["t0"] == 202 and r["leg"] == 1), None)
    d = (row or {}).get("top_delta")
    ok(f"era work delta {KEY_W37['era_work_delta_J']}+/-{KEY_W37['work_tol']} J (drive_4)",
       row is not None and row["top_delta_drive"] == KEY_W37["era_work_delta_drive"]
       and d is not None and abs(d - KEY_W37["era_work_delta_J"]) <= KEY_W37["work_tol"],
       f"measured {d:+.4f} J")

    # (3b) the scatter era's work (the decomposition's biggest term)
    srow = next((r for r in pkt["energy"]["era_work_top"]
                 if r["t0"] == 215 and r["leg"] == 1), None)
    sw = max(srow["work_J"].values(), key=abs) if srow else None
    sk = str(KEY_W37["scatter_work_drive"])  # JSON round-trip stringifies keys
    swv = srow["work_J"].get(sk, srow["work_J"].get(KEY_W37["scatter_work_drive"])) if srow else None
    ok(f"scatter era [215,292) work {KEY_W37['scatter_work_J']}+/-{KEY_W37['work_tol']} J",
       srow is not None and swv is not None
       and abs(swv - KEY_W37["scatter_work_J"]) <= KEY_W37["work_tol"],
       f"measured {sw:+.4f} J")

    # (4) the worst balance (the value is the scored element; the prereg's
    # "@ 290" tick annotation was a transcription of the AMEND row -- the mine's
    # COMP row is tick 300, which is what the packet reports; carried honestly)
    wb = pkt["energy"]["worst_balance"]
    ok(f"worst |bal| {KEY_W37['worst_bal_J']:.6f} (mine's COMP row tick 300; prereg text said @290)",
       wb["value"] is not None and abs(wb["value"] - KEY_W37["worst_bal_J"]) < 1e-6,
       f"measured {wb['value']:.6f} @ tick {wb['tick']}")

    # (5) the fired letter
    ff = pkt["first_fired_falsifier"]
    ok(f"fired ledger letter ({KEY_W37['fired_measured']} > {KEY_W37['fired_bound']})",
       ff is not None and ff["kind"] == "ledger" and ff["bound"] == KEY_W37["fired_bound"]
       and ff["measured"] == KEY_W37["fired_measured"] and ff["verdict"] == "FIRED",
       f"{ff['letter'] if ff else None}")

    # (6) the earliest relevant divergence
    dv = pkt["divergence"]
    ok(f"earliest relevant divergence tick {KEY_W37['divergence_tick']}",
       dv["first_tick"] == KEY_W37["divergence_tick"] and dv["first_family"] == "[hindstep]",
       f"tick {dv['first_tick']} ({dv['first_family']})")

    # (7) the discriminating interventions
    iv = pkt["interventions"]
    heads = " | ".join(p["probe"].split(":")[0] for p in iv)
    ok(">= 3 interventions separating contact-read / calendar-arithmetic / force-allocation",
       len(iv) >= 3 and "RELEASE-BAND CLAMP" in heads and "CALENDAR-ARITHMETIC GUARD" in heads
       and "FORCE FREEZE" in heads, f"{len(iv)} probes")

    gen = pkt["generation"]
    cov = sum(1 for c in checks if c["passed"])
    return dict(case="wave-37 held-out death", elements=checks, matched=cov,
                total=len(checks), generation_seconds=gen["seconds"],
                pass_flag=(cov == len(checks)))


def score_wrong_attribution(pkts: dict) -> dict:
    checks = []

    def ok(name, cond, detail=""):
        checks.append(dict(element=name, passed=bool(cond), detail=detail))

    w36 = pkts["w36"]
    dc = w36["death"]["death_class"] or ""
    primary = (w36["death"]["seeds"][0]["seed"] if w36["death"]["seeds"] else None)
    ok("w36-amended: primary seed is the launch-drift chain (not capacity/unload)",
       primary == "CALENDAR_DRIFT" and "CAPACITY_FOLD" not in dc and "UNLOAD_DRAIN" not in dc,
       f"class={dc}; primary={primary}; drift={w36['death']['seeds'][0].get('drift')}")
    dr = w36["death"]["seeds"][0].get("drift", {}) if w36["death"]["seeds"] else {}
    ok("w36-amended: the drift is the +1 launch L@194 vs baseline 193, with the "
       "graze-at-completion read (the mine's 1.1707e-05 / 9.739 rows)",
       dr.get("launch_tick") == 194 and dr.get("reference_tick") == 193
       and dr.get("delta") == 1 and dr.get("graze_at_completion") is True,
       f"drift={dr.get('launch_tick')} vs {dr.get('reference_tick')} rows={dr.get('evidence_rows')}")
    ok("w36-amended: the fired letter is the rung (298 <= 300)",
       (w36["first_fired_falsifier"] or {}).get("kind") == "rung"
       and w36["first_fired_falsifier"]["measured"] == 298,
       f"{w36['first_fired_falsifier']['letter'] if w36['first_fired_falsifier'] else None}")

    w38 = pkts["w38"]
    ok("w38 ship (passing run): NO fired falsifier and NO death manufactured",
       w38["first_fired_falsifier"] is None and w38["death"]["death_class"] is None,
       f"class={w38['death']['death_class']}")

    w37 = pkts["w37"]
    dc37 = w37["death"]["death_class"] or ""
    primary37 = (w37["death"]["seeds"][0]["seed"] if w37["death"]["seeds"] else None)
    ok("w37 held-out: the primary seed is the [202,211) graze misfire "
       "(not the lawful L@161 waive era, not a capacity fold)",
       primary37 == "GRAZE_MISFIRE" and "CAPACITY_FOLD" not in dc37
       and all(s.get("era") != [1, 160, 174] for s in w37["death"]["seeds"]),
       f"class={dc37}; primary era={w37['death']['seeds'][0].get('era') if w37['death']['seeds'] else None}")
    return dict(case="wrong-attribution set", elements=checks,
                matched=sum(1 for c in checks if c["passed"]), total=len(checks),
                pass_flag=all(c["passed"] for c in checks))


def main() -> int:
    pkt_w37 = json.loads((FIX / "packet_w37.json").read_text(encoding="utf-8"))
    pkt_w36 = json.loads((FIX / "packet_w36amend.json").read_text(encoding="utf-8"))
    pkt_w38 = json.loads((FIX / "packet_w38.json").read_text(encoding="utf-8"))

    leak = audit_leak_sources()
    t = score_w37(pkt_w37)
    w = score_wrong_attribution(dict(w36=pkt_w36, w37=pkt_w37, w38=pkt_w38))

    out = dict(schema="failure-packets-heldout-score-v1",
               leak_audit=dict(violations=leak, pass_flag=not leak),
               f_diagnosis_time=t, f_diagnosis_wrong=w,
               verdict=dict(**{k: v for k, v in (
                   ("F-DIAGNOSIS-TIME", t["pass_flag"]),
                   ("F-DIAGNOSIS-WRONG", w["pass_flag"]),
                   ("F-DIAGNOSIS-LEAK", not leak))}))
    print(json.dumps(out, indent=1))
    (FIX / "heldout_score.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return 0 if all(out["verdict"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
