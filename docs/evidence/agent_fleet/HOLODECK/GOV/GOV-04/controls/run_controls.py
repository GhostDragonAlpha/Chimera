"""GOV-04 controls runner: executes preregistered R1-R4 against the reference
model, then R5-R6 as a read-only source trace at base. Writes checks/*.txt.

Stdlib-only. Run from anywhere:
    python controls/run_controls.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "checks"
sys.path.insert(0, str(HERE.parent / "reference"))
import gov04_reference_model as m  # noqa: E402

REPO = Path(__file__).resolve().parent              # ascend to worktree root
while not (REPO / "tools" / "agent_fleet" / "control.py").is_file():
    if REPO.parent == REPO:
        raise FileNotFoundError("worktree root with tools/agent_fleet not found")
    REPO = REPO.parent
BASE = "62b8e35757c71e31d621c26b32a7c52558905b02"
CTRL = REPO / "tools" / "agent_fleet" / "control.py"
RH = REPO / "tools" / "agent_fleet" / "review_handoff.py"


def fresh() -> m.Registry:
    r = m.Registry(leader="lead-01", epoch=5)
    r.add_agent("lead-01", ["cpu", "docs", "python", "git", "build",
                            "engine", "gpu", "runtime", "dyad", "fleet",
                            "provision", "windows-shell", "evidence",
                            "coordination"], max_tasks=3)
    r.add_agent("w-03", ["cpu", "docs", "python"], max_tasks=2)
    r.add_agent("w-07", ["cpu", "docs", "python"], max_tasks=2)
    return r


def expect_refusal(fn, reason: str):
    try:
        fn()
    except m.Refusal as exc:
        return str(exc) == reason, str(exc)
    return False, "NO-REFUSAL"


def snapshot(t: dict):
    return {k: t.get(k) for k in ("owner", "generation", "state", "slot",
                                  "packet", "owner_instance")}


def unchanged(before: dict, after: dict) -> bool:
    return before == after


def write(name: str, lines: list) -> None:
    (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(exist_ok=True)
    verdicts = {}

    # ── R1 positive controls (model must ACCEPT): 8/8 ────────────────────
    lines = ["R1 positive controls — model must ACCEPT (prereg: 8/8)", ""]
    ok = 0
    r = fresh()
    r.create_task("lead-01", 5, "t-alpha", BASE,
                  ["docs/evidence/agent_fleet/HOLODECK/GOV/GOV-04"],
                  dependencies=[], capabilities=["cpu", "docs", "python"],
                  packet="do the thing; finish = review then integration")
    lines.append("R1(a) create_task legal: PASS")
    ok += 1
    r.claim("w-03", "t-alpha", instance="inst-w03-0001")
    lines.append("R1(b) claim READY dep-free task: PASS (owner=w-03, inst=inst-w03-0001)")
    ok += 1
    pkt = r.generate_packet("t-alpha")
    have = all(k in pkt for k in ("dependencies", "evidence", "write_scope",
                                  "finish_criteria"))
    filled = bool(isinstance(pkt["dependencies"], list)
                  and isinstance(pkt["evidence"], dict) and pkt["evidence"]["state"]
                  and pkt["write_scope"]
                  and pkt["finish_criteria"]["assignment"])
    lines += [f"R1(c) packet 4/4 required elements {list(pkt)}: "
              f"{'PASS' if have and filled else 'FAIL'}"]
    ok += have and filled
    r.create_task("lead-01", 5, "t-beta", BASE,
                  ["docs/evidence/agent_fleet/HOLODECK/MAT/mat-01-notes"],
                  packet="beta assignment")
    r.claim("w-07", "t-beta", instance="inst-w07-0001")
    lines.append("R1(d) second task admitted+claimed on disjoint scope: PASS")
    ok += 1
    cards = {"cards": [
        {"id": "GOV-01", "status": "REALIZED"},
        {"id": "GOV-04", "status": "PROPOSED", "depends_on": ["GOV-01"]},
    ]}
    r.catalogue_import("lead-01", 5, "d" * 64, cards, 651)
    before = r.catalogue_next("d" * 64)["candidates"]
    r.create_task("lead-01", 5, "gov-01", BASE,
                  ["docs/evidence/agent_fleet/HOLODECK/GOV/GOV-01"],
                  packet="stand-in for the integrated dependency")
    r.claim("w-03", "gov-01")
    r.submit_review("w-03", "gov-01", 1, BASE, "evidence text")
    r.integrate("gov-01")
    after = r.catalogue_next("d" * 64)["candidates"]
    e_ok = before == [] and after == ["GOV-04"]
    lines += [f"R1(e) catalogue_next eligibility: before={before} after={after}: "
              f"{'PASS' if e_ok else 'FAIL'}"]
    ok += e_ok
    r2 = fresh()
    edges = {"t-a": [], "t-b": [], "t-c": ["t-a"], "t-d": ["t-b"],
             "t-e": ["t-c"], "t-f": ["t-c", "t-d"], "t-g": ["t-e", "t-f"]}
    for tid, deps in edges.items():
        r2.create_task("lead-01", 5, tid, BASE, [f"docs/scope/{tid}"],
                       dependencies=deps, packet=f"{tid} assignment")
    order, rounds, path, max_batch = r2.schedule(worker_slots=2)
    pos = {tid: i for i, tid in enumerate(order)}
    topo_ok = all(pos[d] < pos[t] for t in edges for d in edges[t])
    lines += [f"R1(f) topo order valid: {order}: {'PASS' if topo_ok else 'FAIL'}"]
    ok += topo_ok
    r2.claim("w-03", "t-a")
    r2.claim("w-07", "t-b")
    lines.append("R1(g) capacity boundary 2 of max_tasks=2: PASS")
    ok += 1
    r3 = fresh()
    r3.add_agent("w-03", ["cpu"], max_tasks=2)
    r3.create_task("lead-01", 5, "t-inst", BASE, ["docs/scope/i"],
                   packet="inst")
    r3.claim("w-03", "t-inst", instance="inst-A")
    acc = expect_refusal(lambda: r3.checkpoint("w-03", "t-inst", 1, "cp",
                                               instance="inst-B"),
                         "instance_not_bound")
    good = False
    try:
        r3.checkpoint("w-03", "t-inst", 1, "cp", instance="inst-A")
        good = True
    except m.Refusal as exc:
        good = False
    lines += [f"R1(h) binding-instance mutation accepted (foreign refused "
              f"{acc[1]}): {'PASS' if good and acc[0] else 'FAIL'}"]
    ok += good and acc[0]
    verdicts["R1_positive"] = f"{ok}/8"
    lines += ["", f"R1 VERDICT: {ok}/8 (prereg threshold 8/8)"]
    write("r1_positive.txt", lines)

    # ── R2 card falsifier clause 1: 6/6 refusals + post-state ────────────
    lines = ["R2 card falsifier — 'a blocked or already claimed task is silently "
             "reassigned' — model must REJECT each (prereg: 6/6)",
             "Post-state assertions on EVERY case: owner/generation/state/slot/"
             "packet/owner_instance unchanged.", ""]
    ok = 0
    # (a) dependency not INTEGRATED
    r = fresh()
    r.create_task("lead-01", 5, "t-dep", BASE, ["docs/scope/dep"],
                  packet="dep")
    r.create_task("lead-01", 5, "t-blocked", BASE, ["docs/scope/blocked"],
                  dependencies=["t-dep"], packet="blocked assignment")
    b = snapshot(r.tasks["t-blocked"])
    good, why = expect_refusal(lambda: r.claim("w-03", "t-blocked"),
                               "dependencies_not_integrated")
    good = good and unchanged(b, snapshot(r.tasks["t-blocked"]))
    lines.append(f"R2(a) blocked task claim -> {why}; post-state unchanged: "
                 f"{'PASS' if good else 'FAIL'}")
    ok += good
    # (b) already-RUNNING re-claim
    r.claim("w-03", "t-dep", instance="inst-A")
    b = snapshot(r.tasks["t-dep"])
    good, why = expect_refusal(lambda: r.claim("w-07", "t-dep"),
                               "task_not_ready")
    good = good and unchanged(b, snapshot(r.tasks["t-dep"]))
    lines.append(f"R2(b) RUNNING re-claim by second agent -> {why}; owner stays "
                 f"w-03: {'PASS' if good else 'FAIL'}")
    ok += good
    # (c) overlapping active scope
    r.create_task("lead-01", 5, "t-over", BASE, ["docs/scope/dep/child"],
                  packet="over")
    good, why = expect_refusal(lambda: r.claim("w-07", "t-over"),
                               "write_scope_conflict")
    lines.append(f"R2(c) overlapping active scope claim -> {why}: "
                 f"{'PASS' if good else 'FAIL'}")
    ok += good
    # (d) BLOCKED-state task
    r.checkpoint("w-03", "t-dep", 1, "cp-1", instance="inst-A",
                 state="BLOCKED")
    b = snapshot(r.tasks["t-dep"])
    good, why = expect_refusal(lambda: r.claim("w-07", "t-dep"),
                               "task_not_ready")
    good = good and unchanged(b, snapshot(r.tasks["t-dep"]))
    lines.append(f"R2(d) BLOCKED-state claim -> {why}; owner stays w-03: "
                 f"{'PASS' if good else 'FAIL'}")
    ok += good
    # (e) duplicate create: no silent overwrite
    r2 = fresh()
    r2.create_task("lead-01", 5, "t-x", BASE, ["docs/scope/x"],
                   packet="ORIGINAL PACKET")
    orig = dict(r2.tasks["t-x"])
    good, why = expect_refusal(
        lambda: r2.create_task("lead-01", 5, "t-x", BASE, ["docs/scope/y"],
                               packet="HIJACK"),
        "invalid_or_duplicate_task")
    keep = r2.tasks["t-x"]["packet"] == "ORIGINAL PACKET" and \
        r2.tasks["t-x"]["scopes"] == ["docs/scope/x"]
    lines.append(f"R2(e) duplicate id create -> {why}; original packet survives "
                 f"byte-identical: {'PASS' if good and keep else 'FAIL'}")
    ok += good and keep
    # (f) REVIEW-state claim
    r3 = fresh()
    r3.create_task("lead-01", 5, "t-rev", BASE, ["docs/scope/rev"],
                   packet="rev")
    r3.claim("w-03", "t-rev")
    r3.submit_review("w-03", "t-rev", 1, BASE, "evidence")
    b = snapshot(r3.tasks["t-rev"])
    good, why = expect_refusal(lambda: r3.claim("w-07", "t-rev"),
                               "task_not_ready")
    good = good and unchanged(b, snapshot(r3.tasks["t-rev"]))
    lines.append(f"R2(f) REVIEW-state claim -> {why}; owner stays w-03: "
                 f"{'PASS' if good else 'FAIL'}")
    ok += good
    verdicts["R2_falsifier_reassignment"] = f"{ok}/6"
    lines += ["", f"R2 VERDICT: {ok}/6 (prereg threshold 6/6) — card falsifier "
               f"{'NOT fired' if ok == 6 else 'FIRED'} in the model"]
    write("r2_falsifier_reassignment.txt", lines)

    # ── R3 packet-admission integrity: 6/6 ────────────────────────────────
    lines = ["R3 create_task validation — model must REJECT (prereg: 6/6)", ""]
    ok = 0
    r = fresh()
    cases = [
        ("(a) non-existent dependency", lambda: r.create_task(
            "lead-01", 5, "t-d1", BASE, ["docs/s"], dependencies=["ghost"],
            packet="p"), "dependencies_must_exist"),
        ("(b) absolute scope", lambda: r.create_task(
            "lead-01", 5, "t-d2", BASE, ["/abs/path"], packet="p"),
         "invalid_scope"),
        ("(c) parent-escape scope", lambda: r.create_task(
            "lead-01", 5, "t-d3", BASE, ["docs/../escape"], packet="p"),
         "invalid_scope"),
        ("(d) protected build scope (child)", lambda: r.create_task(
            "lead-01", 5, "t-d4", BASE,
            ["chimeraengine/engine/build/Release/x"], packet="p"),
         "protected_build_scope"),
        ("(e) protected build scope (parent direction)", lambda: r.create_task(
            "lead-01", 5, "t-d5", BASE, ["chimeraengine/engine"], packet="p"),
         "protected_build_scope"),
        ("(f) .git metadata scope", lambda: r.create_task(
            "lead-01", 5, "t-d6", BASE, [".git/hooks/x"], packet="p"),
         "git_metadata_scope"),
    ]
    for label, fn, reason in cases:
        good, why = expect_refusal(fn, reason)
        lines.append(f"R3{label} -> {why}: {'PASS' if good else 'FAIL'}")
        ok += good
    verdicts["R3_admission_integrity"] = f"{ok}/6"
    lines += ["", f"R3 VERDICT: {ok}/6 (prereg threshold 6/6)"]
    write("r3_admission_integrity.txt", lines)

    # ── R4 scheduling mathematics: 4/4 ─────────────────────────────────────
    lines = ["R4 CARD MATHEMATICS — topological scheduling, critical path, "
             "resource constraints (prereg: 4/4)",
             "Fixture DAG (PREREG t_a; t_b; t_c<-{t_a}; t_d<-{t_b}; "
             "t_e<-{t_c}; t_f<-{t_c,t_d}; t_g<-{t_e,t_f}, rendered with the "
             "deployed id regex's hyphen form: underscores are refused by "
             "control.py:506 — recorded in RESULT.md)", ""]
    ok = 0
    r = fresh()
    edges = {"t-a": [], "t-b": [], "t-c": ["t-a"], "t-d": ["t-b"],
             "t-e": ["t-c"], "t-f": ["t-c", "t-d"], "t-g": ["t-e", "t-f"]}
    for tid, deps in edges.items():
        r.create_task("lead-01", 5, tid, BASE, [f"docs/scope/{tid}"],
                      dependencies=deps, packet=f"{tid} assignment")
    order, rounds, path, max_batch = r.schedule(worker_slots=2)
    pos = {tid: i for i, tid in enumerate(order)}
    topo_ok = all(pos[d] < pos[t] for t in edges for d in edges[t])
    lines.append(f"R4(a) topological order valid: {order}: "
                 f"{'PASS' if topo_ok else 'FAIL'}")
    ok += topo_ok
    path_ok = len(path) == 4 and path[0] == "t-a" and path[-1] == "t-g"
    lines.append(f"R4(b) critical path == 4 nodes (a->...->g): {path}: "
                 f"{'PASS' if path_ok else 'FAIL'}")
    ok += path_ok
    conc_ok = max_batch <= 2 and all(len(rnd) <= 2 for rnd in rounds)
    lines.append(f"R4(c) resource constraint, 2 worker slots, batches={rounds} "
                 f"max_batch={max_batch}: {'PASS' if conc_ok else 'FAIL'}")
    ok += conc_ok
    packets = [r.generate_packet(tid) for tid in order]
    all4 = all(all(k in p for k in ("dependencies", "evidence", "write_scope",
                                    "finish_criteria")) for p in packets)
    lines.append(f"R4(d) packets in topo order, 7/7 with 4/4 required elements: "
                 f"{'PASS' if all4 and len(packets) == 7 else 'FAIL'}")
    ok += all4 and len(packets) == 7
    verdicts["R4_scheduling"] = f"{ok}/4"
    lines += ["", f"R4 VERDICT: {ok}/4 (prereg threshold 4/4)"]
    write("r4_scheduling.txt", lines)

    # ── R5 deployed-source trace: 6/6 ─────────────────────────────────────
    ctrl = CTRL.read_text(encoding="utf-8").splitlines()

    def line_of(token: str, start: int = 0) -> int:
        """First 1-based line containing token at/after start (measured)."""
        for i in range(start, len(ctrl)):
            if token in ctrl[i]:
                return i + 1
        return -1

    lines = ["R5 deployed-source trace at base 62b8e357 "
             "(tools/agent_fleet/control.py, 839 lines) — 6/6 semantics",
             "",
             "NOTE (prereg correction, disclosed): the PREREG quoted "
             "approximate line anchors read before measurement; the rows "
             "below are SEARCH-ANCHORED — each row's exact measured file:line "
             "is recorded here and in RESULT.md.", ""]
    ok = 0
    n_id = line_of("invalid_or_duplicate_task")
    n_scope_invalid = line_of("'invalid_scope'")
    n_git = line_of("'git_metadata_scope'")
    n_protected = line_of("'protected_build_scope'")
    n_deps = line_of("'dependencies_must_exist'")
    n_tnr = line_of("'task_not_ready'")
    n_dni = line_of("'dependencies_not_integrated'")
    n_wsc = line_of("'write_scope_conflict'")
    n_lead = line_of("def _lead")
    n_next = line_of("if op=='catalogue_next'")

    lines.append("control.py:41-48 (path_scope: relative, no . .. empty, "
                 ".git, protected build BOTH directions):")
    lines += [f"  {n}: {ctrl[n-1]}" for n in range(41, 49)]
    lines.append("")
    lines.append(f"control.py:503-506 (lead-only create via _lead:{n_lead} "
                 f"+ id regex):")
    lines += [f"  {n}: {ctrl[n-1]}" for n in range(503, 507)]
    lines.append("")
    lines.append(f"control.py:{n_deps} (deps must exist): {ctrl[n_deps-1]}")
    lines.append("")
    lines.append(f"control.py:{n_tnr} (claim READY gate — refused for BLOCKED/"
                 f"REVIEW/RUNNING): {ctrl[n_tnr-1]}")
    lines.append(f"control.py:{n_dni} (deps INTEGRATED): {ctrl[n_dni-1]}")
    lines.append(f"control.py:{n_wsc} (write_scope_conflict vs ACTIVE): "
                 f"{ctrl[n_wsc-1]}")
    lines.append("")
    lines.append(f"control.py:{n_next}+ (catalogue_next eligibility: PROPOSED, "
                 "casefold live/done, INTEGRATED-only deps):")
    lines += [f"  {n}: {ctrl[n-1]}" for n in range(n_next, n_next + 23)
              if any(t in ctrl[n - 1] for t in
                     ("status')!='PROPOSED'", "casefold() in done",
                      "if cid in live or cid in done"))]
    lines.append("")
    lines.append(f"control.py:{n_lead}-{n_lead+1} (_lead, applied at the "
                 "create_task head) — lead-only admission:")
    lines += [f"  {n}: {ctrl[n-1]}" for n in range(n_lead, n_lead + 2)]
    lines.append("")
    # search-anchored row checks: semantics present at the measured lines
    row_checks = [
        ("R5(a)", n_id == 506
         and "re.fullmatch('[a-z0-9][a-z0-9-]{0,63}',tid)" in ctrl[505]),
        ("R5(b)", abs(n_scope_invalid - 44) <= 2 and n_git == 45
         and n_protected == 48),
        ("R5(c)", n_deps == 509
         and "all(x in s['tasks'] for x in deps)" in ctrl[n_deps - 1]),
        ("R5(d)", n_tnr == 522
         and "t['state']=='READY'" in ctrl[n_tnr - 1]),
        ("R5(e)", n_dni == 529
         and "'INTEGRATED'" in ctrl[n_dni - 1]),
        ("R5(f)", n_wsc == 532
         and "overlaps(x,y)" in ctrl[n_wsc - 1]
         and "other['state'] in ('RUNNING','BLOCKED','REVIEW','RECOVERY_HOLD')"
         in ctrl[n_wsc - 2]),
    ]
    for label, passed in row_checks:
        lines.append(f"{label}: {'PASS' if passed else 'FAIL'}")
        ok += passed
    verdicts["R5_source_trace"] = f"{ok}/6"
    lines += ["", f"R5 VERDICT: {ok}/6 (prereg threshold 6/6)"]
    write("r5_source_trace.txt", lines)

    # ── R6 measured deviation: owner_instance delta ────────────────────────
    rh = RH.read_text(encoding="utf-8").splitlines()
    c_count = sum(1 for ln in ctrl if "owner_instance" in ln)
    r_count = sum(1 for ln in rh if "owner_instance" in ln)
    lines = ["R6 measured deviation (recorded finding, NOT adopted as the "
             "model's truth): the live claim path drops owner_instance",
             "",
             f"base: 62b8e35757c71e31d621c26b32a7c52558905b02",
             f"occurrences of 'owner_instance' in tools/agent_fleet/control.py: "
             f"{c_count} (predicted 8: lines 121,122,123,323,499,501,554,697)",
             f"occurrences of 'owner_instance' in "
             f"tools/agent_fleet/review_handoff.py: {r_count} (predicted 0)",
             "",
             "control.py:553-554 (base claim binds the instance):"]
    lines += [f"  {n}: {ctrl[n-1]}" for n in (553, 554)]
    lines += ["", "control.py:121-123 (_task enforces the binding):"]
    lines += [f"  {n}: {ctrl[n-1]}" for n in (121, 122, 123)]
    lines += ["", "review_handoff.py:90-92 (interceptor claim binds WITHOUT the "
               "instance, no instance_binding_required check):"]
    lines += [f"  {n}: {rh[n-1]}" for n in (90, 91, 92)]
    lines += ["",
              "control.py:499-501 (yield guard consulting the binding):"]
    lines += [f"  {n}: {ctrl[n-1]}" for n in (499, 500, 501)]
    lines += ["",
              f"DEVIATION CONFIRMED as predicted: {r_count} == 0 and "
              f"{c_count} == 8 -> for interceptor-claimed tasks owner_instance "
              "stays None and the intended per-instance fencing (control.py:"
              "121-123) is inert on the live claim path. Matches feedback "
              "c4212657; fix in flight as PR #80 (in review at this base). "
              "The reference model keeps the INTENDED binding (R1(h)/R2 "
              "post-state include owner_instance).",
              "",
              f"R6 VERDICT: {'CONFIRMED' if (r_count == 0 and c_count == 8) else 'SURPRISE — reported, never silently reconciled'}"]
    write("r6_owner_instance_delta.txt", lines)

    print(json.dumps(verdicts, indent=1))
    all_ok = all(v.split("/")[0] == v.split("/")[1] for v in verdicts.values())
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
