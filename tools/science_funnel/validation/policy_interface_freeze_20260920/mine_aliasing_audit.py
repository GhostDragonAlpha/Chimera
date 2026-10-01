#!/usr/bin/env python3
"""THE ALIASING-AUDIT MINE (declared instrument; lane/policy-interface-freeze-20260920;
preregistered in PREREGISTRATION.md BEFORE the trace build and this run).

Falsifier F1 STATE-ALIASING: on the live CPU walk (the LAST walk run of the
audit trace, the mine_wave47 convention), project every tick through the FROZEN
80-field schema exactly as the deployed recipe would, then search for pairs of
ticks whose observations are BIT-IDENTICAL float32 (all 80 values) while their
labels differ in
  (a) REFLEX MODE: the hind branch (the [dvfa] br= first-sample read: t/h/d/g),
      the fore stepping clock mode (the [dvf] mode= read: 0 stance / 1 swing),
      the capture-event counter moved, the settle window [0,59] membership,
      or a hind-step fire/td, foreclk, or pawcap event on one tick and not the
      other;
  (b) CONTACT REGIME: the per-pad touch pattern (8 pads vs kTouch=1e-5, the
      machinery's own contact quantum);
  (c) DEFORMATION VELOCITY: any pad's per-tick gap delta differing by more than
      kSinkRateMax=2.349e-3 m/tick (the wave-27 mined worst sink rate), or the
      per-tick body advance differing by >= 0.05 m/s (the command-adapter
      receipt's frozen graded-spread bar).

PRE-COMMITTED ACTION (the prereg): on fire, REPORT the pair class and a witness
pair (tick indices + the differing label quantity + the fields that would have
had to separate them). The 80-field table is NOT amended. The verdict is
whatever the search returns.

DECLARED SCOPE (the prereg): the record carries ONLY the channels the trace
determines. Unavailable groups (body velocity, command echo, limiter
saturation) are declared unavailable per the mask convention -- never invented;
pad endpoint identity is not in the trace (the [dvfl] band pair is collapsed,
g1==g2), so the endpoint-signed pad channels ride ordering 'lohi' exactly as
the obs-split lane declared, with split_abs reconstructed by the wave-46
calibration (g_lo=gmin, g_hi=2*pad_y-g_lo, split_abs=g_hi-g_lo).
The mid-leg slots (ml/mr) have NO body on this walker (four paws: fore_left,
fore_right, rear_left, rear_right): they are DECLARED UNAVAILABLE. The paw ->
slot mapping is fl=fore_left, fr=fore_right, hl=rear_left, hr=rear_right.

Usage: python mine_aliasing_audit.py <audit_trace_stderr.txt> <out_dir>
Output: mine_aliasing_audit_out.txt + aliased_pairs.json in the out dir.
Exit 0 always -- the verdict is a REPORT (F1's pre-committed action), not a
gate; the honest verdict is carried in the receipt either way.
"""
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
EXPORT = os.path.join(REPO, "tools", "science_funnel", "typeb_export")
sys.path.insert(0, EXPORT)

import observation_schema as oschema  # noqa: E402

KTOUCH = 1e-5           # the machinery's own contact-vs-not quantum
K_SINK_RATE_MAX = 2.349e-3   # m/tick, the wave-27 mined worst sink rate
V_GRADED_BAR = 0.05     # m/s, the command-adapter receipt's frozen graded bar
SETTLE_TICKS = 60       # the machinery's own settle window [0, 59]
# the paw -> observation-slot mapping (declared: this walker has four paws)
PAD_MAP = {  # dvfp (fore) / dvp (rear) k -> (obs slot, paw name)
    "fore": [(0, "fl", "fore_left"), (1, "fl", "fore_left"),
             (2, "fr", "fore_right"), (3, "fr", "fore_right")],
    "rear": [(0, "hl", "rear_left"), (1, "hl", "rear_left"),
             (2, "hr", "rear_right"), (3, "hr", "rear_right")],
}

