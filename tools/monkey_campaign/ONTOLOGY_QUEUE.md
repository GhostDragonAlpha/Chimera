# Ontology-derived slot refill

The sealed monkey_completion_map.json and its pinned ontology contract define
the backlog. ONT-<task ID> cards are generated deterministically, in dependency
layers. Only the 76 selected tasks participate. The seven conditional tasks require
a lead scope amendment. Existing active cards, hashes, attempts, and PRs survive.

Refill runs in the merge transaction. A free slot keeps its branch-N identity and
receives eligible work. Independent upstream tasks can run in parallel. A task's
dependencies must have qualified winners; a merged diagnostic does not qualify
its parent task. Existing active diagnostics/scaffolds for a task finish before its
qualification card is commissioned. Each generated card starts by reconciling and
reusing existing evidence, then implementing only missing work.

Ontology connection IDs, containment, calculation clauses, verification profiles,
camera fields and checkpoint IDs travel inside each card. Task depends_on is the
approved execution graph: containment or a connection alone does not invent an
ordering edge. Integration checkpoints collect their contributors and must never
become prerequisites of those same contributors. Changing the graph requires a
lead scope amendment; workers cannot alter it to unlock themselves.

## Qualification and acceptance

The existing review CLI takes an additional ontology_qualification object for an
ACCEPTED review of an ONT card:

```json
{
  "task_id": "W01",
  "scope_sha256": "<sealed scope digest>",
  "head_sha": "<reviewed PR head>",
  "criteria_sha256": "<card criteria digest>",
  "done_when_verified": true,
  "profile_verified": true,
  "evidence": {
    "source": {"reference": "<receipt>", "raw_sha256": "<64 hex>"},
    "numerical": {"reference": "<receipt>", "raw_sha256": "<64 hex>"},
    "independent_review": {"reference": "<receipt>", "raw_sha256": "<64 hex>"}
  }
}
```

Visible profiles also require visual and camera evidence entries; motion and final
playthrough profiles require runtime evidence. The lead must read and verify these
artifacts, including their raw hashes, full task acceptance and profile applicability.
Structural receipt validation is not automatic verification of physical truth.
Additional runtime requirements in done_when still apply even for an offline profile.
Camera receipts include all profile camera fields, tags, diagnostic visibility,
angle/distance and the clean view where specified. Passing a static proxy does not
qualify native behavior. A changed PR head invalidates the receipt and review.

After GitHub merge verification, the receipt is retained with the winner and unlocks
downstream cards atomically. Scope drift refuses refill rather than silently
rewriting active criteria. No automatic model starts, GPU leases or lead polling
are introduced. When all eligible slots await review, workers follow the existing
independent-review loop; missing upstream evidence is a named blocker, not fake work.

## Enforced visual-file gate (astra-0020)

For visual tasks, evidence.camera.reference must be an absolute local path to the
actual chimera.visual_capture_manifest.v1 JSON (maximum 2 MiB); evidence.visual.reference
must locate the actual captured media (maximum 4 GiB). Both raw SHA-256 values are
recomputed at review and merge. Remote artifacts must first be made available locally.
The qualification receipt also supplies capture_context: task_id, subject_sha256,
run_id, capture_sha256 and tick_interval, pinned by the independent reviewer to the
actual run. The existing visual_capture validator checks the exact task profile,
camera distance/orientation/projection, views, clean/diagnostic pairs and tag metadata.
Wrong hashes or missing/invalid camera metadata refuse acceptance. The lead still
must inspect the media and authenticate subject/run provenance: structural validation
does not decode pixels, prove physics, or authenticate a worker's claims.
