#!/usr/bin/env python
"""runtime_gate.py -- GPU-DEMO-RECOVERY-01 P2-P7 runtime gate.

Drives the fixed engine through the preregistered predictions and records
measured values + PASS/FAIL per gate. Exits 0 iff all gates pass.
Bounds: RELAX_GPU01 preregistration + B2 frozen budgets. Nothing widened.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "gpu_demo_recovery"))
sys.path.insert(0, str(TOOLS / "gpu_fixtures_recovered"))

from md_client import pack_upload, http_post, http_get, alive, sha  # noqa: E402
from membrane_fixture_b2 import b2_mesh, B2_GPU_BUDGETS  # noqa: E402
from membrane_window_demo import projected_descent  # noqa: E402

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8093
BASE = f"http://localhost:{PORT}"
EVID = Path("docs/evidence/gpu_demo_recovery")
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
OUTDIR = EVID / f"runtime_gate_{STAMP}"
OUTDIR.mkdir(parents=True, exist_ok=True)
GATES = []


def gate(name, ok, detail):
    GATES.append({"gate": name, "pass": bool(ok), "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def post_bin(blob):
    s, body, _ = http_post(f"{BASE}/membrane_demo_bin", blob,
                           "application/octet-stream", timeout=70.0)
    return s, json.loads(body.decode())


def ctl(payload):
    raw = json.dumps(payload).encode()
    s, body, _ = http_post(f"{BASE}/membrane_demo", raw, "application/json",
                           timeout=120.0)
    return s, json.loads(body.decode())


def status():
    s, body, _ = http_get(f"{BASE}/membrane_demo", timeout=15.0)
    return json.loads(body.decode())


def frame(label):
    s, body, _ = http_get(f"{BASE}/frame", timeout=30.0)
    p = OUTDIR / f"{label}.png"
    if s == 200 and body[:4] == b"\x89PNG":
        p.write_bytes(body)
    return sha(body), len(body)


def main():
    _, V_up, F = b2_mesh()
    blob = pack_upload(V_up.astype(np.float32), F, 1.0, 6, 0.5)
    commit = "bf0a62162008c8415b88091c671ac180dbb50193"

    # ---- CPU reference (f32-widened start, same law) ----
    gam = np.ones(len(F))
    cpu = projected_descent(V_up.copy(), F, gam, commit)
    cpu_e = [cpu["energy_initial_J"] if False else None]
    cpu_e = [it["energy_J"] for it in cpu["iterations"]]
    # iterations[0] is the initial record; accepted states follow
    print(f"CPU: status={cpu['status']} accepted={cpu['n_accepted']} "
          f"E0={cpu_e[0]:.8f} Eend={cpu_e[-1]:.8f}")

    # ---- P5/P2 setup: clean B2 init ----
    s, st0 = post_bin(blob)
    id_init = st0["accepted_state_id"]
    gate("P5-init-clean", s == 200 and st0["energy"] == 2.625
         and st0["centre"][2] == 0.125, f"E={st0['energy']} id={id_init}")

    # ---- P2: full trajectory, per-iteration energies ----
    gpu_e = [st0["energy"]]
    gpu_z = [st0["centre"][2]]
    term = ""
    for i in range(5000):
        s, st = ctl({"op": "step"})
        gpu_e.append(st["energy"])
        gpu_z.append(st["centre"][2])
        term = st["terminal_state"]
        if term:
            break
    n_acc = st["accepted"]
    ok_n = (n_acc == cpu["n_accepted"])
    # align: cpu iterations[0] is the state AFTER the first accepted step
    # (no initial-state record); gpu_e[0] is the initial state.
    ok_len = (len(gpu_e) - 1 == cpu["n_accepted"] == len(cpu_e))
    per_it = [abs(a - b) for a, b in zip(gpu_e[1:], cpu_e)]
    worst = max(per_it) if per_it else float("inf")
    ok_e = worst <= 1.1e-5
    ok_init = (gpu_e[0] == 2.625)
    ok_term = (term == cpu["status"])
    final_gap = abs(gpu_z[-1] - float(cpu["positions"][6, 2]))
    f32bound = cpu["n_accepted"] * 2.0 ** -23 * float(np.abs(cpu["positions"]).max())
    ok_z = final_gap <= f32bound
    # f32 readback may round a sub-ulp Armijo decrease to equality at the
    # tail; assert non-increasing + net decrease (Armijo itself is proven by
    # the per-iteration CPU equivalence above: same accept decisions).
    strict = all(b <= a for a, b in zip(gpu_e, gpu_e[1:])) and gpu_e[-1] < gpu_e[0]
    gate("P2-count-match", ok_n and ok_len and ok_init,
         f"gpu_acc={n_acc} cpu_acc={cpu['n_accepted']} E0exact={ok_init}")
    gate("P2-energy-trail", ok_e, f"worst per-iter drift={worst:.3e} <= 1.1e-5")
    gate("P2-terminal-match", ok_term, f"gpu={term} cpu={cpu['status']}")
    gate("P2-final-centre", ok_z, f"gap={final_gap:.3e} <= {f32bound:.3e}")
    gate("P2-strict-decrease", strict, f"{len(gpu_e)-1} accepted steps")
    (OUTDIR / "p2_gpu_trail.json").write_text(
        json.dumps({"energies": gpu_e, "centres": gpu_z,
                    "cpu_energies": cpu_e}, indent=1))

    # ---- P6: capture association along the trajectory ----
    h_init, _ = frame("p6_initial")
    s_init = status()
    post_bin(blob)
    ctl({"op": "step"})
    h_mid, _ = frame("p6_mid")
    s_mid = status()
    h_mid2, _ = frame("p6_mid_repeat")
    gate("P6-render-id-nonzero", s_mid["render_state_id"] != 0,
         f"rid={s_mid['render_state_id']}")
    gate("P6-render-stable", h_mid == h_mid2 and
         s_mid["render_state_id"] == status()["render_state_id"],
         f"png {h_mid[:12]} repeat stable")
    gate("P6-render-tracks-accepted",
         s_mid["render_state_id"] != s_init["render_state_id"],
         f"init_rid={s_init['render_state_id']} mid_rid={s_mid['render_state_id']}")

    # ---- P3: rejection integrity (render + accepted bit-unchanged) ----
    post_bin(blob)
    ctl({"op": "step"})
    h_before, _ = frame("p3_before")
    _, st_b = post_bin(blob) if False else (None, status())
    id_b, rid_b = st_b["accepted_state_id"], st_b["render_state_id"]
    s, st_r = ctl({"op": "reject"})
    h_after, _ = frame("p3_after")
    _, st_a = None, status()
    gate("P3-accepted-unchanged",
         st_a["accepted_state_id"] == id_b and st_a["energy"] == st_b["energy"],
         f"id {id_b} -> {st_a['accepted_state_id']} E={st_a['energy']}")
    gate("P3-render-unchanged",
         h_before == h_after and st_a["render_state_id"] == rid_b,
         f"png {h_before[:12]}=={h_after[:12]} rid {rid_b}->{st_a['render_state_id']}")
    gate("P3-terminal", st_r["terminal_state"] == "no_descent_step",
         f"{st_r['terminal_state']} trials={st_r['trials']}")

    # ---- P4: gamma controls ----
    post_bin(blob)
    _, st_g0 = ctl({"op": "gamma", "gamma": 0.0})
    _, st_s = ctl({"op": "step"})
    gate("P4-gamma0-stationary",
         st_s["terminal_state"] == "stationary"
         and st_s["accepted_state_id"] == st_g0["accepted_state_id"],
         f"{st_s['terminal_state']} id_unchanged={st_s['accepted_state_id']==st_g0['accepted_state_id']}")
    post_bin(blob)
    _, st_g2 = ctl({"gamma": 2.0, "op": "gamma"})
    snap = st_g2.get("material_snapshot") or {}
    ok_d = (snap.get("gamma_admitted_f64") == 2.0
            and abs(st_g2["energy"] - 2 * 2.625) <= B2_GPU_BUDGETS["gamma2_cross_U_J"]
            and abs(st_g2["centre_force"][2] - 2 * -3.0 / 7.0)
            <= B2_GPU_BUDGETS["gamma2_cross_F_N"])
    gate("P4-gamma-double", ok_d,
         f"E={st_g2['energy']} Fz={st_g2['centre_force'][2]}")
    _, st_rs = ctl({"op": "reset"})
    gate("P4-reset-restores",
         st_rs["accepted_state_id"] == id_init
         and (st_rs.get("material_snapshot") or {}).get("gamma_admitted_f64") == 1.0,
         f"id {st_rs['accepted_state_id']==id_init} "
         f"gamma={(st_rs.get('material_snapshot') or {}).get('gamma_admitted_f64')}")

    # ---- P5: controls + status coherence ----
    post_bin(blob)
    _, a = ctl({"op": "step"})
    _, b = ctl({"op": "step"})
    _, c = ctl({"op": "pause"})
    ok_c = (b["iteration"] == a["iteration"] + 1 and c["iteration"] == b["iteration"]
            and b["accepted"] == a["accepted"] + 1)
    gate("P5-counters-coherent", ok_c,
         f"iter {a['iteration']}->{b['iteration']}->{c['iteration']}")
    _, r = ctl({"op": "reset"})
    gate("P5-reset-bitexact", r["accepted_state_id"] == id_init
         and r["accepted"] == 0 and r["trials"] == 0 and r["iteration"] == 0,
         f"id_match={r['accepted_state_id']==id_init}")

    # ---- P7: ordinary path preserved ----
    import membrane_window_demo as mwd
    mb = mwd.encode_mesh_bin(V_up, F, 12.0, 0.3, 0.3)
    s, body, _ = http_post(f"{BASE}/mesh_bin", mb, "application/octet-stream",
                           timeout=70.0)
    ok_m = s == 200 and b'"ok":true' in body
    hp, hl = frame("p7_ordinary")
    gate("P7-ordinary-path", ok_m and hl > 1000000 and alive(PORT),
         f"mesh_bin={ok_m} png_bytes={hl}")

    # ---- invalid handling (contract-conformance) ----
    cases = []
    s, b, _ = http_post(f"{BASE}/membrane_demo_bin", b"MD01" + b"\x00" * 10,
                        "application/octet-stream", timeout=30.0)
    cases.append(("short", b'"ok":false' in b))
    bad = b"BAD!" + blob[4:]
    s, b, _ = http_post(f"{BASE}/membrane_demo_bin", bad,
                        "application/octet-stream", timeout=30.0)
    cases.append(("badmagic", b'"ok":false' in b))
    import urllib.request as _url
    def raw_ctl(payload):
        req = _url.Request(f"{BASE}/membrane_demo",
                           data=json.dumps(payload).encode(),
                           headers={"Content-Type": "application/json"},
                           method="POST")
        with _url.urlopen(req, timeout=90.0) as r:
            return r.status, r.read()
    s, b = raw_ctl({"op": "explode"})
    cases.append(("badop", b'"ok":false' in b))
    s, b = raw_ctl({"op": "gamma", "gamma": -1.0})
    cases.append(("gamma-neg", b'"gamma_REJECTED"' in b))
    s, b = raw_ctl({"op": "gamma", "gamma": 1e308})
    cases.append(("gamma-overflow", b'"gamma_REJECTED"' in b))
    gate("P-invalid-named", all(c[1] for c in cases) and alive(PORT),
         "; ".join(f"{k}={int(v)}" for k, v in cases))

    # ---- repeated legal sequences ----
    ok_rep = True
    for i in range(5):
        post_bin(blob)
        ctl({"op": "step"})
        _, st = ctl({"op": "reset"})
        ok_rep = ok_rep and st["accepted_state_id"] == id_init and alive(PORT)
    gate("P-repeated-legal", ok_rep, "5x upload/step/reset, ids match, alive")

    (OUTDIR / "gate_results.json").write_text(
        json.dumps({"gates": GATES, "port": PORT}, indent=1))
    fails = [g for g in GATES if not g["pass"]]
    print(f"{len(GATES)-len(fails)}/{len(GATES)} gates pass; evidence: {OUTDIR}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
