"""ONT-W01 tick-3 discrete forelimb parity defect — records verifier.

Read-only, stdlib-only, CPU-only. Verifies the pinned acceptance records for the
tick-3 forelimb parity closure (the C09 contract's frozen entry states and event
traces) against their pinned claims, exactly as frozen in PREREGISTRATION.md
(committed before this file existed). The oracle is deterministic byte/token
comparison of git-object-pinned record bytes; no physics is re-run, no tolerance
exists anywhere in this module, no GPU is touched, no repo file is written.

Usage:
    python -B implementation.py --out parity_records_audit.json

Exit code 0 iff the frozen done_when decision rule evaluates SATISFIED_BY_RECORDS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

SCHEMA = "ont-w01.parity_records_audit.v1"
TASK_ID = "W01"
SCOPE_SHA256 = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"
CRITERIA_SHA256 = "c42bd4f9ce228ebddcb1be6c87b261979c8a38987ff3d5e74ad37536f397be24"
PREREG_BLOB = "6bd7e3c94e14897ffe0280ebe31f9322b1fc3a5d"

# ---------------------------------------------------------------------------
# Pinned records (frozen in PREREGISTRATION.md before this module was written)
# ---------------------------------------------------------------------------

ARCHIVE_TAG = "archive/20260925/agent/typeb-gpu-finish-20260922"
PINNED_COMMIT = "a62b286effa27ee2db7bbcb65507a2ac45ad0d0c"  # SHUTDOWN CHECKPOINT
DEFECT_COMMIT = "7a845267"  # closeout-3, the defect-era census
GPU_PREFIX = "tools/science_funnel/typeb_gpu/"
BARS_PATH = "tools/science_funnel/validation/typeb_gpu_fullport_20260921/bars_split_b32.json"
P02P03_REPORT_PATH = "tools/monkey_campaign/agents/P02P03/report.md"

RECORDS: Dict[str, Dict[str, str]] = {
    "R-state-host": {"rev": PINNED_COMMIT, "path": GPU_PREFIX + "co8_t41_fixture/state_t40_host.txt"},
    "R-state-gpu": {"rev": PINNED_COMMIT, "path": GPU_PREFIX + "co8_t41_fixture/state_t40_gpu.txt"},
    "R-state-cpp": {"rev": PINNED_COMMIT, "path": GPU_PREFIX + "co8_t41_fixture/state_t39_cpp.txt"},
    "R-scene": {"rev": PINNED_COMMIT, "path": GPU_PREFIX + "co8_t41_fixture/scene_sha256.txt"},
    "R-cp45": {"rev": PINNED_COMMIT, "path": GPU_PREFIX + "cp_walk45.txt"},
    "R-hl45": {"rev": PINNED_COMMIT, "path": GPU_PREFIX + "hl_walk45.txt"},
    "R-csub5": {"rev": DEFECT_COMMIT, "path": GPU_PREFIX + "csub_t5.txt"},
    "R-ksub5": {"rev": DEFECT_COMMIT, "path": GPU_PREFIX + "ksub_t5.txt"},
    "R-csub41": {"rev": PINNED_COMMIT, "path": GPU_PREFIX + "csub41L.err"},
    "R-ksub41": {"rev": PINNED_COMMIT, "path": GPU_PREFIX + "ksub41N.out"},
    "R-hlv2": {"rev": PINNED_COMMIT, "path": GPU_PREFIX + "co8_hl_v2.out"},
    "R-hlpre": {"rev": PINNED_COMMIT, "path": GPU_PREFIX + "co8_hl_full6.out"},
    "R-gpuv2": {"rev": PINNED_COMMIT, "path": GPU_PREFIX + "co8_dll_v2b_120.txt"},
    "R-bars": {"rev": PINNED_COMMIT, "path": BARS_PATH},
}

# Pinned bar sentences (commit-message substrings), frozen from the receipts.
MESSAGE_CLAIMS: Sequence[Tuple[str, str]] = (
    ("2dee187d", "BIT-EXACT THROUGH 41 ALIGNED WALK STATES"),
    ("3ab21e5f", "census 20/20 SUBPRE + 20/20 TAUFULL + 20/20 SUBFULL"),
    ("3ab21e5f", "the entire tick-3 and tick-41 interiors line-identical"),
    ("055d6c05", "HOST REPLAY WALKS PAST TICK 41 to t=100 rc=0"),
    ("055d6c05", "host-GPU v2 parity t=1..43"),
)
P02P03_CLAIMS: Sequence[str] = (
    "## 2. W01 — tick-3 discrete forelimb parity defect",
    "Verdict: CLOSED",
)
RESOLVED_COMMITS = (
    "7a845267", "2dee187d", "3ab21e5f", "77023970", "37ab0c8f",
    "2c1dc8f2", "b643a850", "9376c3d8", "ef3f3554", "055d6c05", "8feea42a",
)

SCENE_SHA256 = "f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342"
HLV2_FINAL_SUMMARY = "y=0.215657301 vx=0.664807 rc=0 adv=7 refused=0 ticks=100"

# ---------------------------------------------------------------------------
# Record collection (read-only git plumbing)
# ---------------------------------------------------------------------------


def _git(args: Sequence[str], attempts: int = 3) -> bytes:
    """Run read-only git plumbing, retrying transient stream failures."""
    last = None
    for _ in range(attempts):
        proc = subprocess.run(["git"] + list(args), capture_output=True)
        if proc.returncode == 0:
            return proc.stdout
        last = proc
        time.sleep(0.2)
    raise RuntimeError("git %s failed: %s" % (" ".join(args), (last.stderr or b"?").decode("utf-8", "replace")[:400]))


def git_object_exists(rev: str) -> bool:
    proc = subprocess.run(["git", "cat-file", "-e", rev + "^{commit}"], capture_output=True)
    return proc.returncode == 0


def git_blob_oid(rev: str, path: str) -> Optional[str]:
    proc = subprocess.run(["git", "rev-parse", "%s:%s" % (rev, path)], capture_output=True)
    if proc.returncode != 0:
        return None
    return proc.stdout.decode().strip()


def git_commit_message(rev: str) -> str:
    return _git(["log", "-1", "--format=%B", rev]).decode("utf-8", "replace")


def read_record(rev: str, path: str) -> bytes:
    return _git(["cat-file", "-p", "%s:%s" % (rev, path)])


def collect_records() -> Dict[str, Optional[bytes]]:
    out: Dict[str, Optional[bytes]] = {}
    for name, pin in RECORDS.items():
        try:
            out[name] = read_record(pin["rev"], pin["path"])
        except RuntimeError:
            out[name] = None
    return out


def collect_identities() -> Dict[str, dict]:
    idents: Dict[str, dict] = {}
    idents["archive_tag_commit"] = _git(["rev-parse", ARCHIVE_TAG + "^{commit}"]).decode().strip()
    for name, pin in RECORDS.items():
        oid = git_blob_oid(pin["rev"], pin["path"])
        idents[name] = {"rev": pin["rev"], "path": pin["path"], "blob_oid": oid}
    return idents


# ---------------------------------------------------------------------------
# Parsers (exact token comparisons; no numeric tolerance anywhere)
# ---------------------------------------------------------------------------

_FULL_RE = re.compile(r"^FULL t=(\d+)\s(.*)$")
_TICK_RE = re.compile(r"^tick\s+(\d+):(.*)$")
_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
_PHYSICS_RE = re.compile(r"^(q|v|tau)(\d+)$")


def normalize_lines(raw: bytes) -> List[str]:
    """Split into lines with the capture's CR artifact removed (line-final only)."""
    text = raw.decode("utf-8", "replace")
    return [line.rstrip("\r") for line in text.splitlines()]


