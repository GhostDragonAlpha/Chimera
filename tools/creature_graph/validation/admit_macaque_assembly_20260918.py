"""Admit the whole-body macaque assembly derivation (RULE 0) into the authored program.

Idempotent AND revision-aware, one lane-owned object. If a stored record equals the
current revision the script is a byte-preserving no-op; if it equals a known PRIOR
revision of the same lane object it is replaced by the current revision; anything
else refuses loudly -- graph policy is never silently overwritten. Formatting is
preserved (1-space indent, CRLF, no BOM).

Run from the checkout root with the pinned interpreter:
    python -B tools/creature_graph/validation/admit_macaque_assembly_20260918.py
then rebuild the store:
    python -B tools/creature_graph/build_graph.py

The record is banked BEFORE any implementing code exists (RULE 0): the derivation at
docs/research/20260918_monkey_assembly_derivation.md authors the assembly map, mass
distribution, standing statics, fall sequence, gait reference and staged ladder from
admitted graph data only; nothing in it has been measured in simulation, so the
falsifier status is honestly "untested". It contains no engine code.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROGRAM = ROOT / "tools" / "creature_graph" / "data" / "authored" / "project_program.json"

ASSEMBLY_ID = "work.creature.macaque_assembly"

DOC = "docs/research/20260918_monkey_assembly_derivation.md"
ADMITTER = "tools/creature_graph/validation/admit_macaque_assembly_20260918.py"

REVISIONS = [
    # revision 1 (current): the derivation is authored; nothing simulated yet.
    {
        "id": ASSEMBLY_ID,
        "kind": "work",
        "name": "Whole-body macaque assembly derived from admitted graph data (AUTHORED)",
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "model.anatomy.macaque_arm",
            "work.creature.macaque_whole_body_sources",
            "work.environment.terrain",
            "work.creature.macaque_intake",
        ],
        "physical": {
            "statement":
                "The admitted graph records assemble into one 32-DOF physically "
                "simulated macaque: a 6-coordinate floating base on the HAT "
                "(Oku Table 1 HAT minus two declared arm carve-outs = 7.371998 kg), "
                "two 7-coordinate rhesus arm chains (0.406001 kg each), and two "
                "6-coordinate hindlimbs (hip ball + knee + ankle + MTP; 0.927 kg "
                "each) for a preserved total of 10.038 kg / W = 98.44 N. The "
                "derivation at docs/research/20260918_monkey_assembly_derivation.md "
                "computes, with no free parameter: the standing configuration at "
                "the Cayo plane (-42.82679794555668 m ellipsoidal; hip height "
                "0.3307 m, trunk pitch 26.33 deg, COM 0.1917 m ahead of the hind "
                "paws, inside the support polygon by ~0.25 m both ways), the "
                "trunk-beam girdle split (fore paws 34.18 N = 34.7% BW each, hind "
                "15.04 N = 15.3%: 69/31 fore-dominant), the static muscle demands "
                "against Guimaraes PCSA capacities with Oku-fit effective moment "
                "arms (triceps surae 22.3-28.6% activation, knee flexors 4.3-5.6%), "
                "the fore-paw tenability bound (0.110 m at the walking pose), the "
                "zero-activation fall (elbow 58 ms -> knee 98 ms -> hip 191 ms, "
                "~20.49 J dissipated to prone), and the gait reference (Oku ROMs, "
                "GRF peak 1.082 BW, duty 0.663, bilateral closure -2.3%; Janisch "
                "cercopithecoid excursions). It implements nothing.",
            "prediction":
                "Replayed in the qualified dynamics, the assembled body at the "
                "derived stance carries fore paws at 34.7% BW each (+/-10), stands "
                "with triceps surae inside the 22-29% activation band, and with "
                "zero activation folds elbow-first inside 0.2 s dropping the COM "
                "0.358 -> ~0.15 m with ~20.49 J appearing in the impact/friction "
                "ledgers at the packets' 1e-5 J closure bar. NONE of this is "
                "measured in simulation yet.",
            "contract": {
                "derivation": DOC,
                "sources": [
                    "model.anatomy.macaque_arm (limblab monkeyArmModel @ 4fb7ddee, "
                    "M. mulatta, MIT)",
                    "oku2021 Table 1 inertias via "
                    "work.creature.macaque_whole_body_sources (M. fuscata, CC BY)",
                    "guimaraes2026.hindlimb_architecture (M. mulatta PCSA, CC BY)",
                    "oku2021.bipedal_series (SIMULATION-derived gait reference, CC BY)",
                    "janisch.wildprimate_kinematics (cercopithecoid quadrupedal "
                    "analog, CC BY)",
                    "work.environment.terrain wiring (Cayo plane height)",
                    "docs/research/muscle_physiology_reference.md (specific "
                    "tension 25-32 N/cm^2)",
                ],
                "declared_mappings": [
                    "HAT carve-out: fuscata HAT minus 2x mulatta arm chain mass, "
                    "total preserved at 10.038 kg; HAT COM fraction and pitch "
                    "inertia retained on the residual",
                    "second arm = first arm mirrored through the sagittal plane",
                    "hip abduction/rotation DOFs derived from function, locked at 0 "
                    "until the balance stage",
                    "no tail DOF (req.macaque_rebuild); head welded into HAT; "
                    "mandible locked (future feeding lane)",
                ],
                "explicit_unknowns": [
                    "fuscata forelimb mass split inside Oku HAT (Ogihara model "
                    "ON_REQUEST)",
                    "Ogihara 3-D joint axes and true hip-to-shoulder span "
                    "(reference s = 0.30 m, bounds [0.28, 0.482])",
                    "Janisch angle-convention signs (source R code unpinned); the "
                    "foot-pitch sign (+/-15.75 deg) is disambiguated dynamically "
                    "by falsifier F3",
                    "Oku cycle period (series x axis is percent of cycle)",
                    "rectus femoris absent from the Guimaraes Macaca sheet; "
                    "knee-extensor capacity quotes VAS only",
                ],
                "staged_ladder": [
                    "A: 2-coordinate mounted arm (qualified, frozen)",
                    "B: 7-coordinate arm (seven_coordinate_lift packet F1-F9)",
                    "C: 8-DOF free root (free_root_balance packet F1-F9)",
                    "D: 20-DOF second arm (mirror-oracle gate at 1e-12)",
                    "E: 32-DOF hindlimbs; F1 statics replay (69/31 paw split, "
                    "ankle 22-29% band), F2 fall cascade, F3 foot-pitch "
                    "disambiguation",
                    "F: hip abd/rot unlock; walk closure per F4",
                ],
                "owned_files": [DOC, ADMITTER],
            },
        },
        "falsifier": {
            "statement":
                "If the replayed statics differ from the derivation's fore/hind paw "
                "split (69/31) by more than 10 points, place the COM projection "
                "outside the derived support polygon, hold a passive stance, fold "
                "in any order other than elbow->knee->hip on zero activation, "
                "settle without ~20.49 J of accounted dissipation, or violate the "
                "1e-5 J ledger closure on any status query -- the assembly claim "
                "is FALSE and the implementing lane supersedes this record with "
                "the measured revision. A creature that cannot FALL cannot walk.",
            "acceptance_test":
                "Not yet runnable: stages C-E of the ladder execute the falsifiers "
                "of docs/research/20260918_monkey_assembly_derivation.md sections "
                "3-6 via the packets' qualification machinery and record measured "
                "results here in revision 2. Until then the honest status is "
                "untested.",
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
    changed = admit(objects, ASSEMBLY_ID, REVISIONS)
    if changed == 1:
        return 1
    if changed:
        out = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
        PROGRAM.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
