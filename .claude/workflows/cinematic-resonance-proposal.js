export const meta = {
  name: 'cinematic-resonance-proposal',
  description: 'Architect the Cinematic Resonance Extraction methodology (film/TV -> Chimera vertical slice) as an actionable, honesty-verified proposal document',
  whenToUse: 'Invoke when ready to design the film->game extraction pipeline (after the current game vision ships). args: { work?, mediaNotes?, outPath? } — defaults to The Expanse. Produces docs/CINEMATIC_RESONANCE_PROPOSAL.md; ~14 agents.',
  phases: [
    { title: 'Ground', detail: 'live Chimera state + real integration points (never trust stale counts)' },
    { title: 'Architect', detail: '6 section architects in parallel' },
    { title: 'Refute', detail: 'adversarial honesty pass per section' },
    { title: 'Synthesize', detail: 'assemble and write the proposal document' },
  ],
}

const WORK = (args && args.work) || 'The Expanse — 6-season television series, 62 episodes'
const MEDIA = (args && args.mediaNotes) || 'raw media assumed: video files + subtitles per episode; exact codecs/paths unknown at design time'
const OUT = (args && args.outPath) || 'E:/PythonChimera/Chimera/docs/CINEMATIC_RESONANCE_PROPOSAL.md'

const CANON = `
## THE DESIGN FRAME (canon — the Gardener's vision; do not dilute)
Chimera's Generational Protocol becomes GAMEPLAY. The player lives one generation per run:
- DAWN: receives the Will and Forewarnings (inherited heuristics) of prior generations.
- DAY: meets observations — surprises/events that challenge inherited heuristics; the player assays them.
- NIGHT: dream_loop consolidation distills the day's surprises into <=2 candidate lessons.
- TESTAMENT: the player pays an irreversible cost (a phantom pain chosen), writes their Will.
- FROZEN SKY: a starfield rendering this testament among all previous testaments (conceptual, not yet built).
TWO INVIOLABLE DESIGN LAWS:
- Law #1 (Erisaid): the game never explains the player's WHY. Extraction must preserve the mystery of motivation.
- Law #2 (Love): identity never gates anything; love has exactly one machine-readable signature — cost paid and attention given. The game verifies love through cost, never through identity or narrative exposition.

## THE COMMISSION (answer ALL of it)
Target work: ${WORK}. Media: ${MEDIA}. Methodology MUST generalize to any narrative work.
S1 EXTRACTION ARCHITECTURE — multi-modal streams and their Chimera mappings:
  Visual frames (shot detection, object/color/composition) -> shot graph, palettes, composition rules -> environments/assets/mood.
  Dialogue audio (STT, diarization, sentiment) -> labeled transcript + valence -> dialogue/narrative graph.
  Music/sound (spectral, tempo/key, tension mapping) -> tension curve -> pacing, sleep/wake rhythm.
  Script/subtitles (scene parsing, character extraction, plot graph) -> narrative graph, arcs -> heuristics, observations.
  Temporal (scene duration, cut speed, dialogue pacing) -> rhythm map, beat structure -> time dilation, game-loop timing.
S2 AUTOMATED PIPELINE — end-to-end from raw media to playable demo: ingestion; FFmpeg keyframe extraction; vision models (CLIP/SAM-class or VLM) for shots/objects; Whisper for transcription; Librosa-class spectral analysis; LLM narrative-graph parsing; a central synthesis LLM mapping features onto Chimera structures; feed into the EXISTING pipeline (dream_loop, asset generation, graphify_record); output a playable Generation Protocol demo. Name concrete tools with honest maturity flags; prefer what already runs locally (LM Studio, MCPStdioClient) where sane.
S3 MAPPING RULES — a formal translation layer, e.g.: protagonist central conflict -> phantom pain; supporting-character advice -> heuristic; plot twist -> observation; climax -> testament; character death/departure -> Frozen Sky star; visual motif -> asset. Extend, formalize (input signature -> output record schema -> which graphify_record call), give per-rule confidence.
S4 DEMO OUTPUT — the player's vertical-slice experience, Dawn through Testament through Frozen Sky, concretely staged with the extracted Expanse material as the worked example.
S5 TECHNICAL REQUIREMENTS — compute (local-first: this machine runs UE5.8 + LM Studio; state honest VRAM/hours), model stack, storage (62 episodes raw + intermediates + assets), integration points into the existing Python pipeline (name the real modules), timeline to first demo.
S6 PHILOSOPHICAL ALIGNMENT — how extraction upholds both Design Laws, mechanically not rhetorically.
PLUS: scalability to arbitrary works; emotional/narrative fidelity limits; player agency vs watching; what grade-A would demand of the pipeline; the AI's role (tool/collaborator/witness — argue a position).
FINAL BAR: actionable within 48h by an engineer; honest about unknowns/risks; tone = ambitious, grounded, iterative.`

