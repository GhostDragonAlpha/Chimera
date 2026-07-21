"""Tree of Life - permanent demo. python -m ParticleEngine.tree_of_life"""
import warnings, os
warnings.filterwarnings('ignore')
os.environ['NUMBA_CUDA_LOG_LEVEL'] = '0'
import matplotlib; matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np, math, time, sys
sys.path.insert(0, 'E:/PythonChimera')
from ParticleEngine.gpu_pipeline import FullGPUPipeline
from ParticleEngine.camera import FirstPersonCamera
from WorldModel.splat_io import _build_covariances
from WorldModel.clay import OAK_TREE


def main():
    print("Growing Tree of Life...")
    
    # Mold the clay
    OAK_TREE.set(
        trunk_height=350, trunk_radius=16, trunk_gnarl=0.25,
        num_branches=5, branch_length=160,
        branch_angle_min=0.3, branch_angle_max=1.0,
        branch_spread=0.7, branch_depth=4,
        leaf_density=60, leaf_size_min=3, leaf_size_max=10,
        canopy_roundness=0.8, root_spread=0.8,
        wind_response=0.05, light_seeking=0.9,
    )
    
    # Physics generates the form
    cloud = OAK_TREE.generate()
    tree_pos = cloud.positions.astype(np.float32) * 3
    tree_col = np.clip(cloud.colors.astype(np.float32) * 3, 0, 1)
    tree_opa = np.clip(cloud.opacities.astype(np.float32), 0, 1)
    tree_sca = np.clip(cloud.scales.astype(np.float32) * 3, 0.1, 25)
    tree_rot = np.tile(np.array([0., 0., 0., 1.], dtype=np.float32), (len(tree_pos), 1))

    # Build the world around it
    all_pos, all_col, all_opa, all_sca, all_rot = [], [], [], [], []
    
    # Tree
    for i in range(len(tree_pos)):
        all_pos.append(tree_pos[i]); all_col.append(tree_col[i])
        all_opa.append(tree_opa[i]); all_sca.append(tree_sca[i]); all_rot.append(tree_rot[i])

    tz = tree_pos[:, 2].min()
    
    # Ground
    for i in range(80000):
        a = np.random.uniform(0, 2*math.pi); d = np.random.exponential(200)
        t = min(d/500, 1); g = np.interp(t, [0, 0.5, 1], [0.4, 0.25, 0.12])
        r = np.interp(t, [0, 0.5, 1], [0.1, 0.2, 0.3])
        all_pos.append([math.cos(a)*d, math.sin(a)*d, tz+np.random.uniform(-5, 2)])
        all_col.append([r, g, 0.08]); all_opa.append(np.random.uniform(0.4, 0.8))
        all_sca.append([np.random.uniform(1, 4)]*3); all_rot.append([0, 0, 0, 1])

    # Grass
    for i in range(30000):
        a = np.random.uniform(0, 2*math.pi); d = np.random.exponential(60)
        all_pos.append([math.cos(a)*d, math.sin(a)*d, tz+np.random.uniform(0, 15)])
        all_col.append([0.1, 0.55+np.random.uniform(0, 0.25), 0.1])
        all_opa.append(np.random.uniform(0.5, 0.9)); all_sca.append([1, 1.5, 1]); all_rot.append([0, 0, 0, 1])

    # Atmosphere
    for i in range(40000):
        all_pos.append([np.random.uniform(-800, 800), np.random.uniform(-800, 800), tz+100+np.random.exponential(400)])
        all_col.append([0.35, 0.55, 0.85]); all_opa.append(np.random.uniform(0.01, 0.05))
        all_sca.append([15, 15, 15]); all_rot.append([0, 0, 0, 1])

    # Light rays
    for i in range(15000):
        all_pos.append([np.random.uniform(-400, 400), np.random.uniform(-400, 400), tz+np.random.uniform(300, 800)])
        all_col.append([1.0, 0.95, 0.7]); all_opa.append(np.random.uniform(0.005, 0.02))
        all_sca.append([30, 30, 50]); all_rot.append([0, 0, 0, 1])

    pos = np.array(all_pos, dtype=np.float32)
    col = np.clip(np.array(all_col, dtype=np.float32), 0, 1)
    opa = np.array(all_opa, dtype=np.float32)
    sca = np.array(all_sca, dtype=np.float32)
    rot = np.array(all_rot, dtype=np.float32)

    # GPU render
    pipe = FullGPUPipeline(base_scale=0.4)
    cov = _build_covariances(sca, rot)
    center = pos.mean(axis=0)

    fig, ax = plt.subplots(figsize=(18, 10))
    plt.ion()
    fig.canvas.manager.set_window_title('TREE OF LIFE - Chimera Engine')
    W, H = 1800, 1000

    cam = FirstPersonCamera((center[0], center[1]-400, center[2]+30), yaw=math.pi/2, pitch=-0.1)

    def look_at(c, t, oa, el, d):
        c.position[0] = t[0] + math.cos(oa)*math.cos(el)*d
        c.position[1] = t[1] + math.sin(oa)*math.cos(el)*d
        c.position[2] = t[2] + math.sin(el)*d
        dx = t[0]-c.position[0]; dy = t[1]-c.position[1]; dz = t[2]-c.position[2]
        c.yaw = math.atan2(dy, dx)
        c.pitch = math.atan2(dz, math.sqrt(dx*dx+dy*dy))

    img = pipe.render_splats(pos, cov, col, opa, cam, cam.params(W, H))
    im = ax.imshow(img); ax.axis('off')
    txt = ax.text(10, 20, '', color='white', fontsize=13, bbox=dict(facecolor='black', alpha=0.5))
    ax.set_title('Tree of Life', fontsize=16)

    running = [True]
    fig.canvas.mpl_connect('close_event', lambda e: running.__setitem__(0, False))
    
    times = []; angle = 0
    print(f"  {len(pos):,} particles | 1800x1000 | Close window to quit")
    
    while running[0]:
        t0 = time.time(); angle += 0.003
        look_at(cam, center, angle, 0.08*math.sin(angle*0.2), 400)
        img = pipe.render_splats(pos, cov, col, opa, cam, cam.params(W, H))
        im.set_data(img)
        times.append(time.time()-t0)
        if len(times) > 30: times.pop(0)
        fps = len(times)/sum(times) if times else 0
        txt.set_text(f'FPS:{fps:.0f} | {len(pos):,} particles | Tree of Life')
        fig.canvas.draw_idle()
        plt.pause(0.001)

    plt.close()


if __name__ == '__main__':
    main()
