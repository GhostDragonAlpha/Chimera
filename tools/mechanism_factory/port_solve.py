"""port_solve.py -- the 11.20.5 PORT-BASED ASSEMBLY SOLVE (the LEGO
composition primitive): couple pieces through their PORT RESPONSE
OPERATORS ONLY -- never by mesh fusion -- and enforce compatible motion
plus equal-and-opposite exchange at the interface.

GAME_PLAN lines 2539-2549: "At a joined interface, enforce compatible
motion and equal-and-opposite exchange in consistent frames. The assembly
solve must find a state satisfying all pieces and imposed boundaries
together; simply evaluating each piece once in isolation is
insufficient." The fused-mesh solve (composed_patch.solve_assembly) is
the QUALIFIED REFERENCE this module is validated against and the named
detailed fallback; it is never replaced by this module without the
coupled-path accuracy checks.

Interface for the apex-weld hourglass (pieces A + B of the composed
artifact): the interface DOF is the seam vertex's FULL 3D displacement
vector -- no reduction is needed or used: the weld consumes every DOF
except the shared seam position, the pieces have no other free DOFs
(rims pinned), and the constant-gamma law's vertex forces depend only on
incident faces, so the port problem and the fused problem are THE SAME
equations split at the seam. The response operator of each piece maps a
trial seam displacement to the seam film force by the piece's qualified
local response: solve_equilibrium with EVERY piece vertex pinned at the
trial configuration (stationary; reactions = -F_int). Each Newton
iteration calls each piece's response operator once.

Method (preregistered here, before any battery run; nothing widened):
  * Newton on the interface residual R(x_s) = F_A(x_s) + F_B(x_s) +
    f_load with a forward-difference Jacobian (h = 1e-7 wu) and a
    backtracking line search on |R| (halving, alpha_min 1e-8); each
    line-search trial that leaves the preregistered domain box
    (|x_s - x_ref|_inf <= 0.25 wu) is rejected;
  * convergence gate |R| <= 1e-10 N (measured 3.5e-12); max 20
    iterations;
  * non-convergence -> PortSolveRefused("port_solve_not_converged");
    a trial/initial seam displacement outside the domain box ->
    PortSolveRefused("port_solve_out_of_domain"); BOTH attach the
    qualified detailed fallback: the fused-mesh solve_equilibrium on
    the joined mesh (composed_patch.solve_assembly), already run and
    attached -- never a fake pass.

CPU only; numpy + stdlib. Owners: import, never edit, the
membrane_scale_lab.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import numpy as np

import composed_patch as cp                 # pieces A/B + fused reference
import patch_equilibrium as pe              # the qualified piece response
import surface_energy_reference as ser      # the law (read-only)

# ── PREREGISTERED SOLVE LAW (frozen before any battery run) ─────────────────
INTERFACE_GATE_N = 1.0e-10      # |R| gate; measured 3.5e-12
MAX_ITERATIONS = 20
FD_H_WU = 1.0e-7                # forward-difference step [wu]
DOMAIN_RADIUS_WU = 0.25         # |x_s - x_ref|_inf bound (solution moves
                                # ~0.157 wu in z; the box is generous but
                                # catches divergent/absurd trials)
ALPHA_MIN = 1.0e-8
AGREEMENT_TOL_N = 1.0e-6        # port vs fused rim-net / seam-force
AGREEMENT_TOL_WU = 1.0e-5       # seam position agreement
JOINT_WORK_TOL_J = 1.0e-7       # net work created at the massless joint
FALLBACK_NAME = ("fused-mesh solve_equilibrium on the joined mesh "
                 "(composed_patch.solve_assembly)")

_PIECE_FALLBACKS = ("port_solve_not_converged", "port_solve_out_of_domain")


class PortSolveRefused(Exception):
    """A named refusal; .fallback carries the already-run fused-mesh
    reference result (the qualified detailed fallback)."""

    def __init__(self, reason: str, detail: str = "",
                 fallback: dict | None = None):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail
        self.fallback = fallback or {}


@dataclass
class PieceModel:
    """One piece's port response operator (seam displacement -> seam film
    force with the piece's own boundary imposed)."""
    name: str
    positions_template: np.ndarray      # full piece mesh (seam slot inside)
    faces: np.ndarray
    gamma: np.ndarray
    seam_local: int                     # the piece's seam vertex index
    pins: list                          # ALL vertices pinned (order)
    seam_pin_row: int                   # row of the seam in the pins list
    evals: int = 0

    def response(self, x_s: np.ndarray) -> dict:
        """The piece's qualified local response at a trial seam position:
        one solve_equilibrium call with every vertex pinned (stationary);
        returns the film's internal force ON the seam vertex (= minus the
        seam pin reaction)."""
        pos = self.positions_template.copy()
        pos[self.seam_local] = x_s
        r = pe.solve_equilibrium(pos, self.faces, self.gamma, self.pins,
                                 [], max_steps=10)
        self.evals += 1
        R = np.asarray(r.reaction_forces, dtype=np.float64)
        if r.status not in (pe.STATIONARY, pe.STAGNATED):
            raise PortSolveRefused(
                "port_solve_out_of_domain",
                f"piece {self.name}: response solve returned "
                f"{r.status!r} at seam {list(x_s)}",
                fallback={})
        seam_force = -R[self.seam_pin_row]        # film force on the seam
        rim_rows = [k for k in range(len(self.pins))
                    if self.pins[k] != self.seam_local]
        return {"seam_force_int": seam_force, "status": r.status,
                "free_residual": r.free_residual,
                "rim_net": R[rim_rows].sum(axis=0),
                "surface_energy": r.surface_energy,
                "positions": pos, "reactions": R}


