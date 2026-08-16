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
//   embodiment genomes (bear): after the final ledger —
//              {"type":"rig","chains":[{limbIdx,fore,side,elbow,path,digits,
//              rest}...],"ears":[[x,y,z]...],"waveCh":W}
//              then either one {"type":"selftest",...} line (argv[3]) or an
//              interactive anim loop driven by stdin commands (wave/walk/
//              rest/auto) emitting {"type":"anim","tick":N,"cmd":C,"res":R,
//              "body":[bx,0,0],"visitor":[x,y,z]|null,"posed":[[x,y,z,px,py,
//              pz],...],...} — posed = FK-rigged limb/digit cells, cell units.
//              Growth frames carry done:false on embodiment genomes so the
//              relay does not cut the stream before the anim frames.
// 3D cell identity is the integer triple — oracles need no float compares.
//
// N4 Rule 0 (stated before the build):
//   STATEMENT:  the G4 embodiment layer (FK chains read off the grown limb
//               ledger, damped-pseudoinverse IK, gait, wave) and the G5
//               learner (retinal senses -> Q-learning over rest/wave/walk)
//               are language-independent: this core reproduces the JS
//               reference (spiace_grow.html ?genome=bear) number for number.
//   PREDICTION: rig 4 chains x 2 joints + 2 ears, waveCh = fore/+z; wave
//               minResidual 0.04881518056285238 at raiseIters 15, iters 230;
//               400-tick walk: bodyX += 400*4*2/60, diagonal gait in phase,
//               ipsilateral anti-phase; senses 1/3/2/5/0; 320 episodes:
//               visits [9450,89,93,92,1736,1888,1958], last30 > first30+0.3,
//               greedy == [0,1,1,1,2,2,2], final bodyX 789.8666666666321.
//   FALSIFIER:  any of those off (beyond 1e-9 float dust) in the selftest
//               ledger, or the Python-oracle FK segment audit > 1e-6, kills
//               the port claim (test_native.py F-N4a..j).
//
// N5 Rule 0 (stated before the build):
//   STATEMENT:  a genome-declared gravity kernel (SI in, sim units derived)
//               with rigid-body COM dynamics and velocity-projection ground
//               contact carries the grown bear at EXACT rest equilibrium —
//               and free fall under it follows the symplectic-Euler ledger
//               E_n = gH - g^2 n/2 exactly. Physics is numerically INERT at
//               equilibrium: every N4 number stays bit-identical with it ON.
//   PREDICTION: g_sim = 9.81/(60^2*0.06) = 9.81/216 cells/tick^2; the ground
//               plane is DERIVED from the grown body (lowest rest cell,
//               y = -4) — nothing placed by hand; a drop from H = 8 body
//               heights (64 cells; the 8 puts the predicted terminal drift
//               ~1.8% under the 2% bound) contacts at the first tick n with
//               n(n+1) >= 2H/g  (n = 53; continuous sqrt(2H/g) = 53.09);
//               free-fall energy matches the ledger to 1e-12; after landing,
//               300 ticks hold velY == 0 exactly and penetration within 1 ULP
//               (measured 4.4e-16 — the projection's add/subtract rounding).
//   FALSIFIER:  contact tick off by more than 1 from the discrete/analytic
//               prediction, ledger mismatch > 1e-12, any post-landing jitter,
//               or ANY N4 number moving kills the physics claim
//               (test_native.py F-N5a..e).
//
// N6 Rule 0 (stated before the build):
//   STATEMENT:  the world the bear stands on is GROWN, not placed — a
//               seeded integer LCG + Jacobi relaxation CA
//               (h' = (a+2b+c+2)>>2) produces a deterministic heightfield,
//               and the N5 contact law generalizes from a flat plane to
//               "the highest terrain under the grown footprint" without
//               touching a single body-local number.
//   PREDICTION: the CA terminates when the walkability contract holds (max
//               |slope| <= 1 cell/column, edges included) — the iteration
//               count is an output, not an input; the ENTIRE N4 ledger
//               (wave/gait/senses/Q/visits/bodyX) is bit-identical on the
//               hills; the 400-tick walk's per-tick bodyY trace is
//               replicable by an oracle running the same IEEE ops to 0.0;
//               the drop law (contact at the first n with n(n+1) >= 2H/g)
//               holds on any terrain height.
//   FALSIFIER:  wire terrain != Python-oracle terrain on ANY column, any N4
//               field moving on the hills, walk-trace divergence > 0, or a
//               contact tick off the discrete prediction kills the claim
//               (test_native.py F-N6a..e).
//
// N7 Rule 0 (stated before the build):
//   STATEMENT:  locomotion is EARNED, not imposed — the body advances at the
//               stance-foot sweep rate A*w*|cos phi| (w = 2*pi/T) while ground
//               contact holds, and not at all while airborne. The retired
//               no-slip constant 4A/T is exactly the cycle-mean of the earned
//               rate: the continuous mean of |cos| over a cycle is 2/pi, so
//               A*(2*pi/T)*(2/pi) = 4A/T. Flat-ground steady walking is
//               unchanged ON AVERAGE, but each tick now carries the gait's
//               true oscillation, and flight carries none.
//   PREDICTION: (a) a walking bear in free fall translates EXACTLY zero
//               cells while contact is false (bit-exact, not epsilon); (b)
//               the 400-tick flat walk's bodyX equals the discrete sum
//               sum_t A*(2*pi/T)*|cos(2*pi*t/T)| computed in the same IEEE
//               op order; (c) one full gait cycle sums to 4A within the
//               quadrature error of the |cos| Riemann sum (< 1%).
//   FALSIFIER:  any nonzero airborne translation, bodyX off the oracle's
//               discrete sum by > 1e-9, or the cycle mean off 4A by > 1%
//               kills the claim (test_native.py F-N7a..c).
//   KNOWN CONSEQUENCE (deliberate, documented): the G5 learner ledger
//               diverges from the JS reference — the beckon gradient d0-d1
//               now oscillates per tick with the stride, so visits/Q/
//               first30/last30/minResAuto/bodyXfinal all move. The
//               JS-imposed-stride reference is RETIRED; the Python oracle in
//               test_native.py replicates the full wave+walk+learn protocol
//               under the new law (lossy-double LCG, spec hypot, IK port)
//               and becomes the reference of record.
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
// Run:   ./ca_core.exe [tick_ms] [genome_path] [selftest]
//          tick_ms default = the genome's tickMs; genome_path default =
//          <exe dir>/genomes/wall.chimera; selftest = embodiment genomes run
//          the synchronous G4/G5 protocol and print one ledger line

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <mutex>
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
  // embodiment (G4 rig/IK + G5 learner) — creature kind, required when
  // embodiment = 1; every constant's derivation is in the genome file
  int embodiment = 0;
  double b4A = 0, b4Lam = 0, b4Dth = 0, b4ThMax = 0, b4WaveRes = 0,
         b4WaveTh = 0, b4LowerRes = 0;
  int b4T = 0, b4Iters = 0, b4Hold = 0;
  double l5Near = 0, l5Far = 0, l5BearEps = 0, l5Alpha = 0, l5Gamma = 0,
         l5Eps0 = 0, l5EpsDecay = 0, l5EpsMin = 0;
  int l5EpTicks = 0;
  double r5WaveNear = 0, r5WaveFar = 0, r5WaveAbsent = 0, r5WalkTick = 0,
         r5Beckon = 0, r5Startle = 0, r5RestAbsent = 0, r5RestPresent = 0;
  // N5 physics membrane — SI in, sim units derived (see bear.chimera); the
  // ground plane itself is derived from the grown body, never declared
  double gravity = 0, tickHz = 0;
  // N6 terrain membrane — optional; a CA-grown fixed-point heightfield over
  // [terrainX0, terrainX1], heights k/terrainScale cells as offsets from the
  // body's ground; terrainSlope is the walkability contract (scale units)
  int terrain = 0, terrainSeed = 0, terrainAmp = 0, terrainX0 = 0,
      terrainX1 = 0, terrainScale = 1024, terrainSlope = 0;
  // N8 goal membrane — optional, requires terrain; a flag at goalX. The core
  // derives everything else (careful amplitude, slip threshold, episode
  // budget) from the physics constants — the genome declares only the flag.
  int goal = 0, goalX = 0;
  // T1 vox membrane — an IMPORTED cell set (kind=vox): the body is DATA
  // (genomes/<cellsFile>), not grown. The rig chains ride that same data file;
  // physics/gait/nav are unchanged (the shape-agnostic claim).
  std::string cellsFile;
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
    if (kv.count("embodiment") && std::stoi(kv["embodiment"]) == 1) {
      g.embodiment = 1;
      g.b4A = needD("b4A"); g.b4Lam = needD("b4Lam"); g.b4Dth = needD("b4Dth");
      g.b4ThMax = needD("b4ThMax"); g.b4WaveRes = needD("b4WaveRes");
      g.b4WaveTh = needD("b4WaveTh"); g.b4LowerRes = needD("b4LowerRes");
      g.b4T = needI("b4T"); g.b4Iters = needI("b4Iters");
      g.b4Hold = needI("b4Hold");
      g.l5Near = needD("l5Near"); g.l5Far = needD("l5Far");
      g.l5BearEps = needD("l5BearEps"); g.l5Alpha = needD("l5Alpha");
      g.l5Gamma = needD("l5Gamma"); g.l5Eps0 = needD("l5Eps0");
      g.l5EpsDecay = needD("l5EpsDecay"); g.l5EpsMin = needD("l5EpsMin");
      g.l5EpTicks = needI("l5EpTicks");
      g.r5WaveNear = needD("r5WaveNear"); g.r5WaveFar = needD("r5WaveFar");
      g.r5WaveAbsent = needD("r5WaveAbsent"); g.r5WalkTick = needD("r5WalkTick");
      g.r5Beckon = needD("r5Beckon"); g.r5Startle = needD("r5Startle");
      g.r5RestAbsent = needD("r5RestAbsent");
      g.r5RestPresent = needD("r5RestPresent");
      g.gravity = needD("gravity"); g.tickHz = needD("tickHz");
      if (kv.count("terrain") && std::stoi(kv["terrain"]) == 1) {
        g.terrain = 1;                            // N6: grow the world too
        g.terrainSeed = needI("terrainSeed");
        g.terrainAmp = needI("terrainAmp");
        g.terrainX0 = needI("terrainX0"); g.terrainX1 = needI("terrainX1");
        g.terrainSlope = needI("terrainSlope");
        if (kv.count("terrainScale"))
          g.terrainScale = std::stoi(kv["terrainScale"]);
        if (g.terrainAmp < 0 || g.terrainX1 <= g.terrainX0 ||
            g.terrainSlope < 1 || g.terrainScale < 1 ||
            (g.terrainScale & (g.terrainScale - 1)) != 0)   // power of 2: the
          die4("INVALID: terrain sanity bounds failed in " + path);   // h/S
      }                                                   // division is exact
      if (kv.count("goal") && std::stoi(kv["goal"]) == 1) {
        g.goal = 1;                                     // N8: the flag
        g.goalX = needI("goalX");
        if (!g.terrain)
          die4("INVALID: goal requires the terrain membrane in " + path);
        if (g.goalX <= g.terrainX0 || g.goalX >= g.terrainX1)
          die4("INVALID: goalX outside the terrain domain in " + path);
      }
      if (g.b4T <= 0 || g.b4Iters <= 0 || g.b4Dth <= 0 || g.b4ThMax <= 0 ||
          g.l5Near <= 0 || g.l5Far <= g.l5Near || g.l5EpTicks <= 0 ||
          g.l5Alpha <= 0 || g.l5Gamma <= 0 || g.l5Gamma >= 1 ||
          g.gravity <= 0 || g.tickHz <= 0)
        die4("INVALID: embodiment sanity bounds failed in " + path);
    }
  } else if (g.kind == "vox") {
    // T1: an imported cell set — the body is DATA, not grown. Only the B4
    // gait constants and the N5 physics membrane are declared; the rig
    // chains ride the cellsFile. L5/R5/N6/N8 are absent (stand/walk only).
    g.cell = needD("cell"); g.cellsFile = need("cellsFile");
    g.b4A = needD("b4A"); g.b4Lam = needD("b4Lam"); g.b4Dth = needD("b4Dth");
    g.b4ThMax = needD("b4ThMax"); g.b4Iters = needI("b4Iters");
    g.b4T = needI("b4T"); g.gravity = needD("gravity"); g.tickHz = needD("tickHz");
    if (g.cell <= 0 || g.b4A <= 0 || g.b4T <= 0 || g.b4Iters <= 0 ||
        g.b4Lam <= 0 || g.gravity <= 0 || g.tickHz <= 0)
      die4("INVALID: vox sanity bounds failed in " + path);
    if (kv.count("embodiment") && std::stoi(kv["embodiment"]) == 1)
      g.embodiment = 1;
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
  std::vector<std::array<int, 3>> path;   // G4 chain ledger: root + each
};                                        // stepped cell (digits: spawn cell)
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
    t.path.push_back({L.root[0], L.root[1], L.root[2]});   // G4 chain ledger
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
    t.path.push_back({bx, by, bz});         // G4 chain ledger
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
        dt.path.push_back({cc[0], cc[1], cc[2]});   // digits start at spawn
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

