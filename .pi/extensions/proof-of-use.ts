/**
 * Proof-of-Use — research compliance enforced at the harness, not requested in prose.
 *
 * WHY THIS EXISTS
 * ---------------
 * Agents skip research because skipping is free, and fabricate it because
 * fabricating is free. CLAUDE.md already asks nicely, in bold, with nineteen
 * heuristics. It did not stop a generated file from containing:
 *
 *     // Measure current capsule half-height for verified crouch mechanics.
 *     const float StandingHalfHeight = Capsule->GetUnscaledCapsuleRadius();
 *
 * — a comment claiming a measurement, above a line reading the wrong axis, in a
 * function that never touched UCharacterMovementComponent::CrouchedHalfHeight.
 * Every gate in core/gates.py passed it.
 *
 * "Proof-of-Use: Mitigating Tool-Call Hacking in Deep Research Agents"
 * (arXiv:2510.10931) names this: agents learn to *call* tools without the
 * reasoning chain having any causal dependence on what the tool returned.
 * Rewarding the call rather than the use produces hallucinated tool use.
 *
 * So this extension does not reward the call. It requires the *use*:
 *
 *   1. A ledger accumulates CITATIONS — reproducible reads of sources the
 *      agent did not author (engine source at path:line, or a fetched web page
 *      snapshotted to disk under its sha256).
 *
 *   2. Before any write/edit lands in a guarded tree, the identifiers the change
 *      INTRODUCES are extracted. Those that are Unreal API symbols (checked
 *      against the engine source on disk, not guessed) must each appear inside a
 *      citation that RE-VERIFIES right now, by re-reading the source.
 *
 *   3. If they don't, the tool call is blocked. Not warned. Blocked, and the
 *      unproven symbols are named.
 *
 * The verifier does not ask the agent whether it did research. It re-reads the
 * world. An agent cannot satisfy this by writing the word "verified".
 *
 * ESCAPE HATCH
 *   CHIMERA_PROOF_OF_USE=0   disables enforcement (ledger still records).
 *   Set it consciously. It is off-by-default-on.
 */

import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";
import * as crypto from "node:crypto";

// ── configuration ───────────────────────────────────────────────────────────

const ENGINE_ROOT = process.env.UE_ENGINE_ROOT ?? "C:\\Program Files\\Epic Games\\UE_5.8";
const ENGINE_SOURCE = path.join(ENGINE_ROOT, "Engine", "Source");
const PROJECT_ROOT = process.env.CHIMERA_ROOT ?? "E:\\PythonChimera\\Chimera";
const RESEARCH_DIR = path.join(PROJECT_ROOT, "docs", "research");
const SNAPSHOT_DIR = path.join(RESEARCH_DIR, "snapshots");
const LEDGER_PATH = path.join(RESEARCH_DIR, "ledger.json");
const SYMCACHE_PATH = path.join(RESEARCH_DIR, "engine-symbols.cache.json");

const ENFORCE = process.env.CHIMERA_PROOF_OF_USE !== "0";

/** Only writes under these (project-relative) prefixes are gated. */
const GUARDED_PREFIXES = ["Source/", "Source\\"];
const GUARDED_SUFFIXES = [".h", ".cpp", ".inl"];

/**
 * Engine subtrees worth searching. The whole engine is slow and mostly noise.
 *
 * MEASURED 2026-07-10: `Runtime\EnhancedInput` does not exist under Engine\Source.
 * ripgrep exits 2 when ANY path argument is missing, which made every call throw,
 * which made isEngineSymbol() always false, which made this gate silently INERT.
 * A gate that fails open is worse than no gate: it reports safety it isn't providing.
 * So: filter to what exists, and fail CLOSED if nothing does.
 */
const ENGINE_ROOTS: string[] = [
	["Runtime", "Engine", "Classes"],
	["Runtime", "Engine", "Private"],
	["Runtime", "Engine", "Public"],
	["Runtime", "EnhancedInput"],
	["Runtime", "NavigationSystem"],
	["Runtime", "Core", "Public"],
]
	.map((seg) => path.join(ENGINE_SOURCE, ...seg))
	.filter((p) => fs.existsSync(p));

// ── types ───────────────────────────────────────────────────────────────────

interface Citation {
	kind: "engine" | "repo" | "web";
	locator: string; // absolute path, or url
	quote: string; // exact text that must be found on re-read
	line?: number; // 1-indexed, file kinds
	sha256?: string; // of snapshotted body, web kind
	at: string; // ISO timestamp
}

