"""TypeB-P1 M2 declared perturbation patcher (prereg_typeb_p1.json M2).

Injects ONE mid-run command step (controller tick 150) into the reflex layer's
candidate command surfaces, in the WORKING TREE only, never committed. The
reach-annulus clamps and every reflex guard stay DOWNSTREAM of the injection --
they are the veto surface under test, not removed.

  B  plant-target command: hind launch xoff and fore_xoff() scaled x1.6
  C  posture command: trunk posture target += 0.15 rad
  D  phase clock command: left-leg phase += 0.25 cycle at tick 150 (one-shot)
  restore: git checkout -- gait_controller.hpp

Usage: python apply_tb2_perturb.py B|C|D|restore
"""
import os, subprocess, sys
GAIN = os.environ.get("TB2_GAIN", "1.6")

REPO = r"E:\ChimeraWork\tb1-agent"
SRC = REPO + r"\ChimeraEngine\engine\gait_controller.hpp"
TAG = "TYPEB-P1 M2 DECLARED COMMAND"

def rd():
    with open(SRC, "r", encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")

def wr(s):
    with open(SRC, "w", encoding="utf-8", newline="") as f:
        f.write(s.replace("\n", "\r\n"))

def sub1(s, anchor, repl):
    n = s.count(anchor)
    if n != 1:
        sys.exit("ANCHOR FAIL (count=%d): %r" % (n, anchor[:70]))
    return s.replace(anchor, repl)

A_FORE = (" double fore_xoff()const{ // x_off = v * t_stance/2 at the CURRENT measured speed\n"
          "  return (std::max)(0.,s_.v[3])*(DUTY_SAMPLED*T_CYCLE)/2.;}")
B_FORE = (" double fore_xoff()const{ // x_off = v * t_stance/2 at the CURRENT measured speed\n"
          "  double x0=(std::max)(0.,s_.v[3])*(DUTY_SAMPLED*T_CYCLE)/2.;\n"
          "  return ticks_>=150?" + GAIN + "*x0:x0;} //" + TAG + " B: plant-target command x" + GAIN + " at tick 150\n")

A_HIND = ("     double xoff=(std::max)(0.,s_.v[3])*(DUTY_SAMPLED*T_CYCLE)/2.;\n"
          "     auto hip=e.point(pelvis_row_,hind_mount_[hl]).first;")
B_HIND = ("     double xoff=(std::max)(0.,s_.v[3])*(DUTY_SAMPLED*T_CYCLE)/2.;\n"
          "     if(ticks_>=150)xoff*=" + GAIN + "; //" + TAG + " B: plant-target command x" + GAIN + " at tick 150\n"
          "     auto hip=e.point(pelvis_row_,hind_mount_[hl]).first;")

A_POST = "   double target_post=trunk_amp*tables_.trunk_target(phi_[0]);"
C_POST = ("   double target_post=trunk_amp*tables_.trunk_target(phi_[0]);\n"
          "   if(ticks_>=150)target_post+=0.15; //" + TAG + " C: posture command +0.15 rad at tick 150")

A_CLK = "  last_torque_=impulse_torque;++ticks_;}"
D_CLK = ("  last_torque_=impulse_torque;\n"
         "  if(ticks_==150)phi_[0]+=0.25; //" + TAG + " D: one-shot phase-clock command +0.25 cycle, left leg\n"
         "  ++ticks_;}")

def main():
    mode = sys.argv[1]
    if mode == "restore":
        subprocess.run(["git", "-C", REPO, "checkout", "--",
                        "ChimeraEngine/engine/gait_controller.hpp"], check=True)
        print("RESTORED ship controller bytes")
        return
    s = rd()
    if TAG in s:
        sys.exit("a M2 perturbation patch is already applied -- restore first")
    if mode == "B":
        s = sub1(s, A_FORE, B_FORE)
        s = sub1(s, A_HIND, B_HIND)
    elif mode == "C":
        s = sub1(s, A_POST, C_POST)
    elif mode == "D":
        s = sub1(s, A_CLK, D_CLK)
    else:
        sys.exit("mode must be B, C, D or restore")
    wr(s)
    print("M2 PERTURBATION APPLIED:", mode)

if __name__ == "__main__":
    main()
