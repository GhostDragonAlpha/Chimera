# Lead channel and ten-slot memory verification

2026-09-24. Synthetic tests: 18 passed, including ten concurrent registrations with
unique slots, refusal of an eleventh/duplicate, safe reinitialization, reconciliation,
stale-generation rejection, retained handoff memory, next-hour (not rolling) expiry,
no deadline renewal by reports, no release without cessation confirmation, instruction
revision changes, rollback and unversioned edits, malformed metadata, path limits and
the absence of implicit human/lead authentication.

Time-zone display is drawn from the Windows system timezone. Read-only host inspection
reported Id=Central Standard Time, DaylightName=Central Daylight Time, with current
timestamp offset -05:00. UTC is retained alongside local display for unique identity.

The tests did not register real GLM workers, receive GLM acknowledgement, run a background
hourly timer, revoke a native task claim, stop an agent process or enforce exclusive OS
file access. Those must not be inferred from the helper's successful tests.

Five suggestion-box tests cover concurrent submissions, exact retry idempotence,
unchanged original questions, append-only answers, stale/concurrent answer refusal,
payload/queue bounds, and an operator-message reference for lead review. Idempotent
initialization preserves the mailbox and review record. There is no scheduler, model
invocation, process control or automatic lead review. The operator's final instruction
is manual review when the operator messages Astra; the earlier hourly-lead proposal
was superseded before any automation was created.

Worker onboarding routes scoped operator requests through existing task ownership and
architecture questions to the shared mailbox. The new ten-slot reporting store does
not replace the native task/controller registry. Lead-role fields are not authentication.
