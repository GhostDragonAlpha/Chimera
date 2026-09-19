"""Admit the macaque gait-controller derivation (RULE 0) into the authored program.

Lane gait-controller-20260918. One lane-owned object: work.creature.gait_controller.
Idempotent AND revision-aware, in the exact shape of
admit_solver_packets_20260918.py: if the stored record equals the current revision
the script is a byte-preserving no-op; if it equals a known PRIOR revision of the
same lane object it is replaced by the current revision; anything else refuses
loudly -- graph policy is never silently overwritten. Formatting is preserved
(1-space indent, CRLF, no BOM).

Run from the checkout root with the pinned interpreter:
    python -B tools/creature_graph/validation/admit_gait_controller_20260918.py
then rebuild the store:
    python -B tools/creature_graph/build_graph.py

The record is banked with falsifier status "untested" (honest): the derivation
doc authors the controller contract, tables, caps, stores and falsifier
envelopes; NOTHING in it has been measured on the engine.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROGRAM = ROOT / "tools" / "creature_graph" / "data" / "authored" / "project_program.json"

GAIT_ID = "work.creature.gait_controller"

DOC = "docs/research/20260918_gait_controller_derivation.md"
DERIVE = "tools/science_funnel/validation/gait_controller_20260918/derive_gait_numbers.py"
DERIVED = "tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json"
ADMITTER = "tools/creature_graph/validation/admit_gait_controller_20260918.py"

GAIT_REVISIONS = [
    # revision 1 (current): the derivation is authored; nothing measured yet.
    {
        "id": GAIT_ID,
        "kind": "work",
        "name": "Macaque gait controller derived from the admitted movement data (AUTHORED)",
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "model.dynamics.coupled_arm",
            "model.anatomy.macaque_arm",
            "work.dynamics.seven_coordinate_lift_packet",
            "work.dynamics.free_root_balance_packet",
            "work.creature.macaque_whole_body_sources",
        ],
        "physical": {
            "statement":
                "The measured bipedal gait of the Japanese macaque -- one duty "
                "factor, four joint-angle waveforms, one ground-reaction force "
                "pair and four joint-moment waveforms over one 0.71 s cycle "
                "(Oku 2021 admitted bytes), with the quadrupedal cercopithecoid "
                "stride statistics (Janisch 2024 admitted bytes) as the "
                "forelimb/substrate analog -- fully determines a phase-driven "
                "walking controller without learning, sweeps or taste: a "
                "contact-reset gait-phase clock (T = 0.71 s, duty 0.68, 21-node "
                "target tables per joint), the qualified mass-normalized PD "
                "servo at f_s = 4.0 Hz derived from a 0.95 amplitude-ratio "
                "criterion at the 1.41 Hz gait fundamental, torque caps at 1.25x "
                "the measured |tau_peak|, per-drive stores at 1.5x the measured "
                "positive work per stride, and stability from the free-root "
                "packet's barycentric support-hull condition with a derived "
                "capture-step reflex. Every constant is measured, quoted, or "
                "derived in docs/research/20260918_gait_controller_derivation.md.",
            "prediction":
                "A free-root macaque assembly carrying the target tables through "
                "the control law walks: duty factor 0.68 in [0.63, 0.73], peak "
                "vertical GRF 1.08 BW within +/-10%, toe-off at 68% +/- 5% cycle, "
                "the weight-support closure 2*I_stance = BW*T_cycle within 3%, "
                "per-drive positive work per stride within its store with zero "
                "depletion events over 10 consecutive cycles, and the CoM "
                "projection inside the support hull at every loaded tick. NONE "
                "of this is measured yet.",
            "contract": {
                "derivation": DOC,
                "derives": [
                    "gait cycle from the admitted GRF: duty 0.683 sampled (paper "
                    "0.67), toe-off 68%, stance 0.483 s, swing 0.227 s, double "
                    "support 37% of the cycle (Section 1)",
                    "the natural-pendulum check: swing runs 2.2x faster than "
                    "T_nat = 1.015 s, so the clock is an explicit contact-reset "
                    "hybrid, not a passive oscillator (Section 1.6)",
                    "21-node piecewise-linear phase tables (rad) for hip/knee/"
                    "ankle/MP in the Oku sign convention, max reconstruction "
                    "error 4.1 deg (Section 2.4)",
                    "GRF profile: peak 106.5 N = 1.082 BW at 3%, loading rate "
                    "13.2 kN/s, stance impulse 34.48 N.s with the closure "
                    "identity 2*I = BW*T at -1.3% (Section 3)",
                    "torque requirements: |tau_peak| hip 8.97 / knee 5.31 / "
                    "ankle 5.92 / MP 0.71 N.m; positive work per stride hip "
                    "5.25 / knee 2.56 / ankle 3.27 / MP 0.50 J (Section 4)",
                    "the budget verdict: the qualified 2.0 J per-drive store "
                    "does NOT power one stride (hip needs 3.25 J at arm scale); "
                    "derived store floor = 1.5x W+_d; caps = 1.25x |tau_peak| "
                    "(Section 4.3/4.4)",
                    "controller: phase clock + tables + capped mass-normalized "
                    "PD (f_s = 4.0 Hz derived) + support-hull stability with "
                    "the capture-step reflex (Section 5)",
                    "eight measured falsifiers F-G1..F-G8 with refusal "
                    "envelopes, and the staged ladder A..G from the frozen "
                    "mounted arm to the walking macaque (Sections 6-7)",
                ],
                "falsifiers": [
                    "F-G1 realized trajectories within the node tables +/-5 deg, "
                    "excursions within +/-10% of measured",
                    "F-G2 duty 0.68 in [0.63, 0.73], left/right phase offset "
                    "0.50 +/- 0.02 (contact reset required)",
                    "F-G3 GRF envelope: peak 1.08 BW +/-10%, toe-off 68% +/-5%, "
                    "closure 2*I_stance = BW*T within 3%",
                    "F-G4 energy: per-drive W+ per stride within 2x table and "
                    "within store; zero empty_events over 10 strides",
                    "F-G5 the free-root falsifier: controller off -> the body "
                    "falls; any hover refutes the simulator",
                    "F-G6 stability: 10 cycles without tip; the capture reflex "
                    "must land an early touchdown under a scripted push",
                    "F-G7 determinism: two identical runs, bit-identical status "
                    "streams",
                    "F-G8 ledger closure |balance_error_J| < 1e-5 and "
                    "|store_balance_error_J| < 1e-5 on every status query",
                ],
                "owned_files": [
                    DOC,
                    DERIVE,
                    DERIVED,
                    ADMITTER,
                ],
            },
        },
        "falsifier": {
            "statement":
                "If the controller is removed and the body does not fall, or the "
                "realized angles, GRF profile, or duty factor leave the stated "
                "envelopes, or a drive depletes its store mid-walk, or the CoM "
                "projection leaves the support hull without a tip, or any status "
                "query violates the ledger identities -- this derivation is "
                "FALSE and the controller is refused. A creature that cannot "
                "FALL cannot walk.",
            "acceptance_test":
                "Not yet runnable: the implementing lanes execute stages D-F of "
                "the ladder in docs/research/20260918_gait_controller_derivation.md "
                "and record measured results per falsifier in a later revision. "
                "Until then the honest status is untested.",
            "status": "untested",
        },
    },
]


def admit(objects, object_id, revisions):
    current = revisions[-1]
    prior = revisions[:-1]
    existing = [o for o in objects if o.get("id") == object_id]
    if existing:
        if existing[0] == current:
            print(f"{object_id}: already at current revision (no-op)")
            return 0
        if existing[0] in prior:
            objects[objects.index(existing[0])] = current
            print(f"{object_id}: superseded prior revision with current")
            return 2
        print(f"{object_id}: REFUSAL -- exists with foreign content; "
              "graph policy is never silently overwritten", file=sys.stderr)
        return 1
    objects.append(current)
    print(f"{object_id}: admitted to {PROGRAM}")
    return 2


def main() -> int:
    raw = PROGRAM.read_bytes()
    payload = json.loads(raw.decode("utf-8-sig"))
    objects = payload["objects"]
    changed = admit(objects, GAIT_ID, GAIT_REVISIONS)
    if changed == 1:
        return 1
    if changed:
        out = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
        PROGRAM.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
