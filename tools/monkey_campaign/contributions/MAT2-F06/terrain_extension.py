#!/usr/bin/env python3
"""MAT2-F06: the DECLARED terrain-aware extension (prereg section 3, laws E1-E7).

This module is THIS card's own declared implementation. It wraps -- never
modifies -- the pinned scene bytes and the pinned F02/F07 authority modules:

  E1 HEADING   psi(t+1) = psi(t) + dt * yaw_rate(t)   (the record's channel)
  E2 POSITION  arc-length advance of the record's com_v along the heading
               (the tick advances on psi(t); the heading updates at the
               tick boundary)
  E3 SLOPE     v(t+1) = v_scene(t+1) - dt * g * grade(t);  grade = the pinned
               BUNDLE gradient . forward (terrain only; obstacle faces are
               contact surfaces, not grade).  g = 9.80665 (pinned trunk
               declaration).  grade == 0 on the certified flat line, so the
               term is exactly 0.0 and the certified channels stay
               bit-identical (prereg P1).
  E4 SUPPORT   s(t) = H(px, pz) -- the composite declared surface height
               (pinned bundle + the declared log capsule tops of E5).
  E5 LOG TOPS  H_log = site terrain + sqrt(max(0, r^2 - d_perp^2)) from the
               pinned declaration rows (yaw_index 0 rows).  Rocks and stands
               are contact_stop solids WITHOUT top profiles (F07's declared
               behavior; declared absent, never imputed).
  E6 STOPS     trunk ring (axis distance <= R + 0.25 = 0.287 m, exactly the
               pinned F07 mask's trunk blocking law), obstacle footprints
               inflated by the declared 0.25 m body envelope, and the
               step-over envelope D_step = ground_clearance + lift_gain *
               lift_hi (derived from pinned scene constants + the frozen
               manifest bounds).  contact_stop semantics: the position
               ceases to advance; the stop tick/state are receipted.
  E7 CHANNELS  the per-tick extension record (px, pz, psi, s, grade,
               support grounds/spread, stop_state) + the scene's own record.

The script derivation law (prereg section 4): each case's turn ticks are
derived by replaying THIS deterministic recursion; the execution run replays
the derived event table; the traces must be bit-identical (refusal
`f06_script_drift`).

Run: import-only (the arms live in terrain_walking.py).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

DT = 1.0 / 300.0
G_GRAV = 9.80665          # pinned: trunk_declaration.json derivation.gravity_m_s2
TURN_RATE_RAD_S = 0.8     # 20 mouse counts per 50 ms interval (the pinned mapper law)
TURN_COUNTS = 20
TURN_FINE_COUNTS = 1      # the fine tail event: rate 0.04 rad/s (one count)
# the declared turn quantization law (prereg section 4 derivation): a turn is
# emitted as 20-count interval events plus at most one fine 1-count tail, on
# the 15-tick port boundary grid.  One count contributes
# 0.04 rad/s * 15 ticks / 300 = 0.002 rad; the planned-vs-achieved heading
# residual is therefore at most half a count step.
TURN_RESIDUAL_BOUND_RAD = 0.001

FWD = "tools/monkey_campaign/contributions"
SEAM_PREFIX = tuple((FWD + "/MAT2-U01/reconcile/pinned_seam").split("/"))


class Refusal(Exception):
    """A named refusal."""


def require(condition, code: str = "", detail="") -> None:
    if not condition:
        raise Refusal(code + (": " + str(detail) if detail else ""))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _load_sibling(root: Path, rel_parts, name):
    path = root.joinpath(*rel_parts)
    require(path.exists(), "input_pin_missing:" + "/".join(rel_parts))
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TerrainWorld:
    """The pinned authorities, loaded once from the verified extraction."""

    def __init__(self, pinned_root: Path, obstacles_override=None):
        root = Path(pinned_root)
        self.root = root
        # the pinned F02 surface (validator ON)
        tq = _load_sibling(root, (FWD, "MAT2-F02", "pins", "terrain_query.py"),
                           "f06_terrain_query")
        bundle = json.loads((root / FWD / "MAT2-F02" / "pins" /
                             "terrain_bundle.json").read_bytes().decode("utf-8"))
        self.surface = tq.TerrainSurface(bundle, validate=True)
        # the pinned F07 module (its own pin table re-verifies its deps)
        self.f07 = _load_sibling(root, (FWD, "MAT2-F07", "implementation.py"),
                                 "f06_f07_implementation")
        self.obstacles = obstacles_override if obstacles_override is not None \
            else json.loads(
                (root / FWD / "MAT2-F07" / "assets" /
                 "obstacle_declaration.json").read_bytes().decode("utf-8"))["obstacles"]
        self.trunk = json.loads(
            (root / FWD / "MAT2-F02" / "pins" /
             "trunk_declaration.json").read_bytes().decode("utf-8"))
        self.logs = [o for o in self.obstacles if o["kind"] == "log"
                     and o["yaw_index"] == 0]
        solid = self.trunk["collision_representation"]["solid"]
        self.trunk_cx = float(solid["axis_base_m"][0])
        self.trunk_cz = float(solid["axis_base_m"][2])
        self.trunk_r = float(solid["radius_m"])
        # the declared body envelope: the pinned F07 module's own constant
        self.body_envelope = float(self.f07.BLOCK_INFLATION_M)
        self.trunk_ring = self.trunk_r + self.body_envelope
        # re-derived routes + mask (P2)
        self.mask, self.attribution = self.f07.build_mask(self.obstacles,
                                                          self.surface)
        self.free = self.f07.free_cells(self.mask)
        start = (self.f07.MASK_N // 2, self.f07.MASK_N // 2)
        require(start in self.free, "f06_spawn_cell_blocked", start)
        self.reach = self.f07.bfs_reachable(start, self.free)

    # -- composite declared surface (E4/E5) ----------------------------------
    def log_top(self, x, z):
        """The declared capsule top profile: max over pinned log rows."""
        best = 0.0
        for ob in self.logs:
            cx, _, cz = ob["centre_m"]
            r = ob["log_radius_m"]
            half = ob["log_length_m"] / 2.0
            dx = x - cx
            dz = z - cz
            if dx < -half or dx > half:
                continue
            d = abs(dz)
            if d < r:
                h = math.sqrt(r * r - d * d)
                if h > best:
                    best = h
        return best

    def height(self, x, z):
        """E4: the composite declared surface height."""
        require(self.surface.classify(x, z) == "inside",
                "f06_extent_violation", (x, z, self.tick if hasattr(self, 'tick') else None))
        return self.surface.height_at(x, z) + self.log_top(x, z)

    def terrain_gradient(self, x, z):
        """E3: the pinned BUNDLE gradient only (terrain, not obstacle faces)."""
        return self.surface.gradient_at(x, z)

    def trunk_axis_distance(self, x, z):
        return math.hypot(x - self.trunk_cx, z - self.trunk_cz)

    def footprint_contact(self, x, z):
        """E6: the inflated obstacle footprint the body envelope enters."""
        for ob in self.obstacles:
            if ob["kind"] == "log":
                continue          # logs are the step-over class, not walls
            if self.f07.inside_footprint(ob, x, z):
                return ob["id"]
        return None

    # -- P2: the sealed route replay -----------------------------------------
    def route_by_name(self, name):
        """Re-derive a sealed F07 route; returns (record, path, metrics)."""
        dest = self.f07.destination_table(self.obstacles)[name]
        near = self.f07.nearest_reachable(self.reach, dest[0], dest[1])
        require(near is not None, "f07_route_missing", name)
        path = self.f07.route_path((self.f07.MASK_N // 2, self.f07.MASK_N // 2),
                                   (near[1], near[2]), self.free)
        metrics = self.f07.route_metrics(path, self.obstacles, self.surface)
        rec = {"destination_m": [self.f07.grid6(dest[0]), self.f07.grid6(dest[1])],
               "reached": True, "viewpoint_offset_m": self.f07.grid6(near[0]),
               "viewpoint_cell": [near[1], near[2]]}
        rec.update(metrics)
        return rec, path

    def attribution_audit(self):
        return self.f07.attribution_audit(self.mask, self.attribution)


class TerrainWalkScene:
    """The declared E1-E7 extension around ONE pinned WalkScene."""

    def __init__(self, world: TerrainWorld, scene, manifest: dict,
                 scene_const: dict):
        self.world = world
        self.scene = scene
        p = scene.params
        lift_hi = float(manifest["action"]["bounds_hi"][2])
        self.d_step = float(p["ground_clearance"]) + float(p["lift_gain"]) * lift_hi
        self.support_offsets = (0.257, -0.012, 0.074)   # fore chain, heel, mp
        self.px = 0.0
        self.pz = 0.0
        self.psi = 0.0
        self.s = world.height(0.0, 0.0)
        self.stop_state = "none"
        self.stop_tick = None
        self.stall_tick = None
        self.mute_grade = False      # the declared FB2 tamper path only
        self.tick = 0

    # -- declared helpers -----------------------------------------------------
    def _support_grounds(self):
        out = []
        for off in self.support_offsets:
            fx = self.px + off * math.cos(self.psi)
            fz = self.pz + off * math.sin(self.psi)
            out.append(self.world.height(fx, fz))
        return out

    def step(self, applied, saturation):
        """One declared tick: the pinned scene's step + the E1-E7 laws."""
        sc = self.scene
        w = self.world
        rec_pre = sc.observation_record()
        commanded_forward = float(applied[1]) > 0.0 or float(applied[5]) > 0.0
        sc.step(applied, saturation)
        # E3: the declared additive grade term (exact on the flat line).
        # mute_grade is the DECLARED FB2 tamper path only (never a clean arm).
        gx, gz = w.terrain_gradient(self.px, self.pz)
        grade = gx * math.cos(self.psi) + gz * math.sin(self.psi)
        if not self.mute_grade:
            sc.v = sc.v - DT * G_GRAV * grade
        # E2: arc-length advance on the tick's heading; E1 at the boundary.
        # contact_stop (E6): once stopped, the position holds every tick.
        pre_x, pre_z = self.px, self.pz
        if self.stop_tick is not None:
            self.psi = (self.psi + DT * float(rec_pre["yaw_rate"])) % (2.0 * math.pi)
        else:
            self.px += DT * sc.v * math.cos(self.psi)
            self.pz += DT * sc.v * math.sin(self.psi)
            self.psi = (self.psi + DT * float(rec_pre["yaw_rate"])) % (2.0 * math.pi)
        # E4: support height
        self.s = w.height(self.px, self.pz)
        # E6: stops (the position ceases to advance AT the declared stop
        # surface: the tick's advance is projected back to the crossing)
        stop = "none"
        d0 = w.trunk_axis_distance(pre_x, pre_z)
        d1 = w.trunk_axis_distance(self.px, self.pz)
        if d1 <= w.trunk_ring and d0 > w.trunk_ring:
            stop = "trunk"
        else:
            hit = w.footprint_contact(self.px, self.pz)
            if hit is not None and w.footprint_contact(pre_x, pre_z) is None:
                stop = "obstacle:" + hit
        grounds = self._support_grounds()
        spread = max(grounds) - min(grounds)
        if (stop == "none" and self.stop_tick is None
                and (max(grounds) - self.s) > self.d_step):
            stop = "step_over"
        if stop != "none" and self.stop_tick is None:
            self.stop_state = stop
            self.stop_tick = self.tick
            if stop == "trunk":
                # the radial projection to the declared ring (exact 0.287)
                fx, fz = self.px - pre_x, self.pz - pre_z
                L2 = fx * fx + fz * fz
                ox, oz = pre_x - w.trunk_cx, pre_z - w.trunk_cz
                if L2 > 0.0:
                    b = 2.0 * (ox * fx + oz * fz)
                    c = ox * ox + oz * oz - w.trunk_ring * w.trunk_ring
                    disc = b * b - 4.0 * L2 * c
                    if disc >= 0.0:
                        f = (-b - math.sqrt(disc)) / (2.0 * L2)
                        f = min(max(f, 0.0), 1.0)
                        self.px = pre_x + f * fx
                        self.pz = pre_z + f * fz
                        self.s = w.height(self.px, self.pz)
            else:
                self.px, self.pz = pre_x, pre_z   # contact_stop: hold position
        # the declared stall marker (E3's honest negative on A2)
        if (self.stall_tick is None and commanded_forward
                and sc.v <= 0.0 and self.stop_tick is None):
            self.stall_tick = self.tick
        row = {
            "tick": self.tick,
            "px_m": self.px, "pz_m": self.pz, "psi_rad": self.psi,
            "s_m": self.s, "grade": grade,
            "support_grounds_m": grounds, "support_spread_m": spread,
            "stop_state": self.stop_state,
            "stall": self.stall_tick is not None,
            "com_v_m_s": sc.v, "com_x_m": sc.x,
            "warm_l": sc.warm_l, "warm_r": sc.warm_r,
            "contact_count": rec_pre["contact_count"],
            "foot_contacts": rec_pre["foot_contacts"],
            "foot_forces": rec_pre["foot_forces"],
            "pad_gaps": rec_pre["pad_gaps"],
            "intervention_reason": rec_pre["intervention_reason"],
            "applied_cmd": [float(v) for v in applied],
            "saturation": [float(v) for v in saturation],
            "phase_left": rec_pre["phase_left"],
            "phase_right": rec_pre["phase_right"],
            "yaw_rate_rad_s": rec_pre["yaw_rate"],
            "trip_l": sc.trip_l, "trip_r": sc.trip_r,
            "scene_state_sha256": sc.state_sha256(),
        }
        self.tick += 1
        return row

    def state_sha256(self):
        ext = canonical({
            "px_m": repr(self.px), "pz_m": repr(self.pz),
            "psi_rad": repr(self.psi), "s_m": repr(self.s),
            "stop_state": self.stop_state, "stop_tick": self.stop_tick,
            "stall_tick": self.stall_tick,
        })
        return sha_bytes(self.scene.state_sha256().encode() + ext)

    # -- declared terminal predicates ----------------------------------------
    def terminal(self):
        if self.stall_tick is not None:
            return "stall"
        if self.stop_state == "step_over":
            return "step_over"
        if self.stop_state == "trunk":
            return "trunk"
        if self.stop_state.startswith("obstacle:"):
            return self.stop_state
        return None


def corridor_grade_envelope(world: TerrainWorld, waypoints, step_m=0.01):
    """The derived grade envelope along the declared polyline (prereg P4/P5):
    dense samples; |gradient . direction| per sample; the max returned with
    the profile.  A derivation from pinned bytes, run before the arm."""
    profile = []
    for i in range(1, len(waypoints)):
        x0, z0 = waypoints[i - 1]
        x1, z1 = waypoints[i]
        L = math.hypot(x1 - x0, z1 - z0)
        require(L > 0.0, "f06_zero_leg")
        n = max(1, int(round(L / step_m)))
        dx, dz = (x1 - x0) / L, (z1 - z0) / L
        for k in range(n):
            f = k / n
            x, z = x0 + (x1 - x0) * f, z0 + (z1 - z0) * f
            gx, gz = world.terrain_gradient(x, z)
            profile.append(abs(gx * dx + gz * dz))
    gx, gz = world.terrain_gradient(*waypoints[-1])
    profile.append(abs(gx * 0.0 + gz * 0.0))
    return max(profile), profile
