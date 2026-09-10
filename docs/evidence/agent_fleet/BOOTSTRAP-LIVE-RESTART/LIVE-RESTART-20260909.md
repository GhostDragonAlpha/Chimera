# LIVE-RESTART-20260909 — durable operating installation verified

Record of the controlled transition that adopted the manually-launched control
service into the managed launch path (`bootstrap_fleet.py`) and proved the
registry survives a full restart unchanged.

## Preregistration (written before the run)

- STATE: one documented operator command can own the persistent fleet service:
  refuse conflicting starts, hold credentials outside the checkout, and survive
  bounded restarts with every claim and session token intact.
- PREDICTION: (1) bootstrap `status` reports the five stages
  installation→running→reconciled→enrolled→ready; (2) a `start` on an already
  live fleet port is refused; (3) adoption + a full controlled restart keeps
  revision, epoch, leader, owner, slot and generation of every task unchanged;
  (4) the pre-restart supervisor/session tokens still authenticate after restarts.
- FALSIFIER: a restart that drops a claim, changes owner/slot/generation, or a
  start that silently spawns a second service behind the live one.

## Execution timeline (UTC)

| step | action | result |
| ---- | ------ | ------ |
| 05:55 | `bootstrap_fleet.py status --port 8099` (pre-adoption) | fleet running; unmanaged (no pidfile) |
| 06:02 | snapshot captured | `revision=23 epoch=1 leader=big-pickle`, 5 tasks RUNNING, 5/5 slots |
| 06:03 | controlled stop of manual instance pid 10268 | port 8099 free |
| 06:03 | `bootstrap_fleet.py start --port 8099` | pid 1296, `running: yes (reconciled=True)`, pidfile matches |
| 06:04 | `bootstrap_fleet.py restart --ack "<controlled live restart ...>"` | stopped 1296 → spawned 36204, reconciled |
| 06:04 | post-restart snapshot | identical registry: `revision=23 epoch=1 leader=big-pickle`; all five tasks RUNNING, owner/slot/generation unchanged |
| 06:04 | `status` | stages all OK, pidfile matches True |

## Verified facts

- Credentials lived only in `E:\ChimeraWork\control\.service_secrets.json` (outside
  the checkout); the same secrets served both pre- and post-restart instances, so
  session tokens and the supervisor token remained valid across the transition.
- Registry identity: `reconciled` requires the persisted secret hashes to equal
  the registry's stored identity hashes — a service restarted with foreign
  credentials would refuse its own state rather than present it.
- `os.kill(pid,0)` is NOT a liveness probe on Windows (WinError 87). Bootstrap
  resolves the listener owner via `netstat` and requires the pidfile pid to equal
  the listener owner before it will stop anything. Unmanaged live instances are
  REFUSED, not force-killed.
- A second `start` on a live fleet port is refused (`duplicate_start_refused`);
  a foreign listener on the same port is refused (`conflicting_listener_refused`).

## Offline acceptance

- `tools/agent_fleet/test_bootstrap_fleet.py` — 4 operator-path tests driving the
  real CLI + real spawned service on isolated ports: start→ready→duplicate-refused;
  stop demanded ack and cleared stages; foreign listener blocked start and stop;
  restart preserved claims/checkpoints/session tokens.
- Full fleet baseline (50 offline tests) still green.

Milestone evidence: RESTART-PROOF (see docs/THE_MASTER_LIST.md).