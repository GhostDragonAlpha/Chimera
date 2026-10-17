L1 CONFIRMED — all 8 rows match digit-for-digit; 0.8 N residual 7.32231333233635e-07 equals receipt scale_m 1.0 exactly.
L2 CONFIRMED — apex_z strictly decreasing (0.38696→-0.05954); all free_residual_N ≤ 1e-6 (max 7.32e-7); stagnated-with-residual-in-gate per receipt_adapter.py:_case_converged lines 106-116 (stationary OR stagnated with residual ≤ packet 1e-6).
L3 Amendment (piece_record.py amend_domain_measurements lines 419-480) from [0.8] to in-law loads must carry: new valid_loads_N=[0.0,0.4,0.8,1.2,1.6,2.0,2.5,3.0], receipt_name=load_domain_study_20261017.json, archived prior bytes (automatic), domain_amendment_history append, validate() coverage check. Eligible: all 8 studied loads — residual in law (≤1e-6) AND terminal state valid (stagnated/stationary).
L4 FROZEN CRITERIA:
| # | Predicate | Threshold | Evidence Source |
|---|-----------|-----------|-----------------|
| 1 | Objective: set ctl-6 load so apex_z in band | [0.147, 0.197] wu | 1.6 N equilibrium ± 0.025 wu (0.5×min adjacent spacing 0.0503 wu) |
| 2 | Success: terminal apex_z in band AND free_residual_N ≤ 1e-6 | apex_z∈[0.147,0.197] AND residual≤1e-6 | packet 1e-6 law; engine telemetry + CPU re-solve cross-check ≤1e-7 (f32-exact allowance) |
| 3 | Failure: out of band after bounded moves OR load refused by domain | >N moves OR load∉valid_loads_N | piece_record.validate() piece_load_unmeasured |
| 4 | Feedback: /frame screenshot + telemetry numbers | apex_z, load_N, free_residual_N per frame | measured telemetry |
| 5 | Restart: reset bit-exactness | restore initial geometry byte-exact | composed_chain.build_star seeds from record |
| 6 | Replay: re-upload identical hashes | same input hash → same output hash | append-only evidence law |
