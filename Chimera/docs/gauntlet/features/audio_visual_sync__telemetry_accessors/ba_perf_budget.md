# Bachelor: performance budget — audio_visual_sync/telemetry_accessors

Budgets, declared: fps floor 60 fps in the L_RegolithYard walk path with the
instrument active (the instrument may not cost the frame it measures); sampling
path under 0.05 ms per footstep event; memory ceiling 64 samples x 8 bytes ring
buffer plus counters — under 1 KB, zero allocations per sample; no additional
draw calls (the feature renders nothing).

Measurement plan, per the telemetry law: python -m core.telemetry_probe --soak
30 run FOREGROUNDED — the background throttle freezes fps AND all Niagara/anim
simulation, so a backgrounded soak would measure a paused world and call it
performant. Comparison is against the same soak on a build with the component's
sampling compiled out; the delta is the instrument's true cost, and the budget
above is what that delta must stay under.