out_lines = []
def P(*a):
    s = " ".join(str(x) for x in a)
    out_lines.append(s)
    print(s)


def parse_run(trace_path: str, stdout_path: str | None = None) -> dict:
    """The LAST walk run (the mine_wave47 convention) with the series this
    audit's labels need. stdout_path (the same run's ship stdout) supplies the
    F-G26 unload-class census and the F-G28 hind-fire list (cross-check)."""
    lines = open(trace_path, encoding="utf-8", errors="replace").read().splitlines()
    idx = [i for i, l in enumerate(lines) if l.startswith("WALK REFUSED")]
    run = lines[idx[-2] + 1:idx[-1]]
    mref = re.match(r"WALK REFUSED tick (\d+): (\S+)", lines[idx[-1]])
    refusal = (int(mref.group(1)), mref.group(2))

    dv, dvp, dvfp, dvf, dvfa, dvfl = {}, {}, {}, {}, {}, {}
    hind_events, foreclk_events, pawcap_events = defaultdict(set), defaultdict(set), defaultdict(set)
    fires_order = []
    for l in run:
        m = re.match(r"\[dv\] t=(\d+) ptq=\S+ ptgt=\S+ pang=\S+ pspd=\S+ ev=(\d+) phL=(\S+) phR=(\S+) com=\((\S+),(\S+)\) hull=(\d+) in=(\d) bx=(\S+)", l)
        if m:
            dv[int(m.group(1))] = dict(ev=int(m.group(2)), phL=float(m.group(3)),
                                       phR=float(m.group(4)),
                                       com_e=float(m.group(5)), com_s=float(m.group(6)),
                                       hull=int(m.group(7)), in_hull=int(m.group(8)),
                                       bx=float(m.group(9)))
            continue
        m = re.match(r"\[dvfp\] t=(\d+) k=(\d) gap=(\S+) rxn=(\S+) frc=(\S+) slip=(\S+)", l)
        if m:
            dvfp[(int(m.group(1)), int(m.group(2)))] = (float(m.group(3)), float(m.group(5)))
            continue
        m = re.match(r"\[dvp\] t=(\d+) k=(\d) gap=(\S+) rxn=(\S+) frc=(\S+) slip=(\S+)", l)
        if m:
            dvp[(int(m.group(1)), int(m.group(2)))] = (float(m.group(3)), float(m.group(5)))
            continue
        m = re.match(r"\[dvf\] t=(\d+) leg=(\d) mode=(\d)", l)
        if m:
            dvf[(int(m.group(1)), int(m.group(2)))] = int(m.group(3))
            continue
        m = re.match(r"\[dvfa\] t=(\d+) leg=(\d) br=(\w) held=(\d) sg=(\S+) c=(\S+) cmd_y=(\S+) pad_y=(\S+) plant_y=(\S+)", l)
        if m:
            t, leg = int(m.group(1)), int(m.group(2))
            dvfa.setdefault(t, {})
            if leg not in dvfa[t]:   # first-sample per (t, leg), the declared convention
                dvfa[t][leg] = dict(br=m.group(3), held=int(m.group(4)),
                                    pad_y=float(m.group(8)))
            continue
        m = re.match(r"\[dvfl\] t=(\d+) leg=(\d) g1=(\S+) g2=(\S+) edge=(\S+)", l)
        if m:
            t, leg = int(m.group(1)), int(m.group(2))
            dvfl.setdefault(t, {})
            if leg not in dvfl[t]:
                dvfl[t][leg] = dict(gmin=float(m.group(3)), g2=float(m.group(4)),
                                    edge=float(m.group(5)))
            continue
        if l.startswith("[hindstep] fire"):
            m = re.match(r"\[hindstep\] fire leg=(\d) tick=(\d+)", l)
            hind_events[int(m.group(2))].add("fire:" + str(m.group(1)))
            fires_order.append((int(m.group(2)), int(m.group(1))))
            continue
        if l.startswith("[hindstep] td"):
            m = re.match(r"\[hindstep\] td leg=(\d) tick=(\d+)", l)
            hind_events[int(m.group(2))].add("td:" + str(m.group(1)))
            continue
        if l.startswith("[foreclk]"):
            m = re.match(r"\[foreclk\] (\S+)", l)
            mt = re.search(r"tick=(\d+)", l)
            if mt:
                foreclk_events[int(mt.group(1))].add(m.group(1))
            continue
        if l.startswith("[pawcap]"):
            mt = re.search(r"td=(\d+)", l)
            if mt:
                pawcap_events[int(mt.group(1))].add("cap")
            continue
    return dict(refusal=refusal, dv=dv, dvp=dvp, dvfp=dvfp, dvf=dvf, dvfa=dvfa,
                dvfl=dvfl, hind_events=hind_events, foreclk_events=foreclk_events,
                pawcap_events=pawcap_events, fires_order=fires_order,
                n_run_lines=len(run), unload_ticks=_unload_ticks_from_stdout(stdout_path))


