# Transport review — cf275281
Statement: authenticated malformed resource requests are refused through the documented JSON response without committing state; the next valid request remains usable.
Prediction: a missing or numeric resource name produces a named non-2xx JSON refusal; controller revision is unchanged; snapshot then succeeds.
Falsifier: disconnected response, unhandled exception, mutation, or failed subsequent snapshot. Inputs target only a fresh temporary DB and ephemeral loopback test server.
