"""
Chimera Engine CLI — unified command line for the dialectical workflow.

Commands:
  python -m ChimeraEngine witness --beats <path>
      Run beat script and record evidence through the Witness Gate.

  python -m ChimeraEngine analyze
      Run the Council: surface design questions from simulation state.

  python -m ChimeraEngine helm
      Gap analysis: what's the biggest divergence from design intent?

  python -m ChimeraEngine verify --beats <path>
      Full verification cycle: witness → record → verify.

  python -m ChimeraEngine view
      Launch the interactive particle viewer.

  python -m ChimeraEngine demo
      Run the batch render demo.
"""

import sys, argparse, json, time
from pathlib import Path


def cmd_witness(args):
    from ChimeraEngine.beats import BeatRunner
    from ChimeraEngine.gates import WitnessGate, VerifyGate

    bf = getattr(args, 'beats', None)
    if not bf:
        print("No beats specified.")
        return 1
    print(f"Witness Gate — {bf}")
    runner = BeatRunner(fps=60)
    result = runner.run(bf)

    gate = WitnessGate()
    gr = gate.check(result)

    print(f"\n  {gr.gate}: {'PASS' if gr.passed else 'FAIL'}")
    print(f"  Beats: {result.beats_reached}/{result.beats_total}")
    print(f"  Time:  {result.walltime_s:.1f}s")
    print(f"  {result.temperature}")

    if not gr.passed:
        for o in result.outcomes:
            if not o.reached:
                for e in o.expectations:
                    if not e["passed"]:
                        print(f"    FAIL: {o.name} — {e['name']}: {e['detail']}")

    if getattr(args, 'record', False):
        vg = VerifyGate()
        vr = vg.verify(gr)
        print(f"  {vr.gate}: {'PASS' if vr.passed else 'FAIL'} — {vr.note}")

    return 0 if gr.passed else 1


def cmd_analyze(args):
    from ParticleEngine.core import ParticleSimulator
    from ParticleEngine.kernels.standard import (
        gravity_kernel, wind_kernel, box_boundary_kernel, accumulation_kernel)
    from ParticleEngine.control_vars import default_physics_registry
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ChimeraEngine.council import Council

    print("Council — analyzing simulation state...")
    sim = ParticleSimulator(20000)
    reg = default_physics_registry()
    for k in [gravity_kernel, wind_kernel, box_boundary_kernel, accumulation_kernel]:
        sim.add_kernel(k, k.__name__)
    sim.spawn(5000, 'dust', (0, 0, 500), 300, mass=0.005, life=-1,
              color=(0.75, 0.68, 0.55, 0.8), size=0.5)
    sim.spawn(3000, 'sand', (200, 100, 600), 200, mass=0.02, life=-1,
              color=(0.9, 0.72, 0.35, 0.9), size=0.4)
    sim.spawn(500, 'atmosphere', (0, 0, 2000), 800, mass=0.001, life=-1,
              color=(0.5, 0.6, 0.85, 0.05), size=12.0)
    for _ in range(60): sim.step(1/60, reg.snapshot())

    pipe = FullGPUPipeline()
    pipe.upload(sim._data[:sim.count])
    cvars = reg.snapshot()
    for _ in range(30): pipe.step_particles(1/60, cvars)

    council = Council()
    questions = council.analyze(pipe.download_particles(), pipe)

    print(f"\n  {len(questions)} design questions surfaced:\n")
    for i, q in enumerate(questions):
        print(f"  [{q.category}] {q.text}")

    if getattr(args, 'ask_lm', False):
        for q in questions:
            answer = council.ask_lm(q)
            print(f"\n  LM: {answer[:300]}")

    return 0


def cmd_helm(args):
    from ParticleEngine.core import ParticleSimulator
    from ParticleEngine.kernels.standard import (
        gravity_kernel, wind_kernel, box_boundary_kernel, accumulation_kernel)
    from ParticleEngine.control_vars import default_physics_registry
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ChimeraEngine.helm import default_helm

    print("Helm — gap analysis...")
    sim = ParticleSimulator(20000)
    reg = default_physics_registry()
    for k in [gravity_kernel, wind_kernel, box_boundary_kernel, accumulation_kernel]:
        sim.add_kernel(k, k.__name__)
    sim.spawn(5000, 'dust', (0, 0, 500), 300, mass=0.005, life=-1,
              color=(0.75, 0.68, 0.55, 0.8), size=0.5)
    sim.spawn(3000, 'sand', (200, 100, 600), 200, mass=0.02, life=-1,
              color=(0.9, 0.72, 0.35, 0.9), size=0.4)
    sim.spawn(2000, 'atmosphere', (0, 0, 2000), 800, mass=0.001, life=-1,
              color=(0.5, 0.6, 0.85, 0.08), size=12.0)
    for _ in range(60): sim.step(1/60, reg.snapshot())

    pipe = FullGPUPipeline()
    pipe.upload(sim._data[:sim.count])
    cvars = reg.snapshot()
    for _ in range(30): pipe.step_particles(1/60, cvars)

    helm = default_helm()
    gaps = helm.analyze(pipe.download_particles(), pipe)

    print()
    if gaps:
        for g in gaps:
            print(f"  [{g.severity:.2f}] {g.name}")
            print(f"       Target: {g.design_target}")
            print(f"       Reality: {g.reality}")
    else:
        print("  No gaps found. All design targets met.")

    return 0


