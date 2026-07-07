export const meta = {
  name: 'chimera-task-cycling',
  description: 'Cycle through Chimera pending tasks one subagent at a time',
  phases: [
    { title: 'Cycling', detail: 'Process observation queue, heuristics, scholar implementation, GPA resolution in rotation' },
  ],
}

const CYCLE_TASKS = [
  'observation_queue_processing',
  'pending_heuristics_review',
  'scholar_implementation',
  'gpa_resolution',
]

let cycle_count = 0
// Loop until budget exhausted or max cycles reached
const MAX_CYCLES = 3

while (cycle_count < MAX_CYCLES && (budget.total === null || budget.remaining() > 150_000)) {
  cycle_count++
  log(`Starting workflow cycle ${cycle_count}`)
  
  for (const task of CYCLE_TASKS) {
    if (budget.total !== null && budget.remaining() <= 150_000) {
      break
    }
    
    log(`Processing task in cycle ${cycle_count}: ${task}`)
    
    const result = await agent(`Chimera workflow: Process the pending task '${task}'. 
      Context: Current state shows GPA is 0.3 (critically low, needs >= 1.0 to pass pre-flight), 
      observation queue has 14 features awaiting human's eyes (Verb_Look, Player_Character_Model_Visor_Apply, Verb_Shovel, Verb_Bend, Verb_PickUp, Verb_Drop, Tool_Weapon_Model, System_Economy, System_SaveLoad, System_Factions and more),
      pending heuristics H-15 (surprise: beat discovered expected gap) and H-16 (pathway: sleepwalker.beat_run -> partial) are pending approval in PENDING_HEURISTICS.md,
      scholar.py needs to be implemented for research corpus per DREAM_ROSTER.md TIER 1 gap,
      and the procedural dust-accumulation mask technical_research item needs 3+ cited sources.`, {
        phase: 'Cycling',
        label: `task:${task}`,
        effort: 'medium'
    })
    
    if (result) {
      log(`Task '${task}' result preview: ${String(result).substring(0, 200)}...`)
    } else {
      log(`Task '${task}' had no result or was skipped.`)
    }
  }
  
  log(`Cycle ${cycle_count} complete. Remaining budget: ${Math.round(budget.remaining()/1000)}k tokens`)
}

log(`Workflow completed ${cycle_count} cycles.`)
return { cycles_completed: cycle_count }