"""Oak tree demo — procedural Quercus robur rendered as Gaussian splats."""
import sys, math, numpy as np
import matplotlib; matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from ParticleEngine.core import ParticleSimulator
from ParticleEngine.control_vars import default_physics_registry
from ParticleEngine.gpu_pipeline import FullGPUPipeline
from ParticleEngine.camera import FirstPersonCamera
from ParticleEngine.kernels.standard import gravity_kernel, box_boundary_kernel
from ParticleEngine.tree_trainer import TreeParams


def build_oak(sim, params: TreeParams):
    A = 19
    np.random.seed(params.seed)

    def trunk(start, height, base_radius):
        for i in range(200):
            t = i/199; y = start[1] + height*t
            r = base_radius*(1-t*0.8)*(1+params.trunk_gnarl*math.sin(t*12))
            x = start[0]+math.sin(t*5)*r*0.3; z = start[2]+math.cos(t*7)*r*0.3
            for _ in range(5):
                ox=np.random.uniform(-r,r); oy=np.random.uniform(-r,r); oz=np.random.uniform(-r,r)
                if ox*ox+oy*oy+oz*oz < r*r:
                    sim.spawn(1,'dust',(x+ox,y+oy,z+oz),0,mass=1e9,life=-1,
                              color=(0.25,0.15,0.07,0.9),size=2.5+r*0.2)
        return (start[0],start[1]+height*0.7,start[2]), r*0.3

    def branch(start, direction, length, radius, depth):
        if length < 15 or radius < 0.5: return
        end = (start[0]+direction[0]*length, start[1]+direction[1]*length, start[2]+direction[2]*length)
        n = max(5, int(length/3))
        for i in range(n):
            t=i/(n-1); x=start[0]+direction[0]*length*t; y=start[1]+direction[1]*length*t; z=start[2]+direction[2]*length*t
            r=radius*(1-t*0.7)
            for _ in range(3):
                ox=np.random.uniform(-r,r); oy=np.random.uniform(-r,r); oz=np.random.uniform(-r,r)
                sim.spawn(1,'dust',(x+ox,y+oy,z+oz),0,mass=1e9,life=-1,color=(0.3,0.18,0.08,0.9),size=1.5+r*0.3)
        if depth > 0:
            for b in range(2 if depth>1 else 3):
                t_split=0.4+b*0.2
                sx=start[0]+direction[0]*length*t_split; sy=start[1]+direction[1]*length*t_split; sz=start[2]+direction[2]*length*t_split
                h_angle=math.atan2(direction[0],direction[1])+np.random.uniform(-params.branch_spread,params.branch_spread)*(-1 if b%2==0 else 1)
                v_angle=np.random.uniform(params.branch_angle_min,params.branch_angle_max)
                nd=(math.sin(v_angle)*math.sin(h_angle),math.sin(v_angle)*math.cos(h_angle),math.cos(v_angle))
                branch((sx,sy,sz),nd,length*0.5,radius*0.55,depth-1)
        if depth <= 1:
            for _ in range(params.leaf_density):
                lx=end[0]+np.random.uniform(-40,40); ly=end[1]+np.random.uniform(-40,40); lz=end[2]+np.random.uniform(-40,40)
                g=np.random.uniform(0.3,0.8)
                sim.spawn(1,'social',(lx,ly,lz),np.random.uniform(10,30),mass=1e9,life=-1,color=(0.05,g,0.08,0.9),size=np.random.uniform(params.leaf_size_min,params.leaf_size_max))
            for _ in range(params.acorn_density):
                ax=end[0]+np.random.uniform(-15,15); ay=end[1]+np.random.uniform(-15,15); az=end[2]+np.random.uniform(-15,15)
                sim.spawn(1,'sand',(ax,ay,az),5,mass=1e9,life=-1,color=(0.5,0.35,0.15,0.9),size=np.random.uniform(1.5,3))

    (sp, r) = trunk(sim, (0,-400,0), params.trunk_height, params.trunk_radius)
    for i in range(params.num_main_branches):
        ang = i*2*math.pi/params.num_main_branches + np.random.uniform(-0.3,0.3)
        va = np.random.uniform(params.branch_angle_min, params.branch_angle_max)
        nd = (math.sin(va)*math.cos(ang), math.sin(va)*math.sin(ang), math.cos(va))
        branch(sim, sp, nd, params.branch_length, r, params.branch_depth)

    for _ in range(params.root_count):
        ang=np.random.uniform(0,2*math.pi); dist=np.random.uniform(20,60)
        sim.spawn(1,'dust',(math.cos(ang)*dist,-400,math.sin(ang)*dist),3,mass=1e9,life=-1,color=(0.2,0.12,0.05,0.9),size=2)
    for _ in range(params.moss_count):
        sim.spawn(1,'sand',(np.random.uniform(-300,300),-400,np.random.uniform(-300,300)),np.random.uniform(3,12),mass=1e9,life=-1,color=(0.12,0.35,0.1,0.7),size=np.random.uniform(1,3))
    for _ in range(params.atmosphere_count):
        sim.spawn(1,'atmosphere',(np.random.uniform(-500,500),np.random.uniform(-350,500),np.random.uniform(-500,500)),np.random.uniform(20,60),mass=1e9,life=-1,color=(0.25,0.55,0.3,0.3),size=np.random.uniform(2,5))


