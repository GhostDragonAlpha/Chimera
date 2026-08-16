"""score_saturation.py — the quality-band instrument (operator directive 2026-08-16).

The P/V band is set by SATURATION, driven by taste (operator directive
2026-08-16): a taste judgment — the human's or an LLM's, EQUALLY valuable,
no hierarchy — is the discovery instrument. Each critique round names what
offends; each offense is a deficiency class. When the discovery curve
saturates (Chao2 completeness + dry tail), the scores at that point ARE the
band floor. Same mathematics as the engine's S1 question saturation:
species accumulation with a Chao2 estimate of the unseen.

Rule 0 (stated before use): a deliverable's deficiency space is finite and
discoverable by repeated skeptical critique. Prediction: rounds produce a
rising-then-dry discovery curve. Falsifier: rounds keep discovering NEW
deficiency classes at a flat rate — the curve never humps — meaning the
rubric's categories are wrong, not incomplete; re-frame (rule 8), don't keep
scoring.

Ledger: score_ledger.json (tracked — it IS the band's evidence).
Each entry: {task, P, V, p_breakdown, v_breakdown, deficiencies: [ids...]}.
A deficiency id is stable text (e.g. "v:subject<15%-of-frame") so repeat
sightings are the SAME species, not new ones.

Saturation rule (standard species-accumulation stopping rule, the same one
the engine's S1 uses):
  completeness = S_obs / S_chao2,  S_chao2 = S_obs + f1^2 / (2*f2)
  (f1 = deficiency classes seen in exactly ONE round, f2 = in exactly TWO)
  SATURATED when completeness >= 0.9 AND the last 3 rounds discovered 0 new
  classes (dry tail). Both thresholds are the conventional stopping rule;
  the operator can raise them, never lower them, per scoreband.

Usage:
  python score_saturation.py add <task> <P> <V> <def-id> [def-id...]
  python score_saturation.py status
  python score_saturation.py render        # rewrite scoreboard.html

scoreboard.html is regenerated on every `add` — it is never stale. Open it
in any browser; no server. The latest proof strips are inlined from
scratch/ when present (missing images hide themselves).
"""
import html
import json
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parent / "score_ledger.json"
BOARD = Path(__file__).resolve().parent / "scoreboard.html"
DRY_TAIL = 3
COMPLETENESS_MIN = 0.9


def load():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"rounds": []}


def stats(rounds):
    seen = {}
    order = []
    per_round_new = []
    for r in rounds:
        new = 0
        for d in r["deficiencies"]:
            if d not in seen:
                seen[d] = 0
                order.append(d)
                new += 1
            seen[d] += 1
        per_round_new.append(new)
    s_obs = len(seen)
    f1 = sum(1 for v in seen.values() if v == 1)
    f2 = sum(1 for v in seen.values() if v == 2)
    s_chao2 = s_obs + (f1 * f1 / (2 * f2) if f2 else (f1 * (f1 - 1) / 2 if f1 > 1 else 0))
    completeness = s_obs / s_chao2 if s_chao2 else 1.0
    tail = 0
    for n in reversed(per_round_new):
        if n == 0:
            tail += 1
        else:
            break
    saturated = completeness >= COMPLETENESS_MIN and tail >= DRY_TAIL and len(rounds) > DRY_TAIL
    return {
        "rounds": len(rounds), "S_obs": s_obs, "f1": f1, "f2": f2,
        "S_chao2": round(s_chao2, 2), "completeness": round(completeness, 3),
        "per_round_new": per_round_new, "dry_tail": tail,
        "saturated": saturated,
    }


