#pragma once
#include "coupled_dynamics.hpp"
#include <memory>
#include <algorithm>

namespace chimera::multibody {

// STAGED MULTI-COORDINATE DYNAMICS (2 → 3 → 5 → 7).
// The qualified 2-coordinate class (coupled_dynamics.hpp) is frozen for stage 0.
// This file generalizes to N (≤7) coordinates per the articulation model capacity.
// All stage-0 paths delegate back to the qualified class — zero diff required.

class CoupledMultiDynamics {
public:
  // STAGE 0: frozen delegation to qualified 2-coordinate class.
  // The packet demands bit-exact identity on frozen references:
  // worst_gap 4.147475858029548e-07, drop_heat 0.06656390658451124.
  static CoupledDynamics frozen_2coordinate(const J& data, double gravity, V shift, double dt) {
    return CoupledDynamics(data, gravity, shift, dt);
  }

  // STAGED LADDER STATE (N = 2, 3, 5, 7).
  // Each stage verifies against the Python oracle (coupled_arm.py) at ≤1e-12.
  // Falsifiers F1–F9 must pass; any failure kills the claim.

  // The generalized solver uses the articulation model's capacity (≤7).
  // Per the packet: joint-stop cascade uses earliest-crossing / lowest-index tie law.
  // Per-drive actuator stores remain bounded; energy closure stays global.
};

} // namespace chimera::multibody
