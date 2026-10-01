# R_AFTER diagnostic probe (agent R-after-window-verifier, 2026-09-14)
# NOT a fix, NOT part of any pass/fail protocol: classifies the gait-run
# V1b failure (gravity armed, g_contact_n = 0) as binary-wide vs
# restore-state-specific, by arming gravity on a FRESHLY-CLASSIFIED body
# (the H15 gallery bring-alive path, no session restore) on a throwaway
# engine. Reuses h15_gallery's Engine (PID-tracked kill) + bring_alive.
import json
import sys
import time
from pathlib import Path

REPO = Path(r"E:\ChimeraWork\slot-01")
sys.path.insert(0, str(REPO / "docs" / "evidence" / "agent_fleet"
                     / "SHIP" / "H15_GALLERY"))
import h15_gallery as g  # noqa: E402

PORT = 8139
OUT = REPO / "docs/evidence/agent_fleet/SHIP/R_AFTER/run1_gait" \
    / "gravity_probe_fresh_body.json"

eng = g.Engine(PORT, g.REPO / ".tmp" / "build_tick" / "Release"
               / "chimera_engine.exe")
rec = {"purpose": "classify V1b: gravity contact on a fresh-classified "
                  "body (no session restore), new binary a62c6b46",
       "port": PORT, "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
try:
    eng.start()  # asserts born EMPTY (sealed:false)
    rec["boot"] = "empty cwd, born unsealed (asserted by Engine.start)"
    body = g.bring_alive(type("B", (), {"base": eng.base})(),
                         g.OBJ_DIR / "blob.obj", 9, 25.0)
    rec["bring_alive"] = {k: body.get(k) for k in
                          ("name", "a1", "seal")}
    st0 = g.get_json(eng.base, "/tick_state")
    m_kg = st0.get("V_whole", 0.0) * 1000.0
    w_n = m_kg * 9.81
    rec["expect_weight_N"] = w_n

    # arm gravity -- COMPACT json (the arm routes parse compact only)
    arm = g.post(eng.base, "/tick_gravity", '{"on":true}')
    rec["arm"] = arm
    polls = []
    t_end = time.time() + 12.0
    while time.time() < t_end:
        s = g.get_json(eng.base, "/tick_state")
        polls.append({k: s.get(k) for k in
                      ("gravity_on", "g_contact_n", "root_y", "root_vy",
                       "n_cells", "sealed", "conserve_pct")})
        time.sleep(0.5)
    rec["polls"] = polls
    last = polls[-1]
    contact = last["g_contact_n"]
    rec["verdict"] = {
        "gravity_on_last": last["gravity_on"],
        "g_contact_n_last": contact,
        "dev_pct_from_weight": (abs(contact - w_n) / w_n * 100.0
                                if w_n else None),
        "root_y_last": last["root_y"],
        "abs_root_vy_max": max(abs(p["root_vy"]) for p in polls),
    }
    print(json.dumps(rec["verdict"], indent=2))
finally:
    eng.kill()
    rec["killed"] = "engine killed by PID (Engine.kill)"

OUT.write_text(json.dumps(rec, indent=2), encoding="utf-8")
print("wrote", OUT)
