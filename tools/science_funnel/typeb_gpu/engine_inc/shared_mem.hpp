#pragma once
#include <windows.h>
#include <cstdint>
#include <cstring>

// Windows shared-memory ring buffer for engine <-> shim IPC.
constexpr uint32_t kRingSlots = 1024;
constexpr size_t   kSlotBytes = 64;
constexpr size_t   kRingHeader = sizeof(uint32_t) * 2 + sizeof(uint64_t);
constexpr size_t   kRingSize   = kRingHeader + kRingSlots * kSlotBytes;

struct alignas(8) RingHeader {
    uint64_t magic     = 0xA110C0DECAFEBABEULL;
    uint32_t write_idx = 0;
    uint32_t read_idx  = 0;
};

// Physics state packet — mirrors master_loop position array columns.
struct alignas(8) StatePacket {
    float x, y, z;
    float vx, vy, vz;
    float cr, cg, cb;
    float size;
    char  pad[16];
};

static_assert(sizeof(StatePacket) <= kSlotBytes, "StatePacket too large for slot");

class SharedRing {
public:
    SharedRing() = default;
    explicit SharedRing(const char* name) { open(name, false); }
    bool open(const char* name, bool create = false) {
        close();
        if (create) {
            handle_ = CreateFileMappingA(INVALID_HANDLE_VALUE, nullptr, PAGE_READWRITE,
                                         0, static_cast<DWORD>(kRingSize), name);
            if (!handle_) return false;
            ptr_ = MapViewOfFile(handle_, FILE_MAP_ALL_ACCESS, 0, 0, kRingSize);
            if (!ptr_) { CloseHandle(handle_); handle_ = nullptr; return false; }
            auto* h = reinterpret_cast<RingHeader*>(ptr_);
            h->magic     = 0xA110C0DECAFEBABEULL;
            h->write_idx = 0;
            h->read_idx  = 0;
            std::memset(static_cast<char*>(ptr_) + kRingHeader, 0, kRingSlots * kSlotBytes);
        } else {
            handle_ = OpenFileMappingA(FILE_MAP_ALL_ACCESS, FALSE, name);
            if (!handle_) return false;
            ptr_ = MapViewOfFile(handle_, FILE_MAP_ALL_ACCESS, 0, 0, kRingSize);
            if (!ptr_) { CloseHandle(handle_); handle_ = nullptr; return false; }
            auto* h = reinterpret_cast<RingHeader*>(ptr_);
            if (h->magic != 0xA110C0DECAFEBABEULL) return false;
        }
        return true;
    }

    void close() {
        if (ptr_) { UnmapViewOfFile(ptr_); ptr_ = nullptr; }
        if (handle_) { CloseHandle(handle_); handle_ = nullptr; }
    }

    bool push(const StatePacket& pkt) {
        if (!ptr_) return false;
        auto* h = reinterpret_cast<RingHeader*>(ptr_);
        uint32_t next = (h->write_idx + 1) % kRingSlots;
        if (next == h->read_idx) return false; // full
        auto* slot = reinterpret_cast<StatePacket*>(
            static_cast<char*>(ptr_) + kRingHeader + h->write_idx * kSlotBytes);
        *slot = pkt;
        h->write_idx = next;
        return true;
    }

    bool pop(StatePacket& pkt) {
        if (!ptr_) return false;
        auto* h = reinterpret_cast<RingHeader*>(ptr_);
        if (h->write_idx == h->read_idx) return false; // empty
        auto* slot = reinterpret_cast<StatePacket*>(
            static_cast<char*>(ptr_) + kRingHeader + h->read_idx * kSlotBytes);
        pkt = *slot;
        h->read_idx = (h->read_idx + 1) % kRingSlots;
        return true;
    }

    uint32_t used() const {
        if (!ptr_) return 0;
        auto* h = reinterpret_cast<RingHeader*>(ptr_);
        if (h->write_idx >= h->read_idx)
            return h->write_idx - h->read_idx;
        return kRingSlots - h->read_idx + h->write_idx;
    }

private:
    HANDLE handle_ = nullptr;
    void*  ptr_    = nullptr;
};
