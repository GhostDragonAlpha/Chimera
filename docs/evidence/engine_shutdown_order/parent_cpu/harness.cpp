#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <mutex>
#include <thread>
#include <vector>
#include <string>
#define CHANNEL(n) static std::mutex g_##n##_mutex; static std::condition_variable g_##n##_cv; static bool g_##n##_applied = false;
CHANNEL(mem) CHANNEL(md) CHANNEL(mesh) CHANNEL(hinge) CHANNEL(water)
CHANNEL(gait) CHANNEL(volp) CHANNEL(frost) CHANNEL(skin)
// Generated verbatim from the current main.cpp, never a handwritten twin.
#include "production_helpers.hpp"

struct Channel { std::mutex* mutex; std::condition_variable* cv; bool* applied; };
#define REF(n) {&g_##n##_mutex, &g_##n##_cv, &g_##n##_applied}

int main() {
    Channel channels[] = {REF(mem), REF(md), REF(mesh), REF(hinge), REF(water),
                          REF(gait), REF(volp), REF(frost), REF(skin)};
    std::atomic<int> entered{0}, cancelled{0}, wrong{0};
    std::vector<std::thread> workers;
    for (auto c : channels) workers.emplace_back([&, c] {
        std::unique_lock<std::mutex> lock(*c.mutex);
        entered.fetch_add(1);
        try {
            wait_for_shutdown(*c.cv, lock, std::chrono::seconds(60), [&]{return *c.applied;});
            wrong.fetch_add(1);
        } catch (const ShutdownCancellation&) { cancelled.fetch_add(1); }
    });
    while (entered.load() != 9) std::this_thread::yield();
    g_shutdown_closing.store(true);
    notify_shutdown_channels();
    for (auto& w : workers) w.join();
    if (cancelled != 9 || wrong != 0) return 10;
    puts("actual_helpers: nine channel cancellations observed");
    {
        std::unique_lock<std::mutex> lock(g_mem_mutex);
        g_mem_applied = true;
        try {
            if (!wait_for_shutdown(g_mem_cv, lock, std::chrono::seconds(60), []{return g_mem_applied;})) return 11;
        } catch (const ShutdownCancellation&) { return 12; }
    }
    puts("actual_helpers: already-applied success preserved");
    struct WitnessMutex {
        bool held = false;
        void lock() { held = true; }
        void unlock() { held = false; }
    } witness;
    struct WitnessCondition {
        WitnessMutex& m; bool saw_lock = false;
        void notify_all() { saw_lock = m.held; }
    } condition{witness};
    notify_shutdown(witness, condition);
    if (!condition.saw_lock || witness.held) return 13;
    puts("actual_helpers: notification owns matching mutex");

    g_shutdown_closing.store(false);
    g_shutdown_test_boot_waiting.store(false);
    std::mutex boot_mutex;
    std::condition_variable boot_cv;
    std::atomic<bool> cancel{false}, returned{false}, cancelled_delay{false};
    std::thread boot([&] {
        cancelled_delay = wait_for_shutdown_delay(boot_mutex, boot_cv, cancel, std::chrono::seconds(60));
        returned = true;
    });
    while (!g_shutdown_test_boot_waiting.load()) std::this_thread::yield();
    bool parked = false;
    {
        // Entry witness is set under this mutex. Acquiring it now observes
        // the worker's release into its condition-variable wait.
        std::lock_guard<std::mutex> lock(boot_mutex);
        parked = !returned.load();
        cancel = true;
    }
    notify_shutdown(boot_mutex, boot_cv);
    boot.join();
    if (!parked || !returned || !cancelled_delay) return 14;
    puts("actual_helpers: observed parked boot delay cancelled and joined");
    return 0;
}
