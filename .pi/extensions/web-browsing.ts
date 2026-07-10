/**
 * Real Web Browsing Extension — Playwright + local Chromium.
 *
 * 2026-07-10 repair. Three defects were found by probe, not by reading:
 *
 *   1. `page.evaluate(() => ... params.maxChars ...)` — the callback is
 *      serialized into the browser, where `params` does not exist. Every
 *      web_browse call threw `ReferenceError: params is not defined` and the
 *      catch turned it into a polite string. The tool had never worked.
 *      Fixed: arguments are passed as the second argument to evaluate().
 *
 *   2. web_search_real scraped Google `div.g`. Measured headless: HTTP 200,
 *      zero matches, page title is the raw URL — a bot wall. It returned an
 *      empty array with status "success".
 *      Fixed: Startpage primary (10/10 results, direct hrefs), Bing fallback
 *      (works with waitUntil:"networkidle"; hrefs are ck/a redirects whose
 *      real target is base64url in the `u` param, minus a leading "a1").
 *
 *   3. Both failure modes were SILENT. An agent could not distinguish
 *      "searched, found nothing" from "the tool is dead."
 *      Fixed: zero results is `isError: true`, always.
 *
 * Measured 2026-07-10 (headless chromium, realistic UA):
 *   startpage 200 / a.result-link=10    ddg-lite 403    ddg-html 403
 *   bing 200 / li.b_algo=10 (networkidle)    mojeek captcha    marginalia 502
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { chromium, type Browser, type Page } from "playwright";

const UA =
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
	"(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36";

let browser: Browser | null = null;
let page: Page | null = null;

interface SearchHit {
	title: string;
	url: string;
}

/** Bing wraps results in /ck/a?...&u=a1<base64url>&... — recover the target. */
function unwrapBing(href: string): string {
	try {
		const u = new URL(href).searchParams.get("u");
		if (!u || !u.startsWith("a1")) return href;
		const b64 = u.slice(2).replace(/-/g, "+").replace(/_/g, "/");
		const decoded = Buffer.from(b64, "base64").toString("utf8");
		return decoded.startsWith("http") ? decoded : href;
	} catch {
		return href;
	}
}

