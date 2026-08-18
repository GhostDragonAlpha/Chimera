#pragma once
#include <vector>
#include <cstdint>
#include "shared_mem.hpp"

struct Particle {
    float x, y, z;
    float vx, vy, vz;
    float cr, cg, cb;
    float size;
};

struct EngineConfig;  // forward decl to avoid circular include

class Physics {
public:
    void init(int n, const struct EngineConfig& cfg);
    void set_params(float G, float rw, float rb, float rc,
                    float kw, float kb, float gamma_w, float dt);
    void step();                                        // run one compute dispatch
    bool push_state_to_ring(const char* ring_name);     // write state to shared mem

    std::vector<Particle>& particles() { return parts_; }
    const std::vector<Particle>& particles() const { return parts_; }
    int count() const { return static_cast<int>(parts_.size()); }

private:
    std::vector<float> pos_, vel_, acc_; // flat [x,y,z] per particle, interleaved
    std::vector<Particle> parts_;
    float G_=1.0f, rw_=0.5f, rb_=2.0f, rc_=3.0f;
    float kw_=100.0f, kb_=10.0f, gamma_w_=5.0f, dt_=0.02f;
};
