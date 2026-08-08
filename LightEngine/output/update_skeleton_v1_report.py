"""Fill in theStandingHuman v1 report from the two run logs."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "skeleton_v1_report.md"


def parse_log(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    verdicts: dict[str, str] = {}
    samples: list[dict] = []
    worst_bodies: list[tuple[str, int]] = []
    worst_joints: list[tuple[str, float]] = []
    worst_ropes: list[tuple[str, float]] = []

    for line in lines:
        # Verdict lines like "  (a) INTEGRITY      : PASS  ..."
        m = re.match(r"\s*\(([a-f])\)\s+(\w[\w\- ]+?)\s*:\s*(\w+)", line)
        if m:
            letter, name, status = m.groups()
            verdicts[letter] = (name.strip(), status.strip())
            continue

        # Telemetry lines
        if line.startswith("[") and "tick=" in line and "|" in line:
            body = re.sub(r"^\[[^\]]+\]\s*", "", line)
            sample: dict[str, Any] = {}
            # tokenize key=value pairs separated by whitespace
            for token in re.split(r"\s+\|\s*", body):
                if "=" in token:
                    k, v = token.split("=", 1)
                    sample[k.strip()] = v.strip()
            if "tick" in sample:
                samples.append(sample)
            continue

        # Worst offenders
        if "bodies by max clusters:" in line:
            part = line.split(":", 1)[1]
            for item in part.split(","):
                item = item.strip()
                if "(" in item:
                    n, c = item.rsplit("(", 1)
                    worst_bodies.append((n.strip(), int(c.replace(")", ""))))
        if "joints by smallest capture gap:" in line:
            part = line.split(":", 1)[1]
            for item in part.split(","):
                item = item.strip()
                if "(" in item:
                    n, g = item.rsplit("(", 1)
                    worst_joints.append((n.strip(), float(g.replace(")", ""))))
        if "ropes by max compression:" in line:
            part = line.split(":", 1)[1]
            for item in part.split(","):
                item = item.strip()
                if "(" in item:
                    n, c = item.rsplit("(", 1)
                    worst_ropes.append((n.strip(), float(c.replace(")", ""))))

    return {
        "verdicts": verdicts,
        "samples": samples,
        "worst_bodies": worst_bodies,
        "worst_joints": worst_joints,
        "worst_ropes": worst_ropes,
    }


def _fmt(val):
    return "n/a" if val is None else val


def last_sample_metrics(samples: list[dict]) -> dict:
    if not samples:
        return {}
    s0 = samples[0]
    s_last = samples[-1]
    out: dict[str, Any] = {}
    for key in ("head_z", "plate_F", "com_margin", "worst_joint", "worst_body"):
        out[key] = s_last.get(key, "n/a")
    # numeric ranges
    def nums(key):
        vals = []
        for s in samples:
            try:
                vals.append(float(s[key]))
            except Exception:
                pass
        return vals
    for key in ("head_z", "plate_F", "com_margin", "capture_gap"):
        vals = nums(key)
        if vals:
            out[f"{key}_min"] = min(vals)
            out[f"{key}_max"] = max(vals)
        else:
            out[f"{key}_min"] = None
            out[f"{key}_max"] = None
    # clusters
    try:
        out["max_clusters"] = max(int(s.get("clusters", "1").replace("max", "")) for s in samples)
    except Exception:
        out["max_clusters"] = "n/a"
    return out


def verdict_md(verdicts: dict, letter: str) -> str:
    if letter not in verdicts:
        return "**TBD**"
    name, status = verdicts[letter]
    return f"**{status}**"


def main():
    main_log = ROOT / "print_skeleton_v1_log.txt"
    ctrl_log = ROOT / "print_skeleton_v1_control_log.txt"

    main_p = parse_log(main_log) if main_log.exists() else {}
    ctrl_p = parse_log(ctrl_log) if ctrl_log.exists() else {}
    main_m = last_sample_metrics(main_p.get("samples", []))
    ctrl_m = last_sample_metrics(ctrl_p.get("samples", []))

    report = REPORT.read_text(encoding="utf-8")

    # Verdict section
    verdict_block = "### Main\n\n"
    for letter in "abcde":
        verdict_block += f"- ({letter}) {main_p.get('verdicts', {}).get(letter, ('', 'TBD'))[0]:17s}: {verdict_md(main_p.get('verdicts', {}), letter)}\n"
    verdict_block += "- (f) CONTROL (FALL) : skipped\n\n### Control\n\n"
    for letter in "abcde":
        verdict_block += f"- ({letter}) {ctrl_p.get('verdicts', {}).get(letter, ('', 'TBD'))[0]:17s}: {verdict_md(ctrl_p.get('verdicts', {}), letter)}\n"
    verdict_block += f"- (f) CONTROL (FALL) : {verdict_md(ctrl_p.get('verdicts', {}), 'f')}\n"

    report = re.sub(
        r"### Main\n\n.*?(?=### Selected per-body grain counts)",
        verdict_block + "\n",
        report,
        flags=re.S,
    )

    def _rng(m, kmin, kmax, fmt):
        vmin = m.get(kmin)
        vmax = m.get(kmax)
        if vmin is None or vmax is None:
            return "n/a"
        return f"[{vmin:{fmt}}, {vmax:{fmt}}]"

    # Main run dynamics
    main_dyn = f"""### Main run

- Max clusters: {main_m.get('max_clusters', 'n/a')}, worst body: {main_m.get('worst_body', 'n/a')}
- Capture gap range: {_rng(main_m, 'capture_gap_min', 'capture_gap_max', '.4f')} lu
- COM margin range: {_rng(main_m, 'com_margin_min', 'com_margin_max', '.4f')} lu
- Head z range: {_rng(main_m, 'head_z_min', 'head_z_max', '.3f')} lu
- Plate F range: {_rng(main_m, 'plate_F_min', 'plate_F_max', '.2f')}
"""

    # Control run dynamics
    ctrl_dyn = f"""### Control run

- Max clusters: {ctrl_m.get('max_clusters', 'n/a')}, worst body: {ctrl_m.get('worst_body', 'n/a')}
- Capture gap range: {_rng(ctrl_m, 'capture_gap_min', 'capture_gap_max', '.4f')} lu
- COM margin range: {_rng(ctrl_m, 'com_margin_min', 'com_margin_max', '.4f')} lu
- Head z range: {_rng(ctrl_m, 'head_z_min', 'head_z_max', '.3f')} lu
- Plate F range: {_rng(ctrl_m, 'plate_F_min', 'plate_F_max', '.2f')}
"""

    report = re.sub(
        r"### Main run\n\n.*?### Control run\n\n.*?(?=## 5\. Verdict)",
        main_dyn + "\n" + ctrl_dyn + "\n",
        report,
        flags=re.S,
    )

    REPORT.write_text(report, encoding="utf-8")
    print("Updated", REPORT)


if __name__ == "__main__":
    main()
