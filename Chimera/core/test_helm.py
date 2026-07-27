"""Tests for core.helm — run: python core/test_helm.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PASS = TOTAL = 0


def check(name, cond):
    global PASS, TOTAL
    TOTAL += 1
    print(("  ok  " if cond else "FAIL  ") + name)
    PASS += cond


def main():
    import core.helm as helm

    # 1: token extraction strips the glued UE prefix (the bug that hid erisaid)
    check("tokens: AErisaidActor -> {erisaid}", helm._camel_tokens("AErisaidActor") == {"erisaid"})
    check("tokens: USacrificeLogComponent -> {sacrifice, log}",
          helm._camel_tokens("USacrificeLogComponent") == {"sacrifice", "log"})
    check("tokens: UStaticMeshComponent drops to engine words",
          "static" in helm._camel_tokens("UStaticMeshComponent"))

    # 2: engine builtins vs project systems
    erisaid = helm.VisionSystem("AErisaidActor", "§10", "the shell")
    mesh = helm.VisionSystem("UStaticMeshComponent", "§4", "a mesh")
    check("AErisaidActor is a project system", erisaid.is_project)
    check("UStaticMeshComponent is NOT (engine builtin)", not mesh.is_project)
    check("§10 world outweighs §1 math", erisaid.weight > helm.VisionSystem(
        "FVector", "§1", "").weight)

    # 3: parse the real seed — it must yield many classes + project systems
    systems = helm.parse_vision()
    check("vision parses to many classes (ast, deterministic)", len(systems) > 100)
    project = [s for s in systems if s.is_project]
    check("finds a healthy set of project systems (not ~4)", len(project) >= 15)
    names = {s.name for s in project}
    check("catches the soul systems", {"AErisaidActor", "USacrificeLogComponent"} <= names)

    # 4: realization scoring against a synthetic index
    idx = {"classes": {"sacrifice", "log"}, "features": set(), "graduated": set()}
    sac = next(s for s in project if s.name == "USacrificeLogComponent")
    check("realization: in-source but not graduated -> 0.5",
          helm.realization(sac, idx) == 0.5)
    idx2 = {"classes": {"sacrifice", "log"}, "features": {"sacrifice"},
            "graduated": {"sacrifice"}}
    check("realization: graduated -> 1.0", helm.realization(sac, idx2) == 1.0)
    absent = next(s for s in project if helm.realization(
        s, {"classes": set(), "features": set(), "graduated": set()}) == 0.0)
    check("realization: absent system -> 0.0", absent is not None)

    # 5: vision_gap + steer produce a coherent heading
    gap = helm.vision_gap()
    check("vision gap: fraction in [0,1] and targets ranked by gap_value",
          0.0 <= gap["realized_fraction"] <= 1.0
          and all(gap["targets"][i]["gap_value"] >= gap["targets"][i + 1]["gap_value"]
                  for i in range(len(gap["targets"]) - 1)))
    s = helm.steer()
    check("steer: a heading among the known categories",
          s["heading"] in {"Contain", "Fix", "Graduate", "Build", "Verify",
                           "Polish", "Consolidate"})
    # compare against the fraction STEER used (self-consistent) — a fresh
    # vision_gap() call re-reads live rep state and can drift mid-test
    check("steer: Build pressure tracks the vision gap it used",
          abs(s["scores"]["Build"] - round(1.0 - s["realized_fraction"], 2)) <= 0.01)
    line = helm.preflight_line()
    check("preflight line names the heading + realized %",
          "[0.7] Helm" in line and "steer ->" in line)

    print(f"\n{PASS}/{TOTAL} tests passed")
    return 0 if PASS == TOTAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
