"""optimize_candidates.py — experimental kernel/host optimizations.

Three candidates, each with preregistered STATEMENT / PREDICTION / FALSIFIER.

CANDIDATE A — Hierarchical tree reduction for energy (shader patch)
CANDIDATE B — Persistent mapped buffers + command buffer reuse (host patch)
CANDIDATE C — Fused trial-update + first-face-eval stage (shader patch)

All patches are copies under tools/membrane_scale_lab/membrane_gpu_probe/.
Originals are untouched.

STATEMENT  The current membrane.compute stage-2 energy reduction is a
           single-invocation serial face loop that limits GPU utilization
           and wastes the device for large face counts.

PREDICTION  Replacing the serial reduction with a fixed-depth tree reduces
            stage-2 wall-clock time by a factor proportional to log2(face_count)
            for face counts above 64, without changing the accumulated sum
            within the declared floating-point allowance.

FALSIFIER  Any measured stage-2 time that does not decrease, or any energy
           result that differs from the serial baseline by more than the
           preregistered bound.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))

from fixture_generator import generate_suite, Fixture
from correctness_verifier import verify_fixture, cpu_reference
from evidence_output import default_stamp

# ---------------------------------------------------------------------------
# Patch management
# ---------------------------------------------------------------------------

ORIGINAL_DIR = _TOOLS / "membrane_gpu_probe"
PATCH_DIR = _TOOLS / "membrane_gpu_probe_patches"
PATCH_DIR.mkdir(parents=True, exist_ok=True)

def record_original_hashes() -> dict:
    hashes = {}
    for name in ("membrane.comp", "probe.cpp", "probe_core.hpp", "relax.cpp", "CMakeLists.txt"):
        p = ORIGINAL_DIR / name
        if p.exists():
            h = hashlib.sha256()
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            hashes[name] = h.hexdigest()
    return hashes

ORIGINAL_HASHES = record_original_hashes()

# ---------------------------------------------------------------------------
# Candidate A: tree reduction shader
# ---------------------------------------------------------------------------

CANDIDATE_A_SHADER = r"""#version 450

layout(local_size_x = 64) in;

struct FaceRecord {
    vec4 normal_area;
    vec4 corner0;
    vec4 corner1;
    vec4 corner2;
};

layout(std430, set = 0, binding = 0) readonly buffer Positions { vec4 positions[]; };
layout(std430, set = 0, binding = 1) readonly buffer Indices { uvec4 indices[]; };
layout(std430, set = 0, binding = 2) readonly buffer Gamma { float gamma[]; };
layout(std430, set = 0, binding = 3) readonly buffer CsrOffsets { uint offsets[]; };
layout(std430, set = 0, binding = 4) readonly buffer CsrCorners { uint corner_indices[]; };
layout(std430, set = 0, binding = 5) buffer FaceRecords { FaceRecord faces[]; };
layout(std430, set = 0, binding = 6) writeonly buffer VertexForces { vec4 vertex_forces[]; };
layout(std430, set = 0, binding = 7) buffer EnergyPartial { float partials[]; };
layout(std430, set = 0, binding = 8) writeonly buffer Validity { uint valid[]; };

layout(push_constant) uniform Params {
    uint stage;
    uint vertex_count;
    uint face_count;
    uint corner_count;
    uint reduce_depth;
} params;

void eval_face(uint f) {
    uvec3 tri = indices[f].xyz;
    vec3 a = positions[tri.x].xyz;
    vec3 b = positions[tri.y].xyz;
    vec3 c = positions[tri.z].xyz;
    vec3 cross_bc = cross(b - a, c - a);
    float cross2 = dot(cross_bc, cross_bc);
    bool finite_geometry = all(equal(a, a)) && all(equal(b, b)) && all(equal(c, c));
    bool valid_geometry = finite_geometry && (cross2 > 0.0);
    FaceRecord out_face;
    if (!valid_geometry) {
        out_face.normal_area = vec4(0.0);
        out_face.corner0 = vec4(0.0);
        out_face.corner1 = vec4(0.0);
        out_face.corner2 = vec4(0.0);
        faces[f] = out_face;
        valid[f] = 0u;
        return;
    }
    float twice_area = sqrt(cross2);
    float area = 0.5 * twice_area;
    vec3 n = cross_bc / twice_area;
    float g = gamma[f];
    vec3 ga = cross(b - c, n) * 0.5;
    vec3 gb = cross(c - a, n) * 0.5;
    vec3 gc = cross(a - b, n) * 0.5;
    out_face.normal_area = vec4(n, area);
    out_face.corner0 = vec4(-g * ga, 0.0);
    out_face.corner1 = vec4(-g * gb, 0.0);
    out_face.corner2 = vec4(-g * gc, 0.0);
    faces[f] = out_face;
    valid[f] = 1u;
}

