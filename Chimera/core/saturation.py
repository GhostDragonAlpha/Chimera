"""saturation -- the completeness gate, built from the ACTUAL principle of measured saturation.

The operator's demand (2026-07-24): a completeness/DRY gate must NEVER be an assertion ("I asked
enough"). It must be the measured signature of a discovery curve going OVER THE HUMP and flattening
-- the point where you realize you've gotten it all -- and that saturation must be PROVEN every
time the gate runs, with the curve as the evidence. "You stopped" is not "you saturated."

THE SCIENCE (this is not a metaphor -- it is the standard instrument for "have I found them all?"):
Discovering the variables of X by asking questions is a SPECIES-ACCUMULATION problem. Each question
is a sample; each new variable is a new species. Two measured signals say "you've gotten it all",
and the gate requires BOTH:

  1. Chao2 completeness (Chao 1987, bias-corrected -- ecology's unseen-species estimator):
         S_est = S_obs + f1*(f1-1) / (2*(f2+1))      f1 = vars seen in exactly ONE question
                                                      f2 = vars seen in exactly TWO questions
     completeness = S_obs / S_est. Many one-off discoveries (large f1) => many still unseen =>
     NOT done. When new questions only re-surface known variables (f1 -> 0), S_est -> S_obs => done.

  2. A dry tail (loop-until-dry): the last K questions each added ZERO new variables. A single
     lucky gap is not saturation; a SUSTAINED flat tail is. This is the "over the hump": you kept
     asking and the world kept handing back only what you already had.

    completeness >= C_min  AND  dry_tail >= K   =>   SATURATED.

Otherwise: keep asking. The gate RENDERS the accumulation curve every time it runs, so DRY is a
witnessed measurement, never a claim. The provenance is enforced by the data model itself: a
variable can only enter the record because a question-round discovered it -- a hand-declared
variable with no round cannot even be in the curve (that is THE_FORMULA's S2a, for free).

The operator still calls the final ENOUGH -- but now ON the measured curve: you can only ratify
DRY when the measurement shows saturation, and you can always demand a higher bar. Physics measures
the approach to complete; the human calls complete.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

Rounds = Sequence[Iterable[str]]  # ordered; each round = the variables ONE question/probe discovered


@dataclass
class Saturation:
    """The measured saturation of a discovery process -- the receipt the gate produces every run."""
    questions: int              # rounds asked
    observed: int               # S_obs: distinct variables discovered
    accumulation: list          # cumulative distinct variables after each question (THE CURVE)
    marginal: list              # new distinct variables per question (the discovery rate)
    f1: int                     # singletons: variables found in exactly ONE question
    f2: int                     # doubletons: variables found in exactly TWO questions
    estimated_total: float      # Chao2 (bias-corrected): S_est
    unseen: float               # S_est - S_obs: estimated variables still undiscovered
    completeness: float         # S_obs / S_est, in [0, 1]
    dry_tail: int               # trailing questions that added ZERO new variables
    k_required: int
    c_required: float
    saturated: bool
    verdict: str

    def receipt(self) -> str:
        head = "SATURATED" if self.saturated else "NOT SATURATED"
        return (f"[{head}] {self.observed} variables over {self.questions} questions; "
                f"completeness {self.completeness:.2f} "
                f"(Chao2 est {self.estimated_total:.1f}, ~{self.unseen:.0f} unseen); "
                f"dry tail {self.dry_tail} {'>=' if self.dry_tail >= self.k_required else '<'} "
                f"{self.k_required}.\n           {self.verdict}")


def measure(rounds: Rounds, k: int = 3, c_min: float = 0.95) -> Saturation:
    """Measure the saturation of a question-by-question discovery process. Pure and deterministic."""
    rounds = [list(dict.fromkeys(r)) for r in rounds]   # de-dup within a question, keep order
    incidence: dict[str, int] = {}                      # how many questions each variable appeared in
    seen: set[str] = set()
    accumulation, marginal = [], []
    for r in rounds:
        new = 0
        for v in r:
            incidence[v] = incidence.get(v, 0) + 1
            if v not in seen:
                seen.add(v)
                new += 1
        marginal.append(new)
        accumulation.append(len(seen))

    S_obs = len(seen)
    f1 = sum(1 for c in incidence.values() if c == 1)
    f2 = sum(1 for c in incidence.values() if c == 2)
    # Chao2, bias-corrected form -- always computable (the +1 kills the div-by-zero at f2==0):
    S_est = S_obs + (f1 * (f1 - 1)) / (2 * (f2 + 1))
    completeness = (S_obs / S_est) if S_est > 0 else 0.0
    unseen = max(0.0, S_est - S_obs)

    dry_tail = 0                                         # trailing questions that discovered nothing new
    for m in reversed(marginal):
        if m == 0:
            dry_tail += 1
        else:
            break

    saturated = bool(S_obs > 0 and dry_tail >= k and completeness >= c_min)

    if saturated:
        verdict = (f"The curve went OVER THE HUMP: the last {dry_tail} questions each returned "
                   f"nothing new, and Chao2 estimates only ~{unseen:.0f} variables remain unseen. "
                   f"You've gotten it all.")
    elif dry_tail < k:
        verdict = (f"You STOPPED, you did not SATURATE: fewer than {k} questions in a row have "
                   f"returned nothing-new (dry tail {dry_tail}). Keep asking until the curve flattens.")
    else:
        verdict = (f"The tail is flat but Chao2 still estimates ~{unseen:.0f} unseen variables "
                   f"(completeness {completeness:.2f} < {c_min:.2f}): too many one-off discoveries. "
                   f"Not complete yet.")

    return Saturation(len(rounds), S_obs, accumulation, marginal, f1, f2, S_est, unseen,
                      completeness, dry_tail, k, c_min, saturated, verdict)


def _render(sat: Saturation, path: str, title: str) -> None:
    """Draw the accumulation curve with the Chao2 asymptote and the dry tail -- the visual witness."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = sat.questions
    xs = list(range(1, n + 1))
    color = "#2e7d32" if sat.saturated else "#b71c1c"
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(xs, sat.accumulation, "-o", color=color, lw=2, ms=5, label="variables discovered (cumulative)")
    ax.axhline(sat.estimated_total, ls="--", color="#555", lw=1.2,
               label=f"Chao2 estimate of ALL variables ({sat.estimated_total:.1f})")
    if sat.dry_tail > 0:                                 # shade the flat tail -- the "over the hump" region
        ax.axvspan(n - sat.dry_tail + 0.5, n + 0.5, color=color, alpha=0.12,
                   label=f"dry tail ({sat.dry_tail} questions, nothing new)")
    ax.set_xlabel("questions asked")
    ax.set_ylabel("distinct variables found")
    ax.set_title(f"{title}\n{('SATURATED' if sat.saturated else 'NOT SATURATED')} "
                 f"- completeness {sat.completeness:.2f}", color=color, fontsize=11)
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.25)
    ax.margins(x=0.02)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def prove(rounds: Rounds, k: int = 3, c_min: float = 0.95, png: str | None = None,
          title: str = "saturation") -> Saturation:
    """Measure AND (if png given) render. Always returns the measured evidence -- proven every time."""
    sat = measure(rounds, k, c_min)
    if png:
        _render(sat, png, title)
    return sat


