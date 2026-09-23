# fleet_supervisor/supervisor.py -- one supervisor, one CLI.
#
# Subcommands:
#   launch   -- admit + contain a spec (JSON on stdin or --spec-file), print result JSON
#   hold     -- launch, print result JSON, then HOLD the job handles until killed
#               (this is the kill-on-owner-exit shape used by the falsifier suite)
#   complete -- graceful-then-terminate a session by id
#   status   -- folded registry + live job accounting (JSON)
#   touch    -- a lane marks activity (idle clock reset)
#   reconcile -- one reconcile pass (report only; never kills ambiguous)
#   serve    -- the long-running loop: reconcile every 15 s, complete-all on stop
#   gates    -- broker gate matrix self-check (injected inputs, no side effects)
from __future__ import annotations

import argparse
import json
import os
import sys
import time

from . import broker, jobobject, launcher, lifecycle, registry


def _load_spec(args) -> dict:
    if args.spec_file:
        with open(args.spec_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(sys.stdin.read())


def _sup(args) -> lifecycle.Supervisor:
    return lifecycle.Supervisor(
        registry_path=args.registry, control_dir=args.control,
        poll_interval_s=args.poll, complete_deadline_s=args.deadline)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="fleet_supervisor")
    ap.add_argument("--registry", default=os.environ.get("FLEET_REGISTRY_PATH", registry.DEFAULT_REGISTRY))
    ap.add_argument("--control", default=os.environ.get("FLEET_CONTROL_DIR", broker.DEFAULT_CONTROL_DIR))
    ap.add_argument("--poll", type=float, default=lifecycle.DEFAULT_POLL_INTERVAL_S)
    ap.add_argument("--deadline", type=float, default=lifecycle.DEFAULT_COMPLETE_DEADLINE_S)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("launch")
    p.add_argument("--spec-file")
    p.add_argument("--json", action="store_true", default=True)

    p = sub.add_parser("hold")
    p.add_argument("--spec-file")
    p.add_argument("--seconds", type=float, default=3600.0,
                   help="hold at most this long, then complete-all and exit")

    p = sub.add_parser("complete")
    p.add_argument("session_id")
    p.add_argument("--deadline", type=float, default=None)
    p.add_argument("--reason", default="requested")

    p = sub.add_parser("touch")
    p.add_argument("session_id")

    p = sub.add_parser("status")
    p.add_argument("--watch", action="store_true")

    p = sub.add_parser("reconcile")

    p = sub.add_parser("serve")
    p.add_argument("--interval", type=float, default=None)

    p = sub.add_parser("gates")

    args = ap.parse_args(argv)

    if args.cmd == "launch":
        sup = _sup(args)
        res = sup.launch(_load_spec(args))
        print(json.dumps(res.to_dict()))
        return 0 if res.ok else 2

    if args.cmd == "hold":
        sup = _sup(args)
        res = sup.launch(_load_spec(args))
        print(json.dumps(res.to_dict()), flush=True)
        if not res.ok:
            return 2
        t0 = time.time()
        while time.time() - t0 < args.seconds:
            time.sleep(0.1)
        sup.complete(res.session_id, reason="hold expiry")
        return 0

    if args.cmd == "complete":
        sup = _sup(args)
        out = sup.complete(args.session_id, deadline=args.deadline, reason=args.reason)
        print(json.dumps(out))
        return 0 if out.get("ok") else 2

    if args.cmd == "touch":
        sup = _sup(args)
        print(json.dumps({"session_id": args.session_id, "touched": sup.touch(args.session_id)}))
        return 0

    if args.cmd == "status":
        sup = _sup(args)
        folded = registry.fold(args.registry)
        live = {}
        for sid, rec in registry.active_sessions(args.registry).items():
            jh = sup.handles.get(sid) or jobobject.open_job(rec.get("job_name") or "")
            ent = {"status": rec.get("status"), "pid": rec.get("pid"),
                   "creation_time_us": rec.get("creation_time_us"),
                   "kind": rec.get("kind"), "owner_lane": rec.get("owner_lane"),
                   "job_name": rec.get("job_name")}
            if jh:
                try:
                    acct = jobobject.query_job_accounting(jh)
                    ent["active_processes"] = acct["active_processes"]
                    ent["total_processes"] = acct["total_processes"]
                    ent["io_bytes_total"] = acct["io_bytes_total"]
                    ent["members"] = lifecycle.live_member_identities(jh)
                except jobobject.WinError as e:
                    ent["accounting_error"] = str(e)
                if jh not in sup.handles.values():
                    jobobject.close_handle(jh)
            live[sid] = ent
        print(json.dumps({"registry_sessions": len(folded), "active": live,
                          "mode": broker.read_mode(args.control),
                          "reservation": broker.read_reservation(args.control),
                          "memory": jobobject.memory_status()}, indent=1))
        return 0

    if args.cmd == "reconcile":
        sup = _sup(args)
        rep = sup.reconcile_pass()
        print(json.dumps(rep, indent=1))
        return 0

    if args.cmd == "serve":
        sup = _sup(args)
        sup.serve(args.interval)
        return 0

    if args.cmd == "gates":
        print(json.dumps(gate_matrix(args.control, args.registry), indent=1))
        return 0

    return 1


