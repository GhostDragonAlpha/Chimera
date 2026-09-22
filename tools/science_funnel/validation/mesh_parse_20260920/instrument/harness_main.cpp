// harness_main.cpp -- mesh_parse_20260920 lane instrument driver.
// Times the SHIPPED parser's logic (a timer-instrumented copy, logic
// byte-identical) on a given source file: 'O' OBJ subset or 'G' glTF/GLB.
// No HTTP, no engine, no server: the P-COST derivation numbers come from
// here. The body bytes written with --out are the exact full-mesh-format
// payload import_mesh produces -- the parity fence compares 'O' vs 'G'.
//
// usage: mesh_instr.exe <kind> <source-file> [--repeat N] [--out FILE]
//                       [--body-sha-expected HEX]
#include "importer.hpp"

#define _CRT_SECURE_NO_WARNINGS

#include <chrono>
#include <cstdio>
#include <cstring>
#include <string>

int main(int argc, char** argv) {
    if (argc < 3) {
        std::fprintf(stderr,
                     "usage: mesh_instr <kind O|G> <source> [--repeat N] "
                     "[--out FILE]\n");
        return 2;
    }
    const char kind = argv[1][0];
    const char* path = argv[2];
    int repeat = 1;
    const char* out_path = nullptr;
    for (int i = 3; i < argc; ++i) {
        if (i + 1 < argc && std::strcmp(argv[i], "--repeat") == 0) {
            repeat = std::atoi(argv[++i]);
        } else if (i + 1 < argc && std::strcmp(argv[i], "--out") == 0) {
            out_path = argv[++i];
        }
    }
    if (kind != 'O' && kind != 'G') {
        std::fprintf(stderr, "kind must be O or G\n");
        return 2;
    }

    FILE* f = std::fopen(path, "rb");
    if (!f) { std::fprintf(stderr, "cannot open %s\n", path); return 2; }
    std::string src;
    {
        char buf[1 << 16];
        size_t got;
        while ((got = std::fread(buf, 1, sizeof(buf), f)) > 0)
            src.append(buf, got);
        std::fclose(f);
    }
    std::printf("source: %s (%.2f MB) kind %c\n",
                path, (double)src.size() / 1048576.0, kind);

    std::string first_body;
    double first_wall_ms = 0.0;
    for (int rep = 0; rep < repeat; ++rep) {
        importer::Stats st;
        std::string body, err;
        const auto t0 = std::chrono::steady_clock::now();
        const bool ok = importer::import_mesh(kind, src, body, st, err);
        const auto t1 = std::chrono::steady_clock::now();
        const double wall_ms =
            std::chrono::duration<double, std::milli>(t1 - t0).count();
        if (!ok) {
            std::printf("rep %d REFUSED: %s\n", rep, err.c_str());
            return 1;
        }
        if (rep == 0) {
            first_body = body;
            first_wall_ms = wall_ms;
        } else {
            const bool same = body == first_body;
            std::printf("rep %d identical_to_first=%s\n", rep,
                        same ? "true" : "FALSE");
        }

        const importer::PhaseReport ph = importer::last_phases();
        std::printf("rep %d wall_ms=%.1f (%.2f s) body_bytes=%zu\n",
                    rep, wall_ms, wall_ms / 1000.0, body.size());
        std::printf("  stats: verts=%u tris=%u volume=%.12g ymin=%.9g "
                    "ymax=%.9g winding_flipped=%s\n",
                    st.verts, st.tris, st.volume, st.ymin, st.ymax,
                    st.winding_flipped ? "true" : "false");
        std::printf("  finish_total_ms=%.1f\n", ph.finish_total_ms);
        for (int i = 0; i < ph.n; ++i)
            std::printf("  phase %-18s %10.1f ms\n", ph.names[i], ph.ms[i]);
    }
    if (out_path) {
        FILE* o = std::fopen(out_path, "wb");
        if (!o) { std::fprintf(stderr, "cannot write %s\n", out_path); return 2; }
        std::fwrite(first_body.data(), 1, first_body.size(), o);
        std::fclose(o);
        std::printf("first rep body written: %s (%zu bytes, wall %.1f ms)\n",
                    out_path, first_body.size(), first_wall_ms);
    }
    return 0;
}