static const char* cMat(int m) { return m == 1 ? "limb" : m == 2 ? "eye"
                                           : m == 3 ? "ear" : "skin"; }

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

// G4/G5 embodiment layer (defined below runCrit): rig, wire emitters, modes
static void bearRig();
static void learnReset();
static void emitRig();
static void emitSelftest();
static int runEmbodiment(int tickMs);
static void physTick();                   // N5: defined with the N5 block
static void navInit();                    // N8: defined with the N8 block
// T1 vox membrane (defined near main): an imported cell set, rig off that data
static int runVox(int tickMs, bool selftest);

static int runCrit(int tickMs, bool selftest) {
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
    // embodiment genomes keep done:false on growth frames so the relay does
    // not cut the SSE stream before the anim frames (the final ledger still
    // carries done:true; the viewer marks COMPLETE from that)
    cEmitFrame(done && !W.embodiment);
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
  if (W.embodiment) {
    bearRig();                 // G4: rig the finished body off the ledger
    learnReset();              // G5: fresh learner (eps = EPS0, rng = 1337)
    if (selftest) { emitRig(); emitSelftest(); return 0; }
    return runEmbodiment(tickMs);   // G4/G5: interactive stdin-driven anim
  }
  return 0;
}
// Ported verbatim from spiace_grow.html lines 1019-1430 (the JS reference).
// Statement/prediction/falsifier for this layer live in the file header (N4).
// ============================ EMBODIMENT (G4 rig/IK + G5 learner) ============
// Ported verbatim from spiace_grow.html lines 1019-1430 (the JS reference).
// Math.hypot is the ECMAScript spec algorithm (max * sqrt(sum (n/max)^2)),
// NOT sqrt(x^2+y^2+z^2) — the learner's float trail depends on the rounding.
static double hypot3(double a, double b, double c) {
  a = std::fabs(a); b = std::fabs(b); c = std::fabs(c);
  const double mx = std::fmax(a, std::fmax(b, c));
  if (mx == 0) return 0;
  const double s = (a/mx)*(a/mx) + (b/mx)*(b/mx) + (c/mx)*(c/mx);
  return mx * std::sqrt(s);
}
static void bnorm3(const double v[3], double out[3]) {   // JS norm3 (hypot)
  double l = hypot3(v[0], v[1], v[2]);
  if (l == 0) l = 1.0;
  out[0] = v[0]/l; out[1] = v[1]/l; out[2] = v[2]/l;
}
// rotate v about unit axis a by th (Rodrigues) — the T_joint of the product
static void rot3(const double v[3], const double a[3], double th,
                 double out[3]) {
  const double c = std::cos(th), s = std::sin(th);
  const double d = a[0]*v[0] + a[1]*v[1] + a[2]*v[2];
  out[0] = v[0]*c + (a[1]*v[2]-a[2]*v[1])*s + a[0]*d*(1-c);
  out[1] = v[1]*c + (a[2]*v[0]-a[0]*v[2])*s + a[1]*d*(1-c);
  out[2] = v[2]*c + (a[0]*v[1]-a[1]*v[0])*s + a[2]*d*(1-c);
}
static void sub3(const double u[3], const double v[3], double out[3]) {
  out[0] = u[0]-v[0]; out[1] = u[1]-v[1]; out[2] = u[2]-v[2];
}
static void add3(const double u[3], const double v[3], double out[3]) {
  out[0] = u[0]+v[0]; out[1] = u[1]+v[1]; out[2] = u[2]+v[2];
}
static void cross3(const double a[3], const double b[3], double out[3]) {
  out[0] = a[1]*b[2]-a[2]*b[1]; out[1] = a[2]*b[0]-a[0]*b[2];
  out[2] = a[0]*b[1]-a[1]*b[0];
}

struct BChain {
  int limbIdx; bool fore; int side;
  std::vector<std::array<int, 3>> path;                 // the GROWN ledger
  int elbow;
  double theta[2] = {0, 0};
  std::vector<std::vector<std::array<int, 3>>> digits;  // digit paths
  double rest[3] = {0, 0, 0};                           // theta=0 IS grown
};
struct Bear {
  bool rigged = false;
  std::vector<BChain> rig;
  std::string cmd = "rest";
  long cmdTick = 0, iters = 0, raiseIters = -1;         // -1 = JS null
  double minResidual = 0; bool hasMinRes = false;
  double lastRes = 0; bool hasLastRes = false;
  bool waveDone = false;
  std::string wavePhase;                                // "" = JS null
  long holdUntil = 0;
  double thetaMaxEver = 0;
  bool nan = false;
  double body[3] = {0, 0, 0};
  // N5 physics state — bodyY is the vertical offset ABOVE the derived rest
  // contact (groundY == groundMinY, so rest bodyY == 0 exactly); cell units
  double bodyY = 0, velY = 0, groundY = 0, groundMinY = 0, bodyH = 0;
  bool contact = true;
  // N6 terrain state — grown footprint x-range and the support under it
  int bodyLoX = 0, bodyHiX = 0;
  double lastGround = 0;                            // groundAt() at physTick
  std::vector<std::array<double, 3>> walkTrace;     // {tick, bodyY, ground}
  std::vector<std::pair<long, std::vector<std::array<double, 3>>>> gaitLog;
  int waveCh = -1, nEars = 0;
};
static Bear bear;
static double gSim = 0;                   // N5: derived gravity, cells/tick^2

