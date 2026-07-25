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
    """Generate the APPEARANCE MESSENGER and MEASURE its convergence with the physics. The engine
    PROJECTS the term's physics into a light-view (appearance.py), then reads a feature back out of
    the pixels and checks it against what the physics law predicts (convergence.py) -- one membrane,
    two messengers. No hand-supplied picture, no aesthetic drift: the appearance must measurably
    CONVERGE (e.g. the star's glow color == blackbody(T)), or it DIVERGES and prove() refuses.
    Refused outright if the term has no projector yet (no light-view to agree with)."""
    return ENG.render(term)


@mcp.tool()
def prove(term: str) -> str:
    """The one door. Attempts to record `term` as PROVEN. Runs every gate -- S0 frame, provenance,
    measured saturation, classify, an appearance that CONVERGES with the physics, a legal terminal --
    and writes the codebook ONLY if all pass. Refuses otherwise, naming the blocking gate. This is
    the tool that forces the work."""
    return ENG.prove(term)


@mcp.tool()
def decide(term: str, ruling: str) -> str:
    """THE HUMAN terminal. Record the operator's ruling on a matter of taste/meaning. This is the
    one terminal an LLM can never stand in for -- reserved for the operator's judgement."""
    return ENG.decide(term, ruling)


if __name__ == "__main__":
    mcp.run()
