"""reconstruct.py -- attempt graph (waves 28-38), serial path (35-38), reconciliation.

Rule-0 prereg (frozen BEFORE this code):
  tools/science_funnel/validation/workflow_telemetry_20260921/PREREGISTER_F_EVENT_GAP.md

Outcome rule (fixed in the prereg): assigned from the receipts' own verdicts and
ship-commit messages, never re-judged:
  pass True  -> certified
  pass False -> fired
  pass None  -> pruned if the ship message names the premise FALSIFIED,
                else fired if the successor's base description names this wave
                REVERTED, else certified
  no receipt -> abandoned (no terminal record recoverable; anchors still required)

Missing TIMING is null (unknown), never zero. F-EVENT-GAP is about EVENTS, not
clocks: a wave-level attempt visible in any independent record must exist in the
ledger, and every ledger attempt needs >=1 independent anchor.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from . import collectors as C
from .schema import Event, digest

SCOPE = {str(w) for w in C.WAVES}
_ORDER = [str(w) for w in C.WAVES]


def _wave_sort(wv: str):
    return (int(wv.rstrip("b")), 1 if wv.endswith("b") else 0)


def _epoch(ts: Optional[str]) -> Optional[float]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts).timestamp()
    except ValueError:
        return None


def _span(t0: Optional[float], t1: Optional[float]) -> Optional[float]:
    if t0 is None or t1 is None:
        return None
    return round(max(0.0, t1 - t0), 1)


def parse_base_sha(base: str) -> Optional[str]:
    if not base:
        return None
    m = re.match(r"\s*([0-9a-f]{8,})", base)
    return m.group(1) if m else None


# --------------------------------------------------------------- attempts --

def _ship_commit(wave: str, commits: dict) -> Optional[dict]:
    rows = commits.get(wave, [])
    ships = [r for r in rows if r.get("role") == "ship"]
    if not ships:
        # receipt-less attempts (wave-28b): the merge wrapper is the only
        # terminal record of the arm -- still an independent git anchor
        ships = [r for r in rows if r.get("role") == "merge"]
    ships.sort(key=lambda r: r["ts"])
    return ships[-1] if ships else None


def _prereg_commit(wave: str, commits: dict) -> Optional[dict]:
    rows = [r for r in commits.get(wave, []) if r.get("role") == "prereg"]
    rows.sort(key=lambda r: r["ts"])
    return rows[0] if rows else None


def _child_base_text(wave: str, receipts: dict) -> str:
    """The NEXT receipt's `base` description of this wave's shipped state."""
    i = _ORDER.index(wave)
    for nxt in _ORDER[i + 1:]:
        r = receipts.get(nxt)
        if r:
            return r["doc"].get("base", "") or ""
    return ""


def outcome_for(wave: str, receipts: dict, commits: dict) -> tuple:
    """-> (outcome, note). Fixed by the prereg; no re-judgment of physics."""
    r = receipts.get(wave)
    ship = _ship_commit(wave, commits)
    ship_msg = ship["subject"] if ship else ""
    if not r:
        note = ("no wave receipt; recorded abandoned per the frozen rule -- the "
                "wave's own pass verdict is not recoverable from a receipt")
        if ship:
            note += f"; terminal record IS recoverable: git {ship['repo']}:" \
                    f"{ship['sha']} \"{ship['subject'][:110]}\""
        return "abandoned", note
    p = r["doc"].get("pass")
    if p is True:
        return "certified", "receipt pass=true"
    if p is False:
        return "fired", "receipt pass=false" + (
            " (law REVERTED per ship commit)" if "REVERT" in ship_msg.upper()
            else "")
    if "FALSIF" in ship_msg.upper():
        note = ("receipt pass=null; ship message names a premise FALSIFIED")
        if "shipped" in ship_msg.lower():
            # recorded discrepancy: the keyword matched, but the same subject
            # also reports the law SHIPPED (wave-31: a SUB-hypothesis was
            # falsified inside the decomposition). The frozen rule's output is
            # kept; the auditor adjudicates from the anchors. Not tuned away.
            note += (" -- DISCREPANCY: the same subject also reports the law "
                     "SHIPPED (likely a sub-hypothesis falsified inside the "
                     "decomposition); frozen keyword rule kept, auditor to "
                     "adjudicate")
        return "pruned", note
    if "REVERT" in _child_base_text(wave, receipts).upper():
        return ("fired",
                "receipt pass=null; successor base names this wave REVERTED")
    return ("certified",
            "receipt pass=null; ship message reports the law shipped and no "
            "successor record reverts it")


def build_attempts(receipts: dict, commits: dict) -> dict:
    """attempt_id-keyed attempt records (the ledger's spine)."""
    attempts = {}
    for w in C.WAVES:
        wv = str(w)
        r = receipts.get(wv)
        ship = _ship_commit(wv, commits)
        prereg = _prereg_commit(wv, commits)
        base_sha = parse_base_sha(r["doc"].get("base", "")) if r else None
        outcome, onote = outcome_for(wv, receipts, commits)
        policy = None
        if r:
            d = r["doc"]
            policy = (d.get("frozen_rule_0_sha")
                      or d.get("frozen_rule_0_amendment_sha")
                      or digest(d.get("rule_0")))
        attempts[wv] = {
            "attempt_id": f"wave-{wv}",
            "wave": wv,
            "lane": (r["doc"].get("lane") if r else
                     (ship["subject"][:70] if ship else
                      f"wave-{wv} (lane unknown)")),
            "receipt": r,
            "parent_manifest_sha": base_sha,
            "claim_digest": digest(r["doc"].get("rule_0")) if r else None,
            "policy_version": policy,
            "prereg_commit": prereg,
            "ship_commit": ship,
            "outcome": outcome,
            "outcome_note": onote,
            "parent_attempt": None,
            "child_attempts": [],
        }
    # causal links: parent = the wave whose SHIP sha starts the base manifest
    ship_by_sha = {}
    for wv, a in attempts.items():
        sc = a["ship_commit"]
        if sc:
            ship_by_sha[sc["sha"]] = wv
    for wv, a in attempts.items():
        psha = a["parent_manifest_sha"]
        if psha:
            for sha, pw in ship_by_sha.items():
                if psha.startswith(sha) or sha.startswith(psha):
                    a["parent_attempt"] = f"wave-{pw}"
                    break
    for wv, a in attempts.items():
        p = a["parent_attempt"]
        if p:
            attempts[p.split("-", 1)[1]]["child_attempts"].append(a["attempt_id"])
    return attempts


# ------------------------------------------------- serial path (waves 35-38) --

def serial_path(attempts: dict, artifacts: dict) -> dict:
    """The measured division of wall-clock time on the serial critical path.

    Phase boundaries (fixed in the prereg, artifact-anchored):
      wait_for_lead : parent ship commit      -> first receipt-dir artifact mtime
      reproduce     : first artifact          -> base_tr_stdout mtime
      mine_derive   : base_tr_stdout          -> PRE-REGISTRATION commit
      build_run     : PRE-REGISTRATION commit -> candidate wNN_stdout.txt mtime
      verify_decide : candidate stdout        -> SHIP commit
    """
    out = {}
    for w in C.TIMED_WAVES:
        wv = str(w)
        a = attempts.get(wv)
        art = artifacts.get(wv, {}).get("files", {})
        if not a or not art:
            out[wv] = {"error": "artifacts missing"}
            continue
        times = {k: _epoch(v) for k, v in art.items()}
        ship_ts = _epoch(a["ship_commit"]["ts"]) if a["ship_commit"] else None
        prereg_ts = _epoch(a["prereg_commit"]["ts"]) if a["prereg_commit"] else None
        parent_ts = _ship_ts_of_parent(attempts, wv)
        # Files whose mtime PREDATES the parent's ship commit are carried-in
        # instruments (e.g. the declared run harness copied forward with its
        # old mtime) -- they are inherited state, not this lane's activity.
        lane_times = {k: t for k, t in times.items()
                      if parent_ts is None or t is None or t >= parent_ts - 1}
        first_art = min([t for t in lane_times.values() if t is not None],
                        default=None)
        dropped = sorted(set(times) - set(lane_times))
        base_tr = _first_file_ts(times, ("base_tr_stdout.txt",
                                         "base_tr_stderr.txt"))
        cand = _first_file_ts(times, (f"w{wv}_stdout.txt", f"w{wv}_stderr.txt"))
        phases = {
            "wait_for_lead": _span(parent_ts, first_art),
            "reproduce": _span(first_art, base_tr),
            "mine_derive": _span(base_tr, prereg_ts),
            "build_run": _span(prereg_ts, cand),
            "verify_decide": _span(cand, ship_ts),
        }
        lane_span = _span(parent_ts, ship_ts)
        total = sum(v for v in phases.values() if v is not None)
        delta = (round(lane_span - total, 1)
                 if lane_span is not None and all(v is not None for v in
                                                  phases.values()) else None)
        out[wv] = {
            "phases_seconds": phases,
            "lane_span_seconds": lane_span,
            "reconciled_sum_seconds": round(total, 1),
            "f_time_accounting_delta_seconds": delta,
            "f_time_accounting": ("PASS" if delta is not None and
                                  abs(delta) <= 120 else "FIRES"),
            "boundary_anchors": {
                "parent_ship": parent_ts, "first_artifact": first_art,
                "base_trace": base_tr, "prereg_commit": prereg_ts,
                "candidate_stdout": cand, "ship_commit": ship_ts},
            "carried_in_artifacts_ignored": dropped,
            "note": "build and run are NOT separable in the surviving artifacts; "
                    "build_run is the combined interval (recorded limitation, "
                    "never split by guess). Artifacts with mtimes predating the "
                    "parent's ship commit are carried-in instruments and are "
                    "excluded from lane phases (recorded, not hidden).",
        }
    return out


def _ship_ts_of_parent(attempts: dict, wv: str) -> Optional[float]:
    a = attempts[wv]
    p = a.get("parent_attempt")
    if p:
        pa = attempts.get(p.split("-", 1)[1])
        if pa and pa.get("ship_commit"):
            return _epoch(pa["ship_commit"]["ts"])
    return None


def _first_file_ts(times: dict, names) -> Optional[float]:
    for n in names:
        if times.get(n) is not None:
            return times[n]
    return None


# ------------------------------------------------------------- reconciliation --

def reconcile(attempts: dict, receipts: dict, commits: dict, janitor: list) -> dict:
    """F-EVENT-GAP: independent records vs the ledger. Missing EVENTS fire."""
    indep = {}
    for wv in receipts:
        indep.setdefault(wv, []).append(
            f"receipt sha256:{receipts[wv]['sha256'][:16]}")
    for wv, rows in commits.items():
        for r in rows:
            if r.get("role") in ("prereg", "ship"):
                indep.setdefault(wv, []).append(f"git {r['repo']}:{r['sha']}")
    for j in janitor:
        wv = j.get("wave")
        if wv and wv in SCOPE:
            indep.setdefault(wv, []).append(
                f"janitor {j.get('ts')}:{j.get('action')}:{j.get('dir')}")

    indep_waves = set(indep) & SCOPE
    ledger_waves = set(attempts)
    missing = sorted(indep_waves - ledger_waves, key=_wave_sort)
    unanchored = []
    for wv, a in attempts.items():
        if not (a.get("ship_commit") or a.get("receipt") or
                a.get("prereg_commit")):
            unanchored.append(a["attempt_id"])
    return {
        "falsifier": "F-EVENT-GAP",
        "prereg": "tools/science_funnel/validation/workflow_telemetry_20260921/"
                  "PREREGISTER_F_EVENT_GAP.md",
        "independent_records": {k: sorted(set(v)) for k, v in
                                sorted(indep.items(), key=lambda kv: _wave_sort(kv[0]))},
        "ledger_attempts": sorted((a["attempt_id"] for a in attempts.values()),
                                  key=lambda x: _wave_sort(x.split("-", 1)[1])),
        "missing_from_ledger": missing,
        "unanchored_attempts": unanchored,
        "verdict": "FIRES" if (missing or unanchored) else "PASS",
    }


# ------------------------------------------------------------------ events --

def build_events(attempts: dict, artifacts: dict, spath: dict) -> list:
    """One Event per phase the attempt is EVIDENCE of having entered."""
    events = []
    timed_set = {str(x) for x in C.TIMED_WAVES}
    for wv in sorted(attempts, key=_wave_sort):
        a = attempts[wv]
        aid = a["attempt_id"]
        art = artifacts.get(wv, {}).get("files", {})
        timed = wv in timed_set and bool(art)
        sp = spath.get(wv, {}) if timed else {}
        prereg = a["prereg_commit"]
        ship = a["ship_commit"]
        anchors_base = {
            "prereg_commit": prereg["sha"] if prereg else None,
            "ship_commit": ship["sha"] if ship else None,
            "receipt_sha256": (a["receipt"] or {}).get("sha256"),
            "receipt_file": (a["receipt"] or {}).get("path"),
        }
        if timed and sp.get("phases_seconds"):
            ph = sp["phases_seconds"]
            files = artifacts[wv]["files"]
            first_ts = min([v for v in files.values() if v], default=None)
            events.append(Event(
                ts=first_ts, lane=a["lane"], attempt_id=aid,
                parent_manifest=a["parent_manifest_sha"] or "",
                claim_digest=a["claim_digest"], phase="registered",
                active_seconds=ph.get("reproduce"),
                wait_seconds=ph.get("wait_for_lead"),
                resources="parent-bytes reproduction runs before the freeze",
                parent_attempt=a["parent_attempt"],
                child_attempts=a["child_attempts"],
                policy_version=a["policy_version"],
                anchors=anchors_base,
                note=f"claim frozen at prereg commit "
                     f"{prereg['sha'] if prereg else '?'} "
                     f"({prereg['ts'] if prereg else 'ts unknown'}); "
                     f"mine_derive {ph.get('mine_derive')}s precedes the freeze"))
            events.append(Event(
                ts=None, lane=a["lane"], attempt_id=aid,
                parent_manifest=a["parent_manifest_sha"] or "",
                claim_digest=a["claim_digest"], phase="building",
                active_seconds=ph.get("build_run"), wait_seconds=None,
                resources="amended build + candidate run (combined interval; "
                          "compile split unmeasured)",
                parent_attempt=a["parent_attempt"],
                policy_version=a["policy_version"],
                anchors=dict(anchors_base, candidate_stdout=f"w{wv}_stdout.txt"),
                note="build_run combined; the running-phase split is unknown, "
                     "never imputed zero"))
            events.append(Event(
                ts=_epoch_of(files.get(f"w{wv}_stdout.txt")), lane=a["lane"],
                attempt_id=aid,
                parent_manifest=a["parent_manifest_sha"] or "",
                claim_digest=a["claim_digest"], phase="running",
                active_seconds=None, wait_seconds=None,
                resources="run END anchored by candidate stdout mtime",
                parent_attempt=a["parent_attempt"],
                policy_version=a["policy_version"],
                anchors=dict(anchors_base, candidate_stdout=f"w{wv}_stdout.txt"),
                note="duration unmeasurable separately from build; see building"))
            events.append(Event(
                ts=None, lane=a["lane"], attempt_id=aid,
                parent_manifest=a["parent_manifest_sha"] or "",
                claim_digest=a["claim_digest"], phase="verifying",
                active_seconds=ph.get("verify_decide"), wait_seconds=None,
                resources="trace rerun + fence checks + measurement append",
                parent_attempt=a["parent_attempt"],
                policy_version=a["policy_version"],
                anchors=dict(anchors_base,
                             artifact_dir=artifacts[wv]["dir"]),
                note="trace stdout byte-equality + fence + append"))
        else:
            events.append(Event(
                ts=prereg["ts"] if prereg else None,
                lane=a["lane"], attempt_id=aid,
                parent_manifest=a["parent_manifest_sha"] or "",
                claim_digest=a["claim_digest"], phase="registered",
                active_seconds=None, wait_seconds=None,
                resources="historical wave: sub-commit artifacts did not "
                          "survive; timing unknown, never imputed zero",
                parent_attempt=a["parent_attempt"],
                child_attempts=a["child_attempts"],
                policy_version=a["policy_version"],
                anchors=anchors_base, note=""))
        # deciding event: every attempt gets exactly one (terminal record)
        events.append(Event(
            ts=ship["ts"] if ship else None,
            lane=a["lane"], attempt_id=aid,
            parent_manifest=a["parent_manifest_sha"] or "",
            claim_digest=a["claim_digest"], phase="deciding",
            active_seconds=None, wait_seconds=None,
            outcome=a["outcome"],
            resources="ship commit = terminal record",
            parent_attempt=a["parent_attempt"],
            child_attempts=a["child_attempts"],
            policy_version=a["policy_version"],
            anchors=anchors_base, note=a["outcome_note"]))
    return events


def _epoch_of(iso: Optional[str]) -> Optional[str]:
    return iso  # ts field carries the artifact's ISO mtime directly