// posed lattice position of chain cell path[k]: T(theta) = prod T_joint,
// joint axes carried by upstream rotations (matrix product, not parallel)
static void fkPoint(const BChain& ch, int k, double out[3]) {
  const auto& P = ch.path;
  const double t0 = ch.theta[0], t1 = ch.theta[1];
  const double a0[3] = {1, 0, 0}, a1r[3] = {0, 1, 0};   // shoulder pitch /
  const double P0[3] = {(double)P[0][0], (double)P[0][1], (double)P[0][2]};
  const double Pe0[3] = {(double)P[ch.elbow][0], (double)P[ch.elbow][1],
                         (double)P[ch.elbow][2]};       // elbow swing
  double Pe[3];
  { double d[3], r[3]; sub3(Pe0, P0, d); rot3(d, a0, t0, r); add3(P0, r, Pe); }
  const double Pk[3] = {(double)P[k][0], (double)P[k][1], (double)P[k][2]};
  if (k <= ch.elbow) {
    double d[3], r[3]; sub3(Pk, P0, d); rot3(d, a0, t0, r); add3(P0, r, out);
  } else {
    double d[3], r1[3], r2[3];
    sub3(Pk, Pe0, d); rot3(d, a1r, t1, r1); rot3(r1, a0, t0, r2);
    add3(Pe, r2, out);
  }
}
static void fkDigit(const BChain& ch,
                    const std::vector<std::array<int, 3>>& dp, int j,
                    double out[3]) {                    // digits ride wrist
  const auto& w0i = ch.path[ch.path.size() - 1];
  const double a0[3] = {1, 0, 0}, a1r[3] = {0, 1, 0};
  double Pw[3]; fkPoint(ch, (int)ch.path.size() - 1, Pw);
  const double d[3] = {(double)dp[j][0] - w0i[0], (double)dp[j][1] - w0i[1],
                       (double)dp[j][2] - w0i[2]};
  double r1[3], r2[3];
  rot3(d, a1r, ch.theta[1], r1);
  rot3(r1, a0, ch.theta[0], r2);
  add3(Pw, r2, out);
}
static void solve3(const double M[3][3], const double b[3], double out[3]) {
  auto d3 = [](const double N[3][3]) {                // Cramer, no library
    return N[0][0]*(N[1][1]*N[2][2]-N[1][2]*N[2][1])
         - N[0][1]*(N[1][0]*N[2][2]-N[1][2]*N[2][0])
         + N[0][2]*(N[1][0]*N[2][1]-N[1][1]*N[2][0]);
  };
  const double det = d3(M);
  if (std::fabs(det) < 1e-12) { out[0] = out[1] = out[2] = 0; return; }
  for (int c = 0; c < 3; c++) {
    double N[3][3];
    for (int r = 0; r < 3; r++)
      for (int cc = 0; cc < 3; cc++) N[r][cc] = cc == c ? b[r] : M[r][cc];
    out[c] = d3(N) / det;
  }
}
// one damped-pseudoinverse correction: dtheta = Jt (J Jt + lam I)^-1 e
static double ikStep(BChain& ch, const double T[3]) {
  const double P0[3] = {(double)ch.path[0][0], (double)ch.path[0][1],
                        (double)ch.path[0][2]};
  double tip[3]; fkPoint(ch, (int)ch.path.size() - 1, tip);
  double e[3]; sub3(T, tip, e);
  const double res = hypot3(e[0], e[1], e[2]);
  const double a0[3] = {1, 0, 0};
  double a1w[3]; { const double y[3] = {0, 1, 0}; rot3(y, a0, ch.theta[0], a1w); }
  double Pe[3]; fkPoint(ch, ch.elbow, Pe);
  double j0[3], j1[3], r0[3], r1[3];
  sub3(tip, P0, r0); cross3(a0, r0, j0);        // dtip/dtheta = a x r (exact)
  sub3(tip, Pe, r1); cross3(a1w, r1, j1);
  const double M[3][3] = {
    {j0[0]*j0[0]+j1[0]*j1[0]+W.b4Lam, j0[0]*j0[1]+j1[0]*j1[1],
     j0[0]*j0[2]+j1[0]*j1[2]},
    {j0[1]*j0[0]+j1[1]*j1[0], j0[1]*j0[1]+j1[1]*j1[1]+W.b4Lam,
     j0[1]*j0[2]+j1[1]*j1[2]},
    {j0[2]*j0[0]+j1[2]*j1[0], j0[2]*j0[1]+j1[2]*j1[1],
     j0[2]*j0[2]+j1[2]*j1[2]+W.b4Lam}};
  double w[3]; solve3(M, e, w);
  const double* J[2] = {j0, j1};
  for (int j = 0; j < 2; j++) {
    double d = J[j][0]*w[0] + J[j][1]*w[1] + J[j][2]*w[2];
    d = std::fmax(-W.b4Dth, std::fmin(W.b4Dth, d));
    ch.theta[j] = std::fmax(-W.b4ThMax, std::fmin(W.b4ThMax, ch.theta[j] + d));
  }
  const double tm = std::fmax(std::fabs(ch.theta[0]), std::fabs(ch.theta[1]));
  if (tm > bear.thetaMaxEver) bear.thetaMaxEver = tm;
  if (!std::isfinite(ch.theta[0]) || !std::isfinite(ch.theta[1]) ||
      !std::isfinite(res))
    bear.nan = true;
  bear.iters++;
  return res;
}
// ============================ N6 TERRAIN MEMBRANE =============================
// The world is GROWN, not placed: a seeded integer LCG lays down noise, then
// a relaxation CA smooths it in FIXED POINT (heights are k/terrainScale
// cells; the scale is a power of 2 so h/scale stays IEEE-exact) until the
// walkability contract holds (max |slope| <= terrainSlope, flat-world edges
// included) — the iteration count is an OUTPUT, never an input. The update
// h' = trunc((a+2b+c)/4) truncates toward zero: symmetric and contractive.
// (An earlier integer-cell form with (s+2)>>2 rounding FAILED the contract —
// the quantization has slope-2 attractors, measured stuck from iteration 2
// through 60. Documented in the genome and the plan.) The Python oracle in
// test_native.py replicates every op exactly (pure ints).
static bool terrainOn = false;
static std::map<int, int> terrH;                  // column -> fixed-point h
static int terrIters = 0;
static void genTerrain() {
  if (!W.terrain) return;
  terrainOn = true;
  const int S = W.terrainScale;
  long long st = W.terrainSeed;                   // integer LCG (no doubles)
  auto nx = [&]() { st = (st * 1103515245 + 12345) & 0x7fffffff; return st; };
  for (int x = W.terrainX0; x <= W.terrainX1; x++)
    terrH[x] = (int)(nx() % (2 * W.terrainAmp * S + 1)) - W.terrainAmp * S;
  auto at = [](const std::map<int, int>& h, int x) {
    const auto it = h.find(x); return it == h.end() ? 0 : it->second; };
  for (;;) {
    const std::map<int, int> prev = terrH;        // Jacobi snapshot
    for (int x = W.terrainX0; x <= W.terrainX1; x++) {
      const int s = at(prev, x - 1) + 2 * at(prev, x) + at(prev, x + 1);
      terrH[x] = s >= 0 ? s >> 2 : -((-s) >> 2);  // trunc toward zero
    }
    int maxSlope = 0;
    for (int x = W.terrainX0; x <= W.terrainX1 + 1; x++)
      maxSlope = std::max(maxSlope,
                          std::abs(at(terrH, x) - at(terrH, x - 1)));
    if (++terrIters > 1000) die4("TERRAIN: relaxation did not converge");
    if (maxSlope <= W.terrainSlope) break;
  }
}
// the body's support height: the highest terrain column under the grown
// footprint (the belly rests on a hilltop honestly); flat membrane == N5.
// h/terrainScale is exact (the scale is a power of 2).
static double groundAt() {
  if (!terrainOn) return bear.groundY;
  // per-column support with the 0-outside-domain rule; NB: `g` must NOT be
  // clamped at 0 — an all-negative footprint inside the domain is a real
  // depression (the oracle caught a phantom flat floor at bodyX=0: the wire
  // said ground -4.000 where the terrain reads -4.037109)
  int g = 0;
  bool first = true;
  const int bx = (int)std::floor(bear.body[0]);
  for (int x = bx + bear.bodyLoX; x <= bx + bear.bodyHiX; x++) {
    const auto it = terrH.find(x);
    const int h = it == terrH.end() ? 0 : it->second;
    g = first ? h : std::max(g, h);
    first = false;
  }
  return bear.groundMinY + (double)g / W.terrainScale;
}

// the rig: chains read off the GROWN ledger — roots, elbows, wrists, digits,
// rest tips all measured, nothing placed by hand
static void bearRig() {
  bear.rig.clear();
  for (int i = 0; i < (int)cLimbs.size(); i++) {
    const CTip* main = nullptr;
    for (const auto& t : cTips)
      if (!t.digit && t.limbIdx == i && !t.path.empty()) { main = &t; break; }
    if (!main || main->path.size() < 3) continue;
    BChain ch; ch.limbIdx = i; ch.fore = cLimbs[i].fore; ch.side = cLimbs[i].side;
    ch.path = main->path;
    ch.elbow = (int)main->path.size() / 2;
    for (const auto& t : cTips)
      if (t.digit && t.limbIdx == i && !t.path.empty()) ch.digits.push_back(t.path);
    fkPoint(ch, (int)ch.path.size() - 1, ch.rest);
    bear.rig.push_back(ch);
  }
  bear.rigged = true;
  int w = -1;
  for (int i = 0; i < (int)bear.rig.size(); i++)
    if (bear.rig[i].fore && bear.rig[i].side > 0) { w = i; break; }
  if (w < 0)
    for (int i = 0; i < (int)bear.rig.size(); i++)
      if (bear.rig[i].fore) { w = i; break; }
  bear.waveCh = w;
  // ears: the two highest skin cells of the head bulb (derived, not drawn)
  std::vector<int> cand;
  for (int i = 0; i < (int)cCellsV.size(); i++)
    if (cCellsV[i].mat == 0 && cCellsV[i].x >= cOrgBall[0] + W.eyeXMin)
      cand.push_back(i);
  std::stable_sort(cand.begin(), cand.end(),   // JS sort is stable (ES2019)
                   [](int a, int b) { return cCellsV[a].y > cCellsV[b].y; });
  for (int i = 0; i < 2 && i < (int)cand.size(); i++) {
    cCellsV[cand[i]].mat = 3; bear.nEars++;
  }
  // N5: derive the physics membrane from the GROWN body — the ground plane is
  // where the body's lowest cell already rests; the drop height is 8 body
  // heights (the selftest's energy-ledger bound drives the 8, see header)
  double loY = 1e300, hiY = -1e300;
  int loX = cCellsV[0].x, hiX = cCellsV[0].x;
  for (const auto& c : cCellsV) {
    loY = std::fmin(loY, (double)c.y); hiY = std::fmax(hiY, (double)c.y);
    loX = std::min(loX, c.x); hiX = std::max(hiX, c.x);
  }
  bear.groundMinY = loY; bear.groundY = loY; bear.bodyH = hiY - loY;
  bear.bodyLoX = loX; bear.bodyHiX = hiX;         // N6: the grown footprint
  gSim = W.gravity / (W.tickHz * W.tickHz * W.cell);   // SI -> cells/tick^2
  genTerrain();                         // N6: grow the world (if declared)
  navInit();                            // N8: derive the navigator (if declared)
}

