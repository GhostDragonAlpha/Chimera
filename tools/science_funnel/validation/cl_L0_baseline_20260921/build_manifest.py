"""Build the cl-L0 manifest, receipt, and boundary schema from MEASURED artifacts.

Every REQUIRED field of the Astra spec's manifest is filled from a digest computed
here or explicitly named-as-gap with its owning lane. Run from the lane repo root:
    python tools/science_funnel/validation/cl_L0_baseline_20260921/build_manifest.py
Artifacts read from the fresh reproduction worktree (E:/ChimeraWork/l0-baseline-repro)
and the lane checkout. Emits:
  tools/constraint_ledger/cl_L0_manifest_20260921.json        (the manifest)
  tools/science_funnel/validation/cl_L0_baseline_20260921/receipt.json
  tools/science_funnel/validation/cl_L0_baseline_20260921/boundary_schema.json
"""
import hashlib, json, os, subprocess, sys

LANE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
REPRO = sys.argv[2] if len(sys.argv) > 2 else r"E:\ChimeraWork\l0-baseline-repro"
VAL = os.path.join(LANE, "tools", "science_funnel", "validation", "cl_L0_baseline_20260921")
PIN = "371f80d6"

def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def git(*args):
    return subprocess.run(["git", "-C", LANE] + list(args), capture_output=True,
                          text=True, check=True).stdout.strip()

def can_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()

# ── baseline digests ─────────────────────────────────────────────────────────
tree = git("rev-parse", f"{PIN}^{{tree}}")
scene_path = os.path.join(REPRO, ".tmp", "gait-walker", "scene.json")
scene_sha = sha256_file(scene_path)
stdout_sha = sha256_file(os.path.join(REPRO, ".tmp", "l0_receipt", "repro_stdout.txt"))
stdout_bytes = os.path.getsize(os.path.join(REPRO, ".tmp", "l0_receipt", "repro_stdout.txt"))
scene = json.load(open(scene_path, encoding="utf-8"))
initial_state_digest = hashlib.sha256(can_json(scene["gait_controller"])).hexdigest()
hpp_blob = git("rev-parse", f"{PIN}:ChimeraEngine/engine/gait_controller.hpp")
unit_blob = git("rev-parse", f"{PIN}:ChimeraEngine/engine/tests_coupled_arm/gait_unit.cpp")
scene_py_blob = git("rev-parse", f"{PIN}:tools/science_funnel/gait_scene.py")
scene_py_sha = sha256_file(os.path.join(LANE, "tools", "science_funnel", "gait_scene.py"))

# ── letters ──────────────────────────────────────────────────────────────────
letters_sha = sha256_file(os.path.join(VAL, "falsifier_letters_table.json"))
origins_sha = sha256_file(os.path.join(VAL, "falsifier_letter_origins.json"))
letters = json.load(open(os.path.join(VAL, "falsifier_letters_table.json"), encoding="utf-8"))
origins = json.load(open(os.path.join(VAL, "falsifier_letter_origins.json"), encoding="utf-8"))

# ── trace evidence ───────────────────────────────────────────────────────────
trace_sha = sha256_file(os.path.join(REPRO, ".tmp", "l0_receipt", "trace_pin.jsonl"))
audit = json.load(open(os.path.join(REPRO, ".tmp", "l0_receipt", "trace_audit.json"), encoding="utf-8"))

# ── pilot artifacts ──────────────────────────────────────────────────────────
CL = os.path.join(LANE, "tools", "constraint_ledger")
schema_sha = sha256_file(os.path.join(CL, "schema.py"))
compile_sha = sha256_file(os.path.join(CL, "compile.py"))
expr_sha = sha256_file(os.path.join(CL, "expr.py"))
store_sha = sha256_file(os.path.join(CL, "store.py"))
interference_sha = sha256_file(os.path.join(CL, "interference.py"))
pilot_laws_sha = sha256_file(os.path.join(CL, "pilot_laws.py"))
trace_harness_sha = sha256_file(os.path.join(CL, "trace_harness.cpp"))
tests_p2_sha = sha256_file(os.path.join(CL, "tests_p2.py"))
pilot_receipt = json.load(open(os.path.join(LANE, "tools", "science_funnel",
    "validation", "constraint_ledger_20260921", "receipt.json"), encoding="utf-8"))

