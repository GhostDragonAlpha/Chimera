"""
Bridge between the Python particle engine and Unreal Engine's render pipeline.

Transport modes:
  1. `mcp`  — Uses the existing MCP automation bridge (WebSocket via chiR24 CLI).
  2. `none` — Headless mode: simulation runs, states can be read programmatically.
  3. `stdout` — Dump particle data as JSON lines (for debugging/piping).
  4. `batching` — Accumulate frames and send in chunks (for performance).

Design principle: the bridge is a SINK for particle state. It receives
a ParticleState and routes it to the renderer. It does NOT modify
the simulation — the sim pushes, the bridge consumes.
"""

import json
import time
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Callable
from ParticleEngine.core import ParticleState, COL, TYPE_NAMES, C_POS, C_COLOR


@dataclass
class BridgeConfig:
    """Configuration for the UE bridge transport."""
    mode: str = "none"               # "mcp", "none", "stdout"
    batch_frames: int = 1            # Send every N frames (1 = every frame)
    max_particles_per_frame: int = 50000  # Cap particles sent per frame
    downsample: int = 1              # Send every Nth particle (1 = all)
    send_positions: bool = True
    send_colors: bool = True
    send_types: bool = True
    send_props: bool = False         # Control var values (larger payload)


class UEBridge:
    """
    Bridges particle state from Python simulation to Unreal Engine.

    Usage:
        bridge = UEBridge(BridgeConfig(mode="mcp"))
        sim = ParticleSimulator(max_particles=100_000)
        # ... spawn particles, add kernels ...
        for _ in range(frames):
            sim.step(dt, cvars)
            bridge.send(sim.snapshot())
        bridge.close()
    """

    def __init__(self, config: BridgeConfig | None = None):
        self.config = config or BridgeConfig()
        self._frame_count = 0
        self._mcp_client = None
        self._socket: Optional[object] = None
        self._callbacks: list[Callable] = []  # post-send hooks

        if self.config.mode == "mcp":
            self._init_mcp()

    def _init_mcp(self):
        """Lazily connect to the MCP bridge."""
        try:
            from core.telemetry_probe import MCPStdioClient
            self._mcp_client = MCPStdioClient()
            print("[ParticleBridge] MCP client connected.")
        except Exception as e:
            print(f"[ParticleBridge] MCP init failed: {e}. Falling back to 'none' mode.")
            self.config.mode = "none"

    def send(self, state: ParticleState):
        """
        Send a snapshot of particle state to UE for rendering.
        Called once per frame (or every N frames depending on config).
        """
        self._frame_count += 1

        if self._frame_count % self.config.batch_frames != 0:
            return

        if self.config.mode == "none":
            return

        payload = self._build_payload(state)
        if payload is None:
            return

        if self.config.mode == "mcp" and self._mcp_client:
            self._send_mcp(payload)
        elif self.config.mode == "stdout":
            self._send_stdout(payload)

        for cb in self._callbacks:
            try:
                cb(state, payload)
            except Exception:
                pass

    def _build_payload(self, state: ParticleState) -> dict | None:
        """Convert ParticleState to a JSON-serialisable payload for UE."""
        if state.active_count == 0:
            return None

        active_idx = np.where(state.active_mask)[0]
        n = min(len(active_idx), self.config.max_particles_per_frame)

        # Downsample
        step = max(1, self.config.downsample)
        indices = active_idx[::step][:n]

        payload: dict = {
            "frame": self._frame_count,
            "timestamp": state.timestamp,
            "particle_count": state.particle_count,
            "sent_count": len(indices),
        }

        if self.config.send_positions:
            pos = state.data[indices, C_POS]
            payload["positions"] = pos.tolist()

        if self.config.send_colors:
            cr = state.data[indices, COL["cr"]]
            cg = state.data[indices, COL["cg"]]
            cb = state.data[indices, COL["cb"]]
            ca = state.data[indices, COL["alpha"]]
            # Pack as RGBA
            payload["colors"] = np.stack([cr, cg, cb, ca], axis=1).tolist()

        if self.config.send_types:
            types = state.data[indices, COL["type"]].astype(int)
            payload["types"] = types.tolist()

        if self.config.send_props:
            props = state.data[indices, 12:16]
            payload["props"] = props.tolist()

        return payload

    def _send_mcp(self, payload: dict):
        """Send particle data via MCP bridge."""
        try:
            # Use a custom manage_tools action: update_particle_batch
            # The UE side needs a handler that processes this payload.
            result = self._mcp_client.call(
                "manage_tools",
                {"action": "update_particle_batch", "payload": payload},
            )
            # Don't block on success — fire and forget if possible
        except Exception as e:
            # If MCP fails (e.g., editor not ready), don't crash the sim
            if self._frame_count % 300 == 0:  # Log every 5 seconds at 60fps
                print(f"[ParticleBridge] MCP send failed (frame {self._frame_count}): {e}")

    def _send_stdout(self, payload: dict):
        """Dump payload as a single JSON line to stdout."""
        # Truncate large arrays for readability
        summary = {
            k: v if k not in ("positions", "colors", "props", "types")
            else f"[{len(v)} elements]"
            for k, v in payload.items()
        }
        print(json.dumps(summary))

    def on_send(self, callback: Callable):
        """Register a callback invoked after each send (for instrumentation)."""
        self._callbacks.append(callback)

    def close(self):
        """Clean up MCP client if open."""
        if self._mcp_client:
            try:
                self._mcp_client.close()
            except Exception:
                pass
            self._mcp_client = None
        self._callbacks.clear()


