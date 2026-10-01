#!/usr/bin/env python3
"""AN2 ONE-LIMB: the causal demos on the CURRENT binary (scratch engine).

Run against a FRESH scratch only. Sequencing discipline follows the
standing BATTERY.md laws: quiet-rest prelude (the quiet window is 1 s;
a stimulus that arrives during the refractory window has its rising
edge consumed silently), full decay waits between phases (tau 0.5 s,
the 0.1 mm cutoff needs ~8 taus), breathing suspended (it is
pressure-blind by construction, but a demo should not depend on that).

Demo A -- the sensory-path disconnect (the existing C1 nerve, the
coarse-grained ancestor of the patch-path cut the ONE-LIMB code adds):
  arm -> touch left shin -> flinch fires (active contribution) ->
  cut the nerve -> the SAME touch: NO active response while the
  passive mechanical response (cell pressure, dimple) matches ->
  reconnect -> no synthesized spike. Consistent IDs + engine timestamps.

Demo B -- isolation by controlled boundary loading (the honest
substitute for the NOT-implemented open-wound fluid transfer):
  press inside the foot cell -> the foot cell's pressure rises while
  the other cells' pressures stay EXACTLY 0 (no fluid exchange across
  an intact septum) and the volume books stay balanced.
"""
import json
import sys
import time
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8171"
OUT = sys.argv[2] if len(sys.argv) > 2 else \
    "docs/evidence/agent_fleet/SHIP/ONE_LIMB/demo_nerve_cut_scratch.json"

SHIN_HIT = [0.7523937821388245, 1.4666244983673096, 0.0418538823723793]
FOOT_HIT = [0.49212169647216797, 0.04936373606324196, 1.2293583154678345]
FORCE_N = 20000.0
DECAY_WAIT_S = 5.0     # ~10 tissue taus: the 0.1 mm cutoff is reached


