import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

/**
 * Chimera Custom Tools — wraps core pipeline operations as pi tools.
 *
 * All commands run through Git Bash explicitly (`shell: GIT_BASH` below) because
 * Node's execSync ignores Pi's own `shellPath` setting and defaults to cmd.exe on
 * Windows. Paths are POSIX-mounted (E: -> /e/) to match that shell, per
 * AGENTS.md's "Windows Shell & Command Reference".
 */

const GIT_BASH = "C:/Users/allen/AppData/Local/Programs/PortableGit/bin/bash.exe";
const CHIMERA_ROOT = "/e/PythonChimera/Chimera";
const execOpts = (timeout: number) => ({ encoding: "utf-8" as const, timeout, shell: GIT_BASH });
const q = (s: string) => JSON.stringify(s);

export default function (pi: ExtensionAPI) {

  // ─── chimera_preflight ────────────────────────────────────────────────
  pi.registerTool({
    name: "chimera_preflight",
    label: "Chimera Pre-Flight",
    description: "Run full Chimera pre-flight check (graph health, GPA, loop board, inheritance, environment)",
    promptSnippet: "One-command project health: graph nodes, GPA trend, spiral loop board, pending heuristics, phantom pains, last pipeline run, LM Studio/MCP status",
    parameters: Type.Object({}),
    async execute() {
      const { execSync } = await import("node:child_process");
      try {
        const result = execSync(`cd ${CHIMERA_ROOT} && python -m core.preflight`, execOpts(60000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "preflight failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_postflight ───────────────────────────────────────────────
  pi.registerTool({
    name: "chimera_postflight",
    label: "Chimera Post-Flight",
    description: "Record phase completion with typed helpers (phase, result, inheritance, phantom pains)",
    parameters: Type.Object({
      phase: Type.String({ description: 'Phase name, e.g. "Verb_Look verification"' }),
      result: Type.String({ description: 'Verbatim UBT output or key result string' }),
      inheritance: Type.Optional(Type.String({ description: '<=3 sentences for next session' })),
      phantomPain: Type.Optional(Type.Array(Type.String())),
      painVerdicts: Type.Optional(Type.Array(Type.String({ description: '"<id>:confirmed|refuted|still-open"' }))),
    }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      const parts = [
        `cd ${CHIMERA_ROOT} && python -m core.postflight`,
        `--phase ${q(params.phase)}`,
        `--result ${q(params.result)}`,
      ];
      if (params.inheritance) parts.push(`--inheritance ${q(params.inheritance)}`);
      if (params.phantomPain?.length) {
        for (const p of params.phantomPain) parts.push(`--phantom-pain ${q(p)}`);
      }
      if (params.painVerdicts?.length) {
        for (const v of params.painVerdicts) parts.push(`--pain-verdict ${q(v)}`);
      }
      try {
        const result = execSync(parts.join(" "), execOpts(60000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "postflight failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_graph_query ──────────────────────────────────────────────
  // Real dispatcher: core/graphify_query_cli.py wraps graphify_query() from
  // core/graphify_interface.py directly -- the same unified query interface CLAUDE.md's
  // "g.query(...)" refers to. Confirmed live against chimera_dna_graph.json.
  pi.registerTool({
    name: "chimera_graph_query",
    label: "Chimera Graph Query",
    description: "Query the DNA graph: pattern, file, mutation, community, chain, config, campus, health, feature, pathway, or gpa",
    parameters: Type.Object({
      queryType: Type.String({ description: '"pattern" | "file" | "mutation" | "community" | "chain" | "config" | "campus" | "health" | "feature" | "pathway" | "gpa"' }),
      queryValue: Type.Optional(Type.String({ description: "Identifier for the query type, e.g. a feature name, pathway topic, or campus name" })),
    }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      let cmd = `cd ${CHIMERA_ROOT} && python -m core.graphify_query_cli ${q(params.queryType)}`;
      if (params.queryValue) cmd += ` ${q(params.queryValue)}`;
      try {
        const result = execSync(cmd, execOpts(30000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "graph query failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_run_sleepwalker ──────────────────────────────────────────
  pi.registerTool({
    name: "chimera_run_sleepwalker",
    label: "Chimera Sleepwalker",
    description: "Run sleepwalker beat script in PIE (AI playtester) — records SimPlaytest evidence to graph",
    parameters: Type.Object({
      beatsFile: Type.Optional(Type.String({ description: 'Beats file path, e.g. "docs/beats/verb_interactions.beats.json"' })),
      sessionName: Type.Optional(Type.String({ description: "Session name for chronicle" })),
    }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      let cmd = `cd ${CHIMERA_ROOT} && python -m core.sleepwalker`;
      cmd += ` --beats ${q(params.beatsFile ?? "docs/beats/verb_interactions.beats.json")}`;
      cmd += ` --session ${q(params.sessionName ?? `pi_agent_session`)}`;
      try {
        const result = execSync(cmd, execOpts(120000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "sleepwalker failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_build_project ────────────────────────────────────────────
  pi.registerTool({
    name: "chimera_build_project",
    label: "Chimera Build",
    description: "Compile Chimera project via UBT (Development or DebugGame config)",
    parameters: Type.Object({
      config: Type.Optional(Type.String({ description: 'Build config: "Development" (default) | "DebugGame"' })),
    }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      const config = params.config || "Development";
      const cmd = `cd ${CHIMERA_ROOT} && "/c/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" ChimeraEditor Win64 ${config} "E:/PythonChimera/Chimera/Chimera.uproject" -waitmutex`;
      try {
        const result = execSync(cmd, execOpts(300000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "build failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_record_feature ───────────────────────────────────────────
  pi.registerTool({
    name: "chimera_record_feature",
    label: "Chimera Record Feature",
    description: "Record a feature update via typed helper (avoids rejected_* junk nodes)",
    parameters: Type.Object({
      name: Type.String({ description: 'Feature name, e.g. "Verb_Look"' }),
      loop: Type.Number({ description: "Spiral loop number (required by the underlying CLI)" }),
      status: Type.String({ description: '"not_started" | "researching" | "verified" | "sim_verified" | "encoded" | "needs_refinement"' }),
      notes: Type.Optional(Type.String()),
    }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      let cmd = `cd ${CHIMERA_ROOT} && python -m core.graphify_record feature --name ${q(params.name)} --loop ${params.loop} --status ${q(params.status)}`;
      if (params.notes) cmd += ` --param ${q(`notes=${params.notes}`)}`;
      try {
        const result = execSync(cmd, execOpts(30000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "record_feature failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_run_rehearsal ────────────────────────────────────────────
  pi.registerTool({
    name: "chimera_run_rehearsal",
    label: "Chimera Rehearsal",
    description: "Run rehearsal engine to decide next candidate (veto-table-backed decision)",
    parameters: Type.Object({ useLM: Type.Optional(Type.Boolean()) }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      let cmd = `cd ${CHIMERA_ROOT} && python -m core.rehearsal --candidates-file docs/rehearsal_candidates.json --decide`;
      if (params.useLM) cmd += " --use-lm";
      try {
        const result = execSync(cmd, execOpts(60000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "rehearsal failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_dream_loop ───────────────────────────────────────────────
  pi.registerTool({
    name: "chimera_dream_loop",
    label: "Chimera Dream Loop",
    description: "Run nightly dream loop (distill failures → ≤2 heuristics, preview compaction)",
    parameters: Type.Object({}),
    async execute() {
      const { execSync } = await import("node:child_process");
      try {
        const result = execSync(`cd ${CHIMERA_ROOT} && python -m core.dream_loop`, execOpts(60000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "dream_loop failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_unblock ──────────────────────────────────────────────────
  pi.registerTool({
    name: "chimera_unblock",
    label: "Chimera Unblock",
    description: "Self-heal known blockers (editor/LM/PIE/git/disk)",
    parameters: Type.Object({
      ensure: Type.Optional(Type.String({ description: '"all" | "editor" | "lm" | "pie" | "git" | "disk"' })),
    }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      const cmd = `cd ${CHIMERA_ROOT} && python -m core.unblock --ensure ${q(params.ensure ?? "all")}`;
      try {
        const result = execSync(cmd, execOpts(60000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "unblock failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_doc_audit ────────────────────────────────────────────────
  pi.registerTool({
    name: "chimera_doc_audit",
    label: "Chimera Doc Audit",
    description: "Check docs-vs-code drift (nightly via floor)",
    parameters: Type.Object({}),
    async execute() {
      const { execSync } = await import("node:child_process");
      try {
        const result = execSync(`cd ${CHIMERA_ROOT} && python -m core.doc_audit`, execOpts(60000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "doc_audit failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_gardener_tend ────────────────────────────────────────────
  pi.registerTool({
    name: "chimera_gardener_tend",
    label: "Chimera Gardener Tend",
    description: "Auto-tend the heuristic queue (doc-organ rules self-promote, gate approvals queue)",
    parameters: Type.Object({ dryRun: Type.Optional(Type.Boolean()) }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      let cmd = `cd ${CHIMERA_ROOT} && python -m core.gardener --tend`;
      if (params.dryRun) cmd += " --dry-run";
      try {
        const result = execSync(cmd, execOpts(60000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "gardener failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_collapse_proxy ───────────────────────────────────────────
  pi.registerTool({
    name: "chimera_collapse_proxy",
    label: "Chimera Collapse Proxy",
    description: "Whole-experience observation sweep (holistic acceptance/rejection)",
    parameters: Type.Object({
      fromSimtest: Type.Optional(Type.String()),
      valence: Type.Optional(Type.String({ description: '"accepted" | "rejected"' })),
    }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      let cmd = `cd ${CHIMERA_ROOT} && python -m core.collapse_proxy`;
      if (params.fromSimtest) cmd += ` --from-simtest ${q(params.fromSimtest)}`;
      if (params.valence) cmd += ` --valence ${q(params.valence)}`;
      try {
        const result = execSync(cmd, execOpts(60000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "collapse_proxy failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_solver ───────────────────────────────────────────────────
  pi.registerTool({
    name: "chimera_solver",
    label: "Chimera Solver",
    description: "Figure out fixes for UNKNOWN blockers (fix-or-draft; bare 'blocked' forbidden)",
    parameters: Type.Object({
      blocker: Type.String({ description: "Description of the blocker" }),
      context: Type.Optional(Type.String({ description: "Verbatim error/context" })),
    }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      let cmd = `cd ${CHIMERA_ROOT} && python -m core.solver --blocker ${q(params.blocker)}`;
      if (params.context) cmd += ` --context ${q(params.context)}`;
      try {
        const result = execSync(cmd, execOpts(60000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "solver failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_graph_compactor ──────────────────────────────────────────
  pi.registerTool({
    name: "chimera_graph_compactor",
    label: "Chimera Graph Compactor",
    description: "Archive-never-delete graph hygiene (dry-run or apply)",
    parameters: Type.Object({
      action: Type.Optional(Type.String({ description: '"dry-run" | "apply"' })),
    }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      const flag = params.action === "apply" ? "--apply" : "--dry-run";
      const cmd = `cd ${CHIMERA_ROOT} && python -m core.graph_compactor ${flag}`;
      try {
        const result = execSync(cmd, execOpts(60000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "compactor failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_result_grader ────────────────────────────────────────────
  pi.registerTool({
    name: "chimera_result_grader",
    label: "Chimera Result Grader",
    description: "Grade a feature against the rubric (zero LM dependency in gate path)",
    parameters: Type.Object({
      feature: Type.String({ description: "Feature name to grade" }),
      evidenceFile: Type.Optional(Type.String({ description: "Path to ev.json evidence file" })),
    }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      let cmd = `cd ${CHIMERA_ROOT} && python -m core.result_grader --feature ${q(params.feature)}`;
      if (params.evidenceFile) cmd += ` --evidence ${q(params.evidenceFile)}`;
      try {
        const result = execSync(cmd, execOpts(60000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "result_grader failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_spiral_forks ─────────────────────────────────────────────
  pi.registerTool({
    name: "chimera_spiral_forks",
    label: "Chimera Spiral Forks",
    description: "Bounded sacrificial research forks (3 briefs: conservative/alternative/wild)",
    parameters: Type.Object({
      feature: Type.String({ description: "Feature to fork research for" }),
      useLM: Type.Optional(Type.Boolean()),
    }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      let cmd = `cd ${CHIMERA_ROOT} && python -m core.spiral_forks --feature ${q(params.feature)}`;
      if (params.useLM) cmd += " --use-lm";
      try {
        const result = execSync(cmd, execOpts(120000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "spiral_forks failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_pipeline_run ─────────────────────────────────────────────
  pi.registerTool({
    name: "chimera_pipeline_run",
    label: "Chimera Full Pipeline",
    description: "Run the full pipeline (DSL Parse → Code Gen → Build → Playtest → Report)",
    parameters: Type.Object({}),
    async execute() {
      const { execSync } = await import("node:child_process");
      try {
        const result = execSync(`cd ${CHIMERA_ROOT} && python run_deep_space_trader_pipeline.py`, execOpts(600000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "pipeline failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_telemetry_probe ──────────────────────────────────────────
  pi.registerTool({
    name: "chimera_telemetry_probe",
    label: "Chimera Telemetry Probe",
    description: "Run telemetry probe (crash-free log, fps vs target, growth) — measure FOREGROUNDED",
    parameters: Type.Object({ soakSeconds: Type.Optional(Type.Number()) }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      let cmd = `cd ${CHIMERA_ROOT} && python -m core.telemetry_probe --out telemetry_last.json`;
      if (params.soakSeconds) cmd += ` --soak ${params.soakSeconds}`;
      try {
        const result = execSync(cmd, execOpts(120000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "telemetry_probe failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_fix_dna_pollution ────────────────────────────────────────
  pi.registerTool({
    name: "chimera_fix_dna_pollution",
    label: "Chimera Fix DNA Pollution",
    description: "Quarantine junk nodes from key mismatches (run if graph has unknown_* nodes)",
    parameters: Type.Object({}),
    async execute() {
      const { execSync } = await import("node:child_process");
      try {
        const result = execSync(`cd ${CHIMERA_ROOT} && python fix_dna_key_mismatch_pollution.py`, execOpts(60000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "fix_dna failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── chimera_graphify_record ──────────────────────────────────────────
  // Generic dispatcher: passes recordType straight through as the subcommand name and lets
  // graphify_record.py's own argparse validate it (clear "invalid choice" error beats a
  // TypeScript-side guess at every subcommand's exact flags).
  pi.registerTool({
    name: "chimera_graphify_record",
    label: "Chimera Graphify Record",
    description: "Typed CLI for graph mutations (feature, pathway, loop, phase, grade, surprise, observe, heuristic, ...) — see core/graphify_record.py for the authoritative subcommand list",
    parameters: Type.Object({
      recordType: Type.String({ description: 'e.g. "feature" | "pathway" | "loop" | "phase" | "grade" | "surprise" | "observe" | "heuristic"' }),
      name: Type.Optional(Type.String()),
      verdict: Type.Optional(Type.String()),
      notes: Type.Optional(Type.String()),
      derivedFrom: Type.Optional(Type.String()),
    }),
    async execute(_toolCallId, params) {
      const { execSync } = await import("node:child_process");
      let cmd = `cd ${CHIMERA_ROOT} && python -m core.graphify_record ${params.recordType}`;
      if (params.name) cmd += ` --name ${q(params.name)}`;
      if (params.verdict) cmd += ` --verdict ${q(params.verdict)}`;
      if (params.notes) cmd += ` --notes ${q(params.notes)}`;
      if (params.derivedFrom) cmd += ` --derived-from ${q(params.derivedFrom)}`;
      try {
        const result = execSync(cmd, execOpts(60000));
        return { content: [{ type: "text", text: result.trim() }], details: { status: "success" } };
      } catch (err: any) {
        const msg = err.stderr?.toString() || err.message || "graphify_record failed";
        return { content: [{ type: "text", text: msg }], details: { status: "error" }, isError: true };
      }
    },
  });

  // ─── Session start notification ───────────────────────────────────────
  pi.on("session_start", async (_event, ctx) => {
    const sessionFile = ctx.sessionManager.getSessionFile();
    ctx.ui.notify(
      sessionFile ? `Chimera tools loaded (session: ${sessionFile})` : "Chimera tools loaded",
      "info"
    );
  });

  // ─── Tool call interception for safety ────────────────────────────────
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName === "chimera_build_project" || event.toolName === "chimera_pipeline_run") {
      ctx.ui.notify(`Running ${event.toolName} — this compiles/runs the full pipeline and may take several minutes.`, "info");
    }
  });
}
