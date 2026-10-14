// timer_microbench.cpp -- the F3(c) instrumentation-overhead bound.
//
// Measures the cost of ONE tickcost::Scope pair (the RAII chrono scope the
// instrument inserts at every anchor) on this machine, so the per-tick
// overhead can be BOUNDED analytically: overhead/tick = scope_pairs_per_tick
// x measured_ns_per_pair. The instrument's own hit counters give the pairs
// per tick (~870 on the walk; see receipt). Compiled and run ONCE beside the
// final matrix; the result is recorded in the receipt.
//
// Trailer Agent: tickcost.
#include "tickcost_probe.hpp"
#include <cstdio>
int main() {
  const int N = 1000000;
  // warmup
  for (int i = 0; i < 10000; ++i) { tickcost::Scope s(tickcost::FK_EVALUATE); }
  auto t0 = std::chrono::steady_clock::now();
  for (int i = 0; i < N; ++i) { tickcost::Scope s(tickcost::FK_EVALUATE); }
  auto t1 = std::chrono::steady_clock::now();
  double ns_per_pair = std::chrono::duration<double, std::nano>(t1 - t0).count() / N;
  // a bare now() pair for reference
  auto b0 = std::chrono::steady_clock::now();
  for (int i = 0; i < N; ++i) { auto a = std::chrono::steady_clock::now(); (void)a; }
  auto b1 = std::chrono::steady_clock::now();
  double ns_now = std::chrono::duration<double, std::nano>(b1 - b0).count() / N;
  std::printf("[tc-bench] scope_pair_ns=%.1f now_ns=%.1f n=%d\n", ns_per_pair, ns_now, N);
  return 0;
}