# ── Headless test harness ───────────────────────────────────────

def run_headless_test(frames: int = 300, fps: int = 60):
    """
    Run a self-contained particle simulation in headless mode.
    No Unreal Engine needed — pure Python verification.
    Spawns dust and sand particles, applies gravity + wind + accumulation.

    Returns: (final_state, stats_history)
    """
    from ParticleEngine.core import ParticleSimulator
    from ParticleEngine.kernels.standard import (
        gravity_kernel, wind_kernel, ground_collision_kernel,
        accumulation_kernel, box_boundary_kernel, color_lifetime_kernel,
    )
    from ParticleEngine.control_vars import default_physics_registry

    sim = ParticleSimulator(max_particles=20_000)
    reg = default_physics_registry()

    # Register kernels
    sim.add_kernel(gravity_kernel, "gravity")
    sim.add_kernel(wind_kernel, "wind")
    sim.add_kernel(ground_collision_kernel, "ground_collision")
    sim.add_kernel(box_boundary_kernel, "box_boundary")
    sim.add_kernel(accumulation_kernel, "accumulation")
    sim.add_kernel(color_lifetime_kernel, "color_lifetime")

    # Spawn particles
    sim.spawn(
        count=5000, type_name="dust",
        position=(0, 0, 500), spread=200.0,
        mass=0.01, life=-1,  # immortal dust
        color=(0.7, 0.65, 0.55, 0.8), size=0.5,
    )
    sim.spawn(
        count=3000, type_name="sand",
        position=(100, 50, 800), spread=150.0,
        mass=0.05, life=-1,  # immortal sand
        color=(0.85, 0.7, 0.4, 0.9), size=0.3,
    )

    # Moon gravity + light wind
    reg.set("gravity", (0, 0, -162))
    reg.set("wind_vector", (30, 10, 5))
    reg.set("wind_strength", 0.3)
    reg.set("restitution", 0.1)
    reg.set("ground_level", 0.0)

    dt = 1.0 / fps
    stats = []
    bridge = UEBridge(BridgeConfig(mode="stdout", batch_frames=60))

    for f in range(frames):
        cvars = reg.snapshot()
        sim.step(dt, cvars)

        if f % 30 == 0:
            st = sim.stats()
            stats.append(st)
            bridge.send(sim.snapshot())

    bridge.close()
    return sim, stats
