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
    """S3. Send each discovered variable to its terminal: 'PHYSICS' (measurable fact) or
    'THE HUMAN' (taste/meaning). No other terminal is legal."""
    return ENG.classify(term, assignments)


@mcp.tool()
def render(term: str) -> str:
    """Render the term's appearance and let the HUMAN DYAD judge it. The engine renders a Gaussian-
    splat MOVIE (beginning->end; splat_appearance.py, with matplotlib as a placeholder fallback), then
    the HUMAN side -- a SEPARATE vision LLM + the operator -- reads it BLIND and cross-references to the
    physics (human_messenger.py) -> an alignment 0-1. Physics is a NUMBER, the human is a TERM: two
    different systems, never a monad. No vision model = FAIL and the operator is SUMMONED via CAPCOM;
    the human disagreeing means the render is wrong -- start over. Only the operator's own reading overrides."""
    return ENG.render(term)


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


if __name__ == "__main__":
    mcp.run()
