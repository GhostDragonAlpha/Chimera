# Ten slot publication branches

Slot N publishes to branch-N, for N=1 through 10. These names persist when a
completed card is replaced. The task ID and criteria hash identify the current work;
the slot number is not a permanent physical membrane. The card planning IDs bind it
to ontology membranes, ports, dependencies and visual checkpoints.

Workers use isolated scratch directories or detached checkouts. Do not create new
remote attempt branches, share a working directory, or push to the numbered branch.
Submit a patch or preserved commit, source/base SHA, task ID, attempt ID, criteria
hash and verification receipt to the task inbox. The lead serializes publication,
checks the current remote head, and creates/updates the slot PR. Competing patches
remain separate candidates until reviewed. No force push or timer takeover.

After merge, record the verified winning head and refill the card. Before publishing
the next card, the lead brings the numbered branch forward from the integration
branch with an ordinary fast-forward/merge; refuse unexplained unmerged history.
Keep the archive mapping, PR and task history. Do not delete numbered branches.

During migration, existing attempt branches and PRs remain valid preservation and
review references; workers must not rename/switch other active worktrees. Submit
corrections through the task inbox for lead transfer to the numbered branch.
The main and integration branches are not task lanes. Historical branches may be
retired only after archive verification and approval of the cleanup set.
