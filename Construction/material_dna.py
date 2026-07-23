"""Rung 1 of cracking the material-DNA code: recover a KNOWN material's PBR genome
{albedo, roughness, metalness} from renders alone, by differentiable analysis-by-synthesis
on the GPU. We set the ground truth, render it under several lights/views, then optimize a
random guess until its render matches -- and check the recovered DNA equals the truth.
This is the inverse-rendering engine, proven where we know the answer."""
import numpy as np, torch
dev = "cuda"; PI = np.pi


def _n(x): return x / (x.norm(dim=-1, keepdim=True) + 1e-9)


def brdf(n, v, l, Lc, albedo, rough, metal):
    """Cook-Torrance GGX. Shapes broadcast to (...,3); rough/metal are (...,1)."""
    h = _n(v + l)
    NdotL = (n * l).sum(-1, keepdim=True).clamp(min=1e-4)
    NdotV = (n * v).sum(-1, keepdim=True).clamp(min=1e-4)
    NdotH = (n * h).sum(-1, keepdim=True).clamp(min=0)
    VdotH = (v * h).sum(-1, keepdim=True).clamp(min=0)
    a = rough * rough
    D = a * a / (PI * ((NdotH * NdotH * (a * a - 1) + 1) ** 2) + 1e-9)         # GGX distribution (roughness)
    k = (rough + 1) ** 2 / 8
    G1 = lambda x: x / (x * (1 - k) + k + 1e-9)
    G = G1(NdotV) * G1(NdotL)                                                  # geometry/shadowing (roughness)
    F0 = 0.04 * (1 - metal) + albedo * metal                                  # Fresnel base (metalness)
    F = F0 + (1 - F0) * (1 - VdotH).clamp(min=0) ** 5                          # Schlick Fresnel (view angle)
    spec = D * G * F / (4 * NdotV * NdotL + 1e-6)
    diff = (1 - metal) * albedo / PI                                          # metals have no diffuse
    return (diff + spec) * Lc * NdotL                                         # x cos(normal,light)


def hemi(m, seed):
    g = torch.Generator().manual_seed(seed); d = torch.randn(m, 3, generator=g); d[:, 2] = d[:, 2].abs() + 0.35
    return _n(d).to(dev)


VIEWS = hemi(8, 1)[:, None, :]                    # (8,1,3)
LIGHTS = hemi(6, 2)[None, :, :]                   # (1,6,3)
LC = (0.6 + 0.7 * torch.rand(6, 3, generator=torch.Generator().manual_seed(3))).to(dev)[None, :, :]
N = torch.tensor([[[0., 0, 1]]], device=dev)      # surface normal (1,1,3)


def render_all(albedo, rough, metal):
    return brdf(N, VIEWS, LIGHTS, LC, albedo, rough, metal)   # -> (8,6,3)


def recover(O, iters=2500):
    ra = torch.zeros(1, 1, 3, device=dev, requires_grad=True)
    rr = torch.zeros(1, 1, 1, device=dev, requires_grad=True)
    rm = torch.zeros(1, 1, 1, device=dev, requires_grad=True)
    opt = torch.optim.Adam([ra, rr, rm], lr=0.03)
    for _ in range(iters):
        alb = torch.sigmoid(ra); ro = 0.05 + 0.9 * torch.sigmoid(rr); me = torch.sigmoid(rm)
        loss = ((render_all(alb, ro, me) - O) ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    return torch.sigmoid(ra).detach().flatten(), (0.05 + 0.9 * torch.sigmoid(rr)).item(), torch.sigmoid(rm).item(), loss.item()


tests = {
    "OAK   (dielectric)": (torch.tensor([[[0.55, 0.32, 0.14]]], device=dev), 0.60, 0.00),
    "COPPER (metal)":      (torch.tensor([[[0.95, 0.64, 0.54]]], device=dev), 0.25, 1.00),
}
print(f"{'material':20}{'albedo (truth -> recovered)':44}{'rough':16}{'metal':14}")
print("-" * 92)
for name, (a_gt, r_gt, m_gt) in tests.items():
    O = render_all(a_gt, torch.tensor([[[r_gt]]], device=dev), torch.tensor([[[m_gt]]], device=dev))
    a_r, r_r, m_r, loss = recover(O)
    ag = a_gt.flatten().cpu().numpy(); ar = a_r.cpu().numpy()
    print(f"{name:20}[{ag[0]:.2f} {ag[1]:.2f} {ag[2]:.2f}] -> [{ar[0]:.2f} {ar[1]:.2f} {ar[2]:.2f}]   "
          f"{r_gt:.2f} -> {r_r:.2f}    {m_gt:.2f} -> {m_r:.2f}   (fit err {loss:.1e})")
