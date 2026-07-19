# GAUSSIAN FOUNDRY — AGENT WORKFLOW

This is the master workflow. Everything else is reference.

## 1. RECEIVE DIRECTION

Human gives a goal, problem, or question.

## 2. INTERNAL COUNCIL (7 gates, ~3 min)

Run this in your own context. No external agents.

```
Gate 1 — Frame the problem
  Write a one-sentence definition. What are we actually solving?

Gate 2 — 10 questions
  Ask 10 specific, technical questions about the problem.
  Each question probes a different angle.

Gate 3 — Answer all 10
  Answer every question from what you already know.
  If you genuinely don't know, say it.

Gate 4 — Deeper questions
  The answers from Gate 3 reveal 10 deeper questions.
  Each builds on something one of the answers said.

Gate 5 — Answer those
  Answer the deeper questions.
  At this point you should see the implementation.

Gate 6 — Saturation check
  Can you see the exact file changes?
  If yes: proceed to Gate 7.
  If no: loop back to Gate 4 with the remaining unknowns.

Gate 7 — Output spec
  Produce a structured spec with:
  - mechanic_name or change_title
  - target_files (exact paths)
  - code_changes (what changes in each file)
  - player_experience (how it feels from the user's side)
```

## 3. EXECUTE

Choose the right tool:

| If you need... | Use... |
|----------------|--------|
| Research UE5 source code | `research_engine` tool |
| Search project code | `readSeek_grep`, `readSeek_refs` |
| Read/edit a file | `read`, `edit`, `write` |
| Run a bash command | `bash` |
| Send a prompt to the worker agent | `worker_client.py` -> PiWorker.prompt() |
| Run the forge pipeline | `forge.py` with a spec JSON |
| Check project health | `chimera_preflight` |
| Access UE5 viewport | `mcp_capture_viewport`, `mcp_set_camera` |
| Spawn actors in UE5 | `mcp_spawn_actor` |

## 4. REPORT

Post the full council report verbatim:
- All 20 Q&A pairs (Gates 2-5)
- What was implemented this cycle (file paths, line counts)
- What's still open (next direction)
- Saturation state (which targets are clear)

The human reads every Q&A to determine the next direction.

## 5. COMMIT

`git add -A && git commit -m "[summary]" && git push origin master`

---

## FILE ARCHITECTURE

```
worker_bridge/
  main.py              — FastAPI bridge server (keep running)
  forge.py             — Workshop pipeline (use when you have a spec)
  worker_client.py     — Python SDK for bridge (use for worker prompts)
  dashboard.html       — Monitoring UI
  send_build_brief.py  — Example: send brief to worker
  *.bat, *.ps1         — Launchers for visible windows
  chronicle/           — Q&A records (auto-generated)
  specs/               — Spec manifests (auto-generated)
```

## TOOL HIERARCHY

1. **Internal council** — fastest path, use first
2. **Direct file edit** — `read` + `edit` tools for Python files
3. **Worker bridge** — `worker_client.py` for design work, research, second opinions
4. **Forge** — `forge.py spec.json` for multi-file implementations with gates
5. **MCP tools** — for UE5 viewport, actor spawning, screenshots
6. **Research engine** — for UE5 source code lookups