def gate_matrix(control_dir: str, registry_path: str) -> dict:
    """The P-GATES matrix with INJECTED inputs -- no launches, no side effects."""
    results = {}
    ms_now = jobobject.memory_status()

    def mem_fn_factory(free_gib):
        def fn():
            m = dict(ms_now)
            m["free_phys_gib"] = free_gib
            return m
        return fn

    base = {"session_id": "gate-probe", "owner_lane": "gate", "worktree": None,
            "command": ["cmd", "/c", "exit"], "ports": [], "kind": "server",
            "resources": {"cpu_pct": None, "mem_gib": 8.0, "max_procs": 64}}
    ok, why = broker.admit(base, control_dir=control_dir, registry_path=registry_path)
    results["baseline_server_admitted"] = {"ok": ok, "why": why}

    gpu = dict(base, kind="gpu_phase", resources={"cpu_pct": None, "mem_gib": 8.0, "max_procs": 64})
    ok, why = broker.admit(gpu, control_dir=control_dir, registry_path=registry_path)
    results["gpu_phase_without_reservation_refused"] = {"ok": not ok, "why": why}

    b = dict(base, kind="build", resources={"mem_gib": 16.0})
    # gaming-mode check with an INJECTED mode file in a temp control dir
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        broker.write_mode("gaming", td)
        ok_g, why_g = broker.admit(b, control_dir=td, registry_path=registry_path)
        results["gaming_refuses_build"] = {"ok": not ok_g, "why": why_g}
        ok_g, why_g = broker.admit(gpu, control_dir=td, registry_path=registry_path)
        results["gaming_refuses_gpu"] = {"ok": not ok_g, "why": why_g}
        ok_g, why_g = broker.admit(base, control_dir=td, registry_path=registry_path)
        results["gaming_admits_server"] = {"ok": ok_g, "why": why_g}

    # reservation states in a FLEET-mode temp dir (default, no mode file) so
    # the reservation logic is what is actually being measured
    with tempfile.TemporaryDirectory() as td:
        broker.write_reservation({"owner_id": "train-A", "heartbeat_ts": time.time(),
                                  "expected_end_ts": time.time() + 600, "status": "held"}, td)
        ok_g, why_g = broker.admit(dict(gpu, session_id="intruder-B"),
                                   control_dir=td, registry_path=registry_path)
        results["gpu_refused_other_owner"] = {"ok": not ok_g, "why": why_g}
        ok_g, why_g = broker.admit(dict(gpu, session_id="train-A"),
                                   control_dir=td, registry_path=registry_path)
        results["gpu_admitted_owner"] = {"ok": ok_g, "why": why_g}
        broker.write_reservation({"owner_id": "train-A", "heartbeat_ts": time.time() - 999,
                                  "expected_end_ts": time.time() + 600, "status": "held"}, td)
        ok_g, why_g = broker.admit(dict(gpu, session_id="train-A"),
                                   control_dir=td, registry_path=registry_path)
        results["gpu_heartbeat_lost_is_UNCERTAIN_not_free"] = {"ok": not ok_g, "why": why_g}
        broker.write_reservation({"owner_id": "train-A", "heartbeat_ts": time.time(),
                                  "expected_end_ts": time.time() - 1, "status": "held"}, td)
        ok_g, why_g = broker.admit(dict(gpu, session_id="train-A"),
                                   control_dir=td, registry_path=registry_path)
        results["gpu_expired_end_is_STILL_OCCUPIED"] = {"ok": not ok_g, "why": why_g}

    # memory ceiling: 46 GiB declared + 8 new > 48 -> refuse
    import tempfile
    with tempfile.TemporaryDirectory() as tr:
        reg = os.path.join(tr, "r.jsonl")
        for i in range(2):
            registry.append(reg, {
                "event": "launch", "session_id": f"probe-{i}", "owner_lane": "probe",
                "kind": "server", "command": ["cmd"], "ports": [], "status": "running",
                "pid": 111111 + i, "creation_time_us": 1, "job_name": f"Local\\nonexistent-{i}",
                "resources": {"mem_gib": 23.0}, "last_activity": time.time()})
        ok_m, why_m = broker.admit(base, control_dir=control_dir, registry_path=reg)
        results["fleet_ceiling_refuses_46_plus_8"] = {"ok": not ok_m, "why": why_m}
        small = dict(base, resources={"mem_gib": 1.0})
        ok_m, why_m = broker.admit(small, control_dir=control_dir, registry_path=reg)
        results["fleet_ceiling_admits_46_plus_1"] = {"ok": ok_m, "why": why_m}

    # RAM reserve with injected low reading
    ok_r, why_r = broker.admit(base, control_dir=control_dir, registry_path=registry_path,
                               memory_status_fn=mem_fn_factory(30.0))
    results["low_free_ram_30GiB_refused"] = {"ok": not ok_r, "why": why_r}
    ok_r, why_r = broker.admit(base, control_dir=control_dir, registry_path=registry_path,
                               memory_status_fn=mem_fn_factory(40.0))
    results["free_ram_40GiB_admitted"] = {"ok": ok_r, "why": why_r}
    results["real_free_ram_gib"] = ms_now["free_phys_gib"]
    return results


if __name__ == "__main__":
    sys.exit(main())
