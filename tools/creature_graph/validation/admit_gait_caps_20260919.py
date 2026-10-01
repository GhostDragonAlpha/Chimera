"""Amend the gait walker's drive caps (model.dynamics.gait_walker revision 3):
the caps' provenance moves from the source model's dynamic peaks to OUR
assembly's measured quasi-static demands.

THE DERIVATION (tools/science_funnel/validation/gait_zero_20260919/
derive_stance_hold.py, receipt_wave4): the original caps are 1.25x the
source walk's measured torque peaks -- peaks recorded UNDER that walk's
dynamic (pendulum) unloading. Our entry state cannot presume that unloading
(the vault must be ESTABLISHED, and it cannot start from a pose the knee
cannot hold): measured, the knee demand is 7.28 N.m vs the 6.6 cap AT the
entry instant and 8.81-10.54 vs 6.6 through the single-support window
(phi 0.183-0.5); the walk sags monotonically from tick 0 (-0.4 J
gravitational per 10 ticks, measured in the [ledger10] energy books) and
the vault never establishes.

THE AMENDMENT LAW: cap_j = 1.25 x max over the single-support stance window
of |tau_j_static(phi)| -- every input measured from the admitted bytes (the
zero-mapped tables, the Table-1 segments, the rolling-law contact).

  knee:  1.25 x 10.54 = 13.18  (was 6.64)
  ankle: 1.25 x  7.21 =  9.01  (was 7.40)
  hip:   1.25 x  7.33 =  9.16  -> cap stays 11.22 (the current cap already exceeds)
  MP:    1.25 x  0.01 =  0.01  -> cap stays 0.88
  posture: 1.25 x 8.14 = 10.18 -> cap stays 11.22

PREDICTION: the walk no longer sags from tick 0 (the gravitational books
plateau/oscillate over the first stance), the vault establishes (KE
sustained), and the walk survives at least one full cycle (213 ticks; the
current refusal is 118).

FALSIFIERS: (1) the same <=118-tick refusal with the same sag signature --
the caps were not the binding constraint: revert and the amendment is
falsified; (2) F-G5 must stay green (the fall/stand falsifiers do not
regress); (3) the centripetal check: once the vault runs, the mid-gait knee
load should fall BACK under the old cap -- the amendment covers entry and
recovery, not a blanket raise.

Idempotent, revision-aware. Run from the checkout root:
    python -B tools/creature_graph/validation/admit_gait_caps_20260919.py
then rebuild the store, recompile the scene.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROGRAM = ROOT / "tools/creature_graph/data/authored/project_program.json"
MODEL_ID = "model.dynamics.gait_walker"

NEW_CAPS = {"hip": 11.21825, "knee": 13.175, "ankle": 9.01375, "MP": 0.88137500}
# 1.25 x [8.9746, 10.54, 7.21, 0.7051 original MP cap kept]


def main() -> int:
    payload = json.loads(PROGRAM.read_bytes().decode("utf-8-sig"))
    objects = payload["objects"]
    wid = [i for i, o in enumerate(objects) if o.get("id") == MODEL_ID]
    if not wid:
        print(f"{MODEL_ID}: REFUSAL -- record missing", file=sys.stderr)
        return 1
    rec = objects[wid[0]]
    contract = rec["physical"]["contract"]
    if "zero_map_rad" not in contract:
        print(f"{MODEL_ID}: REFUSAL -- revision 2 (zero map) must be banked first", file=sys.stderr)
        return 1
    if contract.get("cap_provenance") == "assembly_statics_v1":
        # FALSIFIER (1) FIRED (20260919 wave 5): same <=118-tick refusal, the
        # same fall depth (y=0.1345 vs 0.1343) with the doubled knee cap -- the
        # caps were never the binding constraint ([pt] trace: the entry foot
        # LIFTS at tick 0, nothing touches; the right swing leg catches; by
        # tick 60 all four points skate at 1.2 m/s under 40 N total -- the
        # splits, not a torque deficit). Per this membrane's own law: REVERT.
        for d in contract["drives"]:
            if "torque_cap_provenance_previous" in d:
                d["torque_cap_N_m"] = d.pop("torque_cap_provenance_previous")
        contract["cap_provenance"] = "source_peaks_v1_RESTORED"
        contract["cap_amendment_note"] = (
            "REVISED (wave 5, falsifier 1 fired): the assembly-statics cap amendment "
            "(knee 13.18, ankle 9.01) was banked, measured, and FALSIFIED -- the walk fell "
            "identically (tick 118, y=0.1345) with the doubled caps; the caps were not binding. "
            "Original source-peak caps restored. The binding failures are the entry-contact "
            "bounce and stance-foot skating (see receipt_wave5)."
        )
        rec["revision_note"] = (rec.get("revision_note", "") +
                                " cap amendment reverted (falsifier 1: not binding).")
        PROGRAM.write_bytes(json.dumps(payload, indent=1, ensure_ascii=False).encode("utf-8") + b"\n")
        print(f"{MODEL_ID}: amendment REVERTED (falsifier fired; source caps restored)")
        return 0
    amended = 0
    for d in contract["drives"]:
        j = d["joint"]
        new = NEW_CAPS[j]
        old = float(d["torque_cap_N_m"])
        if abs(new - old) > 1e-9:
            d["torque_cap_N_m"] = round(new, 6)
            d["torque_cap_provenance_previous"] = round(old, 6)
            amended += 1
    contract["cap_provenance"] = "assembly_statics_v1"
    contract["cap_amendment_note"] = (
        "revision 3 (20260919 wave 5): caps = 1.25x the ASSEMBLY's own quasi-static demands "
        "(derive_stance_hold.py, receipt_wave4_stance_hold.json) over the single-support window -- "
        "knee 6.64->13.18, ankle 7.40->9.01; hip/MP/posture unchanged (already above the static law). "
        "The original caps presumed the source walk's pendulum unloading, which an entry state cannot "
        "presume: the knee was 10% over cap at the entry instant and 33-60% over through the window, "
        "and the walk sagged from tick 0 (measured -0.4 J/10 ticks). Falsifiers: (1) same <=118-tick "
        "sag refusal -> revert, amendment falsified; (2) F-G5 stays green; (3) once vaulting, the "
        "mid-gait knee load should fall back under the OLD cap (the amendment covers entry/recovery)."
    )
    rec["revision_note"] = (rec.get("revision_note", "") +
                            " revision 3: drive caps re-provenanced to the assembly's measured statics (wave 5).")
    PROGRAM.write_bytes(json.dumps(payload, indent=1, ensure_ascii=False).encode("utf-8") + b"\n")
    print(f"{MODEL_ID}: revision 3 banked ({amended} drive caps amended)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
