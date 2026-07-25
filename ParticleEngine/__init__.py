"""
Chimera Particle Engine — Python-native simulation + Unreal rendering bridge.

Architecture:
  Python (simulation) ←→ Unreal Engine (rendering)
       │                      │
  ┌────┴─────┐       ┌───────┴────────┐
  │ NumPy/   │       │ Instanced meshes│
  │ Taichi   │ ←──→  │ Splat rendering │
  │ kernels  │       │ Viewport camera │
  └──────────┘       └────────────────┘
       │
  ┌────┴─────┐
  │ Control  │ ← user/dialectical-design input
  │ Variable │
  │ DSL      │
  └──────────┘

Every particle carries writable control variables that govern
emergent behavior — physical (dust, sand, atmosphere) and abstract
(social intent, trade flow, educational specimen state).
"""
from ParticleEngine.core import ParticleSimulator, ParticleState
from ParticleEngine.control_vars import ControlVariable, VarRegistry
from ParticleEngine.kernels.standard import gravity_kernel, wind_kernel, ground_collision_kernel
from ParticleEngine.splat import SplatConverter, SplatState
from ParticleEngine.camera import FirstPersonCamera, CameraParams
from ParticleEngine.rasterizer import SplatRasterizer, RenderConfig
from ParticleEngine.reflect import reflect_kernel, gaussian_scatter_kernel

__version__ = "0.1.0"