class NotSaturated(Exception):
    """Raised by the gate when a variable set has not been PROVEN complete by saturation."""


def gate(rounds: Rounds, k: int = 3, c_min: float = 0.95, png: str | None = None) -> Saturation:
    """THE GATE (THE_FORMULA S2b / S7). Passes only on measured saturation; refuses a claim of DRY."""
    sat = prove(rounds, k, c_min, png=png)
    if not sat.saturated:
        raise NotSaturated(sat.verdict)
    return sat


# --- PROVE THE PRINCIPLE by discrimination: it must PASS the done and REFUSE the not-done ----------

def _main() -> int:
    import os
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # CASE A -- "Eden is lush", variables DISCOVERED by questioning, then AUDITED until dry.
    # Each list is one question's yield. Re-surfaced (already-known) variables carry the saturation
    # signal: near the end, questions from new angles return only things we already have.
    discovered = [
        ["canopy", "understory", "forest_floor"],                       # what makes it read green?
        ["soil_loam", "water_table", "mycorrhiza"],                     # what feeds the plants?
        ["streams", "rainfall", "humidity", "water_table"],            # where is the water?
        ["light_dapple", "growing_season", "canopy"],                  # what light reaches in?
        ["fauna_mammal", "fauna_bird", "insects", "pollinators"],      # what lives here?
        ["fruit", "flowers", "decomposers", "leaf_litter"],            # what is the cycle?
        # --- audit questions: asked from fresh angles, they return ONLY known variables ---
        ["canopy", "understory", "leaf_litter", "pollinators"],        # re-ask "green" -> nothing new
        ["streams", "humidity", "rainfall", "mycorrhiza", "fruit"],    # re-ask "water/cycle" -> nothing new
        ["fauna_bird", "insects", "flowers", "soil_loam", "decomposers"],  # re-ask "life" -> nothing new
        ["forest_floor", "growing_season", "light_dapple", "fauna_mammal"],  # re-ask "floor/light" -> nothing new
    ]

    # CASE B -- "Eden is lush", variables DECLARED (my failure): three climate knobs, then stop.
    declared = [
        ["land_fraction", "warmth", "wetness"],
    ]

    scratch = os.environ.get("CHIMERA_SCRATCH", ".")
    a = prove(discovered, png=os.path.join(scratch, "saturation_pass.png"), title="Eden lush -- DISCOVERED + audited")
    b = prove(declared,   png=os.path.join(scratch, "saturation_fail.png"), title="Eden lush -- DECLARED (3 knobs)")

    print("  === PROVE( the saturation-measurement principle ) -- it must DISCRIMINATE ===\n")
    print("  CASE A -- variables DISCOVERED by questioning, then audited until dry:")
    print("   ", a.receipt(), "\n")
    print("  CASE B -- variables DECLARED (the failure: 3 knobs, no probing tail):")
    print("   ", b.receipt(), "\n")

    ok = a.saturated and not b.saturated               # the gate is real only if it PASSES A and REFUSES B
    print(f"  === VERDICT: the principle {'DISCRIMINATES' if ok else 'FAILED'} "
          f"(passes the complete, refuses the incomplete) ===")
    if ok:
        print("    DRY is now a measured saturation -- proven every time, with the curve as the receipt.")
        print("    A hand-declared variable set cannot pass: it never asked the questions that prove it.")
    return 0 if ok else 1


