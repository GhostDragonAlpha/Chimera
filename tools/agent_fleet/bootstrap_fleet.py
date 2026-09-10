"""bootstrap_fleet.py -- ONE operator command for the persistent control service.

Refuses conflicting starts, persists credentials OUTSIDE the checkout, reports
distinct stages, and never edits or slows the live registry behind workers.

Commands (documented for the operator):
    bootstrap_fleet.py status  [--root DIR] [--port P] [--json]
    bootstrap_fleet.py start   [--root DIR] [--port P] [--no-auth-verify]
    bootstrap_fleet.py stop    --ack "<controlled-transition note>" [--json]
    bootstrap_fleet.py restart --ack "<controlled-transition note>" [--json]

Stage ladder reported by status (each stage gates the next):
    installation - control dir + persisted credentials present
    running      - service responds on the port with the fleet fingerprint
    reconciled   - registry identity hashes match the persisted credentials
    enrolled     - at least one live agent is enrolled
    ready        - a leader has been elected at the current epoch

A `start` that finds ANY live listener on the port is refused: a fleet
instance (duplicate start) or anything else (conflicting listener). Stale
pidfiles from unclean stops are reported and reclaimed only when the port is
confirmed free. Credentials are generated once and reused across restarts so
session tokens and the registry survive every bounded transition.
"""
import argparse
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = Path(r"E:\ChimeraWork")
FINGERPRINT = "authenticated_post_required"  # fleet service GET /v1/action body
READY_TIMEOUT = 20.0  # seconds to wait for the service to answer after spawn


def _curl(port, token=None, path="/v1/action", payload=None):
    """Small HTTP client; returns (status, json_or_text, raw) or None on refusal."""
    url = "http://127.0.0.1:%d%s" % (port, path)
    headers = {}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = "Bearer " + token
        data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            body = None
            try:
                body = json.loads(raw)
            except ValueError:
                pass
            return resp.status, body, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        body = None
        try:
            body = json.loads(raw)
        except ValueError:
            pass
        e.close()
        return e.code, body, raw
    except (OSError, urllib.error.URLError):
        return None, None, None


def fleet_on_port(port):
    """(True, 'fleet') if our service answers; (True,'foreign') if occupied by
    another listener; (False, None) if the port is free."""
    status, body, raw = _curl(port)
    if status is None:
        return False, None
    if status == 405 and isinstance(body, dict) and body.get("error") == FINGERPRINT:
        return True, "fleet"
    return True, "foreign"


