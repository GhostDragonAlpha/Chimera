# FINDINGS -- docs-evidence-link-audit-01 (dangling references)

Every DANGLING reference from the fleet docs set, verbatim, for
lead disposition. `beyond-id-class` = yes for references whose
class is not the known controller-record-id class
(PATH/MDLINK/PR). Counts: resolved=459 dangling=85
controller-labeled=178 ignored=970.

| # | class | source | line | token | reason | beyond-id-class |
|---|-------|--------|------|-------|--------|-----------------|
| 1 | PATH | docs/THE_AGENT_FLEET.md | 38 | `E:\PythonChimera` | outside-repo:unlabeled | yes |
| 2 | TASKID | docs/THE_AGENT_FLEET.md | 697 | `fleet-run-queue-01` | unlabeled-controller-id | no |
| 3 | TASKID | docs/THE_AGENT_FLEET.md | 697 | `fleet-orient-continuation-01` | unlabeled-controller-id | no |
| 4 | TASKID | docs/THE_AGENT_FLEET.md | 697 | `engine-vulkan-cleanup-01` | unlabeled-controller-id | no |
| 5 | TASKID | docs/THE_AGENT_FLEET.md | 698 | `fleet-controller-upgrade-01` | unlabeled-controller-id | no |
| 6 | PATH | docs/THE_MASTER_LIST.md | 2212 | `ChimeraEngine/engine_state.json` | path-not-in-tree | yes |
| 7 | PATH | docs/THE_MASTER_LIST.md | 2407 | `.git/config` | path-not-in-tree | yes |
| 8 | PR | docs/THE_MASTER_LIST.md | 2449 | `PR19` | pr-not-in-history | yes |
| 9 | TASKID | docs/THE_MASTER_LIST.md | 2461 | `dyad-resident-identity-01` | unlabeled-controller-id | no |
| 10 | TASKID | docs/THE_MASTER_LIST.md | 2579 | `fleet-head-reconcile-01` | unlabeled-controller-id | no |
| 11 | TASKID | docs/THE_MASTER_LIST.md | 2580 | `studio-grid-depth-01` | unlabeled-controller-id | no |
| 12 | TASKID | docs/THE_MASTER_LIST.md | 2580 | `engine-vulkan-cleanup-01` | unlabeled-controller-id | no |
| 13 | TASKID | docs/THE_MASTER_LIST.md | 2581 | `engine-feature-resource-lifetime-01` | unlabeled-controller-id | no |
| 14 | TASKID | docs/THE_MASTER_LIST.md | 2581 | `dyad-resident-identity-01` | unlabeled-controller-id | no |
| 15 | TASKID | docs/THE_MASTER_LIST.md | 2582 | `window-capture-ownership-01` | unlabeled-controller-id | no |
| 16 | TASKID | docs/THE_MASTER_LIST.md | 2600 | `fleet-head-reconcile-tool-01` | unlabeled-controller-id | no |
| 17 | TASKID | docs/THE_MASTER_LIST.md | 2647 | `fleet-review-followups-02` | unlabeled-controller-id | no |
| 18 | TASKID | docs/THE_MASTER_LIST.md | 2670 | `fleet-orient-continuation-01` | unlabeled-controller-id | no |
| 19 | PATH | docs/evidence/agent_fleet/CATALOGUE_REPIN/PREREGISTRATION.md | 42 | `E:\ChimeraWork\slot-03` | outside-repo:unlabeled | yes |
| 20 | PATH | docs/evidence/agent_fleet/CATALOGUE_REPIN/PREREGISTRATION.md | 55 | `evidence/MEASUREMENT.json` | path-not-in-tree | yes |
| 21 | TASKID | docs/evidence/agent_fleet/CATALOGUE_REPIN/RESULT.md | 36 | `demo-studio-state-01` | unlabeled-controller-id | no |
| 22 | TASKID | docs/evidence/agent_fleet/CATALOGUE_REPIN_02/PREREGISTRATION.md | 12 | `fleet-catalogue-repin-01` | unlabeled-controller-id | no |
| 23 | TASKID | docs/evidence/agent_fleet/CATALOGUE_REPIN_02/PREREGISTRATION.md | 15 | `window-capture-02` | unlabeled-controller-id | no |
| 24 | PATH | docs/evidence/agent_fleet/CATALOGUE_REPIN_02/PREREGISTRATION.md | 48 | `E:\ChimeraWork\slot-04` | outside-repo:unlabeled | yes |
| 25 | TASKID | docs/evidence/agent_fleet/CATALOGUE_REPIN_02/RESULT.md | 13 | `window-capture-02` | unlabeled-controller-id | no |
| 26 | TASKID | docs/evidence/agent_fleet/CLIENT_INSTANCE/PREREGISTRATION.md | 1 | `fleet-client-instance-01` | unlabeled-controller-id | no |
| 27 | TASKID | docs/evidence/agent_fleet/CLIENT_INSTANCE/RESULT.md | 1 | `fleet-client-instance-01` | unlabeled-controller-id | no |
| 28 | PATH | docs/evidence/agent_fleet/CONTROLLER_TRANSITION/RESULT.md | 67 | `SLOT_BINDING/RESULT.md` | path-not-in-tree | yes |
| 29 | PATH | docs/evidence/agent_fleet/CONTROLLER_TRANSITION/RESULT.md | 90 | `FLEET_OPERATIONS_RECORD/RECORD.md` | path-not-in-tree | yes |
| 30 | TASKID | docs/evidence/agent_fleet/DYAD_RETAINED_REVIEWS/PREREGISTRATION.md | 1 | `dyad-retained-reviews-01` | unlabeled-controller-id | no |
| 31 | TASKID | docs/evidence/agent_fleet/DYAD_RETAINED_REVIEWS/PREREGISTRATION.md | 3 | `subagent-worker-06` | unlabeled-controller-id | no |
| 32 | TASKID | docs/evidence/agent_fleet/DYAD_RETAINED_REVIEWS/PREREGISTRATION.md | 19 | `subagent-worker-06` | unlabeled-controller-id | no |
| 33 | TASKID | docs/evidence/agent_fleet/DYAD_RETAINED_REVIEWS/PREREGISTRATION.md | 27 | `GLM-DYAD-02` | unlabeled-controller-id | no |
| 34 | TASKID | docs/evidence/agent_fleet/DYAD_RETAINED_REVIEWS/RESULT.md | 1 | `dyad-retained-reviews-01` | unlabeled-controller-id | no |
| 35 | TASKID | docs/evidence/agent_fleet/DYAD_RETAINED_REVIEWS/RESULT.md | 3 | `subagent-worker-06` | unlabeled-controller-id | no |
| 36 | TASKID | docs/evidence/agent_fleet/DYAD_SUBAGENT_TEMPLATE/PREREGISTRATION.md | 1 | `dyad-subagent-template-01` | unlabeled-controller-id | no |
| 37 | TASKID | docs/evidence/agent_fleet/DYAD_SUBAGENT_TEMPLATE/RESULT.md | 1 | `dyad-subagent-template-01` | unlabeled-controller-id | no |
| 38 | TASKID | docs/evidence/agent_fleet/EVIDENCE_HYGIENE/PREREGISTRATION.txt | 1 | `fleet-evidence-hygiene-01` | unlabeled-controller-id | no |
| 39 | TASKID | docs/evidence/agent_fleet/EVIDENCE_HYGIENE/PREREGISTRATION.txt | 4 | `subagent-worker-05` | unlabeled-controller-id | no |
| 40 | TASKID | docs/evidence/agent_fleet/EVIDENCE_HYGIENE/PREREGISTRATION.txt | 5 | `subagent-worker-05` | unlabeled-controller-id | no |
| 41 | PATH | docs/evidence/agent_fleet/EVIDENCE_HYGIENE/PREREGISTRATION.txt | 19 | `E:\PythonChimera\.gitignore` | outside-repo:unlabeled | yes |
| 42 | PATH | docs/evidence/agent_fleet/EVIDENCE_HYGIENE/PREREGISTRATION.txt | 24 | `.git/hooks/pre-commit` | path-not-in-tree | yes |
| 43 | TASKID | docs/evidence/agent_fleet/EVIDENCE_HYGIENE/PREREGISTRATION.txt | 113 | `subagent-worker-05` | unlabeled-controller-id | no |
| 44 | TASKID | docs/evidence/agent_fleet/EVIDENCE_HYGIENE/RESULT.txt | 1 | `fleet-evidence-hygiene-01` | unlabeled-controller-id | no |
| 45 | TASKID | docs/evidence/agent_fleet/EVIDENCE_HYGIENE/RESULT.txt | 4 | `subagent-worker-05` | unlabeled-controller-id | no |
| 46 | PATH | docs/evidence/agent_fleet/EVIDENCE_HYGIENE/RESULT.txt | 12 | `.git/hooks` | path-not-in-tree | yes |
| 47 | PATH | docs/evidence/agent_fleet/EVIDENCE_HYGIENE/RESULT.txt | 69 | `python.exe` | path-not-in-tree | yes |
| 48 | PATH | docs/evidence/agent_fleet/EVIDENCE_HYGIENE/RESULT.txt | 71 | `state.sqlite` | path-not-in-tree | yes |
| 49 | TASKID | docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/PREREGISTRATION.md | 1 | `docs-evidence-link-audit-01` | unlabeled-controller-id | no |
| 50 | TASKID | docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/PREREGISTRATION.md | 3 | `subagent-worker-09` | unlabeled-controller-id | no |
| 51 | TASKID | docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/PREREGISTRATION.md | 4 | `subagent-worker-09` | unlabeled-controller-id | no |
| 52 | TASKID | docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/PREREGISTRATION.md | 71 | `SLOT02-PARALLEL-01` | unlabeled-controller-id | no |
| 53 | PATH | docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/PREREGISTRATION.md | 89 | `E:\ChimeraWork` | outside-repo:unlabeled | yes |
| 54 | TASKID | docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/PREREGISTRATION.md | 146 | `subagent-worker-09` | unlabeled-controller-id | no |
| 55 | TASKID | docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/RESULT.md | 1 | `docs-evidence-link-audit-01` | unlabeled-controller-id | no |
| 56 | TASKID | docs/evidence/agent_fleet/HEAD_RECONCILE/PREREGISTRATION-20260911-lead-fresh.md | 1 | `fleet-head-reconcile-01` | unlabeled-controller-id | no |
| 57 | TASKID | docs/evidence/agent_fleet/HEAD_RECONCILE/PREREGISTRATION.md | 1 | `fleet-head-reconcile-tool-01` | unlabeled-controller-id | no |
| 58 | TASKID | docs/evidence/agent_fleet/HEAD_RECONCILE/RESULT-20260911.md | 1 | `fleet-head-reconcile-01` | unlabeled-controller-id | no |
| 59 | TASKID | docs/evidence/agent_fleet/HEAD_RECONCILE/RESULT-20260911.md | 20 | `run-queue-01` | unlabeled-controller-id | no |
| 60 | TASKID | docs/evidence/agent_fleet/HEAD_RECONCILE/RESULT-20260911.md | 20 | `window-capture-01` | unlabeled-controller-id | no |
| 61 | TASKID | docs/evidence/agent_fleet/HIERARCHY_CONTINUATION/PREREGISTRATION-20260911-fresh.md | 1 | `fleet-orient-continuation-02` | unlabeled-controller-id | no |
| 62 | TASKID | docs/evidence/agent_fleet/HIERARCHY_CONTINUATION/RESULT-20260911-fresh.md | 1 | `fleet-orient-continuation-02` | unlabeled-controller-id | no |
| 63 | TASKID | docs/evidence/agent_fleet/HIERARCHY_CONTINUATION/RESULT-20260911-fresh.md | 66 | `subagent-worker-04` | unlabeled-controller-id | no |
| 64 | TASKID | docs/evidence/agent_fleet/MAINTENANCE_AMENDMENT_01/PREREGISTRATION.md | 1 | `fleet-maintenance-amendment-01` | unlabeled-controller-id | no |
| 65 | TASKID | docs/evidence/agent_fleet/MAINTENANCE_AMENDMENT_01/RESULT.md | 1 | `fleet-maintenance-amendment-01` | unlabeled-controller-id | no |
| 66 | TASKID | docs/evidence/agent_fleet/REVIEW_FOLLOWUPS_02/PREREGISTRATION.md | 1 | `fleet-review-followups-02` | unlabeled-controller-id | no |
| 67 | TASKID | docs/evidence/agent_fleet/REVIEW_FOLLOWUPS_02/PREREGISTRATION.md | 59 | `window-capture-ownership-02` | unlabeled-controller-id | no |
| 68 | TASKID | docs/evidence/agent_fleet/REVIEW_FOLLOWUPS_02/PREREGISTRATION.md | 72 | `subagent-worker-02` | unlabeled-controller-id | no |
| 69 | PATH | docs/evidence/agent_fleet/REVIEW_FOLLOWUPS_02/RESULT.md | 15 | `TRANSPORT_BODY_LIMIT/MEASUREMENT.json` | path-not-in-tree | yes |
| 70 | PATH | docs/evidence/agent_fleet/SLOT_BINDING/PREREGISTRATION.md | 8 | `state.sqlite` | path-not-in-tree | yes |
| 71 | TASKID | docs/evidence/agent_fleet/TASK_ABANDON/PREREGISTRATION.md | 1 | `fleet-task-abandon-01` | unlabeled-controller-id | no |
| 72 | TASKID | docs/evidence/agent_fleet/TASK_ABANDON/PREREGISTRATION.md | 137 | `fleet-orient-continuation-01` | unlabeled-controller-id | no |
| 73 | TASKID | docs/evidence/agent_fleet/TASK_ABANDON/PREREGISTRATION.md | 137 | `engine-vulkan-cleanup-01` | unlabeled-controller-id | no |
| 74 | TASKID | docs/evidence/agent_fleet/TASK_ABANDON/PREREGISTRATION.md | 138 | `fleet-controller-upgrade-01` | unlabeled-controller-id | no |
| 75 | TASKID | docs/evidence/agent_fleet/TASK_ABANDON/RESULT.md | 1 | `fleet-task-abandon-01` | unlabeled-controller-id | no |
| 76 | TASKID | docs/evidence/agent_fleet/TASK_ABANDON/RESULT.md | 106 | `engine-vulkan-cleanup-01` | unlabeled-controller-id | no |
| 77 | TASKID | docs/evidence/agent_fleet/TASK_ABANDON/RESULT.md | 106 | `window-capture-ownership-01` | unlabeled-controller-id | no |
| 78 | TASKID | docs/evidence/agent_fleet/TASK_ABANDON/RESULT.md | 107 | `fleet-controller-upgrade-01` | unlabeled-controller-id | no |
| 79 | TASKID | docs/evidence/agent_fleet/TRANSPORT_BODY_LIMIT/PREREGISTRATION.md | 1 | `fleet-transport-body-limit-01` | unlabeled-controller-id | no |
| 80 | TASKID | docs/evidence/agent_fleet/TRANSPORT_BODY_LIMIT/RESULT.md | 1 | `fleet-transport-body-limit-01` | unlabeled-controller-id | no |
| 81 | TASKID | docs/evidence/agent_fleet/TRANSPORT_BODY_LIMIT/RESULT.md | 49 | `fleet-review-followups-02` | unlabeled-controller-id | no |
| 82 | TASKID | docs/evidence/agent_fleet/WINDOW_CAPTURE/PREREGISTRATION.md | 1 | `window-capture-ownership-02` | unlabeled-controller-id | no |
| 83 | TASKID | docs/evidence/agent_fleet/WINDOW_CAPTURE/PREREGISTRATION.md | 8 | `dyad-resident-identity-01` | unlabeled-controller-id | no |
| 84 | TASKID | docs/evidence/agent_fleet/WINDOW_CAPTURE/RESULT.md | 1 | `window-capture-ownership-02` | unlabeled-controller-id | no |
| 85 | TASKID | docs/evidence/agent_fleet/WINDOW_CAPTURE/RESULT.md | 12 | `window-capture-ownership-01` | unlabeled-controller-id | no |

