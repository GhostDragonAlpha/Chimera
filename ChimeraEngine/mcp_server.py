"""ChimeraEngine -- the workflow as an MCP server. The AI's Unreal.

A bounded, typed tool surface over the engine's OWNED state. These tools are the only sanctioned
way to move a term toward "proven"; `prove` is the one door, and it refuses until every gate
passes. Registered in `.mcp.json`, these appear as first-class tools -- the workflow becomes the
interface, not a document to remember.

Run:  python ChimeraEngine/mcp_server.py    (stdio; Claude Code launches it from .mcp.json)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # import engine_state without the pkg __init__
import engine_state
from mcp.server.fastmcp import FastMCP

ENG = engine_state.Engine()
mcp = FastMCP("chimera-engine")


@mcp.tool()
def orient() -> str:
    """The viewport. Shows the current term and its gate progress, the whole hierarchy
    (setting-first from the seed), the codebook of proven terms, and the ONE next move.
    Call this first, every time -- it is how you know where you are and what is legal next."""
    return ENG.orient()


@mcp.tool()
def next() -> str:
    """Advance to the next term to prove -- the shallowest open node whose parent is already
    proven, i.e. setting-first descent from the seed. You do not pick the term; the hierarchy does."""
    n = ENG.next_term()
    if not n:
        return "The hierarchy is complete at this resolution. Nothing open to prove."
    ENG.state["current"] = n
    ENG._save()
    return (f"NEXT TERM: `{n}`\ncontext (the story you carry here): {' > '.join(ENG.context(n))}\n"
            f"next action: {ENG.next_action(n)}")


@mcp.tool()
def frame(term: str, claim: str) -> str:
    """S0. State the term as exactly ONE atomic claim. Compound claims are refused -- split them."""
    return ENG.frame(term, claim)


@mcp.tool()
def question(term: str, question: str, variables: list[str]) -> str:
    """S1. Submit one question and the variables it DISCOVERED (never declared). The engine
    accumulates rounds and MEASURES the discovery curve. Keep calling until it reports saturated:
    the curve must go over the hump (a dry tail + Chao2 completeness), not stop when you feel done."""
    return json.dumps(ENG.question(term, question, variables), indent=2)


@mcp.tool()
def classify(term: str, assignments: dict[str, str]) -> str:
    """S3. Send each discovered variable to its terminal: 'PHYSICS#path/to/numbers.json#key'
    (measurable fact with measurement pointer) or 'THE HUMAN' (taste/meaning). No other terminal
    is legal."""
    return ENG.classify(term, assignments)


@mcp.tool()
def render(term: str, reading: str = "", aligns: str = "") -> str:
    """Render the term's appearance and let the HUMAN DYAD judge it. The engine renders a Gaussian-
    splat MOVIE (beginning->end; splat_appearance.py, with matplotlib as a placeholder fallback), then
    the HUMAN side -- a SEPARATE vision LLM + the operator -- reads it BLIND and cross-references to the
    physics (human_messenger.py) -> an alignment 0-1. Physics is a NUMBER, the human is a TERM: two
    different systems, never a monad. No vision model = FAIL and the operator is SUMMONED via CAPCOM;
    the human disagreeing means the render is wrong -- start over. Only the operator's own reading
    overrides: pass YOUR reading + aligns ('yes'/'no' or 0-1) and it is authoritative -- the
    operator is the human terminal; the proxy is their proxy, not their superior."""
    return ENG.render(term, reading=reading, aligns=aligns)


@mcp.tool()
def prove(term: str) -> str:
    """The one door, AND the boundary crossing. Attempts to record `term` as PROVEN. Runs every gate
    -- S0 frame, provenance, measured saturation, classify, an appearance that CONVERGES with the
    physics, a legal terminal -- and writes the codebook ONLY if all pass. Because this call arrives
    through the MCP tool surface, it proves in the ENGINE SYSTEM (via='mcp'): the term CROSSES THE
    BOUNDARY and counts as proven in both systems. A driver holding the Engine directly cannot cross
    it -- that is proving with your own system alone. Refuses otherwise, naming the blocking gate."""
    return ENG.prove(term, via="mcp")


@mcp.tool()
def decide(term: str, ruling: str) -> str:
    """THE HUMAN terminal. Record the operator's ruling on a matter of taste/meaning. This is the
    one terminal an LLM can never stand in for -- reserved for the operator's judgement."""
    return ENG.decide(term, ruling)


@mcp.tool()
def hear(term: str, reading: str = "", aligns: str = "") -> str:
    """THE SOUND DYAD -- judge a term by EAR (its matter as PRESSURE: sonify.py -> a WAV). The render's twin.
    The OPERATOR is the primary, authoritative ear; the Omni AI ear is a logged, MEASURED-UNRELIABLE second
    opinion and can NEVER gate a proof alone. To rule authoritatively, pass your own `reading` (what YOU
    hear) + `aligns` ('yes'/'no' or 0-1). With no reading it runs the advisory AI ear and records it (not a
    proof). Sound is ADDITIVE -- it deepens a term, it does not block `prove`. The WAV path is returned to play."""
    return ENG.hear(term, reading=reading, aligns=aligns)


@mcp.tool()
def reload() -> str:
    """OPEN THE LEVEL. Hot-reload the world into the running engine instead of restarting the session:
    re-read the story (new terms from THE_STORY.md via gen_decl.py -> terms_data.py), rebuild the
    hierarchy, reconcile the ledger (every proof kept), and reload the scene renderer. Call this after
    changing the story or a scene. (Changes to the engine's OWN logic -- engine_state.py, this file --
    still need a one-time session restart; you cannot hot-swap the running class, only its world.)"""
    return ENG.reload_world()


