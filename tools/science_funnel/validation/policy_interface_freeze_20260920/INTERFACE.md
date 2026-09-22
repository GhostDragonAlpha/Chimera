# THE FROZEN POLICY OBSERVATION INTERFACE (v2, 80 fields)

Frozen by `lane/policy-interface-freeze-20260920` (Agent: ifreeze), preregistered in
`PREREGISTRATION.md` before generation. The machine table is
`observation_interface_v2.json` (sha256 `e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a4f1188b1c0671c`,
68230 bytes); it is GENERATED from the live code
(`tools/science_funnel/typeb_export/interface_freeze.py` + `observation_schema.py`)
and the pinned v2 manifest section
(`tools/science_funnel/validation/obs_split_channels_20260921/obs_section_v2.json`,
sha256 `3de82a1156ac2f39ed04da24c7fd40357642d7bc029e09b509dfc3ea1af63079`).
The freeze-drift unittest regenerates the table and compares BYTES; any schema change
without a version bump fails (prereg falsifier F2).

## THE LAW (what a trained skill #1 will hold everyone to)

1. **Ordering.** Exactly 80 float32 scalars, in `observation_schema.FIELD_NAMES` order
   (the table's `order` list; the JSON `fields` array carries `index` for every name).
   Group order: gait_phase(5), contact_aggregate(4), contact_per_foot(6), contact_force(6),
   body_velocity(5), prev_requested_cmd(8), prev_applied_cmd(8), limiter_saturation(8),
   intervention(5), command_clock(3), sensor_health(2), phase_dynamics(4), pad_split(16).
   Sub-orders: feet `fl,fr,ml,mr,hl,hr`; command vectors leg-major `l,r` x channels
   `phase_off,stride_amp,lift_amp,stiff` (index = leg*4 + channel); pad legs `hl,hr`.

2. **Normalization (the deployed recipe's only arithmetic).**
   `x = clip((raw - mean) / max(std, 1e-8), -8.0, +8.0)`, float32 throughout.
   mean/std per field are the v2 manifest section's measured values (record-set-derived;
   never-available fields carry mean 0 / std 1). The same constants live in every
   manifest's `normalization` block and are pinned by the manifest hash.

3. **Missing values are NEVER invented.** A channel the record does not determine is
   DECLARED UNAVAILABLE: mask 0, value = mean fill (exactly 0.0 in normalized space).
   The availability mask itself is an observed field (`mask_mean`, `mask_frac_avail`,
   pinned available). Availability rules, per field (the table's `availability_rule`):
   - `group_delivery` (56 fields): unavailable iff the group was not delivered this
     tick or the source scalar is missing.
   - `pair_delivery` (8: pad g_heel/g_mp/split per hind leg): additionally require the
     pair ordering `heel_mp`; a `lohi` reconstructed pair leaves them unavailable.
   - `delta_prev` (8: pad dg_*/split_rate/split_abs_rate): additionally require the
     previous delivered sample of their base channel (a delivery gap masks the next delta).
   - `derived_flag` (6: support_ge3_flag, intv one-hots, contact_count_delta):
     unavailable exactly when their base scalar(s) are missing.
   - `self_observing` (2: mask_mean, mask_frac_avail): available whenever the
     projection runs.

4. **Clipping is in normalized space at +/-8.0** (declared in the recipe and mirrored
   in the manifest). Rare-event one-hots fire HARD positive (the recorded refusal tick
   measured x >= 4.0); silence sits at -mean/std < 0 (the P3 harness's measured
   convention).

5. **Versioning.** `OBS_SCHEMA_VERSION = 2` (80 = 64 frozen legacy + 16 pad-split).
   `FIELDS[:64]` is field-for-field the v1 table (1b6d7749, cross-asserted by test);
   a v1 consumer (64-length norm arrays) receives a v1-width projection and a
   v1-width mask, and legacy records replay bitwise-identically (F-CHANNELS-INERT,
   action-stream sha e25406e8...). The table itself is `policy-interface/2.0.0`
   (`interface_freeze.INTERFACE_FREEZE_VERSION`).

6. **Privilege.** No privileged quantity (root pose, anatomy, acceptance-monitor state,
   physics internals — the `PRIVILEGED_SOURCES` set) may ever occupy a slot; the
   manifest validator refuses any `privileged != False` field.

## THE PER-FIELD TABLE (summary; full rows in the JSON)

| idx | group | fields | unit / frame | meaning (short) |
|----|-------|--------|--------------|-----------------|
| 0-3 | gait_phase | gait_phase_{sin,cos}_{left,right} | 1 / gait_clock | per-leg clock phase on the unit circle |
| 4 | gait_phase | gait_phase_frac | 1 / gait_clock | raw cycle fraction 0..1 |
| 5-8 | contact_aggregate | contact_count_norm, support_ge3_flag, unload_class_flag, hind_step_class_flag | 1 / body | contact census + class flags |
| 9-14 | contact_per_foot | foot_contact_{fl,fr,ml,mr,hl,hr} | 1 / body | binary per-foot contact |
| 15-20 | contact_force | foot_force_{fl,fr,ml,mr,hl,hr} | N_bw_frac / body | per-foot force, body-weight fractions |
| 21-23 | body_velocity | com_vel_x_heading, com_vel_y_heading, com_vel_z | m_s / heading,heading,world | CoM velocity |
| 24-25 | body_velocity | yaw_rate, yaw_rate_prev | rad_s / world | yaw rate + held previous sample |
| 26-33 | prev_requested_cmd | prev_req_{l,r}_{phase_off,stride_amp,lift_amp,stiff} | cmd / walk_interface | last requested (pre-limiter) command |
| 34-41 | prev_applied_cmd | prev_app_{l,r}_... | cmd / walk_interface | last applied (post-limiter) command |
| 42-49 | limiter_saturation | lim_sat_{l,r}_... | 1 / walk_interface | per-channel clip indicator |
| 50-53 | intervention | intv_none, intv_refusal, intv_ledger_breach, intv_falsifier_red | 1 / controller | intervention one-hot |
| 54 | intervention | ticks_since_intv | tick_norm / controller | ticks since last intervention (clamp 3000) |
| 55-56 | command_clock | hold_tick_frac, policy_gate | 1 / controller | position in the 15-tick hold; the 20 Hz gate |
| 57 | command_clock | freq_scale | 1 / walk_interface | gait frequency scale |
| 58-59 | sensor_health | mask_mean, mask_frac_avail | 1 / observation | the mask observes itself |
| 60-63 | phase_dynamics | phase_rate_norm, contact_count_delta, contact_count_prev, time_since_reset | mixed | first differences of clock and census |
| 64-79 | pad_split | pad_{g_heel,g_mp,dg_heel,dg_mp,split,split_rate,split_abs,split_abs_rate}_{hl,hr} | m, m_per_tick / world | the wave-46/47 rotational pad channels (see JSON rows for the ordering/mask law) |

## REGENERATION (the only legal way to change this file)

```
python tools/science_funnel/typeb_export/interface_freeze.py \
    tools/science_funnel/validation/policy_interface_freeze_20260920/observation_interface_v2.json
```

Deterministic: identical inputs produce byte-identical output (measured twice this
lane). A different byte stream means the SCHEMA changed: bump `OBS_SCHEMA_VERSION` /
`INTERFACE_FREEZE_VERSION` together, regenerate, and re-review — the F2 unittest pins
the committed bytes.
