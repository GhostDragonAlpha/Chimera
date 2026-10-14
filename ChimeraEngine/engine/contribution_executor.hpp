#pragma once
#include <atomic>
#include <condition_variable>
#include <cstddef>
#include <exception>
#include <functional>
#include <mutex>
#include <stdexcept>
#include <thread>
#include <vector>

namespace chimera::multibody {

// Bounded, persistent CPU executor. Callbacks own distinct result slots and read
// immutable inputs. This class schedules computations, never commits body state.
// One invocation completes before the next begins; collect results in input order.
class ContributionExecutor {
 std::size_t workers_;
 std::vector<std::thread> threads_;
 std::mutex invocation_, mutex_;
 std::condition_variable wake_, done_;
 bool stopping_ = false;
 std::size_t generation_ = 0, remaining_ = 0, count_ = 0;
 std::atomic<std::size_t> next_{0};
 std::function<void(std::size_t)> job_;
 std::vector<std::exception_ptr> failures_;
 inline static thread_local const ContributionExecutor* active_ = nullptr;

 void execute_indices() noexcept {
  const auto previous = active_;
  active_ = this;
  for (;;) {
   const auto index = next_.fetch_add(1, std::memory_order_relaxed);
   if (index >= count_) break;
   try { job_(index); }
   catch (...) { failures_[index] = std::current_exception(); }
  }
  active_ = previous;
 }

 void worker() {
  std::size_t seen = 0;
  for (;;) {
   std::unique_lock<std::mutex> lock(mutex_);
   wake_.wait(lock, [&] { return stopping_ || generation_ != seen; });
   if (stopping_) return;
   seen = generation_;
   lock.unlock();
   execute_indices();
   lock.lock();
   if (--remaining_ == 0) done_.notify_one();
  }
 }

 void stop_and_join() noexcept {
  { std::lock_guard<std::mutex> lock(mutex_); stopping_ = true; }
  wake_.notify_all();
  for (auto& thread : threads_) if (thread.joinable()) thread.join();
 }

public:
 explicit ContributionExecutor(std::size_t workers) : workers_(workers) {
  if (workers < 1 || workers > 4)
   throw std::invalid_argument("contribution_worker_count_out_of_range");
  // Serial default avoids any background threads. The owner must outlive calls.
  if (workers == 1) return;
  try {
   threads_.reserve(workers);
   for (std::size_t i = 0; i < workers; ++i)
    threads_.emplace_back([this] { worker(); });
  } catch (...) { stop_and_join(); throw; }
 }
 ~ContributionExecutor() { stop_and_join(); }
 ContributionExecutor(const ContributionExecutor&) = delete;
 ContributionExecutor& operator=(const ContributionExecutor&) = delete;
 std::size_t workers() const noexcept { return workers_; }

 void for_each(std::size_t count, const std::function<void(std::size_t)>& function) {
  if (active_ == this) throw std::logic_error("contribution_recursive_invocation");
  if (count && !function) throw std::invalid_argument("contribution_missing_callback");
  std::unique_lock<std::mutex> invocation(invocation_);
  if (!count) return;
  // All allocations happen before waking workers. On allocation failure there is
  // no active job and no partially published result.
  std::vector<std::exception_ptr> failures(count);
  std::function<void(std::size_t)> job(function);
  {
   std::lock_guard<std::mutex> lock(mutex_);
   count_ = count;
   next_.store(0, std::memory_order_relaxed);
   failures_ = std::move(failures);
   job_ = std::move(job);
   remaining_ = workers_;
   ++generation_;
  }
  if (workers_ == 1) execute_indices();
  else {
   wake_.notify_all();
   std::unique_lock<std::mutex> lock(mutex_);
   done_.wait(lock, [&] { return remaining_ == 0; });
  }
  job_ = {}; // No worker can still refer to callback captures after this barrier.
  for (const auto& failure : failures_) if (failure) std::rethrow_exception(failure);
 }
};
} // namespace chimera::multibody
