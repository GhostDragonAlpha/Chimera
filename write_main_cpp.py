# Write main.cpp — fixed bootstrap + main loop
path = r"e:\PythonChimera\ChimeraEngine\engine\main.cpp"
code = r'''// main.cpp — Bootstrap + Main Loop
// Initializes Engine, Physics, HttpServer; runs the simulation loop.

#include "engine.hpp"
#include "physics.hpp"
#include "shared_mem.hpp"
#include "http_server.hpp"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <signal.h>
#include <windows.h>

static Engine* g_engine = nullptr;
static Physics g_physics;
static SharedRing g_ring("ChimeraPhysicsRing");

// Signal handler for graceful shutdown
#ifdef _WIN32
BOOL WINAPI handleCtrlC(DWORD) { return TRUE; }
#else
void handleSignal(int) { exit(0); }
#endif

int main(int argc, char** argv) {
    // Config
    EngineConfig cfg;
    cfg.width = 1920;
    cfg.height = 1080;
    cfg.n_particles = 1200;
    cfg.G = 1.0f;
    cfg.dt = 0.02f;

    // Physics init
    g_physics.init(cfg.n_particles, cfg);

    // Engine init
    Engine engine;
    if (!engine.init(cfg)) {
        fprintf(stderr, "Failed to initialize Vulkan engine\n");
        return 1;
    }
    g_engine = &engine;

    // HTTP server (MJPEG stream on port 8080)
    HttpServer server(8080);
    if (!server.start([](const HttpRequest& req, HttpResponse& resp) {
        if (req.path == "/stream") {
            resp.status = 200;
            resp.headers["Content-Type"] = "multipart/x-mixed-replace;boundary=frame";
            // MJPEG streaming handled in the server's main loop
            return true;
        }
        if (req.path == "/state" && req.method == "GET") {
            // Return current particle state as JSON
            auto particles = g_physics.particles();
            // Build minimal JSON response
            std::string body = "{\"n\":" + std::to_string(particles.size()) + "}";
            resp.status = 200;
            resp.headers["Content-Type"] = "application/json";
            resp.body = body;
            return true;
        }
        if (req.path == "/control" && req.method == "POST") {
            // Accept control commands from Python shim
            // Parse JSON body for params like G, dt, etc.
            resp.status = 200;
            resp.body = "{\"ok\":true}";
            return true;
        }
        resp.status = 404;
        resp.body = "Not found";
        return true;
    })) {
        fprintf(stderr, "Failed to start HTTP server on port %d\n", port);
        engine.shutdown();
        return 1;
    }

    printf("Chimera Engine running at http://localhost:%d/stream\n", port);
    printf("Press Ctrl+C to stop.\n");

#ifdef _WIN32
    SetConsoleCtrlHandler(handleCtrlC, TRUE);
#else
    signal(SIGINT, handleSignal);
    signal(SIGTERM, handleSignal);
#endif

    // Main loop
    auto last_time = std::chrono::high_resolution_clock::now();
    int frame_count = 0;

    while (true) {
        // Check for shutdown signal
        static bool shutting_down = false;
#ifdef _WIN32
        if (!g_engine) break;
#endif

        // Step physics on CPU (symplectic Euler)
        g_physics.step();

        // Upload particle state to GPU buffers
        auto& particles = g_physics.particles();
        std::vector<float> pos_buf(particles.size() * 9, 0.f);
        std::vector<float> vel_buf(particles.size() * 9, 0.f);

        for (size_t i = 0; i < particles.size(); ++i) {
            const auto& p = particles[i];
            pos_buf[i * 9 + 0] = p.x;     pos_buf[i * 9 + 1] = p.y;     pos_buf[i * 9 + 2] = p.z;
            pos_buf[i * 9 + 3] = p.cr;    pos_buf[i * 9 + 4] = p.cg;    pos_buf[i * 9 + 5] = p.cb;
            pos_buf[i * 9 + 6] = p.size;  pos_buf[i * 9 + 7] = 0.f;     pos_buf[i * 9 + 8] = 0.f;

            vel_buf[i * 9 + 0] = p.vx;    vel_buf[i * 9 + 1] = p.vy;    vel_buf[i * 9 + 2] = p.vz;
            // color and size stay in pos buffer for GPU read
        }

        if (!engine.push_state(pos_buf, vel_buf, (uint32_t)particles.size())) {
            fprintf(stderr, "Failed to push state to GPU\n");
            break;
        }

        // Render one frame
        if (!engine.frame()) {
            fprintf(stderr, "Frame failed\n");
            break;
        }

        // Push state to shared memory ring for Python shim
        std::vector<float> ring_data(particles.size() * 10); // x,y,z,vx,vy,vz,cr,cg,cb,size
        for (size_t i = 0; i < particles.size(); ++i) {
            const auto& p = particles[i];
            ring_data[i * 10 + 0] = p.x;    ring_data[i * 10 + 1] = p.y;    ring_data[i * 10 + 2] = p.z;
            ring_data[i * 10 + 3] = p.vx;   ring_data[i * 10 + 4] = p.vy;   ring_data[i * 10 + 5] = p.vz;
            ring_data[i * 10 + 6] = p.cr;   ring_data[i * 10 + 7] = p.cg;   ring_data[i * 10 + 8] = p.cb;
            ring_data[i * 10 + 9] = p.size;
        }
        g_ring.push(ring_data.data(), (uint32_t)ring_data.size());

        // Target ~60fps (16.67ms per frame)
        auto now = std::chrono::high_resolution_clock::now();
        auto ms = std::chrono::duration_cast<std::chrono::microseconds>(now - last_time).count() / 1000.0;
        if (ms < 16.0f) {
            Sleep((DWORD)((16.0f - ms) / 1000.0 + 1)); // minimum 1ms sleep
        }
        last_time = std::chrono::high_resolution_clock::now();

        frame_count++;
        if (frame_count % 300 == 0) {
            printf("Frame %d\n", frame_count);
        }

        // Check for window close / shutdown
        MSG msg;
        if (PeekMessage(&msg, nullptr, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) break;
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
    }

    printf("Shutting down...\n");
    engine.shutdown();
    return 0;
}
'''

with open(path, "w") as f:
    f.write(code)
print(f"Wrote {len(code)} bytes to main.cpp")