def _unload_ticks_from_stdout(stdout_path: str | None) -> set[int]:
    """The F-G26 unload-class census ticks (the stdout's own class line; the
    wave-38 slice's declared source for unload_class)."""
    if stdout_path is None:
        return set()
    import json as _json
    doc = _json.loads(open(stdout_path, "rb").read().decode("utf-8"))
    for line in doc.get("measured", []):
        if "unload_class_ticks=" in line:
            tail = line.split("unload_class_ticks=", 1)[1]
            if "@" in tail:
                tail = tail.split("@", 1)[1]
            return {int(t) for t in re.findall(r"\d+", tail)}
    return set()


def build(parsed: dict) -> tuple[list[dict], dict]:
    """Per-tick record (the trace-determined channels only) + the label table."""
    dv, dvp, dvfp, dvf, dvfa, dvfl = (parsed["dv"], parsed["dvp"], parsed["dvfp"],
                                      parsed["dvf"], parsed["dvfa"], parsed["dvfl"])
    hind_events, foreclk_events, pawcap_events = (parsed["hind_events"],
                                                  parsed["foreclk_events"],
                                                  parsed["pawcap_events"])
    unload_ticks = parsed["unload_ticks"]
    ticks = sorted(dv)
    recs, labels = [], {}
    prev_count = None
    prev_gaps = None
    for t in ticks:
        s = dv[t]
        # ---- pads: 8 (gap, force) per tick, in dvfp k0..3 then dvp k0..3 order
        pads = {}
        for kind, table in (("fore", dvfp), ("rear", dvp)):
            for k, slot, paw in PAD_MAP[kind]:
                g, f = table.get((t, k), (None, None))
                pads.setdefault(paw, []).append((g, f))
        paw_gap = {paw: min(g for g, _ in v if g is not None) if v else None
                   for paw, v in pads.items()}
        paw_frc = {paw: sum(f for _, f in v if f is not None) for paw, v in pads.items()}
        touching = {paw: (g is not None and g <= KTOUCH) for paw, g in paw_gap.items()}
        contact_count = sum(1 for v in touching.values() if v)
        # ---- phases (the controller's own clock)
        phL, phR = s["phL"], s["phR"]
        if t == 0:
            phase_rate = None
        else:
            d = phL - dv[t - 1]["phL"]
            if d <= -0.5:
                d += 1.0
            elif d > 0.5:
                d -= 1.0
            phase_rate = d
        # ---- pad-split reconstruction (the wave-46 calibration; ordering 'lohi')
        pad_gaps, pad_ord = {}, {}
        for leg, slot in ((0, "hl"), (1, "hr")):
            a, b = dvfa.get(t, {}).get(leg), dvfl.get(t, {}).get(leg)
            if a is not None and b is not None:
                g_lo = b["gmin"]
                g_hi = 2.0 * a["pad_y"] - g_lo
                pad_gaps[slot] = [g_lo, g_hi]
                pad_ord[slot] = "lohi"
        gap_series = [paw_gap[p] for p in ("fore_left", "fore_right", "rear_left", "rear_right")]
        fire_ticks = {ft for ft, _leg in parsed["fires_order"]}
        rec = {
            "tick": t,
            "phase_left": phL, "phase_right": phR, "phase_frac": phL,
            "phase_rate": phase_rate,
            "contact_count": contact_count,
            "contact_count_prev": prev_count,
            "foot_contacts": None,   # DECLARED: the 6-slot group is all-or-nothing in the
            "foot_forces": None,     # frozen reader; this walker has FOUR paws (fl, fr,
            # hl, hr) -- the ml/mr slots have no body, so the vector is not determined
            # element-wise. The groups ride UNAVAILABLE (mask 0, mean fill; the P3
            # normalization already carries them never-available at 0/1). The per-paw
            # truth stays in the LABELS (touch pattern) and the aggregate (contact_count).
            "intervention_reason": "none",
            "ticks_since_intervention": 3000,   # the projector's own no-intervention clamp
            "hold_tick": t % 15,
            "is_decision_tick": t % 15 == 0,
            "ticks_since_reset": t,
            # the class flags the records DO determine: the unload class from the
            # stdout census (the F-G26 line, the wave-38 slice's own source) and
            # the hind-step class from the [hindstep] fire events (cross-checked
            # against the F-G28 fire list in the receipt)
            "available_groups": ["gait_phase", "contact_aggregate",
                                 "command_clock", "intervention",
                                 "sensor_health", "phase_dynamics", "pad_split"],
            "pad_gaps": pad_gaps or None,
            "pad_pair_ordering": pad_ord or None,
        }
        if t in unload_ticks:
            rec["unload_class"] = 1     # the stdout census's own class (F-G26)
        if t in fire_ticks:
            rec["hind_step_class"] = 1  # the [hindstep] fire tick (cross-checked vs F-G28)
        recs.append(rec)
        # ---- labels
        ev_delta = s["ev"] - dv[t - 1]["ev"] if t > 0 else 0
        dg = ([None] * 4 if prev_gaps is None else
              [None if (g is None or p is None) else g - p
               for g, p in zip(gap_series, prev_gaps)])
        vx = None if t == 0 else (s["bx"] - dv[t - 1]["bx"]) * 300.0
        labels[t] = dict(
            br_L=dvfa.get(t, {}).get(0, {}).get("br"), br_R=dvfa.get(t, {}).get(1, {}).get("br"),
            fm_L=dvf.get((t, 0)), fm_R=dvf.get((t, 1)),
            ev_delta=ev_delta, settle=t < SETTLE_TICKS,
            hind_ev=tuple(sorted(hind_events.get(t, ()))),
            foreclk_ev=tuple(sorted(foreclk_events.get(t, ()))),
            pawcap_ev=tuple(sorted(pawcap_events.get(t, ()))),
            touch=tuple(touching[p] for p in ("fore_left", "fore_right", "rear_left", "rear_right")),
            dg=dg, vx=vx,
            hull=(s["hull"], s["in_hull"]),
        )
        prev_count = contact_count
        prev_gaps = gap_series
    return recs, labels


