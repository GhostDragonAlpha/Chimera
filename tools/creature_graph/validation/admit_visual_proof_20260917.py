"""Admit work.data.visual_proof_20260917 (RULE 0) into the authored program.

Idempotent AND revision-aware: the lane owns exactly this object. If the
stored record equals the current revision the script is a byte-preserving
no-op; if it equals a known PRIOR revision of this same lane object it is
replaced by the current revision (this is how the lane records its own
falsified assumptions); anything else refuses loudly -- graph policy is
never silently overwritten. Formatting is preserved (1-space indent, CRLF).

Run from the checkout root:
    python -B tools/creature_graph/validation/admit_visual_proof_20260917.py
then rebuild the store:
    python -B tools/creature_graph/build_graph.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROGRAM = ROOT / "tools" / "creature_graph" / "data" / "authored" / "project_program.json"

OBJECT_ID = "work.data.visual_proof_20260917"

REVISIONS = [
    # revision 1 (superseded): assumed a sequential-draco decode was possible.
    {
        "id": OBJECT_ID,
        "kind": "work",
        "name": "Visual proof renders of admitted library data (PROOF-OF-INTAKE)",
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "work.data.batch_intake",
            "work.environment.terrain",
            "concept.gait",
        ],
        "physical": {
            "statement":
                "Every batch-admitted library family this work pins -- the "
                "Smithsonian USNM 15259 cranium/mandible GLB pair, PanTHERIA "
                "traits (genus Macaca), the pinned Copernicus GLO-30 window at "
                "the Luquillo control (18.425, -65.95), and the Janisch wild "
                "primate stride angles -- renders deterministically to a PNG "
                "from the pinned bytes alone, so an operator can SEE what was "
                "admitted. The renders are PROOF OF INTAKE and decodability; "
                "they are never physics verification, never qualification, and "
                "carry that label in-image and in the manifest.",
            "prediction":
                "Re-rendering any family from the same pinned inputs under the "
                "pinned interpreter reproduces the PNG byte-identically, and the "
                "manifest chain (input sha256 -> png sha256) verifies against "
                "the files on disk.",
            "contract": {
                "renders": [
                    "smithsonian USNM 15259 cranium + mandible: GLB container "
                    "parsed with stdlib struct (glTF-binary JSON+BIN chunks); "
                    "z-buffer raster ~320x240 under the document.json camera "
                    "node (quaternion pose, perspective yfov 52 deg, viewer "
                    "gamma 2), lights and radial background",
                    "pantheria: genus Macaca BMR (18-1_BasalMetRate_mLO2hr) vs "
                    "adult mass (5-1_AdultBodyMass_g), log-log; the dual-"
                    "measured Macaca rows plotted over the dual-measured library "
                    "cloud (the admitted connector records BMR measured on only "
                    "a minority of rows)",
                    "terrain: shaded relief of a 201x201-sample window of the "
                    "pinned Copernicus GLO-30 tile at the Luquillo control "
                    "(18.425, -65.95) read through terrain.sample_grid with the "
                    "DEM+geoid paths pinned in test_terrain",
                    "janisch: hip/knee angle-angle stride traces (MID substrate), "
                    "one polyline per species in stride order from "
                    "wildprimate_kin.csv",
                ],
                "falsified_assumption":
                    "The task brief assumed a pure struct decode of the GLB "
                    "geometry; the pinned artifacts are KHR_draco_mesh_compression "
                    "REQUIRED (accessors carry no bufferView), so plain accessor "
                    "reads are impossible. The pinned streams use MESH_SEQUENTIAL "
                    "ENCODING (draco method 0), which is decoded by a pure-python "
                    "stdlib decoder in visual_proof.py; the decode is falsified "
                    "against the glTF accessor min/max and face counts recorded "
                    "in the pinned bytes.",
                "labels": "Every PNG carries the in-image label PROOF-OF-INTAKE; "
                          "the manifest restates: proof of intake, NOT physics "
                          "verification.",
                "manifest": "tools/science_funnel/validation/"
                            "visual_proof_20260917/manifest.json records input "
                            "sha256 -> png sha256 for every render plus producer "
                            "identities; no render exists outside the chain.",
                "owned_files": [
                    "tools/science_funnel/visual_proof.py",
                    "tools/science_funnel/tests/test_visual_proof.py",
                    "tools/science_funnel/validation/visual_proof_20260917/",
                    "tools/creature_graph/validation/admit_visual_proof_20260917.py",
                ],
            },
        },
        "falsifier": {
            "statement":
                "A render that is not reproducible byte-identically from the "
                "pinned inputs, or that survives a one-byte input flip with an "
                "unchanged PNG, is not a visual proof.",
            "acceptance_test":
                "Render every family twice under the pinned interpreter and "
                "require identical PNG bytes; copy each pinned input, flip "
                "exactly one byte, re-render and require the PNG hash to change "
                "or the renderer to refuse loudly (compressed-container "
                "corruption refuses; it can never render identical bytes); "
                "verify the manifest chain input->png hashes on disk.",
            "status": "untested",
        },
    },
    # revision 2 (current): the sequential assumption was falsified by the
    # pinned bytes (edgebreaker + valence); the event stream diverges from the
    # reference layouts; the geometry decode refuses and the smithsonian
    # renders honestly show the accessor bounding boxes only.
    {
        "id": OBJECT_ID,
        "kind": "work",
        "name": "Visual proof renders of admitted library data (PROOF-OF-INTAKE)",
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "work.data.batch_intake",
            "work.environment.terrain",
            "concept.gait",
        ],
        "physical": {
            "statement":
                "Every batch-admitted library family this work pins renders "
                "deterministically to a PNG from the pinned bytes alone, as far "
                "as those bytes honestly decode, so an operator can SEE what was "
                "admitted: PanTHERIA Macaca traits, the Copernicus GLO-30 window "
                "at the Luquillo control (18.425, -65.95), the Janisch wild "
                "primate stride angles -- full data renders; the Smithsonian "
                "USNM 15259 GLB pair renders its accessor-declared bounding "
                "boxes under the document.json camera because the draco geometry "
                "REFUSES to decode (recorded refusal, see falsified assumptions). "
                "The renders are PROOF OF INTAKE and decodability; they are "
                "never physics verification, never qualification, and carry "
                "that label in-image and in the manifest.",
            "prediction":
                "Re-rendering any family from the same pinned inputs under the "
                "pinned interpreter reproduces the PNG byte-identically, and the "
                "manifest chain (input sha256 -> png sha256) verifies against "
                "the files on disk.",
            "contract": {
                "renders": [
                    "smithsonian USNM 15259 cranium + mandible: glTF-binary "
                    "container + JSON chunk parsed with stdlib struct; render = "
                    "accessor-declared bounding-box wireframe under the "
                    "document.json camera (quaternion pose, yfov 52 deg, radial "
                    "background), labelled 'geometry decode refused - bbox "
                    "intake only'; the draco geometry itself refuses (see "
                    "falsified_assumptions) and the refusal is recorded in the "
                    "manifest refusals list",
                    "pantheria: genus Macaca BMR (18-1_BasalMetRate_mLO2hr) vs "
                    "adult mass (5-1_AdultBodyMass_g), log-log; the dual-"
                    "measured Macaca rows plotted over the dual-measured library "
                    "cloud (only one Macaca row, Macaca mulatta, is dual-"
                    "measured -- that sparsity is the honest data state and is "
                    "stated on the render)",
                    "terrain: shaded relief of a 201x201-sample window of the "
                    "pinned Copernicus GLO-30 tile at the Luquillo control "
                    "(18.425, -65.95) read through terrain.sample_grid with the "
                    "DEM+geoid paths pinned in test_terrain; the 7-step "
                    "reduction runs at the control and its numbers are recorded "
                    "in the manifest",
                    "janisch: hip/knee angle-angle stride traces (MID substrate), "
                    "one polyline per species+video in stride order from "
                    "wildprimate_kin.csv",
                ],
                "falsified_assumptions": [
                    "ASSUMPTION FALSIFIED: a pure struct decode of the GLB "
                    "geometry is impossible -- the pinned artifacts REQUIRE "
                    "KHR_draco_mesh_compression (accessors carry no bufferView).",
                    "ASSUMPTION FALSIFIED: a draco MESH_SEQUENTIAL_ENCODING "
                    "decode was the next candidate; the pinned streams are "
                    "MESH_EDGEBREAKER_ENCODING (method 1) with the VALENCE "
                    "traversal decoder (type 2), bitstream 2.2.",
                    "ASSUMPTION FALSIFIED: the google/draco edgebreaker decoder "
                    "(HEAD and 1.3.6 both checked) does not parse the pinned "
                    "topology-split event section: the first event pair already "
                    "violates the reference delta check (source delta 667, split "
                    "delta 6724 > 667), and neither event order completes the "
                    "section. The producer variant is unidentified; a "
                    "producer-matching decoder does not exist in this lane. The "
                    "geometry decode therefore REFUSES and no geometry render is "
                    "claimed. Next executable options: identify the exact "
                    "producer and port its event decoder, or re-pin a non-draco "
                    "USNM 15259 derivative artifact with operator authorization.",
                ],
                "labels": "Every PNG carries the in-image label PROOF-OF-INTAKE; "
                          "the manifest restates: proof of intake, NOT physics "
                          "verification.",
                "manifest": "tools/science_funnel/validation/"
                            "visual_proof_20260917/manifest.json records input "
                            "sha256 -> png sha256 for every render, the recorded "
                            "refusals, and producer identities; no render exists "
                            "outside the chain.",
                "owned_files": [
                    "tools/science_funnel/visual_proof.py",
                    "tools/science_funnel/tests/test_visual_proof.py",
                    "tools/science_funnel/validation/visual_proof_20260917/",
                    "tools/creature_graph/validation/admit_visual_proof_20260917.py",
                ],
            },
        },
        "falsifier": {
            "statement":
                "A render that is not reproducible byte-identically from the "
                "pinned inputs, or that survives a one-byte input flip with an "
                "unchanged PNG, is not a visual proof.",
            "acceptance_test":
                "Render every family twice under the pinned interpreter and "
                "require identical PNG bytes; copy each pinned input, flip "
                "exactly one byte, re-render and require the PNG hash to change "
                "or the renderer to refuse loudly (compressed-container "
                "corruption refuses; it can never render identical bytes); "
                "verify the manifest chain input->png hashes on disk.",
            "status": "untested",
        },
    },

    # revision 3 (current; banked BEFORE code, Rule 0): the operator delegated
    # the decode-path decision. Two more premises were falsified mechanically
    # (all Smithsonian derivatives are draco; no Python decoder exists on PyPI).
    # The chosen path is the OFFICIAL Google Draco WASM decoder running in a
    # browser page -- the trusted reference decoder, not a port. Decoding is
    # pure, so the decoded buffer sha256s are the geometry's machine identity;
    # the browser screenshot is PERCEPTUAL EVIDENCE for the human, never the
    # proof itself.
    {
        "id": OBJECT_ID,
        "kind": "work",
        "name": "Visual proof renders of admitted library data (PROOF-OF-INTAKE)",
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "work.data.batch_intake",
            "work.environment.terrain",
            "concept.gait",
        ],
        "physical": {
            "statement":
                "Every batch-admitted library family this work pins renders "
                "deterministically to a PNG from the pinned bytes alone, as far "
                "as those bytes honestly decode, so an operator can SEE what was "
                "admitted: PanTHERIA Macaca traits, the Copernicus GLO-30 window "
                "at the Luquillo control (18.425, -65.95), the Janisch wild "
                "primate stride angles -- full data renders. The Smithsonian "
                "USNM 15259 GLB pair becomes a TRUE decoded-geometry render "
                "(shaded, z-buffered, under the document.json camera) whenever "
                "the decode identity is present and verifies: glb sha256 match, "
                "and decoded position/normal/index buffer bytes whose sha256 "
                "equals the recorded decode hashes. When the decode identity is "
                "absent or fails verification the render falls back to the "
                "honest accessor-bounding-box + recorded-refusal form (revision "
                "2 behavior); it never draws geometry it cannot verify. The "
                "decode identity is produced by the OFFICIAL Google Draco WASM "
                "decoder (draco_wasm_wrapper + draco_decoder.wasm, pinned CDN "
                "URLs, fetched sha256s recorded) running in a browser page via "
                "three.js GLTFLoader + DRACOLoader -- the trusted reference "
                "decoder, never a reimplementation. The browser screenshot is "
                "labelled PERCEPTUAL EVIDENCE: the decode hash is the proof, "
                "the picture is for the human. The renders are PROOF OF INTAKE "
                "and decodability; they are never physics verification, never "
                "qualification, and carry that label in-image and in the "
                "manifest.",
            "prediction":
                "The WASM decode is a pure function of the pinned bytes: "
                "re-decoding the same pinned GLB -- in fresh decoder instances, "
                "in a separate decode pass, and in a second harness run -- "
                "yields byte-identical POSITION/NORMAL/index buffers, so the "
                "recorded sha256s reproduce exactly. The renderer, fed the "
                "pinned decoded buffers, reproduces the true-geometry PNG "
                "byte-identically under the pinned interpreter, and the "
                "manifest chain (glb sha256 + buffer sha256s -> png sha256) "
                "verifies against the files on disk.",
            "contract": {
                "renders": [
                    "smithsonian USNM 15259 cranium + mandible, decode identity "
                    "present: TRUE decoded-geometry render from the pinned "
                    "position/normal/index buffers (sha-verified before use), "
                    "z-buffered Lambert shading under the document.json camera "
                    "(quaternion pose, yfov 52 deg, radial background), "
                    "labelled with the position-buffer hash prefix; the draco "
                    "decode section of the manifest records per specimen: glb "
                    "sha256, draco header facts (bitstream, encoder method, "
                    "traversal), decoded position/normal/index buffer sha256, "
                    "vertex/index counts, and the harness screenshot sha256",
                    "smithsonian USNM 15259 cranium + mandible, decode identity "
                    "absent or failing verification: accessor-declared "
                    "bounding-box wireframe under the document.json camera, "
                    "labelled 'geometry decode refused - bbox intake only', "
                    "with the refusal recorded in the manifest refusals list",
                    "browser harness screenshot per specimen (PERCEPTUAL "
                    "EVIDENCE): three.js WebGL render of the freshly decoded "
                    "mesh, committed next to the renders it evidences",
                    "pantheria: genus Macaca BMR (18-1_BasalMetRate_mLO2hr) vs "
                    "adult mass (5-1_AdultBodyMass_g), log-log; the dual-"
                    "measured Macaca rows plotted over the dual-measured library "
                    "cloud (only one Macaca row, Macaca mulatta, is dual-"
                    "measured -- that sparsity is the honest data state and is "
                    "stated on the render)",
                    "terrain: shaded relief of a 201x201-sample window of the "
                    "pinned Copernicus GLO-30 tile at the Luquillo control "
                    "(18.425, -65.95) read through terrain.sample_grid with the "
                    "DEM+geoid paths pinned in test_terrain; the 7-step "
                    "reduction runs at the control and its numbers are recorded "
                    "in the manifest",
                    "janisch: hip/knee angle-angle stride traces (MID substrate), "
                    "one polyline per species+video in stride order from "
                    "wildprimate_kin.csv",
                ],
                "falsified_assumptions": [
                    "ASSUMPTION FALSIFIED: a pure struct decode of the GLB "
                    "geometry is impossible -- the pinned artifacts REQUIRE "
                    "KHR_draco_mesh_compression (accessors carry no bufferView).",
                    "ASSUMPTION FALSIFIED: a draco MESH_SEQUENTIAL_ENCODING "
                    "decode was the next candidate; the pinned streams are "
                    "MESH_EDGEBREAKER_ENCODING (method 1) with the VALENCE "
                    "traversal decoder (type 2), bitstream 2.2.",
                    "ASSUMPTION FALSIFIED: the google/draco edgebreaker decoder "
                    "(HEAD and 1.3.6 both checked) does not parse the pinned "
                    "topology-split event section: the first event pair already "
                    "violates the reference delta check (source delta 667, split "
                    "delta 6724 > 667), and neither event order completes the "
                    "section. The producer variant is unidentified; a pure-"
                    "python port is falsified and is never retried.",
                    "ASSUMPTION FALSIFIED (2026-09-18 lane): a non-draco "
                    "Smithsonian derivative of USNM 15259 was assumed to exist "
                    "for re-pinning; the medium and low derivatives of BOTH the "
                    "cranium and the mandible were probed and ALL carry "
                    "KHR_draco_mesh_compression REQUIRED.",
                    "ASSUMPTION FALSIFIED (2026-09-18 lane): a Python Draco "
                    "decoder was assumed to be installable; the PyPI names "
                    "pydraco, pydraco3 and draco-loader all resolve to nothing "
                    "(404). No Python decoder exists.",
                    "PATH CHOSEN (operator-delegated decision, 2026-09-18): "
                    "decode with the OFFICIAL Google Draco WASM decoder inside "
                    "a browser page (three.js GLTFLoader + DRACOLoader over "
                    "draco_wasm_wrapper.js / draco_decoder.wasm fetched from "
                    "pinned CDN URLs with recorded sha256). Trusted decoder, "
                    "no port. If the browser/WASM channel cannot execute in "
                    "this environment the lane records an honest refusal with "
                    "cause and stops -- it never ships bounding-box renders as "
                    "if they were geometry.",
                ],
                "labels": "Every PNG carries the in-image label PROOF-OF-INTAKE; "
                          "decoded-geometry renders additionally carry the "
                          "position-buffer hash prefix; harness screenshots "
                          "carry PERCEPTUAL EVIDENCE; the manifest restates: "
                          "proof of intake, NOT physics verification.",
                "manifest": "tools/science_funnel/validation/"
                            "visual_proof_20260917/manifest.json records input "
                            "sha256 -> png sha256 for every render, the draco "
                            "decode section (glb sha, draco header facts, "
                            "decoded buffer sha256s, counts, screenshot sha), "
                            "any recorded refusals, and producer identities; "
                            "no render exists outside the chain.",
                "owned_files": [
                    "tools/science_funnel/visual_proof.py",
                    "tools/science_funnel/tests/test_visual_proof.py",
                    "tools/science_funnel/validation/visual_proof_20260917/",
                    "tools/science_funnel/data/smithsonian/draco_decode/",
                    "tools/science_funnel/validation/draco_decode_20260918/",
                    "tools/creature_graph/validation/admit_visual_proof_20260917.py",
                ],
            },
        },
        "falsifier": {
            "statement":
                "A render that is not reproducible byte-identically from the "
                "pinned inputs, or that survives a one-byte input flip with an "
                "unchanged PNG, is not a visual proof. A decode whose buffers "
                "do not reproduce identically on re-decode is not a machine "
                "identity. A decoded-geometry render from buffer bytes that do "
                "not match their recorded sha256, or from a GLB whose sha256 "
                "does not match the decode record, is not a visual proof. A "
                "corrupted GLB that still decodes silently is not a decoder.",
            "acceptance_test":
                "Decode every pinned GLB twice through the official WASM "
                "decoder (fresh decoder instances, separate passes) and require "
                "identical position/normal/index buffer hashes. Decode a "
                "one-byte-corrupted GLB copy and require a loud failure "
                "recorded as a refusal. The renderer verifies glb sha256 and "
                "all buffer sha256s before drawing geometry and refuses loudly "
                "on mismatch (falling back to the honest bbox render). Render "
                "every family twice under the pinned interpreter and require "
                "identical PNG bytes; flip exactly one byte of a pinned input "
                "and require the PNG hash to change or the renderer to refuse "
                "loudly; verify the manifest chain on disk.",
            "status": "untested",
        },
    },
]

CURRENT = REVISIONS[-1]
PRIOR = REVISIONS[:-1]


def main() -> int:
    raw = PROGRAM.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    objects = payload["objects"]
    existing = [o for o in objects if o.get("id") == OBJECT_ID]
    if existing:
        if existing[0] == CURRENT:
            print(f"{OBJECT_ID}: already at current revision (no-op)")
            return 0
        if existing[0] in PRIOR:
            objects[objects.index(existing[0])] = CURRENT
            out = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
            PROGRAM.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
            print(f"{OBJECT_ID}: superseded prior revision with current")
            return 0
        print(f"{OBJECT_ID}: REFUSAL -- exists with foreign content; "
              "graph policy is never silently overwritten", file=sys.stderr)
        return 1
    objects.append(CURRENT)
    out = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
    PROGRAM.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
    print(f"{OBJECT_ID}: admitted to {PROGRAM}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
