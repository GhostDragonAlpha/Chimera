#!/usr/bin/env python3
"""THE OBS-POPULATE MINE -- F1 SEPARATION re-run (lane/obs-populate-20260920;
preregistered in record.md BEFORE the delivery build and this run).

Two legs over ONE fresh walk trace (F2 anchors the bytes; this mine parses):

  CONTROL leg -- the interface-freeze mine's own pipeline VERBATIM (their
  parse_run + build + the frozen-table normalization + their projection loop
  with the caller-owned pad prev_state + their frozen alias clauses): must
  reproduce their pinned census (21 aliased pairs, 13 context-only, 277
  distinct observations, 13 bit-identical groups / 38 ticks) and the pinned
  per-pair reasons EXACTLY -- the re-run instrument measures the same walk.

  TREATMENT leg -- the SAME records with the body_velocity group DELIVERED
  (body_velocity.deliver_body_velocity: field 21 com_vel_x_heading from the
  trace's own CoM-projection east, first-differenced at 300 Hz): the frozen
  80-field table and reader are UNCHANGED; the delivery is record-side only.
  The search re-runs over the re-projected observations; every one of the 21
  pairs must separate (F1) and no new aliased pair may appear (P3).

Usage: python mine_obs_populate.py <audit_trace_stderr.txt> <out_dir>
Output: mine_obs_populate_out.txt + aliased_pairs_after.json + pair_ledger.json
Exit 0 iff the control census is reproduced AND zero aliased pairs survive
treatment (the F1 verdict); exit 1 on any fired clause (never tuned away).
"""
import hashlib
import json
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
EXPORT = os.path.join(REPO, "tools", "science_funnel", "typeb_export")
IFREEZE = os.path.join(REPO, "tools", "science_funnel", "validation",
                       "policy_interface_freeze_20260920")
sys.path.insert(0, EXPORT)
sys.path.insert(0, IFREEZE)

import observation_schema as oschema  # noqa: E402
import body_velocity as bvel  # noqa: E402
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "mine_aliasing_audit", os.path.join(IFREEZE, "mine_aliasing_audit.py"))
mine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mine)

TRACE_ANCHOR = "c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481"
PINNED = os.path.join(IFREEZE, "aliased_pairs.json")

out_lines = []
def P(*a):
    s = " ".join(str(x) for x in a)
    out_lines.append(s)
    print(s)


def project_all(recs: list[dict], mean: np.ndarray, std: np.ndarray):
    """The interface-freeze projection loop VERBATIM (their caller-owned
    pad prev_state discipline), returning per-tick obs bytes + the dup map."""
    groups = defaultdict(list)
    obs_bytes = {}
    masks_avail = np.zeros(oschema.OBS_DIM, dtype=np.int64)
    prev_state: dict = {}
    for rec in recs:
        obs, mask = oschema.project_trace(rec, mean, std, prev_state)
        ps = dict(prev_state)
        for leg in ("hl", "hr"):
            v = rec.get("pad_gaps") or {}
            if leg in v:
                ps["pad_split_abs_" + leg] = float(v[leg][1])
            else:
                ps.pop("pad_split_abs_" + leg, None)
        prev_state = ps
        b = obs.tobytes()
        obs_bytes[rec["tick"]] = b
        groups[b].append(rec["tick"])
        masks_avail += (mask > 0).astype(np.int64)
    return groups, obs_bytes, masks_avail


def search(groups) -> tuple[list, list]:
    """The interface-freeze search VERBATIM: their frozen clauses + context."""
    dup_groups = {h: ts for h, ts in groups.items() if len(ts) > 1}
    fired, context_only = [], []
    for h, ts in dup_groups.items():
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                a, b = LABELS[ts[i]], LABELS[ts[j]]
                why = mine.alias_reason(a, b)
                ctx = mine.context_reason(a, b)
                if why:
                    fired.append((ts[i], ts[j], why + (("; context: " + ctx) if ctx else "")))
                elif ctx:
                    context_only.append((ts[i], ts[j], ctx))
    return fired, context_only


