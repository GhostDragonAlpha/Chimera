#include "ChimeraEngine/engine/contribution_executor.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstddef>
#include <exception>
#include <iostream>
#include <mutex>
#include <stdexcept>
#include <thread>
#include <vector>

namespace {

using chimera::multibody::ContributionExecutor;
using namespace std::chrono_literals;

struct Checks {
    bool worker_limits = false;
    bool all_indices_once = false;
    bool overlap_two = false;
    bool overlap_four = false;
    bool lowest_failure_and_drain = false;
    bool reusable_after_failure = false;
    bool recursive_refusal = false;
    bool external_calls_serialize = false;
    bool destructor_completes_work = false;
};

struct IndexedFailure : std::exception {
    explicit IndexedFailure(std::size_t value) : index(value) {}
    const char* what() const noexcept override { return "indexed callback failure"; }
    std::size_t index;
};

bool rejects_worker_count(std::size_t count) {
    try {
        ContributionExecutor executor(count);
    } catch (const std::invalid_argument&) {
        return true;
    } catch (...) {
        return false;
    }
    return false;
}

bool overlap_probe(std::size_t workers) {
    ContributionExecutor executor(workers);
    if (executor.workers() != workers) return false;

    std::atomic<std::size_t> active{0};
    std::atomic<std::size_t> maximum{0};
    std::mutex mutex;
    std::condition_variable changed;
    std::size_t arrived = 0;
    bool rendezvous = false;

    executor.for_each(workers, [&](std::size_t) {
        const auto now_active = active.fetch_add(1) + 1;
        auto observed = maximum.load();
        while (observed < now_active &&
               !maximum.compare_exchange_weak(observed, now_active)) {
        }

        std::unique_lock<std::mutex> lock(mutex);
        ++arrived;
        if (arrived == workers) {
            rendezvous = true;
            changed.notify_all();
        } else {
            changed.wait_for(lock, 2s, [&] { return rendezvous; });
        }
        lock.unlock();
        active.fetch_sub(1);
    });
    return rendezvous && maximum.load() >= 2;
}

bool concurrent_calls_serialize() {
    ContributionExecutor executor(2);
    std::mutex mutex;
    std::condition_variable changed;
    bool first_entered = false;
    bool release_first = false;
    bool second_started = false;
    bool second_entered = false;
    std::atomic<std::size_t> active{0};
    std::atomic<std::size_t> maximum{0};
    std::atomic<bool> calls_succeeded{true};

    auto observe_active = [&] {
        const auto now_active = active.fetch_add(1) + 1;
        auto observed = maximum.load();
        while (observed < now_active &&
               !maximum.compare_exchange_weak(observed, now_active)) {
        }
    };

    std::thread first([&] {
        try {
            executor.for_each(1, [&](std::size_t) {
                observe_active();
                std::unique_lock<std::mutex> lock(mutex);
                first_entered = true;
                changed.notify_all();
                changed.wait_for(lock, 6s, [&] { return release_first; });
                lock.unlock();
                active.fetch_sub(1);
            });
        } catch (...) {
            calls_succeeded = false;
        }
    });

    bool first_ready = false;
    {
        std::unique_lock<std::mutex> lock(mutex);
        first_ready = changed.wait_for(lock, 2s, [&] { return first_entered; });
    }

    std::thread second([&] {
        {
            std::lock_guard<std::mutex> lock(mutex);
            second_started = true;
            changed.notify_all();
        }
        try {
            executor.for_each(1, [&](std::size_t) {
                observe_active();
                std::lock_guard<std::mutex> lock(mutex);
                second_entered = true;
                changed.notify_all();
                active.fetch_sub(1);
            });
        } catch (...) {
            calls_succeeded = false;
        }
    });

    bool second_ready = false;
    {
        std::unique_lock<std::mutex> lock(mutex);
        changed.wait_for(lock, 2s, [&] { return second_started; });
        second_ready = changed.wait_for(lock, 250ms, [&] { return second_entered; });
        release_first = true;
        changed.notify_all();
    }
    first.join();
    second.join();
    return first_ready && !second_ready && calls_succeeded.load() &&
           second_entered && maximum.load() == 1;
}

bool failure_order_and_drain(ContributionExecutor& executor) {
    constexpr std::size_t count = 32;
    std::array<std::atomic<unsigned>, count> calls{};
    for (auto& call : calls) call.store(0);

    bool caught_lowest = false;
    try {
        executor.for_each(count, [&](std::size_t index) {
            calls[index].fetch_add(1);
            if (index == 19 || index == 2 || index == 11)
                throw IndexedFailure(index);
        });
    } catch (const IndexedFailure& failure) {
        caught_lowest = failure.index == 2;
    } catch (...) {
        return false;
    }

    bool every_job_ran = true;
    for (const auto& call : calls) every_job_ran &= call.load() == 1;
    return caught_lowest && every_job_ran;
}

bool reusable_after_failure(ContributionExecutor& executor) {
    constexpr std::size_t count = 17;
    std::array<std::atomic<unsigned>, count> calls{};
    for (auto& call : calls) call.store(0);
    executor.for_each(count, [&](std::size_t index) {
        calls[index].fetch_add(1);
    });
    for (const auto& call : calls) {
        if (call.load() != 1) return false;
    }
    return true;
}

bool recursive_refusal() {
    ContributionExecutor executor(2);
    std::atomic<bool> refused{false};
    std::atomic<bool> attempted{false};
    std::array<std::atomic<unsigned>, 8> calls{};
    for (auto& call : calls) call.store(0);
    const auto caller = std::this_thread::get_id();

    executor.for_each(calls.size(), [&](std::size_t index) {
        calls[index].fetch_add(1);
        if (index != 0 || std::this_thread::get_id() == caller) return;
        attempted = true;
        try {
            executor.for_each(1, [](std::size_t) {});
        } catch (const std::logic_error&) {
            refused = true;
        } catch (...) {
        }
    });

    if (!attempted.load() || !refused.load()) return false;
    for (const auto& call : calls) {
        if (call.load() != 1) return false;
    }
    return true;
}

bool destructor_completes_work() {
    constexpr std::size_t count = 64;
    std::array<std::atomic<unsigned>, count> calls{};
    for (auto& call : calls) call.store(0);
    {
        ContributionExecutor executor(4);
        executor.for_each(count, [&](std::size_t index) {
            calls[index].fetch_add(1);
        });
    }
    for (const auto& call : calls) {
        if (call.load() != 1) return false;
    }
    return true;
}

}  // namespace

