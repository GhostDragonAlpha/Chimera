/**
 * Real Web Browsing Extension — uses Playwright for actual browser automation
 * Replaces pi-web-access (fake API search) with real Chromium browsing
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { chromium, type Browser, type Page } from "playwright";

let browser: Browser | null = null;
let page: Page | null = null;

export default function (pi: ExtensionAPI) {
	// ─── Playwright browser management ──────────────────────────────

	async function getBrowser() {
		if (!browser) {
			browser = await chromium.launch({ headless: true });
		}
		return browser;
	}

	async function getPage() {
		const b = await getBrowser();
		if (!page) {
			page = await b.newPage();
		}
		return page;
	}

	// ─── Core browsing tools ────────────────────────────────────────

	pi.registerTool({
		name: "web_browse",
		label: "Browse Web Page",
		description:
			"Open a URL in Chromium and extract readable content. Returns full text, links, and page structure.",
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
				await p.goto(params.url, {
					waitUntil: "domcontentloaded",
					timeout: 30000,
				});

				// Extract readable content
				const content = await p.evaluate(() => {
					const text = document.body?.innerText || "";
					return text.substring(0, params.maxChars);
				});

				// Extract links
				const links = await p.evaluate(() => {
					const anchors = Array.from(document.querySelectorAll("a[href]"));
					return anchors
						.map((a) => ({
							text: a.textContent?.trim(),
							href: a.getAttribute("href"),
						}))
						.filter((l) => l.text && l.href);
				});

				return {
					content: [
						{
							type: "text",
							text: `## Page Content\n${content}\n\n## Links (${links.length})\n${JSON.stringify(links.slice(0, 50), null, 2)}`,
						},
					],
					details: { status: "success" },
				};
			} catch (err: any) {
				return {
					content: [
						{
							type: "text",
							text: `Error browsing ${params.url}: ${err.message}`,
						},
					],
					details: { status: "error" },
					isError: true,
				};
			}
		},
	});

	pi.registerTool({
		name: "web_search_real",
		label: "Real Web Search",
		description:
			"Search the web using actual browser navigation to Google/Bing. Returns real results with full page content.",
		parameters: Type.Object({
			query: Type.String({ description: "Search query" }),
			maxResults: Type.Number({
				description: "Max results (default 5)",
				default: 5,
			}),
		}),
		async execute(_toolCallId, params) {
			try {
				const p = await getPage();

				// Search via Google
				await p.goto(
					`https://www.google.com/search?q=${encodeURIComponent(params.query)}&num=${params.maxResults}`,
					{
						waitUntil: "domcontentloaded",
						timeout: 30000,
					},
				);

				// Extract search results
				const results = await p.evaluate((maxRes) => {
					const resultElements = Array.from(document.querySelectorAll("div.g"));
					return resultElements.slice(0, maxRes).map((el) => ({
						title: el.querySelector("h3")?.textContent || "No title",
						url: el.querySelector("a")?.getAttribute("href"),
						snippet:
							el.querySelector('span[style*="height"]')?.textContent || "",
					}));
				}, params.maxResults);

				return {
					content: [
						{
							type: "text",
							text: `## Search Results for "${params.query}"\n\n${JSON.stringify(results, null, 2)}`,
						},
					],
					details: { status: "success" },
				};
			} catch (err: any) {
				return {
					content: [{ type: "text", text: `Search failed: ${err.message}` }],
					details: { status: "error" },
					isError: true,
				};
			}
		},
	});

	pi.registerTool({
		name: "web_extract",
		label: "Extract Page Data",
		description:
			"Extract specific data from a page using CSS selectors or XPath. Returns structured data.",
		parameters: Type.Object({
			url: Type.String({ description: "URL to extract from" }),
			selector: Type.String({
				description: "CSS selector (e.g., 'div.content', '.class', '#id')",
			}),
			field: Type.Optional(
				Type.String({
					description: "Field to extract: text, href, src, value",
				}),
			),
		}),
		async execute(_toolCallId, params) {
			try {
				const p = await getPage();
				await p.goto(params.url, {
					waitUntil: "domcontentloaded",
					timeout: 30000,
				});

				const data = await p.evaluate(
					(sel, field) => {
						const elements = Array.from(document.querySelectorAll(sel));
						return elements.map((el) => {
							if (field === "href") return el.getAttribute("href");
							if (field === "src") return el.getAttribute("src");
							if (field === "value") return el.value;
							return el.innerText || "";
						});
					},
					params.selector,
					params.field,
				);

				return {
					content: [
						{
							type: "text",
							text: `## Extracted Data\n${JSON.stringify(
								data.filter((d) => d),
								null,
								2,
							)}`,
						},
					],
					details: { status: "success" },
				};
			} catch (err: any) {
				return {
					content: [
						{ type: "text", text: `Extraction failed: ${err.message}` },
					],
					details: { status: "error" },
					isError: true,
				};
			}
		},
	});

	pi.registerTool({
		name: "web_screenshot",
		label: "Page Screenshot",
		description: "Take a screenshot of a webpage. Returns base64 image data.",
		parameters: Type.Object({
			url: Type.String({ description: "URL to screenshot" }),
			fullPage: Type.Boolean({
				description: "Capture full page (not just viewport)",
				default: false,
			}),
		}),
		async execute(_toolCallId, params) {
			try {
				const p = await getPage();
				await p.goto(params.url, { waitUntil: "networkidle", timeout: 30000 });

				const screenshot = await p.screenshot({ fullPage: params.fullPage });
				const base64 = screenshot.toString("base64");

				return {
					content: [{ type: "image", data: `data:image/png;base64,${base64}` }],
					details: { status: "success" },
				};
			} catch (err: any) {
				return {
					content: [
						{ type: "text", text: `Screenshot failed: ${err.message}` },
					],
					details: { status: "error" },
					isError: true,
				};
			}
		},
	});

	// ─── Cleanup on shutdown ────────────────────────────────────────

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