def _staged_files() -> list[str]:
    import subprocess
    try:
        out = subprocess.run(["git", "diff", "--cached", "--name-only"],
                             capture_output=True, text=True, check=True).stdout
    except Exception:
        return []
    return [ln.strip().replace("\\", "/") for ln in out.splitlines() if ln.strip()]


def _lint(argv) -> int:
    """Pre-commit gate: when the completeness gate ITSELF is touched, re-prove it discriminates.

    Cheap otherwise (no-op). This is the guard that keeps the gate from silently rotting into a
    rubber stamp -- if an edit makes it stop refusing an incomplete set, the commit fails.
    """
    staged = _staged_files()
    touched = [f for f in staged if f.endswith("core/saturation.py")
               or f.endswith("tests/test_saturation.py")]
    if not touched:
        return 0
    complete = measure([["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i", "d"], ["j", "k", "a"],
                        ["l", "m", "n", "o"], ["p", "q", "r", "s"],
                        ["a", "b", "s", "q"], ["g", "h", "i", "f", "p"],
                        ["m", "n", "o", "d", "r"], ["c", "k", "l", "j"]])
    declared = measure([["land_fraction", "warmth", "wetness"]])
    if complete.saturated and not declared.saturated:
        print(f"[saturation] PASS: the completeness gate still discriminates "
              f"(complete {complete.completeness:.2f}/dry {complete.dry_tail}; "
              f"declared refused at {declared.completeness:.2f}/dry {declared.dry_tail}).")
        return 0
    print("[saturation] FAIL: the completeness gate no longer discriminates -- it would "
          "rubber-stamp an incomplete variable set. DRY must stay a measured saturation. "
          "Fix core/saturation.py.")
    return 1


if __name__ == "__main__":
    import sys
    if "--staged" in sys.argv:
        raise SystemExit(_lint(sys.argv))
    raise SystemExit(_main())