int main() {
    Checks checks;
    checks.worker_limits = rejects_worker_count(0) && rejects_worker_count(5) &&
        ContributionExecutor(1).workers() == 1 &&
        ContributionExecutor(4).workers() == 4;

    constexpr std::size_t index_count = 128;
    std::array<std::atomic<unsigned>, index_count> index_calls{};
    for (auto& call : index_calls) call.store(0);
    ContributionExecutor four_workers(4);
    four_workers.for_each(index_count, [&](std::size_t index) {
        index_calls[index].fetch_add(1);
    });
    checks.all_indices_once = true;
    for (const auto& call : index_calls)
        checks.all_indices_once &= call.load() == 1;

    checks.overlap_two = overlap_probe(2);
    checks.overlap_four = overlap_probe(4);
    checks.lowest_failure_and_drain = failure_order_and_drain(four_workers);
    checks.reusable_after_failure = reusable_after_failure(four_workers);
    checks.recursive_refusal = recursive_refusal();
    checks.external_calls_serialize = concurrent_calls_serialize();
    checks.destructor_completes_work = destructor_completes_work();

    const bool pass = checks.worker_limits && checks.all_indices_once &&
        checks.overlap_two && checks.overlap_four &&
        checks.lowest_failure_and_drain && checks.reusable_after_failure &&
        checks.recursive_refusal && checks.external_calls_serialize &&
        checks.destructor_completes_work;

    std::cout << "{\"checks\":{"
              << "\"worker_limits\":" << (checks.worker_limits ? "true" : "false") << ','
              << "\"all_indices_once\":" << (checks.all_indices_once ? "true" : "false") << ','
              << "\"overlap_two\":" << (checks.overlap_two ? "true" : "false") << ','
              << "\"overlap_four\":" << (checks.overlap_four ? "true" : "false") << ','
              << "\"lowest_failure_and_drain\":" << (checks.lowest_failure_and_drain ? "true" : "false") << ','
              << "\"reusable_after_failure\":" << (checks.reusable_after_failure ? "true" : "false") << ','
              << "\"recursive_refusal\":" << (checks.recursive_refusal ? "true" : "false") << ','
              << "\"external_calls_serialize\":" << (checks.external_calls_serialize ? "true" : "false") << ','
              << "\"destructor_completes_work\":" << (checks.destructor_completes_work ? "true" : "false")
              << "},\"counts\":{\"indices\":" << index_count
              << ",\"failure_jobs\":32,\"reuse_jobs\":17,\"destructor_jobs\":64}"
              << ",\"pass\":" << (pass ? "true" : "false") << "}\n";
    return pass ? 0 : 1;
}