def main():
    sim = ParticleSimulator(150000)
    reg = default_physics_registry()
    sim.add_kernel(gravity_kernel,'g'); sim.add_kernel(box_boundary_kernel,'b')
    reg.set('gravity',(0,0,0)); reg.set('boundary_min',(-5000,)*3); reg.set('boundary_max',(5000,)*3)

    params = TreeParams.random()
    params.trunk_height = 300; params.trunk_radius = 14
    params.num_main_branches = 5; params.leaf_density = 40
    build_oak(sim, params)

    for _ in range(3): sim.step(1/60, reg.snapshot())
    print(f'Oak: {sim.count} particles')

    pipe = FullGPUPipeline(base_scale=0.7)
    pipe.upload(sim._data[:sim.count])

    fig, ax = plt.subplots(figsize=(8, 10)); plt.ion()
    fig.canvas.manager.set_window_title('Chimera — Oak Tree')
    W, H = 700, 900
    cam = FirstPersonCamera((0, -1100, 150), yaw=math.pi/2, pitch=0.12)

    def look_at(cam, target, oa, el, d):
        cam.position[0]=target[0]+math.cos(oa)*math.cos(el)*d
        cam.position[1]=target[1]+math.sin(oa)*math.cos(el)*d
        cam.position[2]=target[2]+math.sin(el)*d
        dx=target[0]-cam.position[0]; dy=target[1]-cam.position[1]; dz=target[2]-cam.position[2]
        cam.yaw=math.atan2(dy,dx); cam.pitch=math.atan2(dz,math.sqrt(dx*dx+dy*dy))

    p=cam.params(W,H); img=pipe.render_from_gpu(cam,p); im=ax.imshow(img); ax.axis('off')
    txt=ax.text(10,20,'',color='white',fontsize=12,bbox=dict(facecolor='black',alpha=0.5))
    ax.set_title('Oak Tree — Quercus robur', fontsize=14)

    times, angle, running = [], 0, True
    def on_close(e):
        nonlocal running; running = False
    fig.canvas.mpl_connect('close_event', on_close)

    print('Orbiting — close window to quit')
    while running:
        t0=time.time(); angle+=0.005; el=0.15*math.sin(angle*0.4)
        look_at(cam,(0,-50,180),angle,el,1000)
        pipe.step_particles(1/60,reg.snapshot())
        img=pipe.render_from_gpu(cam,cam.params(W,H)); im.set_data(img)
        times.append(time.time()-t0)
        if len(times)>30: times.pop(0)
        fps=len(times)/sum(times) if times else 0
        txt.set_text(f'FPS:{fps:.0f} | {pipe._n} pts | Oak')
        fig.canvas.draw_idle(); plt.pause(0.001)
    plt.close()

if __name__ == "__main__":
    import time
    main()
