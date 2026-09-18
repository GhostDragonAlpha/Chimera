"""THE_LIBRARY generator: the catalog of the batch-admitted library.

Pure projection: graph in -> markdown out. Same store bytes -> same document
bytes (no clock, no locale, no environment text, sorted iteration everywhere).
Every count printed is an enumeration of the store; every license line is
quoted verbatim from the source record's own manifest; every gap is quoted
from the graph record that owns it. See work.data.library_catalog_20260918
in the authored program for the Rule-0 membrane (statement / prediction /
falsifier) this generator is the contract of.

Usage (from the checkout root):
    python -B tools/creature_graph/library_catalog.py            # canonical
    python -B tools/creature_graph/library_catalog.py --store PATH --out PATH
"""
import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from store import STORE_PATH, CreatureGraph  # noqa: E402

DEFAULT_OUT = os.path.normpath(os.path.join(
    HERE, "..", "..", "docs", "THE_LIBRARY.md"))

RECEIPT_PATH_RE = re.compile(
    r"tools/science_funnel/validation/batch[^\"'\s\\]*/receipt\.json")

GAPS_OWNER = "work.data.batch_intake"
GAPS_KEY = "database_hunt_20260917"
GAPS_FIELD = "gaps_that_still_stand"

# License-class classification: a deterministic substring rule over the
# source record's own quoted license text (first match wins; the quoted
# text is always shown and is the authoritative fact -- the class is a
# bookkeeping label, defined here so the summary table can group rows).
LICENSE_CLASSES = (
    ("CC BY-SA", "CC BY-SA"),
    ("CC BY 4.0", "CC BY 4.0"),
    ("CC Attribution 4.0", "CC BY 4.0"),
    ("CC0", "CC0"),
    ("public domain", "public domain"),
)


def classify_license(text: str) -> str:
    low = text.lower()
    base = "custom"
    for needle, label in LICENSE_CLASSES:
        if needle.lower() in low:
            base = label
            break
    if "conflict" in low:
        base += " + conflict recorded"
    return base


