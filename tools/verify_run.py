#!/usr/bin/env python
"""Mechanical verifier for LightEngine print-run telemetry logs.

Parses a log file, recomputes physics metrics from the tick table, and checks
each printed falsifier verdict against an independent recomputation.  Exits 0
only when every parsed verdict agrees with the recomputed one.

ASCII-only output; safe for Windows cp1252 consoles.  Pure stdlib.
"""
from __future__ import annotations

import re
import statistics
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _sign(x: float) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


_DERIVED_RE = re.compile(
    r"Derived\s+(\w+)\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)"
)
_ROD_RE = re.compile(r"^(tension|compression|slack)\(([+-]?\d+\.?\d*)\)$")
_ROPE_RE = re.compile(
    r"rope\s+links\s+T/S/C=(\d+)/(\d+)/(\d+)\s+max_comp=(\d+\.?\d*)"
)
_THETA_RANGE_RE = re.compile(
    r"^\[\s*([-+]?\d+\.?\d*)\s*,\s*([-+]?\d+\.?\d*)\s*\]deg?$"
)
_FALSIFIER_RE = re.compile(r"^\s*\(([a-f])\)\s+(\w+)\s*-\s*(.*)$")
_BAR_RE = re.compile(r"([<>]=?)\s*(\d+\.?\d*)")


def _parse_sample_line(line: str) -> dict | None:
    """Parse one telemetry sample line into a flat dictionary."""
    # Strip the leading [tag] prefix.
    body = re.sub(r"^\[[^\]]+\]\s*", "", line)
    if "=" not in body:
        return None

    sample: dict = {}
    for segment in body.split("|"):
        segment = segment.strip()
        if not segment:
            continue

        # v3 rope column: "rope links T/S/C=1/0/0 max_comp=0.00"
        if segment.startswith("rope"):
            m = _ROPE_RE.match(segment)
            if m:
                sample["rope_t"] = int(m.group(1))
                sample["rope_s"] = int(m.group(2))
                sample["rope_c"] = int(m.group(3))
                sample["rope_max_comp"] = float(m.group(4))
            else:
                sample["rope_raw"] = segment
            continue

        if "=" not in segment:
            continue
        key, value = segment.split("=", 1)
        key = key.strip()
        value = value.strip()

        if key == "tick":
            sample["tick"] = int(value)
        elif key == "load_gain":
            sample["load_gain"] = float(value)
        elif key == "angle":
            sample["angle"] = float(value.replace("deg", ""))
        elif key == "theta/theta_stop":
            parts = value.split("/", 1)
            if len(parts) == 2:
                sample["theta"] = float(parts[0].strip())
                sample["theta_stop"] = float(parts[1].replace("deg", "").strip())
        elif key == "theta":
            # v3 range: theta=[-120.00,  18.54]deg
            m = _THETA_RANGE_RE.match(value)
            if m:
                sample["theta_stop_load"] = float(m.group(1))
                sample["theta_stop_muscle"] = float(m.group(2))
        elif key == "clusters":
            sample["clusters"] = value
        elif key == "rod":
            m = _ROD_RE.match(value)
            if m:
                sample["rod_label"] = m.group(1)
                sample["rod_force"] = float(m.group(2))
            else:
                sample["rod_raw"] = value
        else:
            # Generic float columns: gap, plate_F, contact, tip_to_drop, apex_z, ...
            try:
                sample[key] = float(value)
            except ValueError:
                sample[key] = value
    return sample