def render(led):
    """Write scoreboard.html — the human-facing P/V page (operator directive
    2026-08-16: the human needs easy access to the two numbers, every round).
    Self-contained, no JS deps, no server. Latest proof strips inline."""
    rounds = led["rounds"]
    s = stats(rounds)
    last = rounds[-1] if rounds else {"task": "—", "P": 0, "V": 0,
                                      "deficiencies": []}
    # per-species sighting table, first/last round
    seen = {}
    for i, r in enumerate(rounds):
        for d in r["deficiencies"]:
            e = seen.setdefault(d, {"n": 0, "first": i, "last": i})
            e["n"] += 1
            e["last"] = i
    rows = "".join(
        f"<tr class='{'persist' if e['last'] == len(rounds) - 1 else 'resolved'}'>"
        f"<td>{html.escape(d)}</td><td>{e['n']}</td>"
        f"<td>{html.escape(rounds[e['first']]['task'])}</td>"
        f"<td>{html.escape(rounds[e['last']]['task'])}</td>"
        f"<td>{'ACTIVE' if e['last'] == len(rounds) - 1 else 'not seen this round'}</td></tr>"
        for d, e in sorted(seen.items(), key=lambda kv: (-kv[1]["last"], -kv[1]["n"])))
    hist = "".join(
        f"<tr><td>{html.escape(r['task'])}</td><td class='p'>{r['P']:.0f}</td>"
        f"<td class='v'>{r['V']:.0f}</td><td>{len(r['deficiencies'])} "
        f"(+{s['per_round_new'][i]} new)</td></tr>"
        for i, r in enumerate(rounds))
    # P/V history sparkline (inline SVG, 2 polylines)
    W, H = 560, 120
    def pts(key):
        if len(rounds) < 2:
            return ""
        return " ".join(f"{i * W / (len(rounds) - 1):.0f},"
                        f"{H - (r[key] / 100) * H:.0f}"
                        for i, r in enumerate(rounds))
    spark = (f"<svg width='{W}' height='{H}'>"
             f"<polyline points='{pts('P')}' fill='none' stroke='#6cf' "
             f"stroke-width='3'/><polyline points='{pts('V')}' fill='none' "
             f"stroke='#fc6' stroke-width='3'/></svg>") if len(rounds) > 1 else ""
    strips = "".join(
        f"<figure><img src='scratch/_proof_{t}_strip.png' "
        f"onerror=\"this.parentNode.style.display='none'\">"
        f"<figcaption>{html.escape(t)} proof strip</figcaption></figure>"
        for t in (["t7", "t5"] if last["task"].lower().startswith("t7")
                  else ["t5"]))
    sat = ("SATURATED — the band floor is set"
           if s["saturated"] else
           f"NOT saturated — completeness {s['completeness']} (need ≥ "
           f"{COMPLETENESS_MIN}), dry tail {s['dry_tail']} (need ≥ {DRY_TAIL})")
    BOARD.write_text(f"""<!doctype html><html><head><meta charset="utf-8">
<title>SPIACE quality band</title><style>
body{{background:#111;color:#eee;font-family:system-ui;margin:32px}}
h1{{font-size:20px;font-weight:600;color:#aaa;margin:0 0 4px}}
.scores{{display:flex;gap:48px;margin:16px 0}}
.score{{text-align:center}}
.num{{font-size:96px;font-weight:700;line-height:1}}
.p .num,.p{{color:#6cf}} .v .num,.v{{color:#fc6}}
.lbl{{font-size:14px;color:#aaa;letter-spacing:2px}}
table{{border-collapse:collapse;margin:12px 0;font-size:14px}}
td,th{{border:1px solid #333;padding:4px 10px;text-align:left}}
th{{color:#aaa}} .persist td{{color:#eee}} .resolved td{{color:#777}}
.sat{{font-size:15px;padding:8px 12px;border:1px solid #444;display:inline-block}}
img{{max-width:900px;display:block;border:1px solid #333}}
figure{{margin:16px 0}} figcaption{{color:#888;font-size:13px}}
</style></head><body>
<h1>SPIACE quality band — {html.escape(last['task'])} (round {len(rounds)})</h1>
<div class="scores">
<div class="score p"><div class="num">{last['P']:.0f}</div><div class="lbl">PHYSICS</div></div>
<div class="score v"><div class="num">{last['V']:.0f}</div><div class="lbl">VISUAL</div></div>
</div>
<div class="sat">{html.escape(sat)}</div>
<h2 style="font-size:15px;color:#aaa">history (blue=P, gold=V)</h2>{spark}
<table><tr><th>round</th><th>P</th><th>V</th><th>deficiencies</th></tr>{hist}</table>
<h2 style="font-size:15px;color:#aaa">deficiency species (sighting counts are the Chao2 evidence)</h2>
<table><tr><th>species</th><th>sightings</th><th>first</th><th>last</th><th>state</th></tr>{rows}</table>
{strips}
</body></html>""", encoding="utf-8")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    led = load()
    if args[0] == "add":
        task, p, v = args[1], float(args[2]), float(args[3])
        defs = args[4:]
        led["rounds"].append({"task": task, "P": p, "V": v, "deficiencies": defs})
        LEDGER.write_text(json.dumps(led, indent=2) + "\n")
        render(led)                 # the board is never stale
        s = stats(led["rounds"])
        print(f"logged {task}: P={p} V={v} deficiencies={len(defs)} "
              f"({s['per_round_new'][-1]} new) — scoreboard.html rewritten")
    elif args[0] == "render":
        render(led)
        print(f"scoreboard.html rewritten ({len(led['rounds'])} rounds)")
    elif args[0] == "status":
        s = stats(led["rounds"])
        print(json.dumps(s, indent=2))
        if led["rounds"]:
            last = led["rounds"][-1]
            print(f"latest: {last['task']} P={last['P']} V={last['V']}")
        if s["saturated"]:
            band = led["rounds"][-1]
            print(f"SATURATED — band floor set at P={band['P']} V={band['V']} "
                  f"(completeness {s['completeness']}, dry tail {s['dry_tail']})")
        else:
            print(f"NOT saturated — completeness {s['completeness']} "
                  f"(need >= {COMPLETENESS_MIN}), dry tail {s['dry_tail']} "
                  f"(need >= {DRY_TAIL}); keep discovering")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
