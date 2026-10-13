# B6 — working processes on the resident runtime

GAME_PLAN_ACTION_RPG.md §13, B6 gate row: *"add working processes"* —
evidence column: *"Qualify each needed channel separately: chamber
pressure/flux, a valve, finite actuator, sensor, heat transfer or growth"*;
acceptance: *"Paired exchanges conserve material inventories and close the
energy balance including storage, supplied work, heat and boundary flux;
closing or severing a path removes only its contribution."* Gallery item 9
adds the transactional half: *"Open one of two chambers, once transport
exists. Only connected inventories exchange; a patch consumes resources and
does not reset pressure/history for free."*

All of it runs on the **same resident scene, clock and lock lane** as
B2–B5 (`B2Scene`, fixed 1/4000 s substep, `b2_mtx_`), qualified by
`tools/construction_packet/test_b6_processes.py` (7/7, run twice
consecutively green, port 8794) against the Release build. No genre
physics: the process layer is one pressure law plus paired exchange rules,
and the engine's own ledger proves the bookkeeping.

## The law (b2_scene.hpp, stated once, enforced everywhere)

* **Chamber** — inventory `q` (m³, signed), rest volume `V0 > 0`, bulk
  modulus `κ > 0`:
  `P = κ·(q − V)/V0`, stored pressure energy `U = κ·(q − V)²/(2·V0)`.
  This is the membrane's accepted linear-compressibility law
  (`membrane_tick.cpp:752`, `c.p = (c.v0 − v)/(κ·v0)`) generalised from
  volume-vs-rest to inventory-vs-volume: the same quadratic a spring
  stores, which is what makes every exchange close *exactly*.
* **Valve** `{a, b, g}` — `J = g·(P_a − P_b)` m³/s applied to **both**
  sides within the same substep, so inventory is conserved by
  construction (`b` is a chamber or `"env"` with `P_env = 0`).
  Chamber↔chamber: the pair's ΔU is negative under the admission
  stability cap and is booked as dissipation ≥ 0. Chamber↔env: −ΔU is
  energy carried across the boundary, exact by the quadratic identity
  `ΔU = (P_old + P_new)/2 · ΔX`.
* **Heat link** `{a, b, k}` — `dE = k·(T_a − T_b)·h` moved in an exact
  pair (`T_a −= dE/C_a`, `T_b += dE/C_b`); thermal energy is conserved to
  floating point by construction.
* **Piston** `{chamber, part, n, area, stroke, f_max}` — finite
  actuator: `F_raw = P·area` along a world axis applied at the part's COM
  (the chamber's reaction goes to the world: the chamber is built into
  the lair ground, like the ground rung). Beyond `stroke` the ram is
  **disengaged** — zero force *and* the volume coupling is clamped, so a
  coasting ram can neither suck nor vacuum-pump the chamber. Within
  stroke, `f_max` caps the push; the withheld work is booked as relief
  dissipation. Thermodynamic work is measured as `W = −ΔU = P̄·ΔV`, exact.
* **Ledger** — every mutation's energy change is measured before/after
  that single mutation, so the sequential contributions telescope to the
  total ΔU and the per-substep residual
  `ΔU_press + ΔU_th + W + diss + boundary` is pure fp noise. The
  telemetry field `max_residual_energy_J` is the implementation-vs-law
  proof (the tendon ledger's `|drain − (work + heat + dElastic)| ≤ 1e-6 J`
  precedent, tightened to fp).
* **Stability at admission** (fixed h = 1/4000 s): a valve needs
  `g·h·(κ_a/V0_a + κ_b/V0_b) < 0.5`, a heat link `k·h·(1/C_a + 1/C_b) <
  0.5` — the explicit update must not outrun the chamber it feeds.
* **Sensor** — `GET /tick_b2_process` (`chimera.b2_process.v1`) is
  read-only: `state_hash` is invariant across reads.
* **Transactions** — every control validates fully before mutating (the
  B4 law); refusals name themselves and leave the hash untouched.
  `save/restore` carries the full plant (chambers, valves, heat, pistons,
  ledger) with the same validation, so a restored scene is bit-identical.

## Channel-by-channel qualification (measured)

| gate channel | test | measured |
|---|---|---|
| chamber pressure/flux | `test_chamber_pressure_law_and_energy` | P = −80 kPa / +10 kPa / 0 and U = 320 / 5 / 0 J against the hand-computed law, `delta ≤ 1e-6`; refusals (V0=0, duplicate id, unknown field) leave the hash fixed |
| valve (paired transport) | `test_valve_equalizes_and_conserves` | q₁+q₂ = 0.002 m³ conserved to 1e-9 rel; equalised P = −90 kPa ± 50; dissipation 10 J ± 1 % (analytic 820→810 J); `flux = g·ΔP` and chamber `flux_in = −J` on the same substep; `max_residual_energy_J < 1e-9` (observed ~2e-13) |
| closing/severing removes only its contribution | `test_valve_close_sever_patch_contributions` | closed valve `flux = 0` exactly while the surviving env leak still obeys `J = g·P₂` (±3 %, one-substep print lag); after sever, both inventories frozen to 1e-12 over 50 ms of sim time |
| patch consumes, history survives (gallery 9) | same test | patch of the env leak debits exactly `cost_m3` (±1e-10 print resolution), refuses a cost the chamber cannot pay, removes only the patched path, and the surviving chamber's P is the law of the debited q — not a reset; `residual_inventory_m3` ~ 4e-19 |
| heat transfer | `test_heat_pair_exact_transfer` | 400/300 K → 350.0 ± 0.5 K in 12 τ; `moved_J_run` = 5000 J ± 1 %; `u_th_total_J` = 70000 J conserved to 1e-9 rel; refusals: link onto a zero-capacity chamber, unstable `k` |
| finite actuator | `test_piston_finite_actuator` | ram (1.1 kg box incl. rest sink) driven by `f_max = 5 N` over 50 mm: `work_J_run` = 3.75 J ± 2 % (= chamber −ΔU), `relief_J_run` = 3.5 J ± 2 % (the withheld 3.5 J), coast speed 0.6739 vs analytic √(2·5·0.05/1.1) = 0.6742 (0.05 %); beyond the stop `force = 0`, `V_m3` frozen over 100 ms, `q` untouched to 1e-12 |
| sensor | `test_sensor_readonly` | hash invariant across three sensor reads (paused); fixed schema/ledger/chamber key sets |
| transaction law | `test_process_transaction_law` | 11 malformed process documents all refused with self-naming errors; hash invariant across all of them |