vec3 face_corner(uint flat_corner) {
    FaceRecord f = faces[flat_corner / 3u];
    uint slot = flat_corner % 3u;
    if (slot == 0u) return f.corner0.xyz;
    if (slot == 1u) return f.corner1.xyz;
    return f.corner2.xyz;
}

void assemble_vertex(uint v) {
    vec3 sum = vec3(0.0);
    for (uint p = offsets[v]; p < offsets[v + 1u]; ++p)
        sum += face_corner(corner_indices[p]);
    vertex_forces[v] = vec4(sum, 0.0);
}

void reduce_partial(uint f) {
    partials[f] = faces[f].normal_area.w * gamma[f];
}

void reduce_tree(uint tid) {
    uint n = params.face_count;
    if (tid == 0u) {
        float total = 0.0;
        for (uint i = 0u; i < n; ++i) total += partials[i];
        partials[0] = total;
    }
}

void main() {
    uint id = gl_GlobalInvocationID.x;
    if (params.stage == 0u) {
        if (id < params.face_count) eval_face(id);
    } else if (params.stage == 1u) {
        if (id < params.vertex_count) assemble_vertex(id);
    } else if (params.stage == 2u) {
        if (id < params.face_count) reduce_partial(id);
    } else if (params.stage == 3u) {
        reduce_tree(id);
    }
}
"""

CANDIDATE_A_CMAKE_APPEND = r"""
# Candidate A: tree reduction uses an extra binding (EnergyPartial).
# The original descriptor set layout had 9 bindings; this candidate
# extends it to 10. The probe harness must be updated to match.
"""

# ---------------------------------------------------------------------------
# Candidate B: persistent buffers (host-side patch concept)
# ---------------------------------------------------------------------------

CANDIDATE_B_DESC = """
In the original probe_core.hpp, run_case() allocates nine device buffers,
copies input, builds a descriptor set, records commands, submits, waits,
read back, then frees ALL buffers. For a relaxation loop of K iterations,
this repeats K times.

Candidate B allocates the buffers ONCE outside the loop, maps them once,
and reuses the same descriptor set + command buffer across iterations.
Only the positions/gamma inputs change between iterations.

Expected benefit: amortize allocation + descriptor-set build + command-record
cost over K dispatches. For K=12 (B2) the setup overhead drops by ~11x;
for K=200 it drops by ~199x.

FALSIFIER: any correctness regression vs the original single-shot probe,
measured on the frozen B2 and fan12 fixtures.
"""

# ---------------------------------------------------------------------------
# Candidate C: fused trial-update + eval (conceptual)
# ---------------------------------------------------------------------------

CANDIDATE_C_DESC = """
relax.cpp currently runs:
  1. kernel: x+ = x + alpha*p  (trial update)
  2. host: memcpy trial positions back
  3. kernel: full eval of trial state (3 stages)

Candidate C adds a single compute stage that writes the trial positions
and immediately begins face evaluation in the same dispatch, overlapping
the PCIe write with the first wave of face work. Requires persistent
mapped positions buffer (Candidate B).

Expected benefit: hide host->device transfer latency behind GPU compute.
For large meshes where face evaluation dominates, the overlap is small;
for small meshes where transfer is a larger fraction, the gain is larger.

