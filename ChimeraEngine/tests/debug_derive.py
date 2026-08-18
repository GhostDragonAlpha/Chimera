"""Minimal debug for derive kernel buffer corruption."""
import numpy as np
from numba import cuda

# Recreate the derive kernel inline to test it standalone
@cuda.jit
def _derive_buffer_kernel(
    pos: np.ndarray,        # (N, 3) float32
    scale_base: np.ndarray, # (N, 3) float32
    color_base: np.ndarray, # (N, 3) float32
    opacity_base: np.ndarray,# (N,) float32
    mass: np.ndarray,       # (N,) float32
    charge: np.ndarray,     # (N,) float32
    lensing_sx: np.ndarray, # (L,) float32
    lensing_sy: np.ndarray, # (L,) float32
    lensing_str: np.ndarray,# (L,) float32
    buffer: np.ndarray,     # (N, 28) float32
    brightness_gain: float,
    N: int, L: int,
    screen_w: int,
    screen_h: int,
):
    i = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    if i >= N:
        return
    
    sx = scale_base[i, 0]
    sy = scale_base[i, 1]
    sz = scale_base[i, 2]
    volume = sx * sy * sz
    density = mass[i] / (volume + 1e-12)
    
    rest_volume = sx * sy * sz
    vol_ratio = volume / (rest_volume + 1e-12)
    brightness = brightness_gain / max(vol_ratio, 0.01)
    
    # Pre-rasterization lensing: warp position toward nearest lensing center
    px = pos[i, 0]
    py = pos[i, 1]
    pz = pos[i, 2]
    
    if L > 0:
        sx_screen = float(screen_w) / 2.0 + px * 50.0
        sy_screen = float(screen_h) / 2.0 - py * 50.0
        
        deflect_x, deflect_y = 0.0, 0.0
        for ci in range(L):
            cx = lensing_sx[ci]
            cy = lensing_sy[ci]
            st = lensing_str[ci] * 30.0
            dx = sx_screen - cx
            dy = sy_screen - cy
            dist_sq = dx*dx + dy*dy + 1.0
            deflect_x += st * dx / dist_sq
            deflect_y += st * dy / dist_sq
        
        px += (deflect_x - float(screen_w) / 2.0) / 50.0
        py -= (deflect_y - float(screen_h) / 2.0) / 50.0
    
    base = i * 28
    buffer[base + 0] = px
    buffer[base + 1] = py
    buffer[base + 2] = pz
    buffer[base + 3] = 0.0
    buffer[base + 4] = 0.0
    buffer[base + 5] = 0.0
    buffer[base + 6] = sx
    buffer[base + 7] = sy
    buffer[base + 8] = sz
    buffer[base + 9] = 0.0
    buffer[base + 10] = 0.0
    buffer[base + 11] = 0.0
    buffer[base + 12] = 1.0
    
    cr = color_base[i, 0] * brightness
    cg = color_base[i, 1] * brightness
    cb = color_base[i, 2] * brightness
    buffer[base + 13] = min(cr, 1.0)
    buffer[base + 14] = min(cg, 1.0)
    buffer[base + 15] = min(cb, 1.0)
    
    buffer[base + 16] = opacity_base[i]
    buffer[base + 17] = density
    for k in range(18, 28):
        buffer[base + k] = 0.0


def main():
    N = 20
    L = 0
    
    # Create simple test data
    pos = np.zeros((N, 3), dtype=np.float32)
    for i in range(N):
        pos[i] = [i * 0.1, i * 0.2, i * 0.3]
    
    mass = np.ones(N, dtype=np.float32)
    charge = np.zeros(N, dtype=np.float32)
    scale_base = np.ones((N, 3), dtype=np.float32) * 0.1
    color_base = np.ones((N, 3), dtype=np.float32) * 0.5
    opacity_base = np.full(N, 0.8, dtype=np.float32)
    
    buffer = np.zeros((N, 28), dtype=np.float32)
    
    # Upload to device
    d_pos = cuda.to_device(pos)
    d_mass = cuda.to_device(mass)
    d_charge = cuda.to_device(charge)
    d_scale_base = cuda.to_device(scale_base)
    d_color_base = cuda.to_device(color_base)
    d_opacity_base = cuda.to_device(opacity_base)
    d_buffer = cuda.to_device(buffer.copy())
    d_lensing_sx = cuda.device_array(L, dtype=np.float32) if L > 0 else None
    d_lensing_sy = cuda.device_array(L, dtype=np.float32) if L > 0 else None
    d_lensing_str = cuda.device_array(L, dtype=np.float32) if L > 0 else None
    
    # Launch kernel
    block = 64
    grid = max(1, (N + block - 1) // block)
    _derive_buffer_kernel[grid, block](
        d_pos, d_scale_base, d_color_base, d_opacity_base,
        d_mass, d_charge,
        d_lensing_sx, d_lensing_sy, d_lensing_str,
        d_buffer, 1.0, N, L, 2560, 1440
    )
    cuda.synchronize()
    
    # Read back
    result = d_buffer.copy_to_host()
    print("Buffer rows:")
    for i in range(N):
        print(f"  row {i}: pos=({result[i,0]:.4f}, {result[i,1]:.4f}, {result[i,2]:.4f}) expected ({pos[i,0]:.4f}, {pos[i,1]:.4f}, {pos[i,2]:.4f})")
    
    # Check if correct
    for i in range(N):
        assert abs(result[i, 0] - pos[i, 0]) < 1e-5, f"Row {i}: x mismatch {result[i,0]} vs {pos[i,0]}"
        assert abs(result[i, 1] - pos[i, 1]) < 1e-5, f"Row {i}: y mismatch {result[i,1]} vs {pos[i,1]}"
        assert abs(result[i, 2] - pos[i, 2]) < 1e-5, f"Row {i}: z mismatch {result[i,2]} vs {pos[i,2]}"
    print("All checks passed!")


if __name__ == "__main__":
    main()
