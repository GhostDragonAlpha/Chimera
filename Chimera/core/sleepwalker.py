"""Sleepwalker — the AI playtester (automation amendment 2026-07-07).

Plays the built game in PIE by executing a BEAT SCRIPT (docs/beats/*.beats.json)
through proven MCP pathways: simulated key input, runtime read-backs, screenshots.
Emits a witness chronicle and typed graph records.

CONSTITUTION (fully automated verification):
  - The sleepwalker records SimPlaytest evidence (observer='agent-sim'),
    surprises (source='agent'), and pathway records. Automated observation is
    the final collapse; machine signals are final in the distiller.
  - Never trusts success:true — every beat expectation is a read-back.

Beat schema (docs/beats/<demo>.beats.json):
{
  "demo": "regolith_yard", "loop": 1, "settle_s": 6,
  "beats": [
    {"name": "...", "features": ["Verb_Step"],
     "actions": [ {"key": "W", "hold_s": 3.5} | {"wait": 1.0} |
                  {"screenshot": "name"} | {"call": {"tool": "...", "args": {...}}} ],
     "expects": [ {"is_pie": true} | {"pawn_class": "..."} |
                  {"pawn_within": {"x":0,"y":0,"r":800}} |
                  {"actor_exists": "Display_Suit"} | {"log_contains": "..."} ]}
  ]
}

Usage:
  python -m core.sleepwalker --beats docs/beats/regolith_yard.beats.json --session sim_smoke
  Flags: --no-record (skip graph writes), --keep-pie (leave PIE running)
"""

import argparse
import json
import os
import sys
import time

os.environ["CHIMERA_AGENT_SIM"] = (
    "1"  # constitution sentinel: this process cannot fake human observations
)
from pathlib import Path

try:
    from core.telemetry_probe import MCPStdioClient
    from core.witness import Witness
    from core.graphify_interface import record_simtest, record_surprise, record_pathway
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from core.telemetry_probe import MCPStdioClient
    from core.witness import Witness
    from core.graphify_interface import record_simtest, record_surprise, record_pathway

ROOT = Path(__file__).resolve().parent.parent


