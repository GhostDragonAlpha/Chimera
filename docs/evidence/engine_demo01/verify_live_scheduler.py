"""Targeted corrected-session checks against the parent-owned native endpoint.

This exercises the panel's session class directly, not pointer input. The
Windows Security window remains untouched. Parent must verify PID/port first.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "E:/ChimeraWork/slot-03/tools")
from engine_demo import DemoSession, DemoTransport

OUT = Path(__file__).parent / "scheduler_after"


def wait_for(predicate, seconds=10):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(.02)
    raise RuntimeError("targeted scheduler check did not reach expected state")


def main():
    OUT.mkdir(exist_ok=False)
    transport = DemoTransport("http://127.0.0.1:8101")
    messages = []
    session = DemoSession(transport, OUT, callback=messages.append)
    record = {"source_head": "eb408d174742ab6daac30f580acd718ef558c336",
              "mode": "session class and actual native HTTP; no pointer input",
              "native_pid": 34620, "checks": {}}
    try:
        record["before"] = transport.status()
        if record["before"]["active"]:
            raise RuntimeError("expected new uninitialized owned runtime")
        session.run(3)
        wait_for(lambda: not session.running)
        record["refusal_messages"] = list(messages)
        record["checks"]["refused_run_halts"] = (
            len(messages) == 1 and messages[0].startswith("ERROR:")
            and not any("run complete" in m for m in messages))
        session.initialize()
        wait_for(lambda: transport.status()["active"])
        initial = transport.status()
        session.run()
        wait_for(lambda: transport.status()["iteration"] > 0)
        session.reset()
        wait_for(lambda: transport.status()["iteration"] == 0)
        time.sleep(.5)
        record["reset_settled"] = transport.status()
        record["checks"]["reset_stays_reset"] = (
            record["reset_settled"]["iteration"] == 0 and
            record["reset_settled"]["accepted_state_id"] == initial["accepted_state_id"])
        session.run()
        wait_for(lambda: not session.running)
        terminal = transport.status()
        time.sleep(.5)
        record["terminal"] = terminal
        record["terminal_settled"] = transport.status()
        record["checks"]["terminal_stops_steps"] = (
            bool(terminal["terminal_state"]) and
            record["terminal_settled"]["iteration"] == terminal["iteration"] and
            record["terminal_settled"]["accepted_state_id"] == terminal["accepted_state_id"])
    except Exception as exc:
        record["error"] = str(exc)
    finally:
        session.close()  # No process handle: leaves parent's real GUI/engine intact.
        record["messages"] = messages
        with (OUT / "result.json").open("x", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2)
    print(json.dumps(record.get("checks"), indent=2))
    return 0 if "error" not in record and all(record["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