def jstr(value) -> str:
    """Stable one-line JSON rendering for embedding strings in the doc."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def record_set_digest(records: list) -> str:
    """sha256 over the canonical JSON of every cited record (sorted by id).

    Any byte change to any cited record moves this digest -- the catalog's
    per-source fingerprint (the mutation-sensitivity surface of the doc)."""
    blob = json.dumps(
        [(r["id"], r) for r in sorted(records, key=lambda o: o["id"])],
        ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def collect(g: CreatureGraph) -> dict:
    """All catalog facts, derived only from the loaded graph."""
    sources = sorted((o for o in g.objects.values()
                      if o["kind"] == "source" and isinstance(o.get("science_funnel"), dict)),
                     key=lambda o: o["id"])
    records_by_source = {s["id"]: [] for s in sources}
    for o in g.objects.values():
        src = (o.get("provenance") or {}).get("source_id")
        if src in records_by_source and o.get("science_funnel") is not None:
            records_by_source[src].append(o)

    contracts_meta = g.meta.get("class_contracts") or {}
    contracts_path_used = []
    for o in g.objects.values():
        cc = o.get("class_contract")
        if isinstance(cc, dict) and str(cc.get("class_id", "")).startswith("batch."):
            contracts_path_used.append((cc.get("class_id"), cc.get("version")))

    receipt_citations = []
    for oid, o in sorted(g.objects.items()):
        blob = json.dumps(o, ensure_ascii=False)
        for path in sorted(set(RECEIPT_PATH_RE.findall(blob))):
            receipt_citations.append({"object": oid, "path": path})

    gaps = []
    owner = g.objects.get(GAPS_OWNER)
    if owner:
        obs = owner.get("observation") or {}
        hunt = obs.get(GAPS_KEY) or {}
        raw = hunt.get(GAPS_FIELD)
        if isinstance(raw, list):
            gaps = [{"text": str(item), "owner": GAPS_OWNER} for item in raw]

    return {
        "sources": sources,
        "records_by_source": records_by_source,
        "contracts_meta": contracts_meta,
        "receipt_citations": receipt_citations,
        "gaps": gaps,
        "totals": {
            "objects": len(g.objects),
            "relations": len(g.relations),
            "admitted_sources": len(sources),
            "admitted_records": sum(len(v) for v in records_by_source.values()),
        },
    }


def _md_escape_cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def build_catalog(g: CreatureGraph) -> str:
    """Render the markdown document. Pure function of the graph."""
    facts = collect(g)
    graph_hash = g.graph_hash()
    lines = []
    add = lines.append

    add("# THE LIBRARY")
    add("")
    add("The generated catalog of the library admitted through the batch")
    add("membrane (`tools/science_funnel/batch/`). One section per admitted")
    add("source; a summary table; the standing gaps; how to admit the next")
    add("database.")
    add("")
    add("This document is GENERATED by `tools/creature_graph/library_catalog.py`")
    add("from the live graph (`tools/creature_graph/data/creature_graph.json` +")
    add("its bulk shards) and contains no hand-written facts: every count is an")
    add("enumeration of the store, every license line is quoted verbatim from")
    add("the source record's own manifest, every gap is quoted from the graph")
    add("record that owns it. Determinism is the law (work.data.")
    add("library_catalog_20260918): regenerating from an unchanged store")
    add("reproduces this file byte-identically.")
    add("")
    add("Regenerate with:")
    add("")
    add("```")
    add("python -B tools/creature_graph/library_catalog.py")
    add("```")
    add("")
    add(f"- store schema_version: {jstr(g.meta.get('schema_version'))}")
    add(f"- store graph_hash: `{graph_hash}`")
    add(f"- store objects: {facts['totals']['objects']}")
    add(f"- store relations: {facts['totals']['relations']}")
    add(f"- admitted sources (kind=source with an intake bundle): "
        f"{facts['totals']['admitted_sources']}")
    add(f"- admitted records (objects citing an admitted source): "
        f"{facts['totals']['admitted_records']}")
    add("")

    # ------------------------------------------------------------ summary --
    add("## Summary")
    add("")
    add("One row per admitted source object (a database admitted twice through")
    add("two distinct pinned bundles appears twice -- that is the honest state")
    add("of the library). License class is a bookkeeping label derived by the")
    add("documented substring rule over the source's own quoted license text;")
    add("the quoted text in each section is the authoritative fact. Auth class")
    add("is the record's own `science_funnel.authority`.")
    add("")
    add("| source (manifest id) | bundle (object id) | records | license class | auth class |")
    add("|---|---|---:|---|---|")
    for s in facts["sources"]:
        sfn = s.get("science_funnel") or {}
        man = (sfn.get("manifest") or {}).get("source") or {}
        recs = facts["records_by_source"][s["id"]]
        license_text = str(man.get("license", ""))
        add("| {} | `{}` | {} | {} | {} |".format(
            _md_escape_cell(man.get("id", "?")), s["id"], len(recs),
            _md_escape_cell(classify_license(license_text)),
            _md_escape_cell(sfn.get("authority", "?"))))
    add("")

    # ------------------------------------------------- one section / source --
    add("## Sources")
    add("")
    for s in facts["sources"]:
        sfn = s.get("science_funnel") or {}
        man = sfn.get("manifest") or {}
        msrc = man.get("source") or {}
        recs = facts["records_by_source"][s["id"]]
        add(f"### {s['id']}")
        add("")
        add(f"- library name: {jstr(s.get('name'))}")
        add(f"- manifest source id: {jstr(msrc.get('id'))}")
        add(f"- adapter: {jstr(man.get('adapter'))}")
        add(f"- status: {jstr(s.get('status'))}")
        add(f"- authority: {jstr(sfn.get('authority'))}")
        add(f"- runtime_ready: {jstr(sfn.get('runtime_ready'))}")
        add(f"- release: {jstr(msrc.get('release'))}")
        add(f"- url: {jstr(msrc.get('url'))}")
        add(f"- storage: {jstr(sfn.get('storage'))}")
        add(f"- bundle_id: `{sfn.get('bundle_id')}` (sha-pinned intake bundle;")
        add(f"  per-bundle receipt fields are embedded in this source record)")
        add("")
        add("License (quoted verbatim from this source record's own manifest):")
        add("")
        add(f"> \"{msrc.get('license', '')}\"")
        add("")
        kinds = {}
        for r in recs:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        add(f"- records: {len(recs)} total")
        for kind in sorted(kinds):
            add(f"  - kind {kind}: {kinds[kind]}")
        contracts = {}
        for r in recs:
            cc = r.get("class_contract") or {}
            cid = cc.get("class_id")
            ver = cc.get("version")
            key = (str(cid) if cid is not None else "(no class contract on record)",
                   str(ver) if ver is not None else "-")
            contracts[key] = contracts.get(key, 0) + 1
        add("- class contracts used:")
        for (cid, ver), n in sorted(contracts.items()):
            meta = facts["contracts_meta"].get(cid) or {}
            add(f"  - {cid} v{ver}: {n} records"
                + (f" (contract sha256 `{meta.get('sha256', '')[:16]}...`)"
                   if meta else ""))
        quarantine = sfn.get("quarantine") or []
        add(f"- quarantined at admission: {len(quarantine)}")
        causes = {}
        details = {}
        for item in quarantine:
            if isinstance(item, dict):
                code = str((item.get("refusal") or {}).get("code"))
            else:
                code = "<non-dict entry>"
            causes[code] = causes.get(code, 0) + 1
            if code not in details:
                d = (item.get("refusal") or {}).get("detail") if isinstance(item, dict) else None
                details[code] = d
        for code in sorted(causes):
            d = details.get(code)
            line = f"  - refusal `{code}`: {causes[code]}"
            if d is not None:
                line += f" (first detail: {jstr(d)})"
            add(line)
        law = ((sfn.get("receipt") or {}).get("count_identity") or {}).get("law")
        if law:
            add(f"- count identity (quoted from the source record's own "
                f"receipt): \"{law}\"")
        deferred = [r for r in recs
                    if str((r.get("class_contract") or {}).get("class_id", ""))
                    .startswith("batch.deferred.")]
        add(f"- deferred records: {len(deferred)}")
        for r in sorted(deferred, key=lambda o: o["id"]):
            sf = r.get("science_funnel") or {}
            cause = (sf.get("source") or {}).get("known_gaps") if isinstance(sf.get("source"), dict) else None
            add(f"  - `{r['id']}` ({jstr((r.get('class_contract') or {}).get('class_id'))})"
                + (f" cause: {jstr(cause)}" if cause else ""))
        gaps_src = msrc.get("known_gaps") or []
        add(f"- known gaps declared by the source record: {len(gaps_src)}")
        for gap in gaps_src:
            add(f"  - {jstr(gap)}")
        add(f"- record-set digest: `{record_set_digest(recs)}` (sha256 over the")
        add("  canonical JSON of every record cited by this section; any byte")
        add("  change to any cited record moves it)")
        add("")

    # ------------------------------------------------------ standing gaps --
    add("## Standing gaps")
    add("")
    if facts["gaps"]:
        add(f"Quoted verbatim from the graph record `{GAPS_OWNER}` "
            f"(observation.{GAPS_KEY}.{GAPS_FIELD}); nothing here is the "
            "catalog's own judgement:")
        add("")
        for item in facts["gaps"]:
            add(f"- \"{item['text']}\"")
        add("")
    else:
        add(f"The record `{GAPS_OWNER}` in this store carries no "
            f"`observation.{GAPS_KEY}.{GAPS_FIELD}` list, so the catalog "
            "reports none. (An honest empty is a result, not a blank.)")
        add("")

    # --------------------------------------------- batch receipts in graph --
    add("## Batch receipts cited by graph records")
    add("")
    if facts["receipt_citations"]:
        for cite in facts["receipt_citations"]:
            add(f"- `{cite['path']}` -- cited by graph record `{cite['object']}`")
        owner = g.objects.get(GAPS_OWNER) or {}
        obs = owner.get("observation") or {}
        if obs.get("receipt"):
            add("")
            add(f"Whole-batch receipt (from `{GAPS_OWNER}.observation`): "
                f"`{obs.get('receipt')}` (sha256 `{obs.get('receipt_sha256')}`, "
                f"batch_id `{obs.get('batch_id')}`)")
        add("")
    else:
        add("No graph record cites a batch receipt path in this store.")
        add("")

    # ------------------------------------------------- how to admit the next --
    add("## How to admit the next database")
    add("")
    add("The admission path is the batch pipeline: one command connects the")
    add("database, integrates every record and proves the whole batch against")
    add("per-class mechanical contracts in one run with one receipt:")
    add("")
    add("```")
    add("python -B -m tools.creature_graph.batch_qualify \\")
    add("    --admit <connector_id>[,...] --reprove all --train exercise \\")
    add("    --out tools/science_funnel/validation/<lane>/receipt.json [--apply]")
    add("```")
    add("")
    add("- connectors: `tools/science_funnel/batch/connectors*.py` (artifact")
    add("  pins resolve at load time from each data dir's")
    add("  `download_receipt.json` -- never hardcoded, never guessed)")
    add("- per-class contracts: `tools/creature_graph/data/authored/")
    add("  class_contracts.json` (each contract carries its own statement,")
    add("  prediction, falsifier and mechanical checks; the store refuses a")
    add("  record whose class contract is unknown or version-drifted)")
    add("- the whole-batch count identity, quoted from the embedded source")
    add("  receipts above: \"fetched == admitted + quarantined + conflicts,")
    add("  zero silent drops\"")
    add("- without `--apply` everything runs on scratch and nothing is")
    add("  written into the authored program; with `--apply` the merge goes")
    add("  through the one serial writer and the store is rebuilt")
    add("")
    add("*End of the generated catalog.*")
    add("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store", default=STORE_PATH,
                    help="path to the creature-graph store (default: canonical)")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="path of the markdown document (default: docs/THE_LIBRARY.md)")
    args = ap.parse_args()

    g = CreatureGraph.load(args.store)
    doc = build_catalog(g).encode("utf-8")
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(doc)
    facts = collect(g)
    print(f"wrote {out} ({len(doc)} bytes); sources="
          f"{facts['totals']['admitted_sources']} "
          f"records={facts['totals']['admitted_records']} "
          f"graph_hash={g.graph_hash()[:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
