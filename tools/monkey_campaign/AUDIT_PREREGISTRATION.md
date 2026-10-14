# Workflow audit and task-start correction, 2026-09-24

Statement: a new worker must receive a concrete authorized task, not just an arrival
receipt. The current GLM file-coordinated fleet can own bounded diagnostic tasks through
its existing shared slot registry without enrollment in the dormant prototype controller.
Prediction: two simultaneous claims cannot receive the same task/slot; a task cannot
be reclaimed on time expiry or completed by a stale generation; a blocked/empty queue
returns a concrete cause. Existing registered workers and protected jobs stay intact.
Falsifiers before implementation: duplicate task claims, eleven allocated slots, foreign
or expired completion accepted, native readiness fabricated, or writes beyond an explicit
owned diagnostic directory. Claims here authorize bounded read-only investigation plus
the named report outputs, not arbitrary source edits or hardware runs.

Additional audit falsifiers: a placeholder timestamp accepted as a dated acknowledgement;
engine current term presented as an agent identity; a static receipt treated as native
runtime acceptance; old and new scope/file digests conflated. Historical documents remain
records; active entry points must route to the canonical campaign and current policy.
