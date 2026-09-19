"""Admit the CT visual-skeleton layer for the whole-body macaque scene (RULE 0) into the
authored program.

Idempotent AND revision-aware, one lane-owned object. If a stored record equals the
current revision the script is a byte-preserving no-op; if it equals a known PRIOR
revision of the same lane object it is replaced by the current revision; anything
else refuses loudly -- graph policy is never silently overwritten. Formatting is
preserved (1-space indent, CRLF, no BOM).

Run from the checkout root with the pinned interpreter:
    python -B tools/creature_graph/validation/admit_macaque_skeleton_layer_20260919.py
then rebuild the store:
    python -B tools/creature_graph/build_graph.py

The record is banked BEFORE any scene code exists (RULE 0): the 25 committed CT bone
meshes of USNM 497136-3 (M. mulatta, 160 um CT, MorphoSource 000875604, commercial
license pinned in download_receipt.json) are declared to become the macaque scene's
visual skeleton layer on the stage-E whole-body assembly at the derived standing pose.
The femur pair (bones 2, 3, by near-equal principal-axis length and head-acetabular
end identified by axial-skeleton proximity) is declared to receive the segment-aware
scale mapping 0.163 / (pc1 extent) onto the thigh segment, head seated at the hip
joint center. Nothing has been mounted or rendered; the falsifier status is honestly
"untested". This file contains no scene code.

Revision 2 substituted the MEASURED joint-span mapping (0.163 / head-cap-to-
condyle-cap centroid) after the extent mapping fired the mapping discriminator at
the knee. Revision 3 (current) records the compile-time measurement: the scene
compiler tools/science_funnel/macaque_skeleton_scene.py runs green against the
admitted store, pins both the operator's nearest-surface falsifier and the
landmark-seating residuals, and the falsifier status flips to "passing". The rev1
"nearest-surface 11.279/11.840 mm" firing numbers were a vertex-distance proxy; the
exact-surface metric does not separate the two mappings (both reach the joint with
the bone tip), and the true rev1 discriminator is the measured condyle-cap-centroid
seating residual ~18.3 mm at the knee.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROGRAM = ROOT / "tools" / "creature_graph" / "data" / "authored" / "project_program.json"

RECORD_ID = "work.creature.macaque_skeleton_layer"

CT_RECEIPT = "tools/science_funnel/data/morphosource_ct/mesh_receipt.json"
CT_DOWNLOAD = "tools/science_funnel/data/morphosource_ct/download_receipt.json"
ADMITTER = "tools/creature_graph/validation/admit_macaque_skeleton_layer_20260919.py"

REVISIONS = [
    # revision 1 (prior): the skeleton-layer claim is declared with a principal-axis
    # EXTENT scale mapping; later measured and fired at the knee on that mapping.
    {
        "id": RECORD_ID,
        "kind": "work",
        "name": "CT bone meshes as the whole-body macaque scene visual skeleton layer (AUTHORED)",
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "work.creature.macaque_assembly",
            "work.creature.macaque_whole_body_sources",
        ],
        "physical": {
            "statement":
                "The 25 committed CT bone meshes of USNM 497136-3 (Macaca mulatta, "
                "160 um CT, MorphoSource 000875604; license pinned in "
                "download_receipt.json) become the macaque scene's visual skeleton "
                "layer, mounted on the stage-E whole-body assembly of "
                "work.creature.macaque_assembly at its derived standing pose (hip "
                "height 0.3307 m, hip +0.3287 rad, knee -0.8661 rad, ankle +1.3082, "
                "MP +0.8198; Cayo plane y = -42.82679794555668 m). Each bone is "
                "converted mm -> m (x0.001). The femur pair (bones 2 and 3, "
                "identified by near-equal principal-axis length 48.10/48.50 mm and a "
                "head end marked by proximity to the axial skeleton/acetabulum at "
                "1.78/4.84 mm) receives the declared segment-aware scale mapping "
                "0.163 / (principal-axis extent) onto the 0.163 m thigh segment, head "
                "seated at the hip joint center and the long principal axis aligned "
                "with the derived hip->knee direction. The other bones render at true "
                "mm scale in the CT frame; their segment attribution is not yet "
                "derived (manifest carries size class only).",
            "prediction":
                "After the declared mm->m conversion, segment-aware scale mapping and "
                "mount, the nearest-surface distance from the mounted femur pair to "
                "the derived hip and knee joint centers is each at most 5 mm, and all "
                "25 meshes render at correct mm scale in the compiled scene. This is "
                "measured on the compiled geometry, not in the engine.",
            "contract": {
                "derivation": "docs/research/20260918_monkey_assembly_derivation.md",
                "sources": [
                    CT_DOWNLOAD,
                    CT_RECEIPT,
                    "work.creature.macaque_assembly (stage E standing pose)",
                ],
                "declared_mappings": [
                    "femur pair = bones 2,3: near-equal principal-axis length "
                    "(48.10/48.50 mm) and head end nearest the axial skeleton "
                    "(1.78/4.84 mm gap = acetabular side)",
                    "segment-aware scale on thigh = 0.163 m / (bone principal-axis "
                    "extent in m); infant CT -> adult Oku segment mapping, same class "
                    "as the assembly HAT carve-out",
                    "head seated at hip joint center; bone long axis aligned to the "
                    "derived hip->knee direction (thigh 0.163 m at +18.83 deg)",
                    "L/R femur slots declared by projection side of the axial "
                    "skeleton's z centroid (bone 2 = +z, bone 3 = -z)",
                ],
                "explicit_unknowns": [
                    "non-femur bones kept at true mm scale; their segment attribution "
                    "is undetermined (manifest records size class only)",
                    "lateral hip spacing of the standing scaffold is locked at 0 "
                    "(assembly stage E hip abduction locked at 0); both femora mount "
                    "in the sagittal plane",
                    "infant specimen anatomy mounted on adult segment kinematics is a "
                    "declared mapping, not a claim of adult femur proportions",
                ],
                "staged_ladder": [
                    "A: skeleton scene compiler emits the standing scaffold + 25 "
                    "bones at mm scale; femur falsifier measured at compile time",
                    "B: render the compiled scene in the engine and judge the femur "
                    "joint alignment on screen",
                ],
                "owned_files": [CT_DOWNLOAD, CT_RECEIPT, ADMITTER],
            },
        },
        "falsifier": {
            "statement":
                "The skeleton-layer claim is false if the mounted femur pair's "
                "nearest-surface distance to the derived hip or knee joint centers "
                "exceeds 5 mm after the declared mm->m conversion and segment-aware "
                "scale mapping, if the mm->m conversion is not x0.001, if the scale "
                "is not 0.163/(principal-axis extent), or if any of the 25 meshes is "
                "not present at its committed hash in the compiled scene. A bone that "
                "cannot be seated on its joint cannot be a skeleton layer.",
            "acceptance_test":
                "Compile the skeleton scene and measure, on the compiled geometry, "
                "the nearest-surface distance from each mounted femur to the derived "
                "hip and knee joint centers; both must be <= 0.005 m. Implemented as "
                "a compile-time geometric check inside the scene compiler and pinned "
                "by tests/test_macaque_skeleton_scene.py before any engine render or "
                "qualification. Until then the honest status is untested.",
            "status": "untested",
        },
    },
    # revision 2 (current): measured joint-span scale mapping supersedes the rev1
    # extent mapping, which FIRED at the knee (11.3/11.8 mm > 5 mm).
    {
        "id": RECORD_ID,
        "kind": "work",
        "name": "CT bone meshes as the whole-body macaque scene visual skeleton layer (AUTHORED)",
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "work.creature.macaque_assembly",
            "work.creature.macaque_whole_body_sources",
        ],
        "physical": {
            "statement":
                "The 25 committed CT bone meshes of USNM 497136-3 (Macaca mulatta, "
                "160 um CT, MorphoSource 000875604; license pinned in "
                "download_receipt.json) become the macaque scene's visual skeleton "
                "layer, mounted on the stage-E whole-body assembly of "
                "work.creature.macaque_assembly at its derived standing pose (hip "
                "height 0.3307 m, hip +0.3287 rad, knee -0.8661 rad, ankle +1.3082, "
                "MP +0.8198; Cayo plane y = -42.82679794555668 m). Each bone is "
                "converted mm -> m (x0.001). The femur pair (bones 2 and 3, "
                "identified by near-equal principal-axis length 48.10/48.50 mm and a "
                "head end marked by proximity to the axial skeleton/acetabulum at "
                "1.78/4.84 mm gap = acetabular side) receives the MEASURED "
                "segment-aware scale mapping 0.163 / (femur joint span) onto the "
                "0.163 m thigh segment, where joint span = head-cap centroid -> "
                "condyle-cap centroid (42.734/42.970 mm; scale 3.8143/3.7933). The "
                "head-cap centroid is seated at the hip joint center and the "
                "head->condyle axis is aligned with the derived hip->knee direction, "
                "so the condyle-cap centroid lands on the knee center by "
                "construction. The rev1 candidate (0.163 / principal-axis EXTENT "
                "48.102/48.500 mm = scale 3.3886/3.3608) was measured and FIRED the "
                "falsifier at the knee: scaling the extremity extent to 0.163 m "
                "leaves the interior joint span at only ~0.145 m, so the condyles "
                "land 11.279/11.840 mm short of the knee center (> 5 mm). Measured "
                "on the committed preview bone geometry: bone 2 hip 4.234 / knee "
                "1.245 mm; bone 3 hip 3.763 / knee 4.307 mm -- every joint within "
                "5 mm. The other bones render at true mm scale in the CT frame; "
                "their segment attribution is undetermined (manifest carries size "
                "class only).",
            "prediction":
                "After the declared mm->m conversion, the measured joint-span scale "
                "mapping and mount, the nearest-surface distance from each mounted "
                "femur to the derived hip and knee joint centers is each at most "
                "5 mm, and all 25 meshes render at correct mm scale in the compiled "
                "scene. This is measured on the compiled geometry, not in the engine; "
                "the values below are the pre-compile measurement on the committed "
                "preview meshes.",
            "contract": {
                "derivation": "docs/research/20260918_monkey_assembly_derivation.md",
                "sources": [
                    CT_DOWNLOAD,
                    CT_RECEIPT,
                    "work.creature.macaque_assembly (stage E standing pose)",
                ],
                "declared_mappings": [
                    "femur pair = bones 2,3: near-equal principal-axis length "
                    "(48.102/48.500 mm) and head end nearest the axial skeleton "
                    "(1.78/4.84 mm gap = acetabular side)",
                    "femur joint span = head-cap centroid -> condyle-cap centroid "
                    "(10% projection end caps; 42.734/42.970 mm); scale = 0.163 m / "
                    "(joint span in m) = 3.8143/3.7933",
                    "head-cap centroid seated at hip joint center; head->condyle "
                    "axis aligned to the derived hip->knee direction (thigh 0.163 m "
                    "at +18.83 deg); condyle-cap centroid lands on the knee center "
                    "by construction",
                    "L/R femur slots declared by projection side of the axial "
                    "skeleton's z centroid (bone 2 = +z, bone 3 = -z)",
                ],
                "explicit_unknowns": [
                    "non-femur bones kept at true mm scale; their segment attribution "
                    "is undetermined (manifest records size class only)",
                    "lateral hip spacing of the standing scaffold is locked at 0 "
                    "(assembly stage E hip abduction locked at 0); both femora mount "
                    "in the sagittal plane",
                    "infant specimen anatomy mounted on adult segment kinematics is a "
                    "declared mapping, not a claim of adult femur proportions",
                ],
                "staged_ladder": [
                    "A: skeleton scene compiler emits the standing scaffold + 25 "
                    "bones at mm scale; femur falsifier measured at compile time",
                    "B: render the compiled scene in the engine and judge the femur "
                    "joint alignment on screen",
                ],
                "owned_files": [CT_DOWNLOAD, CT_RECEIPT, ADMITTER],
            },
        },
        "falsifier": {
            "statement":
                "The skeleton-layer claim is false if the mounted femur pair's "
                "nearest-surface distance to the derived hip or knee joint centers "
                "exceeds 5 mm after the declared mm->m conversion and the measured "
                "joint-span scale mapping, if the mm->m conversion is not x0.001, if "
                "the femur scale is not 0.163 divided by the measured joint span "
                "(head-cap centroid -> condyle-cap centroid), if the head is not "
                "seated at the hip joint center, or if any of the 25 meshes is not "
                "present at its committed hash in the compiled scene. A bone that "
                "cannot be seated on its joint cannot be a skeleton layer. The rev1 "
                "extent-based scale measurement (knee nearest-surface 11.279/11.840 "
                "mm) already FIRED this falsifier on the committed geometry; rev2 "
                "replaces the mapping.",
            "acceptance_test":
                "Compile the skeleton scene and measure, on the compiled geometry, "
                "the nearest-surface distance from each mounted femur to the derived "
                "hip and knee joint centers; both must be <= 0.005 m. Implemented as "
                "a compile-time geometric check inside the scene compiler and pinned "
                "by tests/test_macaque_skeleton_scene.py before any engine render or "
                "qualification. Until then the honest status is untested.",
            "status": "untested",
        },
    },
    # revision 3 (current): measured at compile time. The scene compiler
    # (tools/science_funnel/macaque_skeleton_scene.py) plus
    # tests/test_macaque_skeleton_scene.py run green against the admitted store;
    # falsifier status is "passing" with the measured values. The honest
    # correction recorded here: the rev1 firing numbers in rev2's narrative
    # (nearest-surface 11.279/11.840 mm) were a VERTEX-DISTANCE PROXY. Measured on
    # the exact point-to-triangle metric, the extent mapping does NOT separate from
    # the joint-span mapping at the surface -- both reach the knee joint with the
    # bone's extremity tip (rev1 exact-surface knee 0.476/2.486 mm, also within
    # tolerance). The quantity the extent mapping actually fails is the
    # landmark-seating residual: scaling the extremity to 0.163 m leaves the
    # condyle-cap centroid ~18.3 mm short of the knee center (rev2's "condyles land
    # short" result, restated honestly). The compiler now emits BOTH the operator's
    # nearest-surface falsifier AND the seating residual, and the seating residual is
    # the mapping discriminator.
    {
        "id": RECORD_ID,
        "kind": "work",
        "name": "CT bone meshes as the whole-body macaque scene visual skeleton layer (AUTHORED)",
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "work.creature.macaque_assembly",
            "work.creature.macaque_whole_body_sources",
        ],
        "physical": {
            "statement":
                "The 25 committed CT bone meshes of USNM 497136-3 (Macaca mulatta, "
                "160 um CT, MorphoSource 000875604; license pinned in "
                "download_receipt.json) become the macaque scene's visual skeleton "
                "layer, mounted on the stage-E whole-body assembly of "
                "work.creature.macaque_assembly at its derived standing pose (hip "
                "height 0.3307 m, hip +0.3287 rad, knee -0.8661 rad, ankle +1.3082, "
                "MP +0.8198; Cayo plane y = -42.82679794555668 m). Each bone is "
                "converted mm -> m (x0.001). The femur pair (bones 2 and 3, "
                "identified by near-equal principal-axis length 48.102/48.500 mm and "
                "a head end marked by proximity to the axial skeleton/acetabulum at "
                "1.78/4.84 mm gap = acetabular side) receives the MEASURED "
                "segment-aware scale mapping 0.163 / (femur joint span) onto the "
                "0.163 m thigh segment, where joint span = head-cap centroid -> "
                "condyle-cap centroid (42.734/42.970 mm; scale 3.8143/3.7933). The "
                "head-cap centroid is seated at the hip joint center and the "
                "head->condyle axis is aligned with the derived hip->knee direction, "
                "so the condyle-cap centroid lands on the knee center by "
                "construction. MEASURED at compile time on the compiler's own "
                "emitted geometry: exact point-to-triangle nearest-surface from the "
                "derived joints to the mounted femurs -- bone 2 hip 0.224 mm / knee "
                "0.003 mm, bone 3 hip 0.015 mm / knee 0.102 mm (every value <= "
                "5 mm); landmark-seating residuals (condyle-cap centroid to knee "
                "center) 3.1e-14 mm / 0.0 (the head-cap centroid is seated exactly "
                "at the hip by construction). The rev1 extent candidate's honest "
                "failure is the seating residual ~18.3 mm at the knee (see the "
                "falsifier correction). The other bones render at true mm scale in "
                "the CT frame; their segment attribution is undetermined (manifest "
                "carries size class only).",
            "prediction":
                "After the declared mm->m conversion, the measured joint-span scale "
                "mapping and mount, the nearest-surface distance from each mounted "
                "femur to the derived hip and knee joint centers is each at most "
                "5 mm, all 25 meshes render at correct mm scale in the compiled "
                "scene, and each femur's landmark-seating residual at the knee is at "
                "most 5 mm. This is measured on the compiled geometry, not in the "
                "engine. FALSIFIER STATUS: passing (rev3, measured).",
            "contract": {
                "derivation": "docs/research/20260918_monkey_assembly_derivation.md",
                "sources": [
                    CT_DOWNLOAD,
                    CT_RECEIPT,
                    "work.creature.macaque_assembly (stage E standing pose)",
                ],
                "declared_mappings": [
                    "femur pair = bones 2,3: near-equal principal-axis length "
                    "(48.102/48.500 mm) and head end nearest the axial skeleton "
                    "(1.78/4.84 mm gap = acetabular side)",
                    "femur joint span = head-cap centroid -> condyle-cap centroid "
                    "(10% projection end caps; 42.734/42.970 mm); scale = 0.163 m / "
                    "(joint span in m) = 3.8143/3.7933",
                    "head-cap centroid seated at hip joint center; head->condyle "
                    "axis aligned to the derived hip->knee direction (thigh 0.163 m "
                    "at +18.83 deg); condyle-cap centroid lands on the knee center "
                    "by construction",
                    "non-femur bones render at true mm scale (x0.001) in the CT "
                    "frame; segment attribution undetermined",
                ],
                "explicit_unknowns": [
                    "non-femur bones' segment attribution is undetermined (manifest "
                    "records size class only)",
                    "lateral hip spacing of the standing scaffold is locked at 0 "
                    "(assembly stage E hip abduction locked at 0); both femora mount "
                    "in the sagittal plane",
                    "infant specimen anatomy mounted on adult segment kinematics is a "
                    "declared mapping, not a claim of adult femur proportions",
                ],
                "staged_ladder": [
                    "A: skeleton scene compiler emits the standing scaffold + 25 "
                    "bones at mm scale; femur falsifier measured at compile time",
                    "B: render the compiled scene in the engine and judge the femur "
                    "joint alignment on screen",
                ],
                "owned_files": [CT_DOWNLOAD, CT_RECEIPT, ADMITTER],
                "measured_values_m": {
                    "bone_2": {"hip_surface": 0.000224370622040146,
                               "knee_surface": 3.411363514252586e-06,
                               "seating_knee": 3.1031676915590914e-17},
                    "bone_3": {"hip_surface": 1.4556536518807113e-05,
                               "knee_surface": 0.00010210699822516641,
                               "seating_knee": 0.0},
                },
            },
        },
        "falsifier": {
            "statement":
                "The skeleton-layer claim is false if the mounted femur pair's "
                "nearest-surface distance to the derived hip or knee joint centers "
                "exceeds 5 mm after the declared mm->m conversion and the measured "
                "joint-span scale mapping, if the mm->m conversion is not x0.001, if "
                "the femur scale is not 0.163 divided by the measured joint span "
                "(head-cap centroid -> condyle-cap centroid), if the head is not "
                "seated at the hip joint center, if a femur's landmark-seating "
                "residual at the knee exceeds 5 mm, or if any of the 25 meshes is "
                "not present at its committed hash in the compiled scene. A bone "
                "that cannot be seated on its joint cannot be a skeleton layer. "
                "CORRECTION to rev2's narrative: the rev1 firing numbers "
                "(nearest-surface 11.279/11.840 mm) were a vertex-proxy artifact; "
                "under the exact point-to-triangle surface metric the extent mapping "
                "reaches the knee joint too (rev1 exact-surface knee 0.476/2.486 "
                "mm). The extent mapping's real failure is the landmark-seating "
                "residual ~18.3 mm at the knee -- the condyle-cap centroid (the "
                "joint's own articulation center) lands 18.3 mm short of the knee "
                "even though the bone's extremity tip reaches it. The built compiler "
                "emits both metrics; the seating residual is the mapping "
                "discriminator, the surface bound is the operator's sanity cap.",
            "acceptance_test":
                "Compile the skeleton scene and measure, on the compiled geometry, "
                "the exact point-to-triangle nearest-surface distance from each "
                "mounted femur to the derived hip and knee joint centers (both <= "
                "0.005 m) AND each femur's landmark-seating residual at the knee "
                "(<= 0.005 m). Implemented as a compile-time geometric check inside "
                "the scene compiler and pinned by tests/test_macaque_skeleton_scene.py "
                "(7 tests green, rev3). Engine screen remains ladder stage B.",
            "status": "passing",
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
    changed = admit(objects, RECORD_ID, REVISIONS)
    if changed == 1:
        return 1
    if changed:
        out = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
        PROGRAM.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())