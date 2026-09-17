# INTAKE-LIFE — Rule 0 admission of three life-science sources
Lane: `lane/intake-life-20260917` (base 5a180eb4) · Worker: intake-life · Preregistered 2026-09-17

This document states the Rule 0 membrane BEFORE the qualifying run. The three
sources were probe-verified (license + authless URL + direct download) by
`docs/research/20260917_dbhunt_phys.md` the same day; this lane converts them
into pinned, mechanically proven batch admissions.

---

## RULE 0 ADMISSION (stated before the run)

**STATEMENT.** Three license-clear, authless life-science databases — PanTHERIA 1.0
(CC0, 5,417 mammal species, BMR + body mass), NCBI taxdmp (public domain, Macaca
subtree names + ranks), Rhea (CC BY 4.0, reaction → ChEBI → SMILES) — can be
admitted as sha256-pinned intake bundles whose adapters carry mechanical
falsifiers per record class, with zero silent drops.

**PREDICTION (not yet measured).**
1. PanTHERIA Macaca BMR records pass with units converted to SI W
   (`mLO2/hr × 20.1 J/mL ÷ 3600 s/hr`), the 20.1 J/mL O₂ calorific equivalent
   carried on every record as a **declared assumption**, never as a measurement.
2. Every PanTHERIA Macaca binomial resolves against the NCBI taxdmp Macaca
   subtree (scientific names + synonyms, all name classes).
3. Every PanTHERIA `-999` sentinel cell is recorded as nodata with an explicit
   unknown on the species record and produces no measurement record.
4. The count identity closes for all three connectors:
   fetched == admitted + quarantined + conflicts, zero silent drops.

**FALSIFIER (named before the run).**
- A `-999` sentinel reaching a measurement record **refuses the class**: the
  adapter must quarantine it before drafting, and the class contract's
  positive-bounded `field_range` check must flag any sentinel-derived value
  (−999 mLO2/hr → −5.58 W < 0) if the adapter guard is ever removed. Verified
  by direct injection before the qualifying run.
- An upstream byte change refuses the fetch (`pin_drift`): PanTHERIA zip must
  hash `fe84274a…46df9`, taxdmp.zip must measure 79,535,405 bytes and match its
  `.md5` sidecar, and re-deriving the Macaca subtree from the pinned zip must
  be byte-identical (idempotent rebuild).
- A Macaca binomial that does NOT resolve against the subtree quarantines that
  record (no fuzzy match, no silent species drop).
- The second full `--apply` run must create zero objects and reproduce the
  graph hash (idempotency falsifier, enforced by `batch_qualify`).

## DERIVATIONS (RULE 1 — no sweeps)

- **BMR → SI W.** `1 mLO2/hr = (1e-3 L / 3600 s) × 20.1 kJ/L? — no:* the exact
  chain used is `W = mLO2hr × 20.1 J / 3600 s` (per mL O₂ consumed), the
  approximate respiratory calorific equivalent for a typical mixed diet
  respiratory quotient. **This is an assumption declared on every record**, not
  a quantity PanTHERIA measured; records carry
  `unknowns: calorific_equivalent_assumed_20.1_J_per_mL_O2`.
- **Mass → SI kg.** grams × 1e-3, exact (existing `units.convert` path).
- **Subtree scope.** Genus *Macaca* taxon + all descendants, nothing else; the
  79.5 MB zip stays in `data/ncbi_taxdmp/` pinned by the download receipt
  (it exceeds the 64 MB bundle artifact limit), bundles pin the two derived
  TSVs, and the derivation is a pure stdlib function of the zip bytes
  (`life_fetch.extract_macaca_subtree`, producer-sha256 recorded).
- **Name resolution.** Exact match after normalization (underscore↔space,
  whitespace collapse); a binomial mapping to more than one subtree taxon
  quarantines (ambiguous), never picks.

## SOURCES (pins recorded in each `download_receipt.json`)

| Source | License | Pin |
|---|---|---|
| PanTHERIA 1.0 `ECOL_90_184.zip` (figshare 5604752) | CC0 | sha256 `fe84274a39ba73b3c9b6950b78ba44c545852db9809d1549b0071cfdde46df9f`, 2,950,934 bytes |
| NCBI taxdmp.zip | public domain (17 USC 105) | 79,535,405 bytes + `.md5` sidecar verified; subtree TSVs derived + pinned |
| Rhea `tsv/rhea-chebi-smiles.tsv` + `LICENSE.txt` | CC BY 4.0 | sha256 in receipt; LICENSE.txt pinned as artifact (it IS the license evidence) |

## RUN COMMAND (preregistered)

```
python -B -m tools.creature_graph.batch_qualify --reprove all \
  --admit pantheria_1_0,ncbi_taxdmp_macaca,rhea_reactions --apply \
  --out tools/science_funnel/validation/batch_life_20260917/receipt.json
