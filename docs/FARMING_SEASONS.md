# Chimera Farming Seasons

> A farmer doesn't hold the whole farm in their head. They follow seasons with
> discrete, repeatable batch processes. Any farmhand can execute any batch.
> Inputs → Procedure → Outputs. Everything written to disk. Nothing lives in memory.

---

## SPRING — Design

**What**: Saturate a feature with questions. Output a spec that can be built.

**Batch inputs**: Feature name, seed reference (CHIMERA_VISION.py § section), related graph nodes
**Batch outputs**: Feature spec JSON in `docs/features/`, answered questions in DNA graph

### Batch 1: Catalog Elements
```
Input:  Feature name, seed section
Action: python core/element_catalog.py
        grep CHIMERA_VISION.py for related classes
        Query DNA graph for existing answers
Output: Element list (UPROPERTY, CVars, config keys relevant to this feature)
```

### Batch 2: Council Debate
```
Input:  Feature name, element list
Action: python -m core.council "<feature design question>" --rounds 2 --record
Output: Council transcript in chronicle/, synthesis posted to CAPCOM
```

### Batch 3: Write Spec
```
Input:  Council transcript, element list
Action: Compile spec JSON with: title, design_rationale, target_files, edit_plan, test_strategy
Output: specs/<feature>.json
Verify:  python -m core.graphify_record feature --name <X> --loop <N> --status designed
```

**Exit condition**: Spec exists, council recorded, feature node is `designed`

---

## SUMMER — Build

**What**: Turn a spec into compilable game artifacts. Train any needed domains.

**Batch inputs**: Feature spec JSON, element catalog entries
**Batch outputs**: Compiled C++, trained genomes, Blueprint assets, config files

### Batch 1: Train Domain (if feature is trainable)
```
Input:  Feature name
Action: python -m core.train_loop <domain_name> --pop 50 --gens 40
        Read auditor output: stuck metrics? → fix model → retrain
Output: Trained genome, audit report
Verify:  Stuck rate < 25%
```

### Batch 2: Decode Genome
```
Input:  Trained genome, domain name
Action: python -c "from core.decoder import apply_genome; apply_genome(genome, domain)"
Output: MCP commands, config files, beat scripts
```

### Batch 3: Generate/Compile
```
Input:  Decoded configs, source changes
Action: Kill editor → build → relaunch
        python -m core.task_board claim --agent <id>
Output: Compiled binary, build mutation recorded in DNA graph
Verify:  UBT exit code 0
```

### Batch 4: Spawn Assets
```
Input:  MCP command list from decoder
Action: python -c "from core.decoder import apply_genome; apply_genome(genome, domain, dry_run=False)"
        Manage_level save
Output: Spawned actors, saved level
Verify:  python -c "from core.telemetry_probe import MCPStdioClient; c=MCPStdioClient(); c.call('inspect',{'action':'get_scene_stats'})"
```

**Exit condition**: Build passes, assets in level, task board `done` with build evidence

---

## FALL — Verify

**What**: Prove the feature works. Run sleepwalker, record evidence, collapse.

**Batch inputs**: Feature name, beat script path, test strategy from spec
**Batch outputs**: Simtest evidence, feature observed, loop board updated

### Batch 1: Lint Beats
```
Input:  Beat script path
Action: python -m core.beat_lint --beats docs/beats/<X>.beats.json
Output: Lint report
Verify:  "Every script speaks only words the Sleepwalker knows"
Block:   Any SETTLED expects? → fix the cause, not the beat
```

### Batch 2: Run Sleepwalker
```
Input:  Beat script, session name
Action: powershell foreground editor → python -m core.sleepwalker --beats <path> --session <name>
Output: Simtest node ID, chronicle
Verify:  beats_reached == beats_total
```

### Batch 3: Record Evidence
```
Input:  Simtest ID, feature names
Action: python -m core.graphify_record observe --feature <X> --verdict accepted --derived-from <simtest_id> --tacit --loop <N>
Output: Observation nodes in DNA graph
```

### Batch 4: Collapse
```
Input:  Simtest ID
Action: python -m core.collapse_proxy --from-simtest <simtest_id> --valence accepted
Output: Features collapsed, loop board updated
```

### Batch 5: Postflight
```
Input:  Phase description, results, simtest IDs, researched sources
Action: python -m core.postflight --phase "..." --result "..." --inheritance "..." --researched "..."
Output: PhaseComplete node, phantom pains, GPA update
Verify:  Postflight accepts (no gate refusals)
```

**Exit condition**: All features observed, postflight recorded, task_progress.md updated

---

## WINTER — Reflect

**What**: Audit the system. Distill lessons. Improve the foundation.

**Batch inputs**: All trained domains, observation queue, phantom pains
**Batch outputs**: Model audit report, dream report, gardener queue, history updated

### Batch 1: Audit Models
```
Input:  Domain names (all)
Action: python -c "from core.train_loop import train_and_audit; [train_and_audit(d) for d in domains]"
Output: Stuck metrics per domain, model bug diagnoses
Fix:    Stuck at zero? Add baseline. Stuck at ceiling? Add spread metric.
```

### Batch 2: Dream Loop
```
Input:  (none — reads graph)
Action: python -m core.dream_loop
Output: PENDING_HEURISTICS.md updated, Dream Report generated
```

### Batch 3: Gardener Tending
```
Input:  PENDING_HEURISTICS.md
Action: python -m core.gardener --tend
Output: Promoted rules, queued gate implementations, tombstoned entries
```

### Batch 4: History Book
```
Input:  (none — reads graph)
Action: python -m core.history_book search --query "<lesson>"
Output: Updated HISTORY_BOOK.md (rewritten nightly by dream_loop)
```

### Batch 5: Graph Hygiene
```
Input:  (none)
Action: python -m core.graph_compactor --dry-run  (apply is manual)
        python -m core.why --backfill --apply
Output: Clean graph, why-chains resolved
```

**Exit condition**: Auditor clean, dreams distilled, history updated, graph compacted

---

## SEASON HANDOFF — THE FARMER'S LEDGER

Between every season, write to disk. Nothing lives in memory.

```
task_progress.md  ← Session block + NEXT list (exact commands, not wishes)
DNA graph         ← record_* / graphify_record (never hand-write)
Config files      ← Decoder writes trained values
Beat scripts      ← docs/beats/<feature>.beats.json
Specs             ← docs/features/<feature>.json or specs/<feature>.json
```

**THE RULE**: Any agent can pick up any batch from any season. The inputs are on disk.
The procedure is in this file. The outputs are written back to disk. No agent needs to
know what happened before or what happens next.

---

## QUICK REFERENCE — Season commands

```powershell
# SPRING
python -m core.council "<topic>" --rounds 2 --record
python -m core.graphify_record feature --name X --loop N --status designed

# SUMMER
python -m core.train_loop erisaid_mirror
python -c "from core.decoder import apply_genome; apply_genome(g, 'erisaid_mirror', dry_run=False)"
python -m core.task_board claim --agent <id>

# FALL
python -m core.beat_lint --beats docs/beats/X.beats.json
python -m core.sleepwalker --beats docs/beats/X.beats.json --session <name>
python -m core.graphify_record observe --feature X --verdict accepted --derived-from <simtest_id> --tacit --loop N
python -m core.postflight --phase "..." --result "..." --inheritance "..." --researched "..."

# WINTER
python -m core.train_loop <domain>
python -m core.dream_loop
python -m core.gardener --tend
python -m core.graph_compactor --dry-run
```
