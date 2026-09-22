"""packet.py -- assemble the failure-analysis packet (one machine pass).

READ-ONLY over the trace; the slice is a causal projection (decisions -> forces
-> contacts -> death) that preserves tick ordering.  It never cuts trace
sections and never proposes a law -- the interventions are discriminating
probes, and the law synthesis stays with the wave lane (the CEGIS split).
"""
from __future__ import annotations

import re

from . import divergence as _div
from . import energy as _energy
from . import eras as _eras
from . import falsifiers as _fals
from . import interventions as _intv
from . import signature as _sig
from .trace_io import Trace, parse_stdout_census


def wave_of_receipt(receipt_path: str, lane: str) -> int:
    m = re.search(r"wave[_-]?(\d+)", receipt_path, re.IGNORECASE) or \
        re.search(r"wave[_-]?(\d+)", lane or "", re.IGNORECASE)
    return int(m.group(1)) if m else None


def build_packet(trace_path: str, stdout_path: str, receipt_path: str,
                 reference_trace=None, reference_stdout=None,
                 prior_library=None, prior_waves_through=None,
                 tick_hz: float = 300.0, reference_role: str = "baseline") -> dict:
    tr = Trace(trace_path)
    census = parse_stdout_census(stdout_path)
    receipt = _fals.Receipt(receipt_path)
    letters = _fals.evaluate_letters(receipt.falsifier_letters(), census)
    fired_first = _fals.first_fired(letters)

    eras = _eras.build_era_table(tr)
    drains = _eras.find_unload_drains(tr, eras)
    folds = _eras.find_capacity_folds(tr, eras)

    ref = Trace(reference_trace) if reference_trace else None
    ref_census = parse_stdout_census(reference_stdout) if reference_stdout else None
    diverge = _div.earliest_divergence(tr, ref) if ref is not None else None

    # the launch-grid divergence is a DEATH seed only against a BASELINE (the
    # accepted predecessor); against a PARENT law the calendar changes are the
    # amendment under test -- reported, never attributed.
    drift = None
    if ref is not None and reference_role == "baseline":
        drift = _eras.find_launch_drift(tr, ref)
    death_info = _eras.classify_death(tr, census, letters, eras, drains, folds,
                                      chain_start_tick=(diverge or {}).get("first_tick"),
                                      launch_drift=drift)
    fired_classes = [c for c in death_info["fired_classes"]]

    era_rows = _energy.era_work_table(tr, ref, eras, dt=1.0 / tick_hz)
    comp_deltas = _energy.matched_component_deltas(tr, ref) if ref is not None else []
    worst = _energy.worst_balance(tr)

    shape = _sig.slice_shape(death_info, eras, diverge or {}, fired_classes)
    sig = _sig.signature_sha16(shape)
    priors, max_sim = ([], 0.0)
    if prior_library:
        limit = prior_waves_through
        if limit is None:
            w = wave_of_receipt(receipt_path, receipt.lane)
            limit = w if w is not None else 10 ** 9
        lib = _sig.load_library(prior_library, limit)
        priors, max_sim = _sig.match_priors(shape, lib)

    death_tick = census.get("refused_tick") or (tr.refusals[0][0] if tr.refusals else None)
    slice_rows = _dependency_slice(tr, eras, era_rows, death_tick, window=6)

    pkt = dict(
        schema="chimera-failure-packet-v1",
        run=dict(trace=trace_path, trace_sha256=tr.sha256,
                 stdout=stdout_path, stdout_sha256=census["sha256"],
                 receipt=receipt_path, lane=receipt.lane, base=receipt.base,
                 receipt_pass=receipt.pass_flag,
                 census=dict(refused_tick=census.get("refused_tick"),
                             refusal=census.get("refusal"),
                             worst_ledger_J=census.get("worst_ledger_J"),
                             checks=census.get("checks"), n_reds=census.get("n_reds"))),
        first_fired_falsifier=fired_first,
        falsifier_letters=letters,
        death=dict(tick=death_tick, death_class=death_info["death_class"],
                   seeds=[dict(seed=s["seed"],
                               era=([s["era"]["leg"], s["era"]["t0"], s["era"]["td"]] if s["era"] else None),
                               waive=s.get("waive"),
                               drift=({k: s["drift"][k] for k in
                                       ("leg", "launch_tick", "reference_tick", "delta",
                                        "propagation", "graze_at_completion", "evidence_rows")}
                                      if s.get("drift") else None))
                          for s in death_info["seeds"]],
                   reference_role=reference_role),
        divergence=diverge,
        era_table=[dict(leg=e["leg"], t0=e["t0"], td=e["td"], length=e["length"],
                        cls=e["cls"], on_grid=e["on_grid"],
                        era_max_pm=e["era_max_pm"], band=_eras.era_graze_class(e),
                        stall_arith=e["stall_arith"], stall_pose=e["stall_pose"],
                        clear_tick=e["clear_tick"],
                        prev_other_fire=e["prev_other_fire"],
                        carrier_drain_onset=e.get("carrier_drain_onset"),
                        capacity_fold=e.get("capacity_fold")) for e in eras],
        dependency_slice=slice_rows,
        energy=dict(worst_balance=worst,
                    era_work_top=era_rows[:8],
                    matched_component_deltas=comp_deltas),
        interventions=_intv.build_interventions(death_info, era_rows),
        replay=dict(scene_note="the run's own committed scene (the receipt's scope letter pins gait_scene.py "
                               "byte-untouched; regenerate per the receipt's harness) + the trace's first-walk run",
                    death_tick=death_tick,
                    harness="the declared raw-byte run harness (run_and_hash*.py; the PowerShell '>' redirect "
                            "re-encodes UTF-16 and is never used)",
                    command=f"python <lane>/.tmp/<wN>_receipt/run_and_hash.py gait_unit[_trace].exe scene.json out",
                    trace_first_walk_line=tr.first_walk_line.strip() if tr.first_walk_line else None),
        signature=dict(shape=shape, sha16=sig,
                       prior_matches=priors, prior_similarity_max=max_sim,
                       prior_waves_through=(prior_waves_through if prior_waves_through is not None
                                            else wave_of_receipt(receipt_path, receipt.lane)),
                       library=prior_library),
    )
    return pkt


