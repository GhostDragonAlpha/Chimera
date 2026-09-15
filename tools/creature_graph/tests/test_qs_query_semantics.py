"""QUERY SEMANTICS -- queries.next_work vs gaps.q_next_ready_task are DIFFERENT
queries that a planner can easily confuse, plus the empty-risk-query trap.

WHAT EACH ACTUALLY ANSWERS (recorded from source, base a12bfbcc):

queries.next_work(g, experience_id="experience.press_and_response")   (queries.py:48-92)
  SUBJECT : unfinished STRUCTURES ONLY -- it EXCLUDES kind in (type, evidence,
            experience, capability, work, region) at :58.  A work item can
            NEVER be the answer.
  CLOSURE : transitive enables_player_experience INTO the experience; objects
            skipping a passing falsifier are dropped (:62-63).
  READINESS: requires_implementation targets all >= geometry_built (:32-40).
  RANKING : inventory priority (PRIORITY_RANK P0/P1/P2), then build_rank, then
            order_hint, then id -- authored plan metadata, not authored_priority.

gaps.q_next_ready_task(g, experience_id="experience.local_withdrawal") (gaps.py:224-242)
  SUBJECT : kind == "work" ONLY (:230) -- a structure can NEVER be the answer.
  CLOSURE : enables_player_experience closure PLUS the dependents closure over
            requires_implementation (gaps.q_blockers_for :141-184), so work that
            requires an enabler shows up blocked; kind evidence/type skipped.
  READINESS: same blockers_of threshold, but "verified" short-circuits (:172).
  RANKING : the AUTHORED authored_priority field (None sorts last), then id.

CONSEQUENCE: on the same store the two functions return different objects with
different ranking fields, under different default experiences -- "what's next"
is two questions.  Both also drop the excluded kind silently, so each answer
looks complete while covering only its own subject.

THE EMPTY-RISK TRAP (gaps.py:191-217 + store.py:176-189): q_evidence_at_risk
returns [] BOTH when the target was checked and nothing captured it AND when
the store contains NO evidence records at all (and stale_evidence returns []
for any record whose capture is empty -- defect D3).  In gaps.run_all_six the
q5 payload renders at_risk=[] as a normal answer, so "no risk found" is
indistinguishable from "nothing could ever be found": an empty risk query
passes despite absent evidence.

EXPECTED-HONEST (recorded semantics, not a defect claim): the two functions'
answers must be read as different queries; the empty list from a risk query
must be disambiguated (e.g. evidence_records_considered: N).

This module REPRODUCES both behaviors on one fixture store so the semantics
are executable, not prose.
"""

import json

import harness
import gaps
import queries


def _planning_store():
    return harness.min_store(
        objects=[
            # the experience both queries target (different defaults)
            {"id": "experience.press_and_response", "kind": "experience",
             "name": "press and response", "status": "specified", "priority": "P0"},
            {"id": "experience.local_withdrawal", "kind": "experience",
             "name": "local withdrawal", "status": "specified", "priority": "P0"},
            # a STRUCTURE that is ready and ranks first for next_work
            {"id": "inst.comp.shin_l", "kind": "volume",
             "name": "left shin compartment", "classification": "type.A1",
             "status": "specified", "priority": "P0", "build_rank": 2,
             "spatial": None, "geometry": {"is_placeholder": True},
             "physical": {"region_a": "region.shin_l", "law": "P = -(V-V0)/(k*V0)"},
             "falsifier": {"statement": "sealed iff conserved", "status": "untested"},
             "dependencies": [],
             "enables": ["experience.press_and_response"]},
            # a blocked structure (its prerequisite is not built)
            {"id": "inst.comp.thigh_l", "kind": "volume",
             "name": "left thigh compartment", "classification": "type.A1",
             "status": "specified", "priority": "P0", "build_rank": 1,
             "spatial": None, "geometry": {"is_placeholder": True},
             "physical": {"region_a": "region.thigh_l", "law": "P = -(V-V0)/(k*V0)"},
             "falsifier": {"statement": "sealed iff conserved", "status": "untested"},
             "dependencies": ["cap.partition"],
             "enables": ["experience.press_and_response"]},
            {"id": "cap.partition", "kind": "capability",
             "name": "the partition capability (not built)",
             "status": "specified", "priority": "P1"},
            # a WORK item: ready, authored_priority 1 -- the q_next_ready_task answer
            {"id": "work.partition_leg_l", "kind": "work",
             "name": "partition the left leg", "status": "specified",
             "priority": "P0", "authored_priority": 1,
             "dependencies": [],
             "enables": ["experience.local_withdrawal",
                         "experience.press_and_response"],
             "falsifier": {"statement": "leg partition not proven until every "
                                        "bone segment is sealed",
                           "status": "untested"}},
        ],
        relations=[
            # enables edges are authored via the `enables` mirror
        ],
    )


