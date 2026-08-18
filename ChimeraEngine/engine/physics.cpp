#include "physics.hpp"
#include "engine.hpp"
#include <random>
#include <algorithm>
#include <iostream>

void Physics::init(int n, const EngineConfig& cfg) {
    parts_.resize(n);
    pos_.resize(n * 4, 0.0f);
    vel_.resize(n * 4, 0.0f);
    acc_.resize(n * 4, 0.0f);

    G_      = cfg.G;
    rw_     = cfg.rw;
    rb_     = cfg.rb;
    rc_     = cfg.rc;
    kw_     = cfg.kw;
    kb_     = cfg.kb;
    gamma_w_= cfg.gamma_w;
    dt_     = cfg.dt;

    std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(-5.0f, 5.0f);
    for (int i = 0; i < n; ++i) {
        parts_[i].x = dist(rng);
        parts_[i].y = dist(rng);
        parts_[i].z = dist(rng);
        parts_[i].vx = dist(rng) * 0.1f;
        parts_[i].vy = dist(rng) * 0.1f;
        parts_[i].vz = dist(rng) * 0.1f;
        // Color: blue-ish with variation
        parts_[i].cr = 0.2f + 0.3f * static_cast<float>(rng()) / RAND_MAX;
        parts_[i].cg = 0.4f + 0.3f * static_cast<float>(rng()) / RAND_MAX;
        parts_[i].cb = 0.8f + 0.2f * static_cast<float>(rng()) / RAND_MAX;
        parts_[i].size = 1.5f + 2.0f * static_cast<float>(rng()) / RAND_MAX;

        pos_[i*4+0] = parts_[i].x;
        pos_[i*4+1] = parts_[i].y;
        pos_[i*4+2] = parts_[i].z;
        pos_[i*4+3] = 1.0f;
        vel_[i*4+0] = parts_[i].vx;
        vel_[i*4+1] = parts_[i].vy;
        vel_[i*4+2] = parts_[i].vz;
        vel_[i*4+3] = 0.0f;
    }
}

void Physics::set_params(float G, float rw, float rb, float rc,
                         float kw, float kb, float gamma_w, float dt) {
    G_ = G; rw_ = rw; rb_ = rb; rc_ = rc;
    kw_ = kw; kb_ = kb; gamma_w_ = gamma_w; dt_ = dt;
}

void Physics::step() {
    int n = static_cast<int>(parts_.size());
    if (n == 0) return;

    // Compute accelerations (CPU fallback — replaced by Vulkan compute in later pass)
    std::fill(acc_.begin(), acc_.end(), 0.0f);
    const float eps2 = 1e-6f;
    for (int i = 0; i < n; ++i) {
        float xi = pos_[i*4+0], yi = pos_[i*4+1], zi = pos_[i*4+2];
        float ax = 0.0f, ay = 0.0f, az = 0.0f;
        for (int j = 0; j < n; ++j) {
            if (i == j) continue;
            float dx = pos_[j*4+0] - xi;
            float dy = pos_[j*4+1] - yi;
            float dz = pos_[j*4+2] - zi;
            float r2 = dx*dx + dy*dy + dz*dz;
            float inv_r3 = 1.0f / ((r2 + eps2) * sqrtf(r2 + eps2));

            // Gravity
            ax += G_ * inv_r3 * dx;
            ay += G_ * inv_r3 * dy;
            az += G_ * inv_r3 * dz;

            // Contact resistance
            float r = sqrtf(r2);
            if (r < rc_) {
                if (r < rw_) {
                    float pen = rw_ - r;
                    float nx = dx/r, ny = dy/r, nz = dz/r;
                    float vrad = vel_[i*4+0]*nx + vel_[i*4+1]*ny + vel_[i*4+2]*nz;
                    ax += (kw_ * pen - gamma_w_ * vrad) * nx;
                    ay += (kw_ * pen - gamma_w_ * vrad) * ny;
                    az += (kw_ * pen - gamma_w_ * vrad) * nz;
                } else if (r < rb_) {
                    float stretch = r - rb_;
                    float nx = dx/r, ny = dy/r, nz = dz/r;
                    ax += kb_ * stretch * nx;
                    ay += kb_ * stretch * ny;
                    az += kb_ * stretch * nz;
                }
            }
        }
        acc_[i*4+0] = ax;
        acc_[i*4+1] = ay;
        acc_[i*4+2] = az;
    }

    // Integrate (symplectic Euler for speed)
    for (int i = 0; i < n; ++i) {
        vel_[i*4+0] += acc_[i*4+0] * dt_;
        vel_[i*4+1] += acc_[i*4+1] * dt_;
        vel_[i*4+2] += acc_[i*4+2] * dt_;
        pos_[i*4+0] += vel_[i*4+0] * dt_;
        pos_[i*4+1] += vel_[i*4+1] * dt_;
        pos_[i*4+2] += vel_[i*4+2] * dt_;
        // Copy back to particles
        parts_[i].x = pos_[i*4+0];
        parts_[i].y = pos_[i*4+1];
        parts_[i].z = pos_[i*4+2];
        parts_[i].vx = vel_[i*4+0];
        parts_[i].vy = vel_[i*4+1];
        parts_[i].vz = vel_[i*4+2];
    }
}

bool Physics::push_state_to_ring(const char* ring_name) {
    SharedRing ring;
    if (!ring.open(ring_name, false)) return false;
    for (const auto& p : parts_) {
        StatePacket pkt{};
        pkt.x = p.x; pkt.y = p.y; pkt.z = p.z;
        pkt.vx = p.vx; pkt.vy = p.vy; pkt.vz = p.vz;
        pkt.cr = p.cr; pkt.cg = p.cg; pkt.cb = p.cb;
        pkt.size = p.size;
        ring.push(pkt);
    }
    return true;
}