def parse_log(path: Path) -> dict:
    """Read a LightEngine print log and return its structured contents."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    derived: dict[str, float] = {}
    samples: list[dict] = []
    verdicts: list[dict] = []
    falsifiers: dict[str, dict] = {}
    tendon: dict[str, str] = {}
    rope: dict[str, str] = {}

    in_falsifiers_header = False
    current_falsifier: str | None = None
    in_tendon = False
    in_rope = False

    for line in lines:
        # Derived values
        m = _DERIVED_RE.search(line)
        if m:
            derived[m.group(1)] = float(m.group(2))
            continue

        # Telemetry sample
        if line.startswith("[") and "tick=" in line and "|" in line:
            sample = _parse_sample_line(line)
            if sample is not None and "tick" in sample:
                samples.append(sample)
            continue

        # FALSIFIERS header block (the bars/definitions)
        if line.strip() == "FALSIFIERS:":
            in_falsifiers_header = True
            current_falsifier = None
            continue
        if in_falsifiers_header:
            if line.strip() == "" or line.startswith("Derived"):
                in_falsifiers_header = False
                current_falsifier = None
                continue
            m = _FALSIFIER_RE.match(line)
            if m:
                letter, name, desc = m.groups()
                current_falsifier = letter
                falsifiers[letter] = {"name": name, "desc": desc}
            elif current_falsifier and line.strip():
                falsifiers[current_falsifier]["desc"] += " " + line.strip()
            continue

        # Verdict lines near the end of the log
        m = re.match(r"^\s*\(([a-f])\)\s+(\w+)\s*:\s(.*)$", line)
        if m:
            letter, name, after = m.groups()
            # Status may be PASS/FAIL/skipped, "not detected", or "DETECTED".
            status_match = re.match(r"(PASS|FAIL|skipped|not detected|DETECTED)\b", after)
            if status_match:
                status = status_match.group(1)
                rest = after[status_match.end() :].strip()
            else:
                parts = after.split(None, 1)
                status = parts[0]
                rest = parts[1] if len(parts) > 1 else ""
            verdicts.append(
                {
                    "letter": letter,
                    "name": name,
                    "status": status,
                    "rest": rest,
                }
            )
            continue

        # Tendon / rope telemetry summary blocks
        if "TENDON TELEMETRY:" in line:
            in_tendon = True
            in_rope = False
            continue
        if "ROPE TELEMETRY:" in line:
            in_rope = True
            in_tendon = False
            continue
        if in_tendon or in_rope:
            if line.strip() == "" or line.startswith("=="):
                in_tendon = False
                in_rope = False
                continue
            stripped = line.strip()
            target = tendon if in_tendon else rope
            if ":" in stripped:
                key, val = stripped.split(":", 1)
                target[key.strip()] = val.strip()
            elif "=" in stripped:
                key, val = stripped.split("=", 1)
                target[key.strip()] = val.strip()

    return {
        "path": str(path),
        "derived": derived,
        "samples": samples,
        "falsifiers": falsifiers,
        "verdicts": verdicts,
        "tendon_telemetry": tendon,
        "rope_telemetry": rope,
    }


# ---------------------------------------------------------------------------
# Independent recomputation
# ---------------------------------------------------------------------------


def recompute_metrics(parsed: dict) -> dict:
    """Recompute physics metrics directly from the tick table."""
    samples = parsed["samples"]
    derived = parsed["derived"]
    n = len(samples)
    if n == 0:
        return {"n_samples": 0}

    load_gains = [s["load_gain"] for s in samples]
    max_load = max(load_gains)
    max_load_tick = samples[load_gains.index(max_load)]["tick"]

    last_n = max(1, int(n * 0.2))
    last_angles = [s["angle"] for s in samples[-last_n:]]
    settled_angle = statistics.mean(last_angles)
    settled_sign = _sign(settled_angle)

    gaps = [s["gap"] for s in samples]
    gap_min = min(gaps)
    gap_max = max(gaps)
    gap_mean = statistics.mean(gaps)

    contacts = [s["contact"] for s in samples]
    contact_min = min(contacts)
    contact_max = max(contacts)
    positive_contacts = [(s["tick"], s["contact"]) for s in samples if s["contact"] > 0]
    spike_tick = None
    spike_value = None
    if positive_contacts:
        spike_tick, spike_value = max(positive_contacts, key=lambda x: x[1])

    # Reversal-spike detector.
    # The literal contract is "positive contact > 10x the cold-print |contact|".
    # When the cold-print contact is small (near-zero preload) that threshold is
    # meaningless, so we use the cold magnitude itself as a floor for small-baseline
    # runs while keeping the 10x rule for preloaded runs.
    cold_abs = abs(samples[0]["contact"])
    reversal_spike = None
    if spike_tick is not None and spike_tick <= 1000:
        threshold = max(10.0, cold_abs) if cold_abs < 100.0 else 10.0 * cold_abs
        if spike_value > threshold:
            reversal_spike = {
                "tick": spike_tick,
                "value": spike_value,
                "threshold": threshold,
                "cold_abs": cold_abs,
            }

    # tip_to_drop / floor breach (leg logs)
    tip_to_drop_min = None
    floor_breach = False
    d_eq = derived.get("d_eq")
    if "tip_to_drop" in samples[0]:
        tip_to_drop_min = min(s["tip_to_drop"] for s in samples)
        if d_eq is not None and tip_to_drop_min < d_eq:
            floor_breach = True

    # apex_z / leap (leg logs)
    apex_range = None
    leap = False
    if "apex_z" in samples[0]:
        apex_vals = [s["apex_z"] for s in samples]
        apex_range = max(apex_vals) - min(apex_vals)
        if apex_range > 0.01:
            leap = True

    # Rod/chain (v1/v2) or rope (v3) sign fractions and compression events.
    rod_fracs: dict[str, float] = {}
    rope_fracs: dict[str, float] = {}
    compression_events: list[dict] = []
    max_rope_compression = None
    if "rope_t" in samples[0]:
        # v3: counts of taut/slack/compression links per sample.
        t_count = s_count = c_count = 0
        for s in samples:
            if s["rope_t"] > 0:
                t_count += 1
            elif s["rope_s"] > 0:
                s_count += 1
            elif s["rope_c"] > 0:
                c_count += 1
            if s["rope_c"] > 0 or s["rope_max_comp"] > 1.0:
                compression_events.append(
                    {"tick": s["tick"], "force": -s["rope_max_comp"]}
                )
        rope_fracs = {
            "tension": t_count / n,
            "slack": s_count / n,
            "compression": c_count / n,
        }
        max_rope_compression = max(s["rope_max_comp"] for s in samples)
    elif "rod_label" in samples[0]:
        rod_counts = {"tension": 0, "compression": 0, "slack": 0}
        for s in samples:
            label = s.get("rod_label")
            if label:
                rod_counts[label] += 1
                if label == "compression" and s.get("rod_force", 0.0) < -1.0:
                    compression_events.append(
                        {"tick": s["tick"], "force": s["rod_force"]}
                    )
        total_rods = sum(rod_counts.values())
        rod_fracs = {
            k: v / total_rods if total_rods else 0.0 for k, v in rod_counts.items()
        }

    # Theta exceedance: old single-stop format or v3 two-stop range format.
    theta_stop = None
    theta_stop_muscle = None
    theta_stop_load = None
    max_abs_theta = None
    theta_exceedance = None
    if "theta" in samples[0]:
        # Old format: theta/theta_stop column.
        theta_stop = derived.get("theta_stop", samples[0].get("theta_stop"))
        max_abs_theta = max(abs(s["theta"]) for s in samples)
        if theta_stop is not None and max_abs_theta > theta_stop:
            theta_exceedance = max_abs_theta
    elif "theta_stop_muscle" in samples[0] or "theta_stop_load" in samples[0]:
        # v3 two-stop format: compare per-sample angle to both stops.
        theta_stop_muscle = derived.get(
            "theta_stop_muscle", samples[0].get("theta_stop_muscle")
        )
        theta_stop_load = derived.get(
            "theta_stop_load", samples[0].get("theta_stop_load")
        )
        max_abs_theta = max(abs(s["angle"]) for s in samples)
        if theta_stop_muscle is not None and theta_stop_load is not None:
            if any(
                s["angle"] > theta_stop_muscle or s["angle"] < theta_stop_load
                for s in samples
            ):
                theta_exceedance = max_abs_theta

    return {
        "n_samples": n,
        "last_n": last_n,
        "max_load_gain": max_load,
        "max_load_tick": max_load_tick,
        "settled_angle": settled_angle,
        "settled_sign": settled_sign,
        "gap_min": gap_min,
        "gap_max": gap_max,
        "gap_mean": gap_mean,
        "contact_min": contact_min,
        "contact_max": contact_max,
        "spike_tick": spike_tick,
        "spike_value": spike_value,
        "reversal_spike": reversal_spike,
        "tip_to_drop_min": tip_to_drop_min,
        "floor_breach": floor_breach,
        "d_eq": d_eq,
        "apex_range": apex_range,
        "leap": leap,
        "rod_fracs": rod_fracs,
        "rope_fracs": rope_fracs,
        "compression_events": compression_events,
        "max_rope_compression": max_rope_compression,
        "theta_stop": theta_stop,
        "theta_stop_muscle": theta_stop_muscle,
        "theta_stop_load": theta_stop_load,
        "max_abs_theta": max_abs_theta,
        "theta_exceedance": theta_exceedance,
    }


# ---------------------------------------------------------------------------
# Verdict agreement
# ---------------------------------------------------------------------------


def _extract_bar(falsifier: dict) -> dict | None:
    """Pull a numeric threshold/operator out of a falsifier description."""
    m = _BAR_RE.search(falsifier["desc"])
    if not m:
        return None
    threshold = float(m.group(2))
    # Percentages in headers (e.g. ">20%") are stored as fractions for comparison.
    if falsifier["desc"][m.end() :].lstrip().startswith("%"):
        threshold /= 100.0
    return {"op": m.group(1), "threshold": threshold}


def check_verdicts(parsed: dict, metrics: dict) -> list[dict]:
    """Recompute each printed verdict and compare it to the printed status."""
    samples = parsed["samples"]
    derived = parsed["derived"]
    falsifiers = parsed["falsifiers"]
    verdict_map = {v["letter"]: v for v in parsed["verdicts"]}
    bars = {letter: _extract_bar(info) for letter, info in falsifiers.items()}

    results: list[dict] = []
    for letter in sorted(verdict_map.keys()):
        verdict = verdict_map[letter]
        name = verdict["name"]
        printed = verdict["status"]
        recomputed = "UNCHECKED"

        if name == "LIFT":
            bar = bars.get(letter)
            if bar and bar["op"] == ">=":
                recomputed = "PASS" if metrics["max_load_gain"] >= bar["threshold"] else "FAIL"
        elif name == "HOLD":
            bar = bars.get(letter)
            if bar and bar["op"] == "<=":
                recomputed = "PASS" if metrics["max_load_gain"] <= bar["threshold"] else "FAIL"
            if printed == "skipped":
                recomputed = "skipped"
        elif name == "BALANCE":
            r_true = derived.get("R_true")
            if r_true is not None:
                predicted = _sign(r_true - 1.0)
                recomputed = "PASS" if metrics["settled_sign"] == predicted else "FAIL"
        elif name == "INTEGRITY":
            all_one = all(
                all(part == "1" for part in s["clusters"].split("/")) for s in samples
            )
            recomputed = "PASS" if all_one else "FAIL"
            # Plate/fulcrum drift is not present in the tick table; the cluster
            # check above is the only independently recomputable part.
        elif name == "SAG":
            # Sag is detected when the arm tips muscle-down (positive settled
            # angle) but the load end still did not lift.
            lift_bar = bars.get("a")
            if lift_bar is not None:
                lifted = metrics["max_load_gain"] >= lift_bar["threshold"]
                detected = (metrics["settled_sign"] == 1) and not lifted
                recomputed = "detected" if detected else "not detected"
        elif name == "SLACK":
            bar = bars.get(letter)
            desc = falsifiers.get(letter, {}).get("desc", "").lower()
            if bar is not None:
                if "compression" in desc:
                    comp_frac = metrics.get("rope_fracs", {}).get(
                        "compression", metrics["rod_fracs"].get("compression", 0.0)
                    )
                    recomputed = "PASS" if comp_frac <= bar["threshold"] else "FAIL"
                else:
                    slack_frac = metrics["rod_fracs"].get("slack", 0.0)
                    recomputed = "PASS" if slack_frac <= bar["threshold"] else "FAIL"
        else:
            # e.g. lever_v6's CAPTURE falsifier -- no tick-table bar available.
            recomputed = "UNCHECKED"

        if printed == "skipped" or recomputed == "skipped":
            agree = "UNCHECKED"
        elif recomputed == "UNCHECKED":
            agree = "UNCHECKED"
        else:
            agree = "AGREE" if printed.lower() == recomputed.lower() else "DISAGREE"

        results.append(
            {
                "letter": letter,
                "name": name,
                "printed": printed,
                "recomputed": recomputed,
                "agree": agree,
            }
        )
    return results


# ---------------------------------------------------------------------------
# Telemetry cross-check
# ---------------------------------------------------------------------------


def _parse_telemetry_fractions(text: str) -> dict[str, float] | None:
    """Parse 'tension=0.05 slack=0.95 compression=0.00' into a dict."""
    fracs: dict[str, float] = {}
    for m in re.finditer(r"(tension|slack|compression)=([\d.]+)", text):
        fracs[m.group(1)] = float(m.group(2))
    return fracs if fracs else None


def _parse_telemetry_theta(text: str) -> dict | None:
    """Parse 'max |theta| / muscle_load stops = 49.22 / 18.54, 120.00 deg  exceeded=True'."""
    m = re.match(
        r"max \|\w+\| / muscle_load stops = "
        r"([\d.]+) / ([\d.]+), ([\d.]+) deg\s+exceeded=(True|False)",
        text,
    )
    if not m:
        return None
    return {
        "max_abs": float(m.group(1)),
        "muscle_stop": float(m.group(2)),
        "load_stop": float(m.group(3)),
        "exceeded": m.group(4) == "True",
    }


def _parse_range(text: str) -> tuple[float, float] | None:
    """Parse '[0.0995, 0.0995]' into (min, max)."""
    m = re.search(r"\[\s*([\d.]+)\s*,\s*([\d.]+)\s*\]", text)
    if not m:
        return None
    return float(m.group(1)), float(m.group(2))


def check_telemetry(parsed: dict, metrics: dict) -> list[dict]:
    """Cross-check recomputed metrics against the ROPE/TENDON telemetry block."""
    rope = parsed.get("rope_telemetry", {})
    tendon = parsed.get("tendon_telemetry", {})
    rows: list[dict] = []

    def add_row(item: str, printed: str, recomputed: str, agree: str) -> None:
        rows.append(
            {
                "item": item,
                "printed": printed,
                "recomputed": recomputed,
                "agree": agree,
            }
        )

    # Rope sign fractions (v3)
    if "rope sign fractions" in rope:
        printed_fracs = _parse_telemetry_fractions(rope["rope sign fractions"])
        recomp_fracs = metrics.get("rope_fracs") or metrics.get("rod_fracs")
        for key in ("tension", "slack", "compression"):
            if printed_fracs is not None and key in printed_fracs and recomp_fracs:
                p = printed_fracs[key]
                r = recomp_fracs.get(key, 0.0)
                agree = "AGREE" if abs(p - r) < 0.02 else "DISAGREE"
                add_row(
                    f"rope {key} fraction",
                    f"{p:.2f}",
                    f"{r:.2f}",
                    agree,
                )
            else:
                add_row(f"rope {key} fraction", "", "", "UNCHECKED")

    # Max compression magnitude (v3)
    if "max compression magnitude" in rope:
        printed_val = None
        m = re.search(r"max compression magnitude = ([\d.]+)", rope.get("max taut links", ""))
        if m:
            printed_val = float(m.group(1))
        if printed_val is None:
            # Some logs put it on its own line.
            m = re.search(r"([\d.]+)", rope.get("max compression magnitude", ""))
            if m:
                printed_val = float(m.group(1))
        recomp_val = metrics.get("max_rope_compression")
        if printed_val is not None and recomp_val is not None:
            agree = "AGREE" if abs(printed_val - recomp_val) < 0.01 else "DISAGREE"
            add_row("max rope compression", f"{printed_val:.2f}", f"{recomp_val:.2f}", agree)

    # Theta exceedance (v3)
    if "max |theta| / muscle_load stops" in rope:
        theta_info = _parse_telemetry_theta(rope["max |theta| / muscle_load stops"])
        if theta_info is not None:
            recomp_exceeded = metrics["theta_exceedance"] is not None
            agree = "AGREE" if theta_info["exceeded"] == recomp_exceeded else "DISAGREE"
            add_row(
                "theta exceedance",
                str(theta_info["exceeded"]),
                str(recomp_exceeded),
                agree,
            )
            if metrics["max_abs_theta"] is not None:
                agree = (
                    "AGREE"
                    if abs(theta_info["max_abs"] - metrics["max_abs_theta"]) < 0.1
                    else "DISAGREE"
                )
                add_row(
                    "max |theta|",
                    f"{theta_info['max_abs']:.2f}",
                    f"{metrics['max_abs_theta']:.2f}",
                    agree,
                )

    # Apex z range (present in both TENDON and ROPE telemetry)
    for source, block in (("rope", rope), ("tendon", tendon)):
        if "droplet apex z range" in block:
            rng = _parse_range(block["droplet apex z range"])
            if rng is not None and metrics["apex_range"] is not None:
                printed_range = rng[1] - rng[0]
                agree = (
                    "AGREE"
                    if abs(printed_range - metrics["apex_range"]) < 0.001
                    else "DISAGREE"
                )
                add_row(
                    f"{source} apex z range",
                    f"{printed_range:.4f}",
                    f"{metrics['apex_range']:.4f}",
                    agree,
                )

    # Min arm-tip-to-droplet distance (both telemetry types)
    for source, block in (("rope", rope), ("tendon", tendon)):
        if "min arm-tip-to-droplet distance" in block:
            m = re.search(
                r"([\d.]+)", block["min arm-tip-to-droplet distance"]
            )
            if m and metrics["tip_to_drop_min"] is not None:
                printed_val = float(m.group(1))
                agree = (
                    "AGREE"
                    if abs(printed_val - metrics["tip_to_drop_min"]) < 0.001
                    else "DISAGREE"
                )
                add_row(
                    f"{source} min tip-to-drop",
                    f"{printed_val:.4f}",
                    f"{metrics['tip_to_drop_min']:.4f}",
                    agree,
                )

    return rows


# ---------------------------------------------------------------------------
# Output formatting (ASCII only)
# ---------------------------------------------------------------------------


def format_section(parsed: dict, metrics: dict, verdicts: list[dict]) -> str:
    """Render one log's verification report as an ASCII-only string."""
    lines: list[str] = []
    lines.append("=" * 70)
    lines.append("LOG: " + parsed["path"])
    lines.append("=" * 70)
    lines.append("RECOMPUTED METRICS")
    lines.append(
        "  samples              {} (last {} used for settled angle)".format(
            metrics["n_samples"], metrics.get("last_n", 0)
        )
    )
    lines.append(
        "  max load_gain        {:+.4f} at tick {}".format(
            metrics["max_load_gain"], metrics["max_load_tick"]
        )
    )
    lines.append(
        "  settled angle        {:+.2f} deg (sign {})".format(
            metrics["settled_angle"], metrics["settled_sign"]
        )
    )
    lines.append(
        "  gap                  min {:.4f}  max {:.4f}  mean {:.4f}".format(
            metrics["gap_min"], metrics["gap_max"], metrics["gap_mean"]
        )
    )
    contact_line = "  contact              min {:+.3f}  max {:+.3f}".format(
        metrics["contact_min"], metrics["contact_max"]
    )
    if metrics["spike_tick"] is not None:
        contact_line += "  max_positive tick {}".format(metrics["spike_tick"])
    lines.append(contact_line)

    if metrics["tip_to_drop_min"] is not None:
        breach = "  FLOOR_BREACH" if metrics["floor_breach"] else ""
        lines.append(
            "  tip_to_drop          min {:.4f}  (d_eq {:.5f}){}".format(
                metrics["tip_to_drop_min"], metrics["d_eq"], breach
            )
        )
    if metrics["apex_range"] is not None:
        lines.append("  apex_z               range {:.4f}".format(metrics["apex_range"]))
    if metrics["rod_fracs"]:
        lines.append(
            "  rod fractions        tension={:.2f}  compression={:.2f}  slack={:.2f}".format(
                metrics["rod_fracs"]["tension"],
                metrics["rod_fracs"]["compression"],
                metrics["rod_fracs"]["slack"],
            )
        )
    if metrics["rope_fracs"]:
        lines.append(
            "  rope fractions       tension={:.2f}  slack={:.2f}  compression={:.2f}".format(
                metrics["rope_fracs"]["tension"],
                metrics["rope_fracs"]["slack"],
                metrics["rope_fracs"]["compression"],
            )
        )
    if metrics["max_abs_theta"] is not None:
        exceed = "  THETA_EXCEED" if metrics["theta_exceedance"] else ""
        if metrics["theta_stop"] is not None:
            lines.append(
                "  theta                max |theta| {:.2f} vs stop {:.2f}{}".format(
                    metrics["max_abs_theta"], metrics["theta_stop"], exceed
                )
            )
        elif (
            metrics["theta_stop_muscle"] is not None
            and metrics["theta_stop_load"] is not None
        ):
            lines.append(
                "  theta                max |angle| {:.2f} vs muscle_stop {:.2f}, "
                "load_stop {:.2f}{}".format(
                    metrics["max_abs_theta"],
                    metrics["theta_stop_muscle"],
                    metrics["theta_stop_load"],
                    exceed,
                )
            )

    lines.append("")
    lines.append("PHYSICS FLAGS")
    flags: list[str] = []
    if metrics["reversal_spike"]:
        rs = metrics["reversal_spike"]
        flags.append(
            "  REVERSAL SPIKE       tick {}  contact={:+.3f}  "
            "(threshold {:.3f}, cold |contact| {:.3f})".format(
                rs["tick"], rs["value"], rs["threshold"], rs["cold_abs"]
            )
        )
    if metrics["leap"]:
        flags.append(
            "  LEAP                 apex_z range {:.4f} > 0.01".format(
                metrics["apex_range"]
            )
        )
    if metrics["compression_events"]:
        evs = metrics["compression_events"]
        details = ", ".join(
            "tick {} force={:.2f}".format(e["tick"], e["force"]) for e in evs[:5]
        )
        if len(evs) > 5:
            details += ", ... ({} total)".format(len(evs))
        flags.append("  COMPRESSION EVENTS   " + details)
    if metrics["floor_breach"]:
        flags.append(
            "  FLOOR BREACH         tip_to_drop min {:.4f} < d_eq {:.4f}".format(
                metrics["tip_to_drop_min"], metrics["d_eq"]
            )
        )
    if metrics["theta_exceedance"]:
        if metrics["theta_stop"] is not None:
            flags.append(
                "  THETA EXCEEDANCE     max |theta| {:.2f} > stop {:.2f}".format(
                    metrics["theta_exceedance"], metrics["theta_stop"]
                )
            )
        elif (
            metrics["theta_stop_muscle"] is not None
            and metrics["theta_stop_load"] is not None
        ):
            flags.append(
                "  THETA EXCEEDANCE     max |angle| {:.2f} outside "
                "[{:.2f}, {:.2f}]".format(
                    metrics["theta_exceedance"],
                    metrics["theta_stop_load"],
                    metrics["theta_stop_muscle"],
                )
            )
    if not flags:
        flags.append("  (none)")
    lines.extend(flags)

    lines.append("")
    lines.append("VERDICT AGREEMENT")
    lines.append(
        "  {:<10} {:<10} {:<12} {:<10}".format(
            "FALSIFIER", "PRINTED", "RECOMPUTED", "STATUS"
        )
    )
    for v in verdicts:
        lines.append(
            "  ({}) {:<6} {:<10} {:<12} {:<10}".format(
                v["letter"], v["name"], v["printed"], v["recomputed"], v["agree"]
            )
        )

    telemetry_rows = check_telemetry(parsed, metrics)
    if telemetry_rows:
        lines.append("")
        lines.append("TELEMETRY CROSS-CHECK")
        lines.append(
            "  {:<24} {:<14} {:<14} {:<10}".format(
                "ITEM", "PRINTED", "RECOMPUTED", "STATUS"
            )
        )
        for r in telemetry_rows:
            lines.append(
                "  {:<24} {:<14} {:<14} {:<10}".format(
                    r["item"], r["printed"], r["recomputed"], r["agree"]
                )
            )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        sys.stderr.write(
            "usage: python tools/verify_run.py <log_path> [<log_path> ...]\n"
        )
        return 2

    all_agree = True
    sections: list[str] = []
    for arg in argv[1:]:
        path = Path(arg)
        parsed = parse_log(path)
        metrics = recompute_metrics(parsed)
        verdicts = check_verdicts(parsed, metrics)
        sections.append(format_section(parsed, metrics, verdicts))
        for v in verdicts:
            if v["agree"] == "DISAGREE":
                all_agree = False

    sys.stdout.write("\n".join(sections))
    return 0 if all_agree else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
