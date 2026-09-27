"""implementation.py -- MAT2-P06 release acceptance limits contract (kind=decision).

CONTRACT LAW (frozen in PREREGISTRATION.md before this file existed): every
numeric in the emitted contract is DERIVED (re-measured at run time from
sha256-asserted bytes recovered read-only at pinned git revisions into
./reference) or explicitly OPERATOR_DECISION_REQUESTED (options +
recommendation, source=None).  Zero fabricated numbers.

Structure:
  * carried_limits(): the 15 DERIVED limits of the lead-accepted ONT-P06
    correction (archived board, PR #156 head 2148f8d3, PASS review 43b415fe,
    lead verdict ACCEPTED), re-measured here from the SAME pinned play-repo
    revisions and program-zero-diffed against the accepted proposal copy
    (reference/ont-p06/limits_proposal.json, sha256 asserted).  The unchanged
    first done_when clause is thereby crosswalked, not re-decided.
  * material_first_limits(): the NEW material-first freeze, derived only from
    existing records: the coupled-arm native validation receipt (source repo
    32105f18) for numerical/convergence/energy bars and their applicability
    boundary; the material-first catalog (source repo 59f81d4d, content
    identical to the live catalog) for camera-visible player outcomes,
    checkpoint acceptances and the first_visible_sequence; the pinned walking
    controller (play repo 8cec4a6b) for the native contact-model status; the
    pinned walker validation source (source repo 8707551c) for the friction
    placeholder status.
  * decision requests: the 4 carried requests (still unanswered -- checked in
    the suggestion mailbox 2026-09-27) plus 3 new requests, one per
    material-first numeric that NO record supplies.
  * separate_acceptance_reports(): the reporting split demanded by the third
    done_when clause, derived from the pinned checkpoint graph and
    first_visible_sequence.

Any pin drift, missing identity, disagreeing cross-check or crosswalk diff
refuses loudly (card falsifier).  Repositories are only read via
`git show` / `git cat-file -e`; nothing is written outside this workspace.
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

# Read-only git sources of the pinned bytes; NEVER imported from, NEVER edited.
PLAY = pathlib.Path("E:/ChimeraWork/monkey-play-20260924")
SRC = pathlib.Path("E:/PythonChimera")

# repo tag -> path -> (commit, content sha256).  Existence of every identity is
# re-verified against its repository at import (card falsifier: "any source
# identity (path/commit) that does not exist" refuses).
PINNED = {
    "play": {
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
    },
    "src": {
        "tools/science_funnel/validation/coupled_native_20260917/receipt.json":
            ("32105f18d7340ba14d4764cc1e0d3abb4496f80f",
             "651fe095553f98ec48ffed9315a492cda4d9af226ce51ff6b89e40c2d76bbc50"),
        "tools/monkey_campaign/monkey_completion_map.json":
            ("59f81d4dcb1cf45192bde124c1e35510fb439f1b",
             "8fa2e1409a2da1e3cbe70a84f59f7620a61d3eed12519171190e9c61543cb272"),
        "tools/creature_graph/validation/admit_gait_walker_20260919.py":
            ("8707551c072a847e1d4d85b50202f3e89d048198",
             "3f149765bc9d17b9cd2ead8e323fc258038f4d81b7e862ea6e300c3680f6eef3"),
    },
}

# The accepted ONT-P06 proposal copy (attempt-workspace record, content sha256
# asserted; the legacy workspace itself stays read-only).
CROSSWALK_TARGET = ("ont-p06/limits_proposal.json",
                    "80d567eaecc432552e5605eda625d6942fe533903386faccf789a0f92744140e")

ACC = "tools/science_funnel/first_skill/acceptance.py"
RECEIPT = "tools/science_funnel/validation/coupled_native_20260917/receipt.json"
CATALOG = "tools/monkey_campaign/monkey_completion_map.json"
WALKER = "tools/creature_graph/validation/admit_gait_walker_20260919.py"
GAIT = "ChimeraEngine/engine/gait_controller.hpp"
EARTH = "ChimeraEngine/engine/earth_environment.hpp"
CLEARING = "tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json"
TRUNK = "tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json"
SESSION = "tools/monkey_campaign/product/session_flow.py"
SERVER = "tools/playable_slice/slice_server.py"
WAVE47 = "tools/science_funnel/validation/gait_zero_20260919/receipt_wave47.json"

SCHEMA = "mat2-p06.release_limits.contract.v1"
CRITERIA = "adfd6c0c8aa993c1ed0c5379a5fe790b8949ea4786ccc7865863b23c8b4d9ce8"
SCOPE = "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097"
ARCHIVED_SCOPE = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"


class SourceFailure(RuntimeError):
    """The card falsifier: refuse loudly rather than ship a bad source."""


def _repo(tag):
    return PLAY if tag == "play" else SRC


def _assert_pinned(reference_dir: pathlib.Path) -> None:
    for tag, files in PINNED.items():
        root = _repo(tag)
        for rel, (commit, want) in files.items():
            path = reference_dir / rel
            if not path.is_file():
                raise SourceFailure(f"pinned_source_missing reference/{rel}")
            got = hashlib.sha256(path.read_bytes()).hexdigest()
            if got != want:
                raise SourceFailure(
                    f"PIN DRIFT: reference/{rel} is {got}, pinned {want}")
            proc = subprocess.run(
                ["git", "-c", f"safe.directory={root}", "-C", str(root),
                 "cat-file", "-e", f"{commit}:{rel}", "--"],
                capture_output=True)
            if proc.returncode != 0:
                raise SourceFailure(
                    f"git_identity_missing {commit}:{rel} (card falsifier)")
    rel, want = CROSSWALK_TARGET
    path = reference_dir / rel
    if not path.is_file():
        raise SourceFailure(f"pinned_source_missing reference/{rel}")
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != want:
        raise SourceFailure(f"PIN DRIFT: reference/{rel} is {got}, pinned {want}")


def read_text(reference_dir, rel):
    return (reference_dir / rel).read_text(encoding="utf-8")


def load_json(reference_dir, rel):
    return json.loads(read_text(reference_dir, rel))


def grep_line(reference_dir, rel, needle):
    for i, line in enumerate(read_text(reference_dir, rel).splitlines(), 1):
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


def prov(tag, rel, method, locator):
    commit, sha = PINNED[tag][rel]
    return {"path": rel, "repo": "play-repository" if tag == "play"
            else "source-checkout", "commit": commit, "blob_sha256": sha,
            "method": method, "locator": locator}


def _finish(limits, key="measurement_mode"):
    for limit in limits:
        limit["class"] = "DERIVED"
        limit["measured_now"] = True
        limit[key] = limit["provenance"][0]["method"]
    return limits


# --------------------------------------------------------------------------
# Carried ONT-P06 limits (crosswalk; same probes as the accepted correction)
# --------------------------------------------------------------------------

def _tick_crosscheck(gait_text: str, earth_text: str):
    """Cross-check the tick law between the two pinned engine headers."""
    gait_line = next(
        (l for l in gait_text.splitlines() if 'require(dt>0&&dt<=1/' in l),
        None)
    if gait_line is None:
        raise SourceFailure("source_line_missing gait tick require")
    tick_gait = int(re.search(r"dt<=1/(\d+)\.", gait_line).group(1))
    substeps = int(re.search(r'substeps"\)==(\d+)', gait_line).group(1))
    earth_line = next(
        (l for l in earth_text.splitlines() if 'tick_hz"))==' in l), None)
    if earth_line is None:
        raise SourceFailure("source_line_missing earth tick_hz")
    tick_earth = int(re.search(r'tick_hz"\)\)==(\d+)', earth_line).group(1))
    if tick_gait != tick_earth:
        raise SourceFailure(
            f"tick_pins_disagree gait={tick_gait} earth={tick_earth}")
    return tick_gait, substeps, tick_earth


def carried_limits(reference_dir) -> list:
    _assert_pinned(reference_dir)

    clearing = load_json(reference_dir, CLEARING)
    trunk = load_json(reference_dir, TRUNK)

    product = reference_dir / "tools/monkey_campaign/product"
    sys.path.insert(0, str(reference_dir))
    sys.path.insert(0, str(product))
    for stale in [k for k in sys.modules
                  if k == "tools" or k.startswith("tools.")
                  or k == "session_flow"]:
        del sys.modules[stale]
    import session_flow as sf  # pinned module, hash-asserted above
    bindings = dict(getattr(sf, "DEFAULT_FLOW_BINDINGS"))
    if set(bindings.values()) != {"confirm", "pause", "restart", "exit"}:
        raise SourceFailure(f"unexpected_flow_actions {sorted(bindings.values())}")
    by_action = {action: key for key, action in bindings.items()}
    controls = {"start_resume": by_action["confirm"],
                "pause": by_action["pause"],
                "restart": by_action["restart"],
                "exit": by_action["exit"]}

    tick_gait, substeps, tick_earth = _tick_crosscheck(
        read_text(reference_dir, GAIT), read_text(reference_dir, EARTH))
    gait_no = grep_line(reference_dir, GAIT,
                        'require(dt>0&&dt<=1/')[0]
    earth_no = grep_line(reference_dir, EARTH, 'tick_hz"))==')[0]

    acc_lines = read_text(reference_dir, ACC).splitlines()
    cap_no = next(i for i, l in enumerate(acc_lines, 1)
                  if l.strip().startswith("EPISODE_CAP_TICKS"))
    window_no = next(i for i, l in enumerate(acc_lines, 1)
                     if l.strip().startswith("EVAL_WINDOW_TICKS"))
    cap = int(acc_lines[cap_no - 1].split("=")[1].split("#")[0].strip())
    window = int(acc_lines[window_no - 1].split("=")[1].split("#")[0].strip())

    ledgers = re.findall(r"worst moving ledger ([0-9.]+) J",
                         read_text(reference_dir, WAVE47))
    if not ledgers or len(set(ledgers)) != 1:
        raise SourceFailure(f"ledger_occurrences_inconsistent {ledgers[:5]}")
    worst = float(ledgers[0])

    vy_no, vy_line = grep_line(reference_dir, SERVER, "SETTLE_VY")
    settle_vy = float(re.search(r"SETTLE_VY\s*=\s*([0-9.]+)", vy_line).group(1))
    sink_no, sink_line = grep_line(reference_dir, SERVER, "SETTLE_SINK_M =")
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
    poll_no, poll_line = grep_line(reference_dir, SERVER, "every 100 ms")
    poll_ms = int(re.search(r"every (\d+) ms", poll_line).group(1))

    half = clearing["boundary"]["physical"]["half_width_m"]
    envelope = clearing["spawn"]["body_radius_envelope_m"]
    trunk_bound = trunk["geometry"]["radius_m"]
    blocking = round(trunk_bound + envelope, 3)

    limits = [
        {"id": "terrain-envelope-half-width-m", "value": half, "unit": "m",
         "source": f"clearing_declaration.json@{short(PINNED['play'][CLEARING][0])} boundary.physical.half_width_m",
         "provenance": [prov("play", CLEARING, "json-field-read",
                             "boundary.physical.half_width_m")]},
        {"id": "spawn-position-m", "value": clearing["spawn"]["position_m"],
         "unit": "m",
         "source": f"clearing_declaration.json@{short(PINNED['play'][CLEARING][0])} spawn.position_m",
         "provenance": [prov("play", CLEARING, "json-field-read",
                             "spawn.position_m")]},
        {"id": "spawn-required-clearance-m",
         "value": clearing["spawn"]["required_clearance_m"], "unit": "m",
         "source": f"clearing_declaration.json@{short(PINNED['play'][CLEARING][0])} spawn.required_clearance_m",
         "provenance": [prov("play", CLEARING, "json-field-read",
                             "spawn.required_clearance_m")]},
        {"id": "body-envelope-radius-m", "value": envelope, "unit": "m",
         "source": f"clearing_declaration.json@{short(PINNED['play'][CLEARING][0])} spawn.body_radius_envelope_m",
         "provenance": [prov("play", CLEARING, "json-field-read",
                             "spawn.body_radius_envelope_m")]},
        {"id": "scene-seed", "value": clearing["seed"], "unit": "dimensionless",
         "source": f"clearing_declaration.json@{short(PINNED['play'][CLEARING][0])} seed",
         "provenance": [prov("play", CLEARING, "json-field-read",
                             "seed")]},
        {"id": "trunk-base-centre-m", "value": trunk["site"]["base_centre_m"],
         "unit": "m",
         "source": f"trunk_declaration.json@{short(PINNED['play'][TRUNK][0])} site.base_centre_m",
         "provenance": [prov("play", TRUNK, "json-field-read",
                             "site.base_centre_m")]},
        {"id": "trunk-blocking-radius-m", "value": blocking, "unit": "m",
         "source": f"trunk_declaration.json@{short(PINNED['play'][TRUNK][0])} geometry.radius_m ({trunk_bound}) + clearing_declaration.json@{short(PINNED['play'][CLEARING][0])} spawn.body_radius_envelope_m ({envelope}), rounded 3 dp (F07 blocking derivation)",
         "provenance": [
             prov("play", TRUNK, "json-field-read + arithmetic",
                  f"geometry.radius_m = {trunk_bound} (F07 trunk bound)"),
             prov("play", CLEARING,
                  "json-field-read + arithmetic",
                  f"spawn.body_radius_envelope_m = {envelope}")]},
        {"id": "controls-bindings", "value": controls, "unit": "keys",
         "source": f"session_flow.py@{short(PINNED['play'][SESSION][0])} DEFAULT_FLOW_BINDINGS imported from the pinned bytes (frozen X02 surface)",
         "provenance": [prov("play", SESSION,
                             "module-import-attribute",
                             "DEFAULT_FLOW_BINDINGS inverted key->action")]},
        {"id": "simulation-tick-hz", "value": tick_gait, "unit": "Hz",
         "source": f"gait_controller.hpp@{short(PINNED['play'][GAIT][0])}:{gait_no} require(dt<=1/{tick_gait}.)+substeps=={substeps}; corroborated earth_environment.hpp@{short(PINNED['play'][EARTH][0])}:{earth_no} tick_hz=={tick_earth}",
         "provenance": [
             prov("play", GAIT, "regex-parse",
                  f"line {gait_no}: dt<=1/{tick_gait}. and substeps=={substeps}"),
             prov("play", EARTH, "regex-parse (cross-check)",
                  f"line {earth_no}: tick_hz=={tick_earth}")]},
        {"id": "walking-episode-cap-ticks", "value": cap, "unit": "ticks",
         "source": f"{ACC}@{short(PINNED['play'][ACC][0])}:{cap_no} EPISODE_CAP_TICKS",
         "provenance": [prov("play", ACC, "literal-parse",
                             f"line {cap_no}: EPISODE_CAP_TICKS = {cap}")]},
        {"id": "walking-eval-window-ticks", "value": window, "unit": "ticks",
         "source": f"{ACC}@{short(PINNED['play'][ACC][0])}:{window_no} EVAL_WINDOW_TICKS",
         "provenance": [prov("play", ACC, "literal-parse",
                             f"line {window_no}: EVAL_WINDOW_TICKS = {window}")]},
        {"id": "walking-worst-ledger-j", "value": worst, "unit": "J",
         "source": f"receipt_wave47.json@{short(PINNED['play'][WAVE47][0])} 'worst moving ledger {worst} J' ({len(ledgers)} consistent occurrences; W03 bar, R5/D-W03 chain); UNRESOLVED: CoT denominator lineage mismatch (D-W04: 13824.5 vs 10.038 kg) — absolute CoT limits cannot freeze until the registration lands",
         "provenance": [prov("play", WAVE47, "regex-parse",
                             f"'worst moving ledger {worst} J' x{len(ledgers)}")]},
        {"id": "stability-settle-sink-m", "value": sink_recorded, "unit": "m",
         "source": f"slice_server.py@{short(PINNED['play'][SERVER][0])}:{sink_no} SETTLE_SINK_M recorded bar {sink_recorded} m; the line expression evaluates to {round(sink_expr_val, 7)} m (rounds to the recorded bar at the line's 4-dp display; the 13824.5 kg lineage stays under the D-W04 caveat)",
         "provenance": [prov("play", SERVER,
                             "recorded-bar-parse + arithmetic cross-check",
                             f"line {sink_no}: comment bar {sink_recorded} m; expression {sink_m.group(1).strip()} = {sink_expr_val} m")]},
        {"id": "stability-settle-vy-ms", "value": settle_vy, "unit": "m/s",
         "source": f"slice_server.py@{short(PINNED['play'][SERVER][0])}:{vy_no} SETTLE_VY",
         "provenance": [prov("play", SERVER, "literal-parse",
                             f"line {vy_no}: SETTLE_VY = {settle_vy}")]},
        {"id": "ui-poll-cadence-ms", "value": poll_ms, "unit": "ms",
         "source": f"slice_server.py@{short(PINNED['play'][SERVER][0])}:{poll_no} (the page's own poll loop)",
         "provenance": [prov("play", SERVER, "regex-parse",
                             f"line {poll_no}: 'every {poll_ms} ms'")]},
    ]
    return _finish(limits)


# --------------------------------------------------------------------------
# New material-first limits (derived from source-checkout pinned records)
# --------------------------------------------------------------------------

def material_first_limits(reference_dir) -> list:
    receipt = load_json(reference_dir, RECEIPT)
    limits_text = receipt["limits"]
    if not isinstance(limits_text, list) or len(limits_text) < 4:
        raise SourceFailure("coupled_receipt_limits_shape")

    residual_bound = None
    order_text = None
    for text in limits_text:
        m = re.search(r"below\s+([0-9.eE+-]+)\s*J", text)
        if m and residual_bound is None:
            residual_bound = float(m.group(1))
        m = re.search(r"approach\s+(\w+)\s+order", text)
        if m and order_text is None:
            order_text = m.group(1)
    if residual_bound is None or order_text is None:
        raise SourceFailure("coupled_receipt_limit_text_not_found")
    if residual_bound != 1e-5:
        # preregistered prediction 2 names this exact bound; anything else in
        # the pinned record is a shape surprise and refuses.
        raise SourceFailure(f"unexpected_residual_bound {residual_bound}")

    metrics = receipt["metrics"]
    needed = ("worst_native_reference_absolute_error",
              "worst_ten_second_energy_residual_J",
              "free_trajectory_refinement_ratio")
    for key in needed:
        if key not in metrics:
            raise SourceFailure(f"coupled_receipt_metric_missing {key}")

    walker_lines = read_text(reference_dir, WALKER).splitlines()
    fric_no = next((i for i, l in enumerate(walker_lines, 1)
                    if l.strip().startswith("CONTACT_FRICTION =")), None)
    if fric_no is None:
        raise SourceFailure("contact_friction_literal_missing")
    fric_line = walker_lines[fric_no - 1]
    fric_val = float(re.search(r"CONTACT_FRICTION\s*=\s*([0-9.]+)",
                               fric_line).group(1))
    fric_cited = "#" in fric_line  # no source citation on the pinned line
    use_no, _ = grep_line(reference_dir, WALKER, '"contact_friction"')

    gait_no, gait_line = grep_line(reference_dir, GAIT, "plane_model_y_=0")
    n_heightfield = len(re.findall(r"heightfield|height_field",
                                   read_text(reference_dir, GAIT)))

    limits = [
        {"id": "coupled-energy-residual-bound-j", "value": residual_bound,
         "unit": "J",
         "source": "coupled_native receipt@32105f18 limits[] text 'Worst energy/store residual must remain below 1e-5 J on preregistered ten-second trials' (first record-backed numerical/energy bar for material-coupled trials)",
         "applies_to": "M07 coupled-step energy accounting; M03/M04 membrane trials",
         "provenance": [prov("src", RECEIPT, "limits-text-parse",
                             f"limits[]: 'below {residual_bound:g} J' (regex on record text)")]},
        {"id": "coupled-refinement-required-order", "value": order_text,
         "unit": "text (free-trajectory convergence requirement)",
         "source": "coupled_native receipt@32105f18 limits[] text 'Free trajectory refinement must approach fourth order; impact trajectories require their own event tolerances'",
         "applies_to": "M07 timestep-refinement duty; impact cases need their own event tolerances",
         "provenance": [prov("src", RECEIPT, "limits-text-parse",
                             f"limits[]: 'approach {order_text} order'")]},
        {"id": "coupled-applicability-boundary",
         "value": [t for t in limits_text if "qualified only" in t
                   or "not separately metered" in t],
         "unit": "verbatim record text (applicability boundary, not a numeric)",
         "source": "coupled_native receipt@32105f18 limits[] verbatim: RK4 explicit reference qualified only for that source model, admitted gains/caps and timestep; no unconditional stability claim; per-substep work metering; discrete ideal-work ledger",
         "applies_to": "these bars are NOT universal physics; M07/M08 must declare their own timestep/convergence against them",
         "provenance": [prov("src", RECEIPT, "limits-text-parse",
                             "limits[] entries 1 and 4 (verbatim)")]},
        {"id": "coupled-worst-measured-energy-residual-j",
         "value": metrics["worst_ten_second_energy_residual_J"], "unit": "J",
         "supporting_observation": True,
         "source": "coupled_native receipt@32105f18 metrics.worst_ten_second_energy_residual_J (measured; demonstrates the 1e-5 J bound was met in the pinned validation)",
         "provenance": [prov("src", RECEIPT, "json-field-read",
                             "metrics.worst_ten_second_energy_residual_J")]},
        {"id": "coupled-refinement-measured-ratio",
         "value": metrics["free_trajectory_refinement_ratio"],
         "unit": "dimensionless (fourth order implies ~2^4=16)",
         "supporting_observation": True,
         "source": "coupled_native receipt@32105f18 metrics.free_trajectory_refinement_ratio (measured)",
         "provenance": [prov("src", RECEIPT, "json-field-read",
                             "metrics.free_trajectory_refinement_ratio")]},
        {"id": "coupled-native-reference-worst-abs-error",
         "value": metrics["worst_native_reference_absolute_error"],
         "unit": "model units (worst native/reference scalar gap, measured)",
         "supporting_observation": True,
         "source": "coupled_native receipt@32105f18 metrics.worst_native_reference_absolute_error (measured over 714 scalar comparisons)",
         "provenance": [prov("src", RECEIPT, "json-field-read",
                             "metrics.worst_native_reference_absolute_error")]},
        {"id": "walker-contact-friction-placeholder", "value": fric_val,
         "unit": "friction coefficient — UNEVIDENCED PLACEHOLDER, explicitly NOT an acceptance limit",
         "source": f"admit_gait_walker_20260919.py@8707551c:{fric_no} bare literal CONTACT_FRICTION = {fric_val} with {'no' if not fric_cited else 'a'} citation comment on the line; consumed at line {use_no}; any friction envelope must be measured before F05/G04 acceptance trials",
         "applies_to": "F05 surface-friction envelope; G04 grip contact",
         "provenance": [prov("src", WALKER, "literal-parse + no-citation-check",
                             f"line {fric_no}: CONTACT_FRICTION = {fric_val} (bare literal); line {use_no}: consumption")]},
        {"id": "native-walking-contact-model",
         "value": f"single ground plane scalar plane_model_y_ (declaration line {gait_no}); heightfield/height_field occurrences in the pinned bytes: {n_heightfield}",
         "unit": "status (structural observation, not a numeric)",
         "source": f"gait_controller.hpp@8cec4a6b:{gait_no} 'plane_world_y_=0,plane_model_y_=0' — the pinned walking engine has a single-plane contact model; no heightfield/trunk contact service exists at this revision",
         "applies_to": "F02/F03/F04/M06 own the material/contact path; no numeric contact tolerance may be claimed met by this pinned engine",
         "provenance": [prov("play", GAIT, "regex-parse + negative-search",
                             f"line {gait_no}: plane_model_y_=0 declaration; 'heightfield|height_field' count = {n_heightfield}")]},
    ]
    return _finish(limits)


# --------------------------------------------------------------------------
# Camera-visible player outcomes (pinned catalog text)
# --------------------------------------------------------------------------

def camera_visible_outcomes(reference_dir) -> dict:
    catalog = load_json(reference_dir, CATALOG)
    contract = catalog["ontology_contract"]
    profiles = {p["id"]: p for p in contract["visual_profiles"]}
    checkpoints = {c["id"]: c for c in contract["checkpoints"]}
    tasks = {t["id"]: t for t in catalog["tasks"]}
    for needed in ("walking", "material"):
        if needed not in profiles:
            raise SourceFailure(f"catalog_profile_missing {needed}")
    for needed in ("MAT-WOODS", "V07"):
        if needed not in checkpoints:
            raise SourceFailure(f"catalog_checkpoint_missing {needed}")
    for needed in ("W10", "F06", "F08", "U07", "K04", "K05", "K06", "K07",
                   "K08", "S05"):
        if needed not in tasks:
            raise SourceFailure(f"catalog_task_missing {needed}")
    sequence = catalog.get("first_visible_sequence")
    if not isinstance(sequence, list) or not sequence:
        raise SourceFailure("catalog_first_visible_sequence_missing")

    def pprov(locator):
        return prov("src", CATALOG, "catalog-text-parse",
                    locator)

    walking = profiles["walking"]
    material = profiles["material"]
    outcomes = {
        "law": "player-visible outcomes are frozen from the pinned catalog text; no outcome is invented here",
        "walking_replay_scenario": {
            "value": walking["scenario"],
            "provenance": [pprov("ontology_contract.visual_profiles[id=walking].scenario")]},
        "walking_falsifier_outcomes": {
            "value": walking["falsifier"],
            "provenance": [pprov("ontology_contract.visual_profiles[id=walking].falsifier")]},
        "material_falsifier_outcomes": {
            "value": material["falsifier"],
            "provenance": [pprov("ontology_contract.visual_profiles[id=material].falsifier")]},
        "clean_view_required": {
            "value": {"walking": walking["clean_view_required"],
                      "material": material["clean_view_required"]},
            "provenance": [pprov("ontology_contract.visual_profiles[walking|material].clean_view_required")]},
        "camera_required_fields": {
            "value": walking["camera_required_fields"],
            "provenance": [pprov("ontology_contract.visual_profiles[id=walking].camera_required_fields")]},
        "walking_through_woods_acceptance": {
            "value": checkpoints["MAT-WOODS"]["acceptance"],
            "provenance": [pprov("ontology_contract.checkpoints[id=MAT-WOODS].acceptance")]},
        "climb_loop_acceptance": {
            "value": checkpoints["V07"]["acceptance"],
            "provenance": [pprov("ontology_contract.checkpoints[id=V07].acceptance")]},
        "feature_completion_clause": {
            "value": tasks["S05"]["done_when"],
            "provenance": [pprov("tasks[id=S05].done_when")]},
        "demonstration_order_first_visible_sequence": {
            "value": sequence,
            "provenance": [pprov("first_visible_sequence")]},
        "controls_surface": {
            "value": "carried limit controls-bindings (frozen X02 session-flow surface)",
            "provenance": [prov("play", SESSION,
                                "cross-reference", "carried_limits:controls-bindings")]},
    }
    for entry in outcomes.values():
        if isinstance(entry, dict) and "value" in entry:
            entry["class"] = "DERIVED"
    return outcomes


# --------------------------------------------------------------------------
# Separate acceptance reports (third done_when clause)
# --------------------------------------------------------------------------

def separate_acceptance_reports(reference_dir) -> dict:
    catalog = load_json(reference_dir, CATALOG)
    contract = catalog["ontology_contract"]
    checkpoints = {c["id"]: c for c in contract["checkpoints"]}
    sequence = catalog["first_visible_sequence"]
    woods = checkpoints["MAT-WOODS"]
    v07 = checkpoints["V07"]

    def pprov(locator):
        return prov("src", CATALOG, "catalog-text-parse",
                    locator)

    return {
        "rule": "Report first walking-through-woods acceptance separately from later full climbing completion; neither report implies or completes the other (done_when clause 3).",
        "report_A_walking_through_woods": {
            "reported": "FIRST (the first product milestone)",
            "checkpoints": ["V03", "V04", "MAT-WOODS"],
            "contributor_tasks": sorted(set(woods["task_ids"]) |
                                        {"W10", "F06", "F08", "U07"}),
            "gate_limits": ["terrain-envelope-half-width-m", "spawn-position-m",
                            "spawn-required-clearance-m",
                            "body-envelope-radius-m", "scene-seed",
                            "trunk-base-centre-m", "trunk-blocking-radius-m",
                            "controls-bindings", "simulation-tick-hz",
                            "walking-episode-cap-ticks",
                            "walking-eval-window-ticks",
                            "walking-worst-ledger-j",
                            "stability-settle-sink-m",
                            "stability-settle-vy-ms", "ui-poll-cadence-ms"],
            "camera_outcomes": ["walking_replay_scenario",
                                "walking_falsifier_outcomes",
                                "walking_through_woods_acceptance",
                                "clean_view_required",
                                "camera_required_fields"],
            "evidence_chain": "MAT-WOODS requires MAT-REUSE; first_visible_sequence places W10/F06 before K08/S05",
            "provenance": [pprov("ontology_contract.checkpoints[id=MAT-WOODS]"),
                           pprov("first_visible_sequence")]},
        "report_B_full_climbing_completion": {
            "reported": "SEPARATELY, only after report_A exists",
            "checkpoints": ["V07"],
            "contributor_tasks": sorted(set(v07["task_ids"])),
            "feature_acceptance_task": "S05",
            "camera_outcomes": ["climb_loop_acceptance",
                                "feature_completion_clause",
                                "camera_required_fields"],
            "evidence_chain": "V07 requires V04+V06; first_visible_sequence places K08/S05 after W10/F06; S05 remains the operator-accepted feature completion",
            "provenance": [pprov("ontology_contract.checkpoints[id=V07]"),
                           pprov("tasks[id=S05].done_when"),
                           pprov("first_visible_sequence")]},
        "class": "DERIVED",
    }


# --------------------------------------------------------------------------
# Decision requests: 4 carried unchanged + 3 new material-first requests
# --------------------------------------------------------------------------

def carried_decision_requests(reference_dir) -> list:
    rel, _ = CROSSWALK_TARGET
    proposal = load_json(reference_dir, rel)
    requests = proposal.get("operator_decision_requests")
    if not isinstance(requests, list) or len(requests) != 4:
        raise SourceFailure("crosswalk_decision_requests_shape")
    return json.loads(json.dumps(requests))  # deep copy


NEW_DECISION_REQUESTS = [
    {"id": "contact-geometric-tolerance",
     "class": "OPERATOR_DECISION_REQUESTED",
     "question": "Numeric bounds for F02 render/collision agreement and F04 tunnelling/interpenetration/ghost-support on the material contact path (no record supplies one; the pinned walking engine is single-plane only)",
     "options": ["penetration bound 0.0025 m = 1% of the frozen body-envelope-radius 0.25 m, render/collision agreement at the same scale",
                 "penetration bound 1e-4 m (solver-tolerance-anchored)",
                 "operator value"],
     "recommendation": "envelope-derived 0.0025 m, frozen only after M06/F02 demonstrate the contact path's achievable tolerance; the single-plane pinned engine must never be presented as having met any contact tolerance",
     "source": None},
    {"id": "surface-friction-envelope",
     "class": "OPERATOR_DECISION_REQUESTED",
     "question": "Surface-friction envelope for the clearing/trunk (the only recorded value is the bare placeholder 0.6 at admit_gait_walker_20260919.py@8707551c:60, uncited)",
     "options": ["measure the bark-on-appendage coefficient before F05/G04 trials",
                 "adopt placeholder 0.6 explicitly labeled UNEVIDENCED and excluded from acceptance evidence",
                 "operator value"],
     "recommendation": "measure before any acceptance trial; the placeholder must not enter acceptance evidence",
     "source": None},
    {"id": "material-pass-performance-budget",
     "class": "OPERATOR_DECISION_REQUESTED",
     "question": "Frame-time/VRAM ceiling for the coupled GPU material passes before M08/M12/R03 performance claims (records carry tick-rate and the coupled-arm receipt's runtime, not a frame/VRAM budget)",
     "options": ["tie to carried frame-time-budget-ms once measured; record the VRAM ceiling at the first M08 reserved-window profile",
                 "33.3 ms (30 fps) degradation floor",
                 "operator value"],
     "recommendation": "tie to the carried frame-time decision and record VRAM at the first profile; no performance pass/fail claim before that measurement exists (C27: contention invalidates benchmark claims)",
     "source": None},
]


# --------------------------------------------------------------------------
# Contract assembly
# --------------------------------------------------------------------------

def _crosswalk_zero_diff(reference_dir, carried, requests) -> dict:
    rel, _ = CROSSWALK_TARGET
    proposal = load_json(reference_dir, rel)
    old = {l["id"]: l["value"] for l in proposal["derived_limits"]}
    new = {l["id"]: l["value"] for l in carried}
    value_diffs = [k for k in sorted(set(old) | set(new))
                   if old.get(k, _MISSING) != new.get(k, _MISSING)]
    old_req = {r["id"]: r for r in proposal["operator_decision_requests"]}
    new_req = {r["id"]: r for r in requests}
    req_diffs = [k for k in sorted(set(old_req) | set(new_req))
                 if old_req.get(k, _MISSING) != new_req.get(k, _MISSING)]
    return {"target": f"reference/{rel}",
            "target_sha256": CROSSWALK_TARGET[1],
            "value_diffs": value_diffs,
            "decision_request_diffs": req_diffs,
            "values_checked": len(old),
            "requests_checked": len(old_req)}


class _Missing:
    def __repr__(self):
        return "<missing>"


_MISSING = _Missing()


def build_contract(reference_dir: pathlib.Path) -> dict:
    carried = carried_limits(reference_dir)
    requests = carried_decision_requests(reference_dir)
    zero_diff = _crosswalk_zero_diff(reference_dir, carried, requests)
    if zero_diff["value_diffs"] or zero_diff["decision_request_diffs"]:
        raise SourceFailure(f"CROSSWALK DIFF {zero_diff}")
    material = material_first_limits(reference_dir)
    outcomes = camera_visible_outcomes(reference_dir)
    reports = separate_acceptance_reports(reference_dir)
    all_requests = requests + json.loads(json.dumps(NEW_DECISION_REQUESTS))

    modes = {}
    for limit in carried + material:
        modes[limit["measurement_mode"]] = \
            modes.get(limit["measurement_mode"], 0) + 1

    # Reconciliation identity check: the live on-disk catalog must equal the
    # pinned catalog bytes (the catalog is otherwise untracked in the repo).
    live_catalog = SRC / CATALOG
    if live_catalog.is_file():
        live_sha = hashlib.sha256(live_catalog.read_bytes()).hexdigest()
        pin_sha = PINNED["src"][CATALOG][1]
        catalog_live_matches_pin = (live_sha == pin_sha)
    else:
        catalog_live_matches_pin = None

    return {
        "schema": SCHEMA,
        "card": "MAT2-P06",
        "planning_id": "P06",
        "kind": "decision",
        "law": "every numeric is DERIVED (re-measured at run time from "
               "sha256-asserted bytes recovered read-only at pinned git "
               "revisions into reference/) or explicitly "
               "OPERATOR_DECISION_REQUESTED; zero fabricated numbers; "
               "operator-decision items remain open requests, not decisions",
        "identities": {
            "criteria_sha256": CRITERIA,
            "criteria_source": "worker_start.py assignment "
                               "6ecad9d537c346c4a31e9ce7b48a1fc7",
            "active_scope_sha256": SCOPE,
            "archived_scope_sha256": ARCHIVED_SCOPE,
            "dependency_P01": {
                "state": "DONE",
                "pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/192",
                "head_sha": "e61838b9fb058b19631717fc5d15be8c31681954",
                "merge_commit_sha": "97993cbefaf00380803d8e67652ac51d50c37d06",
                "merged_at": "2026-09-27T08:47:35Z",
                "source": "kanban_cli.py status board record, read 2026-09-27"},
            "archived_lineage_ONT-P06": {
                "state": "DONE (archived scope, HISTORICAL_SCOPE_READ_ONLY)",
                "pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/156",
                "head_sha": "2148f8d3c722cd41ec05297775538fd949a226e0",
                "criteria_sha256":
                    "7bea081e57fa35a83fcedfc7dfc8243c63d027448b0d9b104eab179dd96f1333",
                "independent_review": "PASS 43b415fe0db04e72b9f5e047754839c4",
                "lead_verdict": "ACCEPTED"},
            "repositories": {
                "play_repository": str(PLAY),
                "play_worktree_head_observed": "8d16d3c1 (read-only)",
                "source_checkout": str(SRC),
                "source_worktree_head_observed": "f394d11f (read-only)"},
            "catalog_live_matches_pin": catalog_live_matches_pin,
        },
        "done_when_map": [
            {"clause": "Supported hardware, controls, terrain/trunk envelope, "
                       "session duration, latency, frame-time and stability "
                       "limits are frozen before acceptance trials",
             "evidence": "crosswalk of the lead-accepted ONT-P06 proposal: "
                         "carried_limits (15 DERIVED, re-measured) + 4 carried "
                         "OPERATOR_DECISION_REQUESTED; byte-identical clause "
                         "text in both cards' done_when",
             "sections": ["carried_limits", "operator_decision_requests(0-3)",
                          "crosswalk"]},
            {"clause": "Freeze numerical/convergence/energy/contact/performance "
                       "limits and camera-visible player outcomes before "
                       "experiments",
             "evidence": "material_first_limits (record-backed bars + status "
                         "freezes), camera_visible_player_outcomes (pinned "
                         "catalog text), new decision requests for the three "
                         "numerics no record supplies",
             "sections": ["material_first_limits",
                          "camera_visible_player_outcomes",
                          "operator_decision_requests(4-6)"]},
            {"clause": "Report first walking-through-woods acceptance "
                       "separately from later full climbing completion",
             "evidence": "report structure derived from the pinned checkpoint "
                         "graph and first_visible_sequence",
             "sections": ["separate_acceptance_reports"]},
        ],
        "crosswalk": zero_diff,
        "carried_limits": carried,
        "material_first_limits": material,
        "camera_visible_player_outcomes": outcomes,
        "separate_acceptance_reports": reports,
        "operator_decision_requests": all_requests,
        "unresolved_acceptance_numerics": [
            "cot-denominator-lineage (D-W04: acceptance CoT uses 13824.5 kg "
            "membrane inventory vs 10.038 kg training body; absolute CoT "
            "limits blocked until the lead-authorized registration lands; "
            "mailbox Q-34439597b1774332972da4d8b4ec6b2a NEEDS_EVIDENCE, "
            "supersession question Q-136fedaa492e4375a5b6f7589345e881 OPEN "
            "as of 2026-09-27)",
            "surface-friction envelope: only an uncited placeholder (0.6) "
            "exists in records",
            "numeric contact tolerances (render/collision agreement, "
            "penetration/tunnelling): absent from all records; the pinned "
            "walking engine is single-plane only",
            "frame-time/VRAM budgets for the coupled GPU material passes: "
            "absent from records until the first M08/R03 reserved-window "
            "profile",
            "W03 walking anchors (302 ticks, 30.970714 J) are baseline "
            "evidence only until rerun against the selected material "
            "representation (catalog W03 material-first note)",
        ],
        "carried_count": len(carried),
        "material_first_derived_count": len(material),
        "decision_requested_count": len(all_requests),
        "measurement_modes": modes,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="release_limits.json")
    ap.add_argument("--reference-dir", default=str(HERE / "reference"))
    args = ap.parse_args(argv)
    contract = build_contract(pathlib.Path(args.reference_dir))
    pathlib.Path(args.out).write_text(
        json.dumps(contract, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps({k: contract[k] for k in
                      ("carried_count", "material_first_derived_count",
                       "decision_requested_count", "measurement_modes",
                       "crosswalk")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
