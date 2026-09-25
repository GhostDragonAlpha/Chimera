# Verifiable simulation and public code

Operator direction, 2026-09-24. Architectural proposal; not an implemented
network runtime, anti-cheat guarantee or evidence that the engine is complete.
The playable-monkey acceptance gates in MONKEY_RUN.md remain in force. This
proposal does not activate multiplayer work or enlarge the sealed feature list.

The product direction is publicly inspectable engine code with separately
controlled game assets, stories and hosted access. Visibility, copyright license,
data confidentiality and server authority are four different decisions.

## Simulation authority

The trusted simulation accepts authenticated player intent, assigns an ordered
sequence/tick, enforces control bounds and computes the next authoritative state.
Clients may predict/interpolate presentation but cannot commit world positions,
forces, inventory or time. Keep the existing 20 Hz speed/heading command contract;
it does not by itself specify the physics integration timestep.

Use monotonic server ticks for integration. Record a server-controlled UTC anchor
for audit correlation, its source and uncertainty; never integrate directly from
an arbitrary client wall clock. Wall-clock corrections, leap handling, outages
and scheduling delays must not grant a player extra simulation time. Authenticated
network time helps establish the time source, not the truth of a simulated event.

For each accepted transition, record schema/runtime/model/asset versions, the
previous state identity, authoritative tick, ordered accepted inputs and RNG state
where applicable, resulting state identity, and validation outcomes. Chain record
hashes and sign checkpoints with keys outside public source. An independent
observer needs a previously trusted checkpoint to detect an operator rewriting
the whole chain. This is an auditable event log; no blockchain consensus or token
system is implied or needed for a single authoritative host.

## Determinism and anomaly handling

Replays require the same initial state, input order, parameters and a declared
numerical execution contract. Physics alone does not predict unknown future
inputs. GPU reduction order, solver state, floating-point modes and version
changes must be characterized. Exact replay may be supported on a pinned
execution profile; cross-device equivalence requires separately declared and
measured bounds. A tolerance cannot be widened after observing a failed case.

Reject unauthenticated, duplicate, stale, out-of-window or out-of-contract inputs.
Do not accept a client state simply because its timestamp or supplied hash looks
valid. Distinguish protocol rejection, physical invariant failure, solver drift,
resource delay and replay mismatch. Preserve evidence; an anomaly alone is not
proof of a cheating person. Automated play can submit physically legal commands,
and information leaks can aid a player without violating motion laws. These need
separate detection and information-disclosure policies.

## Browser and asset boundary

Only send each client the state it is entitled to observe. Keep unreleased source
assets, story data, signing keys and server-only state outside the public source
repository and outside client payloads. Browser rendering exposes delivered code,
meshes, textures and decoded data to the client. Pixel streaming can keep original
asset files on the server but cannot prevent recording the displayed experience.
Do not promise that browser access makes extraction or reverse engineering
impossible. Moving previously public data later does not retract existing copies.

## Qualification before implementation is called complete

- V1: arbitrary client clock offsets and backward wall-clock changes cannot alter
  authoritative step count or grant extra input opportunities.
- V2: tampered, replayed, duplicated and reordered command packets receive named
  outcomes; accepted ordering is deterministic and recoverable.
- V3: recorded inputs replay from pinned checkpoints under the declared numerical
  contract; a changed model, parameter, RNG state or solver mode is detected.
- V4: altered/deleted log records and rollback across a trusted signed checkpoint
  fail verification. Re-hashing an unanchored whole log demonstrates the limit.
- V5: contact, ownership and control-invariant checks distinguish deliberate
  violations from legitimate lag and measured numerical uncertainty.
- V6: injected loss, reconnects, host crashes and clock-source failure preserve
  ordering and recovery without silently accepting client authority.
- V7: a legal-input automation control demonstrates that motion validation alone
  does not detect every form of cheating. No 'perfect anti-cheat' claim follows.
- V8: client payload inspection identifies exactly which assets/state are exposed;
  source-private material and signing secrets do not appear in those payloads.

These are future preregistration headings, not measured results. Each execution
lane must pin concrete fixtures, oracles and numerical criteria before running.

## Primary references

- [Valve: Source Multiplayer Networking](https://developer.valvesoftware.com/wiki/Source_Multiplayer_Networking)
  describes authoritative server simulation, ticks and client prediction.
- [IETF RFC 8915: Network Time Security](https://www.rfc-editor.org/rfc/rfc8915.html)
  authenticates time synchronization; it does not validate application physics.
- [GitHub Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service)
  govern viewing/forking public repositories independently of additional licensing.
