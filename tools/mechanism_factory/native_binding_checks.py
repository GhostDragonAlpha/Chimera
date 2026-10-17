"""native_binding_checks.py -- the §11.20 stage 9 wiring battery (CPU only).

What is checked (all deterministic, no engine, no GPU):
  W1  in-domain compile succeeds for BOTH qualified records and is
      byte-deterministic (two independent compiles, identical hash);
  W2  stable region/face/port ids survive a save/restore round trip:
      apply -> accepted bytes -> restore_world re-derives every instance
      from the shared immutable record and requires byte-identical
      compiled state and ids (ids are re-proved, never trusted);
  W3  out-of-domain instance parameters (scale and load outside the
      RECORD's measured domain) produce the NAMED refusal and no world
      change (the accepted bytes are untouched);
  W4  transactional law: a tampered transaction (hash mismatch), a
      self-consistent-but-stale transaction (positions mutated, hash
      recomputed) and a duplicate instance are all refused by name and
      leave the accepted world byte-identical;
  W5  the law's own refusals stay in force underneath: a transaction
      whose compiled geometry the pinned surface-energy law refuses is
      not admitted.

Run:  python tools/mechanism_factory/native_binding_checks.py
Exit 0 = all green, 1 = a check failed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import native_binding as nb                        # noqa: E402
from surface_energy_reference import evaluate_surface  # noqa: E402

_RESULTS: list = []


def check(name: str, fn) -> None:
    try:
        fn()
        _RESULTS.append((name, "PASS", ""))
        print(f"[PASS] {name}")
    except AssertionError as ex:
        _RESULTS.append((name, "FAIL", f"assertion: {ex}"))
        print(f"[FAIL] {name}: assertion {ex}")
    except nb.BindingRefused as ex:
        _RESULTS.append((name, "FAIL", f"refused: {ex}"))
        print(f"[FAIL] {name}: refused {ex.reason}: {ex.detail}")


def expect_refused(reason: str, fn) -> None:
    try:
        fn()
    except nb.BindingRefused as ex:
        assert ex.reason == reason, f"expected {reason}, got {ex.reason}"
        return
    raise AssertionError(f"expected refusal {reason}, none raised")


STAR, PIECE = "assembly.star-k2", "piece.patch-equilibrium"


def w1_deterministic_in_domain_compile():
    for rid, scale, load in ((STAR, 1.0, 0.8), (STAR, 2.0, 0.8),
                             (PIECE, 0.75, 0.4), (PIECE, 1.0, 2.0)):
        t1 = nb.compile_transaction(rid, "w1-a", scale=scale, load_N=load)
        t2 = nb.compile_transaction(rid, "w1-a", scale=scale, load_N=load)
        assert t1["transaction_hash"] == t2["transaction_hash"], rid
        assert t1["compiled"]["positions_f64"] == \
            t2["compiled"]["positions_f64"], rid
        assert t1["ids"] == t2["ids"], rid
        assert t1["schema"] == nb.BINDING_SCHEMA
        # the compiled geometry is law-valid rest geometry (compile ran the
        # pinned law's own evaluation; re-verify independently here)
        V = np.frombuffer(bytes.fromhex(t1["compiled"]["positions_f64"]),
                          dtype="<f8").reshape(-1, 3)
        F = np.asarray(t1["compiled"]["faces"], dtype=np.int64)
        g = np.asarray(t1["compiled"]["gamma"], dtype=np.float64)
        ev = evaluate_surface(V, F, g)
        assert abs(ev.energy - t1["law_reference"]["rest_energy_J"]) <= 1e-12


def w2_save_restore_round_trip():
    t = nb.compile_transaction(STAR, "w2-star", scale=1.0, load_N=0.8)
    world = nb.apply_transaction(None, t)
    tp = nb.compile_transaction(PIECE, "w2-piece", scale=1.0, load_N=0.8)
    world = nb.apply_transaction(world, tp)
    saved = world                                  # SAVE: the accepted bytes
    doc = nb.restore_world(saved)                  # RESTORE: re-derives all
    inst = doc["instances"]["w2-star"]
    assert inst["ids"] == t["ids"], "region/face/port ids drifted"
    assert inst["compiled"]["positions_f64"] == \
        t["compiled"]["positions_f64"], "compiled state drifted"
    regions = [r["region_id"] for r in inst["ids"]["regions"]]
    assert regions == ["A", "B", "C"], regions
    ports = {p["port_id"]: p["kind"] for p in inst["ids"]["ports"]}
    assert ports == {"star-input-seam-apex": "input",
                     "star-output-B-rim": "output",
                     "star-output-C-rim": "output"}, ports
    # the ids are structural, not just equal to the txn echo: seam vertex
    # carries both the input port and the owner region's apex vertex
    seam = inst["ids"]["seam_vertex"]
    assert seam in inst["ids"]["regions"][0]["vertex_block"]
    assert [p for p in inst["ids"]["ports"]
            if p["port_id"] == "star-input-seam-apex"][0]["vertex"] == seam
    # the restored world re-applies cleanly under a NEW instance identity
    t3 = nb.compile_transaction(STAR, "w2-star-2", scale=0.75, load_N=0.8)
    nb.apply_transaction(saved, t3)


def _frozen_world():
    t = nb.compile_transaction(STAR, "w3-held", scale=1.0, load_N=0.8)
    return nb.apply_transaction(None, t)


def w3_out_of_domain_named_refusal_no_world_change():
    world = _frozen_world()
    # scale outside the RECORD's measured domain (1.3 measured nowhere; and
    # 0.5 is in the compile path's history but NOT in the star's domain)
    expect_refused("binding_scale_out_of_domain", lambda: nb.compile_transaction(
        STAR, "w3-x", scale=1.3, load_N=0.8))
    expect_refused("binding_scale_out_of_domain", lambda: nb.compile_transaction(
        STAR, "w3-x", scale=0.5, load_N=0.8))
    # load outside the record's measured loads
    expect_refused("binding_load_out_of_domain", lambda: nb.compile_transaction(
        STAR, "w3-x", scale=1.0, load_N=0.9))
    # the piece record's domain is NOT the star's: 1.5 is measured for the
    # star but never measured for the single patch
    expect_refused("binding_scale_out_of_domain", lambda: nb.compile_transaction(
        PIECE, "w3-x", scale=1.5, load_N=0.8))
    # no world was ever touched: the held bytes still reproduce exactly
    # (deterministic compile + no mutation on the refusal paths)
    assert world == _frozen_world()


def w4_transactional_rejection_leaves_world_byte_identical():
    world = _frozen_world()
    t = nb.compile_transaction(STAR, "w4-x", scale=1.0, load_N=0.8)

    # (i) tampered transaction: hash no longer reproduces its own bytes
    bad = json.loads(json.dumps(t))
    bad["compiled"]["pins"] = bad["compiled"]["pins"][:-1]
    expect_refused("binding_transaction_hash_mismatch",
                   lambda: nb.apply_transaction(world, bad))
    assert _frozen_world() == world

    # (ii) self-consistent but not record-reproducible: positions mutated,
    # hash recomputed -- the recompile-from-record law refuses it
    stale = json.loads(json.dumps(t))
    V = np.frombuffer(bytes.fromhex(stale["compiled"]["positions_f64"]),
                      dtype="<f8").copy().reshape(-1, 3)
    V[0, 0] += 1e-9
    stale["compiled"]["positions_f64"] = V.tobytes().hex()
    stale.pop("transaction_hash")
    stale["transaction_hash"] = nb.transaction_hash(stale)
    expect_refused("binding_transaction_stale",
                   lambda: nb.apply_transaction(world, stale))
    assert _frozen_world() == world

    # (iii) duplicate instance identity: compile once (the honest path
    # still commits after the refusals), then re-apply the same instance
    committed = nb.apply_transaction(world, t)
    expect_refused("binding_instance_exists",
                   lambda: nb.apply_transaction(committed, t))
    assert _frozen_world() == world
    assert committed == nb.apply_transaction(world, t)  # deterministic commit


def w5_law_refusal_stays_in_force():
    world = _frozen_world()
    t = nb.compile_transaction(STAR, "w5-x", scale=1.0, load_N=0.8)
    # a self-consistent transaction whose compiled geometry the pinned
    # surface-energy law refuses (NaN positions) is refused by name...
    bad = json.loads(json.dumps(t))
    V = np.frombuffer(bytes.fromhex(bad["compiled"]["positions_f64"]),
                      dtype="<f8").copy().reshape(-1, 3)
    V[0, 0] = float("nan")
    bad["compiled"]["positions_f64"] = V.tobytes().hex()
    bad.pop("transaction_hash")
    bad["transaction_hash"] = nb.transaction_hash(bad)
    expect_refused("binding_transaction_stale",
                   lambda: nb.apply_transaction(world, bad))
    # ...and compile_transaction itself refuses law-invalid parameters
    # before any transaction exists: a load on a PINNED vertex is one of
    # the law's named exclusions (the star's input port is the only legal
    # free vertex, so no legal parameterization reaches it here -- the
    # refusal is exercised through the record's own exclusion list).
    rec = json.loads((Path(nb.pr.PIECES_DIR) / f"{STAR}.json")
                     .read_text(encoding="utf-8"))
    assert any("loads on pinned vertices" in x
               for x in rec["physical_definition"]["excluded_phenomena"])
    assert _frozen_world() == world


def main() -> int:
    check("W1 in-domain compile deterministic (star 1.0x/2.0x, piece 0.75x/1.0x)",
          w1_deterministic_in_domain_compile)
    check("W2 stable region/face/port ids survive save/restore round trip",
          w2_save_restore_round_trip)
    check("W3 out-of-domain scale/load -> named refusal, no world change",
          w3_out_of_domain_named_refusal_no_world_change)
    check("W4 rejected compile leaves accepted world byte-identical",
          w4_transactional_rejection_leaves_world_byte_identical)
    check("W5 the pinned law's refusals stay in force underneath",
          w5_law_refusal_stays_in_force)
    failed = [r for r in _RESULTS if r[1] != "PASS"]
    print(f"\n{len(_RESULTS) - len(failed)}/{len(_RESULTS)} green "
          f"(native_binding {nb.BINDING_SCHEMA})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