Scene-level closure observed during the runs: `residual_energy_J` ~1e-14,
`max_residual_energy_J` ~2e-13 with energies in the 800 J range — the
ledger closes at fp, not at tolerance.

## Engineering findings (what the gate exercise discovered)

1. **The ledger caught its own bookkeeping bug.** The first smoke run
   reported `max_residual_energy_J = 4.375 J` — exactly the first
   substep's valve dissipation. Cause: the run totals were staged
   *after* the valve loop mutated them, excluding the increment from the
   closure window. A tolerance-based check would have hidden this; the
   fp-closure requirement localised it to one line.
2. **Stroke must disengage the volume coupling, not just the force.**
   With volume still tracking a coasting ram, the chamber becomes an
   unphysical vacuum pump (U grows unboundedly with zero force). The
   fix clamps the piston's volume contribution at the stop
   (`b6_clamp_disp`) — continuous in position, so U stays continuous
   and the ledger still closes exactly.
3. **Patch energy is real.** Debiting inventory from a *negative*-pressure
   chamber raises U (measured boundary booking −18.2 J for a 0.2 L patch
   at −90 kPa): pulling material out of a suction chamber costs work,
   and the ledger books it against the boundary instead of losing it.
4. **Wall-clock sleeps are not sim time.** The render loop's frame
   pacing can freeze stepping for tens of ms (measured: `steps` frozen
   across a 4 ms sleep), so the battery measures short process windows
   in substeps (`_wait_steps`), the same discipline the B5 window
   assertions needed.
5. **Analytic numbers must use the generator's geometry.** The piston
   box spans `y = −REST_SINK..0.10`, i.e. 1.1 kg, not the nominal 1.0 —
   the first speed assertion failed by exactly the √(1.1) factor. The
   engine was right; the hand computation was wrong.
6. **Flux telemetry lags pressure telemetry by one substep** (flux is
   the law of the force-time pressure; `p_Pa` is post-mutation), so
   flux-law assertions carry a one-substep decay tolerance (≤ 3 %).

## Gate honesty — what B6 does *not* claim

* No **pump** yet: nothing consumes power to move inventory against a
  gradient (Study C's separately-powered pump, GAME_PLAN lines 858–876,
  and line 571's "a command signal does not itself supply energy" remain
  for the pump gate). The valve is a passive conductance.
* Single-phase, species-free inventory: `q` is a signed volume, not a
  gas/liquid with transport-coupled energy beyond the booked pairs
  (GAME_PLAN line 65's transported-energy half is covered for the paired
  exchanges qualified here; advected enthalpy with flow is not modelled).
* Heat is conduction between lumped capacities only — no growth, no
  radiation, no temperature dependence of κ.
* The piston's reaction goes to the world (documented in the header), so
  the chamber+part pair is not internally momentum-conserving; the
  chamber is explicitly a fixture of the lair ground.
* "heat transfer **or growth**": growth is not implemented; the gate's
  disjunction is satisfied by the heat channel.

## Files

* `ChimeraEngine/engine/b2_scene.hpp` / `.cpp` — process state, law,
  ledger, transactions, save/restore, sensor.
* `ChimeraEngine/engine/membrane_tick.hpp` / `.cpp` — `b2_*` wrappers on
  the existing `b2_mtx_` lane.
* `ChimeraEngine/engine/main.cpp` — routes `/tick_b2_chamber`,
  `/tick_b2_valve`, `/tick_b2_valve_set`, `/tick_b2_valve_remove`,
  `/tick_b2_valve_patch`, `/tick_b2_heat`, `/tick_b2_heat_remove`,
  `/tick_b2_piston`, `/tick_b2_piston_remove`, `/tick_b2_process_clear`
  (POST) and `/tick_b2_process` (GET).
* `tools/construction_packet/test_b6_processes.py` — the battery (7/7).

## Reproduce

```
cmake --build .tmp/body-engine --config Release --parallel 2
python tools/construction_packet/test_b6_processes.py        # 7/7, port 8794
```

Regression with the change: `test_construction_packet` 23/23,
`test_b2_statics` 5/5, `test_b2_dynamics` 8/8, `test_b3_layers` 6/6,
`test_b4_assembly` 6/6, `test_b5_bridge` 4/4, `test_b5_shapes` 6/6 —
all green on the same build.
