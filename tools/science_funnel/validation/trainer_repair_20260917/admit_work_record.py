"""Rule-0 admission for work.data.trainer_spine_repair_20260917.

Idempotent: reconciles project_program.json to the exact declared state below
(same declared state -> byte-identical program), then rebuilds the compiled
store through tools/creature_graph/build_graph.py. Run with the project python
from anywhere; paths are resolved from this file.

  python tools/science_funnel/validation/trainer_repair_20260917/admit_work_record.py
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
PROGRAM = os.path.join(ROOT, 'tools', 'creature_graph', 'data', 'authored',
                       'project_program.json')

ADMITTED_UTC = '2026-09-18T00:54:11.600644+00:00'
# The bounded DOMAIN SWEEP ran against the repaired spine on this lane and
# survived (12 completed, 8 refused with designed causes, 2 refused_env,
# 0 internal/refuting classes); see sweep_receipt.json in this directory.
WORK_STATUS = 'verified'
FALSIFIER_STATUS = 'tested_survived'

SOURCE = {
    "id": "source.operator.trainer_spine_repair_20260917",
    "kind": "source",
    "name": "Operator dispatches the trainer-spine repair lane",
    "status": "extracted",
    "physical": {
        "text": "Repair the trainer spine so the batch gate can run ANY domain: "
                "the auditor's short-history shape, the beat_generator audit path, "
                "pref_selftest's seed(rng) protocol alignment, and a two-domain "
                "batch exercise. The admitted falsifier is a bounded domain sweep "
                "over every module in Chimera/core/trainables at pop=6, gens=5.",
        "selection": "Operator lane brief (branch lane/trainer-repair-20260917 from "
                     "14c56162c856); tools/science_funnel/batch/train.py had recorded "
                     "the auditor short-history KeyError and the pref_selftest "
                     "protocol drift for exactly this repair.",
    },
}

WORK = {
    "id": "work.data.trainer_spine_repair_20260917",
    "kind": "work",
    "name": "Repair the trainer spine so the batch gate runs any domain",
    "status": WORK_STATUS,
    "priority": "P0",
    "dependencies": ["work.data.graph_store_split"],
    "evidence": [],
    "falsifier": {
        "statement": "A spine repair that still lets a trainable domain die on an "
                     "internal spine error is not a repair: the bounded domain sweep "
                     "must show every module in Chimera/core/trainables completing "
                     "train_and_audit(pop=6, gens=5) or refusing with its own honest "
                     "cause — never an internal spine TypeError/KeyError.",
        "status": FALSIFIER_STATUS,
    },
    "physical": {
        "statement": "The trainer spine (core/train_loop.py train_and_audit + "
                     "core/model_auditor.py audit_run) returns an audit dict of ONE "
                     "shape at every history length, refuses domains that violate the "
                     "documented seed(rng) / mutate(genome, rng) / measure(genome) "
                     "protocol with a named refusal instead of an internal TypeError, "
                     "and the batch exercise runs the canonical domain plus a second "
                     "domain end to end.",
        "prediction": "After the repair: (1) train_and_audit completes at every "
                      "history length >= 1 with the same audit keys; (2) beat_generator "
                      "and pref_selftest complete at pop=6, gens=3 and pop=6, gens=5 "
                      "(both crashed before — KeyError 'stuck_metrics' on the "
                      "short-history audit dict, TypeError on seed(rng) respectively); "
                      "(3) the bounded sweep over every Chimera/core/trainables module "
                      "at pop=6, gens=5 shows zero internal spine errors: each module "
                      "completes or refuses with its own named cause (protocol "
                      "violation, missing scan, missing optional GPU dependency).",
        "contract": {
            "base_commit": "14c56162c85641877bbbfc3d9bba02bbd5e59ec6",
            "law": [
                "audit_run returns the full shape (generations, total_metrics, "
                "stuck_metrics, stuck_rate, recommendation, stuck) at EVERY history "
                "length; below 5 generations it makes NO stuck-metric claim: "
                "stuck_metrics 0, stuck [], and a recommendation that says no audit "
                "was possible — never 'All metrics moving', which would be a claim.",
                "train_and_audit probes the domain protocol (seed accepts the "
                "protocol's rng, mutate accepts (genome, rng), measure accepts "
                "(genome)) before training and raises DomainRefusal naming the "
                "domain and the violated protocol; it never leaks a raw signature "
                "TypeError.",
                "pref_selftest.seed aligns to the documented protocol by accepting "
                "the rng and ignoring it: the fixture is a deterministic fixed point "
                "by design, so its genome is unchanged.",
                "The batch exercise runs EXERCISE_DOMAINS = (erisaid_mirror, "
                "pref_selftest) — the documented canonical domain plus the domain "
                "this repair unblocked — and records both runs in the receipt dict.",
            ],
            "falsifiers": [
                "DOMAIN SWEEP (bounded, per-module timeout), run by "
                "tools/science_funnel/sweep_trainer_spine.py: every module in "
                "Chimera/core/trainables completes train_and_audit(pop=6, gens=5) "
                "or refuses with its own honest cause — a Refusal/DomainRefusal, a "
                "designed domain-frame refusal (e.g. arrangement's missing-scan "
                "FileNotFoundError), or a missing optional dependency at import "
                "(GPU domains without warp/newton). Any internal spine "
                "TypeError/KeyError, any refused outcome whose exception type is "
                "not a designed refusal, or a timeout/crash without a classified "
                "cause REFUTES the repair.",
            ],
            "owned_files": [
                "Chimera/core/model_auditor.py",
                "Chimera/core/train_loop.py",
                "Chimera/core/trainables/pref_selftest.py",
                "tools/science_funnel/batch/train.py",
                "tools/science_funnel/sweep_trainer_spine.py",
                "tools/science_funnel/tests/test_trainer_spine.py",
                "tools/science_funnel/validation/trainer_repair_20260917/",
            ],
            "not_implemented": [
                "the seven bare-seed() domains (creature, director, brain, economy, "
                "attunement, memorial, weather) keep their signatures and are "
                "refused honestly by the spine; aligning each is per-domain work",
                "no ML quality claim: the exercise proves wiring, not policy",
                "GPU domains stay unexercised where warp/newton are absent",
            ],
        },
    },
    "project_spec": {
        "schema": "chimera.project_spec.v1",
        "admission": "active_specification",
        "category": "work",
        "origin_id": SOURCE["id"],
        "admitted_utc": ADMITTED_UTC,
        "authorization": "Operator's trainer-repair lane brief "
                         "(lane/trainer-repair-20260917 from 14c56162)",
        "authority_scope": "Isolated repository prototype on the assigned lane; "
                           "no production qualification.",
    },
}

RELATION = {
    "src": WORK["id"],
    "rel": "derived_from",
    "dst": SOURCE["id"],
    "note": "Operator-directed trainer-spine repair lane",
}


def main() -> int:
    with open(PROGRAM, encoding='utf-8-sig') as stream:
        program = json.load(stream)
    changed = []

    for obj in (SOURCE, WORK):
        known = {o['id']: o for o in program['objects']}
        if known.get(obj['id']) != obj:
            if obj['id'] in known:
                program['objects'] = [obj if o['id'] == obj['id'] else o
                                      for o in program['objects']]
                changed.append(obj['id'] + ' (updated to declared state)')
            else:
                program['objects'].append(obj)
                changed.append(obj['id'] + ' (admitted)')

    edges = {(e['src'], e['rel'], e['dst'], e.get('note', ''))
             for e in program['relations']}
    key = (RELATION['src'], RELATION['rel'], RELATION['dst'], RELATION['note'])
    if key not in edges:
        program['relations'].append(dict(RELATION))
        changed.append('relation ' + RELATION['src'] + ' -' + RELATION['rel']
                       + '-> ' + RELATION['dst'])

    if changed:
        raw = (json.dumps(program, ensure_ascii=False, indent=1) + '\n').encode()
        with open(PROGRAM, 'wb') as stream:
            stream.write(raw)
    else:
        print('program already at declared state (idempotent no-op)')

    sys.path.insert(0, os.path.join(ROOT, 'tools', 'creature_graph'))
    import build_graph
    graph = build_graph.build()
    errs = graph.check()
    if errs:
        raise SystemExit('store check FAILED:\n  ' + '\n  '.join(errs))
    path = graph.save()
    print('admission:', '; '.join(changed) if changed else 'no-op')
    print('rebuilt', os.path.normpath(path),
          'objects', len(graph.objects), 'relations', len(graph.relations),
          'graph_hash', graph.graph_hash()[:16])
    print('declared_utc', datetime.now(timezone.utc).isoformat())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
