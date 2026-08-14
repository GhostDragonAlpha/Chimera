// SPIACE native core — the CA substrate for the G-genomes, genomes as data.
//
// Rule 0 (stated before the build):
//   STATEMENT:  the CA substrate and genome rule tables are language-
//               independent — this core executing the same R produces the
//               structures the JS reference grew (spiace_grow.html). The
//               .chimera file is the DNA; the binary is the reader.
//   PREDICTION: wall: 210 bricks in 14 ticks, 0 violations. oak: height
//               >= 30, golden-angle phyllotaxis, clean dominance ledger,
//               connected tissue. creature: bilateral symmetry >= 0.85,
//               4 limbs, 12 digits, 2 eyes, corr(x, log a) > 0.85, Turing
//               spots within 30% of the lattice-dispersion prediction.
//   FALSIFIER:  any oracle recomputation from the wire (test_native.py)
//               outside the named bands kills the port claim.
//
// Wire protocol (stdout, one JSON object per line):
//   {"type":"meta","kind":K,"name":N,"cell":C}
//   wall:     {"type":"frame","tick":N,"cells":[[y,i],...],
//              "violations":V,"done":B}
//   oak:      {"type":"frame","tick":N,"cells":[[x,y,z,"mat",born,stem],...],
//              "violations":V,"height":H,"leaves":L,"tips":T,
//              "tipDirs":[[dx,dy,dz,leader],...] (alive tips),"done":B}
//   creature: {"type":"frame","tick":N,"cells":[[x,y,z,"mat"],...],
//              "violations":0,"phase":"P","limbs":L,"eyes":E,"done":B}
//   at done:  {"type":"final", kind-specific ledgers the oracle recomputes
//              from (phyllo/aux/tips | morphA/turingU/surf/limbRoots/eyes)}
// 3D cell identity is the integer triple — oracles need no float compares.
//
// Exit codes: 2 = stalled, 3 = dead wave, 4 = genome file error.
//
// Port bugs FOUND BY THE ORACLE (test_native.py N3, documented honestly):
//   1. cStepTips held `CTip& t` across cTips.push_back (digit spawning) — a
//      reallocation left the reference dangling and later digits read freed
//      heap: wild limb cells at x~528..648, y~-1e9, run-to-run different.
//      4 orphan cells cost symmetry (1.0 -> 0.993), connectivity, and the
//      corrLogAX sign (+0.905 -> -0.60 via outlier leverage). Fixed by
//      copying cell/dir/limbIdx by value before the push loop.
//   2. oActivateBuds held `const OTip* lead` across oTips.push_back — same
//      hazard, silently corrupting the dominance ledger. Fixed: leadId by
//      value.
//
// Build: g++ -O2 -std=c++17 -o ca_core.exe ca_core.cpp
// Run:   ./ca_core.exe [tick_ms] [genome_path]
//          tick_ms default = the genome's tickMs; genome_path default =
//          <exe dir>/genomes/wall.chimera

#include <array>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <map>
#include <set>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

// ============================ genome table (data) =============================
struct Genome {
  std::string kind = "wall", name = "?";
  int tickMs = 120;
  // wall
  double brickLen = 0, brickH = 0, brickD = 0, gap = 0, minSupport = 0;
  int courses = 0, wide = 0, seedI = 0;
  // oak
  double cell = 0, auxDeposit = 0, auxD = 0, auxDecay = 0, domTheta = 0,
         branchAngle = 0, golden = 0, grav = 0, photo = 0, lightMin = 0,
         leafLightMin = 0, leafShade = 0;
  int tipPeriod = 0, maxSteps = 0, maxCells = 0, domZone = 0, budMinAge = 0,
      budEvery = 0, lignify = 0;
  std::vector<double> sunDir;
  // creature
  double mP = 0, mD = 0, mDecay = 0, headMin = 0, tailMax = 0, eyeMin = 0,
         tA = 0, tB = 0, tDu = 0, tDv = 0, tDt = 0;
  int ballR = 0, growPeriod = 0, tailLen = 0, eyeXMin = 0, limbLen = 0,
      digitLen = 0, digits = 0, limbSpace = 0, limbFieldDelay = 0,
      patternTicks = 0, growDeadline = 0, tSteps = 0, turingTicks = 0;
  std::vector<double> foreBand, hindBand, dvBand;
};

static void die4(const std::string& msg) {
  std::fprintf(stderr, "GENOME %s\n", msg.c_str());
  std::exit(4);
}

