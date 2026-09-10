# HTTP lifecycle gen2 review preregistration

## Statement
The finite callback shutdown gate must prove that `HttpServer::stop()` has not returned while its callback is still live, then prove callback exit and stop return after release. Lifecycle tests must also exercise restart on one object, double-stop, and refusal of double-start.

## Prediction
The corrected finite callback control will observe `stop_returned=false` and `callback_exited=false` before release, then both true after release. A test double whose stop returns early will be rejected while its callback remains live. One server object will complete five start/stop cycles, tolerate double-stop, and refuse a second start while running.

## Falsifier
The gate fails if stop is observed returned before callback exit, if the early-return mutation is accepted, if the same object cannot restart, if double-stop is unsafe, or if a running object accepts a second start.

## Safety boundary
The mutation control explicitly joins its worker only after release; it never destroys an object with a live worker. Prior gen2 evidence and source records are preserved. This is CPU harness evidence only.
