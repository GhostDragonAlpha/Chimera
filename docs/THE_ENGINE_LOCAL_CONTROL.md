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
