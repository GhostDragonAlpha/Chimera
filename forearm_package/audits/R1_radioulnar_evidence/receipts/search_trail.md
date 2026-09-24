# R1 — SEARCH TRAIL (all queries, including failures; the trail is part of the result)

Legend: [OK] result obtained · [RL] search backend rate-limited (HTTP 429), retried · [0] zero hits · [PAYWALL] located, full text not open.

## Phase 1 — species/provenance
1. [OK] WebSearch "FreeMusco chimanoid musculoskeletal model" → FreeMusco = Kim & Lee 2025 (Hanyang Univ.); chimanoid = a character in their demos.
2. [RL×4 then OK] WebSearch "FreeMusco arxiv chimanoid/chimpanzoid…" → arXiv:2511.14205 (SIGGRAPH Asia 2025).
3. [OK] WebFetch FreeMusco GitHub README → no model files on front page; MuJoCo 3.2.3.
4. [OK] WebFetch api.github.com git tree (recursive) → `Data/Muscle/Fullbody/chimanoid.xml` + `fullbody.xml` + `Animal/ostrich/*`.
5. [OK] WebFetch raw.githubusercontent chimanoid.xml → ulna/radius/hand_r pos strings byte-identical to baseline; model="fullbody"; mass 0.729; no species names anywhere.
6. [OK] WebFetch arXiv abs page → Chimanoid in abstract (quadrupedal gaits).
7. [OK] WebFetch arXiv HTML full text → the four verbatim Chimanoid quotes (fictional; Humanoid modified ×1.2 arms / ×0.7 legs; "chimpanzee-like proportions").

## Phase 2 — primary anatomy, applicable lane (human = base anatomy)
8. [RL×4 then partial] WebSearch "elbow flexion extension axis radial head capitellum trochlea kinematics" → Morrey & Chao 1976 named; no numbers on the open page. Followed via eutils below.
9. [PARTIAL] WebFetch pubmed search London 1981 → citation + truncated abstract (8 elbows, true lateral roentgenograms). PubMed cookie-wall blocks abstract pages → switched to NCBI eutils.
10. [OK] eutils efetch PMID 7217119 → London 1981 abstract content: single flexion axis through trochlear-sulcus and capitellar arc centers.
11. [OK] eutils esearch "elbow flexion axis radial head center" → 6 PMIDs.
12. [OK] eutils efetch all 6 → **two decisive hits**: PMID 19102564 (Brownhill 2009, n=12 cadavers: sigmoid-notch ridge + RADIAL HEAD define the axis best, p<0.05) and PMID 8118987 (Hollister 1994: forearm rotation axis runs FROM THE CENTER OF THE RADIAL HEAD to the distal ulna). Also screened: capitellar OAT arthroscopy (2015), OA impingement 3D modeling (2013), ulnar flexion-axis definition (2009 — the hit), missed Monteggia (2004), radiohumeral floating-axis translations (2003), interosseous membrane (1994 — the hit).
13. [OK] eutils efetch 19102564 alone → abstract carries n=12/5-techniques/p<0.05; per-technique mm errors are full-text only (recorded as uncertainty).
14. [OK] eutils esummary 19102564, 8118987, 7217119 → exact citations (authors/journal/year/volume/pages/DOI).

## Phase 3 — primary anatomy, supporting quantity (biceps tuberosity position)
15. [OK] eutils esearch "radial tuberosity distance elbow measurement anatomic" → 38 hits, 15 screened by esummary. Best candidates measure interosseous space/nerve safe zones (e.g., Clin Anat 2020 radioulnar distance at the tuberosity) — **no primary tuberosity-to-elbow-joint number located** ⇒ the model's 8.02% tuberosity site is used only qualitatively (proximal-forearm band), never as a cited number.

## Phase 4 — context taxa (Pan name-lane; Macaca campaign-target lane)
16. [0] eutils esearch "Macaca radius ulna length forelimb skeletal" → zero hits.
17. [RL×5 then 0-results] WebSearch "macaque rhesus radius ulna osteometric length forearm primary study" → backend rate-limited, then no direct source.
18. [OK] eutils esearch "rhesus macaque elbow joint anatomy forelimb" → 11 PMIDs; efetch all 11: 2 primary morphometry series (Cheng & Scott 2000; Graham & Scott 2003) + 9 neurophysiology papers. **No radial-head position, no forearm-proportion table in the abstracts** ⇒ Macaca lane: primary morphometry EXISTS but measures different quantities ⇒ INAPPLICABLE (recorded, not forced). (van Wagenen & Asling rhesus radiographic series not locatable via eutils by title terms; not obtained.)
19. [TIMEOUT then OK] eutils esearch "anthropoid elbow joint radial head morphology" (Rose 1988 lane) → service timeouts; located only via Phase-1 knowledge; paywalled, no number extracted ⇒ recorded INAPPLICABLE rather than cited as a "similar percentage".

## Phase 5 — campaign-side verification (local)
20. [OK] baseline reads: XML L593/608/629 (verbatim pos), DERIVATION.md §1–§2, MANIFEST.json, session_reports 01–05 (species mentions), audits/C1_ulna_evidence/report.md, audits/C3_independent_challenge/report.md.
21. [OK] python 3.14 exact-float arithmetic → receipts/arithmetic.txt (all campaign numbers reproduced; chain-sum 315.104 mm — the brief's "315.14" is a transcription slip for C1's 0.315104).
22. [OK] integrity: `git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot` → EMPTY (HEAD 5db981cb at receipt time).

## Explicit negative result
**No primary source located — in any taxon — that places the radial head (or any proximal radius landmark) 4–12 % of forearm length DISTAL to the humeroulnar elbow joint.** The three applicable primary sources place the radial head center ON the elbow axes (axial fraction ≈ 0 %). The falsifier band was tested against this null and the positive evidence alike.