// ============================ G5 LEARNER (situations -> goals) ===============
static const int STRUCT5[7] = {0, 1, 1, 1, 2, 2, 2};   // reward structure
static bool visitorPresent = false;
static double visitorPos[3] = {0, 0, 0};
static int visitorWaveBack = 0;
struct Learn {
  double Q[7][3] = {};
  double eps = 0; long episode = 0, epTick = 0; double epReward = 0;
  std::vector<double> rewards;
  long long rng = 1337;
  long stateVisits[7] = {};
  double minResAuto = 0; bool hasMinResAuto = false;
  long gaitT = 0;
};
static Learn L;
static void learnReset() {
  L = Learn();
  L.eps = W.l5Eps0; L.rng = 1337;
  visitorPresent = false; visitorPos[0] = visitorPos[1] = visitorPos[2] = 0;
  visitorWaveBack = 0;
}
static double rnd() {                 // LCG — deterministic per body
  // JS does this arithmetic in DOUBLES: rng*1103515245 exceeds 2^53 once
  // rng ~ 1e8, so the product rounds to the nearest double BEFORE the mask
  // (measured: exact-int64 math gives rng=1460962527 where the JS reference
  // reads 1460962528 after the first tick — the port replicates the rounding,
  // it does not "fix" it; the JS page is the reference by definition)
  const double x = (double)L.rng * 1103515245.0 + 12345.0;
  const double m = std::fmod(x, 4294967296.0);        // ToInt32 mod 2^32, x>0
  L.rng = (long long)m & 0x7fffffff;
  return (double)L.rng / 0x7fffffff;
}
// the senses: range from the head, bearing from WHICH EYE wins — retinal
// activation = dot(unit(to visitor), eye outward normal) on grown geometry.
// The JS frame sloppiness is DELIBERATE and preserved: `to` mixes the world
// rel vector with the eye's local lattice coords (norm3(rel - e)).
static int senseState() {
  if (!visitorPresent) return 0;
  const double rel[3] = {visitorPos[0] - bear.body[0], visitorPos[1],
                         visitorPos[2]};
  const double d = hypot3(rel[0], rel[1], rel[2]);
  const int zc = (int)std::lround(cOrgBall[2]);
  double actPlus = -2, actMinus = -2;
  for (const auto& e : cEyes) {
    const double e0[3] = {(double)e[0], (double)e[1], (double)e[2]};
    double t1[3], out[3], t2[3], to[3];
    sub3(e0, cOrgHead, t1); bnorm3(t1, out);
    sub3(rel, e0, t2); bnorm3(t2, to);
    const double a = out[0]*to[0] + out[1]*to[1] + out[2]*to[2];
    if (e[2] > zc) actPlus = std::fmax(actPlus, a);
    else actMinus = std::fmax(actMinus, a);
  }
  int bearing = 1;                                    // center
  if (actPlus > actMinus + W.l5BearEps) bearing = 0;  // +z flank
  else if (actMinus > actPlus + W.l5BearEps) bearing = 2;
  return (d <= W.l5Near ? 1 : 4) + bearing;
}
static void spawnEpisode() {
  const double r = rnd();
  if (r < 1.0 / 3.0) visitorPresent = false;
  else {
    const bool near = r < 2.0 / 3.0;
    const double b = rnd();
    visitorPresent = true;
    visitorPos[0] = bear.body[0] + (near ? W.l5Near - 2 : W.l5Far);
    visitorPos[1] = 0;
    visitorPos[2] = b < 1.0 / 3.0 ? 3 : b < 2.0 / 3.0 ? 0 : -3;
  }
  visitorWaveBack = 0;
  L.epTick = 0; L.epReward = 0;
}
static void gaitTick() {                  // one gait step through G4 physics
  L.gaitT++;
  const double phi = 2 * 3.14159265358979323846 * L.gaitT / W.b4T;
  for (auto& ch : bear.rig) {
    const double ph = (ch.fore == (ch.side > 0)) ? 0 : 3.14159265358979323846;
    const double T[3] = {ch.rest[0] + W.b4A * std::sin(phi + ph),
                         ch.rest[1] + 0.6 * W.b4A *
                           std::fmax(0.0, std::cos(phi + ph)),
                         ch.rest[2]};
    for (int i = 0; i < W.b4Iters; i++) ikStep(ch, T);
  }
  // N7: traction is EARNED — the stance pair sweeps at A*w*|cos phi|; the
  // cycle-mean of that rate is exactly the retired 4A/T constant. Airborne,
  // the legs cycle and the body goes nowhere.
  if (bear.contact)
    bear.body[0] += W.b4A * (2 * 3.14159265358979323846 / W.b4T) *
                    std::fabs(std::cos(phi));
}
static void autoTick() {
  physTick();                             // N5: gravity acts on every tick
  const int s = senseState();
  L.stateVisits[s]++;
  int a;
  if (rnd() < L.eps) a = (int)std::floor(rnd() * 3);
  else { const double* q = L.Q[s];
         a = q[0] >= q[1] && q[0] >= q[2] ? 0 : q[1] >= q[2] ? 1 : 2; }
  double d0 = 0;
  if (visitorPresent) {
    const double dv[3] = {visitorPos[0] - bear.body[0], visitorPos[1],
                          visitorPos[2]};
    d0 = hypot3(dv[0], dv[1], dv[2]);
  }
  double r = 0; bool terminal = false;
  if (a == 1) {                      // wave, executed by the G4 IK stack
    BChain& ch = bear.rig[bear.waveCh];
    const double P0[3] = {(double)ch.path[0][0], (double)ch.path[0][1],
                          (double)ch.path[0][2]};
    double off[3], rr[3], up[3];
    sub3(ch.rest, P0, off);
    const double x[3] = {1, 0, 0};
    rot3(off, x, -W.b4WaveTh * ch.side, rr);
    add3(P0, rr, up);
    double res = 0;
    for (int i = 0; i < W.b4Iters; i++) res = ikStep(ch, up);
    if (!L.hasMinResAuto || res < L.minResAuto) {
      L.minResAuto = res; L.hasMinResAuto = true;
    }
    bear.lastRes = res; bear.hasLastRes = true;
    if (!visitorPresent) r = W.r5WaveAbsent;
    else if (d0 <= W.l5Near) { r = W.r5WaveNear; visitorWaveBack = 30;
                               terminal = true; }
    else r = W.r5WaveFar;
  } else if (a == 2) {               // walk, executed by the G4 gait
    if (!visitorPresent) { gaitTick(); r = W.r5WalkTick; }
    else if (d0 <= W.l5Near) { r = W.r5Startle; terminal = true; }
    else {
      gaitTick();
      const double dv[3] = {visitorPos[0] - bear.body[0], visitorPos[1],
                            visitorPos[2]};
      const double d1 = hypot3(dv[0], dv[1], dv[2]);
      r = W.r5WalkTick + W.r5Beckon * (d0 - d1);   // the beckoning gradient
    }
  } else r = visitorPresent ? W.r5RestPresent : W.r5RestAbsent;
  L.epReward += r; L.epTick++;
  const int s2 = senseState();
  double* q = L.Q[s];
  const double mx = std::fmax(L.Q[s2][0], std::fmax(L.Q[s2][1], L.Q[s2][2]));
  q[a] += W.l5Alpha * (r + (terminal ? 0 : W.l5Gamma * mx) - q[a]);
  if (std::getenv("CA_TRACE"))              // N4 debug: tick-level ledger
    std::fprintf(stderr, "TR %ld %ld s=%d a=%d r=%.17g t=%d p=%d dx=%.17g "
                 "dz=%.17g rng=%lld\n", L.episode, L.epTick, s, a, r,
                 terminal ? 1 : 0, visitorPresent ? 1 : 0,
                 visitorPos[0] - bear.body[0], visitorPos[2], L.rng);
  if (terminal || L.epTick >= W.l5EpTicks) {
    L.rewards.push_back(L.epReward);
    L.episode++;
    L.eps = std::fmax(W.l5EpsMin, L.eps * W.l5EpsDecay);
    spawnEpisode();
  }
}

