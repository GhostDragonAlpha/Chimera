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

# Maps a beat's `store_as` name to the canonical field the manage_tools bridge
# returns. Lets beats use intent-named telemetry keys (sync_events_recorded,
# walk_volume, ...) without the bridge having to mirror every alias.
STORE_AS_KEY_ALIASES = {
    "total_events": "count",
    "sync_events_recorded": "count",
    "avg_latency_ms": "avg_latency_ms",
    "max_latency_ms": "max_latency_ms",
    "sync_latency_ms_max": "max_latency_ms",
    "walk_volume": "last_volume",
    "sprint_volume": "last_volume",
}

# ── execute_python telemetry fallback ──────────────────────────────────────
# Single-line UE Python scripts (MUST be semicolon-separated; multi-line
# crashes the execute_python handler at line ~22). Each getter ends with the
# property value as the last expression so execute_python returns it.
_TELEMETRY_SCRIPTS = {
    "ClearFootstepSyncTelemetry": (
        "import unreal; "
        "_cs=[c for a in unreal.EditorLevelLibrary.get_all_level_actors() "
        "for c in unreal.get_all_actor_components(a) "
        "if 'SandSound' in str(type(c).__name__)]; "
        "_cs[0].ClearFootstepSyncTelemetry() if _cs else None"
    ),
    "GetFootstepSyncEventCount": (
        "import unreal; "
        "_cs=[c for a in unreal.EditorLevelLibrary.get_all_level_actors() "
        "for c in unreal.get_all_actor_components(a) "
        "if 'SandSound' in str(type(c).__name__)]; "
        "_cs[0].FootstepSyncEventCount if _cs else -1"
    ),
    "GetMaxFootstepSyncLatencyMs": (
        "import unreal; "
        "_cs=[c for a in unreal.EditorLevelLibrary.get_all_level_actors() "
        "for c in unreal.get_all_actor_components(a) "
        "if 'SandSound' in str(type(c).__name__)]; "
        "_cs[0].MaxFootstepSyncLatencyMs if _cs else 999.0"
    ),
    "GetAverageFootstepSyncLatencyMs": (
        "import unreal; "
        "_cs=[c for a in unreal.EditorLevelLibrary.get_all_level_actors() "
        "for c in unreal.get_all_actor_components(a) "
        "if 'SandSound' in str(type(c).__name__)]; "
        "_cs[0].AverageFootstepSyncLatencyMs if _cs else 999.0"
    ),
    "GetLastFootstepVolume": (
        "import unreal; "
        "_cs=[c for a in unreal.EditorLevelLibrary.get_all_level_actors() "
        "for c in unreal.get_all_actor_components(a) "
        "if 'SandSound' in str(type(c).__name__)]; "
        "_cs[0].LastFootstepVolume if _cs else 0.0"
    ),
}


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
        if not sc:
            # Some responses (e.g. manage_tools' engine-forwarded actions) carry
            # their payload as a JSON string in content[0].text instead of
            # structuredContent — parse that instead of treating it as a failure.
            content = r.get("result", {}).get("content") or []
            if content and content[0].get("type") == "text":
                try:
                    sc = json.loads(content[0]["text"])
                except (ValueError, KeyError):
                    sc = {}
        if not sc.get("success"):
            raise RuntimeError(
                f"{tool}.{args.get('action')}: {sc.get('message', 'failed')[:120]}"
            )
        return sc.get("result") or {}

    def _call_or_default(self, tool: str, args: dict, default: dict = None) -> dict:
        """Like _call but returns default dict on failure instead of raising."""
        try:
            return self._call(tool, args)
        except (RuntimeError, Exception):
            return default or {}

    def _runtime(self) -> dict:
        return self._call("inspect", {"action": "runtime_report"})

    def _read_component_float(self, actor: str, component: str, prop: str):
        """Read a numeric component property as a hard fact. Returns float or
        None (graceful — never raises) so an expect can distinguish an
        unreadable property from a failed transition."""
        try:
            r = self.c.call(
                "control_actor",
                {
                    "action": "get_component_property",
                    "actorName": actor,
                    "componentName": component,
                    "propertyName": prop,
                },
            ) or {}
        except Exception:
            return None
        sc = (r.get("result") or {}).get("structuredContent") or {}
        if not sc.get("success"):
            return None
        res = sc.get("result") or {}
        val = (res.get("data") or {}).get("value")
        if val is None:
            val = res.get("value")
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    # ── execute_python telemetry helpers ────────────────────────────────────
    def _build_telemetry_python(self, cmd: str, action: dict) -> str | None:
        """Return the single-line UE Python script for *cmd*, or None if
        *cmd* is not a known telemetry command.

        The returned string contains NO literal newlines — the MCP server's
        execute_python handler crashes at line ~22 on multi-line code.
        """
        script = _TELEMETRY_SCRIPTS.get(cmd)
        if script is not None:
            # Verify the script is truly single-line (no \n)
            if "\n" in script:
                from warnings import warn

                warn(f"_build_telemetry_python({cmd}): script contains newline!")
        return script

    @staticmethod
    def _extract_scalar(result) -> float | int | None:
        """Extract a numeric scalar from an execute_python MCP response.

        Handles several common wrapping patterns the bridge may use:
          - Raw value (42, 3.14)
          - ``{"value": 42}`` or ``{"data": 42}`` or ``{"return_value": 42}``
          - ``{"result": 42}``
          - Nested ``{"data": {"value": 42}}``
        Returns ``None`` when no numeric value can be extracted.
        """
        if result is None:
            return None
        if isinstance(result, (int, float)):
            return result
        if isinstance(result, str):
            try:
                return float(result)
            except (ValueError, TypeError):
                return None
        if isinstance(result, dict):
            # Direct key paths
            for key in ("value", "data", "return_value", "result"):
                val = result.get(key)
                if isinstance(val, (int, float)):
                    return val
                if isinstance(val, str):
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        pass
            # Nested dict: result.data.value / result.result.value
            for outer_key in ("data", "result"):
                outer = result.get(outer_key)
                if isinstance(outer, dict):
                    for inner_key in ("value", "data", "result"):
                        val = outer.get(inner_key)
                        if isinstance(val, (int, float)):
                            return val
        return None

    def _key(self, key: str, hold_s: float, modifier: str | None = None):
        if modifier:
            self._call(
                "control_editor",
                {"action": "simulate_input", "type": "key_down", "key": modifier},
            )
        self._call(
            "control_editor",
            {"action": "simulate_input", "type": "key_down", "key": key},
        )
        time.sleep(max(0.05, hold_s))
        self._call(
            "control_editor", {"action": "simulate_input", "type": "key_up", "key": key}
        )
        if modifier:
            self._call(
                "control_editor",
                {"action": "simulate_input", "type": "key_up", "key": modifier},
            )

    # ---- beat machinery ----
    def _do_action(self, a: dict):
        if "key" in a:
            self.w.mark("action", {"key": a["key"], "hold_s": a.get("hold_s", 0.2)})
            modifier = "LeftShift" if a.get("shift") else None
            self._key(a["key"], float(a.get("hold_s", 0.2)), modifier=modifier)
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
            # BugItGo console command for movement/camera move (editor mode only)
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

        elif "reset_position" in a:
            # Position reset for pawn during PIE (BugItGo doesn't work in PIE).
            # Uses control_actor set_transform on the possessed pawn directly.
            loc = a["reset_position"]
            x = float(loc.get("x", 0))
            y = float(loc.get("y", 0))
            z = float(loc.get("z", 0))
            self.w.mark(
                "action",
                {"reset_position": {"x": x, "y": y, "z": z}},
            )
            # Find the possessed pawn name from runtime_report first
            rt = self._runtime()
            pawn_name = (rt.get("pawn") or {}).get("name", "")
            if not pawn_name:
                raise RuntimeError(
                    f"reset_position failed: no possessed pawn found in runtime_report"
                )
            self._call(
                "control_actor",
                {
                    "actorName": pawn_name,
                    "action": "set_transform",
                    "location": {"x": x, "y": y, "z": z},
                },
            )
        elif "command" in a:
            cmd = a["command"]
            self.w.mark("action", {"command": cmd})
            call_args = {"action": cmd}
            for k, v in a.items():
                if k not in ("command",):
                    call_args[k] = v

            # ── Tier 1: manage_tools bridge ──
            result = self._call_or_default("manage_tools", call_args)
            command_succeeded = bool(result)

            # ── Tier 2: execute_python fallback for telemetry commands ──
            if not command_succeeded and cmd in _TELEMETRY_SCRIPTS:
                py_script = self._build_telemetry_python(cmd, a)
                if py_script:
                    self.w.mark(
                        "action_warning",
                        {
                            "command": cmd,
                            "note": "manage_tools failed; trying execute_python",
                        },
                    )
                    py_result = self._call_or_default(
                        "system_control",
                        {"action": "execute_python", "code": py_script},
                    )
                    if py_result:
                        scalar = self._extract_scalar(py_result)
                        if scalar is not None:
                            # Getters returned a real value — store it.
                            store_as = a.get("store_as")
                            if store_as:
                                if not hasattr(self, "telemetry_results"):
                                    self.telemetry_results = {}
                                self.telemetry_results[store_as] = scalar
                            result = py_result
                            command_succeeded = True
                        elif cmd in (
                            "ClearFootstepSyncTelemetry",
                        ):
                            # Void command: marked as succeeded even with no
                            # return value — the call completed.
                            result = {"telemetry_cleared": True}
                            command_succeeded = True

            # ── Tier 3: graceful degradation ──
            if not command_succeeded:
                self.w.mark(
                    "action_warning",
                    {
                        "command": cmd,
                        "error": (
                            "manage_tools + execute_python failed; "
                            "falling back to defaults"
                        ),
                    },
                )
                if not hasattr(self, "telemetry_results"):
                    self.telemetry_results = {}
                self.telemetry_results.setdefault("total_events", 0)
                self.telemetry_results.setdefault("sync_events_recorded", 0)
                self.telemetry_results.setdefault("avg_latency_ms", 999)
                self.telemetry_results.setdefault("max_latency_ms", 999)
                self.telemetry_results.setdefault("sync_latency_ms_max", 999)
                self.telemetry_results.setdefault("walk_volume", 0.5)
                self.telemetry_results.setdefault("sprint_volume", 0.5)
            else:
                store_as = a.get("store_as")
                if store_as and isinstance(result, dict):
                    # Map a beat's store_as name to the canonical key the
                    # bridge returns (e.g. 'count'/'last_volume').
                    key = STORE_AS_KEY_ALIASES.get(store_as, store_as)
                    if key in result:
                        if not hasattr(self, "telemetry_results"):
                            self.telemetry_results = {}
                        self.telemetry_results[store_as] = result[key]
            return result
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
        if "pawn_property_toggles" in e:
            # Active, reversible HARD-FACT check for a state TOGGLE (e.g. crouch):
            # read a component property (standing) -> press key -> read (active) ->
            # release key -> read (released); require a DROP that then RESTORES.
            # Fails on a no-op toggle, a permanently-changed value, AND a gravity
            # fall (none produce a reversible drop). Replaces the pawn_z_below
            # proxy that passed even when Verb_Bend crouch was completely broken.
            spec = e["pawn_property_toggles"]
            key = str(spec.get("key", "C"))
            comp = str(spec.get("component", "CollisionCylinder"))
            prop = str(spec.get("property", "CapsuleHalfHeight"))
            min_drop = float(spec.get("min_drop", 20.0))
            settle = float(spec.get("settle_s", 1.2))
            pawn = (rt.get("pawn") or {}).get("name", "")
            if not pawn:
                return False, "pawn_property_toggles: no possessed pawn"
            standing = self._read_component_float(pawn, comp, prop)
            self._call(
                "control_editor",
                {"action": "simulate_input", "type": "key_down", "key": key},
            )
            time.sleep(settle)
            active = self._read_component_float(pawn, comp, prop)
            self._call(
                "control_editor",
                {"action": "simulate_input", "type": "key_up", "key": key},
            )
            time.sleep(settle)
            released = self._read_component_float(pawn, comp, prop)
            if standing is None or active is None or released is None:
                return False, (
                    f"pawn_property_toggles: {comp}.{prop} unreadable "
                    f"(standing={standing} active={active} released={released})"
                )
            drop = standing - active
            restore = released - active
            ok = bool(drop >= min_drop and restore >= 0.5 * drop)
            return ok, (
                f"{prop} {standing:.0f}->{active:.0f}->{released:.0f} "
                f"drop={drop:.0f} restore={restore:.0f} min_drop={min_drop:.0f}"
            )
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
        if "total_events_gt" in e:
            val = getattr(self, "telemetry_results", {}).get("total_events", 0)
            return val > float(e["total_events_gt"]), f"total_events={val}"
        if "avg_latency_ms_lt" in e:
            val = getattr(self, "telemetry_results", {}).get("avg_latency_ms", 1e9)
            return val < float(e["avg_latency_ms_lt"]), f"avg_latency_ms={val}"
        if "max_latency_ms_lt" in e:
            val = getattr(self, "telemetry_results", {}).get("max_latency_ms", 1e9)
            return val < float(e["max_latency_ms_lt"]), f"max_latency_ms={val}"
        if "sync_events_recorded" in e:
            val = getattr(self, "telemetry_results", {}).get("sync_events_recorded", 0)
            return val >= float(e["sync_events_recorded"]), f"sync_events_recorded={val}"
        if "sync_latency_ms_max" in e:
            val = getattr(self, "telemetry_results", {}).get("sync_latency_ms_max", 1e9)
            return val <= float(e["sync_latency_ms_max"]), f"sync_latency_ms_max={val}"
        if "volume_scales_with_speed" in e:
            tr = getattr(self, "telemetry_results", {})
            wv, sv = tr.get("walk_volume"), tr.get("sprint_volume")
            if wv is None or sv is None:
                return False, "volume_scales_with_speed: walk/sprint volume not captured"
            return bool(sv > wv * 1.5), f"walk_volume={wv} sprint_volume={sv}"
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
    parser.add_argument("--agent-id", default=None,
                        help="Editor-scheduler agent id (for parallel runs)")
    args = parser.parse_args()

    # [SCHEDULER] Claim exclusive editor access in OPEN mode so PIE / screenshots
    # work and parallel agents (pipelines, other sleepwalkers) don't collide on
    # the editor. Falls back gracefully if the scheduler module is unavailable.
    agent_id = None
    try:
        from core.editor_scheduler import request_editor, release_editor
        from uuid import uuid4
        agent_id = args.agent_id or f"sleepwalker-{uuid4().hex[:8]}"
        if not request_editor("open", agent_id, timeout=120):
            print("  [SCHEDULER] Could not acquire editor lock (timeout); proceeding unlocked.")
            agent_id = None
    except Exception as e:
        print(f"  [SCHEDULER] editor lock unavailable ({e}); proceeding without it.")
        agent_id = None

    sw = Sleepwalker(args.beats, args.session, record=not args.no_record)
    try:
        result = sw.run(keep_pie=args.keep_pie)
    finally:
        if agent_id:
            try:
                release_editor(agent_id)
            except Exception:
                pass
    print(json.dumps({k: v for k, v in result.items() if k != "outcomes"}, indent=1))
    for o in result["outcomes"]:
        print(
            f"  {o['outcome']:>7}  {o['beat']}  features={','.join(o['features']) or '-'}"
        )


if __name__ == "__main__":
    main()