def parse_full_states(raw: bytes) -> Dict[int, str]:
    """FULL t=N lines -> {N: state token stream (everything after 'FULL t=N')}."""
    states: Dict[int, str] = {}
    for line in normalize_lines(raw):
        m = _FULL_RE.match(line)
        if m:
            states[int(m.group(1))] = m.group(2).strip()
    return states


def parse_tick_lines(raw: bytes) -> Dict[int, str]:
    """'tick   N: summary' lines -> {N: summary text}."""
    ticks: Dict[int, str] = {}
    for line in normalize_lines(raw):
        m = _TICK_RE.match(line)
        if m:
            ticks[int(m.group(1))] = m.group(2).strip()
    return ticks


def parse_state_file(raw: bytes) -> Tuple[Optional[str], int]:
    """Fixture state file -> (the identical FULL state body, line count) or (None, n)."""
    bodies = []
    for line in normalize_lines(raw):
        m = _FULL_RE.match(line)
        if m:
            bodies.append(m.group(2).strip())
    if not bodies:
        return None, 0
    first = bodies[0]
    return (first if all(b == first for b in bodies) else None), len(bodies)


_CENSUS_RE = re.compile(r"^(SUBPRE|SUBFULL|TAUFULL)\s+t=(\d+)\s+sub=(\d+)\s(.*)$")


