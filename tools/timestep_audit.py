"""timestep_audit.py -- EVERY CONTROL CADENCE IN THIS REPO, AGAINST THE dt IT ACTUALLY RUNS AT.

RULE 0, stated before the build, because an instrument is a theory too:

    STATEMENT   Every control-cadence constant in this repository (`*_EVERY = N`, and the bare
                `k % N == 0` gates that predate them), multiplied by the timestep of THE MODEL
                THAT FILE ACTUALLY LOADS, equals the period its own comment or docstring claims.

    PREDICTION  The audit resolves a dt for every file that gates control on a modulus, and finds
                at least one site whose written claim disagrees with its measured cadence by more
                than the printed precision.

    FALSIFIER   Two independent triggers, both named before the run:
                1. If the audit convicts `tools/f3_stand.py` or `tools/train_walk.py` -- the two
                   files whose comments were REPAIRED on 2026-08-04 and are known-correct -- the
                   instrument is wrong, not the code. Those two are the CONTROL SUBJECT, pushed
                   through the whole instrument the way the clay control is (rule 12).
                2. If it reports zero unresolvable dt AND zero mismatches, the colony this task
                   was written to kill is already dead, and that is the finding -- published as
                   such, not converted into a fix list nobody needed.

WHY A TOOL AND NOT A GREP. The defect being hunted is `CTRL_EVERY = 20` under a docstring claiming
0.002 s, which made a "40 ms" control interval actually 20 ms. A grep for `0.002` cannot see it,
because the number that is wrong is the one that is ABSENT: the comment states a period, the code
states a count, and only their PRODUCT is checkable. And the product is not a constant of the
repository -- MEASURED here, 2026-08-04:

    external/myo_sim/leg/assets/myolegs_assets.xml   timestep 0.001   (myobody includes this)
    external/myo_sim/arm/assets/myoarm_assets.xml    timestep 0.002
    ChimeraEngine/train_transition.py  DT = 5e-4     (its own integrator, not an MJCF)

`myobody.xml` itself declares no `<option timestep>` at all; MuJoCo's documented default is 0.002
and the model runs at 0.001, which arrives four include levels down. So an audit that assumed one
dt for the repo would report `CONTROL_EVERY = 20  # still 100 Hz` in train_transition.py as a
defect -- and it is correct: 20 x 5e-4 = 0.01 s = 100 Hz exactly. THE INSTRUMENT MUST MOVE WITH
THE MEMBRANE AND KEEP NO COPY OF IT (rule 20): dt is read from the model, per file, every run.

    python tools/timestep_audit.py            # exit 0 = every claim matches; 1 = a mismatch
    python tools/timestep_audit.py --json agent_logs/timestep_audit.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ("tools", "ChimeraEngine", "Chimera/core", "story")

# THE CONTROL SUBJECT. These two files' comments were repaired on 2026-08-04 and are known to
# state the truth. If the audit convicts them, falsifier 1 has fired and the audit is the defect.
CONTROL_SUBJECTS = ("tools/f3_stand.py", "tools/train_walk.py")

# A CADENCE SITE is either a named constant or a bare modulus gate. Both forms exist in this repo
# and the bare ones are older, so an audit that only read the named ones would report the tidy
# half of the code and call the colony dead.
RE_CONST = re.compile(r"^\s*([A-Z][A-Z0-9_]*(?:_EVERY|_STEP|_STRIDE))\s*=\s*(\d+)\s*(?:#(.*))?$")
RE_GATE = re.compile(r"\b([a-z_]+)\s*%\s*(\d+)\s*==\s*0\b")
RE_DT_ASSIGN = re.compile(r"^\s*(DT|TIMESTEP|_DT)\s*=\s*([0-9.eE+-]+)\s*(?:#.*)?$")
RE_XML = re.compile(r"""["']([^"']*\.xml)["']""")
# CLAIMS. Only three places are read, and each is attributable to the site: the trailing comment
# on the constant's own line, the contiguous comment block directly above it, and docstring lines
# that NAME the constant. A repo-wide scan for "ms" would harvest "540ms at close range" from a
# renderer benchmark and file it against a control loop.
RE_MS = re.compile(r"(\d+(?:\.\d+)?)\s*ms\b", re.I)
RE_HZ = re.compile(r"(\d+(?:\.\d+)?)\s*Hz\b", re.I)
RE_SEC = re.compile(r"(\d*\.\d+)\s*s\b(?!\w)")

# ── WHAT THE NUMBER IS A CLAIM *ABOUT* ────────────────────────────────────────────────────────
# FALSIFIER 1 FIRED ON THE FIRST RUN, 2026-08-04, and the control subjects are what caught it.
# v1 harvested every time-like number within a few lines of a cadence constant and filed it as a
# claim about that cadence. It convicted BOTH known-correct files and two more, and every one of
# the four was the same defect -- MATCHING NAMES IS NOT MATCHING DEFINITIONS (rule 16), applied
# to units instead of variables. Read in the source, the four were:
#
#   f3_stand.py:51            "the timestep is 0.001 s"          <- a TIMESTEP statement, correct
#   train_walk.py:43          "myobody's timestep is 0.001 s"    <- a TIMESTEP statement, correct
#   train_walk.py:44          "not the 25 Hz every docstring
#                              in this pair of files asserted"   <- a NEGATION; 25 Hz is the
#                                                                   repaired-away value
#   port_trainer.py:237-8     "35 deg oscillation for 1.5 s,
#                              then FLAT for the remaining 3.5s" <- a DURATION of an observation
#   train_myobody_directional "T=150 x CONTROL_EVERY=20 x
#                     :91      timestep 0.001 s = a 3.0 s ep."   <- a dt AND a HORIZON, both true
#
# So a time-like number near a cadence is one of four different quantities, and only one of them
# is this audit's business. They are separated by the words around them, which is the only place
# the distinction lives -- a number carries its unit but not its SUBJECT.
RE_NEGATED = re.compile(r"\b(not|never|instead of|rather than|no longer|used to|claimed|"
                        r"asserted|wrongly|was)\b", re.I)
# a clause that ties the number to the CONTROL LOOP -- the only thing whose period is N*dt
RE_ABOUT_CADENCE = re.compile(r"\b(cadence|control|ctrl|interval|parser|drive|neural|loop|"
                              r"corrections?|per step|each step|every step)\b", re.I)
# a clause that says the number IS the integrator step -- checkable, and against dt not N*dt
RE_ABOUT_DT = re.compile(r"\b(timestep|time step|dt|integrator|m\.opt\.timestep)\b", re.I)
# a clause that says the number is a SPAN, not a rate. Not this audit's business at all.
RE_ABOUT_SPAN = re.compile(r"\b(episode|horizon|for the|remaining|over|during|window|lasted|"
                           r"held|survived|fell|settle|elapsed|total|duration|secs?\b|"
                           r"seconds of|s of )\b", re.I)


def clause_around(body: str, span) -> str:
    """The sentence-ish fragment a number sits in. Punctuation and `--` bound it.

    Why a clause and not the whole line: `train_walk.py`'s comment states the TRUE cadence and
    the FALSE one it is correcting, in one sentence. Reading the line as a unit makes both
    numbers claims of the same kind, and the correction convicts the file that made it.
    """
    lo, hi = span
    # THE COLON IS A CLAUSE BOUNDARY, and leaving it out cost the second run its verdict. Both
    # control subjects write `# 20 ms: the timestep is 0.001 s` -- one clause stating the CADENCE
    # and one stating the dt, separated by a colon. Without it the cadence claim reads inside a
    # clause that says "timestep" and gets checked against dt: 20 ms vs 1 ms, a conviction
    # manufactured entirely by where this function decided a sentence ends.
    seps = (";", ".", ",", ":", " -- ", "(", ")")
    start = max((body.rfind(sep, 0, lo) for sep in seps), default=-1)
    end = min((p for p in (body.find(sep, hi) for sep in seps) if p != -1), default=len(body))
    return body[start + 1:end]

# WHICH MODEL A FILE MEANS WHEN IT SAYS NOTHING. Resolved by import, never by guess: a file that
# imports MYOBODY from stand_port is running myobody, and saying so is reading the code, not
# assuming a default. Anything not on this list and naming no xml is reported UNRESOLVED --
# a fallback here would be an assumption wearing a hat.
IMPORT_MODEL = {
    "MYOBODY": "external/myo_sim/body/myobody.xml",
    "MYOLEGS": "external/myo_sim/leg/myolegs.xml",
}

_TS_CACHE: dict[str, float] = {}


def model_timestep(xml_rel: str):
    """m.opt.timestep for a model, MEASURED by loading it. Cached: it is a property of the file."""
    if xml_rel in _TS_CACHE:
        return _TS_CACHE[xml_rel]
    p = (ROOT / xml_rel)
    if not p.exists():
        _TS_CACHE[xml_rel] = None
        return None
    try:
        import mujoco
        m = mujoco.MjModel.from_xml_path(str(p))
        _TS_CACHE[xml_rel] = float(m.opt.timestep)
    except Exception as e:                       # a model this audit cannot load is UNRESOLVED,
        _TS_CACHE[xml_rel] = None                # never silently 0.002
        print(f"  [audit] cannot load {xml_rel}: {type(e).__name__}", file=sys.stderr)
    return _TS_CACHE[xml_rel]


def resolve_dt(path: Path, text: str, lines):
    """This file's own timestep, and WHERE it came from. Returns (dt, provenance) or (None, why).

    Precedence is by specificity, not convenience: a file that declares its own integrator step
    is running that step whatever model it also loads.
    """
    for ln in lines:
        mo = RE_DT_ASSIGN.match(ln)
        if mo:
            try:
                return float(mo.group(2)), f"module-level {mo.group(1)} = {mo.group(2)}"
            except ValueError:
                pass
    # an xml named in the file
    for cand in RE_XML.findall(text):
        rel = cand.replace("\\", "/")
        for probe in (rel, f"external/myo_sim/body/{Path(rel).name}",
                      f"external/myo_sim/leg/{Path(rel).name}"):
            ts = model_timestep(probe)
            if ts:
                return ts, f"{probe} (loaded, m.opt.timestep)"
    # an import that names a model
    for sym, rel in IMPORT_MODEL.items():
        if re.search(rf"\b{sym}\b", text):
            ts = model_timestep(rel)
            if ts:
                return ts, f"imports {sym} -> {rel} (loaded)"
    # a file that imports a cadence from another file inherits that file's world
    if re.search(r"from\s+(train_walk|f3_stand|train_stand|walk_dyad|policy_gait_eval)\s+import",
                 text):
        ts = model_timestep("external/myo_sim/body/myobody.xml")
        if ts:
            return ts, "imports a myobody harness -> myobody.xml (loaded)"
    return None, "no DT, no .xml, no model import -- UNRESOLVED"


def claims_for(lines, i, name):
    """Every period this site CLAIMS, with the text that claims it. Three attributable sources."""
    out = []
    # ATTACHED vs DISTANT. A comment physically attached to an assignment -- on its line, or in
    # the contiguous block immediately above or below it -- documents THAT ASSIGNMENT; that is
    # what attaching it means. A docstring line elsewhere in the file merely mentions the name.
    # The distinction decides what an otherwise-unattributed number is a claim about, and
    # guessing it is what fired falsifier 1 twice.
    src = [(lines[i], "same line", True)]
    j = i - 1
    while j >= 0 and lines[j].strip().startswith("#"):
        src.append((lines[j], f"comment L{j+1}", True))
        j -= 1
    j = i + 1
    while j < len(lines) and lines[j].strip().startswith("#") and "=" not in lines[j]:
        src.append((lines[j], f"comment L{j+1}", True))
        j += 1
    if name:
        for k, ln in enumerate(lines):
            if name in ln and ("\"\"\"" in ln or ln.strip().startswith("#")) and k != i:
                src.append((ln, f"docstring L{k+1}", False))
    for text, where, attached in src:
        body = text.split("#", 1)[1] if "#" in text else text
        for unit, rx in (("ms", RE_MS), ("Hz", RE_HZ), ("s", RE_SEC)):
            for mo in rx.finditer(body):
                cl = clause_around(body, mo.span())
                # ROUTED BY WHAT THE CLAUSE IS ABOUT, and a number the clause does not tie to
                # anything is DROPPED rather than guessed at. A dropped claim costs this audit a
                # check; a guessed one costs it its verdict, which is what falsifier 1 measured.
                if RE_NEGATED.search(cl):
                    subject = "negated"          # the text is CORRECTING this value, not claiming it
                elif RE_ABOUT_DT.search(cl):
                    subject = "dt"               # checkable, but against the timestep
                elif RE_ABOUT_SPAN.search(cl):
                    subject = "span"             # a duration -- not a cadence, not this audit's
                elif RE_ABOUT_CADENCE.search(cl) or (name and name in cl):
                    subject = "cadence"
                elif attached and name:
                    # A bare period in a comment ATTACHED to a named cadence constant is a claim
                    # about that constant. Nothing else is being defined on that line.
                    subject = "cadence"
                else:
                    subject = "unattributed"
                out.append(dict(unit=unit, val=float(mo.group(1)), where=where,
                                raw=mo.group(0).strip(), subject=subject, clause=cl.strip()[:70]))
    return out


def audit():
    rows, unresolved = [], []
    files = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if base.exists():
            files += sorted(base.rglob("*.py"))
    for path in files:
        if "__pycache__" in str(path) or "archive" in str(path):
            continue
        try:
            text = path.read_text(encoding="utf8", errors="replace")
        except OSError:
            continue
        lines = text.splitlines()
        sites = []
        for i, ln in enumerate(lines):
            mo = RE_CONST.match(ln)
            if mo:
                sites.append((i, mo.group(1), int(mo.group(2)), "constant"))
                continue
            if ln.strip().startswith("#"):
                continue
            g = RE_GATE.search(ln)
            # a modulus gate is a CONTROL gate only if the file steps a physics sim; a bare
            # `i % 100 == 0` progress print is not a cadence and convicting it would be noise.
            if g and ("mj_step" in text or "d.ctrl" in text) and int(g.group(2)) > 1:
                sites.append((i, None, int(g.group(2)), f"gate `{g.group(1)} % {g.group(2)}`"))
        if not sites:
            continue
        dt, prov = resolve_dt(path, text, lines)
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        if dt is None:
            unresolved.append((rel, prov, [s[2] for s in sites]))
            continue
        for i, name, n, kind in sites:
            period_ms = n * dt * 1000.0
            hz = 1.0 / (n * dt)
            verdicts, dropped = [], []
            for c in claims_for(lines, i, name):
                unit, val, subject = c["unit"], c["val"], c["subject"]
                if subject in ("negated", "span", "unattributed"):
                    dropped.append(c)            # counted and printed, never silently discarded
                    continue
                if subject == "dt":
                    # THE CLAIM IS ABOUT THE TIMESTEP, so it is checked against the timestep. This
                    # is a real check and it is the ORIGINAL defect's own shape: a docstring
                    # asserting 0.002 over a model that runs 0.001.
                    want = dt * 1000.0 if unit == "ms" else (1.0 / dt if unit == "Hz" else dt)
                    got = (f"{dt*1000:.2f} ms" if unit == "ms" else
                           f"{1.0/dt:.1f} Hz" if unit == "Hz" else f"{dt:.4f} s")
                else:
                    want = period_ms if unit == "ms" else (hz if unit == "Hz" else period_ms / 1000.0)
                    got = (f"{period_ms:.1f} ms" if unit == "ms" else
                           f"{hz:.1f} Hz" if unit == "Hz" else f"{period_ms/1000.0:.4f} s")
                ok = abs(val - want) <= max(0.05 * abs(want), 1e-4 if unit == "s" else 0.5)
                verdicts.append(dict(claim=c["raw"], where=c["where"], ok=bool(ok),
                                     measured=got, about=subject, clause=c["clause"]))
            rows.append(dict(file=rel, line=i + 1, name=name or kind, n=n, dt=dt,
                             period_ms=period_ms, hz=hz, provenance=prov, claims=verdicts,
                             dropped=dropped))
    return rows, unresolved


def main() -> int:
    rows, unresolved = audit()
    print("\nTIMESTEP AUDIT -- every cadence against the dt its own file runs at")
    print("=" * 100)
    print(f"{'file:line':46}{'const':16}{'N':>4}{'dt':>9}{'period':>10}{'Hz':>8}  claim")
    print("-" * 100)
    bad, checked, n_dropped = [], 0, 0
    for r in sorted(rows, key=lambda r: r["file"]):
        tag = f"{r['file']}:{r['line']}"
        n_dropped += len(r["dropped"])
        claim_txt = "(no stated period)"
        if r["claims"]:
            checked += 1
            parts = []
            for c in r["claims"]:
                parts.append(f"{c['claim']}[{c['about']}] "
                             f"{'OK' if c['ok'] else 'MISMATCH -> ' + c['measured']}")
                if not c["ok"]:
                    bad.append((tag, c, r))
            claim_txt = "; ".join(parts)
        elif r["dropped"]:
            claim_txt = ("(" + ", ".join(sorted({d['subject'] for d in r['dropped']}))
                         + " only -- not a cadence claim)")
        print(f"{tag:46}{str(r['name'])[:15]:16}{r['n']:>4}{r['dt']:>9.4f}"
              f"{r['period_ms']:>9.1f}m{r['hz']:>7.1f}  {claim_txt}")
    print("-" * 100)
    if unresolved:
        print(f"\nUNRESOLVED dt -- reported, never assumed ({len(unresolved)} files):")
        for rel, why, ns in unresolved:
            print(f"  {rel:56} N={ns}  {why}")
    # THE CONTROL. If the two known-correct files come back convicted, the instrument is the bug.
    ctrl_bad = [t for t, _, _ in bad if t.split(":")[0] in CONTROL_SUBJECTS]
    print("\n" + "=" * 100)
    print(f"  sites found {len(rows)}, sites stating a checkable period {checked}, "
          f"MISMATCHES {len(bad)}")
    print(f"  time-like numbers DROPPED as not-about-the-cadence: {n_dropped} "
          f"(negations, spans, unattributed -- see --json for every one)")
    print(f"  CONTROL SUBJECT ({', '.join(CONTROL_SUBJECTS)}): "
          + ("CLEAN -- the instrument agrees with the two known-correct files"
             if not ctrl_bad else f"CONVICTED {ctrl_bad} -- FALSIFIER 1 FIRED, the audit is wrong"))
    for tag, c, r in bad:
        print(f"\n  MISMATCH  {tag}  {r['name']} = {r['n']}")
        print(f"            claims {c['claim']!r} in {c['where']}")
        print(f"            measured {c['measured']}  (dt {r['dt']} from {r['provenance']})")
    if not bad and not unresolved:
        print("  FALSIFIER 2: no mismatch and no unresolved dt. The colony is already dead.")
    if "--json" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--json") + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(dict(rows=rows, unresolved=unresolved,
                                       mismatches=[t for t, _, _ in bad],
                                       control_convicted=ctrl_bad), indent=1), encoding="utf8")
        print(f"  JSON: {out}")
    return 1 if (bad or ctrl_bad) else 0


if __name__ == "__main__":
    sys.exit(main())
