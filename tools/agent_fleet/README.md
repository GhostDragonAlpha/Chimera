# Agent fleet control reference

Start with `docs/AGENT_START.md` and `docs/THE_AGENT_FLEET.md`.
Standard-library Python; single controller, authenticated HTTP, local SQLite.
No engine, Git, model, filesystem provisioning or merge actions are executed.

Run from the repository root:

```bash
python -m unittest discover -s tools/agent_fleet -p 'test_*.py' -v
```

The replay tests are control-plane evidence only. Actual process revocation,
Windows slot engines, provider adapters and GitHub publication fencing are
separate deployment gates. All five planned engine installations are unbuilt.
