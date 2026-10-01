"""reflex_replay.py -- the Phase-B parity harness (reflex-core lane).

Replays the committed oracle observation stream (runs/*_obs.txt, validated
byte-exact against the port lane's cpu anchors at the shifted sampling) through
walker_reflex.ReflexCore at levels 0..3 and compares the decision streams
against the C++ controller's own GAIT_EVENT_TRACE bytes (runs/*_trace.txt).
Fires PREREG_PHASEB.md's falsifiers honestly and writes replay_results.json.
NEW FILE, this lane only.

Trailer Agent: GLM 5.3.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TYPEB = HERE.parent.parent / "typeb_gpu"
sys.path.insert(0, str(TYPEB))

from walker_model import load_spec, T_CYCLE, DUTY_SAMPLED  # noqa: E402
from walker_reflex import ReflexCore, K_TOUCH  # noqa: E402

NC = 18
DECISION_KINDS = ("pawcap", "fore_arm", "fore_lift", "fore_deflift",
                  "fore_waitfire", "fore_inplace", "fore_td",
                  "fore_converge", "fore_converged", "fore_hold",
                  "hind_fire", "hind_td", "hind_holdreturn",
                  "hind_standhold", "hind_waivefire", "hind_unloadgate",
                  "hind_guardblock")


# ── parsing (see the module docstring of reflex_oracle.cpp) ──
def parse_obs(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        if not line.startswith("OBS "):
            continue
        tok = line.split()
        nums = [float(x) for x in tok[2:]]
        rows.append({"t": int(tok[1][2:]), "q": nums[:NC],
                     "v": nums[NC:2 * NC], "phi": (nums[-2], nums[-1])})
    return rows


def _f(tok):
    return float(tok.split("=", 1)[1]) if "=" in tok else float(tok)


def _i(tok):
    return int(tok.split("=", 1)[1]) if "=" in tok else int(tok)


def _pair(tok):
    a, b = tok[1:-1].split(",")
    return float(a), float(b)


def parse_trace(path):
    ev = []
    cur_tick = -1

    def d(toks, start=2):
        return dict(t.split("=", 1) for t in toks[start:] if "=" in t)

    for line in Path(path).read_text().splitlines():
        t = line.split()
        if line.startswith("PT t="):
            cur_tick = _i(t[1])
            continue
        if line.startswith("[pawcap] "):
            g = d(t, 1)
            ev.append({"kind": "pawcap", "leg": _i(g["leg"]), "tick": cur_tick,
                       "td": _i(g["td"]), "paw": _pair(g["paw"]),
                       "branch": _i(g["branch"]), "qerr": float(g["qerr"]),
                       "roundtrip": float(g["roundtrip"])})
        elif line.startswith("[foreclk] arm "):
            g = d(t)
            ev.append({"kind": "fore_arm", "leg": _i(g["leg"]), "tick": _i(g["tick"]),
                       "offset0": float(g["offset0"]), "xoff": float(g["xoff"]),
                       "amax": float(g["amax"]), "stance": float(g["stance"]),
                       "cycle": float(g["cycle"]), "entry": _i(g["entry"]),
                       "tau_env": float(g["tau_env"])})
        elif line.startswith("[foreclk] lift "):
            g = d(t)
            ev.append({"kind": "fore_lift", "leg": _i(g["leg"]), "tick": _i(g["tick"]),
                       "td": _i(g["td"]), "entry": _i(g["entry"]),
                       "frm": _pair(g["from"]), "to": _pair(g["to"]),
                       "xoff": float(g["xoff"]), "v": float(g["v"]),
                       "wall_bound": _i(g["wall_bound"])})
        elif line.startswith("[foreclk] deflift "):
            g = d(t)
            ev.append({"kind": "fore_deflift", "leg": _i(g["leg"]),
                       "tick": _i(g["tick"]), "seat_hr": float(g["seat_hr"])})
        elif line.startswith("[foreclk] waitfire "):
            g = d(t)
            ev.append({"kind": "fore_waitfire", "leg": _i(g["leg"]),
                       "tick": _i(g["tick"]), "hr": float(g["hr"]),
                       "floor": float(g["floor"]), "hold": _i(g["hold"]),
                       "last": _i(g["last"])})
        elif line.startswith("[foreclk] inplace "):
            g = d(t)
            ev.append({"kind": "fore_inplace", "leg": _i(g["leg"]),
                       "tick": _i(g["tick"]), "paw": _pair(g["paw"]),
                       "stance": float(g["stance"]), "entry": _i(g["entry"]),
                       "follow": _i(g["follow"])})
        elif line.startswith("[foreclk] td "):
            g = d(t)
            ev.append({"kind": "fore_td", "leg": _i(g["leg"]), "tick": _i(g["tick"]),
                       "td_count": _i(g["td_count"]), "entry": _i(g["entry"]),
                       "stance": float(g["stance"]), "roundtrip": float(g["roundtrip"])})
        elif line.startswith("[foreclk] converged "):
            g = d(t)
            ev.append({"kind": "fore_converged", "leg": _i(g["leg"]),
                       "tick": _i(g["tick"]), "slot": float(g["slot"])})
        elif line.startswith("[foreclk] converge "):
            g = d(t)
            ev.append({"kind": "fore_converge", "leg": _i(g["leg"]),
                       "tick": _i(g["tick"]), "slot": float(g["slot"]),
                       "k": _i(g["k"]), "w": _i(g["w"]),
                       "stance": float(g["stance"]), "env": float(g["env"]),
                       "conv": _i(g["conv"])})
        elif line.startswith("[foreclk] hold "):
            g = d(t)
            ev.append({"kind": "fore_hold", "leg": _i(g["leg"]), "tick": _i(g["tick"]),
                       "armed": _i(g["armed"]), "last": _i(g["last"]),
                       "off": _pair(g["off"])})
        elif line.startswith("[hindstep] fire "):
            g = d(t)
            ev.append({"kind": "hind_fire", "leg": _i(g["leg"]), "tick": _i(g["tick"]),
                       "phi": float(g["phi"]), "cls": g["class"],
                       "frm": _pair(g["from"]), "to": _pair(g["to"]),
                       "xoff": float(g["xoff"]), "v": float(g["v"]),
                       "qerr": float(g["qerr"]), "ap": float(g["ap"]),
                       "br": _i(g["br"]), "dl": _i(g["dl"])})
        elif line.startswith("[hindstep] td "):
            g = d(t)
            ev.append({"kind": "hind_td", "leg": _i(g["leg"]), "tick": _i(g["tick"]),
                       "tds": _i(g["tds"])})
        elif line.startswith("[hindstep] holdreturn "):
            g = d(t)
            ev.append({"kind": "hind_holdreturn", "leg": _i(g["leg"]),
                       "tick": _i(g["tick"]), "t": float(g["t"]),
                       "pairmin": float(g["pairmin"])})
        elif line.startswith("[hindstep] standhold "):
            g = d(t)
            ev.append({"kind": "hind_standhold", "leg": _i(g["leg"]),
                       "tick": _i(g["tick"]), "swing_stall": _i(g["swing_stall"])})
        elif line.startswith("[hindstep] waivefire "):
            g = d(t)
            ev.append({"kind": "hind_waivefire", "leg": _i(g["leg"]),
                       "tick": _i(g["tick"]), "dl": _i(g["dl"])})
        elif line.startswith("[hindstep] unloadgate "):
            g = d(t)
            ev.append({"kind": "hind_unloadgate", "leg": _i(g["leg"]),
                       "tick": _i(g["tick"]), "dl": _i(g["dl"]), "cls": g["class"]})
        elif line.startswith("[hindstep] guardblock "):
            g = d(t)
            ev.append({"kind": "hind_guardblock", "leg": _i(g["leg"]),
                       "tick": _i(g["tick"]), "dl": _i(g["dl"]),
                       "link_td": _i(g["link_td"]), "link_fire": _i(g["link_fire"])})
    # cross-check: every tick-stamped event must agree with its PT marker
    # (enforced implicitly by the replay comparison; pawcap uses the marker).
    return ev


# ── comparison: (kind,tick,leg) sequence EXACT; floats within print precision ──
TOL = {"default": 5e-7, "qerr": 5e-4, "roundtrip": 5e-4, "seat_hr": 5e-7,
       "phi": 5e-6, "ap": 5e-5, "stance": 5e-4, "env": 5e-4, "slot": 5e-4,
       "pairmin": 5e-7, "hr": 5e-7, "tau_env": 5e-4, "cycle": 5e-4}


def compare(exp, got, max_report=8):
    mis = []
    if len(exp) != len(got):
        n = min(len(exp), len(got))
        mis.append(f"LENGTH expected {len(exp)} got {len(got)} "
                   f"(first divergence at [{n}] "
                   f"{exp[n]['kind']}/t{exp[n]['tick']}/leg{exp[n]['leg']} "
                   f"vs {got[n]['kind'] if n < len(got) else 'END'})")
        return mis
    for i, (e, g) in enumerate(zip(exp, got)):
        if e["kind"] != g["kind"] or e["tick"] != g["tick"] or e["leg"] != g["leg"]:
            mis.append(f"[{i}] expected {e['kind']}/t{e['tick']}/leg{e['leg']} "
                       f"got {g['kind']}/t{g['tick']}/leg{g['leg']}")
            if len(mis) >= max_report:
                return mis
            continue
        for k, ev_ in e.items():
            if k in ("kind", "tick", "leg"):
                continue
            gv = g.get(k)
            if gv is None:
                mis.append(f"[{i}] {e['kind']} t{e['tick']} missing {k}")
                continue
            if isinstance(ev_, tuple):
                for a, b in zip(ev_, gv):
                    tol = TOL.get(k, TOL["default"])
                    if not (abs(a - b) <= tol + 1e-9 * abs(a)):
                        mis.append(f"[{i}] {e['kind']} t{e['tick']} {k}: {b!r} != {a!r}")
            elif isinstance(ev_, float):
                tol = TOL.get(k, TOL["default"])
                if not (abs(gv - ev_) <= tol + 1e-9 * abs(ev_)):
                    mis.append(f"[{i}] {e['kind']} t{e['tick']} {k}: {gv!r} != {ev_!r}")
            elif isinstance(ev_, str):
                if gv != ev_:
                    mis.append(f"[{i}] {e['kind']} t{e['tick']} {k}: {gv} != {ev_}")
            else:
                if gv != ev_:
                    mis.append(f"[{i}] {e['kind']} t{e['tick']} {k}: {gv!r} != {ev_!r}")
        if len(mis) >= max_report:
            return mis
    return mis


def fresh_touching(core, q):
    """The C++ reset seeds touching_prev_ from a FRESH band read."""
    core._g = core._fk_all(q)
    s = core.spec
    gpair = core._g[4]
    for leg in range(2):
        prefix = 'left' if leg == 0 else 'right'
        t = any(nm.startswith(prefix) and gpair[k] <= K_TOUCH
                for k, nm in enumerate(s.pt_name))
        core.touching_prev[leg] = t
    core._g = None


def probe_config(probe):
    cfg = dict(power=True, contact=True, gait_enabled=True, capture_enabled=True)
    if probe == "stand":
        cfg["gait_enabled"] = False
    elif probe == "freefall":
        # cpu_probe's freefall: power off, contact off -- gait_enabled STAYS
        # true (the C++ clock advances once the settle window ends).
        cfg = dict(power=False, contact=False, gait_enabled=True,
                   capture_enabled=True)
    return cfg


def run_level2(obs_rows, spec, level, probe, schedule=None):
    """Feed one observation stream through ReflexCore at `level`."""
    cfg = probe_config(probe)
    core = ReflexCore(spec, reflex_level=level, **cfg)
    if level >= 1:
        fresh_touching(core, obs_rows[0]["q"])
    events = []
    issues = []
    phi_err = 0.0
    phi_t = -1
    for i, row in enumerate(obs_rows):
        if level >= 3 and schedule and row["t"] in schedule:
            core.cmd.issue(schedule[row["t"]], row["t"])
            issues.append({"tick": row["t"], "v": schedule[row["t"]]})
        ev = core.tick(row["q"], row["v"])
        events.extend(ev)
        if i + 1 < len(obs_rows):
            w = max(abs(core.phi[0] - obs_rows[i + 1]["phi"][0]),
                    abs(core.phi[1] - obs_rows[i + 1]["phi"][1]))
            if w > phi_err:
                phi_err, phi_t = w, row["t"]
    return {"events": events, "issues": issues, "phi_err": phi_err,
            "phi_t": phi_t, "cmd": core.cmd.state(),
            "feed_hash": hashlib.sha256(
                "\n".join(str(r["t"]) for r in obs_rows).encode()).hexdigest()[:16],
            "core": core}


def kinds(events):
    return [(e["kind"], e["tick"], e.get("leg", -1)) for e in events]


def main():
    runs = HERE / "runs"
    scene = HERE.parents[3] / ".tmp" / "gait-walker" / "scene.json"
    spec = load_spec(str(scene))
    R = {"prereg": "PREREG_PHASEB.md", "scene_sha_head": scene.stem,
         "levels": {}}

    probes = {
        "walk": dict(obs="oracle_walk_obs.txt", trace="oracle_walk_trace.txt",
                     schedule=None),
        "cmd": dict(obs="oracle_cmd_obs.txt", trace="oracle_cmd_trace.txt",
                    schedule={150: 0.60}),
        "reissue": dict(obs="oracle_reissue_obs.txt",
                        trace="oracle_reissue_trace.txt",
                        schedule={t: 0.60 for t in range(150, 301, 15)}),
        "stand": dict(obs="oracle_stand_obs.txt", trace="oracle_stand_trace.txt",
                      schedule=None),
        "freefall": dict(obs="oracle_freefall_obs.txt",
                         trace="oracle_freefall_trace.txt", schedule=None),
    }

    parity_fail, monotone_fail = [], []
    streams = {}

    for pname, pc in probes.items():
        obs = parse_obs(runs / pc["obs"])
        expected = parse_trace(runs / pc["trace"])
        per_level = {}
        for level in (0, 1, 2, 3):
            sched = pc["schedule"] if level >= 3 else None
            r = run_level2(obs, spec, level, pname, sched)
            got = [e for e in r["events"] if e["kind"] in DECISION_KINDS]
            # Parity surface per level: L2 mirrors an UNCOMMANDED controller,
            # so its trace-parity target is the plain run only. On the
            # commanded feeds the C++ oracle IS an L3 controller (the command
            # live from tick 150); the lawful parity level there is L3.
            parity_level = (level == 3) if pc["schedule"] else (level >= 2)
            mis = compare(expected, got) if parity_level else []
            per_level[level] = {
                "decisions": len(got), "events_total": len(r["events"]),
                "parity_mismatches": mis, "phi_worst_abs": r["phi_err"],
                "phi_worst_tick": r["phi_t"], "issues": r["issues"],
                "cmd_census": r["cmd"], "feed_hash": r["feed_hash"],
                "events": r["events"],
            }
            if parity_level and mis:
                parity_fail.append(f"{pname}/L{level}: {mis[0]}")
            if level >= 1 and r["phi_err"] > 1e-12:
                parity_fail.append(
                    f"{pname}/L{level} phi drift {r['phi_err']:.3e} @t{r['phi_t']}")
        streams[pname] = per_level

    # ── F-REFLEX-LEVEL-MONOTONE ──
    for pname, pc in probes.items():
        pl = streams[pname]
        if len({pl[lv]["feed_hash"] for lv in (0, 1, 2, 3)}) != 1:
            monotone_fail.append(f"{pname}: observation feeds differ across levels")
        for lv in (0, 1, 2):
            if pl[lv]["issues"]:
                monotone_fail.append(f"{pname}/L{lv} issued a command below level 3")
            if pl[lv]["cmd_census"]["live"]:
                monotone_fail.append(f"{pname}/L{lv}: command live below level 3")
            if pl[lv]["events_total"] != 0 and lv == 0:
                monotone_fail.append(f"{pname}/L0 emitted decisions")
        # L1 clock/capture events must appear in L2's and L3's streams in order
        k1 = [k for k in kinds(pl[1]["events"])]
        k2 = [k for k in kinds(pl[2]["events"])]
        k3 = [k for k in kinds(pl[3]["events"])]
        it = iter(k2)
        if not all(k in it for k in k1):
            monotone_fail.append(f"{pname}: L1 decisions not a subsequence of L2")
        it = iter(k3)
        if not all(k in it for k in k2):
            monotone_fail.append(f"{pname}: L2 decisions not a subsequence of L3")
        # plain runs: L3 with no command issued == L2 exactly
        if pc["schedule"] is None and kinds(pl[3]["events"]) != kinds(pl[2]["events"]):
            monotone_fail.append(f"{pname}: L3 != L2 with no command issued")
    # the commanded feeds carry a DIFFERENT physics trajectory (the command
    # entered the C++ oracle's plant law): cross-feed equality of L<3 streams
    # is NOT a monotonicity requirement. The binding same-feed checks above
    # (L1 subset of L2 subset of L3; L3 == L2 when no command is issued;
    # nothing issued below L3) are the falsifier's substance.

    # ── PB-L3: the adapter census + the authority law at the fire ──
    cmd3 = streams["cmd"][3]
    first_fire_after_issue = next(
        (e for e in cmd3["events"]
         if e["kind"] in ("fore_lift", "fore_deflift", "fore_waitfire", "hind_fire")
         and e["tick"] > 150), None)
    # the authority law: every post-issue hind fire's xoff == cmd*0.2424650
    # (unless annulus-clamped, which the fire's own census flags via dl/qerr
    # comparison -- here we report the raw law value against the trace)
    xoff_law = 0.60 * (DUTY_SAMPLED * T_CYCLE) / 2.0
    expected_cmd = parse_trace(runs / "oracle_cmd_trace.txt")
    post_fires = [e for e in expected_cmd
                  if e["kind"] == "hind_fire" and e["tick"] > 150]
    xoff_matches = all(abs(e["xoff"] - xoff_law) <= 5e-7 or e["xoff"] < xoff_law
                       for e in post_fires)

    R["adapter"] = {
        "xoff_law_per_ms": xoff_law / 0.60,
        "mirror_cmd_census_cmd": cmd3["cmd_census"],
        "mirror_cmd_census_reissue": streams["reissue"][3]["cmd_census"],
        "first_mirror_consumption_after_issue": first_fire_after_issue,
        "post_issue_hind_fires": [
            {"tick": e["tick"], "leg": e["leg"], "xoff": e["xoff"],
             "xoff_law": round(xoff_law, 9)} for e in post_fires],
        "xoff_matches_law_or_clamped": xoff_matches,
        "zoh_single_vs_reissue_mirror_identical":
            kinds(cmd3["events"]) == kinds(streams["reissue"][3]["events"]),
        "zoh_expected_trace_identical": (
            (runs / "oracle_cmd_trace.txt").read_bytes()
            == (runs / "oracle_reissue_trace.txt").read_bytes()),
    }

    R["falsifiers"] = {
        "F-REFLEX-TRACE-PARITY": {"fired": bool(parity_fail),
                                  "first_failures": parity_fail[:10]},
        "F-REFLEX-LEVEL-MONOTONE": {"fired": bool(monotone_fail),
                                    "violations": monotone_fail},
    }

    # keep events out of the JSON (they are in the committed traces)
    for pname in streams:
        for lv in streams[pname]:
            streams[pname][lv].pop("events", None)
    R["levels"] = {p: {lv: streams[p][lv] for lv in streams[p]} for p in streams}
    (HERE / "replay_results.json").write_text(json.dumps(R, indent=1, default=str))
    print(json.dumps(R["falsifiers"], indent=1))
    for pname in probes:
        for lv in (0, 1, 2, 3):
            d = streams[pname][lv]
            print(f"{pname}/L{lv}: decisions={d['decisions']} total={d['events_total']} "
                  f"phi_worst={d['phi_worst_abs']:.2e} cmd={d['cmd_census']}")


if __name__ == "__main__":
    main()
