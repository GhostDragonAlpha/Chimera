# Chimera Engine — agent onboarding (paste-in)

> Hand this to any agent (or your future self) developing Chimera. You build the game **through**
> the Chimera Engine MCP server — it is your editor. Work through its tools; never around them.

---

You are developing the game **Chimera** through the **Chimera Engine** (tools named
`mcp__chimera-engine__*`). It is the AI's Unreal: the workflow made into tooling so you cannot
drift. Reference: `ChimeraEngine/MCP_ENGINE.md`.

**The iron rules:**

1. **`orient` first, every single time.** It shows where you are, the current term's gate progress,
   the hierarchy, the codebook, and the ONE next move. Never guess the state — read it.
2. **You do not pick the term — `next` does.** Setting-first, from the seed down. Work the term the
   engine hands you; do not jump to a mid-tree scene (that was the founding failure).
3. **Discover variables by `question`, never declare them.** Keep asking until the engine reports
   `saturated` — the discovery curve must go over the hump (a dry tail + Chao2 completeness), not
   stop when you *feel* done. If you invent variables in your head, you've already failed.
4. **`classify` every variable** to `PHYSICS` (a measurable fact) or `THE HUMAN` (taste — the
   operator's `decide`). No other terminal is legal.
5. **`render` a REAL visual.** The true measure is *seeing* it. The engine refuses a path with no
   file behind it — a claim of a visual is not a visual.
6. **`prove` is the only way to mark a term done.** It runs every gate and refuses until all pass,
   naming the blocker. **Read the refusal; do exactly what it says.** Do NOT reach for raw Bash or
   Write to fake progress on a game term — the engine owns "proven" and will not record it.
7. **Taste terminates at the operator.** `decide` is theirs, never yours. Meaning is not yours to
   close.

**The loop:**

```
orient → next → frame → question × N → classify → render → prove
```

**When you're stuck:** the `prove` refusal names the gate *and* the fix — follow it. The only legal
stops are (a) a term is genuinely proven, (b) you are blocked by something real (say so with the
cause), or (c) a decision is **taste**, which bottoms out in the operator (`decide`). "Which term
should I do?" is never a legal stop — `next` already answered it.

**Honest note (V1):** your raw tools still exist; the discipline is to work *through* the engine,
and the engine catches fakes at the state layer — you cannot mark a term proven without the gates.
The pure form (only these tools) is coming. Until then: if you're about to touch a game artifact
with Bash/Write instead of a tool, stop — that's the drift the engine exists to prevent.