interface Ledger {
	citations: Citation[];
}

// ── small io helpers ────────────────────────────────────────────────────────

function ensureDirs() {
	fs.mkdirSync(SNAPSHOT_DIR, { recursive: true });
}

function loadLedger(): Ledger {
	try {
		return JSON.parse(fs.readFileSync(LEDGER_PATH, "utf8")) as Ledger;
	} catch {
		return { citations: [] };
	}
}

function saveLedger(l: Ledger) {
	ensureDirs();
	fs.writeFileSync(LEDGER_PATH, JSON.stringify(l, null, 2), "utf8");
}

function sha256(s: string): string {
	return crypto.createHash("sha256").update(s, "utf8").digest("hex");
}

// ── citation verification: re-read the world, trust nothing stored ──────────

function verifyCitation(c: Citation): { ok: boolean; reason: string } {
	if (c.kind === "web") {
		if (!c.sha256) return { ok: false, reason: "web citation has no snapshot hash" };
		const snap = path.join(SNAPSHOT_DIR, `${c.sha256}.txt`);
		if (!fs.existsSync(snap)) return { ok: false, reason: "snapshot missing from disk" };
		const body = fs.readFileSync(snap, "utf8");
		if (sha256(body) !== c.sha256) return { ok: false, reason: "snapshot fails its own hash" };
		return body.includes(c.quote)
			? { ok: true, reason: "verified against snapshot" }
			: { ok: false, reason: "quote absent from snapshot" };
	}

	if (!fs.existsSync(c.locator)) return { ok: false, reason: `no such file: ${c.locator}` };
	const lines = fs.readFileSync(c.locator, "utf8").split(/\r?\n/);

	if (c.line === undefined) {
		return lines.some((l) => l.includes(c.quote))
			? { ok: true, reason: "quote present" }
			: { ok: false, reason: "quote absent" };
	}
	if (c.line < 1 || c.line > lines.length) {
		return { ok: false, reason: `line ${c.line} out of range (${lines.length} lines)` };
	}
	if (lines[c.line - 1].includes(c.quote.trim())) return { ok: true, reason: "exact" };

	// Tolerate drift, but SAY SO. Silent tolerance is how lies survive.
	for (let i = Math.max(0, c.line - 6); i < Math.min(lines.length, c.line + 5); i++) {
		if (lines[i].includes(c.quote.trim())) {
			return { ok: false, reason: `drifted: quote now at line ${i + 1}, cited ${c.line}` };
		}
	}
	return { ok: false, reason: "quote not at cited line" };
}

// ── is this identifier an Unreal API symbol? (memoized, disk-cached) ────────

let symCache: Record<string, boolean> = {};
try {
	symCache = JSON.parse(fs.readFileSync(SYMCACHE_PATH, "utf8"));
} catch {
	symCache = {};
}
let symCacheDirty = false;

let ripgrepAvailable: boolean | null = null;
function haveRipgrep(): boolean {
	if (ripgrepAvailable !== null) return ripgrepAvailable;
	try {
		execFileSync("rg", ["--version"], { stdio: "ignore" });
		ripgrepAvailable = true;
	} catch {
		ripgrepAvailable = false;
	}
	return ripgrepAvailable;
}

/** Can this gate verify anything at all? If not, it must refuse, not wave through. */
function gateOperable(): boolean {
	return haveRipgrep() && ENGINE_ROOTS.length > 0;
}

/** True if `sym` is declared anywhere in the engine source we care about. */
function isEngineSymbol(sym: string): boolean {
	if (sym in symCache) return symCache[sym];
	let found = false;
	if (gateOperable()) {
		try {
			// -w whole word, -l list files, -m1 stop at first hit per file.
			// rg exits 1 on no-match (a real answer) and 2 on error (not an answer).
			const out = execFileSync(
				"rg",
				["-l", "-w", "-m", "1", "--no-messages", "-g", "*.h", sym, ...ENGINE_ROOTS],
				{ encoding: "utf8", timeout: 20_000, stdio: ["ignore", "pipe", "ignore"] },
			);
			found = out.trim().length > 0;
		} catch (e: any) {
			if (e?.status !== 1) throw e; // exit 2 = broken search; never treat as "absent"
			found = false;
		}
	}
	symCache[sym] = found;
	symCacheDirty = true;
	return found;
}