phase('Ground')
log('Reading live Chimera state — the commission text carries stale counts; ground truth wins')
const ground = await agent(`You are the ground-truth auditor for the Chimera project (E:\\PythonChimera, python workdir E:\\PythonChimera\\Chimera).
Run: cd E:\\PythonChimera\\Chimera && python -m core.preflight  (capture queue counts, GPA, open phantom pains, pending heuristics).
Then grep-selectively (never wholesale): docs/GENERATION_PROTOCOL.md (circadian spec), docs/DEMO_ARCHITECTURE.md (current demo program), core/ entry points relevant to an extraction pipeline: dream_loop.py, heuristic_distiller.py, graphify_record.py CLI surface, asset_generator.py, result_grader.py, telemetry_probe.py (MCPStdioClient), spiral_forks.py.
RETURN <=650 words: (a) live counts (heuristics pending / observation queue / open pains) with the note that any commission text citing other numbers is stale; (b) the exact record-writing surfaces (CLI commands + typed helpers) an extraction pipeline could legally write through (typed recording only — never raw mutate); (c) the gates any generated content must pass (result_grader thresholds, build gate, human observation protocol); (d) what LM Studio currently serves and the vision-layer policy; (e) 3 integration risks you can already see.`,
  { label: 'ground-truth', phase: 'Ground', effort: 'medium' })
const G = ground || '(ground audit failed — architects must flag every integration claim as unverified)'

phase('Architect')
log('6 section architects in parallel')
const CHARTERS = [
  { key: 'S1-extraction', focus: 'SECTION 1 Extraction Architecture. Own the multi-modal stream table: per stream give method, concrete tooling, output schema, and the exact Chimera component + record type it lands in. Define the intermediate "resonance graph" store and its relationship to the DNA graph (docs/chimera_dna_graph.json) — additive, typed, archive-never-delete.' },
  { key: 'S2-pipeline', focus: 'SECTION 2 Automated Pipeline. Own the end-to-end DAG from raw media to playable demo: stages, tools, models, checkpointing, resumability, cost per episode, and where each stage writes via the typed recording surfaces from the ground brief. Local-first (LM Studio/qwen-class models, Whisper, FFmpeg, Librosa); flag any stage that honestly needs a frontier model and the fallback if unavailable.' },
  { key: 'S3-mapping', focus: 'SECTION 3 Mapping Rules. Own the formal translation layer: each rule as (cinematic signature -> detection method -> Chimera record schema -> exact graphify_record/typed-helper call -> confidence + failure mode). Cover at minimum: central conflict->phantom pain, mentor advice->heuristic, plot twist->observation, climax->testament, death/departure->Frozen Sky star, visual motif->asset, tension curve->circadian pacing. Add rules the commission missed; mark speculative ones.' },
  { key: 'S4-demo', focus: 'SECTION 4 Demo Output. Own the player experience of the vertical slice, Dawn->Day->Night->Testament->Frozen Sky, using extracted Expanse material as the staged worked example (choose one season/arc and justify). Show how it differs from watching the show (agency), and how the Regolith Yard / Titan Run demo machinery (docs/DEMO_ARCHITECTURE.md) is reused rather than duplicated.' },
  { key: 'S5-tech', focus: 'SECTION 5 Technical Requirements + Implementation Roadmap. Own compute/storage/model-stack sizing for 62 episodes (state assumptions: resolution, codec, hours), the integration contract with the existing Python pipeline (name real modules from the ground brief), a phased timeline with cycle-sized milestones per the handoff invariant (weak-model-executable items marked), and what grade-A demands beyond the current grade-B pipeline.' },
  { key: 'S6-philosophy', focus: 'SECTION 6 Philosophical Alignment + the AI role question. Own the two Design Laws as MECHANICAL constraints on extraction (what the pipeline must refuse to extract or expose: no motivation exposition into player-facing text — Erisaid; no identity-gated content, love only as cost-paid/attention-given signatures — Love). Define machine-checkable lints for both laws that run in the pipeline. Argue one position on the AI as tool/collaborator/witness, consistent with the Generational Protocol’s existing agent role (agents route, never originate verdicts).' },
]
const sections = await parallel(CHARTERS.map(ch => () => agent(`You are one of six section architects for the Cinematic Resonance Extraction proposal. Other architects own the other sections — stay in your lane, cross-reference by section number only.
${CANON}
## LIVE GROUND TRUTH (verified this run — overrides any stale numbers above)
${G}
## YOUR CHARTER
${ch.focus}
RETURN: your section as final-draft markdown, <=900 words, every tool/model/module named concretely with an honesty flag where maturity or fit is unproven. No filler, no restating the commission.`,
  { label: `arch:${ch.key}`, phase: 'Architect', effort: 'high' })))