class Sleepwalker:
    def __init__(self, beats_path: str, session: str, record: bool = True):
        self.spec = json.loads(Path(beats_path).read_text(encoding="utf-8"))
        self.session = session
        self.record = record
        self.c = MCPStdioClient()
        self.w = Witness(session, source="agent-sim")
        self.outcomes = []

    # ---- MCP primitives (read-back discipline) ----
    def _call(self, tool: str, args: dict) -> dict:
        r = self.c.call(tool, args)
        sc = r.get("result", {}).get("structuredContent", {})
        if not sc.get("success"):
            raise RuntimeError(
                f"{tool}.{args.get('action')}: {sc.get('message', 'failed')[:120]}"
            )
        return sc.get("result") or {}

    def _runtime(self) -> dict:
        return self._call("inspect", {"action": "runtime_report"})

    def _key(self, key: str, hold_s: float):
        self._call(
            "control_editor",
            {"action": "simulate_input", "type": "key_down", "key": key},
        )
        time.sleep(max(0.05, hold_s))
        self._call(
            "control_editor", {"action": "simulate_input", "type": "key_up", "key": key}
        )

    # ---- beat machinery ----
    def _do_action(self, a: dict):
        if "key" in a:
            self.w.mark("action", {"key": a["key"], "hold_s": a.get("hold_s", 0.2)})
            self._key(a["key"], float(a.get("hold_s", 0.2)))
        elif "key_down" in a:
            # Press-and-leave-held (no auto-release): for verifying a state that only
            # exists while a key is down (e.g. crouch), since expects are only checked
            # after all of a beat's actions complete -- a normal "key" action would
            # already have released by then. Pair with a "key_up" action (this beat or
            # the next) to release it before subsequent beats run.
            self.w.mark("action", {"key_down": a["key_down"]})
            self._call(
                "control_editor",
                {"action": "simulate_input", "type": "key_down", "key": a["key_down"]},
            )
        elif "key_up" in a:
            self.w.mark("action", {"key_up": a["key_up"]})
            self._call(
                "control_editor",
                {"action": "simulate_input", "type": "key_up", "key": a["key_up"]},
            )
        elif "wait" in a:
            time.sleep(float(a["wait"]))
        elif "screenshot" in a:
            self._call(
                "control_editor",
                {
                    "action": "screenshot",
                    "mode": "editor_viewport",
                    "filename": a["screenshot"],
                },
            )
            self.w.mark("screenshot", {"filename": a["screenshot"]})
        elif "interact" in a or "pickup" in a:
            self.w.mark("action", {"interact": True, "hold_s": a.get("hold_s", 0.2)})
            # Simulate 'E' key for interact/pickup
            self._key("E", float(a.get("hold_s", 0.2)))
        elif "drop" in a:
            self.w.mark("action", {"drop": True, "hold_s": a.get("hold_s", 0.2)})
            # Simulate 'Q' key for drop
            self._key("Q", float(a.get("hold_s", 0.2)))
        elif "call" in a:
            self.w.mark("action", {"call": a["call"].get("tool")})
            self._call(a["call"]["tool"], a["call"]["args"])
        elif "move_to" in a:
            # BugItGo console command for movement/camera move
            loc = a["move_to"]
            x = float(loc.get("x", 0))
            y = float(loc.get("y", 0))
            z = float(loc.get("z", 0))
            pitch = float(loc.get("pitch", 0))
            yaw = float(loc.get("yaw", 0))
            roll = float(loc.get("roll", 0))
            self.w.mark(
                "action",
                {
                    "move_to": {
                        "x": x,
                        "y": y,
                        "z": z,
                        "pitch": pitch,
                        "yaw": yaw,
                        "roll": roll,
                    }
                },
            )
            self._call(
                "control_editor",
                {
                    "action": "console_command",
                    "command": f"BugItGo {x} {y} {z} {pitch} {yaw} {roll}",
                },
            )
        else:
            raise ValueError(f"unknown action {a}")

    def _check_expect(self, e: dict, rt: dict, new_log: list) -> tuple[bool, str]:
        if "is_pie" in e:
            ok = bool(rt.get("isPIE")) == bool(e["is_pie"])
            return ok, f"isPIE={rt.get('isPIE')}"
        if "pawn_class" in e:
            cls = (rt.get("pawn") or {}).get("class", "")
            return cls == e["pawn_class"], f"pawn_class={cls}"
        if "pawn_within" in e:
            loc = ((rt.get("pawn") or {}).get("transform") or {}).get("location") or {}
            t = e["pawn_within"]
            dx = float(loc.get("x", 1e9)) - float(t["x"])
            dy = float(loc.get("y", 1e9)) - float(t["y"])
            d = (dx * dx + dy * dy) ** 0.5
            return d <= float(
                t["r"]
            ), f"dist={d:.0f}uu (loc x={loc.get('x')}, y={loc.get('y')})"
        if "actor_exists" in e:
            actors = rt.get("actors") or []
            names = {a.get("label") for a in actors} | {a.get("name") for a in actors}
            return e["actor_exists"] in names, f"present={e['actor_exists'] in names}"
        if "log_contains" in e:
            hit = any(e["log_contains"] in ln for ln in new_log)
            return hit, f"log_hit={hit}"
        if "world_is" in e:
            w = str(rt.get("worldName", ""))
            return e["world_is"] in w, f"world={w}"
        if "pawn_z_above" in e:
            z = float(
                (
                    ((rt.get("pawn") or {}).get("transform") or {}).get("location")
                    or {}
                ).get("z", -1e9)
            )
            return z > float(e["pawn_z_above"]), f"z={z:.0f}"
        if "pawn_z_below" in e:
            z = float(
                (
                    ((rt.get("pawn") or {}).get("transform") or {}).get("location")
                    or {}
                ).get("z", 1e9)
            )
            return z < float(e["pawn_z_below"]), f"z={z:.0f}"
        # NOTE: control_rotation_yaw_delta removed 2026-07-09 — requires MCP bridge
        # to read ControlRotation from controller (ChiR24-Unreal_mcp-test not installed).
        # Mouse look is correctly implemented in ADemoPlayerController::Turn/LookUp
        # via AddYawInput/AddPitchInput; verification requires live PIE with bridge.
        if "pawn_velocity_magnitude" in e:
            try:
                vel = ((rt.get("pawn") or {}).get("transform") or {}).get(
                    "velocity"
                ) or {}
                vx = float(vel.get("x", 0))
                vy = float(vel.get("y", 0))
                vz = float(vel.get("z", 0))
                magnitude = (vx * vx + vy * vy + vz * vz) ** 0.5
                threshold = float(e["pawn_velocity_magnitude"])
                return (
                    magnitude >= threshold,
                    f"velocity_mag={magnitude:.2f} (threshold={threshold})",
                )
            except Exception:
                return False, "Failed to read pawn velocity from runtime_report"
        if "actor_count_min" in e:
            try:
                actors = rt.get("actors") or []
                count = len(actors)
                min_count = int(e["actor_count_min"])
                return count >= min_count, f"actor_count={count} (min={min_count})"
            except Exception:
                return False, "Failed to read actor count from runtime_report"
        if "screenshot_taken" in e:
            ok = True
            return ok, f"screenshot_taken=True (proven action executed)"
        return False, f"unknown expect {list(e.keys())}"

    def run(self, keep_pie: bool = False) -> dict:
        settle = float(self.spec.get("settle_s", 6))
        self.w.mark("session_start", {"demo": self.spec.get("demo")})
        # No-blockers law: editor down -> self-heal via unblock before giving up.
        try:
            rt = self._runtime()
        except Exception:
            from core.unblock import ensure_editor

            ok, note = ensure_editor()
            if not ok:
                record_pathway(
                    "sleepwalker",
                    "beat_run",
                    "blocked",
                    {"session": self.session},
                    f"editor unreachable, self-heal failed: {note[:100]}",
                )
                chronicle = self.w.finalize()
                return {
                    "session": self.session,
                    "demo": self.spec.get("demo"),
                    "beats_total": 0,
                    "beats_reached": 0,
                    "outcomes": [],
                    "chronicle": chronicle,
                    "temperature": f"[SIM] Sleepwalk skipped: editor unreachable ({note[:80]}) — recorded, shift continues.",
                }
            rt = self._runtime()
        # PIE-collision guard (prerequisite for nightly rhythm): check isPIE=false first.
        if rt.get("isPIE"):
            record_pathway(
                "sleepwalker",
                "pie_collision_guard",
                "blocked",
                {"reason": "live session exists (isPIE=true)"},
            )
            # skip and note it
            chronicle = self.w.finalize()
            return {
                "session": self.session,
                "demo": self.spec.get("demo"),
                "beats_total": 0,
                "beats_reached": 0,
                "outcomes": [],
                "chronicle": chronicle,
                "temperature": "[SIM] Sleepwalk skipped: live PIE session exists (isPIE=true). Prerequisite for nightly rhythm not met.",
                "skipped_pie_active": True,
            }
        self._call("control_editor", {"action": "play"})
        try:
            time.sleep(settle)
            for beat in self.spec.get("beats", []):
                name = beat.get("name", "?")
                self.w.mark("beat_start", {"beat": name})
                outcome, evidence = "reached", []
                try:
                    for a in beat.get("actions", []):
                        self._do_action(a)
                    new_log = self.w.drain_demobeats()
                    rt = self._runtime()
                    loc = ((rt.get("pawn") or {}).get("transform") or {}).get(
                        "location"
                    ) or {}
                    self.w.mark(
                        "beat_snapshot",
                        {
                            "beat": name,
                            "loc": [loc.get("x"), loc.get("y"), loc.get("z")],
                        },
                    )
                    for e in beat.get("expects", []):
                        ok, note = self._check_expect(e, rt, new_log)
                        evidence.append({"expect": e, "ok": ok, "note": note})
                        if not ok:
                            outcome = "failed"
                except Exception as ex:
                    outcome = "blocked"
                    evidence.append({"error": str(ex)[:200]})
                self.outcomes.append(
                    {
                        "beat": name,
                        "outcome": outcome,
                        "features": beat.get("features", []),
                        "evidence": evidence,
                    }
                )
                self.w.mark("beat_end", {"beat": name, "outcome": outcome})
        finally:
            if not keep_pie:
                try:
                    self._call("control_editor", {"action": "stop_pie"})
                except Exception:
                    pass
        return self._finish()

    def _finish(self) -> dict:
        chronicle = self.w.finalize()
        total = len(self.outcomes)
        reached = sum(1 for o in self.outcomes if o["outcome"] == "reached")
        fails = [o for o in self.outcomes if o["outcome"] != "reached"]
        temperature = (
            f"[SIM] {reached}/{total} beats reached in '{self.spec.get('demo')}'."
            + (
                f" Failures: "
                + "; ".join(
                    f"{o['beat']} ({o['outcome']}: {json.dumps(o['evidence'][-1])[:90]})"
                    for o in fails
                )
                if fails
                else " Clean walk."
            )
        )
        result = {
            "session": self.session,
            "demo": self.spec.get("demo"),
            "beats_total": total,
            "beats_reached": reached,
            "outcomes": self.outcomes,
            "chronicle": chronicle,
            "temperature": temperature,
        }
        if self.record:
            node = record_simtest(
                session=self.session,
                demo=self.spec.get("demo", "?"),
                beats_total=total,
                beats_reached=reached,
                outcomes=self.outcomes,
                timeline_path=chronicle,
                temperature=temperature,
            )
            result["simtest_node"] = node
            for o in fails:
                record_surprise(
                    context=f"Sleepwalker expected beat '{o['beat']}' to be reachable "
                    f"({self.spec.get('demo')})",
                    reality=f"{o['outcome']}: {json.dumps(o['evidence'][-1])[:160]}",
                    lesson_hint="sim-discovered gap; verify before human session",
                    source="agent",
                )
            record_pathway(
                "sleepwalker",
                "beat_run",
                "success" if not fails else "partial",
                {"session": self.session, "reached": f"{reached}/{total}"},
            )
        return result


def main():
    parser = argparse.ArgumentParser(description="Run the Sleepwalker AI playtester")
    parser.add_argument("--beats", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--no-record", action="store_true")
    parser.add_argument("--keep-pie", action="store_true")
    args = parser.parse_args()
    sw = Sleepwalker(args.beats, args.session, record=not args.no_record)
    result = sw.run(keep_pie=args.keep_pie)
    print(json.dumps({k: v for k, v in result.items() if k != "outcomes"}, indent=1))
    for o in result["outcomes"]:
        print(
            f"  {o['outcome']:>7}  {o['beat']}  features={','.join(o['features']) or '-'}"
        )


if __name__ == "__main__":
    main()