// ============================ N5 PHYSICS MEMBRANE =============================
// One gravity kernel, rigid-body COM, velocity-projection ground contact —
// symplectic Euler (the project's integrator), no springs, nothing to tune.
// At equilibrium the projection restores bodyY/velY to 0 EXACTLY each tick
// (IEEE: 0 - g + g == 0), which is why the N4 ledger is untouched with
// physics ON. Free fall follows E_n = gH - g^2 n/2 (derived in the header).
static void physTick() {
  bear.velY -= gSim;
  bear.bodyY += bear.velY;
  bear.contact = false;
  const double ground = groundAt();                 // N6: terrain support
  bear.lastGround = ground;
  const double pen = ground - (bear.bodyY + bear.groundMinY);
  if (pen >= 0) {                         // touching or penetrating: project
    bear.bodyY += pen;                    // -> sole exactly on the support
    bear.velY = 0;                        // inelastic: no bounce, no energy in
    bear.contact = true;
  }
}

// ============================ N8 GOAL MEMBRANE ================================
// Deliberation over the terrain+physics state: a flag at goalX, a 12-state
// sense (bearing x slope x contact), five verbs (rest, walkE/W full, walkE/W
// careful), Q-learning on the L5 constants. ZERO new tunables — every number
// below is derived from the genome's physics (see beargoal.chimera's N8
// header): the careful amplitude A_c is the largest gait that keeps contact
// at the walkability-contract slope, the slip threshold tau is the slope
// where the N7 stride law can no longer pay, and the episode budget is the
// flag distance at the careful cycle-mean rate (4*A_c/T).
struct Nav {
  double Q[12][5] = {};
  double eps = 0; long episode = 0, epTick = 0; double epReward = 0;
  std::vector<double> rewards;
  std::vector<int> arrived;                       // per-episode arrival flag
  long long rng = 1337;                           // own LCG (G5 precedent)
  long visits[12] = {};
  long arrivals = 0, gaitT = 0;
  int lastState = 0, lastVerb = 0; double lastDist = 0;   // wire (emitAnim)
};
static Nav N;
static double navAc = 0, navTau = 0;              // careful amplitude, slip
static int n8EpTicks = 0;                         // episode budget
static void navReset() {
  N = Nav();
  N.eps = W.l5Eps0; N.rng = 1337;
}
static double navRnd() {              // the same lossy-double LCG as rnd()
  const double x = (double)N.rng * 1103515245.0 + 12345.0;
  const double m = std::fmod(x, 4294967296.0);
  N.rng = (long long)m & 0x7fffffff;
  return (double)N.rng / 0x7fffffff;
}
static void navInit() {               // called from bearRig, post-terrain
  if (!W.goal) return;
  const double omega = 2 * 3.14159265358979323846 / W.b4T;
  navAc = gSim / (omega * ((double)W.terrainSlope / W.terrainScale));
  navTau = gSim / (W.b4A * omega);
  n8EpTicks = (int)std::ceil(W.goalX / (4 * navAc / W.b4T));
  navReset();
}
// terrain column height (cells) for the slope sense — the raw grown column,
// not the footprint support: the bear smells the slope AHEAD of its feet
static double colHeightAt(int x) {
  const auto it = terrH.find(x);
  const int h = it == terrH.end() ? 0 : it->second;   // 0 outside the domain
  return bear.groundMinY + (double)h / W.terrainScale;
}
// the sense: s = (bearing*3 + slope)*2 + contact. Bearing: is the flag east?
// Slope: the central difference over the column under the body's center,
// classified against the slip threshold tau (uphill / walkable / steep).
static int navState() {
  const int bx = (int)std::floor(bear.body[0]);
  const int bearing = W.goalX > bx ? 0 : 1;
  const double ss = (colHeightAt(bx + 1) - colHeightAt(bx - 1)) / 2;
  const int slope = ss > 0 ? 0 : ss >= -navTau ? 1 : 2;
  return (bearing * 3 + slope) * 2 + (bear.contact ? 1 : 0);
}
static void navSpawn() {              // symmetric spawns: flagX +/- 15
  N.epTick = 0; N.epReward = 0;
  bear.body[0] = navRnd() < 0.5 ? 0.0 : 30.0;
  bear.bodyY = groundAt() - bear.groundMinY;      // sole exactly on support
  bear.velY = 0; bear.contact = true;
}
static void navTick() {
  physTick();                         // gravity first (the autoTick precedent)
  const int s = navState();
  N.visits[s]++;
  int a;
  if (navRnd() < N.eps) a = (int)std::floor(navRnd() * 5);
  else { const double* q = N.Q[s]; a = 0;         // strict >: lowest index
         for (int i = 1; i < 5; i++) if (q[i] > q[a]) a = i; }
  const double d0 = std::fabs(W.goalX - bear.body[0]);
  if (a != 0) {      // walk verbs: 1 = E full, 2 = W full, 3 = E careful,
    const double dir = (a == 1 || a == 3) ? 1.0 : -1.0;   // 4 = W careful
    const double amp = a <= 2 ? W.b4A : navAc;
    N.gaitT++;
    const double phi = 2 * 3.14159265358979323846 * N.gaitT / W.b4T;
    // the legs honestly cycle (viewer honesty); the oracle reads no IK —
    // rewards and senses never touch it
    for (auto& ch : bear.rig) {
      const double ph = (ch.fore == (ch.side > 0)) ? 0 : 3.14159265358979323846;
      const double T[3] = {ch.rest[0] + amp * std::sin(phi + ph),
                           ch.rest[1] + 0.6 * amp *
                             std::fmax(0.0, std::cos(phi + ph)),
                           ch.rest[2]};
      for (int i = 0; i < W.b4Iters; i++) ikStep(ch, T);
    }
    // the N7 earned-stride law, directed; airborne the stride pays nothing
    if (bear.contact)
      bear.body[0] += dir * amp * (2 * 3.14159265358979323846 / W.b4T) *
                      std::fabs(std::cos(phi));
  }
  const double d1 = std::fabs(W.goalX - bear.body[0]);
  // the beckoning gradient minus uniform time cost; derived from R5 (r5Beckon)
  // and the episode budget n8EpTicks <- goalX via A_c = gSim/(omega * contractSlope),
  // omega = 2*pi/b4T — the flag distance at the careful gait's cycle-mean rate.
  // Slip is the bear's choice (it chose the gait), so airborne time
  // is not waived; shaping needs no clip. Ng et al. potential shaping was
  // tested and falsified (see report).
  double r = W.r5Beckon * (d0 - d1) - 1.0 / n8EpTicks;

  bool terminal = false;
  if ((int)std::floor(bear.body[0]) == W.goalX) {         // standing ON it
    r += W.r5WaveNear; terminal = true; N.arrivals++;
  }
  N.epReward += r; N.epTick++;
  N.lastState = s; N.lastVerb = a; N.lastDist = d1;
  const int s2 = navState();
  double* q = N.Q[s];
  // Bootstrap: max over all verbs in the next state, no clip — the learner
  // must face the full consequences of its gait choices including slip.
  double mx = std::fmax(
      N.Q[s2][0], std::fmax(N.Q[s2][1],
        std::fmax(N.Q[s2][2], std::fmax(N.Q[s2][3], N.Q[s2][4]))));
  q[a] += W.l5Alpha * (r + (terminal ? 0 : W.l5Gamma * mx) - q[a]);
  if (terminal || N.epTick >= n8EpTicks) {
    N.rewards.push_back(N.epReward);
    N.arrived.push_back(terminal ? 1 : 0);
    N.episode++;
    N.eps = std::fmax(W.l5EpsMin, N.eps * W.l5EpsDecay);
    navSpawn();
  }
}

