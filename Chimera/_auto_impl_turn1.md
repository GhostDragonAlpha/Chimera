2.  **Identify Key Requirements:**
   - Implement `stress_gradient_to_emission_prob(gradient)` in `splat_emit.py`.
   - Use a calibrated sigmoid transfer for the 0.21–0.28 gradient range, mapping to [0, 1].
   - Replace direct gradient usage in the candidate processing loop with this mapping.
   - The code must be complete and runnable (standalone or as a module snippet that fits `splat_emit.py`).
   - Address DEEP's point: Don't conflate stress/gradient with LOD/fidelity boundaries. Keep emission probability purely tied to the gradient-to-probability mapping, separate from LOD logic.
   - Output ONLY code.

3.  **Design the Sigmoid Mapping:**
   - Input range: `[0.21, 0.28]` (typical gradients)
   - Output range: `[0.0, 1.0]`
   - Standard sigmoid: `1 / (1 + exp(-k*(x - x0)))`
   - We want to map `[0.21, 0.28]` to roughly `[~0.05, ~0.95]` or exactly `[0, 1]`. Since it's a probability, clamping/saturation is fine, but let's use a scaled sigmoid that covers the range smoothly.
   - Actually, a simpler approach: `sigmoid(x) = 1 / (1 + exp(-scale * (x - center)))`
   - Let `center = 0.245` (midpoint of 0.21 and 0.28)
   - We want `sigmoid(0.21) ≈ 0.0` and `sigmoid(0.28) ≈ 1.0`.
   - Solve for `scale`: `exp(-scale * (0.21 - 0.245)) = exp(scale * 0.035)` should be large enough to push output near 0. Let's pick `scale` such that at `x=0.21`, sigmoid ≈ 0.05, and at `x=0.28`, sigmoid ≈ 0.95.
   - `sigmoid(x) = 1 / (1 + exp(-k*(x - c)))`
   - At x=c, output=0.5.
   - Let's use a simpler linear-ish mapping wrapped in a sigmoid for smoothness, or just a standard scipy/numpy implementation. Since it needs to be runnable without external deps if possible, I'll use `math.exp`.
   - Actually, the prompt says "calibrated sigmoid transfer". I'll implement a clean function:
     ```python
     def stress_gradient_to_emission_prob(gradient):
         # Calibrate sigmoid for range [0.21, 0.28] -> [~0.05, ~0.95], then clamp to [0, 1]
         center = 0.245
         steepness = 60.0  # Tuned so that ±0.035 from center gives near-saturation
         prob = 1.0 / (1.0 + math.exp(-steepness * (gradient - center)))
         return max(0.0, min(1.0, prob))
     ```
   - Wait, let's verify: `exp(-60 * -0.035) = exp(2.1) ≈ 8.17` -> `1/(1+8.17) ≈ 0.109`. At +0.035: `exp(-2.1) ≈ 0.122` -> `1/(1+0.122) ≈ 0.891`. That's reasonable for a probability mapping. I can adjust steepness to 70 or just use a standard logistic function that maps the exact bounds if needed, but clamping is fine.
   - Actually, a more precise calibration: `k = math.log(99) / (0.28 - 0.21)` gives mapping from ~0.01 to ~0.99 over the range. But sigmoid asymptotes. I'll stick with a practical calibrated version that maps the observed gradient cluster smoothly to probabilities, avoiding LOD conflation.

4.  **Address DEEP's Critique (Conflation):**
   - The prompt says: "FAST is treating emission probability as a visual fidelity proxy calibrated to `splat_lod.py` boundaries, but that conflates two..."
   - I need to ensure the code explicitly separates stress gradient mapping from LOD/fidelity logic. The function should only handle gradient -> prob. The candidate processing loop should use this prob for emission decisions independently of any LOD thresholds.
   - I'll write a self-contained module snippet that can be dropped into `splat_emit.py`, including imports, the new function, and a mock candidate processing loop that demonstrates the separation.

5.  **Draft Code Structure:**
   ```python
   import math
   from typing import List, Dict, Any

   def stress_gradient_to_emission_prob(gradient: float) -> float:
       """
       Maps normalized stress gradient (typically 0.21–0.28) to emission probability [0, 1].
       Uses a calibrated sigmoid centered on the observed transition zone midpoint.
       Explicitly decoupled from LOD/fidelity boundaries to avoid conflation with visual scaling.
       """
       center = 0.245  # Midpoint of observed gradient cluster [0.21, 0.28]
       steepness = 65.0  # Tuned for smooth transition across the 0.07 range
       prob = 1.0 / (1.0 + math.exp(-steepness * (gradient - center)))
       return max(0.0, min(1.0, prob))

   def process_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
       """
       Processes consolidated stress candidates using the gradient->probability mapping.
       Separates emission probability from LOD/fidelity thresholds.
       """
       processed = []
       for cand in candidates:
           grad = cand.get("gradation", 0.25)
           # Apply calibrated mapping instead of raw gradient or LOD-boundary proxy
           emit_prob = stress_gradient_to_emission_prob(grad)

           processed.append({
               "center": cand["center"],
               "volume": cand["volume"],
               "type": cand["type"],
               "gradation": grad,
               "emission_probability": emit_prob,
               # LOD/fidelity decisions remain separate and are NOT derived from emit_prob
           })
       return processed

   if __name__ == "__main__":
       # Simulate consolidated output matching rig.py schema
       sample_candidates = [
           {"center": (0.1, 0.2), "volume": 735, "type": "medium_articulation", "gradation": 0.22},
           {"center": (1.5, 2.0), "volume": 17542, "type": "transition_zone", "gradation": 0.245},
           {"center": (3.0, 3.0), "volume": 98, "type": "tendon_anchor", "gradation": 0.27},
       ]
       results = process_candidates(sample