def main() -> None:
    trace, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    P("THE ALIASING-AUDIT MINE -- F1 STATE-ALIASING (preregistered before the build)")
    P("trace:", trace)
    P("=" * 150)
    sha = hashlib.sha256(open(trace, "rb").read()).hexdigest()
    P("trace sha256:", sha)
    parsed = parse_run(trace, stdout_path=os.path.splitext(trace)[0].replace("_stderr", "_stdout") + ".txt")
    P("refusal:", parsed["refusal"], "| run lines:", parsed["n_run_lines"],
      "| hind fires:", len(parsed["fires_order"]))
    recs, labels = build(parsed)
    P("ticks parsed:", len(recs))

    # ---- the frozen normalization (the lane's frozen table = the v2 manifest section)
    table = json.load(open(os.path.join(
        HERE, "observation_interface_v2.json"), encoding="utf-8"))
    mean = np.zeros(oschema.OBS_DIM, dtype=np.float32)
    std = np.ones(oschema.OBS_DIM, dtype=np.float32)
    for f in table["fields"]:
        mean[f["index"]] = f["normalization"]["mean"]
        std[f["index"]] = f["normalization"]["std"]
    P("normalization: the frozen observation_interface_v2.json (sha %s...)"
      % hashlib.sha256(open(os.path.join(HERE, "observation_interface_v2.json"),
                            "rb").read()).hexdigest()[:16])

    # ---- project every tick (the deployed recipe, prev_state caller-owned)
    groups = defaultdict(list)
    masks_avail = np.zeros(oschema.OBS_DIM, dtype=np.int64)
    prev_state = {}
    for rec in recs:
        obs, mask = oschema.project_trace(rec, mean, std, prev_state)
        ps = dict(prev_state)
        for leg in ("hl", "hr"):
            v = rec.get("pad_gaps") or {}
            if leg in v:
                b = float(v[leg][1])
                ps["pad_split_abs_" + leg] = b
            else:
                ps.pop("pad_split_abs_" + leg, None)
        prev_state = ps
        groups[obs.tobytes()].append(rec["tick"])
        masks_avail += (mask > 0).astype(np.int64)
    P("-" * 150)
    P("THE MASK CENSUS (how often each field was AVAILABLE over %d ticks):" % len(recs))
    never = [(table["fields"][i]["name"], int(masks_avail[i])) for i in range(oschema.OBS_DIM)]
    P("  never-available fields (%d): %s" % (
        sum(1 for _, c in never if c == 0),
        [n for n, c in never if c == 0]))
    P("  always-available fields: %d" % sum(1 for _, c in never if c == len(recs)))

    # ---- THE SEARCH (F1)
    dup_groups = {h: ts for h, ts in groups.items() if len(ts) > 1}
    n_dup_ticks = sum(len(ts) for ts in dup_groups.values())
    P("-" * 150)
    P("THE SEARCH: %d distinct observations over %d ticks; %d bit-identical groups "
      "covering %d ticks" % (len(groups), len(recs), len(dup_groups), n_dup_ticks))

    fired = []
    context_only = []
    for h, ts in dup_groups.items():
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                a, b = labels[ts[i]], labels[ts[j]]
                why = alias_reason(a, b)   # EXACTLY the frozen clauses (a)/(b)/(c)
                ctx = context_reason(a, b)  # the event-set label: CONTEXT ONLY
                if why:
                    fired.append((ts[i], ts[j], why + (("; context: " + ctx) if ctx else "")))
                elif ctx:
                    context_only.append((ts[i], ts[j], ctx))
    P("F1 STATE-ALIASING SEARCH (the frozen clauses a/b/c only): %d aliased pairs "
      "(bit-identical obs, differing labels)" % len(fired))
    for t1, t2, why in fired[:24]:
        P("  PAIR (%d,%d): %s" % (t1, t2, why))
    if len(fired) > 24:
        P("  ... %d further pairs (aliased_pairs.json carries all)" % (len(fired) - 24))
    P("context-only pairs (event-set differences OUTSIDE the frozen clauses; carried, "
      "not fired): %d" % len(context_only))
    for t1, t2, why in context_only[:8]:
        P("  CTX  (%d,%d): %s" % (t1, t2, why))
    if len(context_only) > 8:
        P("  ... %d further context pairs (aliased_pairs.json)" % (len(context_only) - 8))
    P("-" * 150)
    # what WOULD have separated them (the declared-scope note)
    if fired:
        P("the fired pairs' differing labels live in channels the trace record does not")
        P("determine (body velocity, command echo, limiter, pad endpoint identity, class")
        P("flags): NECESSARY aliases of this record set, per the prereg's declared scope.")
    P("VERDICT (F1, the pre-committed action): %s"
      % ("FIRED -- %d aliased pairs REPORTED (witnesses above); the 80-field table is "
         "NOT amended; the freeze stands and the finding is carried to the planner lane "
         "as the measured reason certified transitions must guard mode boundaries."
         % len(fired) if fired else
         "GREEN -- no pair of ticks with bit-identical 80-field observations differs in "
         "reflex mode, contact regime, or deformation velocity on this record."))

    # ---- the artifact
    art = dict(
        trace_sha256=sha,
        refusal=list(parsed["refusal"]),
        ticks=len(recs),
        distinct_observations=len(groups),
        bitidentical_groups=len(dup_groups),
        bitidentical_ticks=n_dup_ticks,
        aliased_pairs=[dict(t1=t1, t2=t2, reason=why) for t1, t2, why in fired],
        context_only_pairs=[dict(t1=t1, t2=t2, reason=why) for t1, t2, why in context_only],
        mask_never_available=[n for n, c in never if c == 0],
        prereg_bars=dict(kTouch=KTOUCH, kSinkRateMax=K_SINK_RATE_MAX,
                         v_graded_bar=V_GRADED_BAR, settle_ticks=SETTLE_TICKS),
    )
    with open(os.path.join(out_dir, "aliased_pairs.json"), "w", encoding="utf-8") as f:
        json.dump(art, f, indent=1)
    with open(os.path.join(out_dir, "mine_aliasing_audit_out.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")
    P("artifacts written to", out_dir)
    P("Trailer Agent: ifreeze")


def alias_reason(a: dict, b: dict) -> str | None:
    """EXACTLY the prereg's frozen fire clauses: (a) reflex mode = hind branch,
    fore clock mode, capture-event delta, settle window; (b) contact regime =
    the touch pattern; (c) deformation velocity = pad gap deltas at kSinkRateMax,
    body advance at the graded bar. Nothing else fires."""
    why = []
    if (a["br_L"], a["br_R"]) != (b["br_L"], b["br_R"]):
        why.append("hind branch %s/%s vs %s/%s" % (a["br_L"], a["br_R"], b["br_L"], b["br_R"]))
    if (a["fm_L"], a["fm_R"]) != (b["fm_L"], b["fm_R"]):
        why.append("fore clock mode %s/%s vs %s/%s" % (a["fm_L"], a["fm_R"], b["fm_L"], b["fm_R"]))
    if a["ev_delta"] != b["ev_delta"]:
        why.append("capture-event delta %d vs %d" % (a["ev_delta"], b["ev_delta"]))
    if a["settle"] != b["settle"]:
        why.append("settle window %s vs %s" % (a["settle"], b["settle"]))
    if a["touch"] != b["touch"]:
        why.append("touch pattern %s vs %s" % (a["touch"], b["touch"]))
    for k in range(4):
        da, db = a["dg"][k], b["dg"][k]
        if da is not None and db is not None and abs(da - db) > K_SINK_RATE_MAX:
            why.append("pad %d deformation rate %.6f vs %.6f m/tick (> kSinkRateMax)"
                       % (k, da, db))
    if a["vx"] is not None and b["vx"] is not None and abs(a["vx"] - b["vx"]) >= V_GRADED_BAR:
        why.append("body advance %.4f vs %.4f m/s (>= graded bar)" % (a["vx"], b["vx"]))
    return "; ".join(why) if why else None


def context_reason(a: dict, b: dict) -> str | None:
    """The per-tick event-set label (hindstep/foreclk/pawcap events): CONTEXT
    ONLY -- NOT one of the prereg's frozen fire clauses; reported, never fired."""
    if (a["hind_ev"], a["foreclk_ev"], a["pawcap_ev"]) != (b["hind_ev"], b["foreclk_ev"], b["pawcap_ev"]):
        return ("events hind=%s foreclk=%s pawcap=%s vs hind=%s foreclk=%s pawcap=%s"
                % (a["hind_ev"], a["foreclk_ev"], a["pawcap_ev"],
                   b["hind_ev"], b["foreclk_ev"], b["pawcap_ev"]))
    return None


def parsed_labels(parsed):  # pragma: no cover (kept out of the hot path)
    raise AssertionError


if __name__ == "__main__":
    main()