def main() -> None:
    trace, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    global LABELS
    P("THE OBS-POPULATE MINE -- F1 SEPARATION (preregistered before the delivery build)")
    P("trace:", trace)
    P("=" * 150)
    sha = hashlib.sha256(open(trace, "rb").read()).hexdigest()
    P("trace sha256:", sha, "| anchor:", sha == TRACE_ANCHOR)

    parsed = mine.parse_run(
        trace, stdout_path=os.path.splitext(trace)[0].replace("_stderr", "_stdout") + ".txt")
    recs, LABELS = mine.build(parsed)
    P("ticks parsed:", len(recs), "| refusal:", parsed["refusal"])

    # ---- the frozen normalization (the lane's frozen table = the v2 manifest section)
    table = json.load(open(os.path.join(IFREEZE, "observation_interface_v2.json"),
                           encoding="utf-8"))
    mean = np.zeros(oschema.OBS_DIM, dtype=np.float32)
    std = np.ones(oschema.OBS_DIM, dtype=np.float32)
    for f in table["fields"]:
        mean[f["index"]] = f["normalization"]["mean"]
        std[f["index"]] = f["normalization"]["std"]

    # ================= CONTROL leg (their pipeline verbatim) =================
    groups0, obs0, _m0 = project_all(recs, mean, std)
    fired0, ctx0 = search(groups0)
    dup0 = {h: ts for h, ts in groups0.items() if len(ts) > 1}
    P("-" * 150)
    P("CONTROL (the interface-freeze mine verbatim): %d distinct observations; "
      "%d bit-identical groups covering %d ticks; %d aliased pairs; %d context-only"
      % (len(groups0), len(dup0), sum(len(ts) for ts in dup0.values()),
         len(fired0), len(ctx0)))

    # the pinned artifact (their F1 run) must be reproduced EXACTLY
    pinned = json.load(open(PINNED, encoding="utf-8"))
    pin_pairs = [(p["t1"], p["t2"], p["reason"]) for p in pinned["aliased_pairs"]]
    pin_ctx = [(p["t1"], p["t2"], p["reason"]) for p in pinned["context_only_pairs"]]
    control_ok = (
        pinned["trace_sha256"] == sha
        and list(pinned["refusal"]) == list(parsed["refusal"])
        and pinned["ticks"] == len(recs)
        and pinned["distinct_observations"] == len(groups0)
        and pinned["bitidentical_groups"] == len(dup0)
        and pinned["bitidentical_ticks"] == sum(len(ts) for ts in dup0.values())
        and pin_pairs == fired0
        and pin_ctx == ctx0)
    P("CONTROL vs the pinned aliased_pairs.json (pairs+reasons+census byte-equal):",
      control_ok)

    # ================= TREATMENT leg (the delivery) =================
    series = bvel.com_vel_x_series(parsed["dv"])
    delivered = bvel.deliver_body_velocity(recs, series)
    P("-" * 150)
    P("DELIVERY: body_velocity group declared on %d records; field 21 "
      "com_vel_x_heading delivered on %d/%d ticks (t0 has no predecessor -- "
      "masked, mean fill, per the group_delivery rule)"
      % (len(recs), delivered, len(recs)))

    groups1, obs1, masks1 = project_all(recs, mean, std)
    fired1, ctx1 = search(groups1)
    dup1 = {h: ts for h, ts in groups1.items() if len(ts) > 1}
    P("TREATMENT (delivered): %d distinct observations; %d bit-identical groups "
      "covering %d ticks; %d aliased pairs; %d context-only"
      % (len(groups1), len(dup1), sum(len(ts) for ts in dup1.values()),
         len(fired1), len(ctx1)))

    # ---- the per-pair ledger: every pinned pair, its delivered values, verdict
    i21 = oschema.FIELD_NAMES.index("com_vel_x_heading")
    o21 = {t: np.frombuffer(b, dtype=np.float32)[i21] for t, b in obs1.items()}
    mask_never = [table["fields"][i]["name"] for i in range(oschema.OBS_DIM)
                  if masks1[i] == 0]
    ledger = []
    n_sep = 0
    for t1, t2, reason in fired0:
        separated = obs1[t1] != obs1[t2]
        n_sep += separated
        diff_fields = []
        if separated:
            v1 = np.frombuffer(obs1[t1], dtype=np.float32)
            v2 = np.frombuffer(obs1[t2], dtype=np.float32)
            diff_fields = [table["fields"][k]["name"]
                           for k in np.nonzero(v1 != v2)[0].tolist()]
        body_clause = "body advance" in reason
        pad_clause = "deformation rate" in reason
        touch_clause = "touch pattern" in reason
        ledger.append(dict(
            t1=t1, t2=t2, control_reason=reason,
            clauses=dict(body_advance=body_clause, pad_deformation=pad_clause,
                         touch_pattern=touch_clause),
            delivered=dict(com_vel_x_t1=round(float(series[t1]), 9),
                           com_vel_x_t2=round(float(series[t2]), 9),
                           delta_m_per_s=round(float(series[t2] - series[t1]), 9)),
            separated=bool(separated),
            differing_fields=diff_fields[:6],
            named_deciding_fields=dict(
                body_advance="field 21 com_vel_x_heading (delivered)",
                pad_deformation="NO frozen-vocabulary field carries the per-paw "
                                "min-gap rate (endpoint-signed pad channels ride "
                                "'lohi'; hind-legs-only) -- carried by the "
                                "body-advance clause on this walk; v3 residual",
                touch_pattern="fields 9-14 per-foot slots -- STRUCTURAL on the "
                              "4-paw body (all-or-nothing 6-slot read); this "
                              "pair separates via field 21, its named fields "
                              "stay undetermined")))
    for d in ledger:
        P("  PAIR (%d,%d): separated=%s | delivered %.6f vs %.6f m/s "
          "(delta %.2e) | via %s | clauses: %s"
          % (d["t1"], d["t2"], d["separated"], d["delivered"]["com_vel_x_t1"],
             d["delivered"]["com_vel_x_t2"], d["delivered"]["delta_m_per_s"],
             ",".join(d["differing_fields"][:2]) or "-",
             "+".join(k for k, v in d["clauses"].items() if v)))
    thinest = min(ledger, key=lambda d: abs(d["delivered"]["delta_m_per_s"]))
    P("thinest separation margin: pair (%d,%d) at %.2e m/s"
      % (thinest["t1"], thinest["t2"], abs(thinest["delivered"]["delta_m_per_s"])))
    P("-" * 150)
    P("mask census after delivery: com_vel_x_heading available on %d/%d ticks; "
      "never-available fields now %d (was 54)"
      % (int(masks1[i21]), len(recs), len(mask_never)))

    survivors = [d for d in ledger if not d["separated"]]
    f1_ok = control_ok and len(ledger) == len(fired0) and not survivors and not fired1
    P("F1 SEPARATION VERDICT: %s"
      % ("GREEN -- all %d aliased pairs separate with the delivered field 21; "
         "zero survivors; zero new aliased pairs; the control census is "
         "reproduced exactly." % len(ledger) if f1_ok else
         "FIRED -- survivors=%d new_pairs=%d control_ok=%s (carried verbatim, "
         "never tuned away)" % (len(survivors), len(fired1), control_ok)))

    # ---- artifacts
    art = dict(
        trace_sha256=sha,
        control=dict(distinct_observations=len(groups0),
                     bitidentical_groups=len(dup0),
                     bitidentical_ticks=sum(len(ts) for ts in dup0.values()),
                     aliased_pairs=len(fired0), context_only_pairs=len(ctx0),
                     matches_pinned_census=bool(control_ok)),
        delivery=dict(module="tools/science_funnel/typeb_export/body_velocity.py",
                      mechanism="derived-from-trace (CoM projection east first "
                                "difference x 300 Hz); zero engine bytes; frozen "
                                "reader unchanged; group gate record-side",
                      field="com_vel_x_heading (index 21)",
                      delivered_ticks=delivered, of_ticks=len(recs),
                      declared_side_effect="yaw_rate_prev becomes AVAILABLE at "
                                           "the frozen reader's own declared "
                                           "default (observation_schema._read_field: "
                                           "float(prev.get('yaw_rate', 0.0) or 0.0)) "
                                           "once the body_velocity group is "
                                           "delivered -- the group gate is the "
                                           "only availability lever, there is no "
                                           "per-field opt-out; this lane delivers "
                                           "NO value for it (the reader supplies "
                                           "its own); measured: never-available "
                                           "54 -> 52 (com_vel_x_heading + "
                                           "yaw_rate_prev); carried with cause, "
                                           "the table is untouched (F3)",
                      not_delivered=["com_vel_y_heading (derivable -- scope "
                                     "decision, declared)", "com_vel_z (not "
                                     "determined: planar projection)",
                                     "yaw_rate (not determined here)"],
                      structural_residual="per-foot slots 9-20: all-or-nothing "
                                          "6-slot read vs four paws"),
        aliased_pairs_after=[dict(t1=t1, t2=t2, reason=why) for t1, t2, why in fired1],
        context_only_pairs_after=[dict(t1=t1, t2=t2, reason=why) for t1, t2, why in ctx1],
        pair_ledger=ledger,
        mask_never_available_after=mask_never,
        verdict_f1="GREEN" if f1_ok else "FIRED",
        prereg_bars=pinned["prereg_bars"],
    )
    with open(os.path.join(out_dir, "aliased_pairs_after.json"), "w", encoding="utf-8") as f:
        json.dump(art, f, indent=1)
    with open(os.path.join(out_dir, "pair_ledger.json"), "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=1)
    with open(os.path.join(out_dir, "mine_obs_populate_out.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")
    P("artifacts written to", out_dir)
    P("Trailer Agent: obspop")
    sys.exit(0 if f1_ok else 1)


if __name__ == "__main__":
    main()