```

`--reprove all` is included deliberately: the five existing admissions must
re-prove byte-identically after this lane's code changes (recorded-producer
replay) — evidence unchanged is part of this admission's claim.

## FORCED DEVIATION (recorded 2026-09-17, before the re-run)

The preregistered command above ran once end-to-end and PASSED (all
predictions; receipt batch_id 3958919dfa432d2b; graph 31,744 objects) — but
publishing it was REFUSED by GitHub's hard 100 MB per-file limit: applying
all 23,776 records grew the monolithic stores to project_program.json
104.62 MB and creature_graph.json 114.19 MB (measured; base 32.06/34.94 MB,
delta +77.64/+84.80 MB, ≈3.3–3.6 KB per admitted object including graph
wrapper, derived_from edges and roadmap layout).

This is a structural ceiling of the current single-JSON store design, not a
tunable: even maximal per-record slimming (embedded source prose ≈700 B/record,
payload dedup) leaves creature_graph.json ≈100 MB with zero headroom for the
parallel intake lanes already in flight. Splitting or sharding the store is
architecture work for the lead — named blocker, not patched here.

Derived re-scope, keeping every prediction falsifiable and nothing silently
dropped:
1. `--reprove all --admit pantheria_1_0,ncbi_taxdmp_macaca --apply` →
   `receipt.json` — the applied admission (9,574 records; stores land
   ≈63/69 MB with real headroom).
2. `--admit rhea_reactions` (no `--apply`) →
   `receipt_rhea_proven_not_applied.json` — Rhea is CONNECTED, INTEGRATED and
   PROVEN (bundle verified, contracts 14,202/14,202, count identity closed),
   but not yet graph-resident: its residency waits on the store-split task.
   Nothing is lost — the pinned bytes + recorded producer regenerate the
   bundle deterministically (replay law), and a later
   `--admit rhea_reactions --apply` after the split closes the residency.

## VERDICT (runs completed 2026-09-17)

**SUPPORTED**, every prediction, with two honest corrections the run measured.

**Applied receipt** `validation/batch_life_20260917/receipt.json`
(batch_id a26c43a578637e40, bundle 65fa5a6eb2c0 pantheria / c663a7194d87 taxdmp):
all five pre-existing admissions re-proved byte-identically (evidence
unchanged); PanTHERIA 9,531 records + taxdmp Macaca 43 admitted and applied;
13,395 verified, 0 contract failures, count identity closed; graph 17,541
objects (hash b228888a57e8a879); graphify consumer roundtrip HONEST 7/7;
bundles re-propose as no-ops (idempotent apply); stores land at 59.59 MB
(program) / 66.83 MB (graph) — publishable with headroom.

**Rhea receipt** `validation/batch_life_20260917/receipt_rhea_proven_not_applied.json`
(batch_id 4c8b2ed1017d711a, bundle 10e93d13a533): 14,202 records verified,
0 contract failures, count identity closed, NOT applied (store ceiling, see
FORCED DEVIATION above).

1. **Macaca BMR in SI W — SUPPORTED.** Exactly ONE Macaca species of 21 has a
   measured BMR (*Macaca mulatta*; the other 20 are −999 sentinels recorded as
   nodata with explicit unknowns). Its record admitted in W with the 20.1 J/mL
   O₂ calorific equivalent declared as an assumption; class
   `batch.property.pantheria_trait` passed 4,115/4,115 (3,542 adult masses in
   kg + 573 BMRs in W), zero failures.
2. **Names resolve — SUPPORTED.** 21/21 PanTHERIA Macaca binomials resolved
   against the 43-taxon subtree (mulatta → tax_id 9544); the unresolved-name
   quarantine was proven on a synthetic row before the run.
3. **Sentinels are explicit unknowns — SUPPORTED.** 1,874 sentinel adult-mass
   and 4,843 sentinel BMR cells became trait statuses + unknowns, never
   measurements; 0 sentinel-derived values anywhere. Both falsifier layers
   verified: the adapter guard (quarantine before drafting) and the class
   contract's positive `field_range` (flags −5.58 W exactly, unit-tested).
4. **Count identity — SUPPORTED.** PanTHERIA 9,531/0; taxdmp 43/0; Rhea
   14,202 admitted + 47 duplicate-identity events withholding all 116 rows of
   the 47 CHEBI ids that carry competing SMILES (14,318 fetched = 14,202 +
   116, zero silent drops, no greedy pick).

**Measured corrections to the framing (recorded, not papered over):**
- PanTHERIA holds **5,416 data rows** ("5,417" counts the header line); BMR is
  measured for 573 rows, adult mass for 3,542.
- The sentinel renders as **`-999.00`** in this file; detection is numeric
  (`== −999`), so any rendering is covered.
- `rhea-chebi-smiles.tsv` is a **headerless two-column CHEBI→SMILES participant
  map** (14,318 rows; 14,249 unique ids), not a reaction list — reaction
  membership is a later per-format file set, as the connector's known_gaps say.

**Falsifiers proven before the runs**
(`tools/science_funnel/tests/test_batch_life.py`, 16/16): sentinel renderings;
sentinel rows emit no BMR measurement; injected sentinel-derived value refused
by the class contract exactly; unresolved Macaca name quarantines; subtree
re-derivation byte-identical; wiring merged by the auto-load convention.