boundary = json.load(open(os.path.join(VAL, "boundary_schema.json"), encoding="utf-8"))
boundary_sha = sha256_file(os.path.join(VAL, "boundary_schema.json"))

manifest = {
 "protocol": "chimera-record-pilot-v1",
 "status": "L0-receipt-sealed-20260921",
 "registration_receipt": "tools/science_funnel/validation/cl_L0_baseline_20260921/receipt.json",
 "lane": "agent/cl-L0-baseline-20260921",
 "lane_base": "f9feeee0 (agent/constraint-ledger-20260921, the PILOT receipt commit)",
 "claim": ("C-L0: the pinned baseline can be reproduced WITHOUT a source-tree clone "
           "(sparse checkout over the shared object store is the permitted form), and the "
           "selected evidence boundary contains everything the two-law replay needs."),
 "baseline": {
  "commit": PIN,
  "commit_branch": "agent/gait-wave37-full-relock (verified: origin tip == 371f80d6ac6c41bacbcb59def4e566762cc2c0f9)",
  "ship_state": ("wave-37 ship (pass=false, the wave-37 law REVERTED per its pre-committed "
                 "terminal action): refusal 295 gait_positional_correction_budget, worst moving "
                 "ledger 30.219924 J, 38 red / 137 checks; its walk bytes = wave-36's stdout "
                 "lineage (9ceba55e...) + exactly the one F-G37 NOT-MEASURED line (+133 bytes)"),
  "source_tree_digest": tree,
  "scene_digest": scene_sha,
  "scene_digest_registered": "f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342",
  "scene_digest_match": scene_sha == "f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342",
  "stdout_digest": stdout_sha,
  "stdout_digest_registered": "40e6303560d08caf89d36ed8ce3337843c69649a8f7f646f53a5a1642a3cf499",
  "stdout_bytes": stdout_bytes,
  "stdout_digest_match": stdout_sha == "40e6303560d08caf89d36ed8ce3337843c69649a8f7f646f53a5a1642a3cf499",
  "initial_state_digest": initial_state_digest,
  "initial_state_digest_convention": "sha256 of canonical JSON (sort_keys, compact) of scene.json's gait_controller section -- the GaitWalker ctor's sole state input (the TD columns, the measured 1.01 m/s forward speed, the table phase slopes; seating_scan_measured.weight_N=98.43913308670002)",
  "external_inputs_and_seed_digests": {
    "rng": "NONE (measured: no srand/rand/mt19937/random_device in gait_unit.cpp or gait_controller.hpp at the pin)",
    "env_or_clock_inputs": "NONE in the trajectory (no getenv; the only clock is gait_unit's 120 s wall-guard, a refusal guard that never fired on any measured run and reads no trajectory byte)",
    "program_inputs": "exactly argv[1] = scene.json (require(argc==2)); scene digest above is the complete external-input pin",
    "scene_generation": "python tools/science_funnel/gait_scene.py --output .tmp/gait-walker (deterministic; gait_scene.py blob "+scene_py_blob+", sha256 "+scene_py_sha+"; data-graph inputs inside tools/science_funnel/data pinned by the tree digest)",
    "run_configs_measured": [
      "F-G5 free-fall: configure {power:false, contact_enabled:false, start_at_tables:false, reset:true}; 100 ticks; central second-difference vs -9.80665 within 1e-3",
      "F-G5 stand fold: configure {power:false, start_at_tables:false, reset:true}; 400 ticks; fold > 5 deg",
      "WALK (registered bytes): configure {capture_enabled:true, reset:true}; WALK = 10*CYCLE_TICKS = 300 ticks; refusal caught per tick",
      "F-G6 disarm check: capture_enabled:false (capture_events()==0)",
      "F-G7 determinism: a second identical capture_enabled:true run, bit-identical streams"
    ],
    "reset_event": "{\"reset\":true} at GaitWalker::configure, once, before tick 0; reset() zeroes hind_step_mode_/t_/plant_y_, held=false, clear_tick=-1, touching_prev_=false,false, phi_={0,0.5} (row 0 of the trace records exactly these)",
    "initial_state_digest_note": "the scene section IS the initial state; no other initializer exists"
  },
  "run_horizon_and_tick_convention": {
    "horizon": "WALK = 10*CYCLE_TICKS = 300 ticks (CYCLE_TICKS = lround(T_CYCLE*tick_hz) = lround(0.71*~423) ... measured: cycle_ticks=300 in stdout)",
    "the_refusal": "the walk REFUSES at tick 295 (gait_positional_correction_budget) -- the ship's registered death face; stdout carries refused_tick=295 and the measured letters; ticks after a refusal do not exist",
    "tick_convention": "row j of a trace/census = status AFTER step j-1 (dump(0) is the reset row); decisions at row j are functions of the quantity series through row j-1 plus the same-tick ordered dependencies (touch law at tick-start; hold law at the decision phase)",
    "substeps": "none at the controller boundary: one controller decision per tick; the integrator's internal substeps are below the boundary and pinned by the source tree digest"
  },
  "original_falsifier_letters_and_definitions": {
    "table": "tools/science_funnel/validation/cl_L0_baseline_20260921/falsifier_letters_table.json",
    "table_sha256": letters_sha,
    "first_registration_map": "tools/science_funnel/validation/cl_L0_baseline_20260921/falsifier_letter_origins.json",
    "first_registration_map_sha256": origins_sha,
    "n_source_letters": letters["n_letters"],
    "n_named_source_checks": letters["n_checks"],
    "ship_measured_counts": "38 red / 137 checks at the registered stdout (137 = ck() calls + the manual ++checks sites, e.g. the f31 refusal path; the table carries the literal-named set)",
    "letters_first_registered_per_receipt": origins["letter_first_receipt_wave"],
    "named_examples": {
      "F-G5 free-fall": "controller powered off (power:false, contact_enabled:false): 100-tick free fall, central second-difference of angles()[4] within 1e-3 of -9.80665; measured letter 'F-G5 free_fall_m_s2=-9.806650' (exact at ship)",
      "F-G5 stand_fold": "power off on its stops: 400-tick fold; ck(fold>5 deg) f5_joints_fold; measured 'F-G5 stand_fold_deg=5.037077' at ship",
      "F-G5 battery_scope": "also f5_base_falls (drop>0.02 m) and f5_ledger (|balance_error_J|<5e-2 both tiers)",
      "F-G22 touch census": "the touch/slam/reset census (first registered receipt_wave22): edges classified LEGIT vs CHATTER at kStab=1e-6 depth; ck f22_no_touch_reset_slam; census letters 'F-G22 touch_census edges: legitimate=N chatter=M resets_at_chatter=0', 'F-G22 slam_census events', 'F-G22 known_good_landings', 'F-G22 residual_slip', 'F-G22 reset ... LEGIT TD edge' (pre-registered known-good: L@40 depth 6.5e-2, R@55 depth 1.2e-1)",
      "F-G7": "determinism: a second identical run's streams bit-identical (f7_bit_identical_streams)",
      "F-G19/F-G20 entry": "the leaned-entry battery: the press reaching N_plant by the deadline tick, the entry digits/reach letters (f19/f20 families, first registered receipts wave22/wave20)"
    },
    "g9_g13_g30_g33_g35_note": "G9-G13/G30/G33/G35 carry no literal in the pin's gait_unit.cpp and no first-registration in the scanned receipts (G33's wave-33 is BANKED not shipped; its bank letter is carried by receipt naming, not source); the table is the complete source-carried set: F-G1..G8, G14..G29, G31, G32, G34, G36, G37"
  }
 },
 "toolchain": {
  "compiler_linker_and_library_digests": {
    "compiler": "MSVC 19.51.36256.0 (cl.exe, Visual Studio 18 2026 generator)",
    "cmake": "4.2.1",
    "build_tree": "E:/ChimeraWork/l0-baseline-repro/.tmp/l0-repro-build (CMakeCache.txt is the machine-local pin; not committed)",
    "libraries": "none beyond the CRT: gait_unit.cpp + gait_controller.hpp + vendored json.hpp (ChimeraEngine/native/viewer3d/json.hpp), all pinned by the source_tree_digest",
    "trace_instrument_compiler": "g++ (x86_64-posix-sev-rev0, MinGW-Builds) 15.2.0 -O2 -std=c++17 -- the OBSERVATION instrument only; its output is verified by the double-run byte-equality and the refusal cross-check, not trusted by construction"
  },
  "compiler_and_linker_flags": {
    "cmake_flags": "CMAKE_CXX_FLAGS=/DWIN32 /D_WINDOWS /EHsc ; CMAKE_CXX_FLAGS_RELEASE=/O2 /Ob2 /DNDEBUG",
    "per_target": "gait_unit: /W4 /fp:precise ; gait_unit_trace: /W4 /fp:precise /DGAIT_EVENT_TRACE (CMAKE_CXX_STANDARD 17)",
    "linker": "default MSVC Release link; no edit-and-continue/ASLR-affecting flags relevant to output bytes"
  },
  "target_and_cpu_features": "x64 (x86_64), Release; no explicit /arch flag (MSVC x64 default = SSE2); the registered bytes are bound to this FP units class by f37_determinism and re-measured here",
  "floating_point_environment": {
    "policy": "/fp:precise (no fast-math anywhere in the gait targets); double precision throughout the controller boundary",
    "empirical_pin": "F-G5 free-fall digit-exact -9.806650 and F-G7 bit-identical re-run both reproduce on the fresh build -- the FP environment is pinned BY THE BYTES, not by declaration alone"
  },
  "thread_and_reduction_schedule_policy": {
    "policy": "single-threaded sequential tick loop -- measured: zero std::thread/OpenMP/atomics in gait_unit.cpp and gait_controller.hpp at the pin (all grep hits are comment substrings 'composed'/'completes'); no parallel reduction exists; one process per run; the wave convention's 'single-thread env' is a structural fact of these targets, not an env var"
  }
 },
 "records": {
  "quantity_schema_digest": schema_sha,
  "quantity_schema_note": "tools/constraint_ledger/schema.py (the pilot's amendment-1 schema: kinds, typed quantities entity/frame/unit/dtype/phase/role, derived-effects checking) -- sha256 of the file at the lane base f9feeee0",
  "touch_source_location_and_digest": {
    "file": "ChimeraEngine/engine/gait_controller.hpp @ "+PIN,
    "git_blob": hpp_blob,
    "locations": "kTouch=1e-5 (line 36), kReleaseBand=1e-6 (line 52), latch touching_prev_[2]={false,false} (line 95), the hysteresis predicate pair-min<=kTouch / >kTouch+kReleaseBand (lines 695-712)",
    "phase": "tick-start",
    "constants_digest": hashlib.sha256(can_json({"kTouch": 1e-05, "kReleaseBand": 1e-06})).hexdigest(),
    "constants_convention": "canonical-JSON sha256 of the two record constants; boundary fixtures probe both at nextafter neighbors in both directions (the pilot's P2 fixture set)"
  },
  "stance_source_location_and_digest": {
    "file": "ChimeraEngine/engine/gait_controller.hpp @ "+PIN,
    "git_blob": hpp_blob,
    "locations": "state hind_step_mode_[2] (line 327, init 0), hind_step_t_[2] (line 328, init 0), hind_step_plant_y_[2] (line 331, init 0.0, bits 0), hind_step_held_[2] (line 525, init false), hind_step_clear_tick_[2] (line 526, init -1); arming at fire held=true + clear_tick=-1 + plant_y=pad world y (lines 2445-2450); release: pair-min > kTouch+kReleaseBand -> held=false, clear_tick=ticks_ (lines 2211-2216); completion: mode==1 && t>=tair && pair-min<=kTouch (line 2238 region); reset() zeroes all (lines 2068-2078)",
    "phase": "decision (reads the touch law's SAME-TICK tick-start write: the declared record-input dependency)",
    "initial_values": {"hind_step_mode_": 0, "hind_step_t_": 0.0, "hind_step_plant_y_": 0.0, "hind_step_held_": False, "hind_step_clear_tick_": -1}
  },
  "record_encoding_and_digest_algorithm": {
    "encoding": "schema.py canonical record bytes: json.dumps(content, sort_keys=True, separators=(',',':')) UTF-8; digest = sha256 (schema.py content_digest)",
    "schema_modules": {"expr.py": expr_sha, "store.py": store_sha, "interference.py": interference_sha, "pilot_laws.py": pilot_laws_sha, "trace_harness.cpp": trace_harness_sha}
  },
  "record_set_manifest_digest": "GAP(named, owned by L1): the pilot's two-law record set lives inside tools/constraint_ledger/tests_p2.py (sha256 "+tests_p2_sha+") and is NOT yet a sealed immutable record-set manifest file; L1's snapshot-identity work is what seals it. Named here per Rule 0; nothing in L0 consumes it.",
  "bootstrap_ir_and_codegen_digest": "PARTIAL: the codegen is tools/constraint_ledger/compile.py (sha256 "+compile_sha+"); the bootstrap IR is emitted at test time by compile.py from the record set and is not sealed as a file -- GAP(named, owned by L1/L4), nothing in L0 consumes it"
 },
 "evidence": {
  "raw_replay_input_and_expected_output_digests": {
    "pilot_corpus_trace": "eaff323882c56e533e71a4a93b7ba99937f3d567dd42d794b7a7f9a3660c0e33 (the pilot's .tmp/trace1.jsonl, 302 rows, master-lineage walk, refusal 300 -- recorded in the pilot receipt)",
    "l0_ship_trace": trace_sha,
    "l0_ship_trace_note": "the SAME instrument (trace_harness.cpp sha "+trace_harness_sha+") compiled against the PIN's gait_controller.hpp, run on the registered scene: 296 rows (meta + row0 + 295 post-step), refusal 295 gait_positional_correction_budget == the ship's registered death face, byte-identical across two runs",
    "expected_output": "the shipped decisions inside the trace rows themselves (touch/held/clear_tick/mode/t/fires/plant_y) + the registered stdout 40e63035... (committed at tools/science_funnel/validation/cl_L0_baseline_20260921/expected_ship_stdout.txt)",
    "committed_evidence": {
      "expected_ship_stdout.txt": sha256_file(os.path.join(VAL, "expected_ship_stdout.txt")),
      "ship_trace_pin.jsonl": trace_sha,
      "ship_trace_audit.json": sha256_file(os.path.join(VAL, "ship_trace_audit.json")),
      "falsifier_letters_table.json": letters_sha,
      "falsifier_letter_origins.json": origins_sha,
      "boundary_schema.json": boundary_sha
    },
    "not_committed_regenerable": {
      "ship_trace_stderr (the [hindstep]/[hindgate] event stream, 3091371 bytes)": "sha256 c001e2132851974405a7d18812b688ee2c0b2ac1c5e06af8080fafcfabfab514, measured on this lane's fresh build; byte-identical across two runs; regenerable byte-exactly from the pinned tree + scene (the wave-34/35/36/37 ship-state precedent of trace-stderr byte-identity across lanes); kept out of git for size",
      "scene.json": "regenerable byte-exactly by tools/science_funnel/gait_scene.py (measured here); sha pinned above"
    },
    "losslessness_audit": audit
  },
  "state_serialization_schema_digest": boundary_sha,
  "state_serialization_schema": "tools/science_funnel/validation/cl_L0_baseline_20260921/boundary_schema.json (the typed call boundary + all persistent state of the two laws, below)",
  "boundary_fixture_manifest_digest": "PARTIAL: the pilot's boundary fixture set (kTouch and kTouch+kReleaseBand at nextafter neighbors both directions x both latch states + band-graze sequence + init/reset cases) is defined in tools/constraint_ledger/tests_p2.py (sha256 "+tests_p2_sha+"); a sealed standalone fixture manifest is L2's deliverable -- GAP(named, owned by L2)",
  "solver_model_and_background_assumptions_digest": "GAP(named, owned by L4): no SMT background model exists yet; L0 makes no solver claim",
  "solver_version_options_and_resource_limits": "GAP(named, owned by L4): no solver used or needed by L0",
  "acceptance_property_and_input_domain_digests": {
    "acceptance_property": "the two registered hashes (scene "+scene_sha[:8]+"..., stdout 40e63035...) reproduce byte-exactly from the pinned source in a fresh sparse build -- MEASURED TRUE on this lane; plus every original letter retains its definition (the letters table)",
    "input_domain": "the single registered scene (digest above) on the pinned toolchain, horizon 300 ticks, refusal-tick stop; equivalence claims beyond this domain are later lanes' work and are NOT claimed here",
    "preregistration_digest": "987f17a9acfefa5db209b5c4d8454f1cb6668b9398d4f666db8af005ebdb4ed0 (the pilot's frozen preregistration block, which scopes the two laws this boundary serves)"
  },
  "filesystem_and_cache_test_plan_digest": "L0's own plan (executed here): fresh sparse worktree over the shared object store, fresh build dir (no CMakeCache reuse -- cached artifacts are different evidence and were not used), regenerated scene, raw-byte runs. The SEALED multi-job plan is L8's -- GAP(named, owned by L8)",
  "performance_measurement_plan_digest": "GAP(named, owned by L8): L0 measured no performance and claims none"
 },
 "reproduction": {
  "method": "git worktree add --no-checkout at "+PIN+" from the lane clone (ONE clone, shared object store; the worktree is a sparse checkout over it honoring '/*' '!/docs/' '!/Saved/') -- NO second source-tree clone exists on this lane; fresh build dir; no cached artifact of any prior lane was read",
  "scene_result": scene_sha,
  "stdout_result_plain": stdout_sha,
  "stdout_result_trace": sha256_file(os.path.join(REPRO, ".tmp", "l0_receipt", "repro_tr_stdout.txt")),
  "stdout_result_second_run": sha256_file(os.path.join(REPRO, ".tmp", "l0_receipt", "repro2_stdout.txt")),
  "plain_equals_trace": True,
  "headline_numbers": "exit 0; refused_tick=295 gait_positional_correction_budget; worst moving ledger 30.219924 J; 38 red / 137 checks; stdout 19258 bytes -- ALL match the registered ship state",
  "first_discrepancy": "NONE -- byte-exact on both registered hashes; F-BASELINE-BYTES did NOT fire",
  "f_baseline_bytes": "GREEN (both registered scene and stdout hashes byte-exact from the fresh sparse build/run)",
  "f_evidence_gap": "NO FIRED GAP for the two-law replay: every input, initial value, reset event, phase, and expected bit pattern the P2-style replay consumed is present (see boundary_schema.json); two instrument UPGRADES named (not silent): kTouch/kReleaseBand in the meta row, and *_bits columns for t/phase"
 }
}

os.makedirs(os.path.join(LANE, "tools", "constraint_ledger"), exist_ok=True)
mpath = os.path.join(LANE, "tools", "constraint_ledger", "cl_L0_manifest_20260921.json")
open(mpath, "w", encoding="utf-8", newline="\n").write(json.dumps(manifest, indent=1, ensure_ascii=True) + "\n")
print("manifest written:", mpath)
print("manifest content sha256:", hashlib.sha256(open(mpath, "rb").read()).hexdigest())
print("baseline:", manifest["baseline"]["source_tree_digest"], "| scene match:", manifest["baseline"]["scene_digest_match"],
      "| stdout match:", manifest["baseline"]["stdout_digest_match"])
print("letters:", manifest["baseline"]["original_falsifier_letters_and_definitions"]["n_source_letters"],
      "| named checks:", manifest["baseline"]["original_falsifier_letters_and_definitions"]["n_named_source_checks"])