// the embodiment clock — separate from the growth clock
static void bearAnim() {
  if (!bear.rigged) return;
  bear.cmdTick++;
  if (bear.cmd != "auto" && bear.cmd != "nav") physTick();  // they ride their own ticks
  if (visitorWaveBack > 0) visitorWaveBack--;   // G5 visitor bob clock
  bear.hasLastRes = false;
  double res = 0;
  if (bear.cmd == "wave" && bear.waveCh >= 0) {
    BChain& ch = bear.rig[bear.waveCh];
    const double P0[3] = {(double)ch.path[0][0], (double)ch.path[0][1],
                          (double)ch.path[0][2]};
    double off[3], rr[3], up[3];
    sub3(ch.rest, P0, off);
    const double x[3] = {1, 0, 0};
    rot3(off, x, -W.b4WaveTh * ch.side, rr);
    add3(P0, rr, up);
    const bool lower = bear.wavePhase == "lower";
    for (int i = 0; i < W.b4Iters; i++) res = ikStep(ch, lower ? ch.rest : up);
    bear.hasLastRes = true;
    if (bear.wavePhase == "raise") {
      if (!bear.hasMinRes || res < bear.minResidual) {
        bear.minResidual = res; bear.hasMinRes = true;
      }
      if (res < W.b4WaveRes) {
        bear.wavePhase = "hold";
        bear.holdUntil = bear.cmdTick + W.b4Hold;
        bear.raiseIters = bear.iters;
      }
    } else if (bear.wavePhase == "hold") {
      if (bear.cmdTick >= bear.holdUntil) bear.wavePhase = "lower";
    } else if (bear.wavePhase == "lower") {
      if (res < W.b4LowerRes) {
        bear.cmd = "rest"; bear.waveDone = true; bear.wavePhase = "";
      }
    }
  } else if (bear.cmd == "walk") {
    const double phi = 2 * 3.14159265358979323846 * bear.cmdTick / W.b4T;
    for (auto& ch : bear.rig) {
      // diagonal pairs in phase: (fore,+z) & (hind,-z) at 0, others at pi
      const double ph = (ch.fore == (ch.side > 0)) ? 0 : 3.14159265358979323846;
      const double T[3] = {ch.rest[0] + W.b4A * std::sin(phi + ph),
                           ch.rest[1] + 0.6 * W.b4A *
                             std::fmax(0.0, std::cos(phi + ph)),
                           ch.rest[2]};
      double r = 0;
      for (int i = 0; i < W.b4Iters; i++) r = ikStep(ch, T);
      if (!bear.hasLastRes || r > res) { res = r; bear.hasLastRes = true; }
    }
    // N7: earned traction — stance sweep A*w*|cos phi|, gated by contact
    if (bear.contact)
      bear.body[0] += W.b4A * (2 * 3.14159265358979323846 / W.b4T) *
                      std::fabs(std::cos(phi));
    std::vector<std::array<double, 3>> tips(bear.rig.size());
    for (size_t i = 0; i < bear.rig.size(); i++) {
      double tp[3]; fkPoint(bear.rig[i], (int)bear.rig[i].path.size() - 1, tp);
      tips[i] = {tp[0], tp[1], tp[2]};
    }
    bear.gaitLog.push_back({bear.cmdTick, std::move(tips)});
    if (bear.gaitLog.size() > 400)
      bear.gaitLog.erase(bear.gaitLog.begin());
    // N6: per-tick contact ledger — bodyY/ground AFTER this tick's physTick
    // (which ran pre-stride at the top of bearAnim); the oracle replicates
    bear.walkTrace.push_back(
        {(double)bear.cmdTick, bear.bodyY, bear.lastGround});
    if (bear.walkTrace.size() > 400)
      bear.walkTrace.erase(bear.walkTrace.begin());
  } else if (bear.cmd == "auto") {
    autoTick();                           // G5: the learner drives
  } else if (bear.cmd == "nav") {
    navTick();                            // N8: the navigator drives
  }
  if (bear.hasLastRes) bear.lastRes = res;
}
static void bearCommand(const std::string& c) {
  if (!bear.rigged) return;
  if (c == "wave") {
    bear.cmd = "wave"; bear.cmdTick = 0; bear.iters = 0;
    bear.hasMinRes = false; bear.raiseIters = -1; bear.waveDone = false;
    bear.wavePhase = "raise";
  } else if (c == "walk") {
    bear.cmd = "walk"; bear.cmdTick = 0; bear.gaitLog.clear();
    bear.walkTrace.clear();                       // N6
  } else if (c == "drop") {               // N5: 8 body-heights, from contact
    if (bear.contact) {                   // airborne drops stack nothing
      bear.bodyY += 8 * bear.bodyH; bear.velY = 0; bear.contact = false;
    }
  } else if (c == "nav" && W.goal) {      // N8: walk to the flag (Q persists)
    bear.cmd = "nav"; bear.cmdTick = 0; navSpawn();
  } else bear.cmd = c == "auto" ? "auto" : "rest";
}

// ---------- embodiment wire emitters -----------------------------------------
static void jArr3(const double v[3]) {
  std::printf("[%.17g,%.17g,%.17g]", v[0], v[1], v[2]);
}
static void emitRig() {
  std::printf("{\"type\":\"rig\",\"chains\":[");
  for (size_t i = 0; i < bear.rig.size(); i++) {
    const BChain& ch = bear.rig[i];
    std::printf("%s{\"limbIdx\":%d,\"fore\":%s,\"side\":%d,\"elbow\":%d,"
                "\"path\":[", i ? "," : "", ch.limbIdx,
                ch.fore ? "true" : "false", ch.side, ch.elbow);
    for (size_t k = 0; k < ch.path.size(); k++)
      std::printf("%s[%d,%d,%d]", k ? "," : "", ch.path[k][0], ch.path[k][1],
                  ch.path[k][2]);
    std::printf("],\"digits\":[");
    for (size_t d = 0; d < ch.digits.size(); d++) {
      std::printf("%s[", d ? "," : "");
      for (size_t j = 0; j < ch.digits[d].size(); j++)
        std::printf("%s[%d,%d,%d]", j ? "," : "", ch.digits[d][j][0],
                    ch.digits[d][j][1], ch.digits[d][j][2]);
      std::printf("]");
    }
    std::printf("],\"rest\":");
    jArr3(ch.rest);
    std::printf("}");
  }
  std::printf("],\"ears\":[");
  int n = 0;
  for (const CCell& c : cCellsV)
    if (c.mat == 3) std::printf("%s[%d,%d,%d]", n++ ? "," : "", c.x, c.y, c.z);
  std::printf("],\"waveCh\":%d,\"ground\":%.17g,\"bodyH\":%.17g,\"g\":%.17g",
              bear.waveCh, bear.groundY, bear.bodyH, gSim);
  if (terrainOn) {                        // N6: the grown world, on the wire
    std::printf(",\"terrain\":[");
    bool firstT = true;
    for (const auto& kv : terrH) {
      std::printf("%s[%d,%d]", firstT ? "" : ",", kv.first, kv.second);
      firstT = false;
    }
    std::printf("],\"terrainIters\":%d,\"terrainScale\":%d", terrIters,
                W.terrainScale);
  }
  if (W.goal)                                     // N8: the flag rides the rig
    std::printf(",\"goalX\":%d", W.goalX);
  std::printf("}\n");
  std::fflush(stdout);
}
static void emitAnim() {
  std::printf("{\"type\":\"anim\",\"tick\":%ld,\"cmd\":\"%s\",\"res\":",
              bear.cmdTick, bear.cmd.c_str());
  if (bear.hasLastRes) std::printf("%.17g", bear.lastRes);
  else std::printf("null");
  std::printf(",\"body\":[%.17g,%.17g,0],\"vy\":%.17g,\"contact\":%s,"
              "\"ground\":%.17g,\"visitor\":", bear.body[0], bear.bodyY,
              bear.velY, bear.contact ? "true" : "false", bear.lastGround);
  if (visitorPresent) jArr3(visitorPos);
  else std::printf("null");
  if (bear.cmd == "nav")                  // N8: the deliberation rides the wire
    std::printf(",\"nav\":{\"state\":%d,\"verb\":%d,\"dist\":%.17g,"
                "\"ep\":%ld,\"arrivals\":%ld}", N.lastState, N.lastVerb,
                N.lastDist, N.episode, N.arrivals);
  std::printf(",\"waveBack\":%d,\"episode\":%ld,\"eps\":%.17g,"
              "\"waveDone\":%s,\"posed\":[", visitorWaveBack, L.episode,
              L.eps, bear.waveDone ? "true" : "false");
  bool first = true;
  for (const BChain& ch : bear.rig) {
    for (size_t k = 0; k < ch.path.size(); k++) {
      double p[3]; fkPoint(ch, (int)k, p);
      std::printf("%s[%d,%d,%d,%.17g,%.17g,%.17g]", first ? "" : ",",
                  ch.path[k][0], ch.path[k][1], ch.path[k][2],
                  p[0], p[1], p[2]);
      first = false;
    }
    for (const auto& dp : ch.digits)
      for (size_t j = 0; j < dp.size(); j++) {
        double p[3]; fkDigit(ch, dp, (int)j, p);
        std::printf("%s[%d,%d,%d,%.17g,%.17g,%.17g]", first ? "" : ",",
                    dp[j][0], dp[j][1], dp[j][2], p[0], p[1], p[2]);
        first = false;
      }
  }
  std::printf("],\"done\":false}\n");
  std::fflush(stdout);
}

