"""objective_matrix.py -- DO THE OBJECTIVE'S COMPONENTS FIGHT EACH OTHER?

RULE 0, stated before the run:

    STATEMENT   `stand_reward` MULTIPLIES height x support x joints. A product assumes the
                factors are independently achievable: if two of them are anti-correlated across
                reachable policies, no policy can score high on both, the product is capped by a
                tradeoff nobody wrote down, and the optimiser is being asked for something the
                body cannot do.

    PREDICTION  At least one pair of components is anti-correlated at Pearson r < -0.3, and the
                best-objective policy is NOT the best-survival policy.

    FALSIFIER   All pairs are non-negative and the best-objective policy IS the best-survival
                policy -- the proxy works and its components compose without conflict.

IT RE-USES `objective_survival.py`'s POPULATION AND RE-RUNS NOTHING. The same 200 policies, the
same objective numbers, the same held-out survivals -- because two measurements of the same
question on two different populations cannot be compared, and re-drawing would make the
component matrix and the correlation answer slightly different questions. Reading the JSON is
not a shortcut here; it is the control.

CORRECTION CARRIED FORWARD: the components are height, support, joints and EFFORT. There is no
roll term in the objective -- `kr * roll` is a policy channel, not a reward component.

    python tools/objective_matrix.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
SRC = LOGDIR / "objective_survival.json"
COMPONENTS = ("height", "support", "joints", "effort")


def _pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.std() < 1e-12 or y.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"no {SRC} -- run `python tools/objective_survival.py` first. Refusing "
                         f"to draw a second population and compare it to the first (rule 19).")
    D = json.loads(SRC.read_text(encoding="utf8"))
    rows = D["rows"]
    S = np.array([r["survival"] for r in rows])
    O = np.array([r["objective"] for r in rows])
    C = {c: np.array([r[c] for r in rows]) for c in COMPONENTS}
    scales = np.array([r["scale"] for r in rows])

    print(f"\nTHE OBJECTIVE'S COMPONENTS, AGAINST EACH OTHER -- {len(rows)} policies "
          f"(objective_survival.py's population, re-run of nothing)")
    print("=" * 100)
    print(f"  {'':<10}" + "".join(f"{c:>12}" for c in COMPONENTS) + f"{'survival':>12}")
    M = {}
    for a_ in COMPONENTS:
        line = f"  {a_:<10}"
        M[a_] = {}
        for b_ in COMPONENTS:
            r = 1.0 if a_ == b_ else _pearson(C[a_], C[b_])
            M[a_][b_] = r
            line += f"{r:>12.3f}"
        M[a_]["survival"] = _pearson(C[a_], S)
        line += f"{M[a_]['survival']:>12.3f}"
        print(line)
    print("-" * 100)

    # ── THE TRADEOFFS: pairs the product asks for together and the body delivers apart ──────
    anti = [(a_, b_, M[a_][b_]) for i, a_ in enumerate(COMPONENTS)
            for b_ in COMPONENTS[i + 1:] if np.isfinite(M[a_][b_]) and M[a_][b_] < -0.3]
    if anti:
        print(f"  ANTI-CORRELATED PAIRS (r < -0.3) -- the product asks for both and the body "
              f"trades one for the other:")
        for a_, b_, r in sorted(anti, key=lambda t: t[2]):
            mult = a_ in ("height", "support", "joints") and b_ in ("height", "support", "joints")
            print(f"    {a_:<10} vs {b_:<10} r = {r:+.3f}"
                  + ("   <- BOTH ARE MULTIPLIED FACTORS: the objective contains this "
                     "contradiction" if mult else "   (effort is subtracted, not multiplied)"))
    else:
        print(f"  NO ANTI-CORRELATED PAIR at r < -0.3 -- the components compose without "
              f"fighting each other.")

    # ── WITHIN-RUNG CONTROL, for the same reason the correlation needed one ─────────────────
    # A scale ladder makes every component fall together as the policy degrades, which can
    # manufacture POSITIVE correlations between them out of the sampling alone. Anti-correlation
    # cannot be manufactured that way -- it survives the confound by construction -- but the
    # positive entries above must be read with this line beside them.
    print("-" * 100)
    print(f"  WITHIN-RUNG (fixed scale, the confound held constant), median over rungs:")
    line = f"  {'':<10}" + "".join(f"{c:>12}" for c in COMPONENTS) + f"{'survival':>12}"
    print(line)
    Mw = {}
    for a_ in COMPONENTS:
        line = f"  {a_:<10}"
        Mw[a_] = {}
        for b_ in list(COMPONENTS) + ["survival"]:
            per = []
            for s in sorted(set(scales.tolist())):
                sel = scales == s
                if sel.sum() < 4:
                    continue
                y = S[sel] if b_ == "survival" else C[b_][sel]
                per.append(1.0 if a_ == b_ else _pearson(C[a_][sel], y))
            v = float(np.nanmedian(per)) if per else float("nan")
            Mw[a_][b_] = v
            line += f"{v:>12.3f}"
        print(line)

    # ── THE PARETO QUESTION: is the best objective the best survivor? ───────────────────────
    i_obj, i_surv = int(np.argmax(O)), int(np.argmax(S))
    print("=" * 100)
    print(f"  BEST OBJECTIVE  policy #{i_obj:<4} objective {O[i_obj]:+.4f}   survival "
          f"{S[i_obj]:.2f} s   (rung x{rows[i_obj]['scale']:g})")
    print(f"  BEST SURVIVAL   policy #{i_surv:<4} objective {O[i_surv]:+.4f}   survival "
          f"{S[i_surv]:.2f} s   (rung x{rows[i_surv]['scale']:g})")
    same = i_obj == i_surv
    print(f"  the best-objective policy survives {S[i_obj]:.2f} s; the best survivor lasts "
          f"{S[i_surv]:.2f} s "
          f"-> the objective leaves {S[i_surv] - S[i_obj]:+.2f} s on the table")
    # how far down the objective ranking is the best survivor?
    rank_of_best_surv = int((O > O[i_surv]).sum()) + 1
    print(f"  the best SURVIVOR ranks #{rank_of_best_surv} of {len(rows)} by objective "
          f"({100.0*rank_of_best_surv/len(rows):.0f}th percentile)")
    fires = (not anti) and same
    print(f"  FALSIFIER (no anti-correlated pair AND best-objective == best-survival): "
          + ("FIRES -- the proxy works and its components compose without conflict."
             if fires else
             f"does not fire -- {len(anti)} anti-correlated pair(s)"
             f"{'' if same else ', and the best-objective policy is not the best survivor'}."))

    out = LOGDIR / "objective_matrix.json"
    out.write_text(json.dumps(dict(
        source=str(SRC.name), n=len(rows), matrix=M, matrix_within_rung=Mw,
        anti_pairs=[dict(a=a_, b=b_, r=r) for a_, b_, r in anti],
        best_objective_idx=i_obj, best_survival_idx=i_surv,
        best_objective=dict(objective=float(O[i_obj]), survival=float(S[i_obj])),
        best_survival=dict(objective=float(O[i_surv]), survival=float(S[i_surv])),
        best_survivor_objective_rank=rank_of_best_surv,
        falsifier_fires=bool(fires)), indent=1), encoding="utf8")
    print(f"  JSON: {out}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.6))
    Marr = np.array([[M[a_][b_] for b_ in COMPONENTS] for a_ in COMPONENTS])
    im = ax[0].imshow(Marr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax[0].set_xticks(range(len(COMPONENTS))); ax[0].set_xticklabels(COMPONENTS, fontsize=8)
    ax[0].set_yticks(range(len(COMPONENTS))); ax[0].set_yticklabels(COMPONENTS, fontsize=8)
    for i in range(len(COMPONENTS)):
        for j in range(len(COMPONENTS)):
            ax[0].text(j, i, f"{Marr[i, j]:.2f}", ha="center", va="center", fontsize=8)
    plt.colorbar(im, ax=ax[0])
    ax[0].set_title("component x component (pooled)", fontsize=9)
    ax[1].scatter(C["support"], C["joints"], c=np.log10(scales), cmap="viridis", s=18, alpha=0.8)
    ax[1].set_xlabel("support"); ax[1].set_ylabel("joints")
    ax[1].set_title(f"the multiplied pair: r = {M['support']['joints']:+.2f}", fontsize=9)
    ax[2].scatter(O, S, s=16, alpha=0.6, color="#7f8c8d")
    ax[2].scatter([O[i_obj]], [S[i_obj]], s=120, marker="X", color="#e67e22",
                  label=f"best objective ({S[i_obj]:.1f} s)")
    ax[2].scatter([O[i_surv]], [S[i_surv]], s=120, marker="*", color="#1a7f37",
                  label=f"best survival ({S[i_surv]:.1f} s)")
    ax[2].set_xlabel("objective"); ax[2].set_ylabel("held-out survival s"); ax[2].legend(fontsize=7)
    ax[2].set_title("does maximising the proxy find the survivor?", fontsize=9)
    fig.suptitle(f"OBJECTIVE COMPONENT MATRIX -- {len(anti)} anti-correlated pair(s); "
                 f"best objective survives {S[i_obj]:.1f} s vs best {S[i_surv]:.1f} s",
                 fontsize=11.5)
    png = OUTDIR / "objective_matrix.png"
    fig.savefig(png, dpi=104, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
