# JUDGE TASK — blind-judge dyad run `D1-dryrun`

You are a **stranger with a wallet**. Your briefing is
`docs/evidence/agent_fleet/SHIP/R8_R4_PLAYBOOK/PLAYBOOK.md` — read it and obey
its BLIND RULES exactly; this session's artifacts are in

    E:\ChimeraWork\slot-01\docs\evidence\agent_fleet\SHIP\DYAD_JUDGE\sessions\D1-dryrun_20260914_225117

The pipeline has already PLAYED the session for the mechanics record
(`resp.jsonl` = every command and every screen read, `shots/` = the timed
recording, `session.log` = timestamps). Your job is the JUDGMENT, which no
pipeline can supply: read `resp.jsonl`'s `"did":"text"` screen reads and the
shots AS A BUYER would watch them, then write your verdict.

Write BOTH of these into this directory:

1. `verdict.md` — the playbook's verdict template, filled verbatim.
2. `verdict.json` — the same verdict, machine-readable, EXACTLY this shape:

```json
{
  "judge": "D1-dryrun",
  "date": "<YYYY-MM-DD>",
  "what_is_this": "<your words>",
  "pay_15_20": false,
  "pay_25": false,
  "novelty": 0,
  "novelty_line": "<one line: what it's like, what you've never seen before>",
  "quotes": ["<3 sharpest, verbatim from your answers>"],
  "term": "<2-4 words: the buyer NAME for what this product is -- the dyad term>",
  "lessons_completed": 0,
  "press_test_performed": true,
  "stalls": 0,
  "honesty_note": "<did you know this project before? a judge who peeked must say so>"
}
```

The registry entry (tools/verdict_registry.json, lane "blind-judge") is opened
already with a Rule-0 prediction; your verdict is what CLOSES it. Do not read
any repository file beyond PLAYBOOK.md and this directory.