// ---------- selftest: the synchronous G4/G5 protocol, one ledger line --------
// Mirrors engine/probe_bear_ref.py exactly: wave until waveDone (<= 2000
// anim ticks), walk 400 anim ticks, rest, segment audit, five sense probes,
// then 320 learning episodes. The oracle in test_native.py compares every
// number against the JS reference run.
static void emitSelftest() {
  bearCommand("wave");
  for (int i = 0; i < 2000 && !bear.waveDone; i++) bearAnim();
  const double waveMinRes = bear.minResidual;
  const long waveRaise = bear.raiseIters, waveIters = bear.iters;
  const bool waveDone = bear.waveDone;
  bearCommand("walk");
  for (int i = 0; i < 400; i++) bearAnim();
  const double bodyAfterWalk = bear.body[0];
  const long walkIters = bear.iters;
  const double walkLastRes = bear.lastRes;
  bearCommand("rest");
  // F-G4f segment audit: posed segments must equal grown lengths
  double segErr = -1;
  for (const BChain& ch : bear.rig)
    for (size_t k = 1; k < ch.path.size(); k++) {
      const double rest = hypot3(ch.path[k][0] - (double)ch.path[k-1][0],
                                 ch.path[k][1] - (double)ch.path[k-1][1],
                                 ch.path[k][2] - (double)ch.path[k-1][2]);
      double pa[3], pb[3], dd[3];
      fkPoint(ch, (int)k, pa); fkPoint(ch, (int)k - 1, pb); sub3(pa, pb, dd);
      const double posed = hypot3(dd[0], dd[1], dd[2]);
      const double err = std::fabs(posed - rest);
      segErr = segErr < 0 ? err : std::fmax(segErr, err);
    }
  // sense probes (same sequence as the JS probe)
  visitorPresent = true;
  visitorPos[0] = bear.body[0] + 4; visitorPos[1] = 0; visitorPos[2] = 3;
  const int sNearPlus = senseState();
  visitorPos[2] = -3; const int sNearMinus = senseState();
  visitorPos[2] = 0;  const int sNearCenter = senseState();
  visitorPos[0] = bear.body[0] + 12; const int sFarCenter = senseState();
  // JS __setVisitor(false, 0, 0): pos = [body0, 0, 0] — not stale
  visitorPresent = false;
  visitorPos[0] = bear.body[0]; visitorPos[1] = 0; visitorPos[2] = 0;
  const int sAbsent = senseState();
  // 320 learning episodes
  const long target = L.episode + 320;
  long guard = 0;
  while (L.episode < target && guard++ < 320L * W.l5EpTicks * 3) autoTick();
  double first30 = 0, last30 = 0;
  for (int i = 0; i < 30 && i < (int)L.rewards.size(); i++)
    first30 += L.rewards[i];
  first30 /= 30;
  for (size_t i = L.rewards.size() > 30 ? L.rewards.size() - 30 : 0;
       i < L.rewards.size(); i++)
    last30 += L.rewards[i];
  last30 /= 30;
  std::printf("{\"type\":\"selftest\",\"wave\":{\"minResidual\":%.17g,"
              "\"raiseIters\":%ld,\"iters\":%ld,\"waveDone\":%s},",
              waveMinRes, waveRaise, waveIters, waveDone ? "true" : "false");
  std::printf("\"walk\":{\"iters\":%ld,\"lastRes\":%.17g,\"bodyX\":%.17g,"
              "\"gait\":[", walkIters, walkLastRes, bodyAfterWalk);
  for (size_t i = 0; i < bear.gaitLog.size(); i++) {
    std::printf("%s[%ld,[", i ? "," : "", bear.gaitLog[i].first);
    for (size_t c = 0; c < bear.gaitLog[i].second.size(); c++) {
      const auto& t = bear.gaitLog[i].second[c];
      std::printf("%s[%.17g,%.17g,%.17g]", c ? "," : "", t[0], t[1], t[2]);
    }
    std::printf("]]");
  }
  std::printf("],\"trace\":[");           // N6: per-tick contact ledger
  for (size_t i = 0; i < bear.walkTrace.size(); i++)
    std::printf("%s[%.17g,%.17g,%.17g]", i ? "," : "", bear.walkTrace[i][0],
                bear.walkTrace[i][1], bear.walkTrace[i][2]);
  std::printf("]},\"thetaFinal\":[");
  for (size_t i = 0; i < bear.rig.size(); i++)
    std::printf("%s[%.17g,%.17g]", i ? "," : "", bear.rig[i].theta[0],
                bear.rig[i].theta[1]);
  std::printf("],\"segErr\":%.17g,\"thetaMaxEver\":%.17g,\"nan\":%s,",
              segErr, bear.thetaMaxEver, bear.nan ? "true" : "false");
  std::printf("\"senses\":{\"nearPlus\":%d,\"nearMinus\":%d,"
              "\"nearCenter\":%d,\"farCenter\":%d,\"absent\":%d},",
              sNearPlus, sNearMinus, sNearCenter, sFarCenter, sAbsent);
  std::printf("\"learn\":{\"episode\":%ld,\"eps\":%.17g,\"first30\":%.17g,"
              "\"last30\":%.17g,\"rewards\":[", L.episode, L.eps, first30,
              last30);
  for (size_t i = 0; i < L.rewards.size(); i++)
    std::printf("%s%.17g", i ? "," : "", L.rewards[i]);
  // ---------- N5/N6 physics protocol: drop from 8 body-heights, then rest ---
  // Free fall: velY = -g*n, bodyY = yRest + H - g*n(n+1)/2 after n ticks, so
  // the energy ledger is E_n = gH - g^2 n/2 EXACTLY (per unit mass — M
  // cancels). N6: yRest is whatever support the bear stands on (terrain).
  const double H = 8 * bear.bodyH;
  const double yRest = bear.bodyY;              // the local support offset
  bear.bodyY = yRest + H; bear.velY = 0; bear.contact = false;
  const double E0 = gSim * H;
  double ledgerErr = 0, lastE = E0;
  long contactTick = -1;
  for (long n = 1; n < 100000; n++) {
    physTick();
    if (bear.contact) { contactTick = n; break; }
    lastE = 0.5 * bear.velY * bear.velY + gSim * (bear.bodyY - yRest);
    const double Eexp = gSim * H - 0.5 * gSim * gSim * n;   // the ledger
    const double err = std::fabs(lastE - Eexp) / E0;
    if (err > ledgerErr) ledgerErr = err;
  }
  const double termDrift = (E0 - lastE) / E0;
  double restVyMax = 0, restPenMax = 0;
  for (int i = 0; i < 300; i++) {
    physTick();
    const double av = std::fabs(bear.velY);
    const double ap = std::fabs(bear.lastGround -
                                (bear.bodyY + bear.groundMinY));
    if (av > restVyMax) restVyMax = av;
    if (ap > restPenMax) restPenMax = ap;
  }
  std::printf("],\"Q\":[");
  for (int s = 0; s < 7; s++)
    std::printf("%s[%.17g,%.17g,%.17g]", s ? "," : "", L.Q[s][0], L.Q[s][1],
                L.Q[s][2]);
  std::printf("],\"visits\":[%ld,%ld,%ld,%ld,%ld,%ld,%ld],"
              "\"minResAuto\":%.17g,\"bodyXfinal\":%.17g}",
              L.stateVisits[0], L.stateVisits[1], L.stateVisits[2],
              L.stateVisits[3], L.stateVisits[4], L.stateVisits[5],
              L.stateVisits[6], L.minResAuto, bear.body[0]);
  std::printf(",\"phys\":{\"g\":%.17g,\"ground\":%.17g,\"dropH\":%.17g,"
              "\"contactTick\":%ld,\"analyticTick\":%.17g,\"ledgerErr\":%.17g,"
              "\"termDrift\":%.17g,\"restVyMax\":%.17g,\"restPenMax\":%.17g}",
              gSim, bear.lastGround, H, contactTick,
              std::sqrt(2 * H / gSim), ledgerErr, termDrift,
              restVyMax, restPenMax);
  // ---------- N7: the earned-traction falsifier, run live -------------------
  // Legs cycling while airborne must move the body EXACTLY nowhere; the
  // landing tick must match the discrete drop law; strides resume on contact.
  bearCommand("walk");                          // legs cycle from cmdTick 0
  bear.bodyY += 8 * bear.bodyH;                 // airborne at the drop height
  bear.velY = 0; bear.contact = false;
  double airMoved = 0, bxPrev = bear.body[0];
  long airTicks = 0, landTick = -1;
  for (long n = 1; n <= 400; n++) {
    bearAnim();
    if (!bear.contact) {
      airMoved += std::fabs(bear.body[0] - bxPrev);
      airTicks++;
    } else if (landTick < 0)
      landTick = n;
    bxPrev = bear.body[0];
  }
  std::printf(",\"airwalk\":{\"airTicks\":%ld,\"airMoved\":%.17g,"
              "\"landTick\":%ld,\"bodyX\":%.17g}}\n",
              airTicks, airMoved, landTick, bear.body[0]);
  std::fflush(stdout);
  // ---------- N8: the goal membrane — 320 deliberation episodes -------------
  // A SEPARATE ledger line (the G4-G7 ledger above stays byte-identical).
  if (W.goal) {
    navReset();
    navSpawn();
    long guard = 0;
    while (N.episode < 320 && guard++ < 320L * n8EpTicks * 3) navTick();
    double first30 = 0, last30 = 0;               // arrival RATES, not reward
    for (int i = 0; i < 30 && i < (int)N.arrived.size(); i++)
      first30 += N.arrived[i];
    first30 /= 30;
    for (size_t i = N.arrived.size() > 30 ? N.arrived.size() - 30 : 0;
         i < N.arrived.size(); i++)
      last30 += N.arrived[i];
    last30 /= 30;
    std::printf("{\"type\":\"navtest\",\"goalX\":%d,\"budget\":%d,"
                "\"ac\":%.17g,\"tau\":%.17g,\"episodes\":%ld,\"visits\":[",
                W.goalX, n8EpTicks, navAc, navTau, N.episode);
    for (int s = 0; s < 12; s++)
      std::printf("%s%ld", s ? "," : "", N.visits[s]);
    std::printf("],\"arrivals\":%ld,\"first30\":%.17g,\"last30\":%.17g,"
                "\"Q\":[", N.arrivals, first30, last30);
    for (int s = 0; s < 12; s++) {
      std::printf("%s[", s ? "," : "");
      for (int a = 0; a < 5; a++)
        std::printf("%s%.17g", a ? "," : "", N.Q[s][a]);
      std::printf("]");
    }
    std::printf("],\"rewards\":[");
    for (size_t i = 0; i < N.rewards.size(); i++)
      std::printf("%s%.17g", i ? "," : "", N.rewards[i]);
    std::printf("]}\n");
    std::fflush(stdout);
  }
}

// ---------- interactive anim loop (relay mode): stdin commands, anim frames --
static int runEmbodiment(int tickMs) {
  emitRig();
  static std::mutex cmdMu;
  static std::vector<std::string> cmdQ;
  static bool stdinDone = false;
  std::thread reader([] {
    std::string l;
    while (std::getline(std::cin, l)) {
      if (l.empty()) continue;
      std::lock_guard<std::mutex> g(cmdMu);
      cmdQ.push_back(l);
    }
    std::lock_guard<std::mutex> g(cmdMu);
    stdinDone = true;
  });
  reader.detach();
  while (true) {
    {
      std::lock_guard<std::mutex> g(cmdMu);
      for (const auto& c : cmdQ) bearCommand(c);
      cmdQ.clear();
      if (stdinDone) break;
    }
    bearAnim();
    emitAnim();
    if (tickMs > 0)
      std::this_thread::sleep_for(std::chrono::milliseconds(tickMs));
  }
  return 0;
}