const S = sections.map((s, i) => s || `(architect ${CHARTERS[i].key} failed — mark section as TODO in synthesis)`)

phase('Refute')
log('Adversarial honesty pass — one refuter per section')
const refutations = await parallel(S.map((sec, i) => () => agent(`You are an adversarial reviewer on the Chimera project. Your ONLY job is to attack this proposal section for: invented or misnamed tools/models; integration claims that contradict the ground brief; costs/timelines that are fantasy; violations of the two Design Laws; anything an engineer could NOT start within 48h; missing failure modes. Chimera culture: a recorded failure beats a fake success; never trust success:true.
## GROUND TRUTH
${G}
## SECTION UNDER ATTACK (${CHARTERS[i].key})
${sec}
RETURN <=300 words: numbered list of defects with severity (FATAL/MAJOR/MINOR) and the one-line fix for each. If genuinely sound, say so and list residual risks.`,
  { label: `refute:${CHARTERS[i].key}`, phase: 'Refute', effort: 'medium' })))
const R = refutations.map(r => r || '(refuter failed — treat section as unreviewed)')

phase('Synthesize')
const summary = await agent(`You are the chief editor assembling the final Cinematic Resonance Extraction proposal for the Chimera project.
${CANON}
## LIVE GROUND TRUTH
${G}
## SECTIONS (apply every FATAL/MAJOR fix from the matching refutation; fold MINOR fixes where cheap; keep honesty flags)
${S.map((sec, i) => `\n===== ${CHARTERS[i].key} =====\n${sec}\n----- refutation -----\n${R[i]}`).join('\n')}
## TASK
Write the complete proposal to ${OUT} using the Write tool (overwrite if present). Structure: # Cinematic Resonance Extraction — <subtitle> / Executive Summary / 1 Extraction Architecture / 2 Automated Pipeline / 3 Mapping Rules / 4 Demo Output / 5 Technical Requirements / 6 Philosophical Alignment / 7 Implementation Roadmap / 8 Open Questions & Risks (consolidate every surviving refuter concern here honestly). <=5000 words, every command/module copy-pasteable, cycle-sized roadmap items carrying recipes per the handoff invariant.
THEN return only: a 10-line executive digest + the output path + a one-line git-commit suggestion. Do NOT return the full document text.`,
  { label: 'synthesize', phase: 'Synthesize', effort: 'high' })

return { outPath: OUT, work: WORK, digest: summary }
