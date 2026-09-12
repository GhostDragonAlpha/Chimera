# Agent fleet control reference

Start with [the universal entry](../../docs/AGENT_START.md),
[the operating contract](../../docs/THE_AGENT_FLEET.md), and the
[review slot handoff contract](../../docs/THE_REVIEW_SLOT_HANDOFF.md).
Standard-library Python; single controller, authenticated HTTP, local SQLite.
The HTTP controller records state. Trusted launcher, provisioner and publisher
adapters perform their documented process, filesystem and Git actions separately.

Run from the repository root:

```bash
python -m unittest discover -s tools/agent_fleet -p 'test_*.py' -v
```

After an exact pushed PR is submitted for review, the trusted broker verifies
preservation and drain evidence and calls `release_review_slot`. The task stays
REVIEW, protecting its submitted artifact and write scope, while its slot and
execution capacity become available. Do not require integration merely to free
capacity. Corrections use lead `review_requeue`, ordinary worker `claim`, and
provisioning at the returned `correction_base_head`.

Do not infer exhausted capacity by counting every task whose owner is your agent
ID. A detached review still records that owner. Use its handoff/slot state and the
controller's actual claim decision.

Use your own provisioned session with `client.py`. Its CLI `--arguments` file
contains the operation's argument object; the adapter builds the HTTP
`operation`/`arguments` envelope. Never use another agent's session or ask for
supervisor credentials to repair a malformed request.

A completed local engine hierarchy is not a completed Master list. Continue an
owned controller task or claim eligible READY work. Report a concrete admission
or dependency problem to the lead while continuing other authorized work.

The replay tests are control-plane evidence only. Actual process revocation,
provider adapters and publication fencing require separate evidence. Windows
slot/runtime demonstrations exist in the fleet records, but historical builds
do not establish what is running now. Inspect the actual controller, worktree,
binary and resource ownership before runtime work.