def run():
    g = _planning_store()
    g.sync_dependencies()  # authored dependencies/enables -> relations (store API)

    # -- the two "what's next" queries on the SAME store
    nw = queries.next_work(g)                                   # default: press_and_response
    nw_ids = [item["id"] for item in nw["actionable"]]

    nrt = gaps.q_next_ready_task(g)                             # default: local_withdrawal
    nrt_next = (nrt.get("next") or {}).get("id")
    nrt_ready = [e["id"] for e in nrt.get("ready", [])]

    semantics = {
        "next_work": {
            "module": "queries.py:48-92",
            "default_experience": "experience.press_and_response",
            "answers_with": "STRUCTURES only (kind work EXCLUDED at :58)",
            "ranking": "PRIORITY_RANK, build_rank, order_hint, id",
            "actionable": nw_ids,
            "work_items_in_answer": [i for i in nw_ids if i.startswith("work.")],
        },
        "q_next_ready_task": {
            "module": "gaps.py:224-242",
            "default_experience": "experience.local_withdrawal",
            "answers_with": "WORK items only (kind==work filter at :230)",
            "ranking": "authored_priority (None last), id",
            "next": nrt_next,
            "ready": nrt_ready,
            "structures_in_answer": [i for i in nrt_ready if not i.startswith("work.")],
        },
    }

    # the divergences this module asserts as RECORDED SEMANTICS
    diverges = (
        nrt_next == "work.partition_leg_l"
        and nw_ids == ["inst.comp.shin_l"]             # structure wins next_work
        and all(not i.startswith("work.") for i in nw_ids)
        and all(i.startswith("work.") for i in nrt_ready)
    )

    # -- the empty-risk trap, two flavors:
    # (a) a store with NO evidence records at all: q_evidence_at_risk == [] --
    #     "no risk found" is indistinguishable from "nothing could be checked"
    at_risk = gaps.q_evidence_at_risk(g, "work.partition_leg_l")
    n_evidence = len(g.evidence_records())
    empty_risk_trap = (at_risk == [] and n_evidence == 0)
    # (b) an evidence record EXISTS and the risk query even NAMES it -- but its
    #     capture is empty, so the staleness machinery it promises is inert:
    #     after a real physics-relevant change to the measured object it still
    #     never stales
    g2 = _planning_store()
    g2.sync_dependencies()
    g2.add({"id": "ev.hollow", "kind": "evidence", "name": "hollow record",
            "status": "geometry_built", "priority": None,
            "validation": "passing", "deps": ["work.partition_leg_l"],
            "captured": {}, "captured_utc": "2026-09-15T13:47:00Z"})
    at_risk_hollow = gaps.q_evidence_at_risk(g2, "work.partition_leg_l")
    hollow_stales_before = g2.stale_evidence("ev.hollow")
    g2.get("work.partition_leg_l")["physical"] = {"plan": "the plan changed"}  # PHYSICS_FIELDS member
    hollow_stales_after = g2.stale_evidence("ev.hollow")
    hollow_flipped = g2.refresh_validation()
    hollow_inert = (
        at_risk_hollow != []                       # risk query NAMES the record
        and hollow_stales_before == []
        and hollow_stales_after == []              # ...but staleness is blind
        and hollow_flipped == []
        and g2.get("ev.hollow")["validation"] == "passing"
    )

    semantics["empty_risk_query"] = {
        "flavor_a_zero_evidence_records": {
            "q_evidence_at_risk": at_risk,
            "evidence_records_in_store": n_evidence,
            "empty_despite_absent_evidence": empty_risk_trap,
        },
        "flavor_b_hollow_capture": {
            "q_evidence_at_risk_names_it": at_risk_hollow,
            "stale_evidence_before_change": hollow_stales_before,
            "stale_evidence_after_change": hollow_stales_after,
            "refresh_flipped": hollow_flipped,
            "validation_after": g2.get("ev.hollow")["validation"],
            "protection_promised_but_inert": hollow_inert,
        },
    }

    reproduced = diverges and empty_risk_trap and hollow_inert
    # this module RECORDS semantics: "REPRODUCED" means every documented
    # divergence and trap above was observed exactly as described
    return harness.verdict(
        defect="QS",
        title="QUERY SEMANTICS RECORD (not a defect claim): next_work vs "
              "q_next_ready_task answer different questions; empty risk query "
              "passes despite absent evidence",
        expected_honest="both behaviors are the queries' DOCUMENTED shape here -- "
                        "recorded so planners cannot conflate them: different "
                        "subjects, different defaults, different rankings; an "
                        "empty risk result must be disambiguated from 'no "
                        "evidence exists'",
        observed="next_work -> ['inst.comp.shin_l'] (structure, PRIORITY_RANK "
                 "order); q_next_ready_task -> work.partition_leg_l "
                 "(work item, authored_priority order); q_evidence_at_risk == [] "
                 "with zero evidence records (reads as safe); with an "
                 "empty-capture record the same query NAMES it while "
                 "stale_evidence/refresh stay silent through a real "
                 "physics-relevant change (protection promised but inert)",
        reproduced=reproduced,
        evidence=semantics,
        contract_refs=["queries.py:48-92", "gaps.py:141-184", "gaps.py:191-242",
                       "gaps.py:258-274", "store.py:176-189"],
    )


def test_query_semantics_recorded():
    assert run()["verdict"] == "REPRODUCED"


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