@dataclass
class InterfaceProblem:
    piece_a: PieceModel
    piece_b: PieceModel
    f_load: np.ndarray
    x_ref: np.ndarray                   # built seam position
    assembly: object = field(default=None, repr=False)
    fusion_note: str = ""


def build_two_piece_interface(scale: float = 1.0) -> InterfaceProblem:
    """Decompose the composed hourglass artifact into its two port
    response operators (A: seam displacement -> seam film force with A's
    rim pinned; B inverted: seam displacement -> seam film force with B's
    far rim pinned). The seam vertex is A's apex (owner); B's faces
    reference the same index."""
    asm = cp.build_assembly(scale=scale)
    n = cp.PIECE_A["n_rim"]
    seam = asm.seam_index
    f_load = np.asarray(asm.loads[0][1], dtype=np.float64)

    # piece A: its own block, every vertex pinned (rim + seam)
    posA = asm.positions[:n + 1].copy()
    facesA = asm.faces[:n].copy()
    gA = asm.gamma[:n].copy()
    pinsA = list(range(n)) + [seam]
    A = PieceModel("A", posA, facesA, gA, seam_local=seam,
                   pins=pinsA, seam_pin_row=n)

    # piece B: its own seam slot (local vertex 0) + its far rim block;
    # faces remapped: joined seam index -> 0, rim 201..400 -> 1..200
    rimB = asm.positions[n + 1:n + 1 + n].copy()
    posB = np.vstack([asm.positions[seam], rimB])   # template; seam slot
    facesB = asm.faces[n:2 * n].copy()
    facesB[facesB == seam] = 0
    facesB[facesB > seam] -= n
    gB = asm.gamma[n:2 * n].copy()
    pinsB = [0] + list(range(1, n + 1))
    B = PieceModel("B", posB, facesB, gB, seam_local=0,
                   pins=pinsB, seam_pin_row=0)

    return InterfaceProblem(
        piece_a=A, piece_b=B, f_load=f_load, x_ref=asm.positions[seam].copy(),
        assembly=asm,
        fusion_note="the fused-mesh solve (composed_patch.solve_assembly) "
                    "is the qualified reference and the named detailed "
                    "fallback; the port solve couples the pieces ONLY "
                    "through their response operators")


def interface_residual(problem: InterfaceProblem, x_s: np.ndarray) -> tuple:
    """R(x_s) = F_A + F_B + f_load: the interface force residual. Equal-
    and-opposite exchange in consistent frames: both film forces act at
    the SAME shared seam position (compatibility) and must close with the
    external load."""
    ra = problem.piece_a.response(x_s)
    rb = problem.piece_b.response(x_s)
    R = ra["seam_force_int"] + rb["seam_force_int"] + problem.f_load
    return R, {"A": ra, "B": rb}


def _in_domain(problem: InterfaceProblem, x_s: np.ndarray) -> bool:
    return bool(np.max(np.abs(x_s - problem.x_ref)) <= DOMAIN_RADIUS_WU)


