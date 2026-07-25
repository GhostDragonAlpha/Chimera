"""
Standard simulation kernels for the Chimera Particle Engine.

Each kernel signature:  fn(data, active_mask, control_vars, dt) -> None
All kernels modify `data` in-place. They should only touch columns
declared in core.COL and obey the pipeline contract.
"""