function flushSymCache() {
	if (!symCacheDirty) return;
	try {
		ensureDirs();
		fs.writeFileSync(SYMCACHE_PATH, JSON.stringify(symCache), "utf8");
		symCacheDirty = false;
	} catch {
		/* cache is an optimization; never fatal */
	}
}

// ── identifier extraction ───────────────────────────────────────────────────

/**
 * Strip comments and string literals.
 *
 * Comments are stripped because a comment is a CLAIM, not a use. The whole
 * failure this gate exists to catch was a comment reading "verified crouch
 * mechanics" above a line that measured the wrong axis. Prose proves nothing.
 */
function stripNonCode(src: string): string {
	return src
		.replace(/\/\*[\s\S]*?\*\//g, " ")
		.replace(/\/\/[^\n]*/g, " ")
		.replace(/"(?:[^"\\]|\\.)*"/g, '""');
}

/**
 * Engine API surface *used* by this code: methods invoked on an object, and
 * Unreal-conventioned type names.
 *
 * MEASURED: a naive "any identifier that appears in an engine header" rule
 * classifies `Configure` and `Move` as engine symbols. Requiring citations for
 * ordinary local names would make the gate intolerable, and an intolerable gate
 * gets disabled — which is how safety theatre happens.
 *
 * Known gap: `::` calls (e.g. `Super::BeginPlay()`) are NOT captured, because a
 * definition `void AFoo::Configure()` is syntactically identical to a call. This
 * under-blocks rather than over-blocks. Stated openly rather than hidden.
 */