def parse_census(raw: bytes) -> List[dict]:
    """Census records positionally, with physics-only token dictionaries."""
    records: List[dict] = []
    for line in normalize_lines(raw):
        m = _CENSUS_RE.match(line)
        if not m:
            continue
        kind, t, sub, rest = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        toks: Dict[str, str] = {}
        for field in rest.split():
            kv = _KV_RE.match(field)
            if kv and _PHYSICS_RE.match(kv.group(1)):
                toks[kv.group(1)] = kv.group(2)
        records.append({"kind": kind, "t": t, "sub": sub, "toks": toks})
    return records


def census_divergence(a: List[dict], b: List[dict]) -> Tuple[Optional[dict], dict]:
    """Kind-wise positional divergence of two census record lists.

    The kernel-side drill labels a SUBFULL record with the ENDING substep while
    the C++ side labels it with the STARTING substep (a measured drill
    convention, not a physics fact), so records are aligned within each kind and
    compared on physics tokens only. Returns (first_divergence_or_None, notes)
    where notes carry the per-kind first divergences and the measured SUBFULL
    sub-label convention.
    """
    notes: dict = {"per_kind_first_divergence": {}, "subfull_sublabel_pairs": None}
    first: Optional[dict] = None
    subfull_pairs: List[List[int]] = []
    for kind in ("SUBPRE", "TAUFULL", "SUBFULL"):
        ra_list = [r for r in a if r["kind"] == kind]
        rb_list = [r for r in b if r["kind"] == kind]
        kind_div: Optional[dict] = None
        for i, (ra, rb) in enumerate(zip(ra_list, rb_list)):
            if kind == "SUBFULL":
                subfull_pairs.append([ra["sub"], rb["sub"]])
            if ra["toks"] != rb["toks"]:
                differing = sorted(k for k in set(ra["toks"]) | set(rb["toks"])
                                   if ra["toks"].get(k) != rb["toks"].get(k))
                kind_div = {"kind": kind, "index_in_kind": i, "t": ra["t"], "sub": ra["sub"],
                            "sub_b": rb["sub"], "reason": "physics", "differing_keys": differing[:8]}
                break
        if kind_div is None and len(ra_list) != len(rb_list):
            kind_div = {"kind": kind, "index_in_kind": min(len(ra_list), len(rb_list)),
                        "reason": "record_count", "len_a": len(ra_list), "len_b": len(rb_list)}
        notes["per_kind_first_divergence"][kind] = kind_div
        if kind_div is not None and first is None:
            first = kind_div
    if subfull_pairs:
        notes["subfull_sublabel_pairs"] = subfull_pairs
        notes["subfull_convention_kernel_is_starting_plus_one"] = all(b == a_ + 1 for a_, b in subfull_pairs)
    return first, notes


def aligned_divergence(cp: Dict[int, str], hl: Dict[int, str], up_to: int) -> Optional[int]:
    """First aligned host tick N in 1..up_to with hl[N] != cp[N-1] (or a missing side)."""
    for n in range(1, up_to + 1):
        if n not in hl or (n - 1) not in cp:
            return n
        if hl[n] != cp[n - 1]:
            return n
    return None


# ---------------------------------------------------------------------------
# Frozen claims (P1..P10 of PREREGISTRATION.md)
# ---------------------------------------------------------------------------


def _check(cid: str, prediction: str, ok: bool, detail: dict) -> dict:
    return {"check": cid, "prediction": prediction, "verdict": "PASS" if ok else "FAIL", "detail": detail}


