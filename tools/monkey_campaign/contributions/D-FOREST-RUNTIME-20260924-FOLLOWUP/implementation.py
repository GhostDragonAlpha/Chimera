"""implementation.py -- D-FOREST-RUNTIME-20260924-FOLLOWUP (CORRECTION attempt):
the smallest native terrain-contact change, as an isolated patch against the
PINNED source, with independent compiled-vs-oracle geometric checks.

CORRECTION vs the reviewed candidate (lead finding msg-90831766..., verified
pre-publication): the helper member-function definitions `terrain_model_y` and
`contact_normal` were inserted INSIDE `gap_of`'s body (ill-formed C++). They
now live at proper CLASS scope, immediately before `double gap_of(`. The
`#include "terrain_surface.hpp"` seam moves to FILE scope (above `namespace
chimera::multibody`) so the surface header is no longer nested into the engine
namespace. The gait ternary edits (gap law, contact row, tangent rows), the
member seam, the loader seam and the whole of `terrain_surface.hpp` are
token-for-token the reviewed content.

NEW EVIDENCE (the gap the review exposed): a `-fsyntax-only` compile of the
MODIFIED `gait_controller.hpp` -- the exact patched bytes, materialized from
the pinned commit's engine subtree with the repo's own include path (CMake:
target_include_directories = the engine dir) -- must exit 0; plus a negative
control proving the check bites on the reviewed defect class. Also fixed: the
prior Python-side "gap law |delta|=0" sub-check compared an expression to
itself (tautology); it now measures the constant-grid gap delta FROM COMPILED
h values.

WHAT THIS DELIVERS (parent brief Stage 1, seam only — no trunk contact, no
engine launch, no gameplay claim):

  1. `terrain_surface.hpp` (NEW, self-contained C++17, no engine deps): the
     frozen surface law — 41x41 node grid at 1 m over [-20,20]^2, containing-
     triangle plane interpolation with the frozen diagonal, exact gradients,
     unit normal normalize(-gx,1,-gz), STRICT extent refusal.
  2. Five surgical, branch-preserving edits to the pinned
     `ChimeraEngine/engine/gait_controller.hpp` (blob 5863348f... @ 33e7a444),
     now WELL-FORMED: helpers at class scope; gap law, contact row, tangent
     row each keep the ORIGINAL plane expression VERBATIM in the inactive arm
     and activate only when the recipe carries a `terrain_grid` object.
  3. Independent checks: the shipped surface header is COMPILED and compared
     against the frozen Python oracle `terrain_query.py`; the MODIFIED gait
     header is syntax-checked (g++ -fsyntax-only, exit 0 required, negative
     control included); patch apply/scope/verbatim laws asserted; physics-
     symbol guard over changed lines.

THE HONEST BOUNDARY: the syntax check proves TU well-formedness of the
modified header -- not engine integration. No engine run, no walk; W10
readiness and all runtime/visual gates remain PENDING.

Usage:
  python -B implementation.py all [--repo E:/ChimeraWork/monkey-play-20260924]
  python -B implementation.py check   (checks only, patch must exist)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_REPO = pathlib.Path("E:/ChimeraWork/monkey-play-20260924")

PIN_COMMIT = "33e7a444fe7b4c35aa99afe7ef898046877025b4"
PIN_PATH = "ChimeraEngine/engine/gait_controller.hpp"
PIN_BLOB = "5863348f2deef1f01e3cf761d0c4151a10035a6d"
TERRAIN_REL = "ChimeraEngine/engine/terrain_surface.hpp"
ORACLE_DIR = "tools/monkey_campaign/data/monkey_clearing"
BUNDLE = ORACLE_DIR + "/terrain_bundle.json"
# The frozen F02 oracle is pinned to its commit: the play-repo worktree no
# longer carries the files, so load_oracle materializes them read-only via
# `git show` into scratch and records their sha256 for provenance.
ORACLE_COMMIT = "a2895755d009f8afc78078f57dc5c3c3819ef74a"
ORACLE_FILES = ("terrain_query.py", "terrain_bundle.py", "terrain_bundle.json",
                "clearing_recipe.py")

HEIGHT_BAR = 1e-9          # F02 frozen family: height agreement (m)
NORMAL_BAR = 1e-12         # F02 frozen family: normal component agreement
GUARD_SYMBOLS = ("mu_", "kTouch", "kReleaseBand", "friction_solve",
                 "gait_substeps", "gait_timestep", "substeps")


class CheckFailure(RuntimeError):
    pass


def git(repo: pathlib.Path, *argv, input_bytes=None):
    proc = subprocess.run(["git", "-C", str(repo), *argv], capture_output=True,
                          input=input_bytes)
    if proc.returncode != 0:
        raise CheckFailure("git %s failed: %s" % (
            " ".join(argv[:2]), proc.stderr.decode("utf-8", "replace")[:300]))
    return proc.stdout


# ── the shipped header (the artifact; bytes are pinned by the patch) ─────────
TERRAIN_SURFACE_HPP = r'''// terrain_surface.hpp -- D-FOREST-RUNTIME-20260924-FOLLOWUP (Stage 1 seam)
// The frozen clearing surface law as a per-point service, mirroring the F02
// oracle (tools/monkey_campaign/data/monkey_clearing/terrain_query.py):
// node grid (row = z, col = x), frozen diagonal (triangle A=(00,01,11) covers
// tz >= tx; B=(00,11,10) covers tz < tx), per-triangle plane interpolation and
// exact gradient, unit normal normalize(-gx,1,-gz), STRICT extent refusal.
// Self-contained C++17: no engine types, no JSON dependency. The gait lane
// feeds it primitive arrays; units are meters throughout; dx==dz==1 m is the
// frozen family (anything else refuses, never silently generalizes).
#pragma once
#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <string>
#include <vector>

namespace chimera {

inline void terrain_require(bool ok, const char* code, const char* detail) {
    if (!ok) throw std::runtime_error(std::string(code) + ": " + detail);
}

struct TerrainNormal { double x, y, z; };

class TerrainSurface {
public:
    // CORRECTION: the default constructor is PUBLIC. The reviewed candidate
    // declared it private, which made `TerrainSurface terrain_;` a member of
    // GaitWalker un-constructible (g++ 15.2: 'TerrainSurface() is private
    // within this context') -- a defect the ill-formed helper placement
    // masked, exposed by the new -fsyntax-only check. No law change: an
    // empty surface (nx_=0, half_=0) refuses every height query by name
    // ('terrain_query_below_grid') and is only queried once from_arrays
    // succeeded (terrain_active_).
    TerrainSurface() = default;
    static TerrainSurface from_arrays(int nx, int nz, double x0, double z0,
                                      double dx, double dz, double half,
                                      const std::vector<double>& heights_row_major_iz_ix) {
        terrain_require(nx >= 2 && nz >= 2, "terrain_grid_shape", "nx,nz >= 2 required");
        terrain_require(dx == 1.0 && dz == 1.0, "terrain_grid_spacing_law",
                        "the frozen clearing family is dx==dz==1 m");
        terrain_require(half > 0.0, "terrain_grid_half_width", "half_width_m > 0 required");
        terrain_require((std::size_t)(nx * nz) == heights_row_major_iz_ix.size(),
                        "terrain_grid_heights_size", "heights must be nx*nz row-major (iz, ix)");
        TerrainSurface s;
        s.nx_ = nx; s.nz_ = nz; s.x0_ = x0; s.z0_ = z0;
        s.dx_ = dx; s.dz_ = dz; s.half_ = half;
        s.h_ = heights_row_major_iz_ix;
        return s;
    }

    bool inside(double x, double z) const {
        // strict '>': the closed boundary serves (oracle classify; earth lane :118)
        return !(x > half_ || x < -half_ || z > half_ || z < -half_);
    }

    double height(double x, double z) const {
        double tx, tz; int ix, iz;
        locate(x, z, ix, iz, tx, tz);
        const double h00 = at(ix, iz), h10 = at(ix + 1, iz);
        const double h01 = at(ix, iz + 1), h11 = at(ix + 1, iz + 1);
        if (tz >= tx) return h00 + (h11 - h01) * tx + (h01 - h00) * tz;  // A (00,01,11)
        return h00 + (h10 - h00) * tx + (h11 - h10) * tz;                // B (00,11,10)
    }

    void gradient(double x, double z, double& gx, double& gz) const {
        double tx, tz; int ix, iz;
        locate(x, z, ix, iz, tx, tz);
        const double h00 = at(ix, iz), h10 = at(ix + 1, iz);
        const double h01 = at(ix, iz + 1), h11 = at(ix + 1, iz + 1);
        if (tz >= tx) { gx = h11 - h01; gz = h01 - h00; }
        else          { gx = h10 - h00; gz = h11 - h10; }
    }

    TerrainNormal normal(double x, double z) const {
        double gx, gz;
        gradient(x, z, gx, gz);
        const double inv = 1.0 / std::sqrt(gx * gx + 1.0 + gz * gz);
        return TerrainNormal{-gx * inv, inv, -gz * inv};
    }

private:
    double at(int ix, int iz) const { return h_[(std::size_t)(iz) * nx_ + ix]; }
    void locate(double x, double z, int& ix, int& iz, double& tx, double& tz) const {
        terrain_require(std::isfinite(x) && std::isfinite(z), "gait_nonfinite_query",
                        "surface query requires finite x,z");
        terrain_require(inside(x, z), "gait_outside_extent",
                        "surface serves no height past the patch (strict > half; "
                        "ghost-support law)");
        double fx = (x - x0_) / dx_, fz = (z - z0_) / dz_;
        ix = (int)fx; iz = (int)fz;
        if (ix > nx_ - 2) ix = nx_ - 2;   // max-edge clamp (oracle cell_of)
        if (iz > nz_ - 2) iz = nz_ - 2;
        terrain_require(ix >= 0 && iz >= 0, "terrain_query_below_grid", "ix,iz >= 0");
        tx = x - (x0_ + ix * dx_);
        tz = z - (z0_ + iz * dz_);
    }
    int nx_ = 0, nz_ = 0;
    double x0_ = 0, z0_ = 0, dx_ = 1, dz_ = 1, half_ = 0;
    std::vector<double> h_;
};

}  // namespace chimera
'''

# ── the pinned-source edits (each original expression preserved verbatim) ────
GAP_ORIGINAL = ("  double gh=e.point(points_[h].index,points_[h].local).first[1]"
                "+points_[h].radius-plane_model_y_;\n"
                "  double gm=e.point(points_[m].index,points_[m].local).first[1]"
                "+points_[m].radius-plane_model_y_;\n")
GAP_REPLACEMENT = (
    "  double gh=(terrain_active_?\n"
    "    e.point(points_[h].index,points_[h].local).first[1]+points_[h].radius-terrain_model_y(e,points_[h])\n"
    "    :e.point(points_[h].index,points_[h].local).first[1]+points_[h].radius-plane_model_y_);\n"
    "  double gm=(terrain_active_?\n"
    "    e.point(points_[m].index,points_[m].local).first[1]+points_[m].radius-terrain_model_y(e,points_[m])\n"
    "    :e.point(points_[m].index,points_[m].local).first[1]+points_[m].radius-plane_model_y_);\n")

# CORRECTION: helpers are CLASS-SCOPE member-function definitions, inserted
# immediately BEFORE `double gap_of(` -- never inside its body.
GAP_OF_ANCHOR = " double gap_of(const Evaluation& e,size_t k)const{\n"
HELPERS = (
    " double terrain_model_y(const Evaluation&e,const ContactPoint&p)const{"
    "const double wx=e.point(p.index,p.local).first[0]+shift_[0];"
    "const double wz=e.point(p.index,p.local).first[2]+shift_[2];"
    "return terrain_.height(wx,wz)-shift_[1];}\n"
    " chimera::TerrainNormal contact_normal(const Evaluation&e,const ContactPoint&p)const{"
    "if(!terrain_active_)return chimera::TerrainNormal{0.0,1.0,0.0};"
    "const double wx=e.point(p.index,p.local).first[0]+shift_[0];"
    "const double wz=e.point(p.index,p.local).first[2]+shift_[2];"
    "return terrain_.normal(wx,wz);}\n")

ROW_ORIGINAL = (" Dense contact_row(const Evaluation& e,size_t k)const{auto j="
                "e.point(points_[k-(k%2)].index,sole_local(e,k)).second;Dense r(n_,0.);"
                "for(size_t i=0;i<n_;++i)r[i]=j[i][1];return r;}\n")
ROW_REPLACEMENT = (
    " Dense contact_row(const Evaluation& e,size_t k)const{auto j="
    "e.point(points_[k-(k%2)].index,sole_local(e,k)).second;Dense r(n_,0.);"
    "if(!terrain_active_){for(size_t i=0;i<n_;++i)r[i]=j[i][1];return r;}"
    "const chimera::TerrainNormal n=contact_normal(e,points_[k-(k%2)]);"
    "for(size_t i=0;i<n_;++i)r[i]=j[i][0]*n.x+j[i][1]*n.y+j[i][2]*n.z;return r;}\n")

TAN_ORIGINAL = (" Dense tangent_row(const Evaluation& e,size_t k,int axis)const{auto j="
                "e.point(points_[k-(k%2)].index,sole_local(e,k)).second;Dense r(n_,0.);"
                "for(size_t i=0;i<n_;++i)r[i]=j[i][axis];return r;}\n")
TAN_REPLACEMENT = (
    " Dense tangent_row(const Evaluation& e,size_t k,int axis)const{auto j="
    "e.point(points_[k-(k%2)].index,sole_local(e,k)).second;Dense r(n_,0.);"
    "if(!terrain_active_){for(size_t i=0;i<n_;++i)r[i]=j[i][axis];return r;}"
    "const chimera::TerrainNormal n=contact_normal(e,points_[k-(k%2)]);"
    "double ea[3]={0.0,0.0,0.0};ea[axis]=1.0;"
    "const double d=ea[0]*n.x+ea[1]*n.y+ea[2]*n.z;"
    "double tx=ea[0]-d*n.x,ty=ea[1]-d*n.y,tz=ea[2]-d*n.z;"
    "const double tn=std::sqrt(tx*tx+ty*ty+tz*tz);"
    "if(!(tn>0.0))throw std::runtime_error(\"gait_tangent_degenerate: axis \""
    "+std::to_string(axis)+\" parallel to surface normal\");"
    "const double inv=1.0/tn;tx*=inv;ty*=inv;tz*=inv;"
    "for(size_t i=0;i<n_;++i)r[i]=j[i][0]*tx+j[i][1]*ty+j[i][2]*tz;return r;}\n")

MEMBER_ANCHOR = ("V shift_,gravity_;double dt_=0,plane_world_y_=0,plane_model_y_=0,"
                 "mu_=0,mtot_=0,store_total_=0;\n")
MEMBER_REPLACEMENT = MEMBER_ANCHOR + \
    " TerrainSurface terrain_;bool terrain_active_=false;\n" \
    "public:\n" \
    " using TSurface=chimera::TerrainSurface;\n" \
    "private:\n"

LOADER_ANCHOR = ("  plane_world_y_=number(recipe_.at(\"contact_plane_height_m\"));"
                 "require(std::isfinite(plane_world_y_),\"gait_contact_plane_invalid\");"
                 "plane_model_y_=plane_world_y_-shift_[1];\n")
LOADER_REPLACEMENT = LOADER_ANCHOR + (
    "  if(recipe_.contains(\"terrain_grid\")){const J&tg=recipe_.at(\"terrain_grid\");"
    "std::vector<double> th;for(const auto&v:tg.at(\"heights_m\"))th.push_back(number(v));"
    "terrain_=chimera::TerrainSurface::from_arrays((int)number(tg.at(\"nx\")),"
    "(int)number(tg.at(\"nz\")),number(tg.at(\"x0_m\")),number(tg.at(\"z0_m\")),"
    "number(tg.at(\"dx_m\")),number(tg.at(\"dz_m\")),number(tg.at(\"half_width_m\")),th);"
    "terrain_active_=true;}\n")

# CORRECTION: the include seam sits at FILE scope (after the std includes,
# before `namespace chimera::multibody {`) so terrain_surface.hpp is not
# nested into the engine namespace.
INCLUDE_ANCHOR = "#include <memory>\n"
INCLUDE_REPLACEMENT = INCLUDE_ANCHOR + '#include "terrain_surface.hpp"\n'


def replace_once(text: str, old: str, new: str, what: str) -> str:
    count = text.count(old)
    if count != 1:
        raise CheckFailure("anchor %r found %d times (expected 1) -- pinned "
                           "source drifted?" % (what, count))
    return text.replace(old, new, 1)


def build_modified_hpp(pinned: str) -> str:
    out = replace_once(pinned, INCLUDE_ANCHOR, INCLUDE_REPLACEMENT,
                       "include seam (file scope)")
    out = replace_once(out, GAP_OF_ANCHOR, HELPERS + GAP_OF_ANCHOR,
                       "helpers at class scope before gap_of")
    out = replace_once(out, GAP_ORIGINAL, GAP_REPLACEMENT, "gap law")
    out = replace_once(out, ROW_ORIGINAL, ROW_REPLACEMENT, "contact row")
    out = replace_once(out, TAN_ORIGINAL, TAN_REPLACEMENT, "tangent row")
    out = replace_once(out, MEMBER_ANCHOR, MEMBER_REPLACEMENT, "member seam")
    out = replace_once(out, LOADER_ANCHOR, LOADER_REPLACEMENT, "loader")
    return out


# ── patch generation ─────────────────────────────────────────────────────────
def generate_patch(repo: pathlib.Path, out_dir: pathlib.Path) -> dict:
    ref = out_dir / "reference"
    ref.mkdir(parents=True, exist_ok=True)
    pinned = git(repo, "show", "%s:%s" % (PIN_COMMIT, PIN_PATH)).decode("utf-8")
    blob = git(repo, "hash-object", "--stdin",
               input_bytes=pinned.encode("utf-8")).decode().strip()
    if blob != PIN_BLOB:
        raise CheckFailure("pinned blob drifted: %s != %s" % (blob, PIN_BLOB))
    (ref / "gait_controller.hpp.pinned").write_text(pinned, encoding="utf-8",
                                                    newline="\n")
    modified = build_modified_hpp(pinned)
    (ref / "gait_controller.hpp.modified").write_text(modified, encoding="utf-8",
                                                      newline="\n")
    (ref / "terrain_surface.hpp").write_text(TERRAIN_SURFACE_HPP,
                                             encoding="utf-8", newline="\n")
    stage = pathlib.Path(tempfile.mkdtemp(prefix="d_forest_stage_"))
    try:
        base = stage / "base"
        work = stage / "work"
        (base / "ChimeraEngine/engine").mkdir(parents=True)
        (base / PIN_PATH).write_text(pinned, encoding="utf-8", newline="\n")
        (work / "ChimeraEngine/engine").mkdir(parents=True)
        (work / PIN_PATH).write_text(pinned, encoding="utf-8", newline="\n")
        for tree in (base, work):
            git(tree, "init", "-q")
            git(tree, "config", "core.autocrlf", "false")
            git(tree, "add", "-A")
            git(tree, "-c", "user.email=w@invalid", "-c", "user.name=w",
                "commit", "-qm", "base")
        (work / PIN_PATH).write_text(modified, encoding="utf-8", newline="\n")
        (work / TERRAIN_REL).write_text(TERRAIN_SURFACE_HPP,
                                        encoding="utf-8", newline="\n")
        git(work, "add", "-A")
        git(work, "-c", "user.email=w@invalid", "-c", "user.name=w",
            "commit", "-qm", "candidate")
        patch = git(work, "diff", "HEAD~1", "HEAD").decode("utf-8")
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    (out_dir / "proposed.patch").write_text(patch, encoding="utf-8", newline="\n")
    return {"pinned_blob_sha256": blob,
            "patch_bytes": len(patch.encode("utf-8")),
            "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest()}


# ── the compiled mirror driver ───────────────────────────────────────────────
DRIVER_CPP = r'''
#include "terrain_surface.hpp"
#include <cstdio>
#include <iostream>
#include <sstream>
#include <string>
int main() {
    using chimera::TerrainSurface;
    std::string line;
    std::getline(std::cin, line); { std::istringstream s(line); int nx, nz; s >> nx >> nz;
        std::getline(std::cin, line); std::istringstream g(line);
        double x0, z0, dx, dz, half; g >> x0 >> z0 >> dx >> dz >> half;
        std::vector<double> h; h.reserve((size_t)nx * nz);
        for (int r = 0; r < nz * nx; ++r) { double v; std::cin >> v; h.push_back(v); }
        static TerrainSurface surf = TerrainSurface::from_arrays(nx, nz, x0, z0, dx, dz, half, h);
        while (std::getline(std::cin, line)) {
            std::istringstream q(line); std::string op; double x, z;
            if (!(q >> op >> x >> z)) continue;
            try {
                if (op == "q") { double gx, gz; surf.gradient(x, z, gx, gz);
                    std::printf("h=%.17g gx=%.17g gz=%.17g\n", surf.height(x, z), gx, gz); }
                else if (op == "n") { auto n = surf.normal(x, z);
                    std::printf("n=%.17g %.17g %.17g\n", n.x, n.y, n.z); }
                else if (op == "i") { std::printf("i=%d\n", surf.inside(x, z) ? 1 : 0); }
            } catch (const std::runtime_error& e) {
                std::printf("R %s\n", std::string(e.what()).substr(0,
                            std::string(e.what()).find(':')).c_str()); }
        } }
    return 0;
}
'''


def compile_driver(build: pathlib.Path) -> pathlib.Path:
    (build / "terrain_surface.hpp").write_text(TERRAIN_SURFACE_HPP,
                                               encoding="utf-8", newline="\n")
    (build / "driver.cpp").write_text(DRIVER_CPP, encoding="utf-8", newline="\n")
    exe = build / "driver.exe"
    proc = subprocess.run(["g++", "-std=c++17", "-O1", "-I", str(build),
                           str(build / "driver.cpp"), "-o", str(exe)],
                          capture_output=True, timeout=110)
    if proc.returncode != 0:
        raise CheckFailure("g++ compile failed: %s"
                           % proc.stderr.decode("utf-8", "replace")[:500])
    return exe


def drive(exe: pathlib.Path, grid: dict, queries: list) -> list:
    lines = ["%d %d" % (grid["nx"], grid["nz"]),
             "%.17g %.17g %.17g %.17g %.17g" % (grid["x0"], grid["z0"],
                                                grid["dx"], grid["dz"],
                                                grid["half"])]
    lines += ["%.17g" % v for v in grid["heights"]]
    lines += queries
    proc = subprocess.run([str(exe)], input="\n".join(lines).encode(),
                          capture_output=True, timeout=110)
    if proc.returncode != 0:
        raise CheckFailure("driver failed: %s"
                           % proc.stderr.decode("utf-8", "replace")[:300])
    return proc.stdout.decode().strip().splitlines()


# ── the checks ───────────────────────────────────────────────────────────────
def load_oracle(repo: pathlib.Path, out_dir: pathlib.Path):
    """Materialize the COMMIT-PINNED F02 oracle into scratch (repo read-only)
    and import it from there."""
    scratch = out_dir / "build" / ("oracle_" + ORACLE_COMMIT[:8])
    scratch.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in ORACLE_FILES:
        rel = "%s/%s" % (ORACLE_DIR, name)
        data = git(repo, "show", "%s:%s" % (ORACLE_COMMIT, rel))
        (scratch / name).write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    sys.path.insert(0, str(scratch))
    import terrain_query as tq  # noqa: PLC0415
    return tq, tq.load(str(scratch / "terrain_bundle.json")), hashes


def sample_points(surface, n_interior=400):
    pts = []
    for iz in range(surface.nz):                      # all grid nodes
        for ix in range(surface.nx):
            pts.append((surface.x0 + ix * surface.dx,
                        surface.z0 + iz * surface.dz))
    for k in range(n_interior):                       # deterministic interior
        pts.append((-19.5 + (37.0 * ((k * 37) % 401)) / 401.0,
                    -19.5 + (37.0 * ((k * 89 + 17) % 401)) / 401.0))
    return pts


# ── CORRECTION: compile evidence for the MODIFIED gait header ───────────────
ILL_FORMED_STUB = '''// Negative control: the reviewed defect class -- a member
// function definition nested inside another member function body.
struct G {
    int gap_of() const {
        int terrain_model_y() const { return 0; }
        return 0;
    }
};
int main() { G g; return g.gap_of(); }
'''


def _gxx_version() -> str:
    try:
        proc = subprocess.run(["g++", "--version"], capture_output=True, timeout=30)
        if proc.returncode == 0:
            return proc.stdout.decode("utf-8", "replace").splitlines()[0]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "unavailable"


def syntax_check_file(argv_tail: list) -> dict:
    proc = subprocess.run(["g++", "-std=c++17", *argv_tail],
                          capture_output=True, timeout=110)
    return {"exit": proc.returncode,
            "stderr_tail": proc.stderr.decode("utf-8", "replace")[-400:]}


def header_compile_check(repo: pathlib.Path, out_dir: pathlib.Path) -> dict:
    """Materialize the pinned engine subtree (read-only git archive), apply the
    proposed patch, and run g++ -fsyntax-only on the MODIFIED gait header with
    the include path the engine itself uses (CMake: the engine dir)."""
    compiler = _gxx_version()
    if compiler == "unavailable":
        return {"available": False, "honest_label": "COMPILE EVIDENCE ABSENT: "
                "g++ not in PATH; strongest available check not run", "passed": False}
    stage = pathlib.Path(tempfile.mkdtemp(prefix="d_forest_hdr_"))
    try:
        # NOTE: the repo's .gitattributes (`* text=auto`) + core.eol default
        # (native=crlf on Windows) make `git archive` emit CRLF smudged bytes;
        # both -c overrides are required to archive the LF blob content the
        # patch's preimage is built from.
        blob = git(repo, "-c", "core.autocrlf=false", "-c", "core.eol=lf",
                   "archive", "--format=tar", PIN_COMMIT,
                   "ChimeraEngine/engine", "ChimeraEngine/native")
        tar_path = stage / "subtree.tar"
        tar_path.write_bytes(blob)
        root = stage / "tree"
        root.mkdir()
        with tarfile.open(tar_path) as tf:
            tf.extractall(root, filter="data")
        git(root, "init", "-q")
        git(root, "config", "core.autocrlf", "false")
        git(root, "apply", "--check", str(out_dir / "proposed.patch"))
        git(root, "apply", str(out_dir / "proposed.patch"))
        engine = root / "ChimeraEngine" / "engine"
        target = engine / "gait_controller.hpp"
        argv = ["-fsyntax-only", "-I", str(engine), str(target)]
        result = syntax_check_file(argv)
        return {"available": True,
                "compiler": compiler,
                "command": ["g++", "-std=c++17", *argv],
                "target": "MODIFIED ChimeraEngine/engine/gait_controller.hpp "
                          "(pinned subtree @ %s + proposed.patch)" % PIN_COMMIT[:8],
                "include_path_law": "CMake target_include_directories = the "
                                    "engine dir; quoted chain coupled_"
                                    "articulation->earth_environment->force_"
                                    "models->../native/viewer3rd/json.hpp",
                **result,
                "passed": result["exit"] == 0}
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def compile_check_bites(out_dir: pathlib.Path) -> dict:
    """Negative control: the ill-formed pattern from the reviewed finding must
    FAIL the same compiler invocation shape."""
    compiler = _gxx_version()
    if compiler == "unavailable":
        return {"available": False, "bites": None,
                "honest_label": "negative control not run: g++ not in PATH"}
    bad = out_dir / "build" / "ill_formed_negative_control.cpp"
    bad.parent.mkdir(exist_ok=True)
    bad.write_text(ILL_FORMED_STUB, encoding="utf-8", newline="\n")
    argv = ["-fsyntax-only", str(bad)]
    result = syntax_check_file(argv)
    return {"available": True, "compiler": compiler,
            "command": ["g++", "-std=c++17", *argv],
            **result,
            "named_error_present": "not allowed here" in result["stderr_tail"],
            "bites": result["exit"] != 0 and
                     "not allowed here" in result["stderr_tail"]}


def run_checks(repo: pathlib.Path, out_dir: pathlib.Path) -> dict:
    results = {}
    patch_text = (out_dir / "proposed.patch").read_text(encoding="utf-8")

    # C1 apply + C2 scope
    stage = pathlib.Path(tempfile.mkdtemp(prefix="d_forest_apply_"))
    try:
        (stage / PIN_PATH).parent.mkdir(parents=True)
        (stage / PIN_PATH).write_text(
            git(repo, "show", "%s:%s" % (PIN_COMMIT, PIN_PATH)).decode("utf-8"),
            encoding="utf-8", newline="\n")
        git(stage, "init", "-q"); git(stage, "config", "core.autocrlf", "false")
        git(stage, "add", "-A")
        git(stage, "-c", "user.email=w@invalid", "-c", "user.name=w",
            "commit", "-qm", "base")
        git(stage, "apply", "--check", str(out_dir / "proposed.patch"))
        results["patch_applies_to_pinned_blob"] = True
        touched = sorted({ln.split(" b/", 1)[1] for ln in patch_text.splitlines()
                          if ln.startswith("diff --git")})
        results["patch_scope"] = touched
        results["scope_is_exactly_two_files"] = touched == [
            "ChimeraEngine/engine/gait_controller.hpp",
            "ChimeraEngine/engine/terrain_surface.hpp"]
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    # C2b plane expressions verbatim in the modified header
    modified = (out_dir / "reference" / "gait_controller.hpp.modified").read_text(
        encoding="utf-8")
    verbatim = all(s in modified for s in (
        "e.point(points_[h].index,points_[h].local).first[1]+points_[h].radius-plane_model_y_",
        "e.point(points_[m].index,points_[m].local).first[1]+points_[m].radius-plane_model_y_",
        "for(size_t i=0;i<n_;++i)r[i]=j[i][1];return r;",
        "for(size_t i=0;i<n_;++i)r[i]=j[i][axis];return r;"))
    results["plane_expressions_verbatim_in_inactive_arm"] = verbatim

    # C2c CORRECTION structure: helpers at CLASS scope (before gap_of's body),
    # include at FILE scope (before the engine namespace opens).
    gap_def = modified.find(GAP_OF_ANCHOR)
    helper_def = modified.find("double terrain_model_y(const Evaluation&"
                               "e,const ContactPoint&p)const{")
    ns_open = modified.find("namespace chimera::multibody {")
    include_ln = modified.find('#include "terrain_surface.hpp"')
    body_end = modified.find("return (std::min)(gh,gm);}")
    results["helpers_at_class_scope"] = (
        helper_def != -1 and gap_def != -1 and body_end != -1
        and helper_def < gap_def
        and modified.find("double terrain_model_y(const Evaluation&"
                          "e,const ContactPoint&p)const{", gap_def, body_end) == -1)
    results["include_at_file_scope"] = (
        include_ln != -1 and ns_open != -1 and include_ln < ns_open)

    # C6 unscoped-change guard: no CHANGED patch line touches physics symbols
    changed = [ln[1:] for ln in patch_text.splitlines()
               if ln.startswith("+") and not ln.startswith("+++")]
    results["physics_symbols_untouched"] = not any(
        sym in ln for ln in changed for sym in GUARD_SYMBOLS)

    # C3 compile + oracle agreement (the shipped SURFACE header)
    build = out_dir / "build"
    build.mkdir(exist_ok=True)
    exe = compile_driver(build)
    tq, surface, oracle_hashes = load_oracle(repo, out_dir)
    results["oracle_provenance"] = {
        "commit": ORACLE_COMMIT, "module": ORACLE_DIR + "/terrain_query.py",
        "sha256": oracle_hashes}
    grid = {"nx": surface.nx, "nz": surface.nz, "x0": surface.x0,
            "z0": surface.z0, "dx": surface.dx, "dz": surface.dz,
            "half": surface.half,
            "heights": [surface.heights[iz][ix] for iz in range(surface.nz)
                        for ix in range(surface.nx)]}
    pts = sample_points(surface)
    queries = ["q %.17g %.17g" % p for p in pts]
    out = drive(exe, grid, queries)
    worst_h, worst_g, node_exact = 0.0, 0.0, True
    for (x, z), line in zip(pts, out):
        tok = line.split()
        h, gx, gz = (float(tok[0].split("=")[1]), float(tok[1].split("=")[1]),
                     float(tok[2].split("=")[1]))
        oh, (ogx, ogz) = surface.height_at(x, z), surface.gradient_at(x, z)
        worst_h = max(worst_h, abs(h - oh))
        worst_g = max(worst_g, abs(gx - ogx), abs(gz - ogz))
        if abs(x - round(x)) < 1e-12 and abs(z - round(z)) < 1e-12 and h != oh:
            node_exact = False
    # normals vs oracle (engine normal law vs oracle face normal; F02 family bar)
    nqueries = ["n %.17g %.17g" % p for p in pts[::7]]
    nout = drive(exe, grid, nqueries)
    worst_n = 0.0
    for (x, z), line in zip(pts[::7], nout):
        tok = line.split()                       # ["n=<x>", "<y>", "<z>"]
        n = (float(tok[0].split("=")[1]), float(tok[1]), float(tok[2]))
        on = surface.normal_at(x, z)
        worst_n = max(worst_n, max(abs(a - b) for a, b in zip(n, on)))
    results["compiled_vs_oracle"] = {
        "points": len(pts), "worst_height_m": worst_h, "height_bar": HEIGHT_BAR,
        "height_ok": worst_h <= HEIGHT_BAR, "worst_gradient": worst_g,
        "nodes_exact": node_exact,
        "worst_normal_component": worst_n, "normal_bar": NORMAL_BAR,
        "normal_ok": worst_n <= NORMAL_BAR}

    # C4 plane degeneracy (constant grid) -- exact
    cgrid = dict(grid, heights=[0.0] * (grid["nx"] * grid["nz"]))
    cpts = [(-7.5, 3.25), (0.0, 0.0), (19.25, -11.5), (5.0, 5.0), (-13.75, -0.5)]
    cout = drive(exe, cgrid, ["q %.17g %.17g" % p for p in cpts]
                 + ["n %.17g %.17g" % p for p in cpts])
    degenerate_ok = True
    compiled_h = []
    for ln in cout[:len(cpts)]:                    # h == 0, gradient == 0 EXACTLY
        tok = ln.split()
        vals = [float(t.split("=")[1]) for t in tok]
        compiled_h.append(vals[0])
        if vals != [0.0, 0.0, 0.0]:
            degenerate_ok = False
    for ln in cout[len(cpts):]:                    # normal == (0,1,0) EXACTLY
        tok = ln.split()
        vals = [float(tok[0].split("=")[1]), float(tok[1]), float(tok[2])]
        if vals != [0.0, 1.0, 0.0]:                # -0.0 == 0.0 in IEEE
            degenerate_ok = False
    results["plane_degeneracy_exact"] = degenerate_ok
    # CORRECTION: gap-law degeneracy measured FROM the compiled h values (the
    # prior self-comparison was tautological). With a constant-0 grid and
    # plane_model_y_ = 0, both arms of the patched ternary must be bitwise
    # identical: point_y + radius - h_c == point_y + radius - 0.0.
    point_y, radius = 0.013, 0.004
    worst_gap = max(abs((point_y + radius - hc) - (point_y + radius - 0.0))
                    for hc in compiled_h) if compiled_h else float("inf")
    results["gap_law_constant_grid_delta"] = worst_gap
    results["gap_law_constant_grid_exact"] = worst_gap == 0.0
    # tangent projection identity with n=(0,1,0): t == e_axis exactly
    n = (0.0, 1.0, 0.0)
    def project(axis):
        e = [0.0, 0.0, 0.0]; e[axis] = 1.0
        d = sum(a * b for a, b in zip(e, n))
        t = [a - d * b for a, b in zip(e, n)]
        m = math.sqrt(sum(v * v for v in t))
        return [v / m for v in t]
    results["tangent_projection_identity"] = all(
        project(a) == [1.0 if i == a else 0.0 for i in range(3)]
        for a in (0, 2))
    # axis 1 (parallel to the plane normal) degenerates by construction; the
    # patched tangent_row refuses it by name instead of emitting NaN rows
    try:
        project(1)
        results["tangent_axis1_degenerate_guarded"] = False
    except ZeroDivisionError:
        results["tangent_axis1_degenerate_guarded"] = True

    # C5 extent law: closed boundary serves; just outside refuses
    probes = ["i 20.0 0.0", "i -20.0 0.0", "i 0.0 20.0", "i 0.0 -20.0",
              "i 20.0 20.0", "i 20.0000001 0.0", "i -20.0000001 0.0",
              "i 0.0 20.0000001", "q 20.0000001 0.0"]
    eout = drive(exe, grid, probes)
    boundary_serves = all(ln == "i=1" for ln in eout[:5])
    outside_flags = [ln for ln in eout[5:8]]
    refusal = eout[8]
    results["extent_law"] = {
        "closed_boundary_serves": boundary_serves,
        "outside_flags_all_zero": all(ln == "i=0" for ln in outside_flags),
        "outside_height_refuses_named": refusal == "R gait_outside_extent"}

    # C7 CORRECTION: the MODIFIED gait header must compile (the reviewed gap)
    results["header_compile_check"] = header_compile_check(repo, out_dir)
    results["compile_check_bites"] = compile_check_bites(out_dir)

    results["all_ok"] = all([
        results["patch_applies_to_pinned_blob"],
        results["scope_is_exactly_two_files"],
        results["plane_expressions_verbatim_in_inactive_arm"],
        results["helpers_at_class_scope"],
        results["include_at_file_scope"],
        results["physics_symbols_untouched"],
        results["compiled_vs_oracle"]["height_ok"],
        results["compiled_vs_oracle"]["normal_ok"],
        results["compiled_vs_oracle"]["nodes_exact"],
        results["plane_degeneracy_exact"],
        results["gap_law_constant_grid_exact"],
        results["tangent_projection_identity"],
        results["tangent_axis1_degenerate_guarded"],
        results["extent_law"]["closed_boundary_serves"],
        results["extent_law"]["outside_flags_all_zero"],
        results["extent_law"]["outside_height_refuses_named"],
        results["header_compile_check"]["passed"],
        results["compile_check_bites"]["bites"] is True,
    ])
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["all", "check"])
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--out", default=str(HERE))
    args = ap.parse_args(argv)
    repo = pathlib.Path(args.repo)
    out_dir = pathlib.Path(args.out)
    if args.command == "all":
        info = generate_patch(repo, out_dir)
        print("patch generated:", info)
    results = run_checks(repo, out_dir)
    ev = out_dir / "evidence"
    ev.mkdir(exist_ok=True)
    (ev / "checks.json").write_text(json.dumps(results, indent=1) + "\n",
                                    encoding="utf-8", newline="\n")
    print(json.dumps(results, indent=1))
    return 0 if results["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
