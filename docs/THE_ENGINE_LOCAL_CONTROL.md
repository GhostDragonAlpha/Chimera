# Local engine control without repeated network prompts

Task `engine-local-control-01`, generation 1, base
`513724db295a893f3f57e2b10d3972c34be1f114`.

Alan reports repeatedly approving the engine's network permission popup.
Inspection found `HttpServer::start` binds `INADDR_ANY`; Windows reported both
the owned test instance and existing operator instance listening on `0.0.0.0`.
The private launcher also creates new executable paths for evidence isolation.
[Microsoft documents](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/rules)
that application firewall rules use full executable paths and an application
without a matching rule can trigger a permission prompt. This explains a likely
cause; it is not proof of the exact sequence behind every historical prompt.

## Preregistration

STATEMENT: the embedded engine control server serves same-machine clients on
IPv4 loopback without listening on LAN interfaces or changing firewall policy.
PREDICTION: after binding `htonl(INADDR_LOOPBACK)`, actual Windows socket
enumeration reports `127.0.0.1`; local GET and POST work, while a connection to
the machine's non-loopback address on that port fails. A fresh-path engine
launch is observed for new permission dialogs; lack of a new dialog is a
bounded observation, not a guarantee about every Windows policy or version.
FALSIFIER: wildcard or LAN listener, local API regression, changed/disabled
firewall policy, a new prompt on the tested fresh path, or unsupported claim
that an already-running older executable was repaired.

The API is local development control, not a multiplayer endpoint. This change
does not add a LAN opt-in or a firewall exception. Remote/LAN control would
require a separately declared authenticated interface contract. Preserve the
operator process, protected build artifacts, and all failed evidence.

## Executed results

The network change is committed at `c2de9df4`; the combined build also includes
the integrated Studio correction. Evidence is in
`docs/evidence/engine_local_control/`.

- Two fresh-path MSVC native executables bound only `127.0.0.1:8101`, verified
  through Windows socket enumeration. Frozen B2 initialization by POST and
  status by GET succeeded, reporting active state and energy 2.625 J. This is
  control-path evidence, not a new numerical certificate.
- Neither fresh-path launch produced an observed `PickerHost` process during
  launch and later checks. The previously observed Security prompt used that
  host. This supports the tested no-new-popup observation; it cannot guarantee
  behavior under every policy or identify every possible future notification.
- Connections through the two machine-owned non-loopback addresses timed out.
  They did not connect. The independent CPU harness's stricter expectation of
  an immediate connection-refused error **did not pass**; its failed result and
  preregistration are preserved. Timeout alone does not establish the reason
  for rejection; OS listener enumeration establishes the loopback binding.
- A separate fresh MinGW executable using the actual HTTP server passed local
  GET and POST and bound only `127.0.0.1:49173`. Its source, build attempts,
  binary hashes and commands are retained. No Vulkan was used in that harness.

No firewall setting or rule was changed, and no Security dialog was operated.
The existing operator executable was inspected but not replaced or restarted;
already-running old builds retain their old listener until rebuilt/relaunched.
Owned native test processes and the CPU harness were verified drained.

`prompt_before.json` preserves the original empty output from a no-match process
query; later snapshots are explicit JSON arrays. It is not a successful JSON
verifier input or an independent universal proof that no dialog could exist.

The server's existing shutdown lifecycle also needs repair: `stop()` joins its
accept thread before closing the listening socket. `engine-http-lifecycle-01`
records that separate requirement; it was not silently changed in this fix.