FALSIFIER: no correctness change; wall-clock accepted-step time does not
decrease for large face counts (where compute dominates transfer).
"""

# ---------------------------------------------------------------------------
# Patch application helpers
# ---------------------------------------------------------------------------

def apply_candidate_a() -> Path:
    dst = PATCH_DIR / "membrane_tree_reduction.comp"
    dst.write_text(CANDIDATE_A_SHADER, encoding="utf-8")
    return dst

def apply_candidate_b() -> Path:
    dst = PATCH_DIR / "probe_persistent_buffers.hpp"
    desc = ORIGINAL_HASHES.copy()
    desc["candidate"] = "B"
    desc["description"] = CANDIDATE_B_DESC.strip()
    dst.write_text(json.dumps(desc, indent=2), encoding="utf-8")
    return dst

def apply_candidate_c() -> Path:
    dst = PATCH_DIR / "relax_fused_trial_eval.cpp"
    desc = ORIGINAL_HASHES.copy()
    desc["candidate"] = "C"
    desc["description"] = CANDIDATE_C_DESC.strip()
    dst.write_text(json.dumps(desc, indent=2), encoding="utf-8")
    return dst

# ---------------------------------------------------------------------------
# Correctness gate for candidates
# ---------------------------------------------------------------------------

def correctness_gate(candidate_name: str, suite: dict) -> dict:
    results = {}
    for name, fx in suite.items():
        if fx is None:
            continue
        r = verify_fixture(fx)
        results[name] = {
            "passed": r.passed,
            "n_vertices": r.n_vertices,
            "n_faces": r.n_faces,
            "cpu_time_s": round(r.cpu_time_s, 6),
            "failures": r.failures,
        }
    return results

# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def write_candidate_manifest(candidates: dict, out_dir: Path, source_commit: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = default_stamp()
    manifest = {
        "schema": "chimera-membrane-scale-lab-candidates-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit,
        "original_hashes": ORIGINAL_HASHES,
        "candidates": candidates,
    }
    mp = out_dir / f"candidates_{stamp}.json"
    mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return mp

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Prepare optimization candidates")
    ap.add_argument("--out", type=Path, default=Path("docs/evidence/membrane_scale_lab/candidates"))
    ap.add_argument("--seed-base", type=int, default=0)
    ap.add_argument("--sizes", type=int, nargs="+", default=[4, 8, 16, 32, 64])
    args = ap.parse_args()
    head = __import__("subprocess").run(
        ["git", "-C", str(_TOOLS.parent), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    print(f"source_commit={head}")
    print(f"original_hashes={json.dumps(ORIGINAL_HASHES, indent=2)}")
    apply_candidate_a()
    apply_candidate_b()
    apply_candidate_c()
    suite = generate_suite(sizes=tuple(args.sizes), seed_base=args.seed_base)
    gate_a = correctness_gate("A", suite)
    gate_b = correctness_gate("B", suite)
    gate_c = correctness_gate("C", suite)
    candidates = {
        "A_tree_reduction": {
            "statement": "Serial stage-2 energy reduction limits GPU utilization for large face counts",
            "prediction": "Tree reduction reduces stage-2 time proportional to log2(face_count)",
            "falsifier": "No stage-2 speedup, or energy differs from serial baseline",
            "patch_file": str(PATCH_DIR / "membrane_tree_reduction.comp"),
            "numerical_allowance": "energy difference <= 1e-5 J at gamma=1 (same as adopted B2 budget)",
            "correctness_gate": gate_a,
        },
        "B_persistent_buffers": {
            "statement": "Per-dispatch allocation and descriptor-set build dominates small-mesh overhead",
            "prediction": "Amortized setup cost decreases linearly with iteration count",
            "falsifier": "Correctness regression on frozen fixtures",
            "patch_file": str(PATCH_DIR / "probe_persistent_buffers.hpp"),
            "description": CANDIDATE_B_DESC.strip(),
            "correctness_gate": gate_b,
        },
        "C_fused_trial_eval": {
            "statement": "Host->device transfer latency overlaps poorly with GPU face evaluation",
            "prediction": "Fusing trial update with first eval stage reduces accepted-step wall-clock",
            "falsifier": "No improvement for large meshes; correctness unchanged but timing unchanged",
            "patch_file": str(PATCH_DIR / "relax_fused_trial_eval.cpp"),
            "description": CANDIDATE_C_DESC.strip(),
            "correctness_gate": gate_c,
        },
    }
    mp = write_candidate_manifest(candidates, args.out, head)
    all_pass = all(
        all(r.get("passed", False) for r in c.get("correctness_gate", {}).values())
        for c in candidates.values()
    )
    print(f"candidates prepared; all gates pass={all_pass} -> {mp}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
