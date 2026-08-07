# theStandingHuman — falsifier battery (Lane D draft, operator review)

## 1. STATEMENT
The 206-bone skeleton stands because its printed geometry routes the whole body weight to the ground entirely through bones in compression and ropes in tension. Standing is a property of the frame, not of any muscle.

## 2. PREDICTION (8000-tick main print)
During the verdict window every bone stays one cluster and inside its derived positional band; every capture gap stays inside the derived band; the COM of all non-ground grains projects inside the support polygon formed by the foot bones in contact with the plate; every rope that the static topology requires is taut, every other rope is slack or crumpled; the head height stays within the derived standing band.

## 3. FALSIFIERS (metered, bars derived)

(a) **INTEGRITY — per bone.** Cluster each bone body independently using its grain_id label. FAIL if any bone splits into >=2 clusters at any sample, or if its COM drifts outside the theBone preload band (+/- d_eq) during the verdict window. Localisation: the body label plus the centroid drift of the detached component names which end sheared.

(b) **CAPTURE — per joint.** For each cup/saddle pair, measure parent–child separation projected on the derived joint normal. Band = [S_WALL, d_eq], where d_eq is the bondless cushion equilibrium from theBone force zero-crossing and S_WALL is the theJoint v2 seated-recovery wall. Any sample outside the band during the verdict window fails.

(c) **FRAME — COM over support polygon.** Build the support polygon from the convex hull of world-contact grains belonging to the foot bones (calcaneus, talus, metatarsals) at settle. Project the COM of all non-ground grains onto the ground plane. Falsified if the projection leaves the polygon during the verdict window.

(d) **ROPE — loaded set taut-or-slack, never compressed.** Before the run, derive the loaded rope set from the COM line through the print topology: a rope is loaded iff it is required to keep adjacent bones in compression under gravity. Loaded ropes must show tensile force > F_min = 0.01*K_BOND*r_bond and zero compression samples; all other ropes must be slack (force <= F_min or kink angle > 90 deg). Any rope sample with negative axial force fails.

(e) **STAND — head height.** Let H_head be the print height of the head COM above the support polygon. Band delta_stand = H_head*tan(2 deg) + d_eq, where 2 deg is the spine v2 frame bar and d_eq is the cushion compression allowance. Falsified if head z leaves [print_z +/- delta_stand] during the verdict window.

(f) **CONTROL — cut the ropes.** After the settle period, set all rope tensions to zero. **FALL** is defined as the COM dropping more than delta_fail = L_leg*sin(12 deg) within 600 ticks, where L_leg is the derived femur+tibia effective length and 12 deg is the sacrum-tilt failure angle from spine v1/v2. The frame must fall. Two-sided meaning: a frame that stands without ropes refutes the leg v3 rope law; a frame that falls with intact ropes refutes the frame constitution.

## 4. THE LURCH PROTOCOL
Leg v1–v3 and spine v1/v2 each show a cold-print relaxation spike landing near tick 400 and decaying by tick ~1000. All meters run in listen-only mode from t=0 to t=1200 (= 1.2x the measured 1000-tick decay bound). The verdict window is t=1200–8000 only.

## 5. FAILURE LOCALIZATION

| falsifier fail | membrane law it re-tests |
|---|---|
| INTEGRITY (bone split / drift) | spine v2 constitution: bone is compression-only, no cantilever |
| CAPTURE (joint gap out of band) | socket v1 law: capture must wrap the bone end |
| ROPE (compression or wrong loaded set) | leg v2/v3 law: tendon is tension-only; loaded set comes from statics |
| FRAME / STAND (COM/head leave bounds) | frame constitution: geometry routes gravity |
| CONTROL: stands when ropes are cut | leg v3 rope law refuted |
| CONTROL: falls while ropes are intact | frame constitution refuted |

## 6. WHAT THIS BATTERY DOES NOT DECIDE
Muscle routing, antagonist timing, and gait. Those are theWalkingHuman membranes; this battery only asks whether the standing frame is stable under gravity.

## Three hardest metering problems at 206-bone scale

1. **Per-bone cluster identity.** With 206 bodies, a global cluster test would merge adjacent bones through their contacts. The battery keeps each bone a separate labeled body and clusters inside that label only; detachment localises by body ID and component centroid.

2. **Capture-gap measurement in a crowded chain.** Many contact points are not joints. The battery tags each cup/saddle surface pair and projects separation along the derived joint normal, so only the capture degree of freedom is metered.

3. **Statically indeterminate rope loading.** Many ropes could plausibly carry load; choosing a threshold after the run would be tuning. The battery derives the loaded set from the COM line and print topology before the run, then checks membership (taut vs slack) against that set.
