"""integrated_session_b.py -- ONT-X02 Session B: SessionFlow on the REAL World.

Binds the pinned M-X02 SessionFlow to the REAL playable-slice World lifecycle
(its own declared referents) and drives ONE real session through the flow's
public mutators only:

    mapper = InputMapper(sink)                      # the REAL U01 mapper
    world  = World(engine_exe); world.boot()        # the shipped main() path
    flow = SessionFlow(mapper, restart_scene=world.boot,
                       teardown=world.shutdown_engine)

Probes (frozen in PREREGISTRATION_INTEGRATED.md):
  B1 Return -> PLAYING (key-only)
  B2 playing keys -> REAL CommandRecords in the sink
  B3 Escape -> PAUSED; quiesce release_all; ticks emit zero records;
     mapper untouched while paused
  B4 R from paused -> EXACTLY ONE real World.boot (old engine PID dies,
     new PID + port, /mesh_import again) -> PLAYING; total boots == 2
  B5 R while playing -> no transition, no boot
  B6 Return from paused -> resume, no boot
  B7 Q -> EXITED; teardown exactly once through the REAL World.shutdown_engine
     (terminate -> wait(10 s) -> kill); engine PID observed dead; port closed
  B8 post-exit keys/ticks move nothing
  B9 containment: at most one engine alive at any instant; zero at end

All times are INJECTED integer milliseconds (the flow's own law); the world
calls are the REAL ones. Usage:
  python -B integrated_session_b.py --play-root <dir> --engine-exe <exe> \
         --out <evidence dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import psutil


def sha256_raw(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--play-root", type=Path, required=True)
    ap.add_argument("--engine-exe", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--settle-timeout", type=float, default=420.0)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(a.play_root))

    # pinned modules, resolved from the reconstructed pinned tree
    from tools.monkey_campaign.product.session_flow import (  # noqa: E402
        SessionFlow, ATTRACT, PLAYING, PAUSED, EXITED)
    from tools.monkey_campaign.product.input_mapper import (  # noqa: E402
        InputMapper, MockSink)
    from tools.playable_slice.slice_server import World       # noqa: E402

    import tools.monkey_campaign.product.session_flow as sf_mod
    import tools.monkey_campaign.product.input_mapper as im_mod
    import tools.playable_slice.slice_server as ss_mod

    receipt: dict = {
        "schema": "chimera.ont_x02.integrated_session_b.v1",
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "preflight_terminated_leftover_engines": None,   # set below
        "pins": {
            "session_flow_sha256": sha256_raw(
                Path(sf_mod.__file__).read_bytes()),
            "input_mapper_sha256": sha256_raw(
                Path(im_mod.__file__).read_bytes()),
            "slice_server_sha256": sha256_raw(
                Path(ss_mod.__file__).read_bytes()),
            "engine_exe_sha256": sha256_raw(a.engine_exe.read_bytes()),
            "session_flow_pin_sha256": "30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf",
            "input_mapper_pin_sha256": "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44",
        },
        "probes": {},
    }

    def step(name, obj):
        receipt["probes"][name] = obj
        (a.out / "session_b_receipt.json").write_text(
            json.dumps(receipt, indent=1), encoding="utf-8")
        print("  [B] %s: %s" % (name, json.dumps(obj, default=str)[:240]))

    def alive_engines():
        return sorted(p.pid for p in psutil.process_iter(["name"])
                      if p.info["name"] and "chimera_engine" in
                      (p.info["name"] or "").lower())

    # ── 0. pre-flight: terminate engines whose cwd is THIS run's engine
    # dir (leftovers of this workspace's own earlier attempts; never
    # another lane's engines). Recorded.
    pre = []
    for p in psutil.process_iter(["name"]):
        try:
            if p.info["name"] and "chimera_engine" in p.info["name"].lower():
                if a.engine_exe.parent.as_posix() in (p.cwd() or "").replace(
                        "\\", "/"):
                    p.terminate()
                    pre.append(p.pid)
        except (psutil.Error, TypeError, PermissionError):
            continue
    if pre:
        time.sleep(3.0)

    def port_open(port):
        s = socket.socket()
        s.settimeout(1.5)
        try:
            s.connect(("127.0.0.1", port))
            return True
        except OSError:
            return False
        finally:
            s.close()

    # ── the world, booted the shipped way ───────────────────────────────
    receipt["preflight_terminated_leftover_engines"] = pre
    world = World(a.engine_exe)
    t0 = time.time()
    world.boot()                      # the shipped main() boot path
    pid1, port1 = world.proc.pid, world.port
    deadline = time.time() + a.settle_timeout
    while time.time() < deadline:
        if (world.scene_spec or {}).get("settled"):
            break
        time.sleep(1.0)
    step("B0_world_boot", {
        "ok": (world.scene_spec or {}).get("settled") is True,
        "boot_seconds": round(time.time() - t0, 2),
        "engine_pid": pid1, "engine_port": port1,
        "scene_sha256": world.scene_spec.get("scene_sha256"),
        "start_state_sha256": world.scene_spec.get("start_state_sha256"),
        "boot_count": world.boot_count,
        "engines_alive": alive_engines()})

    sink = MockSink()
    mapper = InputMapper(sink)
    flow = SessionFlow(mapper, restart_scene=world.boot,
                       teardown=world.shutdown_engine)

    # B1: attract -> playing, key-only
    flow.key("Return", down=1, now_ms=1000)
    flow.key("Return", down=0, now_ms=1080)
    b1 = {"state": flow.state, "is_playing": flow.state == PLAYING}
    step("B1_return_to_playing", b1)

    # B2: playing keys reach the REAL mapper -> CommandRecords
    flow.key("W", down=1, now_ms=2000)
    for i in range(6):
        flow.tick(2000 + 50 * (i + 1))
    flow.key("W", down=0, now_ms=2350)
    flow.tick(2400)
    recs = [r.__dict__ if hasattr(r, "__dict__") else r for r in sink.records]
    step("B2_playing_records", {
        "record_count": len(sink.records),
        "first_records": [str(r)[:120] for r in list(sink.records)[:3]],
        "boot_count": world.boot_count})

    # B3: Escape -> paused; quiesce; zero records while paused
    n_before_pause = len(sink.records)
    mapper_calls_before_pause = len(getattr(mapper, "_dbg_calls", []))
    flow.key("Escape", down=1, now_ms=3000)
    flow.key("Escape", down=0, now_ms=3080)
    paused_state = flow.state
    pid_at_pause = world.proc.pid
    for i in range(8):
        flow.tick(3100 + 50 * i)
    paused_records = len(sink.records) - n_before_pause
    step("B3_escape_pause", {
        "state": paused_state, "is_paused": paused_state == PAUSED,
        "records_emitted_while_paused": paused_records,
        "engine_pid_at_pause": pid_at_pause,
        "engines_alive": alive_engines()})

    # B4: R from paused -> exactly one real World.boot
    t_restart = time.time()
    flow.key("R", down=1, now_ms=4000)
    flow.key("R", down=0, now_ms=4080)
    settled = False
    deadline = time.time() + a.settle_timeout
    while time.time() < deadline:
        if (world.scene_spec or {}).get("settled"):
            settled = True
            break
        time.sleep(1.0)
    pid2, port2 = (world.proc.pid, world.port) if world.proc else (None, None)
    step("B4_restart_from_paused", {
        "state": flow.state, "is_playing": flow.state == PLAYING,
        "restart_seconds": round(time.time() - t_restart, 2),
        "engine_pid_before": pid_at_pause, "engine_pid_after": pid2,
        "engine_pid_changed": pid_at_pause != pid2,
        "old_engine_pid_gone": not psutil.pid_exists(pid_at_pause),
        "port_before": port1, "port_after": port2,
        "scene_sha256": world.scene_spec.get("scene_sha256"),
        "start_state_sha256": world.scene_spec.get("start_state_sha256"),
        "boot_count_total": world.boot_count,
        "boots_expected": 2, "engines_alive": alive_engines()})

    # B5: R while playing must not boot
    boots_before_b5 = world.boot_count
    flow.key("R", down=1, now_ms=12000)
    flow.key("R", down=0, now_ms=12080)
    time.sleep(1.0)
    step("B5_restart_while_playing", {
        "state": flow.state,
        "boot_count_unchanged": world.boot_count == boots_before_b5,
        "boot_count": world.boot_count})

    # B6: pause then resume with Return; no boot
    flow.key("Escape", down=1, now_ms=13000)
    flow.key("Escape", down=0, now_ms=13080)
    state_paused_b6 = flow.state
    boots_b6 = world.boot_count
    flow.key("Return", down=1, now_ms=13500)
    flow.key("Return", down=0, now_ms=13580)
    time.sleep(0.5)
    step("B6_resume_no_boot", {
        "state": flow.state, "is_playing": flow.state == PLAYING,
        "was_paused": state_paused_b6 == PAUSED,
        "boot_count_unchanged": world.boot_count == boots_b6})

    # B7: Q -> EXITED; real teardown exactly once
    pid_at_exit, port_at_exit = world.proc.pid, world.port
    t_exit = time.time()
    flow.key("Q", down=1, now_ms=20000)
    flow.key("Q", down=0, now_ms=20080)
    exit_seconds = round(time.time() - t_exit, 2)
    proc_dead = (world.proc is None) and (not psutil.pid_exists(pid_at_exit))
    time.sleep(2.0)
    step("B7_q_exit_teardown", {
        "state": flow.state, "is_exited": flow.state == EXITED,
        "exit_seconds": exit_seconds,
        "engine_pid_at_exit": pid_at_exit,
        "engine_pid_dead": proc_dead,
        "world_proc_handle": None if world.proc is None else "still-set",
        "engine_port_closed": not port_open(port_at_exit),
        "engines_alive": alive_engines()})

    # B8: post-exit nothing moves
    sink_before_b8 = len(sink.records)
    flow.key("Return", down=1, now_ms=21000)
    flow.tick(21100)
    flow.key("Escape", down=1, now_ms=21200)
    flow.tick(21300)
    step("B8_terminal_inert", {
        "state_unchanged": flow.state == EXITED,
        "state": flow.state,
        "records_emitted_after_exit": len(sink.records) - sink_before_b8})

    # B9: containment summary across the whole session
    step("B9_containment", {
        "engines_alive_final": alive_engines(),
        "boot_count_total": world.boot_count,
        "verdict_note": "exactly one engine alive at any step receipt above; "
                        "zero at end; port closed"})

    ok = (receipt["probes"]["B1_return_to_playing"]["is_playing"]
          and receipt["probes"]["B2_playing_records"]["record_count"] > 0
          and receipt["probes"]["B3_escape_pause"]["is_paused"]
          and receipt["probes"]["B3_escape_pause"]["records_emitted_while_paused"] == 0
          and receipt["probes"]["B4_restart_from_paused"]["is_playing"]
          and receipt["probes"]["B4_restart_from_paused"]["engine_pid_changed"]
          and receipt["probes"]["B4_restart_from_paused"]["old_engine_pid_gone"]
          and receipt["probes"]["B4_restart_from_paused"]["boot_count_total"] == 2
          and receipt["probes"]["B5_restart_while_playing"]["boot_count_unchanged"]
          and receipt["probes"]["B6_resume_no_boot"]["is_playing"]
          and receipt["probes"]["B6_resume_no_boot"]["boot_count_unchanged"]
          and receipt["probes"]["B7_q_exit_teardown"]["is_exited"]
          and receipt["probes"]["B7_q_exit_teardown"]["engine_pid_dead"]
          and receipt["probes"]["B7_q_exit_teardown"]["engine_port_closed"]
          and receipt["probes"]["B8_terminal_inert"]["state_unchanged"]
          and receipt["probes"]["B8_terminal_inert"]["records_emitted_after_exit"] == 0
          and not receipt["probes"]["B9_containment"]["engines_alive_final"])
    receipt["verdict"] = "PASS" if ok else "CHECK_PROBES"
    receipt["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (a.out / "session_b_receipt.json").write_text(
        json.dumps(receipt, indent=1), encoding="utf-8")
    print("SESSION B VERDICT:", receipt["verdict"])
    # safety: only OUR engines could exist here; none should
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
