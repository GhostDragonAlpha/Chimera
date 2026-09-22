"""TypeB-P3 recorded trace slice: extracted from the banked wave-38 walk run stdout.

Source of record: the wave-38 lane's raw-byte run harness output
(base_stdout.txt, WALK refused_tick=295, cycle_ticks=213, F-G14/F-G26 contact
censuses), produced by the canonical engine at commit 30821ef7. This script extracts
the REAL recorded per-tick quantities the banked stdout carries -- gait phase clock
(cycle_ticks), contact count census (two_contact tick list + sub2/unload/hind-step
class lists), and the intervention (refusal) tick -- into an immutable JSON fixture.

Honesty note, preregistered: the banked stdout does NOT record per-foot contacts,
forces, body velocities or command streams. Those channels are marked
available=False for every tick in this slice, which is exactly the availability-mask
path the deployed observation recipe defines. No channel is invented.

Usage: python make_trace_slice.py <wave38_stdout.json> <out.json>
"""
from __future__ import annotations

import hashlib
import json
import re
import sys

WALK_TICKS = 302  # the banked run's recorded horizon (refusal at 295 per stdout)


def _ticks_from_list(line: str, key: str) -> list[int]:
    """Parse a census line. Some banked lines carry a leading count then '@'
    (e.g. 'unload_class_ticks=35 @ 114 115 ...') -- the count is NOT a tick."""
    if key not in line:
        return []
    tail = line.split(key, 1)[1]
    if "@" in tail:
        tail = tail.split("@", 1)[1]
    return [int(t) for t in re.findall(r"\d+", tail)]


def extract(stdout_path: str) -> dict:
    with open(stdout_path, "rb") as f:
        doc = json.loads(f.read().decode("utf-8"))
    measured = doc["measured"]
    cycle_ticks = int(doc["cycle_ticks"])

    two_contact: list[int] = []
    unload: list[int] = []
    hind_step: list[int] = []
    refused_tick = None
    for line in measured:
        if "two_contact_ticks=" in line:
            two_contact = _ticks_from_list(line, "two_contact_ticks=")
        if "unload_class_ticks=" in line:
            unload = _ticks_from_list(line, "unload_class_ticks=")
        if "hind_step_class_ticks=" in line:
            hind_step = _ticks_from_list(line, "hind_step_class_ticks=")
        if "refused_tick=" in line:
            refused_tick = int(re.search(r"refused_tick=(\d+)", line).group(1))
    assert two_contact and refused_tick is not None, "census lines not found in record"
    assert all(0 <= t <= WALK_TICKS for t in two_contact + unload + hind_step)

    two = set(two_contact)
    unl = set(unload)
    hind = set(hind_step)
    # contact_count reconstruction honesty: the census records EXACT counts only for
    # the two-contact windows and class flags; elsewhere count is UNKNOWN -> the
    # aggregate channels that need the exact count are unavailable too, except on
    # ticks where the record pins it.
    ticks = []
    for t in range(WALK_TICKS):
        rec = {
            "tick": t,
            "phase_left": ((t % cycle_ticks) / cycle_ticks) % 1.0,
            "phase_right": (((t % cycle_ticks) / cycle_ticks) + 0.5) % 1.0,
            "phase_frac": (t % cycle_ticks) / cycle_ticks,
            "phase_rate": 1.0 / cycle_ticks,
            "available_groups": ["gait_phase", "command_clock", "intervention",
                                 "sensor_health", "phase_dynamics"],
        }
        if t in two:
            rec["contact_count"] = 2
            rec["available_groups"] = rec["available_groups"] + ["contact_aggregate"]
        if t in unl:
            rec["unload_class"] = 1
            rec["available_groups"] = rec["available_groups"] + ["contact_aggregate"] \
                if "contact_aggregate" not in rec["available_groups"] \
                else rec["available_groups"]
        if t in hind:
            rec["hind_step_class"] = 1
            rec["available_groups"] = rec["available_groups"] + ["contact_aggregate"] \
                if "contact_aggregate" not in rec["available_groups"] \
                else rec["available_groups"]
        if t == refused_tick:
            rec["intervention_reason"] = "refusal"
            rec["hold_tick"] = 0
        if t >= refused_tick:
            # the walk is refused at 295: post-refusal ticks run on the held clock;
            # the intervention memory (the refusal itself + ticks-since) stays live
            rec["available_groups"] = ["command_clock", "sensor_health",
                                       "phase_dynamics", "intervention"]
        ticks.append(rec)
    return {
        "kind": "typeb_trace_slice",
        "provenance": {
            "source": "banked wave-38 walk run stdout (raw-byte harness)",
            "engine_commit": "30821ef7",
            "extracted_from": stdout_path,
            "real_channels": ["gait phase clock (cycle_ticks=213)", "two_contact census",
                              "unload_class", "hind_step_class", "refusal tick"],
            "declared_unavailable": ["per-foot contacts", "per-foot forces",
                                     "body velocity", "requested/applied commands",
                                     "exact contact count outside census windows"],
        },
        "cycle_ticks": cycle_ticks,
        "walk_ticks": WALK_TICKS,
        "refused_tick": refused_tick,
        "worst_ledger_J": float(re.search(r"worst_ledger_J=([\d.]+)",
                                          next(l for l in measured if "worst_ledger_J" in l)).group(1)),
        "ticks": ticks,
    }


def main() -> None:
    src, out = sys.argv[1], sys.argv[2]
    sl = extract(src)
    b = json.dumps(sl, sort_keys=True, separators=(",", ":")).encode("utf-8")
    with open(out, "wb") as f:
        f.write(b)
    print("slice bytes:", len(b))
    print("slice sha256:", hashlib.sha256(b).hexdigest())
    print("cycle_ticks:", sl["cycle_ticks"], "refused_tick:", sl["refused_tick"],
          "worst_ledger_J:", sl["worst_ledger_J"])


if __name__ == "__main__":
    main()