def _dependency_slice(tr: Trace, eras: list, era_rows: list, death_tick, window: int = 6) -> list:
    """Slice BACK from the death tick: per era, decision -> forces -> contacts
    -> outcome.  A read-only projection in trace order."""
    relevant = [e for e in eras if e["td"] is None or e["td"] <= (death_tick or tr.max_tick())]
    chosen = relevant[-window:]
    rows = []
    for e in chosen:
        row = next((r for r in era_rows if r["t0"] == e["t0"] and r["leg"] == e["leg"]), None)
        forces = {}
        for k in range(8):
            taus = [tr.dvq[(t, k)][0] for t in range(e["t0"], e["td"] or e["t0"] + 1) if (t, k) in tr.dvq]
            caps = [tr.dvq[(t, k)][1] for t in range(e["t0"], e["td"] or e["t0"] + 1) if (t, k) in tr.dvq]
            if taus:
                pinned = sum(1 for tau, cap in zip(taus, caps) if cap > 0 and tau >= cap - 1e-9)
                forces[k] = dict(tau_max=round(max(taus), 4), pinned_ticks=pinned)
        pms = [tr.pairmin(t, e["leg"]) for t in range(e["t0"], e["td"] or e["t0"] + 1)]
        pms = [p for p in pms if p is not None]
        carrier = 1 - e["leg"]
        crxns = [tr.carrier_rxn(t, carrier) for t in range(e["t0"], e["td"] or e["t0"] + 1)]
        crxns = [r for r in crxns if r is not None]
        waives = [(wl, wt, dl) for (wl, wt, dl, *_r) in
                  [w for w in tr.waivefires if e["leg"] == 1 - w[0] and e["t0"] < w[1] and (e["td"] or 10 ** 9) > w[1]]]
        rows.append(dict(
            era=f"leg{e['leg']} [{e['t0']},{e['td']})",
            decision=dict(fire=e["raw_fire"], waivefires_inside=waives),
            forces=dict(per_drive={str(k): v for k, v in sorted(
                forces.items(), key=lambda kv: -kv[1]["tau_max"])[:3]}),
            contacts=dict(pairmin_min=(min(pms) if pms else None),
                          pairmin_max=(max(pms) if pms else None),
                          band=_eras.era_graze_class(e),
                          carrier_rxn_min=(min(crxns) if crxns else None),
                          carrier_drain_onset=e.get("carrier_drain_onset")),
            outcome=dict(td=e["td"], length=e["length"], on_grid=e["on_grid"],
                         stall_arith=e["stall_arith"], stall_pose=e["stall_pose"],
                         clear_tick=e["clear_tick"],
                         work_delta_top=(dict(drive=row["top_delta_drive"], J=row["top_delta"]) if row and row["top_delta_drive"] is not None else None),
                         work_J_no_match=(max(row["work_J"].values(), key=abs) if row and row["top_delta"] is None and row else None)),
        ))
    return rows