def verify_records(records: Mapping[str, Optional[bytes]], identities: Mapping[str, object]) -> List[dict]:
    checks: List[dict] = []
    missing = sorted(n for n, b in records.items() if b is None)

    # P1 — identities -----------------------------------------------------------------
    p1_detail: dict = {"missing_records": missing, "resolved_commits": [], "message_claims": [], "p02p03_claims": [],
                       "archive_tag_commit": identities.get("archive_tag_commit")}
    p1_ok = not missing and identities.get("archive_tag_commit") == PINNED_COMMIT
    for rev in RESOLVED_COMMITS:
        ok = git_object_exists(rev)
        p1_detail["resolved_commits"].append({"rev": rev, "resolves": ok})
        p1_ok = p1_ok and ok
    for rev, needle in MESSAGE_CLAIMS:
        present = needle in git_commit_message(rev)
        p1_detail["message_claims"].append({"rev": rev, "claim": needle, "present": present})
        p1_ok = p1_ok and present
    try:
        report = read_record("8feea42a", P02P03_REPORT_PATH).decode("utf-8", "replace")
        for needle in P02P03_CLAIMS:
            present = needle in report
            p1_detail["p02p03_claims"].append({"claim": needle, "present": present})
            p1_ok = p1_ok and present
    except RuntimeError:
        p1_detail["p02p03_claims"].append({"claim": P02P03_REPORT_PATH, "present": False})
        p1_ok = False
    checks.append(_check("P1", "identities", p1_ok, p1_detail))

    # P2 — frozen entry states ----------------------------------------------------------
    body_host, n_host = parse_state_file(records["R-state-host"] or b"")
    body_gpu, n_gpu = parse_state_file(records["R-state-gpu"] or b"")
    body_cpp, n_cpp = parse_state_file(records["R-state-cpp"] or b"")
    scene = normalize_lines(records["R-scene"] or b"")[0].strip()
    cp_states = parse_full_states(records["R-cp45"] or b"")
    hl_states = parse_full_states(records["R-hl45"] or b"")
    p2_detail = {
        "sha256_state_host": hashlib.sha256(records["R-state-host"] or b"").hexdigest(),
        "sha256_state_gpu": hashlib.sha256(records["R-state-gpu"] or b"").hexdigest(),
        "host_gpu_bytes_equal": (records["R-state-host"] == records["R-state-gpu"]) and records["R-state-host"] is not None,
        "cpp_differs_only_in_tick_label": None,
        "host_body_equals_hl45_t40": body_host == hl_states.get(40),
        "cpp_body_equals_cp45_t39": body_cpp == cp_states.get(39),
        "scene_sha256": scene,
        "fixture_full_lines": {"host": n_host, "gpu": n_gpu, "cpp": n_cpp},
    }
    if body_host is not None and body_cpp is not None:
        host_lines = normalize_lines(records["R-state-host"] or b"")
        cpp_lines = normalize_lines(records["R-state-cpp"] or b"")
        same_structure = len(host_lines) == len(cpp_lines)
        label_only = same_structure and all(
            hl == cl or cl.replace("FULL t=39 ", "FULL t=40 ", 1) == hl
            for hl, cl in zip(host_lines, cpp_lines)
        )
        p2_detail["cpp_differs_only_in_tick_label"] = bool(label_only and body_cpp == body_host)
    p2_ok = bool(
        p2_detail["host_gpu_bytes_equal"]
        and body_host is not None and body_gpu is not None
        and p2_detail["cpp_differs_only_in_tick_label"]
        and p2_detail["host_body_equals_hl45_t40"]
        and p2_detail["cpp_body_equals_cp45_t39"]
        and scene == SCENE_SHA256
    )
    checks.append(_check("P2", "frozen entry states", p2_ok, p2_detail))

    # P3 — walk-pair parity incl. the tick-3 window --------------------------------------
    first_bad = aligned_divergence(cp_states, hl_states, 41)
    tick3_window = {n: hl_states.get(n) == cp_states.get(n - 1) for n in range(1, 5)}
    beyond = aligned_divergence(cp_states, hl_states, 48)  # probe the whole overlap
    p3_detail = {
        "aligned_equal_through_41": first_bad is None,
        "first_divergence_within_1_41": first_bad,
        "tick3_window_1_4_equal": tick3_window,
        "first_divergence_within_1_48": beyond,
        "cpp_states": len(cp_states),
        "host_states": len(hl_states),
    }
    p3_ok = first_bad is None and all(tick3_window.values()) and (beyond is None or beyond >= 42)
    checks.append(_check("P3", "walk pair bit-exact through aligned state 41 incl. tick-3 window", p3_ok, p3_detail))

    # P4 — defect-era census record (the named tick-3 defect is real in records) ---------
    csub5 = parse_census(records["R-csub5"] or b"")
    ksub5 = parse_census(records["R-ksub5"] or b"")
    div5, notes5 = census_divergence(csub5, ksub5)
    subpre_div = notes5["per_kind_first_divergence"].get("SUBPRE")
    p4_detail = {
        "census_records": {"csub_t5": len(csub5), "ksub_t5": len(ksub5)},
        "first_divergence": div5,
        "subpre_first_divergence": subpre_div,
        "matches_named_defect": bool(subpre_div and subpre_div.get("t") == 3 and subpre_div.get("sub") == 3),
    }
    p4_ok = bool(p4_detail["matches_named_defect"])
    checks.append(_check("P4", "defect-era first diverging census record is SUBPRE t=3 sub=3", p4_ok, p4_detail))

    # P5 — post-fix census 20/20/20 -------------------------------------------------------
    csub41 = parse_census(records["R-csub41"] or b"")
    ksub41 = parse_census(records["R-ksub41"] or b"")

    def _counts(recs: List[dict]) -> Dict[str, int]:
        out = {"SUBPRE": 0, "TAUFULL": 0, "SUBFULL": 0}
        for r in recs:
            out[r["kind"]] += 1
        return out

    counts_a, counts_b = _counts(csub41), _counts(ksub41)
    div41, notes41 = census_divergence(csub41, ksub41)
    p5_detail = {
        "counts_cpp": counts_a,
        "counts_kernel": counts_b,
        "counts_match_claim": counts_a == counts_b == {"SUBPRE": 20, "TAUFULL": 20, "SUBFULL": 20},
        "first_divergence": div41,
        "subfull_sublabel_convention_measured": notes41.get("subfull_convention_kernel_is_starting_plus_one"),
    }
    p5_ok = p5_detail["counts_match_claim"] and div41 is None
    checks.append(_check("P5", "post-fix census 20/20 SUBPRE + 20/20 TAUFULL + 20/20 SUBFULL bit-exact", p5_ok, p5_detail))

    # P6 — v2 host replay past tick 41 -----------------------------------------------------
    hlv2_ticks = parse_tick_lines(records["R-hlv2"] or b"")
    hlv2_states = parse_full_states(records["R-hlv2"] or b"")
    hlv2_lines = normalize_lines(records["R-hlv2"] or b"")
    refused = [ln for ln in hlv2_lines if ln.startswith("REFUSED")]
    p6_detail = {
        "final_tick_summary": hlv2_ticks.get(100),
        "expected_final_tick_summary": HLV2_FINAL_SUMMARY,
        "refused_lines": refused,
        "tick_lines": len(hlv2_ticks),
        "full_states_count": len(hlv2_states),
        "full_states_max_t": max(hlv2_states) if hlv2_states else None,
    }
    p6_ok = bool(hlv2_ticks.get(100) == HLV2_FINAL_SUMMARY and not refused and len(hlv2_states) == 100)
    checks.append(_check("P6", "v2 host replay walks past tick 41 to t=100 rc=0", p6_ok, p6_detail))

    # P7 — pre-v2 vs v2 host: identical t=1..40, first divergence at t=41 -------------------
    hlpre_states = parse_full_states(records["R-hlpre"] or b"")
    first_p7 = None
    for n in range(1, 101):
        if hlpre_states.get(n) != hlv2_states.get(n):
            first_p7 = n
            break
    equal_1_40 = all(hlpre_states.get(n) == hlv2_states.get(n) for n in range(1, 41))
    p7_detail = {"first_divergence": first_p7, "equal_1_40": equal_1_40,
                 "hlpre_states": len(hlpre_states), "hlv2_states": len(hlv2_states)}
    p7_ok = equal_1_40 and first_p7 == 41
    checks.append(_check("P7", "pre-v2 vs v2 host identical t=1..40, first divergence at t=41", p7_ok, p7_detail))

    # P8 — host-GPU v2 parity t=1..43 --------------------------------------------------------
    gpu_states = parse_full_states(records["R-gpuv2"] or b"")
    diffs = [n for n in range(1, 44) if gpu_states.get(n) != hlv2_states.get(n)]
    p8_detail = {"gpu_states": len(gpu_states), "differing_ticks_1_43": diffs,
                 "gpu_max_t": max(gpu_states) if gpu_states else None}
    p8_ok = len(gpu_states) == 43 and not diffs
    checks.append(_check("P8", "host-GPU v2 parity on every FULL state t=1..43", p8_ok, p8_detail))

    # P9 — frozen bars record ------------------------------------------------------------------
    p9_detail: dict = {}
    p9_ok = False
    try:
        bars = json.loads((records["R-bars"] or b"").decode("utf-8"))
        freefall = bars.get("freefall", {})
        stand = bars.get("stand", {})
        nominal = bars.get("nominal", {})
        survival = bars.get("survival", {})
        horizons = [float(h) for h in survival.get("horizons", [])]
        median = sorted(horizons)[len(horizons) // 2] if len(horizons) % 2 == 1 else (
            (sorted(horizons)[len(horizons) // 2 - 1] + sorted(horizons)[len(horizons) // 2]) / 2.0
            if horizons else None)
        p9_detail = {
            "freefall_parity_pass": freefall.get("parity_pass"),
            "freefall_measured_g": freefall.get("measured_g"),
            "freefall_err": freefall.get("err"),
            "stand_parity_pass": stand.get("parity_pass"),
            "stand_max_scaled_diff": stand.get("max_scaled_diff"),
            "nominal_horizon": nominal.get("horizon"),
            "nominal_refused_class": nominal.get("refused_class"),
            "nominal_hind_fires": nominal.get("hind_fires"),
            "nominal_fore_lifts": nominal.get("fore_lifts"),
            "survival_seeds": survival.get("seeds"),
            "survival_median_horizon": median,
            "survival_max_horizon": max(horizons) if horizons else None,
        }
        p9_ok = bool(
            freefall.get("parity_pass") is True
            and freefall.get("measured_g") == 9.806650000000689
            and isinstance(freefall.get("err"), (int, float)) and freefall["err"] <= 1e-9
            and stand.get("parity_pass") is False
            and stand.get("max_scaled_diff") == 0.9511245759469239
            and nominal.get("horizon") == 40 and nominal.get("refused_class") == 5
            and nominal.get("hind_fires") == 0 and nominal.get("fore_lifts") == 0
            and survival.get("seeds") == 64 and median == 40.0
            and horizons and max(horizons) < 100
        )
    except (ValueError, TypeError) as exc:
        p9_detail["error"] = str(exc)
    checks.append(_check("P9", "frozen bars record matches the pinned measured table", p9_ok, p9_detail))

    return checks


def verdict_from_checks(checks: Sequence[dict]) -> Tuple[str, List[str]]:
    by_id = {c["check"]: c["verdict"] for c in checks}
    required = ["P1", "P2", "P3", "P5", "P6", "P7", "P8", "P9"]
    failed = [cid for cid in required if by_id.get(cid) != "PASS"]
    if by_id.get("P4") != "PASS":
        failed.append("P4(defect-record)")
    if not failed and all(by_id.get(cid) == "PASS" for cid in required + ["P4"]):
        return "SATISFIED_BY_RECORDS", failed
    return "NOT_SATISFIED", sorted(set(failed))


def run_audit(out_path: Optional[str] = None) -> dict:
    records = collect_records()
    identities = collect_identities()
    for name, blob in records.items():
        if blob is not None:
            identities[name]["raw_sha256"] = hashlib.sha256(blob).hexdigest()
            identities[name]["size_bytes"] = len(blob)
    checks = verify_records(records, identities)
    verdict, failed = verdict_from_checks(checks)
    audit = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "planning_id": "W01",
        "scope_sha256": SCOPE_SHA256,
        "criteria_sha256": CRITERIA_SHA256,
        "preregistration_blob_oid": PREREG_BLOB,
        "evidence_class": "records/offline (pinned definitions, ledgers, numerical evidence)",
        "numerical_evidence": True,
        "archive_tag": ARCHIVE_TAG,
        "pinned_commit": PINNED_COMMIT,
        "identities": identities,
        "checks": checks,
        "done_when": "Frozen entry-state and event traces satisfy the existing CPU/GPU acceptance bar",
        "done_when_verdict": verdict,
        "failed_predictions": failed,
        "boundaries": {
            "not_claimed": [
                "live GPU qualification re-runs (TIE2 Q1/Q2, queued; W03 scope)",
                "C3 clean-window throughput re-measure (W03 scope)",
                "anchor-version A/B decision (W03/Astra scope)",
                "trained walking acceptance (W05+)",
                "walk-level GPU bars green beyond the recorded freefall GREEN (stand/C1/C2 RED residuals charged to W03's class-41 residual, not to the tick-3 event)",
            ],
            "nonvisual_reason": "Records profile: the truth of this clause lives in pinned ledgers and numerical traces; no visual artifact is evidence here.",
        },
    }
    if out_path:
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(audit, fh, indent=1, sort_keys=False)
            fh.write("\n")
    return audit


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None, help="write the audit JSON here")
    args = parser.parse_args(argv)
    audit = run_audit(args.out)
    print("done_when_verdict:", audit["done_when_verdict"])
    for c in audit["checks"]:
        print("  [%s] %s" % (c["verdict"], c["check"]))
    failed = audit["failed_predictions"]
    if failed:
        print("failed predictions:", ", ".join(failed))
    return 0 if audit["done_when_verdict"] == "SATISFIED_BY_RECORDS" else 1


if __name__ == "__main__":
    sys.exit(main())
