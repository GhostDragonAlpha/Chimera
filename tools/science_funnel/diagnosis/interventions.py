"""interventions.py -- ranked DISCRIMINATING INTERVENTIONS (Astra P2: experiments,
not proposed repairs).

Each probe is a counterfactual replay at the named scene+tick that separates
competing explanations of the death.  A probe names what each outcome would
mean; it never asserts a fix.  Templates are keyed by the detected seed class;
every parameter (ticks, drives, bands) is read from the slice.
"""
from __future__ import annotations

from .eras import KBAND, KTOUCH, TAIR


def _graze_misfire_probes(seeds, era, top_drive):
    t_clear = era["clear_tick"]
    probes = [
        dict(rank=1,
             probe="RELEASE-BAND CLAMP (one quantum): re-decide the hold read at the tick-start rows "
                   f"[{t_clear - 1},{t_clear}] with the release band widened to kTouch+2*kReleaseBand "
                   f"({KTOUCH + 2 * (KBAND - KTOUCH):.2e} band edge {2 * KBAND - KTOUCH:.2e}); the era's max pair-min "
                   f"was {era['era_max_pm']:.3e}, inside (one-quantum-past) the shipped band {KBAND:.2e}.",
             separates={"A contact-timing": "the pad genuinely left the band -> the waive STILL fires at "
                        f"{t_clear} and the death is unchanged",
                        "B band-edge artifact": "the clearing was a one-quantum graze -> the waive CLOSES and the "
                        "calendar does not scatter"},
             replay=dict(ticks=[t_clear - 1, t_clear], read="pairmin", clamp="treat > kTouch+kReleaseBand as OUT")),
        dict(rank=2,
             probe=f"CALENDAR-ARITHMETIC GUARD: at the {t_clear} decision force the era class to the arithmetic "
                   f"answer (launch {era['t0']} - prev_other_fire {era['prev_other_fire']} == tair {TAIR} => STALL); "
                   "the (a)-waive may only open in a REAL era.",
             separates={"B calendar-arithmetic owner": "both stall-era misfires close and the era-work sum pays the "
                        "ledger back by construction (the eras never exist)",
                        "A/C": "the misfire persists -> the read or the forces own it"},
             replay=dict(ticks=[t_clear], decision="waive_open", clamp="stall_arith==True blocks the waive")),
        dict(rank=3,
             probe=f"FORCE FREEZE: hold drive_{top_drive}'s torque at its era-entry value over "
                   f"[{era['t0']},{era['td']}) (the era's top work-delta drive).",
             separates={"C force-allocation": "the pad lands on-grid and never grazes past the band -> the share "
                        "allocation owns the stall",
                        "A/B": "the era still grazes/clears at the same tick -> the read or the arithmetic owns it"},
             replay=dict(ticks=list(range(era["t0"], era["td"])), drive=int(top_drive or 4),
                         clamp="tau held at era-entry value")),
    ]
    return probes


def _stall_seed_probes(era, first_off_grid):
    t0, td = era["t0"], era["td"]
    LEG = "LR"
    fo = (f"{LEG[first_off_grid['leg']]}@{first_off_grid['t0']}" if first_off_grid else "n/a")
    probes = [
        dict(rank=1,
             probe=f"TOUCHDOWN-READ CLAMP: over [{t0},{td}) re-read the swing pad's band entry every tick-start; "
                   f"the era ran {era['length']} ticks (on-grid is 9/15/18) -- was there a band entry the td read "
                   "missed?",
             separates={"A contact-timing": "a genuine band entry exists mid-era -> the completion read owns the "
                        "stall seeding",
                        "B pose/dynamics": "no band entry until the real td -> the swing itself stalled"},
             replay=dict(ticks=list(range(t0, (td or t0 + 30))), read="pairmin",
                         clamp="band-entry decision re-evaluated per tick")),
        dict(rank=2,
             probe=f"WAIVE-OPEN CLAMP at the first off-grid fire ({fo}): block the (a)-waive's opening "
                   "at that decision and replay the calendar.",
             separates={"B calendar owner": "the downstream fires return to the 9/15/18 grid -> the waive's opening "
                        "spread the drift",
                        "C": "the grid stays drifted -> the seeding era owns it"},
             replay=dict(ticks=[first_off_grid["t0"] if first_off_grid else t0], decision="waive_open",
                         clamp="blocked")),
    ]
    return probes


