# Slotless integration acknowledgement response — preregistration

Recorded after the provisioning-gate tests and before this response-only change
or its test.  The inherited acknowledgement transition correctly keys on the
frozen REVIEW head and does not need a slot, but its result text always says a
slot remains held.

## Statement, prediction, falsifier

For a review with a recorded slot handoff, the extension will run the inherited
`ack_integration` path unchanged and then report `slot: null` plus
`slot_status: RELEASED_AT_REVIEW_HANDOFF`.  Slotted acknowledgements retain the
base result.  This loses if any inherited auth/head/epoch/publication gate is
bypassed, if task/request state differs, or if a slotted legacy response changes.
