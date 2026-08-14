// SPIACE native core — skeleton, first genome: the brick wall (G1).
//
// Rule 0 (stated before the build):
//   STATEMENT:  the CA substrate and genome rule tables are language-
//               independent — this core executing the same R produces the
//               structure the JS reference grew (spiace_grow.html?genome=wall).
//   PREDICTION: completes the exact 210-brick blueprint in 14 ticks with 0
//               support violations, streaming one NDJSON frame per tick.
//   FALSIFIER:  any (y,i) mismatch vs the blueprint, any support violation,
//               or a stalled wave kills the port claim (test_native.py is the
//               independent oracle — it recomputes the blueprint itself).
//
// Wire protocol (stdout, one JSON object per line):
//   {"type":"frame","tick":N,"cells":[[y,i],...],"violations":V,"done":B}
// Brick identity is the integer pair (course y, index i) — the oracle needs
// no float comparisons. Geometry (x0,x1) is derivable from (y,i) + the
// genome table, so it never crosses the wire at all.
//
// Genome constants are ported verbatim from the WALL table in
// spiace_grow.html (genomes-as-data: the .chimera table READER that makes
// this shared comes with the kernel-DSL port — skeleton hardcodes one genome).
//
// Build: g++ -O2 -std=c++17 -o ca_core.exe ca_core.cpp
// Run:   ./ca_core.exe [tick_ms]     (default 120; 0 = as fast as possible)

#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <set>
#include <thread>
#include <vector>

namespace wall {
// --- genome table (verbatim from WALL in spiace_grow.html) -----------------
constexpr double brickLen = 0.22, brickH = 0.075, gap = 0.012;
constexpr int courses = 12, wide = 18, seedI = 9;
constexpr double minSupport = 0.30;
} // namespace wall

struct Brick { int y, i; double x0, x1; };
struct Key {
  int y, i;
  bool operator<(const Key& o) const { return y < o.y || (y == o.y && i < o.i); }
};

static std::vector<Brick> buildBlueprint() {
  using namespace wall;
  const double xp = brickLen + gap;
  std::vector<Brick> bp;
  for (int y = 0; y < courses; y++) {
    const int n = (y % 2 == 0) ? wide : wide - 1;
    const double off = (y % 2 == 0) ? 0.0 : xp / 2;
    for (int i = 0; i < n; i++)
      bp.push_back({y, i, i * xp + off, i * xp + off + brickLen});
  }
  return bp;
}

static double overlap(double a0, double a1, double b0, double b1) {
  return std::max(0.0, std::min(a1, b1) - std::max(a0, b0));
}

static bool isSupported(const Brick& b, const std::set<Key>& placed,
                        const std::vector<Brick>& bp) {
  if (b.y == 0) return true;
  for (const Brick& c : bp) {
    if (c.y != b.y - 1 || !placed.count({c.y, c.i})) continue;
    if (overlap(b.x0, b.x1, c.x0, c.x1) > wall::minSupport * wall::brickLen)
      return true;
  }
  return false;
}

static bool eligible(const Brick& b, const std::set<Key>& placed,
                     const std::vector<Brick>& bp) {
  if (!isSupported(b, placed, bp)) return false;
  if (b.y == 0) {
    if (b.i == wall::seedI) return true;
    return placed.count({0, b.i - 1}) || placed.count({0, b.i + 1});
  }
  return true;
}

int main(int argc, char** argv) {
  const int tickMs = argc > 1 ? std::atoi(argv[1]) : 120;
  const std::vector<Brick> bp = buildBlueprint();
  std::set<Key> placed;
  // founder: the seed brick, exactly as the JS reference seeds at load
  for (const Brick& b : bp)
    if (b.y == 0 && b.i == wall::seedI) { placed.insert({b.y, b.i}); break; }

  int tick = 0, violations = 0;
  bool done = false;
  while (!done) {
    tick++;
    std::vector<Key> wave;
    for (const Brick& b : bp)
      if (!placed.count({b.y, b.i}) && eligible(b, placed, bp))
        wave.push_back({b.y, b.i});
    for (const Key& k : wave) placed.insert(k);
    // support audit from scratch every tick — the wall's law is re-verified,
    // never assumed (same ledger discipline as the JS reference)
    violations = 0;
    for (const Brick& b : bp)
      if (placed.count({b.y, b.i}) && !isSupported(b, placed, bp)) violations++;
    done = placed.size() == bp.size();

    std::printf("{\"type\":\"frame\",\"tick\":%d,\"cells\":[", tick);
    bool first = true;
    for (const Key& k : placed) {
      std::printf("%s[%d,%d]", first ? "" : ",", k.y, k.i);
      first = false;
    }
    std::printf("],\"violations\":%d,\"done\":%s}\n", violations,
                done ? "true" : "false");
    std::fflush(stdout);
    if (tickMs > 0)
      std::this_thread::sleep_for(std::chrono::milliseconds(tickMs));
    if (tick > 10000) {  // wave stalled: the falsifier, visible on the wire
      std::fprintf(stderr, "STALLED: wave empty at tick %d\n", tick);
      return 2;
    }
    if (wave.empty() && !done) {
      std::fprintf(stderr, "DEAD WAVE at tick %d (%zu/%zu bricks)\n", tick,
                   placed.size(), bp.size());
      return 3;
    }
  }
  return 0;
}