class FleetBootstrap:
    def __init__(self, root, port, log=print, fail=None):
        self.root = Path(root).resolve()
        self.port = int(port)
        self.ctl = self.root / "control"
        self.db = self.ctl / "state.sqlite"
        self.secrets_path = self.ctl / ".service_secrets.json"
        self.pidfile = self.ctl / "service.pid.json"
        self.out_log = self.ctl / "service.out.log"
        self.err_log = self.ctl / "service.err.log"
        self.log = log
        self.fail = fail if fail is not None else self._default_fail

    def _default_fail(self, msg, code=1):
        print(msg, file=sys.stderr)
        sys.exit(code)

    # --- installation ---------------------------------------------------
    def load_secrets(self):
        if not self.secrets_path.exists():
            return None
        try:
            data = json.loads(self.secrets_path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return None
        if not isinstance(data, dict):
            return None
        sup = data.get("supervisor") or data.get("supervisor_token")
        enr = data.get("enrollment") or data.get("enrollment_token")
        if not sup or not enr or sup == enr:
            return None
        return {"supervisor": sup, "enrollment": enr}

    def ensure_installation(self):
        self.ctl.mkdir(parents=True, exist_ok=True)
        for sub in ("sessions", "snapshots", "args"):
            (self.ctl / sub).mkdir(parents=True, exist_ok=True)
        secrets_dict = self.load_secrets()
        if secrets_dict is None:
            secrets_dict = {"supervisor": secrets.token_urlsafe(32),
                            "enrollment": secrets.token_urlsafe(32)}
            self.secrets_path.write_text(json.dumps(secrets_dict, indent=2),
                                         encoding="utf-8")
            try:
                os.chmod(self.secrets_path, 0o600)
            except OSError:
                pass
            return True, secrets_dict
        return False, secrets_dict

    def verify_reconciled(self, secrets_dict):
        """Registry identity hashes must match the persisted credentials."""
        if not self.db.exists():
            return False, "registry_absent"
        try:
            import sqlite3
            con = sqlite3.connect("file:%s?mode=ro" % self.db, uri=True, timeout=5)
            row = con.execute("SELECT body FROM state WHERE id=1").fetchone()
            con.close()
        except sqlite3.Error as e:
            return False, "registry_unreadable:%s" % e
        if row is None:
            return False, "registry_empty"
        state = json.loads(row[0])
        for label, key in (("supervisor_hash", "supervisor"), ("enrollment_hash", "enrollment")):
            import hashlib
            if state.get(label) != hashlib.sha256(secrets_dict[key].encode()).hexdigest():
                return False, "identity_mismatch:" + label
        return True, state

    # --- process bookkeeping --------------------------------------------
    def _read_pidfile(self):
        if not self.pidfile.exists():
            return None
        try:
            data = json.loads(self.pidfile.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return None
        return data if data.get("port") == self.port else None

    def _write_pidfile(self, pid):
        self.pidfile.write_text(json.dumps({"pid": pid, "port": self.port,
                                            "root": str(self.root),
                                            "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                                           indent=2), encoding="utf-8")

    def _pid_alive(self, pid):
        if pid is None:
            return False
        if os.name != "nt":
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False
        # os.kill(pid, 0) is NOT a liveness probe on Windows (WinError 87).
        # Query the process directly with the least privilege that works.
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)

    def _listener_pid(self):
        """PID of the process LISTENING on self.port, resolved via netstat."""
        try:
            out = subprocess.run(["netstat", "-ano", "-p", "tcp"],
                                 capture_output=True, text=True, timeout=10).stdout
        except (OSError, subprocess.SubprocessError):
            return None
        wanted = ":%d" % self.port
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[-2] == "LISTENING":
                if any(p.endswith(wanted) for p in parts[1:3]):
                    try:
                        return int(parts[-1])
                    except ValueError:
                        return None
        return None

    # --- status -----------------------------------------------------------
    def status(self, as_json=False):
        secrets_dict = self.load_secrets()
        installed = secrets_dict is not None
        on_port, kind = fleet_on_port(self.port)
        running = kind == "fleet"
        reconciled = False
        enrolled = False
        leader = None
        epoch = None
        registry = {}
        if running and secrets_dict is not None:
            status, body, _ = _curl(self.port, secrets_dict["supervisor"],
                                    payload={"operation": "snapshot", "arguments": {}})
            if status == 200 and isinstance(body, dict) and "result" in body:
                snap = body["result"]
                reconciled = isinstance(snap, dict)
                registry = snap
                agent_dict = snap.get("agents", {})
                enrolled = bool(agent_dict) or snap.get("leader") is not None
                leader = snap.get("leader")
                epoch = snap.get("epoch")
        elif not running and installed and self.db.exists():
            ok, state = self.verify_reconciled(secrets_dict)
            if ok:
                reconciled = True
                registry = state
                enrolled = bool(state.get("agents")) or state.get("leader") is not None
                leader = state.get("leader")
                epoch = state.get("epoch")
        ready = bool(running and reconciled and enrolled and leader)
        pf = self._read_pidfile()
        report = {
            "service": {"port": self.port, "running": running,
                        "instance": "fleet" if running else kind,
                        "pid": pf.get("pid") if pf else None,
                        "pidfile_matches": bool(pf),
                        "started_at_utc": pf.get("started_at_utc") if pf else None},
            "stages": {"installation": installed, "running": running,
                       "reconciled": reconciled, "enrolled": enrolled, "ready": ready},
            "registry": registry,
        }
        if as_json:
            print(json.dumps(report, indent=2))
        else:
            self._print_status(report)
        return report

    def _print_status(self, r):
        s = r["service"]; st = r["stages"]
        self.log("fleet service      port %d" % s["port"])
        self.log("  instance         %s" % ("fleet (ours)" if s["running"] else (s["instance"] or "none")))
        if s["pid"]:
            self.log("  pid              %s (pidfile matches: %s)" % (s["pid"], s["pidfile_matches"]))
        line = []
        for name in ("installation", "running", "reconciled", "enrolled", "ready"):
            line.append("%s=%s" % (name, "OK" if st[name] else "NO"))
        self.log("  stages           " + "  ".join(line))
        reg = r["registry"]
        if reg:
            self.log("  revision         %s" % reg.get("revision"))
            self.log("  leader/epoch     %s / %s" % (reg.get("leader"), reg.get("epoch")))
            tasks = reg.get("tasks", {})
            by_state = {}
            for t in tasks.values():
                by_state[t["state"]] = by_state.get(t["state"], 0) + 1
            if by_state:
                self.log("  tasks            " + "  ".join("%s=%d" % kv for kv in sorted(by_state.items())))
            slots = reg.get("slots", {})
            occupied = sum(1 for v in slots.values() if v.get("task"))
            self.log("  slots            %d/%d occupied" % (occupied, len(slots)))
            res = reg.get("resources", {})
            if res:
                self.log("  resources        " + ", ".join(sorted(res)))
            agents = reg.get("agents", {})
            if agents:
                self.log("  agents           " + ", ".join(sorted(agents)))

    # --- start ----------------------------------------------------------
    def start(self, wait=True):
        on_port, kind = fleet_on_port(self.port)
        if kind == "fleet":
            self.fail("duplicate_start_refused: fleet service already running on port %d" % self.port, 1)
        if kind == "foreign":
            self.fail("conflicting_listener_refused: port %d is held by a non-fleet listener" % self.port, 1)
        self.log("port %d free; continuing" % self.port)

        pf = self._read_pidfile()
        if pf is not None and not self._pid_alive(pf.get("pid", -1)):
            stale = dict(pf)
            self.pidfile.unlink(missing_ok=True)
            self.log("recovered_stale_pidfile: %(pid)d (dead from %(started_at_utc)s)" % stale)

        created, secrets_dict = self.ensure_installation()
        self.log("installation: %s" % ("credentials_created" if created else "already_installed"))

        env = dict(os.environ)
        env["CHIMERA_FLEET_SUPERVISOR_TOKEN"] = secrets_dict["supervisor"]
        env["CHIMERA_FLEET_ENROLLMENT_TOKEN"] = secrets_dict["enrollment"]
        args = [sys.executable, str(HERE / "service.py"), "--root", str(self.root),
                "--db", str(self.db), "--port", str(self.port)]
        kwargs = {"cwd": str(HERE), "env": env,
                  "stdin": subprocess.DEVNULL,
                  "stdout": open(self.out_log, "ab", buffering=0),
                  "stderr": open(self.err_log, "ab", buffering=0)}
        if os.name == "nt":
            kwargs["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP
                                       | getattr(subprocess, "DETACHED_PROCESS", 0)
                                       | getattr(subprocess, "CREATE_NO_WINDOW", 0))
        proc = subprocess.Popen(args, **kwargs)
        self._write_pidfile(proc.pid)
        self.log("spawned service pid %d; log: %s" % (proc.pid, self.err_log))

        if wait:
            deadline = time.monotonic() + READY_TIMEOUT
            while time.monotonic() < deadline:
                t, k = fleet_on_port(self.port)
                if k == "fleet":
                    status, body, _ = _curl(self.port, secrets_dict["supervisor"],
                                            payload={"operation": "snapshot",
                                                     "arguments": {}})
                    reconciled = status == 200 and isinstance(body.get("result"), dict)
                    self.log("running: yes (reconciled=%s, pid=%d)" % (reconciled, proc.pid))
                    return {"running": True, "pid": proc.pid, "reconciled": reconciled,
                            "port": self.port}
                if proc.poll() is not None:
                    break
                time.sleep(0.25)
            tail = ""
            if self.err_log.exists():
                tail = self.err_log.read_text(encoding="utf-8", errors="replace")[-500:]
            self.fail("service_exited_before_ready\n" + tail, 3)
        return {"running": False, "pid": proc.pid, "port": self.port,
                "race_window": "still spawning; run status"}

    # --- stop/restart ----------------------------------------------------
    def stop(self, ack):
        if not ack or len(ack.strip()) < 10:
            self.fail("stop_requires_ack: pass --ack '<controlled-transition note>'; "
                      "transitions behind workers must be reported up front", 2)
        on_port, kind = fleet_on_port(self.port)
        if kind != "fleet":
            if kind == "foreign":
                self.fail("refusing_stop_unmanaged: port %d is not our fleet service" % self.port, 1)
            self.log("already_stopped: nothing listening on port %d" % self.port)
            self.pidfile.unlink(missing_ok=True)
            return {"already_stopped": True}
        # The listener owner is the truth; the pid file is the consent record.
        listener = self._listener_pid()
        pf = self._read_pidfile()
        if listener is None:
            self.fail("refusing_stop_unmanaged: live listener on port %d could not be "
                      "resolved to a pid; manual intervention required" % self.port, 1)
        if pf is None or pf.get("pid") != listener:
            self.fail("refusing_stop_unmanaged: listener pid %d does not match the pid "
                      "file; manual intervention required" % listener, 1)
        pid = listener
        subprocess.run(["taskkill", "/PID", str(pid)],
                       capture_output=True, check=False)
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if fleet_on_port(self.port)[1] is None:
                break
            time.sleep(0.2)
        subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                       capture_output=True, check=False)
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if fleet_on_port(self.port)[1] is None:
                break
            time.sleep(0.2)
        self.pidfile.unlink(missing_ok=True)
        if fleet_on_port(self.port)[1] == "fleet":
            self.fail("stop_incomplete: service still answering on port %d" % self.port, 1)
        self.log("stopped pid %d (transition recorded: %s)" % (pid, ack))
        return {"stopped_pid": pid, "ack": ack}

    def restart(self, ack):
        self.stop(ack)
        return self.start(wait=True)


def build_parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("status", "start", "stop", "restart"))
    p.add_argument("--root", type=str, default=str(DEFAULT_ROOT))
    p.add_argument("--port", type=int, default=8099)
    p.add_argument("--json", action="store_true")
    p.add_argument("--ack", type=str, default="")
    p.add_argument("--no-wait", action="store_true", help="spawn and return without readiness")
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    fb = FleetBootstrap(a.root, a.port)
    if a.command == "status":
        r = fb.status(as_json=a.json)
    elif a.command == "start":
        r = fb.start(wait=not a.no_wait)
        if a.json:
            print(json.dumps(r, indent=2))
    elif a.command == "stop":
        r = fb.stop(a.ack)
        if a.json:
            print(json.dumps(r, indent=2))
    elif a.command == "restart":
        r = fb.restart(a.ack)
        if a.json:
            print(json.dumps(r, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())