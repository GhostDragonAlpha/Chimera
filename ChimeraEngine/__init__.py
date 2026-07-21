"""
Chimera Engine — workflow layer over the particle engine.

Applies the dialectical design methodology from the Unreal Chimera
project to the new standalone GPU particle engine.

  Council Q&A  →  Beat scripts  →  Simulation  →  Gates  →  Helm
  (design)         (spec)           (GPU)          (verify)   (steer)
"""

from ChimeraEngine.beats import BeatRunner, BeatOutcome, BeatRun
from ChimeraEngine.gates import WitnessGate, VerifyGate
from ChimeraEngine.helm import Helm, Gap
from ChimeraEngine.council import Council, Question

__version__ = "0.1.0"