static Genome loadGenome(const std::string& path) {
  std::ifstream f(path);
  if (!f) die4("MISSING: " + path);
  std::map<std::string, std::string> kv;
  std::string line;
  while (std::getline(f, line)) {
    const size_t hash = line.find('#');
    if (hash != std::string::npos) line = line.substr(0, hash);
    const size_t eq = line.find('=');
    if (eq == std::string::npos) continue;
    auto trim = [](std::string s) {
      const char* ws = " \t\r\n";
      const size_t a = s.find_first_not_of(ws), b = s.find_last_not_of(ws);
      return a == std::string::npos ? "" : s.substr(a, b - a + 1);
    };
    const std::string k = trim(line.substr(0, eq)), v = trim(line.substr(eq + 1));
    if (!k.empty() && !v.empty()) kv[k] = v;
  }
  auto need = [&](const char* k) -> std::string {
    if (!kv.count(k)) die4(std::string("KEY MISSING: ") + k + " in " + path);
    return kv[k];
  };
  auto needD = [&](const char* k) { return std::stod(need(k)); };
  auto needI = [&](const char* k) { return std::stoi(need(k)); };
  auto needL = [&](const char* k) {
    std::vector<double> out;
    const std::string v = need(k);
    size_t p = 0;
    while (p <= v.size()) {
      const size_t c = v.find(',', p);
      out.push_back(std::stod(v.substr(p, c == std::string::npos
                                           ? std::string::npos : c - p)));
      if (c == std::string::npos) break;
      p = c + 1;
    }
    return out;
  };
  Genome g;
  g.kind = need("kind");
  g.name = need("genome");
  if (kv.count("tickMs")) g.tickMs = std::stoi(kv["tickMs"]);
  if (g.kind == "wall") {
    g.brickLen = needD("brickLen"); g.brickH = needD("brickH");
    g.brickD = needD("brickD"); g.gap = needD("gap");
    g.minSupport = needD("minSupport");
    g.courses = needI("courses"); g.wide = needI("wide"); g.seedI = needI("seedI");
    if (g.brickLen <= 0 || g.gap < 0 || g.courses <= 0 || g.wide <= 1 ||
        g.minSupport <= 0 || g.minSupport >= 1 || g.seedI < 0 ||
        g.seedI >= g.wide)
      die4("INVALID: wall sanity bounds failed in " + path);
  } else if (g.kind == "oak") {
    g.cell = needD("cell"); g.auxDeposit = needD("auxDeposit");
    g.auxD = needD("auxD"); g.auxDecay = needD("auxDecay");
    g.domTheta = needD("domTheta"); g.branchAngle = needD("branchAngle");
    g.golden = needD("golden"); g.grav = needD("grav"); g.photo = needD("photo");
    g.lightMin = needD("lightMin"); g.leafLightMin = needD("leafLightMin");
    g.leafShade = needD("leafShade");
    g.tipPeriod = needI("tipPeriod"); g.maxSteps = needI("maxSteps");
    g.maxCells = needI("maxCells"); g.domZone = needI("domZone");
    g.budMinAge = needI("budMinAge"); g.budEvery = needI("budEvery");
    g.lignify = needI("lignify");
    g.sunDir = needL("sunDir");
    if (g.cell <= 0 || g.tipPeriod <= 0 || g.sunDir.size() != 3 ||
        g.budEvery <= 0 || g.lignify <= 0)
      die4("INVALID: oak sanity bounds failed in " + path);
  } else if (g.kind == "creature") {
    g.cell = needD("cell"); g.mP = needD("mP"); g.mD = needD("mD");
    g.mDecay = needD("mDecay"); g.headMin = needD("headMin");
    g.tailMax = needD("tailMax"); g.eyeMin = needD("eyeMin");
    g.tA = needD("tA"); g.tB = needD("tB"); g.tDu = needD("tDu");
    g.tDv = needD("tDv"); g.tDt = needD("tDt"); g.golden = needD("golden");
    g.ballR = needI("ballR"); g.growPeriod = needI("growPeriod");
    g.tailLen = needI("tailLen"); g.eyeXMin = needI("eyeXMin");
    g.limbLen = needI("limbLen"); g.digitLen = needI("digitLen");
    g.digits = needI("digits"); g.limbSpace = needI("limbSpace");
    g.limbFieldDelay = needI("limbFieldDelay");
    g.patternTicks = needI("patternTicks"); g.growDeadline = needI("growDeadline");
    g.tSteps = needI("tSteps"); g.turingTicks = needI("turingTicks");
    g.maxCells = needI("maxCells");
    g.foreBand = needL("foreBand"); g.hindBand = needL("hindBand");
    g.dvBand = needL("dvBand");
    if (g.cell <= 0 || g.ballR <= 0 || g.foreBand.size() != 2 ||
        g.hindBand.size() != 2 || g.dvBand.size() != 2 || g.digits <= 0)
      die4("INVALID: creature sanity bounds failed in " + path);
  } else die4("INVALID: unknown kind '" + g.kind + "' in " + path);
  return g;
}

static Genome W;

// ============================ shared lattice bits =============================
static inline int k3(int x, int y, int z) {
  return ((x + 64) << 14) | ((y + 64) << 7) | (z + 64);
}
static inline int kx(int k) { return (k >> 14) - 64; }
static inline int ky(int k) { return ((k >> 7) & 127) - 64; }
static inline int kz(int k) { return (k & 127) - 64; }
static const int N6[6][3] = {{1,0,0},{-1,0,0},{0,1,0},{0,-1,0},{0,0,1},{0,0,-1}};

static void norm3v(const double v[3], double out[3]) {
  double l = std::sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]);
  if (l == 0) l = 1.0;                      // JS: Math.hypot(...) || 1
  out[0] = v[0]/l; out[1] = v[1]/l; out[2] = v[2]/l;
}
static void perp3(const double d[3], double az, double out[3]) {
  double u[3];
  if (std::fabs(d[1]) > 0.95) { u[0] = 1; u[1] = 0; u[2] = 0; }
  else { const double t[3] = {-d[2], 0, d[0]}; norm3v(t, u); }
  const double v[3] = {d[1]*u[2]-d[2]*u[1], d[2]*u[0]-d[0]*u[2],
                       d[0]*u[1]-d[1]*u[0]};
  const double c = std::cos(az), s = std::sin(az);
  const double r[3] = {u[0]*c + v[0]*s, u[1]*c + v[1]*s, u[2]*c + v[2]*s};
  norm3v(r, out);
}
static double hash01(int n) {
  const double s = std::sin(n * 127.1) * 43758.5453;
  return s - std::floor(s);
}
static void axisSnap(const double v[3], int o[3]) {
  const double ax = std::fabs(v[0]), ay = std::fabs(v[1]), az = std::fabs(v[2]);
  const int a = ax > ay ? (ax > az ? 0 : 2) : (ay > az ? 1 : 2);
  o[0] = o[1] = o[2] = 0;
  o[a] = v[a] < 0 ? -1 : 1;              // Math.sign(x) || 1
}

// ============================ WALL (G1) =======================================
struct Brick { int y, i; double x0, x1; };
struct Key2 {
  int y, i;
  bool operator<(const Key2& o) const { return y < o.y || (y == o.y && i < o.i); }
};