export default function (pi: ExtensionAPI) {
	async function getBrowser() {
		if (!browser) browser = await chromium.launch({ headless: true });
		return browser;
	}

	async function getPage() {
		const b = await getBrowser();
		if (!page) {
			const ctx = await b.newContext({ userAgent: UA, locale: "en-US" });
			page = await ctx.newPage();
		}
		return page;
	}

	const fail = (text: string) => ({
		content: [{ type: "text" as const, text }],
		details: { status: "error" },
		isError: true,
	});

	// ─── web_browse ─────────────────────────────────────────────────

	pi.registerTool({
		name: "web_browse",
		label: "Browse Web Page",
		description:
			"Open a URL in Chromium and extract readable content. Returns full text and links. " +
			"Errors loudly if the page yields no text — an empty page is never reported as success.",
		parameters: Type.Object({
			url: Type.String({ description: "URL to browse" }),
			maxChars: Type.Number({
				description: "Max characters to return (default 10000)",
				default: 10000,
			}),
		}),
		async execute(_toolCallId, params) {
			try {
				const p = await getPage();
				await p.goto(params.url, { waitUntil: "domcontentloaded", timeout: 30000 });
				await p.waitForTimeout(400);

				// `maxChars` must be PASSED IN. A closure would not survive the
				// jump into the page context. This was defect #1.
				const content = await p.evaluate((maxChars: number) => {
					for (const s of document.querySelectorAll("script,style,nav,footer,header")) {
						s.remove();
					}
					const text = document.body?.innerText || "";
					return text.substring(0, maxChars);
				}, params.maxChars);

				const links = await p.evaluate(() =>
					Array.from(document.querySelectorAll("a[href]"))
						.map((a) => ({
							text: a.textContent?.trim() ?? "",
							href: a.getAttribute("href") ?? "",
						}))
						.filter((l) => l.text && l.href.startsWith("http")),
				);

				if (!content.trim()) {
					return fail(
						`web_browse: ${params.url} returned 0 characters of text. ` +
							`The page is empty, JS-gated, or blocking the browser. This is NOT a successful research step.`,
					);
				}

				return {
					content: [
						{
							type: "text" as const,
							text:
								`## ${params.url}\n## ${content.length} chars extracted\n\n${content}\n\n` +
								`## Links (${links.length})\n${JSON.stringify(links.slice(0, 50), null, 2)}`,
						},
					],
					details: { status: "success", chars: content.length, links: links.length },
				};
			} catch (err: any) {
				return fail(`web_browse FAILED on ${params.url}: ${err.message?.split("\n")[0]}`);
			}
		},
	});

	// ─── web_search_real ────────────────────────────────────────────

	pi.registerTool({
		name: "web_search_real",
		label: "Real Web Search",
		description:
			"Search the web with a real browser (Startpage, falling back to Bing). " +
			"Returns titles and direct URLs. Zero results is reported as an ERROR, never as success.",
		parameters: Type.Object({
			query: Type.String({ description: "Search query" }),
			maxResults: Type.Number({ description: "Max results (default 5)", default: 5 }),
		}),
		async execute(_toolCallId, params) {
			const p = await getPage();
			const tried: string[] = [];

			// -- primary: Startpage. Direct hrefs, no redirect wrapper.
			try {
				await p.goto(
					`https://www.startpage.com/sp/search?query=${encodeURIComponent(params.query)}`,
					{ waitUntil: "domcontentloaded", timeout: 25000 },
				);
				await p.waitForTimeout(700);
				const hits: SearchHit[] = await p.evaluate((max: number) =>
					Array.from(document.querySelectorAll("a.result-link"))
						.slice(0, max)
						.map((a) => ({
							title: ((a as HTMLElement).innerText || "").trim().split("\n")[0],
							url: a.getAttribute("href") || "",
						}))
						.filter((h) => h.url.startsWith("http")),
					params.maxResults,
				);
				if (hits.length) {
					return {
						content: [
							{
								type: "text" as const,
								text: `## ${hits.length} results (startpage) for "${params.query}"\n\n${JSON.stringify(hits, null, 2)}`,
							},
						],
						details: { status: "success", engine: "startpage", count: hits.length },
					};
				}
				tried.push("startpage: 0 results");
			} catch (err: any) {
				tried.push(`startpage: ${err.message?.split("\n")[0]}`);
			}

			// -- fallback: Bing. Needs networkidle; hrefs are ck/a redirects.
			try {
				await p.goto(`https://www.bing.com/search?q=${encodeURIComponent(params.query)}`, {
					waitUntil: "networkidle",
					timeout: 25000,
				});
				const raw: SearchHit[] = await p.evaluate((max: number) =>
					Array.from(document.querySelectorAll("li.b_algo"))
						.slice(0, max)
						.map((li) => ({
							title: (li.querySelector("h2") as HTMLElement | null)?.innerText?.trim() ?? "",
							url: li.querySelector("h2 a")?.getAttribute("href") ?? "",
						}))
						.filter((h) => h.url),
					params.maxResults,
				);
				const hits = raw.map((h) => ({ ...h, url: unwrapBing(h.url) }));
				if (hits.length) {
					return {
						content: [
							{
								type: "text" as const,
								text: `## ${hits.length} results (bing fallback) for "${params.query}"\n\n${JSON.stringify(hits, null, 2)}`,
							},
						],
						details: { status: "success", engine: "bing", count: hits.length },
					};
				}
				tried.push("bing: 0 results");
			} catch (err: any) {
				tried.push(`bing: ${err.message?.split("\n")[0]}`);
			}

			return fail(
				`web_search_real: NO RESULTS for "${params.query}". Every backend failed:\n` +
					tried.map((t) => `  - ${t}`).join("\n") +
					`\nDo not proceed as though research was performed. The search did not happen.`,
			);
		},
	});

	// ─── web_extract ────────────────────────────────────────────────

	pi.registerTool({
		name: "web_extract",
		label: "Extract Page Data",
		description: "Extract data from a page by CSS selector. Empty result set is an error.",
		parameters: Type.Object({
			url: Type.String({ description: "URL to extract from" }),
			selector: Type.String({ description: "CSS selector (e.g. 'div.content', '#id')" }),
			field: Type.Optional(
				Type.String({ description: "Field to extract: text | href | src | value" }),
			),
		}),
		async execute(_toolCallId, params) {
			try {
				const p = await getPage();
				await p.goto(params.url, { waitUntil: "domcontentloaded", timeout: 30000 });

				const data: string[] = await p.evaluate(
					({ sel, field }: { sel: string; field?: string }) =>
						Array.from(document.querySelectorAll(sel))
							.map((el) => {
								if (field === "href") return el.getAttribute("href") ?? "";
								if (field === "src") return el.getAttribute("src") ?? "";
								if (field === "value") return (el as HTMLInputElement).value ?? "";
								return (el as HTMLElement).innerText ?? "";
							})
							.filter(Boolean),
					{ sel: params.selector, field: params.field },
				);

				if (!data.length) {
					return fail(
						`web_extract: selector ${JSON.stringify(params.selector)} matched 0 elements on ${params.url}. ` +
							`The selector is stale or the page is JS-gated.`,
					);
				}

				return {
					content: [
						{ type: "text" as const, text: `## ${data.length} matches\n${JSON.stringify(data, null, 2)}` },
					],
					details: { status: "success", count: data.length },
				};
			} catch (err: any) {
				return fail(`web_extract FAILED: ${err.message?.split("\n")[0]}`);
			}
		},
	});

	// ─── web_screenshot ─────────────────────────────────────────────

	pi.registerTool({
		name: "web_screenshot",
		label: "Page Screenshot",
		description: "Screenshot a webpage. Returns base64 PNG.",
		parameters: Type.Object({
			url: Type.String({ description: "URL to screenshot" }),
			fullPage: Type.Boolean({ description: "Capture full page", default: false }),
		}),
		async execute(_toolCallId, params) {
			try {
				const p = await getPage();
				await p.goto(params.url, { waitUntil: "networkidle", timeout: 30000 });
				const shot = await p.screenshot({ fullPage: params.fullPage });
				return {
					content: [{ type: "image" as const, data: `data:image/png;base64,${shot.toString("base64")}` }],
					details: { status: "success" },
				};
			} catch (err: any) {
				return fail(`web_screenshot FAILED on ${params.url}: ${err.message?.split("\n")[0]}`);
			}
		},
	});

	pi.on("session_shutdown", async () => {
		if (page) {
			await page.close();
			page = null;
		}
		if (browser) {
			await browser.close();
			browser = null;
		}
	});
}
