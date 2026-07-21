"""Train SplatVAE on procedural oak tree clusters, then generate new trees."""
import sys, math, numpy as np, torch
from pathlib import Path
from ParticleEngine.tree_trainer import TreeParams
from WorldModel.model import SplatVAE, splat_cloud_to_tensor, tensor_to_splat_cloud
from WorldModel.splat_io import _build_covariances

OUT = Path("WorldModel/training_data")
OUT.mkdir(parents=True, exist_ok=True)
N_SPLATS = 2048
N_TREES = 200
LATENT_DIM = 64
EPOCHS = 300
BATCH_SIZE = 16

def generate_oak_splat_cloud(params: TreeParams) -> np.ndarray:
    """Generate a dense oak cloud with exactly N_SPLATS splats."""
    np.random.seed(params.seed)
    positions, colors, opacities, scales = [], [], [], []
    
    def branch(sx,sy,sz, dx,dy,dz, L, r, depth, max_d):
        ex,ey,ez = sx+dx*L, sy+dy*L, sz+dz*L
        n = max(10, int(L * 2))
        for i in range(n):
            t = i/(n-1) if n>1 else 0.5
            x,y,z = sx+dx*L*t, sy+dy*L*t, sz+dz*L*t
            rr = r*(1-t*0.6)
            for _ in range(max(1, int(rr/2))):
                positions.append([x+np.random.normal(0,rr/3), y+np.random.normal(0,rr/3), z+np.random.normal(0,rr/3)])
                colors.append([0.32, 0.16, 0.07])
                opacities.append(0.9)
                scales.append([rr*0.7]*3)
        if depth >= max_d:
            for _ in range(params.leaf_density):
                lx,ly,lz = ex+np.random.normal(0,35), ey+np.random.normal(0,35), ez+np.random.normal(0,35)
                positions.append([lx,ly,lz])
                colors.append([0.06, np.random.uniform(0.4,0.8), 0.08])
                opacities.append(np.random.uniform(0.7,0.95))
                s = np.random.uniform(1.5, 4); scales.append([s,s,s])
            return
        n_br = 3 if depth < 2 else (2 if depth < 3 else 1)
        for b in range(n_br):
            t_split = 0.3 + b*0.25
            bx,by,bz = sx+dx*L*t_split, sy+dy*L*t_split, sz+dz*L*t_split
            ha = math.atan2(dx,dy)+np.random.uniform(-0.6,0.6)*(-1 if b%2==0 else 1)
            va = np.random.uniform(params.branch_angle_min, params.branch_angle_max)
            nd = (math.sin(va)*math.sin(ha), math.sin(va)*math.cos(ha), math.cos(va))
            branch(bx,by,bz, nd[0],nd[1],nd[2], L*0.55, r*0.55, depth+1, max_d)
    
    branch(0,-200,0, 0,0.2,0.8, params.trunk_height*0.4, params.trunk_radius, 0, params.branch_depth)
    
    # Pad or truncate to exactly N_SPLATS
    data = np.zeros((N_SPLATS, 10), dtype=np.float32)
    n = min(len(positions), N_SPLATS)
    data[:n, 0:3] = positions[:n]  # xyz
    data[:n, 3:6] = np.clip(colors[:n], 0, 1)  # rgb
    data[:n, 6] = opacities[:n]  # opacity
    data[:n, 7:10] = np.log(np.maximum(scales[:n], 1e-8))  # log scale
    return data


def train():
    print(f"Generating {N_TREES} training trees ({N_SPLATS} splats each)...")
    dataset = []
    for i in range(N_TREES):
        params = TreeParams.random()
        data = generate_oak_splat_cloud(params)
        data[:, 0:3] -= data[:, 0:3].mean(axis=0)  # center
        ext = np.linalg.norm(data[:, 0:3].max(axis=0) - data[:, 0:3].min(axis=0)) or 1
        data[:, 0:3] /= ext  # normalize extent
        dataset.append(data)
        if i % 50 == 0: print(f"  {i}/{N_TREES}")
    
    dataset = np.stack(dataset)  # (N_TREES, N_SPLATS, 10)
    np.save(OUT / "oak_training.npy", dataset)
    print(f"Saved {OUT}/oak_training.npy ({dataset.shape})")
    
    # Train VAE
    print(f"\nTraining SplatVAE ({EPOCHS} epochs)...")
    model = SplatVAE(num_splats=N_SPLATS, point_dim=10, latent_dim=LATENT_DIM)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    data_t = torch.tensor(dataset, dtype=torch.float32)
    n_batches = N_TREES // BATCH_SIZE
    
    for epoch in range(EPOCHS):
        idx = torch.randperm(N_TREES)
        total_loss = 0
        for b in range(n_batches):
            batch = data_t[idx[b*BATCH_SIZE:(b+1)*BATCH_SIZE]]
            recon, mu, logvar = model(batch)
            recon_loss = torch.nn.functional.mse_loss(recon, batch, reduction='sum')
            kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
            loss = recon_loss + 0.0001 * kl_loss
            optimizer.zero_grad(); loss.backward(); optimizer.step()
            total_loss += loss.item()
        if epoch % 30 == 0:
            print(f"  Epoch {epoch}: loss={total_loss/n_batches:.2f}")
    
    torch.save(model.state_dict(), OUT / "oak_vae.pt")
    print(f"Saved {OUT}/oak_vae.pt")
    
    # Generate samples
    print("\nGenerating 5 new trees...")
    model.eval()
    with torch.no_grad():
        for i in range(5):
            z = torch.randn(1, LATENT_DIM)
            gen = model.decoder(z).numpy()[0]  # (N_SPLATS, 10)
            # Un-normalize scales
            gen[:, 7:10] = np.exp(gen[:, 7:10])
            gen[:, 0:3] *= 200  # scale up from unit extent
            
            # Save as .ply
            from WorldModel.splat_io import SplatCloud, save_ply
            cloud = SplatCloud(
                positions=gen[:, 0:3].astype(np.float32),
                colors=np.clip(gen[:, 3:6], 0, 1).astype(np.float32),
                opacities=np.clip(gen[:, 6], 0, 1).astype(np.float32),
                scales=gen[:, 7:10].astype(np.float32),
                rotations=np.tile(np.array([0.,0.,0.,1.], dtype=np.float32), (N_SPLATS, 1)),
            )
            cov = _build_covariances(cloud.scales, cloud.rotations)
            cloud.covariances_3x3 = cov
            fname = OUT / f"generated_tree_{i}.ply"
            save_ply(cloud, str(fname))
            print(f"  {fname} ({cloud.count} splats, extent={np.linalg.norm(cloud.positions.max(0)-cloud.positions.min(0)):.0f})")
    
    return model

if __name__ == "__main__":
    train()