// ============================ T1 VOX MEMBRANE (imported cell set) ==============
// The body is DATA, not grown: loadVox reads genomes/<cellsFile> and populates
// cCellsV + the rig chains (cLimbs/cTips), then bearRig() runs UNCHANGED off
// that same data — the physics/gait/nav layers never see a "shape" flag. The
// cell set is occupancy-mapped onto the CA lattice by native/voxelize_teddy.py;
// the rig chains are its leg columns (hip->paw). No new physics.
static std::string voxCellsPath;                 // resolved in main()
static void loadVox() {
  cCellsV.clear(); cLimbs.clear(); cTips.clear(); cEyes.clear();
  std::ifstream f(voxCellsPath);
  if (!f) die4("MISSING vox cells file " + voxCellsPath);
  auto toks = [](const std::string& l) {
    std::vector<std::string> v; size_t i = 0;
    while (i < l.size()) {
      while (i < l.size() && (l[i] == ' ' || l[i] == '\t')) i++;
      if (i >= l.size()) break;
      size_t j = i; while (j < l.size() && l[j] != ' ' && l[j] != '\t') j++;
      v.push_back(l.substr(i, j - i)); i = j;
    }
    return v;
  };
  std::vector<std::string> lines; std::string line;
  while (std::getline(f, line)) {
    const size_t h = line.find('#');
    if (h != std::string::npos) line = line.substr(0, h);
    if (!line.empty()) lines.push_back(line);
  }
  size_t i = 0;
  auto next = [&]() {
    if (i >= lines.size()) die4("vox: truncated cells file");
    return toks(lines[i++]);
  };
  { const std::vector<std::string> h = next();   // CELLS <n>
    if (h.empty() || h[0] != "CELLS") die4("vox: expected CELLS header");
    const int ncells = std::stoi(h[1]);
    for (int j = 0; j < ncells; j++) {
      const std::vector<std::string> c = next();   // x y z
      if (c.size() != 3) die4("vox: bad cell line");
      cAddCell(std::stoi(c[0]), std::stoi(c[1]), std::stoi(c[2]), 0);
    }
  }
  { const std::vector<std::string> h = next();   // CHAINS <m>
    if (h.empty() || h[0] != "CHAINS") die4("vox: expected CHAINS header");
    const int nchains = std::stoi(h[1]);
    for (int j = 0; j < nchains; j++) {
      const std::vector<std::string> hd = next();   // fore side nx
      if (hd.size() != 3) die4("vox: bad chain header");
      const int fore = std::stoi(hd[0]), side = std::stoi(hd[1]);
      const int nx = std::stoi(hd[2]);
      CLimb L; L.side = side; L.fore = (fore == 1); L.born = 0;
      L.root[0] = L.root[1] = L.root[2] = 0;
      cLimbs.push_back(L);
      CTip t; t.id = (int)cTips.size(); t.limbIdx = j; t.digit = false;
      t.alive = true; t.dir[0] = t.dir[1] = t.dir[2] = 0; t.steps = nx - 1;
      for (int k = 0; k < nx; k++) {
        const std::vector<std::string> p = next();   // x y z
        if (p.size() != 3) die4("vox: bad chain cell line");
        t.path.push_back({std::stoi(p[0]), std::stoi(p[1]), std::stoi(p[2])});
      }
      cLimbs[j].root[0] = t.path[0][0]; cLimbs[j].root[1] = t.path[0][1];
      cLimbs[j].root[2] = t.path[0][2];
      cTips.push_back(t);
    }
  }
  // organizers -> centroid (ears/waveCh selection stays sensible on the data)
  double cx = 0, cy = 0, cz = 0;
  for (const CCell& c : cCellsV) { cx += c.x; cy += c.y; cz += c.z; }
  const double n = (double)cCellsV.size();
  cOrgBall[0] = cx / n; cOrgBall[1] = cy / n; cOrgBall[2] = cz / n;
}
// the final ledger for an imported body: cells + limb roots, no CA fields
static void emitVoxFinal() {
  std::printf("{\"type\":\"final\",\"kind\":\"creature\",\"tick\":0,");
  std::printf("\"cells\":[");
  bool first = true;
  for (const CCell& c : cCellsV) {
    std::printf("%s[%d,%d,%d,\"skin\"]", first ? "" : ",",
                c.x, c.y, c.z);
    first = false;
  }
  std::printf("],\"morphA\":{},\"turingU\":{},\"surf\":[],\"limbRoots\":[");
  for (size_t i = 0; i < cLimbs.size(); i++)
    std::printf("%s[%d,%d,%d]", i ? "," : "",
                cLimbs[i].root[0], cLimbs[i].root[1], cLimbs[i].root[2]);
  std::printf("],\"eyes\":[],\"digits\":0,\"lambdaPred\":0.0,");
  std::printf("\"organizers\":{\"head\":[%.17g,%.17g,%.17g],"
              "\"ventral\":[%.17g,%.17g,%.17g],"
              "\"ball\":[%.17g,%.17g,%.17g]},\"done\":true}\n",
              cOrgBall[0], cOrgBall[1], cOrgBall[2],
              cOrgBall[0], cOrgBall[1], cOrgBall[2],
              cOrgBall[0], cOrgBall[1], cOrgBall[2]);
  std::fflush(stdout);
}
// the stand+walk ledger (F-T1b/c): mirrors the bear's N5 physics section
// minus the wave/sense/learner bits (bear-specific). Stand = drop from 8 body-
// heights, land on the derived ground, rest to equilibrium. Walk = 400-tick
// flat-ground walk; the displacement is the N7 earned-stride sum.
static void emitVoxTest() {
  const double H = 8 * bear.bodyH;
  const double yRest = bear.bodyY;   // local support offset (0 on flat ground)
  bear.bodyY = yRest + H; bear.velY = 0; bear.contact = false;
  const double E0 = gSim * H;
  double ledgerErr = 0, lastE = E0;
  long contactTick = -1;
  for (long n = 1; n < 100000; n++) {
    physTick();
    if (bear.contact) { contactTick = n; break; }
    lastE = 0.5 * bear.velY * bear.velY + gSim * (bear.bodyY - yRest);
    const double Eexp = gSim * H - 0.5 * gSim * gSim * n;
    const double err = std::fabs(lastE - Eexp) / E0;
    if (err > ledgerErr) ledgerErr = err;
  }
  const double termDrift = (E0 - lastE) / E0;
  double restVyMax = 0, restPenMax = 0;
  for (int i = 0; i < 300; i++) {
    physTick();
    const double av = std::fabs(bear.velY);
    const double ap = std::fabs(bear.lastGround -
                                (bear.bodyY + bear.groundMinY));
    if (av > restVyMax) restVyMax = av;
    if (ap > restPenMax) restPenMax = ap;
  }
  bearCommand("walk");
  const double bxStart = bear.body[0];
  for (int i = 0; i < 400; i++) bearAnim();
  std::printf("{\"type\":\"voxtest\",\"stand\":{\"dropH\":%.17g,"
              "\"contactTick\":%ld,\"analyticTick\":%.17g,"
              "\"ledgerErr\":%.17g,\"termDrift\":%.17g,"
              "\"restVyMax\":%.17g,\"restPenMax\":%.17g},",
              H, contactTick, std::sqrt(2 * H / gSim), ledgerErr,
              termDrift, restVyMax, restPenMax);
  std::printf("\"walk\":{\"bodyX\":%.17g,\"iters\":%ld,\"nan\":%s,"
              "\"thetaMaxEver\":%.17g}}\n",
              bear.body[0] - bxStart, bear.iters,
              bear.nan ? "true" : "false", bear.thetaMaxEver);
  std::fflush(stdout);
}
static int runVox(int tickMs, bool selftest) {
  loadVox();                    // populate cCellsV + rig chains from data
  cEmitFrame(false);            // one static frame: the viewer renders the body
  emitVoxFinal();               // final ledger (done=true)
  bearRig();                    // G4 rig + N5 physics init (UNCHANGED)
  learnReset();                 // fresh learner (harmless for stand/walk)
  if (selftest) { emitRig(); emitVoxTest(); return 0; }
  return runEmbodiment(tickMs);
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
  if (W.kind == "vox") {                 // T1: cellsFile is relative to the
    const size_t slash = genomePath.find_last_of("/\\");   // genome's directory
    const std::string dir = slash == std::string::npos ? "." :
                            genomePath.substr(0, slash);
    voxCellsPath = dir + "/" + W.cellsFile;
  }
  const int tickMs = argc > 1 ? std::atoi(argv[1]) : W.tickMs;
  const bool selftest = argc > 3 && std::string(argv[3]) == "selftest";
  const double cellOut = W.kind == "wall" ? 0 : W.cell;
  // T1: an imported body presents as a creature (the viewer's PRESENT table +
  // buttons are keyed by this kind); the sim still dispatches on W.kind.
  const std::string metaKind = (W.kind == "vox") ? "creature" : W.kind;
  std::printf("{\"type\":\"meta\",\"kind\":\"%s\",\"name\":\"%s\","
              "\"cell\":%.17g,\"embodiment\":%d}\n", metaKind.c_str(),
              W.name.c_str(), cellOut, W.embodiment);
  std::fflush(stdout);
  if (W.kind == "oak") return runOak(tickMs);
  if (W.kind == "creature") return runCrit(tickMs, selftest);
  if (W.kind == "vox") return runVox(tickMs, selftest);
  return runWall(tickMs);
}
