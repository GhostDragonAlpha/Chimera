#pragma once
// png_encoder.hpp — minimal self-contained PNG (RGBA8) encoder for the /frame endpoint.
// No external deps: zlib "stored" (uncompressed) deflate blocks + CRC32 + Adler-32.
#include <cstdint>
#include <vector>

namespace png {

inline uint32_t crc32_update(uint32_t c, const uint8_t* data, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        c ^= data[i];
        for (int k = 0; k < 8; ++k)
            c = (c >> 1) ^ (0xEDB88320u & static_cast<uint32_t>(-static_cast<int32_t>(c & 1u)));
    }
    return c;
}

inline void push_u32be(std::vector<uint8_t>& out, uint32_t v) {
    out.push_back(static_cast<uint8_t>((v >> 24) & 0xFF));
    out.push_back(static_cast<uint8_t>((v >> 16) & 0xFF));
    out.push_back(static_cast<uint8_t>((v >> 8) & 0xFF));
    out.push_back(static_cast<uint8_t>(v & 0xFF));
}

inline void push_chunk(std::vector<uint8_t>& out, const char* type, const uint8_t* data, size_t n) {
    push_u32be(out, static_cast<uint32_t>(n));
    const uint8_t* tb = reinterpret_cast<const uint8_t*>(type);
    uint32_t c = crc32_update(0xFFFFFFFFu, tb, 4);
    out.insert(out.end(), tb, tb + 4);
    if (n > 0) {
        c = crc32_update(c, data, n);
        out.insert(out.end(), data, data + n);
    }
    push_u32be(out, ~c);
}

inline std::vector<uint8_t> encode_rgba(const uint8_t* rgba, uint32_t w, uint32_t h) {
    // scanlines, each prefixed with filter byte 0 (None)
    size_t row = static_cast<size_t>(w) * 4;
    std::vector<uint8_t> raw;
    raw.reserve((row + 1) * h);
    for (uint32_t y = 0; y < h; ++y) {
        raw.push_back(0);
        const uint8_t* src = rgba + static_cast<size_t>(y) * row;
        raw.insert(raw.end(), src, src + row);
    }

    // zlib stream: 2-byte header + stored (uncompressed) deflate blocks + Adler-32
    std::vector<uint8_t> z;
    z.reserve(raw.size() + raw.size() / 65535 * 5 + 16);
    z.push_back(0x78);
    z.push_back(0x01);
    size_t pos = 0, total = raw.size();
    while (pos < total) {
        size_t remaining = total - pos;
        size_t chunk = remaining > 65535 ? 65535 : remaining;
        bool final = (pos + chunk >= total);
        z.push_back(final ? 0x01 : 0x00);   // BFINAL=final, BTYPE=00 (stored)
        uint16_t len = static_cast<uint16_t>(chunk);
        z.push_back(static_cast<uint8_t>(len & 0xFF));
        z.push_back(static_cast<uint8_t>(len >> 8));
        uint16_t nlen = static_cast<uint16_t>(~len);
        z.push_back(static_cast<uint8_t>(nlen & 0xFF));
        z.push_back(static_cast<uint8_t>(nlen >> 8));
        z.insert(z.end(), raw.begin() + pos, raw.begin() + pos + chunk);
        pos += chunk;
    }
    uint32_t a = 1, b = 0;
    for (uint8_t byte : raw) {
        a = (a + byte) % 65521u;
        b = (b + a) % 65521u;
    }
    uint32_t adler = (b << 16) | a;
    z.push_back(static_cast<uint8_t>((adler >> 24) & 0xFF));
    z.push_back(static_cast<uint8_t>((adler >> 16) & 0xFF));
    z.push_back(static_cast<uint8_t>((adler >> 8) & 0xFF));
    z.push_back(static_cast<uint8_t>(adler & 0xFF));

    std::vector<uint8_t> out;
    const uint8_t sig[8] = {137, 80, 78, 71, 13, 10, 26, 10};
    out.insert(out.end(), sig, sig + 8);

    uint8_t ihdr[13] = {0};
    ihdr[0] = static_cast<uint8_t>((w >> 24) & 0xFF);
    ihdr[1] = static_cast<uint8_t>((w >> 16) & 0xFF);
    ihdr[2] = static_cast<uint8_t>((w >> 8) & 0xFF);
    ihdr[3] = static_cast<uint8_t>(w & 0xFF);
    ihdr[4] = static_cast<uint8_t>((h >> 24) & 0xFF);
    ihdr[5] = static_cast<uint8_t>((h >> 16) & 0xFF);
    ihdr[6] = static_cast<uint8_t>((h >> 8) & 0xFF);
    ihdr[7] = static_cast<uint8_t>(h & 0xFF);
    ihdr[8] = 8;    // bit depth
    ihdr[9] = 6;    // color type RGBA
    ihdr[10] = 0;   // compression
    ihdr[11] = 0;   // filter
    ihdr[12] = 0;   // interlace
    push_chunk(out, "IHDR", ihdr, sizeof(ihdr));
    push_chunk(out, "IDAT", z.data(), z.size());
    push_chunk(out, "IEND", nullptr, 0);
    return out;
}

} // namespace png
