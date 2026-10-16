"""composed_patch.py -- P5 COMPOSITION: two qualified fan patches joined into
one assembly, solved by the SAME reference law (§11.18 P5: "Join two pieces,
then reuse the same artifact in a second assembly and supported scale").

NO NEW PHYSICS. Both pieces are the lab's own high_degree_fan fixtures; the
reference for the composed artifact is ONE pe.solve_equilibrium on the joined
mesh (connectivity union, seam deduplicated) -- the identical qualified
boundary/load solve of patch_equilibrium.py, applied to a bigger connectivity.

ASSEMBLY (apex-weld hourglass; see composed_patch_checks.py check (g) for the
witnessed topology law that forces this weld face):
  piece A  high_degree_fan(n_rim=200, radius=1.0, height=0.3): rim ring at
           z=0 PINNED (the piece's qualified boundary), apex UP at z=0.3 --
           the SEAM vertex, free, carrying the INPUT PORT (vertical dead
           load, within the packet's 2.0 N force domain).
  piece B  high_degree_fan(n_rim=200, radius=0.8, height=0.3), INVERTED by
           reflection of the placement about the seam plane z=hA (winding
           restored): its apex hangs DOWN onto the seam (shared vertex) and
           its FAR RIM at z=0.6 is PINNED -- the OUTPUT PORT.
  The two films form an hourglass meeting only at the seam: A's film pulls
  the seam toward A's rim plane, B's film pulls it toward B's rim plane, the
  load pulls it down -- a genuinely coupled interior equilibrium (measured
  seam height ~0.14 wu at unit scale), NOT two solves glued together.

SEAM OWNERSHIP (recorded in the receipt): A OWNS the seam vertex list (the
apex index lives in A's vertex block); B REFERENCES it (B's apex vertex is
deduplicated onto A's index; B's faces carry A's index). A seam claim whose
declared coordinates disagree with the owner's is refused BY NAME before any
solve (seam_vertex_coordinate_mismatch), as is a second ownership claim
(seam_owner_conflict).

TOPOLOGY LAW (witnessed, not assumed -- composed_patch_checks.py (g)):
  under the constant-gamma CURRENT-area law every film contracts a free
  boundary (line tension gamma; the packet's own exclusion), so a rim-to-rim
  weld with a FREE seam ring has NO equilibrium (measured: step_limit,
  free residual 1.08), and a rim-to-rim weld onto a PINNED (grounded) ring
  transmits NOTHING into the second piece (measured: B-port delta 0.0
  bit-for-bit). The apex weld is the topology in which the seam is a free
  INTERIOR vertex whose opposing film pulls balance: equilibrium AND real
  port transfer coexist.

SUPPORTED SCALE: the whole assembly is rigidly scaled by s in {1.0, 0.5,
2.0} -- the packet's physical-size axis (0.5-2.0 m at unit gamma); the
resolution axis (n_rim) is untouched. The load stays at the same Newton
magnitude (<= packet max_force_N): balance is a law, not a size.

RECEIPT: schema chimera-mechanism-factory-composed-qualification-v1 (the case
shape differs from the single-piece v2 receipt: composed family, composition/
ownership record, per-scale cases), verified by the SAME receipt_adapter
(extended explicitly, versioned) against the SAME packet thresholds (the
preregistered 1e-6 balance/free-residual law). Evidence via the lab's
resolve_evidence_path (never silently overwritten; exit 2 on exists).

Units follow the packet: positions [wu==m], gamma [J/wu^2], forces N.
CPU only; numpy + stdlib; no engine, no GPU, no network, no LLM calls.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent            # tools/mechanism_factory
_REPO = _HERE.parent.parent                       # PythonChimera/
_TOOLS = _HERE.parent                             # tools/
_LAB = _TOOLS / "membrane_scale_lab"
for _p in (str(_TOOLS), str(_LAB), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import patch_equilibrium as pe                    # noqa: E402  the qualified solve
import fixture_generator as fg                    # noqa: E402  lab fixtures
from surface_energy_reference import (            # noqa: E402
    InvalidSurface, RejectionReason)
from evidence_output import (                     # noqa: E402
    EvidencePathExists, resolve_evidence_path)

EVID_DIR = _REPO / "docs" / "evidence" / "mechanism_factory"
PACKET_PATH = _HERE / "example_packet.json"

COMPOSED_RECEIPT_SCHEMA = "chimera-mechanism-factory-composed-qualification-v1"
COMPOSED_FAMILY = "composed-apex-weld-hourglass"

# Files whose sha256 the composed receipt records (the law/solve/fixture
# owners, the adapter that verifies this schema, and this artifact+battery).
HASHED_SOURCES = [
    "tools/membrane_scale_lab/surface_energy_reference.py",
    "tools/membrane_scale_lab/overdamped_descent.py",
    "tools/membrane_scale_lab/fixture_generator.py",
    "tools/mechanism_factory/patch_equilibrium.py",
    "tools/mechanism_factory/qualification_receipt.py",
    "tools/mechanism_factory/receipt_adapter.py",
    "tools/mechanism_factory/composed_patch.py",
    "tools/mechanism_factory/composed_patch_checks.py",
]


class ComposedRejectionReason:
    """Named refusals of the composition seam (raised as the law's own
    InvalidSurface so the refusal convention is uniform end to end)."""
    SEAM_VERTEX_COORDINATE_MISMATCH = "seam_vertex_coordinate_mismatch"
    SEAM_OWNER_CONFLICT = "seam_owner_conflict"
    SEAM_REFERENCE_MISSING = "seam_reference_missing"
    UNSUPPORTED_SCALE = "unsupported_scale"


# ── frozen assembly parameters (before any run; the checks read THESE) ──────
PIECE_A = {"n_rim": 200, "radius": 1.0, "height": 0.3, "seed": 1}
PIECE_B = {"n_rim": 200, "radius": 0.8, "height": 0.3, "seed": 2}
SEAM_LOAD_N = (0.0, 0.0, -0.8)          # input port: vertical dead load, <=2.0 N
SUPPORTED_SCALES = (1.0, 0.5, 2.0)      # packet scale axis; resolution untouched
MAX_STEPS = 60000                       # same budget law as qualification_receipt
SEAM_COORD_TOL = 1.0e-12                # owner/reference coordinate agreement


@dataclass
class Assembly:
    """A joined two-piece mesh with recorded seam ownership and ports."""
    positions: np.ndarray               # (nV,3) rest coords [wu]
    faces: np.ndarray                   # (m,3) int64, both films' triangles
    gamma: np.ndarray                   # (m,) uniform J/wu^2
    pins: list                          # A rim + B far rim (all pinned)
    loads: list                         # input port: [(seam_index, f)]
    seam_index: int
    seam_record: dict                   # ownership / reference / position
    block_a: list                       # piece A rim pin indices (near port)
    block_b: list                       # piece B far-rim pin indices (output)
    placement: dict                     # frozen placement record (audit)
    scale: float

    @property
    def seam_position(self) -> np.ndarray:
        return self.positions[self.seam_index]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(_REPO), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=30, check=True)
        return out.stdout.strip() or "UNTRACKED"
    except Exception:                                 # pragma: no cover
        return "UNTRACKED"


def _check_scale(scale: float) -> None:
    packet = json.loads(PACKET_PATH.read_bytes())
    lo = packet["admitted_domain"]["scales"]["min_m"]
    hi = packet["admitted_domain"]["scales"]["max_m"]
    if not (lo <= float(scale) <= hi):
        raise InvalidSurface(
            ComposedRejectionReason.UNSUPPORTED_SCALE,
            f"scale {scale} outside the packet's supported physical-size "
            f"axis [{lo}, {hi}] m; refusing to invent an unsupported scale")


def build_assembly(scale: float = 1.0,
                   piece_a: dict = PIECE_A, piece_b: dict = PIECE_B,
                   load: tuple = SEAM_LOAD_N,
                   seam_perturbation: tuple | None = None) -> Assembly:
    """Join two high_degree_fan pieces at the apex weld with named seam
    refusals BEFORE any solve. seam_perturbation shifts piece B's seam CLAIM
    off the owner's coordinates (the (e) falsifier); None is the genuine
    assembly."""
    _check_scale(scale)
    n_a, n_b = piece_a["n_rim"], piece_b["n_rim"]
    h_a = piece_a["height"]

    fa = fg.high_degree_fan(seed=piece_a["seed"], **{
        k: piece_a[k] for k in ("n_rim", "radius", "height")})
    fb = fg.high_degree_fan(seed=piece_b["seed"], **{
        k: piece_b[k] for k in ("n_rim", "radius", "height")})
    assert fa.stats.valid and fb.stats.valid, "fixture validator refused"

    VA, FAx = fa.positions.copy(), fa.faces.copy()
    VB, FBx = fb.positions.copy(), fb.faces.copy()
    # piece B placement: INVERTED by reflection about the seam plane z=h_a.
    # Its apex lands on the seam (2h_a - h_b == h_a iff h_b == h_a, frozen);
    # its far rim lands at z=2h_a. Reflection flips winding -> restore it.
    VB[:, 2] = 2.0 * h_a - VB[:, 2]
    FBx = FBx[:, [0, 2, 1]].copy()
    b_apex_local = n_b

    # ── seam claims, BEFORE any solve ───────────────────────────────────────
    # A owns the seam vertex (its apex). B declares a REFERENCE: the vertex
    # it wants to weld onto, with the coordinates it believes that vertex
    # has. Mismatched coordinates or a second ownership claim are refused.
    a_claim = {"role": "owner", "local_index": n_a,
               "position": VA[n_a].copy()}
    b_claim = {"role": "reference", "local_index": b_apex_local,
               "position": VB[b_apex_local].copy()}
    if seam_perturbation is not None:
        b_claim["position"] = b_claim["position"] + np.asarray(
            seam_perturbation, dtype=np.float64)
    owners = [c for c in (a_claim, b_claim) if c["role"] == "owner"]
    if len(owners) != 1:
        raise InvalidSurface(
            ComposedRejectionReason.SEAM_OWNER_CONFLICT,
            f"seam ownership must be single-valued: {len(owners)} owner "
            f"claims (A and/or B); refusing duplicate ownership")
    owner = owners[0]
    refs = [c for c in (a_claim, b_claim) if c["role"] == "reference"]
    for ref in refs:
        d = float(np.linalg.norm(ref["position"] - owner["position"]))
        if not (d <= SEAM_COORD_TOL):
            raise InvalidSurface(
                ComposedRejectionReason.SEAM_VERTEX_COORDINATE_MISMATCH,
                f"seam reference claims position {ref['position'].tolist()} "
                f"but the owner holds {owner['position'].tolist()} "
                f"(||delta|| = {d:.3e} > {SEAM_COORD_TOL:.0e}); refusing "
                f"overlapping duplicate seam vertices before any solve")

    # ── join: connectivity union, seam deduplicated (B's apex dropped) ─────
    V = np.vstack([VA, VB[:n_b]])                  # A block, then B's rim
    seam_index = n_a                               # A's apex = the seam
    FB = FBx.copy()
    FB[FB == b_apex_local] = seam_index            # B references A's vertex
    FB[FB < n_b] += (n_a + 1)                      # B's rim -> its own block
    F = np.vstack([FAx, FB])
    gamma = np.ones(F.shape[0], dtype=np.float64)
    pins = list(range(n_a)) + list(range(n_a + 1, n_a + 1 + n_b))
    loads = [(seam_index, tuple(load))]

    # the joined mesh must satisfy the law's own validator immediately
    ev_ok = True
    try:
        pe.total_force(V, F, gamma, np.zeros((V.shape[0], 3)))
    except InvalidSurface:
        ev_ok = False
    assert ev_ok, "joined mesh refused by the law's validator"

    # SUPPORTED SCALE: rigid physical-size scaling of the WHOLE assembly
    # (the packet's size axis; the resolution axis -- n_rim -- is untouched,
    # and the load keeps its Newton magnitude: balance is a law, not a size)
    if float(scale) != 1.0:
        V = V * float(scale)

    return Assembly(
        positions=V, faces=F, gamma=gamma, pins=pins, loads=loads,
        seam_index=seam_index,
        seam_record={
            "index": seam_index,
            "owner": "piece A (apex index lives in A's vertex block)",
            "referenced_by": ["piece B (apex vertex deduplicated onto "
                              "A's index; B's faces carry A's index)"],
            "position": [float(v) for v in V[seam_index]],
            "incident_faces": int((F == seam_index).sum()),
            "coordinate_tol": SEAM_COORD_TOL,
        },
        block_a=list(range(n_a)),
        block_b=list(range(n_a + 1, n_a + 1 + n_b)),
        placement={
            "piece_a": {"fixture": "fixture_generator.high_degree_fan",
                        **piece_a, "placement": "identity (rim z=0 pinned, "
                        "apex UP at z=height: seam)"},
            "piece_b": {"fixture": "fixture_generator.high_degree_fan",
                        **piece_b, "placement": "reflected about the seam "
                        "plane z=height (INVERTED: apex hangs down onto the "
                        "seam, far rim at z=2*height), face winding restored",
                        "far_rim_z": 2.0 * piece_b["height"]},
            "weld": "apex-to-apex (see module docstring: free rim rings "
                    "have no equilibrium under this law and grounded ring "
                    "welds transfer nothing -- witnessed in check (g))",
        },
        scale=float(scale))


def solve_assembly(asm: Assembly, max_steps: int = MAX_STEPS) -> dict:
    """THE reference: ONE solve_equilibrium on the joined mesh (connectivity
    union, seam deduplicated) -- the qualified boundary/load solve, not a
    piecewise surrogate. Returns the result plus the coupled metrics."""
    r = pe.solve_equilibrium(asm.positions, asm.faces, asm.gamma, asm.pins,
                             asm.loads, max_steps=max_steps)
    R = np.asarray(r.reaction_forces, dtype=np.float64)
    fsum = np.zeros(3)
    for _i, v in asm.loads:
        fsum += np.asarray(v, dtype=np.float64)
    force_res = float(np.linalg.norm(R.sum(axis=0) + fsum))
    x = r.positions
    mom = np.zeros(3)
    for k, i in enumerate(r.fixed_indices):
        mom += np.cross(x[i], R[k])
    for i, v in asm.loads:
        mom += np.cross(x[i], np.asarray(v, dtype=np.float64))
    moment_res = float(np.linalg.norm(mom))
    rn = np.linalg.norm(R, axis=1)
    blocks = {
        "A_rim_near_load": float(rn[:len(asm.block_a)].mean()),
        "B_far_rim_output": float(rn[len(asm.block_a):].mean()),
    }
    port_force_b = R[len(asm.block_a):].sum(axis=0)     # output-port net force
    return {"result": r, "reactions": R,
            "force_balance_residual": force_res,
            "moment_balance_residual": moment_res,
            "block_mean_reaction_norms": blocks,
            "output_port_net_force_norm": float(np.linalg.norm(port_force_b)),
            "seam_height": float(x[asm.seam_index, 2])}


def reduction_case(piece: dict = PIECE_B) -> dict:
    """Piece B UNLOADED, A absent: the inverted placement with the far rim
    pinned and the (former seam) apex free under zero load degenerates to the
    qualified single-piece zero-load behavior (it flattens onto its rim
    plane). Control: the SAME fan without the placement. Mirror symmetry of
    the law => identical final energy (measured: dE = 0.0)."""
    fb = fg.high_degree_fan(seed=piece["seed"], **{
        k: piece[k] for k in ("n_rim", "radius", "height")})
    n = piece["n_rim"]
    h = piece["height"]
    VB = fb.positions.copy()
    VB[:, 2] = 2.0 * h - VB[:, 2]                  # same inverted placement
    FB = fb.faces[:, [0, 2, 1]].copy()             # winding restored
    g = np.ones(FB.shape[0], dtype=np.float64)
    r_inv = pe.solve_equilibrium(VB, FB, g, list(range(n)), [],
                                 max_steps=MAX_STEPS)
    r_ref = pe.solve_equilibrium(fb.positions, fb.faces, fb.gamma,
                                 list(range(n)), [], max_steps=MAX_STEPS)
    return {"inverted": r_inv, "reference": r_ref,
            "energy_delta": abs(r_inv.energy - r_ref.energy),
            "inverted_apex_rest_on_rim_plane":
                abs(r_inv.positions[n, 2] - 2.0 * h),
            "reference_apex_rest_on_rim_plane":
                abs(r_ref.positions[n, 2])}


def witness_free_ring(n_rim: int = 60) -> dict:
    """TOPOLOGY WITNESS: the literal rim-to-rim weld (shared ring left FREE)
    has NO equilibrium under this law -- every film contracts a free boundary
    (the packet's own exclusion, at assembly scale). Never stationary."""
    fa = fg.high_degree_fan(n_rim=n_rim, radius=1.0, height=0.3, seed=1)
    fb = fg.high_degree_fan(n_rim=n_rim, radius=1.0, height=0.3, seed=2)
    VB = fb.positions.copy()
    VB[:, 2] = -VB[:, 2]                           # B inverted below the ring
    V = np.vstack([fa.positions, [VB[n_rim]]])     # ring shared, B apex added
    FB = fb.faces.copy()
    FB[FB == n_rim] = n_rim + 1
    F = np.vstack([fa.faces, FB])
    g = np.ones(F.shape[0], dtype=np.float64)
    pins = list(range(n_rim)) + [n_rim + 1]        # ring FREE, B apex pinned
    try:
        r = pe.solve_equilibrium(V, F, g, pins,
                                 [(n_rim, (0.0, 0.0, -0.8))],
                                 max_steps=2000)
        return {"status": r.status, "free_residual": r.free_residual,
                "steps": r.n_accepted}
    except InvalidSurface as ex:                   # gate refusal is honest too
        return {"status": f"refused:{ex.reason}", "free_residual": float("nan"),
                "steps": 0}


def witness_pinned_ring(n_rim: int = 60) -> dict:
    """TOPOLOGY WITNESS: the rim-to-rim weld onto a GROUNDED (pinned) seam
    ring transmits NOTHING into piece B: with vs without piece A's load,
    piece B's far-rim (apex) pin reaction is IDENTICAL -- a superposition,
    not a coupled assembly."""
    fa = fg.high_degree_fan(n_rim=n_rim, radius=1.0, height=0.3, seed=1)
    fb = fg.high_degree_fan(n_rim=n_rim, radius=1.0, height=0.3, seed=2)
    VB = fb.positions.copy()
    VB[:, 2] = -VB[:, 2]
    V = np.vstack([fa.positions, [VB[n_rim]], fb.positions[:n_rim]])
    FB = fb.faces.copy()
    FB[FB == n_rim] = n_rim + 1                    # B apex pin
    FB[FB < n_rim] += (n_rim + 2)                  # B rim -> grounded copies
    F = np.vstack([fa.faces, FB])
    g = np.ones(F.shape[0], dtype=np.float64)
    pins = (list(range(n_rim)) + [n_rim + 1]
            + list(range(n_rim + 2, n_rim + 2 + n_rim)))
    kw = dict(max_steps=20000)
    r_on = pe.solve_equilibrium(V, F, g, pins, [(n_rim, (0.0, 0.0, -0.8))],
                                **kw)
    r_off = pe.solve_equilibrium(V, F, g, pins, [], **kw)
    i_b = r_on.fixed_indices.index(n_rim + 1)
    d = float(np.linalg.norm(
        np.asarray(r_on.reaction_forces)[i_b]
        - np.asarray(r_off.reaction_forces)[i_b]))
    return {"status_with_load": r_on.status, "status_no_load": r_off.status,
            "b_port_reaction_delta": d}


# ── composed receipt (schema chimera-mechanism-factory-composed-qualification-
#    v1; verified by receipt_adapter against the SAME packet thresholds) ─────

def _compose_case(asm: Assembly, solved: dict, thr: dict) -> dict:
    r = solved["result"]
    return {
        "case_id": f"{COMPOSED_FAMILY}_scale{asm.scale:g}",
        "family": COMPOSED_FAMILY,
        "status": r.status,
        "outputs": {
            "energy_J": float(r.energy),
            "max_free_residual_N": float(r.free_residual),
            "reactions_N": [[float(v) for v in row]
                            for row in solved["reactions"]],
            "max_force_balance_residual": solved["force_balance_residual"],
            "max_moment_balance_residual": solved["moment_balance_residual"],
            "scale_m": asm.scale,
            "n_rim_per_piece": len(asm.block_a),
            "seam_height_wu": solved["seam_height"],
            "block_mean_reaction_norms_N": solved["block_mean_reaction_norms"],
            "output_port_net_force_N": solved["output_port_net_force_norm"],
        },
        "gpu_job": None,
    }


def _recomputed_pass(cases: list, thr: dict) -> bool:
    allowed = {"stationary", "stagnated"}
    for c in cases:
        if c["status"] not in allowed:
            return False
        out = c["outputs"]
        if out["max_free_residual_N"] > thr["max_free_residual_N"]:
            return False
        if out["max_force_balance_residual"] > thr["max_force_balance_residual"]:
            return False
        if out["max_moment_balance_residual"] > thr["max_moment_balance_residual"]:
            return False
    return True


def composition_record() -> dict:
    return {
        "what": "P5 composition: two qualified high_degree_fan patches "
                "joined into one assembly; reference = ONE solve_equilibrium "
                "on the joined mesh (connectivity union, seam deduplicated); "
                "no new physics",
        "pieces": {"A": dict(PIECE_A, port_in="vertical dead load at the "
                             "seam apex (rim pinned)", placement="identity"),
                   "B": dict(PIECE_B, port_out="reactions at the far rim "
                             "pins (rim pinned)", placement="inverted "
                             "(reflected about the seam plane)")},
        "seam": {
            "vertices": [PIECE_A["n_rim"]],
            "owner": "piece A",
            "referenced_by": ["piece B"],
            "weld": "apex-to-apex hourglass; the seam is a free INTERIOR "
                    "vertex whose opposing film pulls balance (real port "
                    "transfer). Rim-ring welds are structurally impossible "
                    "under this law: a free ring has no equilibrium (film "
                    "contraction, the packet's own exclusion) and a pinned "
                    "ring transfers nothing -- both witnessed in "
                    "composed_patch_checks.py check (g)",
        },
        "ports": {"input": "vertical dead load (0.8 N <= packet "
                  "max_force_N) at the seam apex on piece A's side",
                  "output": "reactions at piece B's far rim pins"},
        "supported_scales_m": list(SUPPORTED_SCALES),
        "scale_axis": "packet physical-size axis (0.5-2.0 m at unit gamma); "
                      "resolution axis (n_rim) untouched",
        "topology_witnesses": {"free_seam_ring": "no equilibrium "
                               "(step_limit, free residual ~1e0)",
                               "pinned_seam_ring": "zero B-port transfer "
                               "(bit-identical reactions with/without load)"},
    }


def build_composed_receipt(cases: list) -> dict:
    packet_bytes = PACKET_PATH.read_bytes()
    packet = json.loads(packet_bytes)
    thr = packet["acceptance_thresholds"]
    ok = _recomputed_pass(cases, thr)
    return {
        "schema": COMPOSED_RECEIPT_SCHEMA,
        "utc": datetime.now(timezone.utc).isoformat(),
        "adapter_version": "adapter-v1",
        "source_commit": _source_commit(),
        "source_file_hashes": {
            rel: _sha256_file(_REPO / rel) for rel in HASHED_SOURCES
        },
        "packet_sha256": _sha256_bytes(packet_bytes),
        "units": packet["units"],
        "composition": composition_record(),
        "declared_verdict": {
            "verdict": "PASS" if ok else "FAIL",
            "recomputed_from": "packet acceptance_thresholds (the "
                               "preregistered 1e-6 balance/free-residual "
                               "law); composed schema adds no thresholds",
        },
        "cases": cases,
    }


def compose_all_scales() -> tuple:
    """Solve the assembly at every supported scale; fail honestly (exit 1
    law lives in main) if any case violates the packet's thresholds."""
    packet = json.loads(PACKET_PATH.read_bytes())
    thr = packet["acceptance_thresholds"]
    cases, failures = [], []
    for scale in SUPPORTED_SCALES:
        asm = build_assembly(scale=scale)
        solved = solve_assembly(asm)
        c = _compose_case(asm, solved, thr)
        ok = (c["status"] in {"stationary", "stagnated"}
              and c["outputs"]["max_free_residual_N"] <= thr["max_free_residual_N"]
              and c["outputs"]["max_force_balance_residual"]
              <= thr["max_force_balance_residual"]
              and c["outputs"]["max_moment_balance_residual"]
              <= thr["max_moment_balance_residual"])
        if not ok:
            failures.append(c["case_id"])
        print(f"{c['case_id']}: status={c['status']} "
              f"free_residual={c['outputs']['max_free_residual_N']:.3e} "
              f"force_bal={c['outputs']['max_force_balance_residual']:.3e} "
              f"moment_bal={c['outputs']['max_moment_balance_residual']:.3e} "
              f"seam_z={c['outputs']['seam_height_wu']:.4f} "
              f"blocks={c['outputs']['block_mean_reaction_norms_N']} -> "
              f"{'OK' if ok else 'FAIL'}")
        cases.append(c)
    return cases, failures


def write_composed_receipt(path: Path, cases: list) -> Path:
    receipt = build_composed_receipt(cases)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list) -> int:
    cases, failures = compose_all_scales()
    if failures:
        print(f"FAIL: threshold/status violation in: {', '.join(failures)}")
        return 1
    out_path = resolve_evidence_path(EVID_DIR, "composed_qualification_receipt",
                                     argv)
    write_composed_receipt(out_path, cases)
    print(f"receipt: {out_path}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except EvidencePathExists as exc:
        print(f"REFUSED: {exc}")
        sys.exit(2)
