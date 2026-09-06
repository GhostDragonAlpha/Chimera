// Deliberately first: test that the engine header owns its dependencies.
#include "png_encoder.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

// Synthetic byte transport fixtures. This does not render or simulate a scene.
int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: capture_fixture OUTPUT_DIRECTORY\n";
        return 2;
    }
    try {
        const std::filesystem::path output(argv[1]);
        std::filesystem::create_directories(output);
        struct Fixture { uint32_t w, h, phase; };
        const Fixture fixtures[] = {{1, 1, 0}, {7, 3, 0}, {257, 65, 0}, {7, 3, 1}};
        for (unsigned i = 0; i < 4; ++i) {
            const auto f = fixtures[i];
            std::vector<uint8_t> pixels(static_cast<std::size_t>(f.w) * f.h * 4);
            for (uint32_t y = 0; y < f.h; ++y) {
                for (uint32_t x = 0; x < f.w; ++x) {
                    const auto p = (static_cast<std::size_t>(y) * f.w + x) * 4;
                    pixels[p]     = static_cast<uint8_t>(x + 17 * f.phase);
                    pixels[p + 1] = static_cast<uint8_t>(3 * y + 29 * f.phase);
                    pixels[p + 2] = static_cast<uint8_t>(x ^ y ^ f.phase);
                    pixels[p + 3] = static_cast<uint8_t>(7 * x + 11 * y + 13 * f.phase);
                }
            }
            const auto encoded = png::encode_rgba(pixels.data(), f.w, f.h);
            std::ofstream stream(output / ("fixture_" + std::to_string(i) + ".png"),
                                 std::ios::binary);
            stream.write(reinterpret_cast<const char*>(encoded.data()),
                         static_cast<std::streamsize>(encoded.size()));
            stream.close();
            if (!stream) throw std::runtime_error("fixture write failed");
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
    return 0;
}
