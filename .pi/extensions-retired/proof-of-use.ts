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

/**
 * Resolve the ripgrep binary ONCE, by absolute path — do not trust the ambient
 * PATH. Pi launched from a normal shell does not inherit every tool's directory,
 * and a gate that disables itself because `rg` isn't on PATH fails closed and
 * blocks every guarded write. (Reported in the field 2026-07-10.)
 *
 * Order: explicit override, then PATH, then known install locations including the
 * Amp CLI's bundled copy and @vscode/ripgrep. Returns an absolute path or null.
 */
let rgResolved: string | null | undefined; // undefined = not yet resolved

function ripgrepPath(): string | null {
	if (rgResolved !== undefined) return rgResolved;

	const home = process.env.USERPROFILE ?? process.env.HOME ?? "";
	const local = process.env.LOCALAPPDATA ?? "";
	const candidates = [
		process.env.CHIMERA_RG, // explicit override wins
		"rg", // PATH
		path.join(home, ".amp", "bin", "rg.exe"),
		path.join(local, "Programs", "Microsoft VS Code", "resources", "app", "node_modules.asar.unpacked", "@vscode", "ripgrep", "bin", "rg.exe"),
		"C:\\Program Files\\Microsoft VS Code\\resources\\app\\node_modules.asar.unpacked\\@vscode\\ripgrep\\bin\\rg.exe",
		path.join(home, "scoop", "shims", "rg.exe"),
		"C:\\ProgramData\\chocolatey\\bin\\rg.exe",
	].filter((c): c is string => !!c);

	for (const cand of candidates) {
		try {
			execFileSync(cand, ["--version"], { stdio: "ignore", timeout: 10_000 });
			rgResolved = cand;
			return rgResolved;
		} catch {
			/* try next */
		}
	}
	rgResolved = null;
	return rgResolved;
}

function haveRipgrep(): boolean {
	return ripgrepPath() !== null;
}

/** Can this gate verify anything at all? If not, it must refuse, not wave through. */
function gateOperable(): boolean {
	return haveRipgrep() && ENGINE_ROOTS.length > 0;
}

/**
 * True if `sym` is declared in THIS PROJECT's own source.
 *
 * The gate's question is not "does this symbol exist in the engine" — asking
 * that exempts hallucinated API calls, since an invented name is never found and
 * so was never checked. (Measured: `SetCapsuleHalfHeightXYZ` passed clean.)
 *
 * The question is "is this call ours". Anything that isn't ours is a foreign API
 * and needs a citation. A symbol that exists nowhere therefore has no citation
 * available, and can never pass — which is the correct outcome.
 */
function isProjectSymbol(sym: string): boolean {
	const key = `proj:${sym}`;
	if (key in symCache) return symCache[key];
	let found = false;
	const src = path.join(PROJECT_ROOT, "Source");
	if (haveRipgrep() && fs.existsSync(src)) {
		try {
			const out = execFileSync(
				ripgrepPath()!,
				["-l", "-m", "1", "--no-messages", "-g", "*.h", "-g", "*.cpp", `\\b${sym}\\s*\\(`, src],
				{ encoding: "utf8", timeout: 20_000, stdio: ["ignore", "pipe", "ignore"] },
			);
			found = out.trim().length > 0;
		} catch (e: any) {
			if (e?.status !== 1) throw e; // exit 2 = broken search; never treat as "absent"
			found = false;
		}
	}
	symCache[key] = found;
	symCacheDirty = true;
	return found;
}

