#!/usr/bin/env python
"""regression.py -- GPU-DEMO-RECOVERY-01 failure-mechanism regression.

Each case DEMONSTRATES failure on the unrepaired build and must pass on the
repaired one. Exits 0 iff all pass; prints a falsifier table otherwise.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import numpy as np

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "gpu_demo_recovery"))
sys.path.insert(0, str(TOOLS / "gpu_fixtures_recovered"))

from md_client import pack_upload, http_post, http_get, alive, sha  # noqa: E402
from membrane_fixture_b2 import b2_mesh  # noqa: E402

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8093
BASE = f"http://localhost:{PORT}"
ROWS = []


def check(name, ok, detail):
    ROWS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def post_bin(blob):
    return http_post(f"{BASE}/membrane_demo_bin", blob,
                     "application/octet-stream", timeout=70.0)


def ctl(payload):
    raw = json.dumps(payload).encode()
    return http_post(f"{BASE}/membrane_demo", raw, "application/json",
                     timeout=90.0)


def status():
    s, body, _ = http_get(f"{BASE}/membrane_demo", timeout=15.0)
    return s, json.loads(body.decode())


def b2blob():
    _, V_up, F = b2_mesh()
    return pack_upload(V_up.astype(np.float32), F, 1.0, 6, 0.5)


def main():
    blob = b2blob()
    # clean B2 baseline
    s, body, _ = post_bin(blob)
    st = json.loads(body.decode())
    e0 = st["energy"]
    id0 = st["accepted_state_id"]
    f0 = tuple(st["centre_force"])

    # R1: cross-size re-upload must be REFUSED by name (never silently accepted)
    _, V, F = b2_mesh()
    V2 = np.vstack([V, V + np.array([2.0, 0.0, 0.0])])
    F2 = np.vstack([F, F + 7])
    big = pack_upload(V2.astype(np.float32), F2, 1.0, 6, 0.5)
    s, body, _ = post_bin(big)
    ok = s == 200 and '"ok":false' in body.decode()
    check("R1-cross-size-refused", ok and alive(PORT),
          f"http={s} alive={alive(PORT)} body={body[:120]!r}")

    # restore B2
    post_bin(blob)

    # R2/R3: degenerate + NaN uploads refused
    Vd = np.zeros((7, 3), dtype=np.float32)
    Fd = np.array([[6, k, (k + 1) % 6] for k in range(6)])
    s, body, _ = post_bin(pack_upload(Vd, Fd, 1.0, 6, 0.5))
    check("R2-degenerate-refused", '"ok":false' in body.decode(),
          f"http={s} body={body[:120]!r}")
    Vn = np.zeros((7, 3), dtype=np.float32)
    Vn[3, 0] = np.nan
    s, body, _ = post_bin(pack_upload(Vn, Fd, 1.0, 6, 0.5))
    check("R3-nan-refused", '"ok":false' in body.decode(),
          f"http={s} body={body[:120]!r}")
    post_bin(blob)

    # R4: gamma admits 2.0 regardless of key order; energy doubles at fixed state
    s, body, _ = ctl({"op": "gamma", "gamma": 2.0})
    st = json.loads(body.decode())
    snap = st.get("material_snapshot") or {}
    admitted2 = snap.get("gamma_admitted_f64") == 2.0
    e2 = st["energy"]
    # energy at fixed B2 state must double: 2*2.625 within frozen doubling bound
    from membrane_fixture_b2 import B2_GPU_BUDGETS
    bound = B2_GPU_BUDGETS["gamma2_cross_U_J"]
    fbound = B2_GPU_BUDGETS["gamma2_cross_F_N"]
    fz2 = st["centre_force"][2]
    ok = (admitted2 and abs(e2 - 2 * e0) <= bound
          and abs(fz2 - 2 * f0[2]) <= fbound)
    check("R4-gamma-opfirst-doubles", ok,
          f"admitted2={admitted2} E={e2} expect~{2*e0} Fz={fz2} expect~{2*f0[2]}")
    s, body, _ = ctl({"gamma": 0.5, "op": "gamma"})
    st = json.loads(body.decode())
    snap = st.get("material_snapshot") or {}
    check("R4b-gamma-keyfirst", snap.get("gamma_admitted_f64") == 0.5,
          f"snapshot={snap} E={st.get('energy')}")

    # R5: reset restores fresh forces (not stale zeros)
    ctl({"op": "gamma", "gamma": 0.0})
    s, body, _ = ctl({"op": "reset"})
    st = json.loads(body.decode())
    fresh = tuple(st["centre_force"])
    ok = (st["accepted_state_id"] == id0 and
          all(abs(a - b) < 1e-9 for a, b in zip(fresh, f0)))
    check("R5-reset-fresh-forces", ok, f"forces={fresh} init={f0}")

    # R7: render association present (nonzero stable render id after a frame)
    http_get(f"{BASE}/frame", timeout=30.0)
    s, st = status()
    rid = st.get("render_state_id", 0)
    check("R7-render-associated", isinstance(rid, int) and rid != 0,
          f"render_state_id={rid} accepted={st.get('accepted_state_id')}")

    fails = [r for r in ROWS if not r[1]]
    print(f"{len(ROWS)-len(fails)}/{len(ROWS)} pass")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