def cmd_verify(args):
    from ChimeraEngine.beats import BeatRunner
    from ChimeraEngine.gates import WitnessGate, VerifyGate

    bf = getattr(args, 'beats', None)
    if not bf:
        print("No beats specified.")
        return 1
    print(f"Verify Gate — {bf}")
    runner = BeatRunner()
    result = runner.run(bf)

    wg = WitnessGate()
    wr = wg.check(result)
    print(f"  Witness: {'PASS' if wr.passed else 'FAIL'}")

    vg = VerifyGate()
    vr = vg.verify(wr)
    print(f"  Verify:  {'PASS' if vr.passed else 'FAIL'} — {vr.note}")

    if getattr(args, 'evidence', False):
        ledger = Path("ChimeraEngine/evidence.json")
        if ledger.exists():
            print(f"\n  Evidence ledger ({ledger.stat().st_size} bytes):")
            entries = json.loads(ledger.read_text())
            for e in entries[-5:]:
                print(f"    {e['gate']}: {'PASS' if e['passed'] else 'FAIL'} — {e['note'][:80]}")

    return 0 if vr.passed else 1


def cmd_fullcycle(args):
    """Full development cycle: Council → Beats → Helm."""
    from pathlib import Path

    print("=" * 55)
    print(" CHIMERA ENGINE — Full Development Cycle")
    print("=" * 55)

    # 1. Council
    print("\n[1/3] COUNCIL — analyzing simulation state...")
    rc = cmd_analyze(args)

    # 2. Witness
    beats_dir = Path(__file__).resolve().parent / "beats"
    beat_files = sorted(beats_dir.glob("*.beats.json"))
    print(f"\n[2/3] WITNESS — running {len(beat_files)} beat script(s)...")
    total_pass = 0
    for bf in beat_files:
        from ChimeraEngine.beats import BeatRunner
        from ChimeraEngine.gates import WitnessGate, VerifyGate
        runner = BeatRunner(fps=60)
        result = runner.run(str(bf))
        gate = WitnessGate()
        gr = gate.check(result)
        vg = VerifyGate()
        vr = vg.verify(gr)
        status = "PASS" if gr.passed else "FAIL"
        print(f"  {bf.name}: {status} ({result.beats_reached}/{result.beats_total})")
        if gr.passed:
            total_pass += 1

    # 3. Helm
    print(f"\n[3/3] HELM — gap analysis...")
    rc2 = cmd_helm(args)

    print(f"\n{'=' * 55}")
    print(f" CYCLE COMPLETE — {total_pass}/{len(beat_files)} beat files passed")
    print(f"{'=' * 55}")
    return 0 if total_pass == len(beat_files) else 1


def main():
    p = argparse.ArgumentParser(description="Chimera Engine — dialectical particle engine workflow")
    sub = p.add_subparsers(dest="command")

    wit = sub.add_parser("witness", help="Run beats through Witness Gate")
    wit.add_argument("--beats", required=True)
    wit.add_argument("--record", action="store_true")

    sub.add_parser("analyze", help="Council: surface design questions")
    ana = sub.choices["analyze"]
    ana.add_argument("--ask-lm", action="store_true")

    sub.add_parser("helm", help="Gap analysis")

    ver = sub.add_parser("verify", help="Full verify cycle")
    ver.add_argument("--beats", required=True)
    ver.add_argument("--evidence", action="store_true")

    sub.add_parser("view", help="Launch interactive viewer")
    sub.add_parser("demo", help="Run batch render demo")
    ful = sub.add_parser("fullcycle", help="Council -> Beats -> Helm in one pass")

    args = p.parse_args()

    if args.command == "witness":
        return cmd_witness(args)
    elif args.command == "analyze":
        return cmd_analyze(args)
    elif args.command == "helm":
        return cmd_helm(args)
    elif args.command == "verify":
        return cmd_verify(args)
    elif args.command == "view":
        from ParticleEngine.viewer import main as view_main
        return view_main()
    elif args.command == "demo":
        from ParticleEngine.standalone import main as demo_main
        return demo_main()
    elif args.command == "fullcycle":
        return cmd_fullcycle(args)
    else:
        p.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