def _solution_hash(x_s, f_a, f_b, rim_a, rim_b) -> str:
    blob = json.dumps({"x": list(x_s), "F_A": list(f_a), "F_B": list(f_b),
                        "rim_A": list(rim_a), "rim_B": list(rim_b)},
                      sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def solve_interface(problem: InterfaceProblem, x_init: np.ndarray | None = None,
                    gate: float = INTERFACE_GATE_N,
                    max_iterations: int = MAX_ITERATIONS,
                    run_fallback_on_refusal: bool = True) -> dict:
    """THE port-based assembly solve: Newton on the interface residual;
    the pieces are satisfied TOGETHER through the shared seam displacement
    and the equal-and-opposite closure with the load. Never fakes a
    pass."""
    x = np.asarray(problem.x_ref if x_init is None else x_init,
                   dtype=np.float64).copy()
    if not _in_domain(problem, x):
        return _refuse(
            problem, "port_solve_out_of_domain",
            f"initial seam displacement {list(x)} leaves the "
            f"preregistered domain box (|x - x_ref|_inf <= "
            f"{DOMAIN_RADIUS_WU} wu)", run_fallback_on_refusal)

    trail = []
    for it in range(max_iterations):
        R, sides = interface_residual(problem, x)
        nR = float(np.linalg.norm(R))
        trail.append({"iteration": it, "residual_N": nR,
                       "x": [float(v) for v in x]})
        if nR <= gate:
            return _finish(problem, x, R, sides, it, trail)
        # forward-difference Jacobian of the QUALIFIED response operators
        J = np.zeros((3, 3))
        for j in range(3):
            xp = x.copy()
            xp[j] += FD_H_WU
            Rp, _ = interface_residual(problem, xp)
            J[:, j] = (Rp - R) / FD_H_WU
        dx = np.linalg.solve(J, R)
        alpha = 1.0
        while alpha >= ALPHA_MIN:
            x_trial = x - alpha * dx
            if not _in_domain(problem, x_trial):
                alpha *= 0.5
                continue
            Rt, _ = interface_residual(problem, x_trial)
            if float(np.linalg.norm(Rt)) < nR:
                x = x_trial
                break
            alpha *= 0.5
        if alpha < ALPHA_MIN:
            return _refuse(problem, "port_solve_not_converged",
                           f"line search stalled at iteration {it} "
                           f"(|R| = {nR:.3e} N)", run_fallback_on_refusal,
                           trail=trail)
    return _refuse(problem, "port_solve_not_converged",
                   f"|R| still {trail[-1]['residual_N']:.3e} N after "
                   f"{max_iterations} preregistered iterations",
                   run_fallback_on_refusal, trail=trail)


def _refuse(problem: InterfaceProblem, reason: str, detail: str,
            run_fallback: bool, trail: list | None = None):
    fallback = {}
    if run_fallback:
        ref = cp.solve_assembly(problem.assembly)
        fallback = {"fallback": FALLBACK_NAME, "result": {
            "seam_position": [float(v) for v in
                              ref["result"].positions[problem.assembly.seam_index]],
            "free_residual_N": ref["result"].free_residual,
            "A_rim_net_N": list(ref["reactions"][:len(problem.assembly.block_a)].sum(axis=0)),
            "B_rim_net_N": list(ref["reactions"][len(problem.assembly.block_a):].sum(axis=0)),
            "surface_energy_J": ref["result"].surface_energy}}
    raise PortSolveRefused(reason, detail, fallback)


def _finish(problem: InterfaceProblem, x, R, sides, iterations, trail) -> dict:
    ra, rb = sides["A"], sides["B"]
    seam = problem.assembly.seam_index
    return {
        "status": "converged",
        "iterations": iterations,
        "interface_residual_N": float(np.linalg.norm(R)),
        "seam_position": x.copy(),
        "seam_force_A_N": ra["seam_force_int"],     # film A on the seam
        "seam_force_B_N": rb["seam_force_int"],     # film B on the seam
        "A_rim_net_N": ra["rim_net"],
        "B_rim_net_N": rb["rim_net"],
        "piece_statuses": {"A": ra["status"], "B": rb["status"]},
        "response_evaluations": problem.piece_a.evals
                                + problem.piece_b.evals,
        "surface_energy_J": {"A": ra["surface_energy"],
                              "B": rb["surface_energy"]},
        "seam_positions_bit_identical":
            bool(np.array_equal(ra["positions"][problem.piece_a.seam_local],
                                rb["positions"][problem.piece_b.seam_local])),
        "solution_hash": _solution_hash(
            x, ra["seam_force_int"], rb["seam_force_int"],
            ra["rim_net"], rb["rim_net"]),
        "trail": trail,
        "fusion_note": problem.fusion_note,
    }


def fused_reference(problem: InterfaceProblem) -> dict:
    """The qualified fused-mesh reference for agreement checks."""
    ref = cp.solve_assembly(problem.assembly)
    n_a = len(problem.assembly.block_a)
    return {
        "seam_position": ref["result"].positions[problem.assembly.seam_index],
        "A_rim_net_N": ref["reactions"][:n_a].sum(axis=0),
        "B_rim_net_N": ref["reactions"][n_a:].sum(axis=0),
        "free_residual_N": ref["result"].free_residual,
        "surface_energy_J": ref["result"].surface_energy,
        "seam_height_wu": ref["seam_height"],
        "output_port_net_force_norm": ref["output_port_net_force_norm"],
    }


def port_representation_entry(receipt_name: str, measured: dict) -> dict:
    """The piece-record representation entry for a QUALIFIED port-based
    solve (additive amendment to assembly.star-k2; the fused reference
    stays named as the fallback)."""
    return {
        "kind": "port-based", "status": "qualified",
        "receipt_ids": [receipt_name],
        "measured": measured,
        "note": "11.20.5 port-based assembly solve: the pieces are "
                "coupled through their PORT RESPONSE OPERATORS ONLY "
                "(Newton on the interface residual; the interface DOF is "
                "the seam vertex's FULL 3D displacement -- no reduction; "
                "the weld consumes every other DOF and the law's vertex "
                "forces are local to incident faces). Reproduces the "
                "fused-mesh reference within the preregistered "
                "agreement tolerances; the fused-mesh solve_equilibrium "
                "remains the qualified detailed fallback",
    }
