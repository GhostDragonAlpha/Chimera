# Chimera — Threat Model

> **The reframe (the human, 2026-07-17): look at this as security.** The studio is an
> access-control system, and saying so out loud rearranges every piece that was already
> here:
>
> | security concept | Chimera piece |
> |---|---|
> | untrusted principal | an agent (LLM following a protocol) |
> | credential | a piece of evidence (simtest, observation, screenshot) |
> | authorization | a gate (witness / why / visual / training / coin / council) |
> | privilege escalation | a waiver |
> | the root of trust | the **PHYSICS terminal** — a `SimPlaytest` the engine witnessed |
> | "the exploit is the product" | already the TRAINER's doctrine — now the gates' too |
>
> An agent that closes a task without moving the seed did not misbehave; it **found an
> exploit in the gate spec**. That is the useful lens: the bugs fixed this week were not
> N accidents, they were one vulnerability class — *a credential nobody authenticated*.

## The threat that is real, and the one that is not

**These agents are careless, not adversarial.** They are LLMs taking the convenient path
to make a gate go green, not pentesters mounting a cryptographic forgery. So the design
target is: **make the convenient path honest, and make dishonesty require deliberate,
visible, multi-step effort.** Perfect unforgeability is neither achievable (the store is
plaintext the agents must write) nor necessary (nobody is attacking it that way). What
IS necessary is that the *easy* lie is refused and the *hard* lie leaves a trace.

## THE CLASS: a credential nobody authenticated

Every integrity bug this week is the same shape — **a field written by one party and
trusted by another without checking who wrote it.**

- `derived_from = "session_continuous_workflow_202607"` — a citation to a node that
  never existed; every consumer tested truthiness, not resolution. *(Fixed: evidence
  must resolve — `5a0bb8f`.)*
- `evidence_ids = "Already documented as [H-1]"` — an English sentence in an id field.
  *(Fixed: the because-edge refuses a non-node endpoint — `3e3e58e`.)*
- 9/9 postflights ran ZERO gates because the stack was opt-in. *(Fixed: derive the
  feature from the phase — `b2fc07f`.)*
- **`record_simtest(...)` mints the PHYSICS terminal itself** — a clean 5/5 run the
  engine never performed, which then resolves and terminates the why-chain at YES.
  *(Fixed: engine-witness credential — `80789f0`; see below.)*

The pattern never changes: **the data to catch it was always present** (`recorded_by`,
`timeline_path`, the ledger status) and **nothing read it.**

## Trust boundaries (attacked, ranked)

| # | Boundary | Attack | Status |
|---|---|---|---|
| 1 | **The PHYSICS terminal** | forge a `SimPlaytest` via `record_simtest` — the engine never ran | **CLOSED** for the convenient path; residual below |
| 2 | Direct graph write | `nodes.append(forged); save_dna_graph()` — skip every gate | **partial** — the credential still has to be forged too, which is deliberate + visible |
| 3 | Self-waiver (separation of duties) | a subagent passes its own `--training-waiver` | **mitigated** — every waiver is CAPCOM-posted (`postflight:512`) and the LEAD verifies independently |
| 4 | Replay | cite another feature's clean simtest | **mitigated** — `collapse_proxy` ties valence to the simtest whose beats name the feature |

### #1 — the fix, and its honest limit

Only the sleepwalker may witness, and it announces itself: it sets `CHIMERA_AGENT_SIM=1`
(its "constitution sentinel") on import. `_mutate_simtest` now stamps
`witnessed_by_engine` (sentinel present) + `chronicle_present` (the engine's timeline
file is on disk) + `witness_authentic`. The **consumer** (`_mutate_observation`) weighs
it: a cited `SimPlaytest` with `witnessed_by_engine == False` proves only **RECORDED**,
never **MEASURED** — so the why-chain **refuses to terminate** on it. A forgery reaches
"keep asking", never PHYSICS. Proven in a membrane: forged run → RECORDED → no terminal;
real run → MEASURED → PHYSICS.

**The check lives at the CONSUMER, not a perimeter — deliberately.** A wall around
`save_dna_graph` would be one more thing to bypass. Weighing the credential at the point
of use means the same defense covers *any* path that produces the node, including a
future one nobody has written yet.

**Residual risk, stated plainly:** the credential is a stored boolean, not a signature.
A determined direct-write attacker (#2) can append a node with `witnessed_by_engine:
True` set by hand and defeat the check. That is acceptable **for this threat model** —
it converts the forgery from a one-line accident (`record_simtest(...,5,5,...)`, which is
how 2 of 97 live nodes were minted, by a test) into a deliberate, multi-step, visibly
dishonest act that `recorded_by` still fingerprints. If the threat model ever changes —
adversarial agents, external contributors — the credential must become a re-derived
check (chronicle exists AND parses AND post-dates the node) or an HMAC the sleepwalker
signs. Not today; today the seam is in place and the easy lie is closed.

## The invariant, for the next agent

**No node authenticates itself. A consumer that trusts a field without asking who wrote
it is the bug — every time, for the whole week this doc summarizes.** When you add a
gate: name the credential it reads, name the process allowed to mint that credential, and
make the consumer weigh provenance. A green check that any principal can produce is not a
check; it is a suggestion with a checkmark.