# ---------------------------------------------------------------------------
# THE PARTS PIPELINE -- the CAD-body + trained-material workflow as tools.
# These wrap tools/*.py (which run under .venv-gs) so the manual method is
# callable through the server: fit the inner-membrane primitives, train
# material concepts into the library, cut the corpus, spray one part at a
# time. The dyad still judges the renders; these just move the machinery.
# ---------------------------------------------------------------------------
import subprocess

REPO = Path(__file__).resolve().parent.parent
GS_PY = REPO / ".venv-gs" / "Scripts" / "python.exe"
DONOR = {  # the approved donor (CO3D bear 34) and its derived artifacts
    "splat": "models/co3d/co3d_34.splat",
    "labels": "models/co3d/bear34_labels.json",
    "skel": "models/co3d/bear34_skeleton_solved.json",
    "shells": "models/co3d/bear34_shells.npz",
    "parts_json": "models/co3d/bear34_parts.json",
    "genomes": "models/co3d/genomes",
    "materials": "models/co3d/materials",
    "parts_out": "models/co3d/parts",
}


def _run_tool(script: str, *args: str, timeout: int = 900) -> str:
    try:
        r = subprocess.run([str(GS_PY), str(REPO / "tools" / script), *args],
                           capture_output=True, text=True, timeout=timeout,
                           cwd=str(REPO))
        out = (r.stdout + r.stderr).strip()
        return out[-4000:] if out else f"(exit {r.returncode}, no output)"
    except subprocess.TimeoutExpired:
        return f"FAILED: {script} timed out after {timeout}s"


@mcp.tool()
def parts_fit() -> str:
    """Fit the analytic CAD primitives to the donor's INNER MEMBRANE (zero of
    application = zero of extraction). Skeleton-anchored capsules for limbs,
    ellipsoids for body parts. Rewrites bear34_parts.json + the colored viz."""
    return _run_tool("fit_parts.py", "--splat", DONOR["splat"], "--labels", DONOR["labels"],
                     "--skel", DONOR["skel"], "--shells", DONOR["shells"],
                     "--out", DONOR["parts_json"], "--viz", "models/co3d/bear34_parts.splat")


@mcp.tool()
def part_spray(part: str, material: str = "", lumband: str = "") -> str:
    """Spray ONE part from the plan (tools/specs/bear34_parts_plan.json). With
    `material` (a trained library name) the coat is SYNTHESIZED from the
    concept -- likelihood floor + color box + tip-line clamp. Else genome tiles."""
    args = ["--part", part, "--shells", DONOR["shells"], "--outdir", DONOR["parts_out"]]
    if material:
        args += ["--material", material, "--materialdir", DONOR["materials"]]
    if lumband:
        lo, hi = lumband.split()
        args += ["--lumband", lo, hi]
    return _run_tool("spray_parts.py", *args)


@mcp.tool()
def material_clusters(genome: str, clusters: int = 8) -> str:
    """List the material clusters a genome contains (chromaticity + log intensity,
    never raw RGB). genome = region name under the donor's genomes dir, or path."""
    g = genome if genome.endswith(".npz") else f"{DONOR['genomes']}/{genome}.npz"
    return _run_tool("train_material.py", "--genome", g, "--clusters", str(clusters),
                     "--outdir", DONOR["materials"])


@mcp.tool()
def material_train(genome: str, pick: int, name: str, clusters: int = 8) -> str:
    """Train a named MATERIAL CONCEPT from one cluster of a genome: GMM over
    [rgb, log scale, h, alpha] + likelihood floor + color box + tip line +
    real fiber tilts. Registered in the library with provenance."""
    g = genome if genome.endswith(".npz") else f"{DONOR['genomes']}/{genome}.npz"
    return _run_tool("train_material.py", "--genome", g, "--clusters", str(clusters),
                     "--pick", str(pick), "--name", name, "--outdir", DONOR["materials"])


@mcp.tool()
def corpus_cut(regions: str, out: str = "models/co3d/corpus/fur.npz") -> str:
    """Cut flat reference-plane training patches (membrane-plane zero, tip-line
    filtered, full 14-var record per splat). regions = space-separated genome names."""
    return _run_tool("cut_patches.py", "--shells", DONOR["shells"], "--genomes",
                     DONOR["genomes"], "--regions", *regions.split(), "--out", out)


@mcp.tool()
def parts_status() -> str:
    """The parts pipeline at a glance: library materials, built parts, corpus files."""
    lines = []
    lib = REPO / DONOR["materials"] / "library.json"
    if lib.exists():
        mats = json.loads(lib.read_text())["materials"]
        lines.append(f"materials ({len(mats)}):")
        for m in mats:
            lines.append(f"  {m['name']}: cluster {m['cluster']} of "
                         f"{Path(m['source_genome']).stem}, n_train={m['n_train']}")
    else:
        lines.append("materials: none trained yet")
    pdir = REPO / DONOR["parts_out"]
    built = sorted(p.stem for p in pdir.glob("*.splat")) if pdir.exists() else []
    lines.append(f"parts built: {', '.join(built) if built else 'none'}")
    cdir = REPO / "models/co3d/corpus"
    corp = sorted(f"{p.name} ({p.stat().st_size//1024}KB)" for p in cdir.glob("*.npz")) if cdir.exists() else []
    lines.append(f"corpus: {', '.join(corp) if corp else 'none'}")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()