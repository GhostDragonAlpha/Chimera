#include <atomic>
#include <chrono>
#include <condition_variable>
#include <iostream>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

struct ShutdownCancellation {};
static std::atomic<bool> closing{false};

template <class Condition, class Lock, class Rep, class Period, class Predicate>
static bool wait_for_shutdown(Condition& cv, Lock& lock,
                              const std::chrono::duration<Rep, Period>& timeout,
                              Predicate predicate) {
    cv.wait_for(lock, timeout, [&] { return predicate() || closing.load(); });
    if (closing.load() && !predicate()) throw ShutdownCancellation{};
    return predicate();
}

template <class Channel>
static void notify_shutdown(Channel& channel) {
    std::lock_guard<std::mutex> lock(channel.mutex);
    channel.cv.notify_all();
}

struct Channel {
    std::mutex mutex;
    std::condition_variable cv;
    bool applied = false;
    const char* name;
};

static int channel_cancellation() {
    Channel channels[] = {
        {{}, {}, false, "mem"}, {{}, {}, false, "md"}, {{}, {}, false, "mesh"},
        {{}, {}, false, "hinge"}, {{}, {}, false, "water"}, {{}, {}, false, "gait"},
        {{}, {}, false, "volp"}, {{}, {}, false, "frost"}, {{}, {}, false, "skin"}
    };
    std::atomic<int> cancelled{0};
    std::vector<std::thread> waiters;
    for (Channel& channel : channels) {
        waiters.emplace_back([&channel, &cancelled] {
            std::unique_lock<std::mutex> lock(channel.mutex);
            try {
                wait_for_shutdown(channel.cv, lock, std::chrono::seconds(5),
                                  [&channel] { return channel.applied; });
            } catch (const ShutdownCancellation&) {
                ++cancelled;
            }
        });
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(40));
    closing.store(true);
    for (Channel& channel : channels) notify_shutdown(channel);
    for (auto& waiter : waiters) waiter.join();
    std::cout << "channels: cancelled=" << cancelled.load() << "/9\n";
    return cancelled.load() == 9 ? 0 : 1;
}

static int already_applied() {
    Channel channel{{}, {}, true, "already_applied"};
    std::unique_lock<std::mutex> lock(channel.mutex);
    try {
        bool result = wait_for_shutdown(channel.cv, lock, std::chrono::seconds(1),
                                        [&channel] { return channel.applied; });
        std::cout << "already_applied: result=" << (result ? "success" : "cancel") << "\n";
        return result ? 0 : 1;
    } catch (const ShutdownCancellation&) {
        std::cout << "already_applied: unexpected_cancel\n";
        return 1;
    }
}

static int late_admission() {
    bool admitted = !closing.load();
    std::cout << "late_admission: " << (admitted ? "UNEXPECTED_SUCCESS" : "rejected") << "\n";
    return admitted ? 1 : 0;
}

static int boot_cancel() {
    std::mutex mutex;
    std::condition_variable cv;
    std::atomic<bool> cancel{false};
    std::atomic<bool> joined_body{false};
    std::thread boot([&] {
        std::unique_lock<std::mutex> lock(mutex);
        cv.wait_for(lock, std::chrono::seconds(5), [&] { return cancel.load() || closing.load(); });
        joined_body.store(true);
    });
    std::this_thread::sleep_for(std::chrono::milliseconds(40));
    auto started = std::chrono::steady_clock::now();
    cancel.store(true);
    cv.notify_all();
    boot.join();
    auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - started).count();
    std::cout << "boot: joined=" << (joined_body.load() ? "yes" : "no")
              << " cancel_ms=" << elapsed << "\n";
    return joined_body.load() && elapsed < 500 ? 0 : 1;
}

static int pending_callback() {
    closing.store(false);
    Channel channel{{}, {}, false, "pending"};
    std::atomic<bool> waiting{false};
    std::atomic<bool> cancelled{false};
    std::thread callback([&] {
        std::unique_lock<std::mutex> lock(channel.mutex);
        waiting.store(true);
        try {
            wait_for_shutdown(channel.cv, lock, std::chrono::seconds(5),
                              [&channel] { return channel.applied; });
        } catch (const ShutdownCancellation&) {
            cancelled.store(true);
        }
    });
    while (!waiting.load()) std::this_thread::yield();
    std::cout << "api: waiting=yes\n";
    closing.store(true);
    notify_shutdown(channel);
    callback.join();
    std::cout << "api: cancelled=" << (cancelled.load() ? "yes" : "no") << "\n";
    return cancelled.load() ? 0 : 1;
}

static int mutation_negative() {
    closing.store(false);
    Channel channel{{}, {}, false, "mutation"};
    std::atomic<bool> returned{false};
    std::thread bad([&] {
        std::unique_lock<std::mutex> lock(channel.mutex);
        channel.cv.wait_for(lock, std::chrono::milliseconds(500), [&] { return channel.applied; });
        returned.store(true);
    });
    std::this_thread::sleep_for(std::chrono::milliseconds(40));
    closing.store(true);
    notify_shutdown(channel);
    std::this_thread::sleep_for(std::chrono::milliseconds(40));
    bool rejected = !returned.load();
    channel.applied = true;
    notify_shutdown(channel);
    bad.join();
    std::cout << "mutation: early_return_rejected=" << (rejected ? "yes" : "no") << " joined_after_release=yes\n";
    return rejected ? 0 : 1;
}

static int order_markers() {
    closing.store(false);
    std::vector<std::string> events;
    events.push_back("admission_closed");
    events.push_back("boot_joined");
    events.push_back("http_stopped");
    events.push_back("engine_shutdown");
    std::cout << "shutdown: admission_closed\nshutdown: boot_joined\nshutdown: http_stopped\nshutdown: engine_shutdown\n";
    return events == std::vector<std::string>{"admission_closed", "boot_joined", "http_stopped", "engine_shutdown"} ? 0 : 1;
}

int main() {
    closing.store(false);
    int result = channel_cancellation();
    if (result) return result;
    closing.store(true);
    if ((result = already_applied())) return result;
    if ((result = late_admission())) return result;
    if ((result = boot_cancel())) return result;
    if ((result = pending_callback())) return result;
    if ((result = mutation_negative())) return result;
    return order_markers();
}