def _unload_drain_probes(drain):
    era = drain["era"]
    onset = drain["onset"]
    probes = [
        dict(rank=1,
             probe=f"REACTION FLOOR: clamp the carrier (leg {drain['carrier']}) pads' read rxn to its era-entry "
                   f"value from tick {onset} (the drain onset; peak {drain['peak']:.2f} N -> <0.5 N).",
             separates={"A contact-timing/read": "the hold survives to its scheduled completion -> the unload read "
                        "owns the collapse",
                        "B force-allocation": "the pads still unload under the same commands -> the share forces own it"},
             replay=dict(ticks=list(range(onset, era["td"] or onset + 12)), read="rxn", clamp="held at era-entry")),
        dict(rank=2,
             probe=f"PARTNER BAND-ENTRY TIMING: delay the swing leg's band-entry decision by one decision row past "
                   f"tick {onset} and watch the carrier's rxn.",
             separates={"A contact-timing": "the carrier recovers -> the hand-off timing owns the drain",
                        "B": "no recovery -> the unload law owns it"},
             replay=dict(ticks=[onset], decision="band_entry", clamp="+1 row")),
    ]
    return probes


def _capacity_fold_probes(fold):
    era = fold["era"]
    probes = [
        dict(rank=1,
             probe=f"CAP RAISE PROBE: raise drive_{fold['drive']}'s torque cap 10% over [{era['t0']},{era['td']}) "
                   "and replay (a probe on the capacity hypothesis, NOT a proposed law -- the cap is a banked "
                   "joint-class constant).",
             separates={"A capacity": "the target error closes -> the joint genuinely ran out",
                        "B target error": "the target error persists at equal torque -> the target derivation owns it"},
             replay=dict(ticks=list(range(era["t0"], era["td"] or era["t0"] + 12)),
                         drive=fold["drive"], clamp="cap x1.10")),
    ]
    return probes


def _calendar_drift_probes(drift):
    ta, tb = drift["launch_tick"], drift["reference_tick"]
    LEG = "LR"
    probes = [
        dict(rank=1,
             probe=f"LAUNCH-READ CLAMP: re-decide the {LEG[drift['leg']]}'s stance read at the completion rows "
                   f"[{ta - 2},{ta - 1}] with the release band edge moved one contact quantum; the drifted launch "
                   f"{LEG[drift['leg']]}@{ta} fired {abs(drift['delta'])} tick(s) "
                   f"{'late' if drift['delta'] > 0 else 'early'} vs the baseline's {tb} "
                   f"(graze-at-completion read: {drift['graze_at_completion']}).",
             separates={"A contact-read": "band-edge re-read re-fires on the baseline tick -> the graze read owned "
                        "the +1 launch",
                        "B dynamics": "the pads stay put under any band edge -> the stance forces put the pad there"},
             replay=dict(ticks=[ta - 2, ta - 1], read="pairmin", clamp="band edge one quantum")),
        dict(rank=2,
             probe=f"STANCE FORCE FREEZE: hold the launcher's stance drives' torque at their era-entry values over "
                   f"the ending era and watch whether the completion-row graze still exits the band at {ta - 1}.",
             separates={"B force-allocation": "the band exit moves -> the unload share owned the graze timing",
                        "A/C": "the exit tick is unchanged -> the read or the deadline arithmetic owns it"},
             replay=dict(ticks=[ta - 9, ta - 1], drive="stance", clamp="tau at era-entry")),
        dict(rank=3,
             probe=f"GRID RE-ANCHOR: re-fire the launch at the baseline tick {tb} (deadline arithmetic unchanged) "
                   f"and replay the calendar; the drift propagated {drift['propagation']} launches.",
             separates={"C deadline-arithmetic": "the calendar re-locks and the downstream launches follow -> the "
                        "+1 drift owned the scatter",
                        "A/B": "the grid re-scatters -> an earlier seed owns it"},
             replay=dict(ticks=[ta], decision="fire", clamp=f"fire at {tb}")),
    ]
    return probes


def build_interventions(death_info, era_work_rows):
    probes = []
    seen_heads = set()
    for s in death_info["seeds"]:
        e = s["era"]
        if e is not None:
            row = next((r for r in era_work_rows if r["t0"] == e["t0"] and r["leg"] == e["leg"]), None)
            top_drive = row["top_delta_drive"] if row else None
        else:
            top_drive = None
        if s["seed"] == "CALENDAR_DRIFT":
            new = _calendar_drift_probes(s["drift"])
        elif s["seed"] == "GRAZE_MISFIRE":
            new = _graze_misfire_probes(s, e, top_drive)
        elif s["seed"] == "STALL_SEED":
            new = _stall_seed_probes(e, death_info.get("first_off_grid_era"))
        elif s["seed"] == "UNLOAD_DRAIN":
            d = next(d for d in death_info["drains"] if d["era"] is e)
            new = _unload_drain_probes(d)
        elif s["seed"] == "CAPACITY_FOLD":
            f = next(f for f in death_info["folds"] if f["era"] is e)
            new = _capacity_fold_probes(f)
        else:
            new = []
        for p in new:
            head = p["probe"].split(":")[0]
            if head in seen_heads:
                continue
            seen_heads.add(head)
            probes.append(p)
    probes.sort(key=lambda p: p["rank"])
    for i, p in enumerate(probes, 1):
        p["rank"] = i
    return probes
