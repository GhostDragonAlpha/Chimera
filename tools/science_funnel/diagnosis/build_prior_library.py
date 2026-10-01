"""build_prior_library.py -- build prior_faces.json from the PAST WAVE RECEIPTS'
death records (waves 28-38's named faces).

This builder READS the receipts' rule_0 statements + measurements status (the
death descriptions) -- that is its whole job; the PACKET GENERATOR never does
(it only reads the emitted JSON, filtered to waves strictly before the diagnosed
run's wave).  Each death_class tag is assigned HERE, by hand, with the receipt's
own words as the justification, and is auditable in the emitted JSON.
"""
from __future__ import annotations

import argparse
import json
import re

RECEIPT_DIR = "tools/science_funnel/validation/gait_zero_20260919"

# The hand tag map: wave -> (death_class, justification quote drawn verbatim
# from that wave's own receipt text, or its parent's statement when the parent
# records the face).  Waves with pass=None are measurement/derivation lanes and
# carry the face they NAME without a ship verdict.
TAGS = {
    28: ("CAPACITY_FOLD", "the ride-concentration fold -- 'whose knee was already at its wave-27 cap ... "
         "the fold is CAP-LIMITED DYNAMICS' (recorded in wave-29's statement as the wave-28 deaths being owned)"),
    29: ("CAPACITY_FOLD", "the ride-concentration fold is a joint-capacity death (wave 29's three-point proof)"),
    30: (None, "derivation lane: derives what the standing knee is actually ASKED through the ride"),
    31: ("BAND_MISS", "after the 142 alternation fire the L pads NEVER re-enter the touch band (pair-min 11.5 mm "
         "at the 151 replant event)"),
    32: ("UNLOAD_DRAIN", "the L's landing UNLOADED the standing R (the R rxn 7.47 N@158 -> 3.80@159 -> 1.59@160 -> 0@161)"),
    33: ("UNLOAD_DRAIN", "the R's share hit 0 at tick 215 -- five ticks BEFORE the L's band entry (220)"),
    34: ("UNLOAD_DRAIN", "the R -- the ride-era carrier -- drained mid-haul; the drain is geometric"),
    35: ("CALENDAR_SCATTER", "the carrier self-unload fire deadline is REAL but its cost is the exchange calendar "
         "itself -- measured twice (the calendar death at 305; the re-phased ride death at 266)"),
    36: ("CALENDAR_SCATTER", "the rung falsifier fired on the first (and only) amended build (the refusal 298 <= 300) "
         "-- a +1 twelfth-launch drift its own pre-registered window allowed but its waive's touch-window could not afford"),
    37: ("GRAZE_MISFIRE", "the re-locked trajectory's OWN dynamics cleared a STALL swing's hold (the R's [202,211) "
         "hold cleared at the 206 decision), the (a)-waive fired INSIDE stall eras, and the calendar scattered; "
         "THE LEDGER FALSIFIER FIRED (33.559179 > the 32.861605 bound)"),
    38: (None, "PASS = TRUE: the rung-pass/ledger-pass composition ships"),
}


def _law_face(statement: str) -> str:
    m = re.search(r"THE [A-Z][A-Z'\- ,]{4,90}?(?: LAW| GUARD|HOLD|DEADLINE|SIDE)(?:\s*\((?:wave \d+)\))?", statement)
    if m:
        return m.group(0).strip()
    m = re.search(r"(THE [A-Z][A-Z'\- ,]{4,80}?)(?:\s*\((?:wave \d+)\))?[.:]", statement)
    return (m.group(1).strip() if m else statement.split(".")[0][:80])


def _status_text(d: dict) -> str:
    ms = d.get("measurements", {})
    if isinstance(ms, list) and ms and isinstance(ms[0], dict):
        return ms[0].get("status", "")
    if isinstance(ms, dict):
        return ms.get("status", "")
    return ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt-dir", default=RECEIPT_DIR)
    ap.add_argument("--out", default="tools/science_funnel/diagnosis/prior_faces.json")
    ap.add_argument("--waves", default="28-38")
    args = ap.parse_args(argv)
    a, b = (int(x) for x in args.waves.split("-"))
    faces = []
    for w in range(a, b + 1):
        path = f"{args.receipt_dir}/receipt_wave{w}.json"
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
        except FileNotFoundError:
            continue
        cls, why = TAGS.get(w, (None, "untagged"))
        status = _status_text(d)
        m = re.search(r"PASS = \w+[^\n]{0,340}", status)
        death_record = m.group(0) if m else status[:340]
        faces.append(dict(wave=w,
                          face=_law_face(d.get("rule_0", {}).get("statement", "")),
                          pass_flag=d.get("pass"),
                          death_class=cls,
                          tag_justification=why,
                          death_record=death_record,
                          lane=d.get("lane"),
                          receipt=path,
                          shape={}))
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(faces, f, indent=1, ensure_ascii=False)
    print(f"[prior-library] {len(faces)} faces -> {args.out}")
    for x in faces:
        print(f"  wave {x['wave']:2d} pass={str(x['pass_flag']):5s} class={str(x['death_class']):14s} {x['face'][:60]}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