def post(path, body):
    req = urllib.request.Request(
        BASE + path, data=body.encode(), method="POST",
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def get_state():
    return json.loads(urllib.request.urlopen(BASE + "/tick_state",
                                             timeout=10).read())


def poll(seconds, dt=0.012):
    rows = []
    t_end = time.time() + seconds
    while time.time() < t_end:
        s = get_state()
        rows.append({
            "wall_s": round(time.time(), 4),
            "ts_us": s["ts_us"], "ticks": s["ticks"],
            "env_l": s["reflex_flinch_env_l"],
            "env_r": s["reflex_flinch_env_r"],
            "dimple_m": s["dimple_m"],
            "P": [c["P"] for c in s["cells"]],
            "V": [c["V"] for c in s["cells"]],
        })
        time.sleep(dt)
    return rows


def summarize(rows):
    return {
        "n": len(rows),
        "env_l_max": max(r["env_l"] for r in rows),
        "env_r_max": max(r["env_r"] for r in rows),
        "dimple_max_m": max(r["dimple_m"] for r in rows),
        "P_max_per_cell": [max(r["P"][i] for r in rows)
                           for i in range(len(rows[0]["P"]))],
    }


def first_env_row(rows):
    for r in rows:
        if r["env_l"] > 0.0:
            return r
    return None


def wait_full_rest(timeout=30.0):
    """Wait until envelopes, pressures AND dimple are all exactly zero.

    The flinch's own pin write moves the mesh, the sealed cells' volumes
    follow, and the relaxation can RE-TRIGGER rising edges while it
    settles -- a fixed 5 s sleep is inside that loop (measured). Rest is
    a STATE, waited for, not assumed; the settle duration is the return
    value (a measured number for the evidence)."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = get_state()
        if (s["reflex_flinch_env_l"] == 0.0 and s["reflex_flinch_env_r"] == 0.0
                and s["dimple_m"] == 0.0
                and max(c["P"] for c in s["cells"]) == 0.0):
            return round(time.time() - t0, 2)
        time.sleep(0.2)
    s = get_state()
    raise AssertionError("no full rest in %.0fs: env_l=%s P=%s dimple=%s"
                         % (timeout, s["reflex_flinch_env_l"],
                            [c["P"] for c in s["cells"]], s["dimple_m"]))


def passive_window(rows, seconds=0.25):
    """the pre-reflex mechanical signature (the flex back-reaction needs
    a fire + a tick to manifest; the first window is the pure press)"""
    t0 = rows[0]["wall_s"]
    win = [r for r in rows if r["wall_s"] - t0 <= seconds]
    return {
        "n": len(win),
        "P_max_per_cell": [max(r["P"][i] for r in win)
                           for i in range(len(rows[0]["P"]))],
        "dimple_max_m": max(r["dimple_m"] for r in win),
    }


def main():
    ev = {"base": BASE, "shin_hit": SHIN_HIT, "foot_hit": FOOT_HIT,
          "force_n": FORCE_N, "decay_wait_s": DECAY_WAIT_S}

    # ── A0: fresh-boot baseline, quiet rest ─────────────────────────
    base = get_state()
    ev["baseline"] = {
        "ts_us": base["ts_us"], "ticks": base["ticks"],
        "n_cells": base["n_cells"],
        "P": [c["P"] for c in base["cells"]],
        "v0": [c["v0"] for c in base["cells"]],
        "reflex_on": base["reflex_on"], "dimple_m": base["dimple_m"],
        "conserve_pct": base["conserve_pct"],
    }
    assert base["n_cells"] == 4, "expected the 4-band tree"
    assert base["reflex_on"] is False, "scratch must boot with reflexes OFF"
    assert max(c["P"] for c in base["cells"]) == 0.0 \
        and base["dimple_m"] == 0.0, "not at rest"

    # ── A1: measure the drive pins once (the documented resolution law),
    # then return everything to authored rest and let the quiet window
    # run its full 1 s BEFORE any stimulus ────────────────────────────
    ev["A_rung_arm"] = {
        "gravity": post("/tick_gravity", '{"on":true}'),
        "stance": post("/tick_stance", '{"on":true}'),
        "gait": post("/tick_gait", '{"on":true}'),
    }
    time.sleep(0.5)
    ev["A_rung_off"] = {
        "gait": post("/tick_gait", '{"on":false}'),
        "stance": post("/tick_stance", '{"on":false}'),
        "gravity": post("/tick_gravity", '{"on":false}'),
    }
    time.sleep(2.0)   # > the 1 s quiet window, at authored rest
    assert max(c["P"] for c in get_state()["cells"]) == 0.0, \
        "rungs must settle to rest"

    # ── A2: arm, suspend the breath (a demo must not need the
    # pressure-blindness construction), wait out the quiet window ────
    ev["A_arm"] = post("/tick_reflex",
                       '{"on":true,"breathing":false}')
    time.sleep(1.5)
    st = get_state()
    ev["A_pins_resolved"] = {"flinch_pin_l": st["reflex_flinch_pin_l"],
                             "flinch_pin_r": st["reflex_flinch_pin_r"],
                             "quiet_s": st["reflex_quiet_s"],
                             "p_coupling": st["reflex_p_coupling"]}
    assert st["reflex_flinch_pin_l"] == 17, "expected strut pin L = 17"
    assert st["reflex_p_coupling"] is True

    # ── A3: CONNECTED case ──────────────────────────────────────────
    t0 = time.time()
    r_touch = post("/tick_touch",
                   json.dumps({"hit": SHIN_HIT, "force_n": FORCE_N}))
    ev["A_connected_touch_response"] = r_touch
    rows_conn = poll(2.5)
    post("/tick_touch_clear", "{}")
    ev["A_connected"] = summarize(rows_conn)
    fe = first_env_row(rows_conn)
    ev["A_connected_latency"] = None if fe is None else {
        "touch_to_first_env_s": round(fe["wall_s"] - t0, 4),
        "poll_dt_s": 0.012,
        "first_env_ts_us": fe["ts_us"], "first_env_ticks": fe["ticks"],
        "P_at_fire_Pa": fe["P"],
    }
    assert ev["A_connected"]["env_l_max"] > 0.0, \
        "CONNECTED case must fire the flinch (active contribution)"
    ev["A_connected_passive_250ms"] = passive_window(rows_conn)
    ev["A_settle_1_s"] = wait_full_rest()

    # ── A4: THE NERVE CUT (the sensory path disconnect) ─────────────
    ev["A_nerve_cut_response"] = post("/tick_reflex",
                                      '{"pressure_coupling":false}')
    st = get_state()
    ev["A_cut_state"] = {"p_coupling": st["reflex_p_coupling"]}
    assert st["reflex_p_coupling"] is False

    # ── A5: the IDENTICAL touch, path cut ───────────────────────────
    t0 = time.time()
    r_touch = post("/tick_touch",
                   json.dumps({"hit": SHIN_HIT, "force_n": FORCE_N}))
    ev["A_cut_touch_response"] = r_touch
    rows_cut = poll(2.5)
    post("/tick_touch_clear", "{}")
    ev["A_cut"] = summarize(rows_cut)
    ev["A_cut_passive_250ms"] = passive_window(rows_cut)
    ev["A_settle_2_s"] = wait_full_rest()

    # ── A6: reconnect; NO stimulus; no synthesized spike ────────────
    ev["A_reconnect_response"] = post("/tick_reflex",
                                      '{"pressure_coupling":true}')
    rows_rec = poll(1.5)
    ev["A_reconnect_no_touch"] = summarize(rows_rec)
    assert ev["A_reconnect_no_touch"]["env_l_max"] == 0.0, \
        "reconnect must not synthesize a stale spike (prereg P10)"
    ev["A_off"] = post("/tick_reflex", '{"on":false}')

    # ── DEMO B: isolation by controlled boundary loading ────────────
    st_rest = get_state()
    assert max(c["P"] for c in st_rest["cells"]) == 0.0 \
        and st_rest["dimple_m"] == 0.0, \
        "B needs full rest"
    t0 = time.time()
    r_touch = post("/tick_touch",
                   json.dumps({"hit": FOOT_HIT, "force_n": FORCE_N}))
    ev["B_touch_response"] = r_touch
    rows_foot = poll(2.5)
    post("/tick_touch_clear", "{}")
    ev["B_foot_press"] = summarize(rows_foot)
    ev["B_isolation"] = {
        "foot_cell_P_max_Pa": ev["B_foot_press"]["P_max_per_cell"][0],
        "other_cells_P_max_Pa": ev["B_foot_press"]["P_max_per_cell"][1:],
        "conserve_pct_during": get_state()["conserve_pct"],
    }
    ev["B_settle_s"] = wait_full_rest()
    end = get_state()
    ev["B_final_state"] = {"P": [c["P"] for c in end["cells"]],
                           "dimple_m": end["dimple_m"],
                           "conserve_pct": end["conserve_pct"]}

    # ── the verdict numbers ─────────────────────────────────────────
    ev["verdict"] = {
        "A_fires_connected": ev["A_connected"]["env_l_max"] > 0,
        "A_silent_cut": ev["A_cut"]["env_l_max"] == 0,
        # The passive response REMAINS with the path cut: the pressed
        # cell still pressurizes (acceptance 4) and the dimple is
        # identical. The connected-minus-cut delta IS the active
        # contribution's mechanical coupling (acceptance 3's law: the
        # reflex-mediated remote responses vanish -- the foot/thigh
        # cells read exactly 0 with the path cut).
        "A_passive_remains_cut_Pa":
            ev["A_cut"]["P_max_per_cell"][3] > 0.0,
        "A_passive_dimple_identical":
            ev["A_connected"]["dimple_max_m"]
            == ev["A_cut"]["dimple_max_m"],
        "A_active_delta_pressed_cell_Pa":
            ev["A_connected"]["P_max_per_cell"][3]
            - ev["A_cut"]["P_max_per_cell"][3],
        "A_remote_foot_cell_connected_Pa":
            ev["A_connected"]["P_max_per_cell"][0],
        "A_remote_foot_cell_cut_Pa":
            ev["A_cut"]["P_max_per_cell"][0],
        "A_passive_dimple_matches":
            abs(ev["A_connected_passive_250ms"]["dimple_max_m"]
                - ev["A_cut_passive_250ms"]["dimple_max_m"])
            <= 0.02 * ev["A_connected_passive_250ms"]["dimple_max_m"],
        "B_no_exchange": all(p == 0.0 for p in
                             ev["B_isolation"]["other_cells_P_max_Pa"]),
        "latency_connected_s": None if ev["A_connected_latency"] is None
        else ev["A_connected_latency"]["touch_to_first_env_s"],
    }
    with open(OUT, "w") as f:
        json.dump(ev, f, indent=1)
    print(json.dumps({"A_connected": ev["A_connected"],
                      "A_latency": ev["A_connected_latency"],
                      "A_cut": ev["A_cut"],
                      "A_reconnect": ev["A_reconnect_no_touch"],
                      "B_isolation": ev["B_isolation"],
                      "verdict": ev["verdict"]}, indent=1))


def wait_rest(seconds):
    """wait, then verify the field fully cleared (deterministic rest)"""
    time.sleep(seconds)
    s = get_state()
    return {"dimple_m": s["dimple_m"], "P": [c["P"] for c in s["cells"]],
            "env_l": s["reflex_flinch_env_l"]}


if __name__ == "__main__":
    main()