/** Classes and methods DEFINED by the incoming text itself. Never foreign. */
function locallyDefined(src: string): Set<string> {
	const code = stripNonCode(src);
	const out = new Set<string>();
	for (const m of code.matchAll(/\b(?:class|struct)\s+(?:\w+_API\s+)?([A-Za-z_]\w*)/g)) out.add(m[1]);
	for (const m of code.matchAll(DEF_RE)) {
		const q = m[0].match(/\b([A-Za-z_]\w*)::([A-Za-z_]\w*)/);
		if (q) {
			out.add(q[1]); // the class being defined
			out.add(q[2]); // the method being defined
		}
	}
	return out;
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
function stripComments(src: string): string {
	return src.replace(/\/\*[\s\S]*?\*\//g, " ").replace(/\/\/[^\n]*/g, " ");
}

/** Comments AND string literals gone. Wrong for `#include "x.h"` — use stripComments there. */
function stripNonCode(src: string): string {
	return stripComments(src).replace(/"(?:[^"\\]|\\.)*"/g, '""');
}

/**
 * Engine API surface *used* by this code: methods invoked on an object or
 * through a scope qualifier, plus Unreal-conventioned type names.
 *
 * MEASURED: a naive "any identifier that appears in an engine header" rule
 * classifies `Configure` and `Move` as engine symbols. Requiring citations for
 * ordinary local names would make the gate intolerable, and an intolerable gate
 * gets disabled — which is how safety theatre happens.
 *
 * `::` is handled by first locating DEFINITIONS — `Ret AFoo::Configure(...) {` —
 * and excluding those exact spans. What remains (`Super::BeginPlay()`,
 * `UGameplayStatics::GetPlayerPawn()`) is a call, and calls need evidence.
 */
const DEF_RE = /\b[A-Za-z_]\w*::[A-Za-z_]\w*\s*\([^;{)]*\)\s*(?:const\s*)?(?:override\s*)?\{/g;
const SCOPE_CALL_RE = /\b([A-Za-z_]\w*)::([A-Za-z_]\w*)\s*\(/g;

/**
 * A used symbol has a DISPLAY name (what the code wrote) and a SEARCH TERM
 * (what to grep for). They differ for scope calls.
 *
 * The qualifier must be part of the identity. `void AFoo::BeginPlay() { Super::BeginPlay(); }`
 * both defines a method named BeginPlay and calls a foreign one spelled the same.
 * Keyed on the bare name, the definition exempts the call. Keyed on `Super::BeginPlay`,
 * it does not.
 */
interface Used {
	display: string; // "Super::BeginPlay" | "SetCapsuleSize" | "UCapsuleComponent"
	term: string; // "BeginPlay"         | "SetCapsuleSize" | "UCapsuleComponent"
	qualifier?: string; // "Super"
}

function apiSymbols(src: string): Map<string, Used> {
	const code = stripNonCode(src);
	const out = new Map<string, Used>();
	const put = (u: Used) => out.set(u.display, u);

	for (const m of code.matchAll(/(?:->|\.)\s*([A-Za-z_][A-Za-z0-9_]{2,})\s*\(/g)) put({ display: m[1], term: m[1] });
	for (const m of code.matchAll(/\b([UAFE][A-Z][A-Za-z0-9_]{2,})\b/g)) put({ display: m[1], term: m[1] });

	// Spans occupied by out-of-line definitions; a call cannot start inside one.
	const defSpans: [number, number][] = [];
	for (const m of code.matchAll(DEF_RE)) defSpans.push([m.index!, m.index! + m[0].length]);
	const insideDef = (i: number) => defSpans.some(([s, e]) => i >= s && i < e);

	for (const m of code.matchAll(SCOPE_CALL_RE)) {
		if (insideDef(m.index!)) continue; // `void AFoo::Configure(` — a definition, not a use
		put({ display: `${m[1]}::${m[2]}`, term: m[2], qualifier: m[1] });
	}
	return out;
}

/** API symbols present in `after` but not in `before`. */
function introduced(before: string, after: string): Used[] {
	const b = apiSymbols(before);
	return [...apiSymbols(after).values()].filter((u) => !b.has(u.display));
}

function isGuarded(p: string): boolean {
	const norm = path.resolve(p);
	const rel = path.relative(PROJECT_ROOT, norm);
	if (rel.startsWith("..")) return false;
	const guardedTree = GUARDED_PREFIXES.some((pre) => rel.startsWith(pre));
	const guardedFile = GUARDED_SUFFIXES.some((s) => norm.toLowerCase().endsWith(s));
	return guardedTree && guardedFile;
}

/** Raw ripgrep over the engine roots. Returns [] on no-match, throws on error. */
function engineGrep(pattern: string, maxHits: number): Citation[] {
	const stdout = (() => {
		try {
			return execFileSync(
				ripgrepPath()!,
				["--no-heading", "--line-number", "--color", "never", "--no-messages",
				 "-m", String(maxHits), "-g", "*.h", "-g", "*.cpp", pattern, ...ENGINE_ROOTS],
				{ encoding: "utf8", timeout: 60_000, stdio: ["ignore", "pipe", "ignore"] },
			);
		} catch (e: any) {
			if (e?.status === 1) return ""; // no match: a real answer
			throw e; // exit 2: the search did not run
		}
	})();

	const hits: Citation[] = [];
	for (const raw of stdout.split(/\r?\n/)) {
		const m = raw.match(/^(.*?):(\d+):(.*)$/);
		if (!m) continue;
		hits.push({ kind: "engine", locator: m[1], line: Number(m[2]), quote: m[3].trim(), at: new Date().toISOString() });
		if (hits.length >= maxHits) break;
	}
	return hits;
}

// ── the extension ───────────────────────────────────────────────────────────

export default function (pi: ExtensionAPI) {
	const ledger = loadLedger();

	/**
	 * A block that offers no way through is a hang, not a gate.
	 * Counts identical refusals so we can escalate instead of spinning forever.
	 */
	const strikes = new Map<string, number>();
	const MAX_STRIKES = 3;

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
					ripgrepPath()!,
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

	// ─── post-write: the preprocessor's verdict, not the agent's ─────────────
	//
	// Proof-of-use guarantees the agent READ the symbol. It cannot guarantee the
	// agent understood it. Measured live: the model read `SetCrouchedHalfHeight(40.0f)`
	// out of CharacterMovementComponent.cpp:751, took the 40.0f, ignored the method,
	// hand-resized the capsule instead, and wrote `#include "Bend.h"` for a header
	// that does not exist. Every citation verified. The file would not compile.
	//
	// Nothing that reads the diff catches that, because the diff looks reasonable.
	// So let an external, non-negotiable oracle speak: does the include resolve?
	// The header exists on disk or it does not. No judgment involved.

	const includeCache: Record<string, boolean> = {};

	/**
	 * Bytes on disk immediately before a guarded write, so a write that turns out
	 * not to compile can be undone. `null` means the file did not exist.
	 *
	 * Without this, `tool_result` only *reports* the bad file — it stays on disk.
	 * A gate that leaves the artifact it rejected is a smoke alarm, not a gate.
	 */
	const priorContent = new Map<string, string | null>();

	const resolveInclude = (inc: string): boolean => {
		if (inc in includeCache) return includeCache[inc];
		let ok = false;
		const projSrc = path.join(PROJECT_ROOT, "Source");
		const roots = [projSrc, ...ENGINE_ROOTS].filter((r) => fs.existsSync(r));
		for (const root of roots) {
			// Includes are written engine-relative ("Components/CapsuleComponent.h")
			// or bare ("Bend.h"). Match on the tail of the path.
			try {
				const out = execFileSync(
					ripgrepPath()!,
					["--files", "--no-messages", "-g", `**/${inc.replace(/\\/g, "/")}`, root],
					{ encoding: "utf8", timeout: 20_000, stdio: ["ignore", "pipe", "ignore"] },
				);
				if (out.trim()) { ok = true; break; }
			} catch (e: any) {
				if (e?.status !== 1) { ok = true; break; } // search broke: do not accuse
			}
		}
		includeCache[inc] = ok;
		return ok;
	};

	pi.on("tool_result", async (event) => {
		if (event.isError) return;
		if (event.toolName !== "write" && event.toolName !== "edit") return;
		const p = (event.input as { path?: string }).path;
		if (!p || !isGuarded(p) || !gateOperable() || !fs.existsSync(p)) return;

		const text = fs.readFileSync(p, "utf8");
		const missing: string[] = [];
		for (const m of stripComments(text).matchAll(/^\s*#\s*include\s*"([^"]+)"/gm)) {
			const inc = m[1];
			if (path.basename(inc).toLowerCase() === path.basename(p, path.extname(p)).toLowerCase() + ".h") {
				// A .cpp including its own not-yet-written header is a normal ordering.
				if (!fs.existsSync(path.join(path.dirname(p), path.basename(inc)))) missing.push(`${inc}  (its own header — write it)`);
				continue;
			}
			if (inc.endsWith(".generated.h")) continue; // emitted by UHT at build time
			if (!resolveInclude(inc)) missing.push(inc);
		}
		if (!missing.length) {
			priorContent.delete(path.resolve(p));
			return;
		}

		// Undo it. A rejected artifact does not get to stay on disk.
		const abs = path.resolve(p);
		const prior = priorContent.get(abs);
		let undo = "no prior state recorded; file left as written";
		if (prior === null) {
			fs.rmSync(abs, { force: true });
			undo = "the file has been DELETED (it did not exist before this write)";
		} else if (typeof prior === "string") {
			fs.writeFileSync(abs, prior, "utf8");
			undo = "the file has been REVERTED to its previous contents";
		}
		priorContent.delete(abs);

		const msg =
			`WRITE REJECTED — unresolvable includes in ${path.basename(p)}:\n` +
			missing.map((m) => `  #include "${m}"`).join("\n") +
			`\n\nThis is the preprocessor, not an opinion: ${undo}.\n` +
			`Create the header first, then write the source that includes it.`;
		if (!process.stdout.isTTY) console.error(`[proof-of-use] INCLUDE-FAIL ${p}: ${missing.join(", ")} — reverted`);
		return { isError: true, content: [{ type: "text" as const, text: msg }] };
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

		// Remember the bytes we may have to put back.
		const abs = path.resolve(input.path);
		priorContent.set(abs, fs.existsSync(abs) ? fs.readFileSync(abs, "utf8") : null);

		// FAIL CLOSED. If the verifier cannot verify, it does not consent.
		if (!gateOperable()) {
			const why = !haveRipgrep()
				? "ripgrep (rg) could not be found (checked PATH, ~/.amp/bin, VS Code, scoop, choco; set CHIMERA_RG to its path)"
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

		// What API symbols does this change INTRODUCE, and what does it define itself?
		let newIds: Used[];
		let afterText: string;
		if (event.toolName === "write") {
			const before = fs.existsSync(input.path) ? fs.readFileSync(input.path, "utf8") : "";
			afterText = input.content ?? "";
			newIds = introduced(before, afterText);
		} else {
			afterText = (input.edits ?? []).map((e) => e.newText).join("\n");
			const seen = new Map<string, Used>();
			for (const e of input.edits ?? []) for (const u of introduced(e.oldText, e.newText)) seen.set(u.display, u);
			newIds = [...seen.values()];
		}

		// Foreign = not ours. Everything foreign needs evidence — including symbols
		// that exist nowhere, which is how invented API calls get caught instead of
		// exempted. A qualified call is ours only if we own the QUALIFIER: we may
		// define `BeginPlay` and still be calling someone else's `Super::BeginPlay`.
		const local = locallyDefined(afterText);
		const ours = (u: Used) =>
			u.qualifier
				? local.has(u.qualifier) || isProjectSymbol(u.qualifier)
				: local.has(u.display) || isProjectSymbol(u.display);

		const needEvidence = newIds.filter((u) => !ours(u));
		flushSymCache();
		if (!needEvidence.length) return;

		const unproven = needEvidence.filter((u) => provenBy(u.term) === null);
		const proven = needEvidence.filter((u) => provenBy(u.term) !== null);

		if (!unproven.length) {
			ctx?.ui?.setStatus?.("proof-of-use", `✓ ${proven.length} foreign symbol(s) backed by citation`);
			return;
		}

		if (!ENFORCE) {
			ctx?.ui?.notify?.(`proof-of-use (advisory): ${unproven.length} unproven symbol(s)`, "warn");
			return;
		}

		// ── Refuse, but hand over the evidence ───────────────────────────────
		// The agent cannot comply with "go read the source" if refusing is all we
		// do; it will reissue the same write forever. So we perform the read now,
		// return the actual engine lines in the refusal, and record them. The
		// retry is then genuinely informed by retrieved text — which is the point.
		// Symbols with zero hits get no citation and stay blocked: they do not exist.
		const found: string[] = [];
		const absent: string[] = [];
		const evidence: string[] = [];

		for (const u of unproven) {
			let hits: Citation[];
			try {
				hits = engineGrep(`\\b${u.term}\\b`, 4);
			} catch {
				return {
					block: true,
					reason: `PROOF-OF-USE: the engine search failed while checking "${u.display}". ` +
						`The verifier is broken; it will not approve what it cannot check.`,
				};
			}
			if (!hits.length) {
				absent.push(u.display);
				continue;
			}
			found.push(u.display);
			for (const h of hits) record(h);
			evidence.push(
				`  ${u.display}\n` +
					hits.map((h) => `    ${path.relative(ENGINE_SOURCE, h.locator)}:${h.line}\n      ${h.quote.slice(0, 140)}`).join("\n"),
			);
		}
		flushSymCache();

		const key = `${path.resolve(input.path)}|${unproven.map((u) => u.display).sort().join(",")}`;
		const n = (strikes.get(key) ?? 0) + 1;
		strikes.set(key, n);

		if (n >= MAX_STRIKES) {
			return {
				block: true,
				reason:
					`PROOF-OF-USE: blocked ${n} times on the same symbols: ${unproven.map((u) => u.display).join(", ")}.\n` +
					(absent.length
						? `These do not exist in UE 5.8: ${absent.join(", ")}. No amount of retrying will create them.\n`
						: "") +
					`STOP retrying this write. Change the approach, or report that you are stuck and why.`,
			};
		}

		const reason =
			`PROOF-OF-USE: this ${event.toolName} introduces foreign API symbols you had not read.\n\n` +
			unproven.map((u) => `  UNPROVEN  ${u.display}`).join("\n") +
			(proven.length ? "\n" + proven.map((u) => `  proven    ${u.display}`).join("\n") : "") +
			(absent.length
				? `\n\nNOT FOUND IN UE 5.8 — these symbols do not exist. Do not write them:\n` +
					absent.map((s) => `  ${s}`).join("\n")
				: "") +
			(evidence.length
				? `\n\nI have now read the engine source for you. This is what it says:\n\n${evidence.join("\n\n")}\n\n` +
					`These are recorded as citations. Reissue the write ONLY if the code above supports it — ` +
					`if it contradicts what you were about to write, change the code, not the citation.`
				: "") +
			`\n\n(Comments do not count as use. A comment saying "verified" proves nothing.)` +
			`\n(Attempt ${n}/${MAX_STRIKES} on these symbols.)`;

		if (!process.stdout.isTTY) {
			console.error(
				`[proof-of-use] BLOCKED ${input.path}: unproven=${unproven.map((u) => u.display).join(",")} absent=${absent.join(",") || "-"}`,
			);
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

	// `--print` / RPC modes have no TUI. Every ui call is optional; a missing
	// notifier must never take the gate down with it.
	pi.on("session_start", async (_e, ctx) => {
		const mode = ENFORCE ? "ENFORCING" : "advisory (CHIMERA_PROOF_OF_USE=0)";
		const msg = !gateOperable()
			? `proof-of-use: CANNOT VERIFY (${!haveRipgrep() ? "ripgrep not found — set CHIMERA_RG" : `no engine roots under ${ENGINE_SOURCE}`}). Guarded writes will be BLOCKED.`
			: `proof-of-use: ${mode}; ${ledger.citations.length} citations; ${ENGINE_ROOTS.length} engine roots`;
		ctx?.ui?.notify?.(msg, gateOperable() ? "info" : "error");
		if (!process.stdout.isTTY) console.error(`[proof-of-use] ${msg}`);
	});

	pi.on("session_shutdown", async () => {
		flushSymCache();
		saveLedger(ledger);
	});
}
