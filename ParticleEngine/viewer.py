"""Interactive GPU particle viewer — WASD flythrough, mouse look, zero Unreal."""
import sys, time, argparse, numpy as np, cv2
from ParticleEngine.camera import FirstPersonCamera


class Viewer:
    def __init__(self, w=1024, h=768, n=50000):
        self.w, self.h, self.n = w, h, n
        self.cam = FirstPersonCamera((0, -800, 400), yaw=np.radians(10), pitch=np.radians(-8))
        self.running, self.frozen = True, False
        self._mx, self._my = 0, 0
        self._last_xy = None
        self._keys = set()
        self._frame, self._times = 0, []

    def _mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN: self._last_xy = (x, y)
        elif event == cv2.EVENT_LBUTTONUP: self._last_xy = None
        elif event == cv2.EVENT_MOUSEMOVE and self._last_xy:
            self._mx += x - self._last_xy[0]
            self._my += y - self._last_xy[1]
            self._last_xy = (x, y)

    def _init(self):
        from ParticleEngine.core import ParticleSimulator
        from ParticleEngine.kernels.standard import (
            gravity_kernel, wind_kernel, box_boundary_kernel, accumulation_kernel)
        from ParticleEngine.control_vars import default_physics_registry
        from ParticleEngine.gpu_pipeline import FullGPUPipeline

        sim = ParticleSimulator(self.n + 5000)
        reg = default_physics_registry()
        for k in [gravity_kernel, wind_kernel, box_boundary_kernel, accumulation_kernel]:
            sim.add_kernel(k, k.__name__)
        nd, ns = int(self.n * 0.45), int(self.n * 0.35)
        na = self.n - nd - ns
        print(f"Spawning {nd} dust + {ns} sand + {na} atmosphere")
        sim.spawn(nd, 'dust', (-500, -300, 600), 500, mass=0.005, life=-1,
                  color=(0.75, 0.68, 0.55, 0.8), size=0.5)
        sim.spawn(ns, 'sand', (300, 200, 700), 400, mass=0.02, life=-1,
                  color=(0.9, 0.72, 0.35, 0.9), size=0.4)
        sim.spawn(na, 'atmosphere', (0, 0, 2500), 1000, mass=0.001, life=-1,
                  color=(0.5, 0.6, 0.85, 0.08), size=12.0)
        for _ in range(30): sim.step(1 / 60, reg.snapshot())

        self.pipe = FullGPUPipeline()
        self.pipe.upload(sim._data[:sim.count])
        self.cvars = {'gravity': (0, 0, -200), 'wind_vector': (15, 8, 3), 'wind_strength': 0.3,
                      'boundary_min': (-5000, -5000, -500), 'boundary_max': (5000, 5000, 5000),
                      'boundary_restitution': 0.4, 'accumulation_threshold': 5.0,
                      'accumulation_rate': 0.03}

    def run(self):
        print("Initializing...")
        self._init()

        cv2.namedWindow("Chimera Particle Engine", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Chimera Particle Engine", self.w, self.h)
        cv2.setMouseCallback("Chimera Particle Engine", self._mouse)

        print(f"\n{'='*55}")
        print(f"  WASD=move  Mouse drag=look  Q/E=up/down  Space=freeze  R=reset  ESC=quit")
        print(f"  {self.n} particles | {self.w}x{self.h}")
        print(f"{'='*55}\n")

        dt, lt = 1/60, time.time()
        while self.running:
            now = time.time(); fd = min(now - lt, 0.1); lt = now

            self.cam.tick(
                dyaw=self._mx, dpitch=self._my,
                forward=1 if 'w' in self._keys else (-1 if 's' in self._keys else 0),
                right=1 if 'd' in self._keys else (-1 if 'a' in self._keys else 0),
                up=1 if 'e' in self._keys else (-1 if 'q' in self._keys else 0),
                dt=dt if self.frozen else fd)
            self._mx = 0; self._my = 0
            p = self.cam.params(self.w, self.h)

            img = self.pipe.step_and_render(dt, self.cvars, self.cam, p)
            bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            self._frame += 1; self._times.append(time.time())
            if len(self._times) > 60: self._times.pop(0)
            fps = len(self._times)/(self._times[-1]-self._times[0]) if len(self._times)>1 else 0
            for i, line in enumerate([
                f"FPS: {fps:.0f}",
                f"Particles: {self.pipe._n}",
                f"Speed: {self.cam.move_speed:.0f}",
                f"Pos: ({self.cam.position[0]:.0f}, {self.cam.position[1]:.0f}, {self.cam.position[2]:.0f})",
                f"{'FROZEN' if self.frozen else 'LIVE'}"
            ]):
                cv2.putText(bgr, line, (10, 25 + i * 22),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

            cv2.imshow("Chimera Particle Engine", bgr)
            key = cv2.waitKey(1) & 0xFF
            self._keys.clear()  # fresh each frame

            if key == 27: self.running = False
            elif key == ord(' '): self.frozen = not self.frozen
            elif key == ord('r'):
                self.cam = FirstPersonCamera((0,-800,400), yaw=np.radians(10), pitch=np.radians(-8))
            elif key == ord('w'): self._keys.add('w')
            elif key == ord('a'): self._keys.add('a')
            elif key == ord('s'): self._keys.add('s')
            elif key == ord('d'): self._keys.add('d')
            elif key == ord('q'): self._keys.add('q')
            elif key == ord('e'): self._keys.add('e')

        cv2.destroyAllWindows()
        print(f"\nClosed. {self._frame} frames.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--particles", type=int, default=50000)
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=768)
    a = p.parse_args()
    Viewer(a.width, a.height, a.particles).run()

if __name__ == "__main__":
    sys.exit(main())