static int runWall(int tickMs) {
  const double xp = W.brickLen + W.gap;
  std::vector<Brick> bp;
  for (int y = 0; y < W.courses; y++) {
    const int n = (y % 2 == 0) ? W.wide : W.wide - 1;
    const double off = (y % 2 == 0) ? 0.0 : xp / 2;
    for (int i = 0; i < n; i++)
      bp.push_back({y, i, i * xp + off, i * xp + off + W.brickLen});
  }
  auto overlap = [](double a0, double a1, double b0, double b1) {
    return std::max(0.0, std::min(a1, b1) - std::max(a0, b0));
  };
  auto isSupported = [&](const Brick& b, const std::set<Key2>& placed) {
    if (b.y == 0) return true;
    for (const Brick& c : bp) {
      if (c.y != b.y - 1 || !placed.count({c.y, c.i})) continue;
      if (overlap(b.x0, b.x1, c.x0, c.x1) > W.minSupport * W.brickLen)
        return true;
    }
    return false;
  };
  auto eligible = [&](const Brick& b, const std::set<Key2>& placed) {
    if (!isSupported(b, placed)) return false;
    if (b.y == 0) {
      if (b.i == W.seedI) return true;
      return placed.count({0, b.i - 1}) || placed.count({0, b.i + 1});
    }
    return true;
  };
  std::set<Key2> placed;
  for (const Brick& b : bp)
    if (b.y == 0 && b.i == W.seedI) { placed.insert({b.y, b.i}); break; }
  int tick = 0;
  bool done = false;
  while (!done) {
    tick++;
    std::vector<Key2> wave;
    for (const Brick& b : bp)
      if (!placed.count({b.y, b.i}) && eligible(b, placed))
        wave.push_back({b.y, b.i});
    for (const Key2& k : wave) placed.insert(k);
    int violations = 0;   // support audit from scratch every tick
    for (const Brick& b : bp)
      if (placed.count({b.y, b.i}) && !isSupported(b, placed)) violations++;
    done = placed.size() == bp.size();
    std::printf("{\"type\":\"frame\",\"tick\":%d,\"cells\":[", tick);
    bool first = true;
    for (const Key2& k : placed) {
      std::printf("%s[%d,%d]", first ? "" : ",", k.y, k.i);
      first = false;
    }
    std::printf("],\"violations\":%d,\"done\":%s}\n", violations,
                done ? "true" : "false");
    std::fflush(stdout);
    if (tickMs > 0)
      std::this_thread::sleep_for(std::chrono::milliseconds(tickMs));
    if (tick > 10000) {
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

// ============================ OAK (G2) ========================================
// mat: 0 wood, 1 bud, 2 leaf
struct OCell { int x, y, z, mat, born, stem; double az, dir0[3], par[3]; };
struct OTip {
  int id; double pos[3]; int cell[3]; double dir[3], az;
  int steps; bool alive, leader;
};

static double oakSun[3];
static std::vector<OCell> oCellsV;                    // insertion order = JS Map
static std::unordered_map<int, int> oIdx;             // k3 -> index
static std::vector<OTip> oTips;
static std::vector<int> oLeaves;                      // k3 keys
static std::vector<std::pair<int, double>> oPhyllo;   // {stem, az}
static std::unordered_map<int, double> oAux;
static int oTick = 0, oDomViolTick = 0, oDomMax = 0;
static bool oDone = false;

static double oLight(int x, int y, int z) {
  int shade = 0;
  for (const int k : oLeaves) {
    const OCell& c = oCellsV[oIdx[k]];
    const double dx = c.x - x, dy = c.y - y, dz = c.z - z;
    const double t = dx*oakSun[0] + dy*oakSun[1] + dz*oakSun[2];
    if (t <= 0) continue;
    const double p2 = dx*dx + dy*dy + dz*dz - t*t;
    if (p2 < 2.25) shade++;                 // 1.5-cell shadow tube
  }
  return std::exp(-W.leafShade * shade);
}

static void oAddCell(int x, int y, int z, int mat, int stem) {
  OCell c; c.x = x; c.y = y; c.z = z; c.mat = mat; c.born = oTick;
  c.stem = stem; c.az = 0;
  c.dir0[0] = c.dir0[1] = c.dir0[2] = 0;
  c.par[0] = c.par[1] = c.par[2] = 0;
  oIdx[k3(x, y, z)] = (int)oCellsV.size();
  oCellsV.push_back(c);
}

static void oStepTip(OTip& t) {
  const double L = oLight(t.cell[0], t.cell[1], t.cell[2]);
  const int period = std::max(1, (int)std::ceil(W.tipPeriod / std::max(L, 0.25)));
  if (oTick % period != 0) return;          // shaded tips grow slower
  // tropisms on green wood only — branches lignify, the leader never does
  const double lign = t.leader ? 1.0 : std::exp(-(double)t.steps / W.lignify);
  const double nd[3] = {t.dir[0] + oakSun[0]*W.photo*L*lign,
                        t.dir[1] + W.grav*lign + oakSun[1]*W.photo*L*lign,
                        t.dir[2] + oakSun[2]*W.photo*L*lign};
  norm3v(nd, t.dir);
  t.pos[0] += t.dir[0]; t.pos[1] += t.dir[1]; t.pos[2] += t.dir[2];
  int bx = 0, by = 0, bz = 0;
  double ba = -2;
  bool found = false;
  for (const auto& d : N6) {
    const int x = t.cell[0]+d[0], y = t.cell[1]+d[1], z = t.cell[2]+d[2];
    if (y < 0 || oIdx.count(k3(x, y, z))) continue;
    const double a = d[0]*t.dir[0] + d[1]*t.dir[1] + d[2]*t.dir[2];
    if (a > ba) { ba = a; bx = x; by = y; bz = z; found = true; }
  }
  if (!found) { t.alive = false; return; }  // crowded out
  oAddCell(bx, by, bz, 0, t.id);            // wood
  oAux[k3(bx, by, bz)] += W.auxDeposit;     // the deposit trail
  t.cell[0] = bx; t.cell[1] = by; t.cell[2] = bz;
  t.steps++;
  if (t.steps % W.budEvery == 0) {          // phyllotaxis: bud per budEvery
    const double azNext = t.az + W.golden;
    double p[3]; perp3(t.dir, azNext, p);
    int off[3]; axisSnap(p, off);
    const int cx = bx+off[0], cy = by+off[1], cz = bz+off[2];
    if (cy >= 0 && !oIdx.count(k3(cx, cy, cz))) {
      t.az = azNext;      // azimuth advances only when a bud actually forms
      const int idx = (int)oCellsV.size();
      oAddCell(cx, cy, cz, 1, t.id);        // bud
      OCell& c = oCellsV[idx];
      c.az = t.az;
      c.dir0[0] = p[0]; c.dir0[1] = p[1]; c.dir0[2] = p[2];
      c.par[0] = t.dir[0]; c.par[1] = t.dir[1]; c.par[2] = t.dir[2];
      oPhyllo.push_back({t.id, t.az});
      if (std::getenv("CA_DEBUG"))
        std::fprintf(stderr, "BUD tick=%d at=(%d,%d,%d) stem=%d az=%.4f "
                     "pardir=(%.4f,%.4f,%.4f) dir0=(%.4f,%.4f,%.4f)\n",
                     oTick, cx, cy, cz, t.id, t.az,
                     t.dir[0], t.dir[1], t.dir[2], p[0], p[1], p[2]);
    }
  }
  if (!t.leader && t.steps % 2 == 1) {      // light-gated leaf placement
    double p[3]; perp3(t.dir, t.az + W.golden / 2, p);
    int off[3]; axisSnap(p, off);
    const int lx = bx+off[0], ly = by+off[1], lz = bz+off[2];
    if (ly >= 0 && !oIdx.count(k3(lx, ly, lz)) &&
        oLight(lx, ly, lz) > W.leafLightMin) {
      oAddCell(lx, ly, lz, 2, t.id);        // leaf
      oLeaves.push_back(k3(lx, ly, lz));
    }
  }
}

static void oAuxStep() {                    // Jacobi diffusion + decay
  std::unordered_map<int, double> next;
  next.reserve(oAux.size() * 2);
  for (const OCell& c : oCellsV) {
    const int k = k3(c.x, c.y, c.z);
    const double a = oAux.count(k) ? oAux[k] : 0.0;
    double sum = 0;
    int n = 0;
    for (const auto& d : N6) {
      const int nk = k3(c.x+d[0], c.y+d[1], c.z+d[2]);
      if (oAux.count(nk)) { sum += oAux[nk]; n++; }
    }
    next[k] = std::max(0.0, a + W.auxD*(sum - n*a) - W.auxDecay*a);
  }
  oAux = std::move(next);
}

static void oActivateBuds() {
  // capture the leader's id BY VALUE: oTips.push_back below can reallocate
  // the vector, and a held pointer into it would dangle mid-loop
  int leadId = -1;
  for (const auto& t : oTips) if (t.leader && t.alive) { leadId = t.id; break; }
  for (OCell& c : oCellsV) {
    if (c.mat != 1 || oTick - c.born <= W.budMinAge) continue;
    const double a = oAux.count(k3(c.x, c.y, c.z)) ? oAux[k3(c.x, c.y, c.z)] : 0.0;
    if (a < W.domTheta && oLight(c.x, c.y, c.z) > W.lightMin) {
      c.mat = 0;                            // bud ignites -> new tip
      if (leadId >= 0 && c.stem == leadId &&
          (double)(oTick - c.born) / W.tipPeriod < W.domZone) {
        oDomViolTick++;                     // leader-strand in-zone ignition
      }
      const double ca = std::cos(W.branchAngle), sa = std::sin(W.branchAngle);
      const double d[3] = {c.par[0]*ca + c.dir0[0]*sa,
                           c.par[1]*ca + c.dir0[1]*sa,
                           c.par[2]*ca + c.dir0[2]*sa};
      OTip t; t.id = (int)oTips.size();
      t.pos[0] = c.x; t.pos[1] = c.y; t.pos[2] = c.z;
      t.cell[0] = c.x; t.cell[1] = c.y; t.cell[2] = c.z;
      norm3v(d, t.dir);
      t.az = c.az; t.steps = 0; t.alive = true; t.leader = false;
      if (std::getenv("CA_DEBUG"))
        std::fprintf(stderr, "IGNITE tick=%d cell=(%d,%d,%d) az=%.4f "
                     "par=(%.4f,%.4f,%.4f) dir0=(%.4f,%.4f,%.4f) "
                     "dir=(%.4f,%.4f,%.4f)\n", oTick, c.x, c.y, c.z, c.az,
                     c.par[0], c.par[1], c.par[2],
                     c.dir0[0], c.dir0[1], c.dir0[2],
                     t.dir[0], t.dir[1], t.dir[2]);
      oTips.push_back(t);
    }
  }
}

static const char* oMat(int m) { return m == 1 ? "bud" : m == 2 ? "leaf" : "wood"; }

static int runOak(int tickMs) {
  norm3v(W.sunDir.data(), oakSun);
  oAddCell(0, 0, 0, 0, 0);
  {
    OTip t; t.id = 0;
    t.pos[0] = t.pos[1] = t.pos[2] = 0;
    t.cell[0] = t.cell[1] = t.cell[2] = 0;
    t.dir[0] = 0; t.dir[1] = 1; t.dir[2] = 0;
    t.az = 0.6; t.steps = 0; t.alive = true; t.leader = true;
    oTips.push_back(t);
  }
  while (!oDone) {
    oTick++;
    oDomViolTick = 0;
    for (auto& t : oTips) if (t.alive) oStepTip(t);
    oAuxStep();
    oActivateBuds();
    if (oDomViolTick > oDomMax) oDomMax = oDomViolTick;
    int maxY = 0, alive = 0;
    for (const OCell& c : oCellsV) maxY = std::max(maxY, c.y);
    for (const auto& t : oTips) if (t.alive) alive++;
    if (maxY >= W.maxSteps || (int)oCellsV.size() >= W.maxCells) oDone = true;
    std::printf("{\"type\":\"frame\",\"tick\":%d,\"cells\":[", oTick);
    bool first = true;
    for (const OCell& c : oCellsV) {
      std::printf("%s[%d,%d,%d,\"%s\",%d,%d]", first ? "" : ",",
                  c.x, c.y, c.z, oMat(c.mat), c.born, c.stem);
      first = false;
    }
    std::printf("],\"violations\":%d,\"height\":%d,\"leaves\":%zu,"
                "\"tips\":%d,\"tipDirs\":[", oDomViolTick, maxY,
                oLeaves.size(), alive);
    // alive tip dirs on the wire so the oracle can evaluate phototropism at
    // the same point the JS reference test does (first frame with >= 60
    // leaves, else done) — tropism is a mid-growth witness: at completion
    // most alive tips are YOUNG and have not bent yet
    first = true;
    for (const auto& t : oTips) {
      if (!t.alive) continue;
      std::printf("%s[%.17g,%.17g,%.17g,%s]", first ? "" : ",",
                  t.dir[0], t.dir[1], t.dir[2], t.leader ? "true" : "false");
      first = false;
    }
    std::printf("],\"done\":%s}\n", oDone ? "true" : "false");
    std::fflush(stdout);
    if (tickMs > 0)
      std::this_thread::sleep_for(std::chrono::milliseconds(tickMs));
    if (oTick > 200000) {
      std::fprintf(stderr, "STALLED: oak at tick %d\n", oTick);
      return 2;
    }
  }
  // final ledger — everything the oracle recomputes from
  std::printf("{\"type\":\"final\",\"kind\":\"oak\",\"tick\":%d,", oTick);
  std::printf("\"phyllo\":[");
  for (size_t i = 0; i < oPhyllo.size(); i++)
    std::printf("%s[%d,%.17g]", i ? "," : "", oPhyllo[i].first,
                oPhyllo[i].second);
  std::printf("],\"aux\":{");
  bool first = true;
  for (const OCell& c : oCellsV) {
    const int k = k3(c.x, c.y, c.z);
    const double a = oAux.count(k) ? oAux[k] : 0.0;
    std::printf("%s\"%d,%d,%d\":%.17g", first ? "" : ",", c.x, c.y, c.z, a);
    first = false;
  }
  std::printf("},\"tips\":[");
  first = true;
  for (const auto& t : oTips) {
    std::printf("%s{\"cell\":[%d,%d,%d],\"dir\":[%.17g,%.17g,%.17g],"
                "\"leader\":%s,\"alive\":%s}", first ? "" : ",",
                t.cell[0], t.cell[1], t.cell[2], t.dir[0], t.dir[1], t.dir[2],
                t.leader ? "true" : "false", t.alive ? "true" : "false");
    first = false;
  }
  std::printf("],\"sun\":[%.17g,%.17g,%.17g],\"done\":true}\n",
              oakSun[0], oakSun[1], oakSun[2]);
  std::fflush(stdout);
  return 0;
}

// ============================ CREATURE (G3) ===================================
// mat: 0 skin, 1 limb, 2 eye
struct CCell { int x, y, z, mat, born; };
struct CTip {
  int id; int cell[3]; double dir[3]; int steps; bool alive, digit;
  int limbIdx;
};
struct CLimb { int root[3]; int side; bool fore; int born; };

static std::vector<CCell> cCellsV;
static std::unordered_map<int, int> cIdx;
static std::unordered_map<int, double> cA, cB;
static std::vector<CTip> cTips;
static std::vector<CLimb> cLimbs;
static std::vector<std::array<int, 3>> cEyes;
static std::string cPhase = "cleavage";
static int cTick = 0, cTuringT = 0, cGrowthStart = -1;
static double cLambdaPred = 0;
static double cOrgHead[3], cOrgVent[3], cOrgBall[3];
static int cOrgHeadKey = 0, cOrgVentKey = 0, cOrgTick = 0;
static const double cGravity[3] = {0, -1, 0};
static std::unordered_map<int, double> cTU, cTV;
static std::vector<int> cSurf;

static void cAddCell(int x, int y, int z, int mat) {
  cIdx[k3(x, y, z)] = (int)cCellsV.size();
  cCellsV.push_back({x, y, z, mat, cTick});
}

static void cCleavage() {
  const size_t n0 = cCellsV.size();         // snapshot: divisions read the
  bool grew = false;                        // LIVE map (same as JS)
  for (size_t i = 0; i < n0; i++) {
    const CCell c = cCellsV[i];
    int bx = 0, by = 0, bz = 0;
    double br = -1;
    bool found = false;
    for (const auto& d : N6) {
      const int x = c.x+d[0], y = c.y+d[1], z = c.z+d[2];
      const double r = std::sqrt((double)(x*x + y*y + z*z));
      if (r > W.ballR + 0.1 || cIdx.count(k3(x, y, z))) continue;
      if (r > br) { br = r; bx = x; by = y; bz = z; found = true; }
    }
    if (found) { cAddCell(bx, by, bz, 0); grew = true; }
  }
  if (!grew) cPhase = "axes";
}

static void cAxes() {
  double cx = 0, cy = 0, cz = 0;
  for (const CCell& c : cCellsV) { cx += c.x; cy += c.y; cz += c.z; }
  const double n = (double)cCellsV.size();
  cx /= n; cy /= n; cz /= n;
  double hd = -1e18, vd = -1e18;
  int hx = 0, hy = 0, hz = 0, vx2 = 0, vy2 = 0, vz2 = 0;
  for (const CCell& c : cCellsV) {
    // head: max x; tie-break min |z - cz| so z-symmetry survives the pick
    if (c.x > hd || (c.x == hd && std::fabs(c.z - cz) < std::fabs(hz - cz))) {
      hd = c.x; hx = c.x; hy = c.y; hz = c.z;
    }
    const double d = (c.x-cx)*cGravity[0] + (c.y-cy)*cGravity[1] +
                     (c.z-cz)*cGravity[2];
    if (d > vd) { vd = d; vx2 = c.x; vy2 = c.y; vz2 = c.z; }
  }
  cOrgHead[0] = hx; cOrgHead[1] = hy; cOrgHead[2] = hz;
  cOrgVent[0] = vx2; cOrgVent[1] = vy2; cOrgVent[2] = vz2;
  cOrgBall[0] = cx; cOrgBall[1] = cy; cOrgBall[2] = cz;
  cOrgHeadKey = k3(hx, hy, hz); cOrgVentKey = k3(vx2, vy2, vz2);
  cOrgTick = cTick;
  cPhase = "pattern";
}

static void cDiffuse(std::unordered_map<int, double>& field, int srcKey) {
  std::unordered_map<int, double> next;
  next.reserve(field.size() * 2 + 64);
  for (const CCell& c : cCellsV) {
    const int k = k3(c.x, c.y, c.z);
    const double a = field.count(k) ? field[k] : 0.0;
    double sum = 0;
    int n = 0;
    for (const auto& d : N6) {
      const int nk = k3(c.x+d[0], c.y+d[1], c.z+d[2]);
      if (field.count(nk)) { sum += field[nk]; n++; }
    }
    next[k] = std::max(0.0, a + W.mD*(sum - n*a) - W.mDecay*a);
  }
  next[srcKey] = W.mP;                      // pinned Dirichlet source
  field = std::move(next);
}

static void cGrow() {
  const double cx0 = cOrgBall[0], cy0 = cOrgBall[1], cz0 = cOrgBall[2];
  struct G { int x, y, z, k; };
  std::vector<G> grown;
  const size_t n0 = cCellsV.size();
  for (size_t i = 0; i < n0; i++) {
    const CCell& c = cCellsV[i];
    if (c.mat != 0) continue;               // differentiated tissue exited
    if ((cTick + c.x*3 + c.y*5 + c.z*7) % W.growPeriod != 0) continue;
    const double a = cA.count(k3(c.x, c.y, c.z)) ? cA[k3(c.x, c.y, c.z)] : 0.0;
    double pref[3];
    if (a > W.headMin) { pref[0] = 0.6; pref[1] = 0; pref[2] = 0; }
    else if (a < W.tailMax) { pref[0] = -1.5; pref[1] = 0; pref[2] = 0; }
    else { pref[0] = 0; pref[1] = (c.y - cy0)*0.15; pref[2] = (c.z - cz0)*0.15; }
    const double cap = c.x >= cx0 + 1 ? W.ballR + 1 : 2;
    int bx = 0, by = 0, bz = 0, bk = 0;
    double ba = -2;
    bool found = false;
    for (const auto& d : N6) {
      const int x = c.x+d[0], y = c.y+d[1], z = c.z+d[2];
      if (std::fabs(y - cy0) > cap || std::fabs(z - cz0) > cap) continue;
      if (x < cx0 - (W.ballR + W.tailLen) || x > cx0 + W.ballR + 2) continue;
      const int kk = k3(x, y, z);
      if (cIdx.count(kk)) continue;
      const double al = d[0]*pref[0] + d[1]*pref[1] + d[2]*pref[2];
      if (al > ba) { ba = al; bx = x; by = y; bz = z; bk = kk; found = true; }
    }
    if (found) grown.push_back({bx, by, bz, bk});
  }
  for (const G& g : grown) {
    if (cIdx.count(g.k)) continue;
    cAddCell(g.x, g.y, g.z, 0);
    double sa = 0, sb = 0;
    int nn = 0;
    for (const auto& d : N6) {
      const int nk = k3(g.x+d[0], g.y+d[1], g.z+d[2]);
      if (!cIdx.count(nk)) continue;
      // ALL tissue neighbors count (JS: cCells.has); a neighbor with no
      // field entry yet contributes 0 — not an exclusion
      sa += cA.count(nk) ? cA[nk] : 0.0;
      sb += cB.count(nk) ? cB[nk] : 0.0;
      nn++;
    }
    if (nn) { cA[g.k] = sa / nn; cB[g.k] = sb / nn; }
  }
}

static void cMarkFounders() {
  const int zc = (int)std::lround(cOrgBall[2]);
  for (CCell& c : cCellsV) {
    if (c.mat != 0 || c.z == zc) continue;  // no midline limbs
    const int k = k3(c.x, c.y, c.z);
    const double a = cA.count(k) ? cA[k] : 0.0;
    const double b = cB.count(k) ? cB[k] : 0.0;
    const bool fore = a >= W.foreBand[0] && a <= W.foreBand[1];
    const bool hind = !fore && a >= W.hindBand[0] && a <= W.hindBand[1];
    if ((!fore && !hind) || b < W.dvBand[0] || b > W.dvBand[1]) continue;
    int dirZ = 0;                           // needs a free flank face
    if (c.z > zc && !cIdx.count(k3(c.x, c.y, c.z+1))) dirZ = 1;
    else if (c.z < zc && !cIdx.count(k3(c.x, c.y, c.z-1))) dirZ = -1;
    if (!dirZ) continue;
    bool clear = true;                      // per-band local inhibition
    for (const CLimb& L : cLimbs) {
      if (L.fore != fore) continue;
      const int dx = L.root[0]-c.x, dy = L.root[1]-c.y, dz = L.root[2]-c.z;
      if (dx*dx + dy*dy + dz*dz < W.limbSpace*W.limbSpace) {
        clear = false; break;
      }
    }
    if (!clear) continue;
    c.mat = 1;                              // the founder IS limb tissue
    cLimbs.push_back({{c.x, c.y, c.z}, dirZ, fore, cTick});
  }
}

static void cSproutLimbs() {
  for (int i = 0; i < (int)cLimbs.size(); i++) {
    const CLimb& L = cLimbs[i];
    const double d[3] = {0, -0.15, (double)L.side};
    CTip t; t.id = (int)cTips.size();
    t.cell[0] = L.root[0]; t.cell[1] = L.root[1]; t.cell[2] = L.root[2];
    norm3v(d, t.dir);
    t.steps = 0; t.alive = true; t.digit = false; t.limbIdx = i;
    cTips.push_back(t);
  }
}

static void cStepTips() {
  const size_t n0 = cTips.size();           // snapshot: digits pushed during
  for (size_t i = 0; i < n0; i++) {         // iteration don't step this tick
    CTip& t = cTips[i];
    if (!t.alive) continue;
    int bx = 0, by = 0, bz = 0;
    double ba = -2;
    bool found = false;
    for (const auto& d : N6) {
      const int x = t.cell[0]+d[0], y = t.cell[1]+d[1], z = t.cell[2]+d[2];
      if (cIdx.count(k3(x, y, z))) continue;
      const double al = d[0]*t.dir[0] + d[1]*t.dir[1] + d[2]*t.dir[2];
      if (al > ba) { ba = al; bx = x; by = y; bz = z; found = true; }
    }
    if (!found) { t.alive = false; continue; }
    cAddCell(bx, by, bz, 1);                // limb tissue
    t.cell[0] = bx; t.cell[1] = by; t.cell[2] = bz;
    t.steps++;
    if (!t.digit && t.steps >= W.limbLen) {
      // COPY before push_back: a vector reallocation would leave the
      // reference `t` dangling, and the next digit would read freed heap
      // (measured: wild limb cells at x~528/y~-1e9, run-to-run garbage —
      // 4 orphan cells broke symmetry 1.0, connectivity, and corrLogAX)
      const int cc[3] = {t.cell[0], t.cell[1], t.cell[2]};
      const double cd[3] = {t.dir[0], t.dir[1], t.dir[2]};
      const int limbIdx = t.limbIdx;
      t.alive = false;
      for (int j = 0; j < W.digits; j++) {
        CTip dt; dt.id = (int)cTips.size();
        dt.cell[0] = cc[0]; dt.cell[1] = cc[1]; dt.cell[2] = cc[2];
        perp3(cd, j * W.golden, dt.dir);
        dt.steps = 0; dt.alive = true; dt.digit = true; dt.limbIdx = limbIdx;
        cTips.push_back(dt);
      }
    } else if (t.digit && t.steps >= W.digitLen) {
      t.alive = false;
    }
  }
}

static void cPickEyes() {
  cEyes.clear();
  const int zc = (int)std::lround(cOrgBall[2]);
  for (const int side : {1, -1}) {
    int bIdx = -1, bz2 = 0;
    double ba = -1;
    for (size_t i = 0; i < cCellsV.size(); i++) {
      const CCell& c = cCellsV[i];
      if (c.mat != 0) continue;             // never repaint a limb founder
      if ((c.z - zc) * side <= 0) continue;
      if (c.x < cOrgBall[0] + W.eyeXMin) continue;
      const double a = cA.count(k3(c.x, c.y, c.z)) ? cA[k3(c.x, c.y, c.z)] : 0.0;
      if (a < W.eyeMin) continue;
      const int az = std::abs(c.z - zc);
      if (az > bz2 || (az == bz2 && a > ba)) { bz2 = az; ba = a; bIdx = (int)i; }
    }
    if (bIdx >= 0) {
      cCellsV[bIdx].mat = 2;                // eye
      cEyes.push_back({cCellsV[bIdx].x, cCellsV[bIdx].y, cCellsV[bIdx].z});
    }
  }
}

static void cTuringInit() {
  cSurf.clear(); cTU.clear(); cTV.clear();
  const double u0 = W.tA + W.tB, v0 = W.tB / (u0 * u0);
  for (const CCell& c : cCellsV) {
    bool boundary = false;
    for (const auto& d : N6)
      if (!cIdx.count(k3(c.x+d[0], c.y+d[1], c.z+d[2]))) { boundary = true; break; }
    if (!boundary) continue;
    const int k = k3(c.x, c.y, c.z);
    const int h = c.x*31 + c.y*57 + c.z*101;
    cTU[k] = u0 + (hash01(h) - 0.5) * 0.02;
    cTV[k] = v0 + (hash01(h + 7) - 0.5) * 0.02;
    cSurf.push_back(k);
  }
  // lambda* prediction on the LATTICE dispersion s_eff(k) = 4 sin^2(k/2)
  const double fu = 2*W.tB/u0 - 1, fv = u0*u0, gu = -2*W.tB/u0, gv = -u0*u0;
  double bestK = 0.05, bestMu = -1e18;
  for (double k = 0.05; k < 4; k += 0.01) {
    const double s = 4 * std::sin(k / 2) * std::sin(k / 2);
    const double tr = fu + gv - (W.tDu + W.tDv) * s;
    const double det = (fu - W.tDu*s) * (gv - W.tDv*s) - fv*gu;
    const double disc = tr*tr - 4*det;
    const double mu = disc >= 0 ? (tr + std::sqrt(disc)) / 2 : tr / 2;
    if (mu > bestMu) { bestMu = mu; bestK = k; }
  }
  cLambdaPred = 2 * 3.14159265358979323846 / bestK;
}

static void cTuringStep() {
  std::unordered_map<int, double> nU, nV;
  nU.reserve(cSurf.size() * 2); nV.reserve(cSurf.size() * 2);
  for (const int k : cSurf) {
    const double u = cTU[k], v = cTV[k];
    double lu = 0, lv = 0;
    for (const auto& d : N6) {              // no-flux BC
      const int nk = k3(kx(k)+d[0], ky(k)+d[1], kz(k)+d[2]);
      if (cTU.count(nk)) { lu += cTU[nk] - u; lv += cTV[nk] - v; }
    }
    const double uvv = u*u*v;
    nU[k] = u + W.tDt * (W.tA - u + uvv + W.tDu * lu);
    nV[k] = v + W.tDt * (W.tB - uvv + W.tDv * lv);
  }
  cTU = std::move(nU); cTV = std::move(nV);
}

static const char* cMat(int m) { return m == 1 ? "limb" : m == 2 ? "eye" : "skin"; }

static void cEmitFrame(bool done) {
  int minX = 1 << 30;
  for (const CCell& c : cCellsV) minX = std::min(minX, c.x);
  std::printf("{\"type\":\"frame\",\"tick\":%d,\"cells\":[", cTick);
  bool first = true;
  for (const CCell& c : cCellsV) {
    std::printf("%s[%d,%d,%d,\"%s\"]", first ? "" : ",",
                c.x, c.y, c.z, cMat(c.mat));
    first = false;
  }
  std::printf("],\"violations\":0,\"phase\":\"%s\",\"limbs\":%zu,"
              "\"eyes\":%zu,\"minX\":%d,\"done\":%s}\n", cPhase.c_str(),
              cLimbs.size(), cEyes.size(), minX, done ? "true" : "false");
  std::fflush(stdout);
}

static int runCrit(int tickMs) {
  cAddCell(0, 0, 0, 0);                     // the zygote
  bool done = false;
  while (!done) {
    cTick++;
    if (cPhase == "cleavage") cCleavage();
    else if (cPhase == "axes") cAxes();
    else if (cPhase == "pattern") {
      cDiffuse(cA, cOrgHeadKey);
      cDiffuse(cB, cOrgVentKey);
      if (cTick - cOrgTick >= W.patternTicks) {
        cMarkFounders();
        cGrowthStart = cTick;
        cPhase = "growth";
      }
    } else if (cPhase == "growth") {
      if (cTick == cGrowthStart + W.limbFieldDelay) cSproutLimbs();
      cStepTips();                          // limb buds step EVERY tick and
      cGrow();                              // BEFORE body division
      cDiffuse(cA, cOrgHeadKey);
      cDiffuse(cB, cOrgVentKey);
      int minX = 1 << 30;
      for (const CCell& c : cCellsV) minX = std::min(minX, c.x);
      const bool tailDone = minX <= cOrgBall[0] - (W.ballR + W.tailLen - 2);
      bool tipsAlive = false;
      for (const auto& t : cTips) if (t.alive) { tipsAlive = true; break; }
      const bool tipsDead = !cTips.empty() && !tipsAlive;
      if ((tailDone && cLimbs.size() >= 4 && tipsDead) ||
          cTick >= W.growDeadline || (int)cCellsV.size() >= W.maxCells) {
        cPickEyes();
        cTuringInit();
        cPhase = "turing";
        cTuringT = 0;
      }
    } else if (cPhase == "turing") {
      for (int i = 0; i < W.tSteps; i++) cTuringStep();
      cDiffuse(cA, cOrgHeadKey);            // fields keep relaxing — the
      cDiffuse(cB, cOrgVentKey);            // oracle reads the STEADY gradient
      if (++cTuringT >= W.turingTicks) { cPhase = "done"; done = true; }
    }
    cEmitFrame(done);
    if (tickMs > 0)
      std::this_thread::sleep_for(std::chrono::milliseconds(tickMs));
    if (cTick > 200000) {
      std::fprintf(stderr, "STALLED: creature at tick %d\n", cTick);
      return 2;
    }
  }
  // final ledger — the oracle recomputes everything from this
  std::printf("{\"type\":\"final\",\"kind\":\"creature\",\"tick\":%d,", cTick);
  std::printf("\"cells\":[");
  bool first = true;
  for (const CCell& c : cCellsV) {
    std::printf("%s[%d,%d,%d,\"%s\"]", first ? "" : ",",
                c.x, c.y, c.z, cMat(c.mat));
    first = false;
  }
  std::printf("],\"morphA\":{");
  first = true;
  for (const CCell& c : cCellsV) {
    const int k = k3(c.x, c.y, c.z);
    const double a = cA.count(k) ? cA[k] : 0.0;
    std::printf("%s\"%d,%d,%d\":%.17g", first ? "" : ",", c.x, c.y, c.z, a);
    first = false;
  }
  std::printf("},\"turingU\":{");
  first = true;
  for (const int k : cSurf) {
    std::printf("%s\"%d,%d,%d\":%.17g", first ? "" : ",", kx(k), ky(k), kz(k),
                cTU[k]);
    first = false;
  }
  std::printf("},\"surf\":[");
  first = true;
  for (const int k : cSurf) {
    std::printf("%s\"%d,%d,%d\"", first ? "" : ",", kx(k), ky(k), kz(k));
    first = false;
  }
  std::printf("],\"limbRoots\":[");
  for (size_t i = 0; i < cLimbs.size(); i++)
    std::printf("%s[%d,%d,%d]", i ? "," : "", cLimbs[i].root[0],
                cLimbs[i].root[1], cLimbs[i].root[2]);
  std::printf("],\"eyes\":[");
  for (size_t i = 0; i < cEyes.size(); i++)
    std::printf("%s[%d,%d,%d]", i ? "," : "", cEyes[i][0], cEyes[i][1],
                cEyes[i][2]);
  int dig = 0;
  for (const auto& t : cTips) if (t.digit) dig++;
  std::printf("],\"digits\":%d,\"lambdaPred\":%.17g,", dig, cLambdaPred);
  std::printf("\"organizers\":{\"head\":[%.17g,%.17g,%.17g],"
              "\"ventral\":[%.17g,%.17g,%.17g],"
              "\"ball\":[%.17g,%.17g,%.17g]},\"done\":true}\n",
              cOrgHead[0], cOrgHead[1], cOrgHead[2],
              cOrgVent[0], cOrgVent[1], cOrgVent[2],
              cOrgBall[0], cOrgBall[1], cOrgBall[2]);
  std::fflush(stdout);
  return 0;
}

// ============================ main ============================================
int main(int argc, char** argv) {
  std::string exeDir = ".";
  if (argc > 0) {
    std::string a0 = argv[0];
    const size_t s = a0.find_last_of("/\\");
    if (s != std::string::npos) exeDir = a0.substr(0, s);
  }
  const std::string genomePath =
      argc > 2 ? argv[2] : exeDir + "/genomes/wall.chimera";
  W = loadGenome(genomePath);
  const int tickMs = argc > 1 ? std::atoi(argv[1]) : W.tickMs;
  const double cellOut = W.kind == "wall" ? 0 : W.cell;
  std::printf("{\"type\":\"meta\",\"kind\":\"%s\",\"name\":\"%s\","
              "\"cell\":%.17g}\n", W.kind.c_str(), W.name.c_str(), cellOut);
  std::fflush(stdout);
  if (W.kind == "oak") return runOak(tickMs);
  if (W.kind == "creature") return runCrit(tickMs);
  return runWall(tickMs);
}