def render_text(pkt: dict) -> str:
    """The compact human-readable rendering (what the operator reads first)."""
    L = []
    r = pkt["run"]
    L.append(f"RUN  {r['trace']} (trace sha {r['trace_sha256'][:12]}...)")
    L.append(f"     refused_tick={r['census']['refused_tick']} worst_ledger_J={r['census']['worst_ledger_J']} "
             f"checks={r['census']['checks']} reds={r['census']['n_reds']}  lane={r['lane']}")
    ff = pkt["first_fired_falsifier"]
    if ff:
        L.append(f"FIRST FIRED FALSIFIER: {ff['letter']} [{ff['kind']}] bound={ff['bound']} measured={ff['measured']}")
        L.append(f"  clause: {ff['clause']}")
    else:
        L.append("FIRST FIRED FALSIFIER: none (the preregistered numeric letters all passed)")
    d = pkt["death"]
    L.append(f"DEATH: tick {d['tick']} class {d['death_class']}")
    for s in d["seeds"]:
        if s.get("drift"):
            dr = s["drift"]
            L.append(f"  seed {s['seed']}: {'LR'[dr['leg']]}@{dr['launch_tick']} vs baseline "
                     f"{dr['reference_tick']} (delta {dr['delta']:+d}, propagated {dr['propagation']}, "
                     f"graze-at-completion={dr['graze_at_completion']})")
        else:
            L.append(f"  seed {s['seed']} era leg{s['era'][0]} [{s['era'][1]},{s['era'][2]}) waive={s.get('waive')}")
    dv = pkt["divergence"]
    if dv:
        L.append(f"DIVERGENCE vs reference: first tick {dv['first_tick']} ({dv['first_family']}), "
                 f"calendar {dv['first_calendar_tick']}, energy {dv['first_energy_tick']}")
    L.append("SLICE (back from the death):")
    for row in pkt["dependency_slice"]:
        oc = row["outcome"]
        cn = row["contacts"]
        L.append(f"  {row['era']} len={oc['length']} band={cn['band']} clear@{oc['clear_tick']} "
                 f"arith_stall={oc['stall_arith']} pose_stall={oc['stall_pose']} "
                 f"pm[{cn['pairmin_min']:.2e},{cn['pairmin_max']:.2e}]"
                 + (f" work_delta_d{oc['work_delta_top']['drive']}={oc['work_delta_top']['J']:+.4f}J"
                    if oc.get("work_delta_top") else
                    (f" work={oc['work_J_no_match']:.4f}J (no reference match)" if oc.get("work_J_no_match") is not None else "")))
    en = pkt["energy"]
    L.append(f"ENERGY: worst |bal| {en['worst_balance']['value']:.6f} @ tick {en['worst_balance']['tick']}")
    for row in en["era_work_top"][:4]:
        top = row["top_delta_drive"]
        if top is not None:
            L.append(f"  era leg{row['leg']} [{row['t0']},{row['td']}) drive_{top} work {row['work_J'][top]:+.4f}J "
                     f"vs ref {row['ref_work_J'][top]:+.4f}J delta {row['top_delta']:+.4f}J")
        else:
            k = max(row["work_J"], key=lambda kk: abs(row["work_J"][kk]))
            L.append(f"  era leg{row['leg']} [{row['t0']},{row['td']}) drive_{k} work {row['work_J'][k]:+.4f}J (no reference match)")
    L.append("INTERVENTIONS (discriminating probes, not repairs):")
    for p in pkt["interventions"]:
        L.append(f"  {p['rank']}. {p['probe'].split(':')[0]}")
        for a, b in p["separates"].items():
            L.append(f"     {a} => {b}")
    sg = pkt["signature"]
    L.append(f"SIGNATURE {sg['sha16']}  priors<={sg['prior_waves_through']}")
    for m in sg["prior_matches"]:
        L.append(f"  wave {m['wave']}: {m['face']} [{m['death_class']}] sim={m['similarity']} {'; '.join(m['why'])}")
    return "\n".join(L)
