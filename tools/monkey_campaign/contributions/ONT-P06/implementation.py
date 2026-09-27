"""implementation.py -- ONT-P06 CORRECTION (lead finding arrival-876e63bf):
release acceptance limits proposal, blob-anchored to pinned git revisions.

CORRECTION LAW: every cited source is recovered READ-ONLY from the play
repository at a pinned commit into ./reference (byte-exact, sha256 asserted
at import -- any drift or missing identity refuses loudly, per the card
falsifier).  Every DERIVED limit is then re-measured AT RUN TIME from those
hash-asserted pinned bytes only; no live-worktree file is read anywhere (the
play worktree at HEAD 8d16d3c1 reorganized the previously cited on-disk
sources away; it is not modified).  The 7 limits the lead found
value-hardcoded in publication-94455595 (controls-bindings,
simulation-tick-hz, walking-worst-ledger-j, trunk-blocking-radius-m,
stability-settle-sink-m, stability-settle-vy-ms, ui-poll-cadence-ms) are now
genuinely read from their pinned sources; the 15 VALUES themselves are
unchanged (lead-verified against the surviving records).  Every taste limit
remains an explicit OPERATOR DECISION REQUEST with options; the output
therefore contains zero un-sourced numerics.

Recovery command (one per pinned file; the play repository is only read):
  git -c safe.directory=E:/ChimeraWork/monkey-play-20260924 \
      -C E:/ChimeraWork/monkey-play-20260924 show <commit>:<path> \
      > reference/<path>
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REFERENCE = HERE / "reference"

# Read-only git source of the pinned bytes; NEVER imported from, NEVER edited.
PLAY = pathlib.Path("E:/ChimeraWork/monkey-play-20260924")

# The pinned lineage: path -> (commit, blob sha256).  Existence of every
# identity is re-verified against the repository at import (the card
# falsifier: "any source identity (path/commit) that does not exist").
PINNED = {
    "tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json":
        ("c9aee37ce9b1602ad4c831fc0804415c4980ccc8",
         "18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1"),
    "tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json":
        ("b4de4de886a9c5bfba4572a2100b2104b178cb2d",
         "94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1"),
    "tools/monkey_campaign/product/session_flow.py":
        ("42f7cdc4ba421cf83ecd2fa0be69e94fb772cd37",
         "30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf"),
    "tools/monkey_campaign/product/input_mapper.py":
        ("8550b634ebd7034bb8873eed41d8bdce4d3843d0",
         "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44"),
    "tools/science_funnel/typeb_export/command_record.py":
        ("e028d6fb55e272da15a31405ba0f92a8c4c0bb0e",
         "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e"),
    "tools/playable_slice/slice_server.py":
        ("0b3b22a5e4763ef69c508a97a6e5cc7e750ab5f8",
         "5accc730541067c48e61122d384e6d2b3e568012908908ae03dcbc06ae6d6eef"),
    "tools/science_funnel/first_skill/acceptance.py":
        ("8294053be688cb9cae5251b16ee927f6338b0b92",
         "1065ab2f23b70ccfa2a34f1ec0f9d04f7591939085d17984cac401935f977fe6"),
    "tools/science_funnel/validation/gait_zero_20260919/receipt_wave47.json":
        ("33e7a444fe7b4c35aa99afe7ef898046877025b4",
         "4480d18b8709d93457784ad23f3662768036498e318c1387c1f6d2ec5b05163d"),
    "ChimeraEngine/engine/gait_controller.hpp":
        ("8cec4a6bf1d6cb74e93cf8b04ec0910634530b81",
         "f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd"),
    "ChimeraEngine/engine/earth_environment.hpp":
        ("ee52a99f44b68cfb6410f07287583aaf068c0083",
         "b4747d349ce201ebadb74227b33725466d16edd860ed421ac590ad789178469a"),
}

ACC = "tools/science_funnel/first_skill/acceptance.py"
SCHEMA = "ont-p06.release_limits.proposal.v1"


class SourceFailure(RuntimeError):
    """The card falsifier: refuse loudly rather than ship a bad source."""


def _assert_pinned() -> None:
    for rel, (commit, want) in PINNED.items():
        path = REFERENCE / rel
        if not path.is_file():
            raise SourceFailure(f"pinned_source_missing reference/{rel}")
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != want:
            raise SourceFailure(
                f"PIN DRIFT: reference/{rel} is {got}, pinned {want}")
        proc = subprocess.run(
            ["git", "-c", f"safe.directory={PLAY}", "-C", str(PLAY),
             "cat-file", "-e", f"{commit}:{rel}", "--"],
            capture_output=True)
        if proc.returncode != 0:
            raise SourceFailure(
                f"git_identity_missing {commit}:{rel} (card falsifier)")


def read_text(rel) -> str:
    return (REFERENCE / rel).read_text(encoding="utf-8")


def load_json(rel):
    return json.loads(read_text(rel))


def grep_line(rel, needle):
    for i, line in enumerate(read_text(rel).splitlines(), 1):
        if needle in line:
            return i, line
    raise SourceFailure(f"source_line_missing {rel} :: {needle!r}")


def safe_arith(expr):
    """Evaluate a pinned-source numeric literal expression (+ - * / only)."""
    tree = ast.parse(expr.strip(), mode="eval")

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.BinOp) and isinstance(
                node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            return left / right
        if isinstance(node, ast.Constant) and isinstance(node.value,
                                                         (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(
                node.op, (ast.USub, ast.UAdd)):
            val = ev(node.operand)
            return -val if isinstance(node.op, ast.USub) else val
        raise SourceFailure(f"unsafe_arithmetic {expr!r}")

    return ev(tree)


def short(sha):
    return sha[:8]


def prov(rel, method, locator):
    commit, sha = PINNED[rel]
    return {"path": rel, "commit": commit, "blob_sha256": sha,
            "method": method, "locator": locator}


def derived_limits() -> list:
    _assert_pinned()

    # 1-5: the F01 clearing declaration, pinned at its authoring commit.
    clearing = load_json("tools/monkey_campaign/data/monkey_clearing/"
                         "clearing_declaration.json")
    # 2/6/7: the F03 trunk declaration, pinned at its authoring commit.
    trunk = load_json("tools/monkey_campaign/data/monkey_trunk/"
                      "trunk_declaration.json")

    # 4: the frozen X02 session flow, imported from the pinned bytes (the
    # prior run's import was dead code; this one does the reading).
    product = REFERENCE / "tools/monkey_campaign/product"
    sys.path.insert(0, str(REFERENCE))
    sys.path.insert(0, str(product))
    for stale in [k for k in sys.modules
                  if k == "tools" or k.startswith("tools.")
                  or k == "session_flow"]:
        del sys.modules[stale]
    import session_flow as sf  # noqa: PLC0415  (pinned module, hash-asserted)
    bindings = dict(getattr(sf, "DEFAULT_FLOW_BINDINGS"))
    if set(bindings.values()) != {"confirm", "pause", "restart", "exit"}:
        raise SourceFailure(f"unexpected_flow_actions {sorted(bindings.values())}")
    by_action = {action: key for key, action in bindings.items()}
    controls = {"start_resume": by_action["confirm"],
                "pause": by_action["pause"],
                "restart": by_action["restart"],
                "exit": by_action["exit"]}

    # 5: the tick law, regex-parsed from the two pinned engine headers (the
    # prior run typed 300; both pins must agree or this refuses).
    gait_rel = "ChimeraEngine/engine/gait_controller.hpp"
    gait_no, gait_line = grep_line(gait_rel, 'require(dt>0&&dt<=1/300.,')
    tick_gait = int(re.search(r"dt<=1/(\d+)\.", gait_line).group(1))
    substeps = int(re.search(r'substeps"\)==(\d+)', gait_line).group(1))
    earth_rel = "ChimeraEngine/engine/earth_environment.hpp"
    earth_no, earth_line = grep_line(earth_rel, 'tick_hz"))==')
    tick_earth = int(re.search(r'tick_hz"\)\)==(\d+)', earth_line).group(1))
    if tick_gait != tick_earth:
        raise SourceFailure(
            f"tick_pins_disagree gait={tick_gait} earth={tick_earth}")

    # 6: the walking acceptance anchors, literal-parsed from the pinned
    # acceptance.py object (the only previously surviving citation).
    acc_lines = read_text(ACC).splitlines()
    cap_no = next(i for i, l in enumerate(acc_lines, 1)
                  if l.strip().startswith("EPISODE_CAP_TICKS"))
    window_no = next(i for i, l in enumerate(acc_lines, 1)
                     if l.strip().startswith("EVAL_WINDOW_TICKS"))
    cap = int(acc_lines[cap_no - 1].split("=")[1].split("#")[0].strip())
    window = int(acc_lines[window_no - 1].split("=")[1].split("#")[0].strip())

    # 7: the W03 worst-ledger bar, regex-parsed from the pinned wave-47
    # receipt (the prior run typed the number; every occurrence must agree).
    wave47_rel = ("tools/science_funnel/validation/gait_zero_20260919/"
                  "receipt_wave47.json")
    ledgers = re.findall(r"worst moving ledger ([0-9.]+) J", read_text(wave47_rel))
    if not ledgers or len(set(ledgers)) != 1:
        raise SourceFailure(f"ledger_occurrences_inconsistent {ledgers[:5]}")
    worst = float(ledgers[0])

    # 8: the slice_server stability and UI cadence constants, parsed from the
    # pinned server bytes (the prior run measured only the line numbers).
    server_rel = "tools/playable_slice/slice_server.py"
    vy_no, vy_line = grep_line(server_rel, "SETTLE_VY")
    settle_vy = float(re.search(r"SETTLE_VY\s*=\s*([0-9.]+)",
                                vy_line).group(1))
    sink_no, sink_line = grep_line(server_rel, "SETTLE_SINK_M =")
    sink_m = re.search(r"SETTLE_SINK_M\s*=\s*([^#]+)#\s*([0-9.]+)\s*m",
                       sink_line)
    if not sink_m:
        raise SourceFailure("settle_sink_recorded_bar_not_found")
    sink_expr_val = safe_arith(sink_m.group(1))
    sink_recorded = float(sink_m.group(2))
    if round(sink_expr_val, 4) != sink_recorded:
        raise SourceFailure(
            f"settle_sink_crosscheck_failed expr={sink_expr_val} "
            f"recorded={sink_recorded}")
    poll_no, poll_line = grep_line(server_rel, "every 100 ms")
    poll_ms = int(re.search(r"every (\d+) ms", poll_line).group(1))

    # Derived values (bit-identical to the lead-verified prior proposal).
    half = clearing["boundary"]["physical"]["half_width_m"]
    envelope = clearing["spawn"]["body_radius_envelope_m"]
    trunk_bound = trunk["geometry"]["radius_m"]
    blocking = round(trunk_bound + envelope, 3)

    limits = [
        {"id": "terrain-envelope-half-width-m", "value": half, "unit": "m",
         "source": f"clearing_declaration.json@{short(PINNED['tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json'][0])} boundary.physical.half_width_m",
         "provenance": [prov("tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json",
                             "json-field-read",
                             "boundary.physical.half_width_m")]},
        {"id": "spawn-position-m", "value": clearing["spawn"]["position_m"],
         "unit": "m",
         "source": f"clearing_declaration.json@{short(PINNED['tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json'][0])} spawn.position_m",
         "provenance": [prov("tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json",
                             "json-field-read", "spawn.position_m")]},
        {"id": "spawn-required-clearance-m",
         "value": clearing["spawn"]["required_clearance_m"], "unit": "m",
         "source": f"clearing_declaration.json@{short(PINNED['tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json'][0])} spawn.required_clearance_m",
         "provenance": [prov("tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json",
                             "json-field-read", "spawn.required_clearance_m")]},
        {"id": "body-envelope-radius-m", "value": envelope, "unit": "m",
         "source": f"clearing_declaration.json@{short(PINNED['tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json'][0])} spawn.body_radius_envelope_m",
         "provenance": [prov("tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json",
                             "json-field-read", "spawn.body_radius_envelope_m")]},
        {"id": "scene-seed", "value": clearing["seed"],
         "unit": "dimensionless",
         "source": f"clearing_declaration.json@{short(PINNED['tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json'][0])} seed",
         "provenance": [prov("tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json",
                             "json-field-read", "seed")]},
        {"id": "trunk-base-centre-m", "value": trunk["site"]["base_centre_m"],
         "unit": "m",
         "source": f"trunk_declaration.json@{short(PINNED['tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json'][0])} site.base_centre_m",
         "provenance": [prov("tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json",
                             "json-field-read", "site.base_centre_m")]},
        {"id": "trunk-blocking-radius-m", "value": blocking, "unit": "m",
         "source": f"trunk_declaration.json@{short(PINNED['tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json'][0])} geometry.radius_m "
                   f"({trunk_bound}) + clearing_declaration.json@"
                   f"{short(PINNED['tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json'][0])} spawn.body_radius_envelope_m ({envelope}), "
                   "rounded 3 dp (F07 blocking derivation)",
         "provenance": [
             prov("tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json",
                  "json-field-read + arithmetic",
                  f"geometry.radius_m = {trunk_bound} (F07 trunk bound)"),
             prov("tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json",
                  "json-field-read + arithmetic",
                  f"spawn.body_radius_envelope_m = {envelope}")]},
        {"id": "controls-bindings", "value": controls, "unit": "keys",
         "source": f"session_flow.py@{short(PINNED['tools/monkey_campaign/product/session_flow.py'][0])} DEFAULT_FLOW_BINDINGS imported from the pinned bytes (frozen X02 surface)",
         "provenance": [prov("tools/monkey_campaign/product/session_flow.py",
                             "module-import-attribute",
                             "DEFAULT_FLOW_BINDINGS inverted key->action")]},
        {"id": "simulation-tick-hz", "value": tick_gait, "unit": "Hz",
         "source": f"gait_controller.hpp@{short(PINNED[gait_rel][0])}:{gait_no} require(dt<=1/{tick_gait}.)+substeps=={substeps}; corroborated earth_environment.hpp@{short(PINNED[earth_rel][0])}:{earth_no} tick_hz=={tick_earth}",
         "provenance": [
             prov(gait_rel, "regex-parse",
                  f"line {gait_no}: dt<=1/{tick_gait}. and substeps=={substeps}"),
             prov(earth_rel, "regex-parse (cross-check)",
                  f"line {earth_no}: tick_hz=={tick_earth}")]},
        {"id": "walking-episode-cap-ticks", "value": cap, "unit": "ticks",
         "source": f"{ACC}@{short(PINNED[ACC][0])}:{cap_no} EPISODE_CAP_TICKS",
         "provenance": [prov(ACC, "literal-parse",
                             f"line {cap_no}: EPISODE_CAP_TICKS = {cap}")]},
        {"id": "walking-eval-window-ticks", "value": window, "unit": "ticks",
         "source": f"{ACC}@{short(PINNED[ACC][0])}:{window_no} EVAL_WINDOW_TICKS",
         "provenance": [prov(ACC, "literal-parse",
                             f"line {window_no}: EVAL_WINDOW_TICKS = {window}")]},
        {"id": "walking-worst-ledger-j", "value": worst, "unit": "J",
         "source": f"receipt_wave47.json@{short(PINNED[wave47_rel][0])} 'worst moving ledger {worst} J' ({len(ledgers)} consistent occurrences; W03 bar, R5/D-W03 chain); UNRESOLVED: CoT denominator lineage mismatch (D-W04: 13824.5 vs 10.038 kg) — absolute CoT limits cannot freeze until the registration lands",
         "provenance": [prov(wave47_rel, "regex-parse",
                             f"'worst moving ledger {worst} J' x{len(ledgers)}")]},
        {"id": "stability-settle-sink-m", "value": sink_recorded, "unit": "m",
         "source": f"slice_server.py@{short(PINNED[server_rel][0])}:{sink_no} SETTLE_SINK_M recorded bar {sink_recorded} m; the line expression evaluates to {round(sink_expr_val, 7)} m (rounds to the recorded bar at the line's 4-dp display; the 13824.5 kg lineage stays under the D-W04 caveat)",
         "provenance": [prov(server_rel, "recorded-bar-parse + arithmetic cross-check",
                             f"line {sink_no}: comment bar {sink_recorded} m; expression {sink_m.group(1).strip()} = {sink_expr_val} m")]},
        {"id": "stability-settle-vy-ms", "value": settle_vy, "unit": "m/s",
         "source": f"slice_server.py@{short(PINNED[server_rel][0])}:{vy_no} SETTLE_VY",
         "provenance": [prov(server_rel, "literal-parse",
                             f"line {vy_no}: SETTLE_VY = {settle_vy}")]},
        {"id": "ui-poll-cadence-ms", "value": poll_ms, "unit": "ms",
         "source": f"slice_server.py@{short(PINNED[server_rel][0])}:{poll_no} (the page's own poll loop)",
         "provenance": [prov(server_rel, "regex-parse",
                             f"line {poll_no}: 'every {poll_ms} ms'")]},
    ]
    for limit in limits:
        limit["class"] = "DERIVED"
        limit["measured_now"] = True
        limit["measurement_mode"] = \
            limit["provenance"][0]["method"]
    return limits


DECISION_REQUESTS = [
    {"id": "session-duration-cap", "class": "OPERATOR_DECISION_REQUESTED",
     "question": "Product session duration limit for acceptance trials",
     "options": ["per-episode (1 s @300 Hz)", "5 min continuous",
                 "30 min continuous", "operator value"],
     "recommendation": "5 min continuous (covers the ground-tree-ground loop "
                       "many times; leaves training-episode semantics "
                       "untouched)", "source": None},
    {"id": "supported-hardware-floor", "class": "OPERATOR_DECISION_REQUESTED",
     "question": "End-user hardware floor phrasing (thin client: browser + "
                 "HTTP to the local engine; rendering is WebGL2 client-side, "
                 "physics server-side)",
     "options": ["any WebGL2 browser", "WebGL2 + dedicated GPU class",
                 "operator list"],
     "recommendation": "any WebGL2 browser (the slice architecture's own "
                       "contract; the server owns physics)",
     "source": None},
    {"id": "network-latency-sla-ms", "class": "OPERATOR_DECISION_REQUESTED",
     "question": "Latency SLA beyond the recorded 100 ms poll cadence",
     "options": ["poll cadence only (100 ms)", "100 ms + 50 ms headroom",
                 "operator value"],
     "recommendation": "poll cadence + 50 ms headroom once a measurement "
                       "protocol exists", "source": None},
    {"id": "frame-time-budget-ms", "class": "OPERATOR_DECISION_REQUESTED",
     "question": "Frame-time budget for acceptance trials (records carry "
                 "ticks/s, not a frame budget)",
     "options": ["16.7 ms (60 fps)", "33.3 ms (30 fps)", "operator value"],
     "recommendation": "16.7 ms with a 30 fps degradation floor, pending the "
                       "viewer lane's own measurement", "source": None},
]


def build_proposal() -> dict:
    limits = derived_limits()
    modes = {}
    for limit in limits:
        modes[limit["measurement_mode"]] = \
            modes.get(limit["measurement_mode"], 0) + 1
    return {
        "schema": SCHEMA,
        "card": "ONT-P06",
        "law": "every numeric is DERIVED (re-measured at run time from "
               "sha256-asserted bytes recovered read-only at pinned git "
               "revisions into reference/; no live-worktree source is read) "
               "or explicitly OPERATOR_DECISION_REQUESTED; zero fabricated "
               "numbers",
        "correction": {
            "supersedes": "publication-94455595e531451db91a9ed701e9fc3f "
                          "(withheld, not published)",
            "lead_finding": "arrival-876e63bf9dbb44a8b10c5b546f783e9b",
            "evidence": "E:/ChimeraWork/monkey-coordination/"
                        "lead-verify-20260926/ONT-P06.json",
            "play_worktree_head": "8d16d3c1",
            "changed": "every cited source re-pointed to a pinned git "
                       "revision recovered into reference/ (sha256 asserted "
                       "at import, identity re-verified against the "
                       "repository); the 7 previously value-hardcoded limits "
                       "(controls-bindings, simulation-tick-hz, "
                       "walking-worst-ledger-j, trunk-blocking-radius-m, "
                       "stability-settle-sink-m, stability-settle-vy-ms, "
                       "ui-poll-cadence-ms) now measured from pinned bytes; "
                       "the 15 VALUES unchanged (lead-verified)",
        },
        "source_lineage": {
            "play_repository": str(PLAY),
            "recovery": "git -c safe.directory=<play> -C <play> show "
                        "<commit>:<path> > reference/<path> (read-only)",
            "pinned_sources": {rel: {"commit": commit, "blob_sha256": sha}
                               for rel, (commit, sha) in PINNED.items()},
        },
        "derived_limits": limits,
        "operator_decision_requests": DECISION_REQUESTS,
        "derived_count": len(limits),
        "decision_requested_count": len(DECISION_REQUESTS),
        "measurement_modes": modes,
        "unresolved_acceptance_numerics": [
            "cot-denominator-lineage (D-W04: acceptance CoT uses 13824.5 kg "
            "membrane inventory vs 10.038 kg training body; absolute CoT "
            "limits blocked until the lead-authorized registration lands; "
            "also the lineage of slice_server.py SETTLE_SINK_M)"],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="limits_proposal.json")
    args = ap.parse_args(argv)
    proposal = build_proposal()
    pathlib.Path(args.out).write_text(
        json.dumps(proposal, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps({k: proposal[k] for k in
                      ("derived_count", "decision_requested_count",
                       "measurement_modes")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