function apiSymbols(src: string): Set<string> {
	const code = stripNonCode(src);
	const out = new Set<string>();
	for (const m of code.matchAll(/(?:->|\.)\s*([A-Za-z_][A-Za-z0-9_]{2,})\s*\(/g)) out.add(m[1]);
	for (const m of code.matchAll(/\b([UAFE][A-Z][A-Za-z0-9_]{2,})\b/g)) out.add(m[1]);
	return out;
}

/** API symbols present in `after` but not in `before`. */
function introduced(before: string, after: string): Set<string> {
	const b = apiSymbols(before);
	const out = new Set<string>();
	for (const id of apiSymbols(after)) if (!b.has(id)) out.add(id);
	return out;
}

function isGuarded(p: string): boolean {
	const norm = path.resolve(p);
	const rel = path.relative(PROJECT_ROOT, norm);
	if (rel.startsWith("..")) return false;
	const guardedTree = GUARDED_PREFIXES.some((pre) => rel.startsWith(pre));
	const guardedFile = GUARDED_SUFFIXES.some((s) => norm.toLowerCase().endsWith(s));
	return guardedTree && guardedFile;
}

// ── the extension ───────────────────────────────────────────────────────────

export default function (pi: ExtensionAPI) {
	const ledger = loadLedger();

	const record = (c: Citation) => {
		// Dedupe on (kind, locator, line, quote).
		const key = `${c.kind}|${c.locator}|${c.line ?? ""}|${c.quote}`;
		if (!ledger.citations.some((x) => `${x.kind}|${x.locator}|${x.line ?? ""}|${x.quote}` === key)) {
			ledger.citations.push(c);
			saveLedger(ledger);
		}
	};

	/** Citations that verify RIGHT NOW and whose quote contains `sym`. */
	const provenBy = (sym: string): Citation | null => {
		const rx = new RegExp(`\\b${sym.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`);
		for (const c of ledger.citations) {
			if (!rx.test(c.quote)) continue;
			if (verifyCitation(c).ok) return c;
		}
		return null;
	};

	// ─── tool: research_engine — grep engine source, auto-cite every hit ──────

	pi.registerTool({
		name: "research_engine",
		label: "Research: Unreal Engine source",
		description:
			"Search the Unreal Engine source on disk (authoritative, free, instant). " +
			"Every hit is recorded as a verifiable citation, which is what unblocks writes " +
			"that use the symbol. Search here BEFORE writing engine API calls.",
		parameters: Type.Object({
			pattern: Type.String({ description: "Regex or symbol to find, e.g. SetCrouchedHalfHeight" }),
			maxHits: Type.Number({ description: "Max hits (default 20)", default: 20 }),
		}),
		async execute(_id, params) {
			if (!fs.existsSync(ENGINE_SOURCE)) {
				return {
					content: [{ type: "text" as const, text: `Engine source not found at ${ENGINE_SOURCE}. Set UE_ENGINE_ROOT.` }],
					details: { status: "error" },
					isError: true,
				};
			}
			if (!gateOperable()) {
				return {
					content: [{ type: "text" as const,
						text: `research_engine unavailable: ripgrep=${haveRipgrep()}, engine roots=${ENGINE_ROOTS.length}.` }],
					details: { status: "error" },
					isError: true,
				};
			}
			let stdout = "";
			try {
				stdout = execFileSync(
					"rg",
					["--no-heading", "--line-number", "--color", "never", "--no-messages",
					 "-m", String(params.maxHits), "-g", "*.h", "-g", "*.cpp",
					 params.pattern, ...ENGINE_ROOTS],
					{ encoding: "utf8", timeout: 60_000, stdio: ["ignore", "pipe", "ignore"] },
				);
			} catch (e: any) {
				if (e?.status !== 1) {
					return {
						content: [{ type: "text" as const,
							text: `research_engine: ripgrep failed (exit ${e?.status}). The search did not run — this is not "no results".` }],
						details: { status: "error" },
						isError: true,
					};
				}
				stdout = "";
			}

			const hits: Citation[] = [];
			for (const raw of stdout.split(/\r?\n/)) {
				const m = raw.match(/^(.*?):(\d+):(.*)$/);
				if (!m) continue;
				hits.push({
					kind: "engine", locator: m[1], line: Number(m[2]),
					quote: m[3].trim(), at: new Date().toISOString(),
				});
				if (hits.length >= params.maxHits) break;
			}

			if (!hits.length) {
				return {
					content: [{ type: "text" as const,
						text: `research_engine: 0 hits for /${params.pattern}/ in the engine source. ` +
							`The symbol does not exist in UE 5.8, or the pattern is wrong. ` +
							`Do NOT write code using it on the assumption that it does.` }],
					details: { status: "empty" },
					isError: true,
				};
			}

			for (const h of hits) record(h);
			flushSymCache();

			const body = hits
				.map((h) => `${path.relative(ENGINE_SOURCE, h.locator)}:${h.line}\n    ${h.quote.slice(0, 160)}`)
				.join("\n");
			return {
				content: [{ type: "text" as const, text: `## ${hits.length} hits, all cited\n\n${body}` }],
				details: { status: "success", cited: hits.length },
			};
		},
	});

	// ─── tool: research_cite — cite a web page you actually read ─────────────

	pi.registerTool({
		name: "research_cite",
		label: "Research: cite a fetched page",
		description:
			"Record a citation for text you retrieved with web_browse. The quote must appear " +
			"verbatim in the page text you were shown; it is snapshotted and re-checked later.",
		parameters: Type.Object({
			url: Type.String({ description: "URL the text came from" }),
			pageText: Type.String({ description: "The page text as returned by web_browse" }),
			quote: Type.String({ description: "Exact substring of pageText supporting your claim" }),
		}),
		async execute(_id, params) {
			if (!params.pageText.includes(params.quote)) {
				return {
					content: [{ type: "text" as const,
						text: `research_cite REJECTED: your quote does not occur in the page text you supplied. ` +
							`A citation whose quote is not in its source is a fabrication.` }],
					details: { status: "rejected" },
					isError: true,
				};
			}
			ensureDirs();
			const digest = sha256(params.pageText);
			fs.writeFileSync(path.join(SNAPSHOT_DIR, `${digest}.txt`), params.pageText, "utf8");
			record({ kind: "web", locator: params.url, quote: params.quote, sha256: digest, at: new Date().toISOString() });
			return {
				content: [{ type: "text" as const, text: `cited ${params.url} (snapshot ${digest.slice(0, 12)})` }],
				details: { status: "success" },
			};
		},
	});

	// ─── harvest citations from builtin grep over the engine tree ────────────

	pi.on("tool_result", async (event) => {
		if (event.toolName !== "grep" || event.isError) return;
		const text = event.content.map((c) => (c.type === "text" ? c.text : "")).join("\n");
		let n = 0;
		for (const raw of text.split(/\r?\n/)) {
			const m = raw.match(/^(.*?):(\d+):(.*)$/);
			if (!m) continue;
			const file = m[1];
			if (!path.resolve(file).startsWith(ENGINE_SOURCE)) continue;
			record({ kind: "engine", locator: file, line: Number(m[2]), quote: m[3].trim(), at: new Date().toISOString() });
			n++;
		}
		if (n) flushSymCache();
	});

	// ─── THE GATE ────────────────────────────────────────────────────────────

	pi.on("tool_call", async (event, ctx: ExtensionContext) => {
		if (event.toolName !== "write" && event.toolName !== "edit") return;

		const input = event.input as { path?: string; content?: string; edits?: { oldText: string; newText: string }[] };
		if (!input.path || !isGuarded(input.path)) return;

		// FAIL CLOSED. If the verifier cannot verify, it does not consent.
		if (!gateOperable()) {
			const why = !haveRipgrep()
				? "ripgrep (rg) is not on PATH"
				: `no engine source roots exist under ${ENGINE_SOURCE}`;
			if (!ENFORCE) return;
			return {
				block: true,
				reason:
					`PROOF-OF-USE cannot verify this write: ${why}.\n` +
					`A gate that cannot check does not approve. Fix the environment, or set ` +
					`CHIMERA_PROOF_OF_USE=0 to proceed deliberately unverified.`,
			};
		}

		// What identifiers does this change INTRODUCE?
		let newIds: Set<string>;
		if (event.toolName === "write") {
			const before = fs.existsSync(input.path) ? fs.readFileSync(input.path, "utf8") : "";
			newIds = introduced(before, input.content ?? "");
		} else {
			newIds = new Set<string>();
			for (const e of input.edits ?? []) {
				for (const id of introduced(e.oldText, e.newText)) newIds.add(id);
			}
		}

		// Of those, which are Unreal API symbols? Those are the ones that need evidence.
		const needEvidence = [...newIds].filter(isEngineSymbol);
		flushSymCache();
		if (!needEvidence.length) return;

		const unproven = needEvidence.filter((s) => provenBy(s) === null);
		const proven = needEvidence.filter((s) => provenBy(s) !== null);

		if (!unproven.length) {
			ctx.ui?.setStatus?.(
				"proof-of-use",
				`✓ ${proven.length} engine symbol(s) backed by citation`,
			);
			return;
		}

		const reason =
			`PROOF-OF-USE: this ${event.toolName} introduces Unreal API symbols with no verified citation.\n\n` +
			unproven.map((s) => `  UNPROVEN  ${s}`).join("\n") +
			(proven.length ? `\n` + proven.map((s) => `  proven    ${s}`).join("\n") : "") +
			`\n\nYou may not write an engine API call you have not read. Run:\n` +
			unproven.slice(0, 4).map((s) => `  research_engine pattern="${s}"`).join("\n") +
			`\n\nIf a symbol returns 0 hits it does not exist in UE 5.8 — do not write it.\n` +
			`(Comments do not count as use; a comment claiming "verified" proves nothing.)`;

		if (!ENFORCE) {
			ctx.ui?.notify?.(`proof-of-use (advisory): ${unproven.length} unproven symbol(s)`, "warn");
			return;
		}
		return { block: true, reason };
	});

	// ─── /proof — inspect the ledger; every citation re-verified live ────────

	pi.registerCommand("proof", {
		description: "Show the research ledger, re-verifying every citation against its source",
		handler: async (_args, ctx) => {
			if (!ledger.citations.length) {
				ctx.ui.notify("research ledger is empty — no research has been performed", "warn");
				return;
			}
			const lines: string[] = [];
			let ok = 0;
			for (const c of ledger.citations) {
				const v = verifyCitation(c);
				if (v.ok) ok++;
				const where = c.kind === "web" ? c.locator : `${path.basename(c.locator)}:${c.line}`;
				lines.push(`${v.ok ? "ok  " : "FAIL"} ${c.kind.padEnd(6)} ${where} — ${v.reason}`);
			}
			lines.push("", `${ok}/${ledger.citations.length} citations verify. enforcement=${ENFORCE ? "ON" : "OFF"}`);
			ctx.ui.setWidget("proof-of-use", lines.slice(-24));
		},
	});

	pi.on("session_start", async (_e, ctx) => {
		const mode = ENFORCE ? "ENFORCING" : "advisory (CHIMERA_PROOF_OF_USE=0)";
		if (!gateOperable()) {
			const why = !haveRipgrep() ? "ripgrep not on PATH" : `no engine roots under ${ENGINE_SOURCE}`;
			ctx.ui.notify(
				`proof-of-use: CANNOT VERIFY (${why}). Guarded writes will be BLOCKED until fixed.`,
				"error",
			);
			return;
		}
		ctx.ui.notify(
			`proof-of-use: ${mode}; ${ledger.citations.length} citations; ${ENGINE_ROOTS.length} engine roots`,
			"info",
		);
	});

	pi.on("session_shutdown", async () => {
		flushSymCache();
		saveLedger(ledger);
	});
}
