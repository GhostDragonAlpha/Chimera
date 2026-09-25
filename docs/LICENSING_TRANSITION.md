# Public source and prospective licensing transition

The operator directed that the ontology/workflow change be the final open-source
PR before changing terms, and confirmed control of all first-party contributions.
The repository remains public. The new default offer is source-visible and
restricted, as stated in [LICENSE](../LICENSE); it is not an open-source license.

The final AGPL workflow/ontology contribution is
[PR #112](https://github.com/GhostDragonAlpha/Chimera/pull/112), merged at
`c525b82c7c3ce0128565424764293a3c85811ab3`. Its reviewed head was
`12f9928cc1d0f16261cb742b7e9b6654f7f8b2d6`. The commit introducing this transition
is subsequent to that cutoff; no history is rewritten. This records a licensing
boundary, not engine completion, gameplay acceptance or a release announcement.
PR #112 targets the active `astra/gait-capture` development branch. The public
default branch is `master`; its pre-transition head is
`33e7a444fe7b4c35aa99afe7ef898046877025b4`. This transition updates the public default branch only. The development PR
was not merged; historical development branches retain their existing license
notices. No unrelated engine/graph lineage is merged by this change.
Historical branches and releases retain their original notices and grants.

Existing AGPL grants survive this change, including for unchanged material that
continues to appear in the public tree. Previously distributed revisions can
still be used under their existing terms. The original license text is preserved
byte-for-byte at [LICENSES/AGPL-3.0-historical.txt](../LICENSES/AGPL-3.0-historical.txt).
AGPL section 2 describes the continuing grant subject to its conditions.
[GNU AGPLv3](https://www.gnu.org/licenses/agpl-3.0.html#section2)

GitHub's public-repository view/fork permissions remain applicable. Keeping source
public does not turn the new restricted offer into an open-source license.
[GitHub Terms, section D](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service#d-user-generated-content)

Third-party licenses and embedded notices remain unchanged. Read
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md), each dependency's license and
the [asset ledger](https://github.com/GhostDragonAlpha/Chimera/blob/c525b82c7c3ce0128565424764293a3c85811ab3/Chimera/docs/ASSET_LICENSES.md). Neither this record nor the
operator's first-party ownership statement claims ownership of third-party work.
Task S01 still owns the complete distribution/provenance audit before packaging.

Private game assets, stories and service access are separate products. This change
does not publish them, withdraw rights already granted for public assets, or claim
that browser delivery prevents extraction or cheating. The future verification
architecture remains a proposal in
[VERIFIABLE_SIMULATION.md](https://github.com/GhostDragonAlpha/Chimera/blob/c525b82c7c3ce0128565424764293a3c85811ab3/docs/architecture/VERIFIABLE_SIMULATION.md).

Subsequent owner-authorized development may proceed under the new default offer.
An outside contribution is not an automatic copyright assignment or relicensing
permission; record explicit rights before incorporating it into that offer.
