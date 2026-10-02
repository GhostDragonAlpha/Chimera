// combine_core.hpp -- deterministic combine core (ENGINE LIFT).
//
// Lift of the approved standalone core wk-runtime-combine combine_core.py
// (lane commit ff4db632da7de133422fbac8aecd386b1c3905c4; base design
// DESIGN.md, EVIDENCE receipt 72859208) into the engine, per the engine
// wiring plan (ENGINE_WIRING_PLAN.md 648ee3c4, target master 522e4ae2).
// Substrate: the PR #319 ContributionExecutor seam (contribution_executor.hpp)
// already consumed by coupled_articulation.hpp Model::evaluate (S-A) and
// coupled_dynamics.hpp (constructor + evaluate plumbing).
//
// The s5 law, unchanged from the approved core:
//   compute independent contributions in parallel,
//   combine deterministically,
//   update each state through its owner,
//   report non-convergence rather than silently accepting an incomplete solve.
//
// Determinism law (as approved): contribution compute functions are PURE --
// they read frozen window inputs and return values; they never mutate shared
// state. Completed results are collected into fixed slots (the executor's own
// contract: "callbacks own distinct result slots and read immutable inputs"),
// and the COMBINE always proceeds in a FIXED canonical order: sorted
// contribution ids, sorted state ids, canonical ledger bytes. Combined-state
// digests hash canonical bytes (sorted ids, hexfloat doubles), so repeated
// runs and every worker interleaving are byte-identical or the caller sees a
// named refusal.
//
// CPU profile (as approved): the pool is capped at four workers -- the
// executor itself refuses >4 (contribution_worker_count_out_of_range) and the
// helpers here refuse >4 by the approved name combine_thread_budget_exceeded.
// THE LIVE DEFAULT IS ONE WORKER (the PR #319 serial law): a null executor or
// a workers()==1 executor runs the identical serial path with no threads.
// Parallel execution is for measured independent-config batches (the
// separately gated whole-game qualification), never a live-tick default.
//
// Named refusals (verbatim from the approved core, minus the Python-only
// pin/contract-validator codes that live in the guards tooling):
//   combine_non_owner_write            state mutation outside the declared owner
//   combine_unknown_state              read/apply of an unregistered state
//   combine_unknown_contribution       duplicate/undeclared contribution id or owner
//   combine_undeclared_contribution_output
//                                      a produced state outside the frozen declaration
//   combine_double_state_write         two contributions claim one state
//   combine_status_regression          status flowed backwards
//   combine_thread_budget_exceeded     worker request above the 4-thread profile
//   combine_bad_status                 status outside the declared flow
//
// Deviations from the Python core, declared honestly:
//  * explicit-synchronization windows only. The implicit/serial_implicit/
//    parallel_implicit iteration machinery stays in the Python fixtures
//    (DESIGN.md stage 3); the ordered engine passes are one-shot windows.
//  * status flow is carried but the engine callers advance straight to
//    accepted on a routed window (the approved explicit-path behavior).
//  * the canonical digest is FNV-1a/64 over canonical bytes, not sha256
//    (std-only header; byte-stability is what the law needs, and the gate
//    captures carry full hexfloat state streams for byte comparison).

#pragma once
#include "contribution_executor.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <functional>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace chimera::combine {

// ---------- named refusals ----------------------------------------------------

class Refusal : public std::runtime_error {
 public:
    Refusal(std::string code, std::string detail)
        : std::runtime_error(code + ": " + detail), code_(std::move(code)),
          detail_(std::move(detail)) {}
    const std::string& code() const noexcept { return code_; }
    const std::string& detail() const noexcept { return detail_; }

 private:
    std::string code_, detail_;
};

inline void require_worker_budget(std::size_t workers) {
    if (workers > 4)
        throw Refusal("combine_thread_budget_exceeded",
                      "requested " + std::to_string(workers) +
                      " workers; the 4-thread profile caps the pool and "
                      "nested parallelism is restricted");
}

// ---------- canonical bytes + digest ------------------------------------------

// Hexfloat form: exact, round-trippable, identical across optimizers and
// compiler libraries for identical IEEE-754 doubles. -0.0 and 0.0 are
// distinct bytes by design (the digest sees them distinctly).
inline std::string canonical(double value) {
    char buf[64];
    std::snprintf(buf, sizeof(buf), "%a", value);
    return buf;
}

// FNV-1a/64 over the canonical byte stream.
inline std::string digest64(const std::string& bytes) {
    std::uint64_t h = 1469598103934665603ull;
    for (unsigned char c : bytes) {
        h ^= c;
        h *= 1099511628211ull;
    }
    char buf[32];
    std::snprintf(buf, sizeof(buf), "%016llx",
                  static_cast<unsigned long long>(h));
    return buf;
}

// ---------- owned state store ---------------------------------------------------

// Status flow (monotone, as approved).
inline const std::vector<std::string>& status_flow() {
    static const std::vector<std::string> flow{"predicted", "iterating",
                                               "accepted"};
    return flow;
}

class OwnedStateStore {
 public:
    OwnedStateStore() = default;

    void register_state(const std::string& state_id,
                        const std::string& owner_membrane) {
        auto it = owners_.find(state_id);
        if (it != owners_.end() && it->second != owner_membrane)
            throw Refusal("combine_unknown_contribution",
                          "state " + state_id + " re-registered under " +
                          owner_membrane + " while owned by " + it->second);
        owners_[state_id] = owner_membrane;
        if (!values_.count(state_id)) values_[state_id] = 0.0;
        if (!status_.count(state_id)) status_[state_id] = "predicted";
    }

    const std::string& owner_of(const std::string& state_id) const {
        auto it = owners_.find(state_id);
        if (it == owners_.end())
            throw Refusal("combine_unknown_state",
                          "state_id " + state_id + " is not registered");
        return it->second;
    }

    bool has(const std::string& state_id) const {
        return values_.count(state_id) != 0;
    }

    double read(const std::string& state_id) const {
        auto it = values_.find(state_id);
        if (it == values_.end())
            throw Refusal("combine_unknown_state",
                          "state_id " + state_id + " is not registered");
        return it->second;
    }

    // The ONLY mutation door, as approved: a non-owner write is refused by
    // name and leaves the store byte-identical.
    void apply(const std::string& state_id, double value,
               const std::string& actor) {
        const std::string& owner = owner_of(state_id);
        if (actor != owner)
            throw Refusal("combine_non_owner_write",
                          "state_id " + state_id + " actor " + actor +
                          " owner " + owner +
                          " (state mutation routes through the declared "
                          "owner ONLY)");
        values_[state_id] = value;
        ++applies_;
    }

    void set_status(const std::string& state_id, const std::string& next,
                    const std::string& actor) {
        const std::string& owner = owner_of(state_id);
        if (actor != owner)
            throw Refusal("combine_non_owner_write",
                          "state_id " + state_id + " actor " + actor +
                          " owner " + owner + " op set_status");
        const auto& flow = status_flow();
        auto at = std::find(flow.begin(), flow.end(), next);
        if (at == flow.end())
            throw Refusal("combine_bad_status",
                          "state_id " + state_id + " status " + next);
        const std::string& old = status_[state_id];
        auto old_at = std::find(flow.begin(), flow.end(), old);
        if (at < old_at)
            throw Refusal("combine_status_regression",
                          "state_id " + state_id + " from " + old + " to " +
                          next +
                          " (value status flows predicted -> iterating -> "
                          "accepted and never regresses)");
        if (next != old) status_[state_id] = next;
    }

    void advance_all(const std::string& floor) {
        for (const auto& entry : owners_)
            set_status(entry.first, floor, entry.second);
    }

    // Canonical bytes: sorted state ids, hexfloat values, sorted status
    // pairs. Identical stores -> identical bytes, at any worker count.
    std::string canonical_bytes() const {
        std::string out;
        for (const auto& v : values_) {          // std::map: sorted ids
            out += v.first;
            out += '=';
            out += canonical(v.second);
            out += ';';
        }
        for (const auto& s : status_) {
            out += s.first;
            out += '~';
            out += s.second;
            out += ';';
        }
        return out;
    }

    std::string digest() const { return digest64(canonical_bytes()); }

    std::size_t applies() const noexcept { return applies_; }

 private:
    std::map<std::string, std::string> owners_;
    std::map<std::string, double> values_;
    std::map<std::string, std::string> status_;
    std::size_t applies_ = 0;
};

// ---------- contributions ---------------------------------------------------------

struct LedgerEntry {
    std::string entry_id;
    std::string unit;
    double value = 0.0;
    std::string canonical_bytes() const {
        return entry_id + '|' + unit + '|' + canonical(value);
    }
};

struct ContributionResult {
    std::map<std::string, double> states;   // state_id -> produced value
    std::vector<LedgerEntry> ledger;
};

struct Contribution {
    std::string contribution_id;
    std::string owner_membrane;
    std::vector<std::string> produces;      // frozen at construction (below)
    std::function<ContributionResult(std::size_t index)> compute;  // pure
};

// ---------- the scheduler -----------------------------------------------------------

class CombineScheduler {
 public:
    // `executor` may be null (serial) or a workers()==1 executor (serial, no
    // threads): both run the identical serial path. Workers 2..4 execute the
    // contributions over the pool; the combine stays canonical either way.
    // `store` is CALLER-OWNED and shared across the ordered windows of one
    // tick (window k+1 reads what window k routed; no window mutates while
    // another computes).
    CombineScheduler(std::vector<Contribution> contributions,
                     chimera::multibody::ContributionExecutor* executor,
                     OwnedStateStore& store)
        : executor_(executor), store_(store) {
        if (executor) require_worker_budget(executor->workers());
        std::sort(contributions.begin(), contributions.end(),
                  [](const Contribution& a, const Contribution& b) {
                      return a.contribution_id < b.contribution_id;
                  });
        for (const auto& c : contributions) {
            if (c.contribution_id.empty())
                throw Refusal("combine_unknown_contribution",
                              "contribution ids are required");
            if (!ids_.insert(c.contribution_id).second)
                throw Refusal("combine_unknown_contribution",
                              "duplicate contribution id " +
                              c.contribution_id);
            contributions_.push_back(c);
            produces_.emplace(c.contribution_id, c.produces);
        }
    }

    OwnedStateStore& store() noexcept { return store_; }
    const OwnedStateStore& store() const noexcept { return store_; }

    // One explicit window: run every contribution (slot per canonical index),
    // combine in the fixed canonical order, route through the owners.
    // Refusals restore nothing here -- the store rejects refused writes
    // byte-identically and the caller owns the tick's failure law.
    struct WindowReport {
        std::size_t contributions = 0;
        std::size_t applied = 0;
        std::vector<std::string> routed;   // "cid->state_id" in canonical order
    };

    WindowReport run_window() {
        WindowReport report;
        report.contributions = contributions_.size();
        const std::size_t n = contributions_.size();
        std::vector<ContributionResult> results(n);
        if (executor_ && executor_->workers() > 1) {
            executor_->for_each(n, [&](std::size_t index) {
                results[index] = contributions_[index].compute(index);
            });
        } else {
            for (std::size_t index = 0; index < n; ++index)
                results[index] = contributions_[index].compute(index);
        }
        // Canonical combine: canonical contribution order (the vector IS the
        // sorted order), sorted state ids per contribution, canonical ledger.
        for (std::size_t index = 0; index < n; ++index) {
            const Contribution& c = contributions_[index];
            const auto declared = produces_.find(c.contribution_id);
            for (const auto& produced : results[index].states) {
                const std::string& sid = produced.first;
                if (std::find(declared->second.begin(), declared->second.end(),
                              sid) == declared->second.end())
                    throw Refusal(
                        "combine_undeclared_contribution_output",
                        "contribution_id " + c.contribution_id +
                        " state_id " + sid);
                if (routed_.count(sid))
                    throw Refusal("combine_double_state_write",
                                  "state_id " + sid + " writers " +
                                  routed_[sid] + "," + c.contribution_id);
                routed_[sid] = c.contribution_id;
                store_.apply(sid, produced.second, c.owner_membrane);
                report.routed.push_back(c.contribution_id + "->" + sid);
                ++report.applied;
            }
            for (const auto& entry : results[index].ledger)
                ledger_bytes_.push_back(c.contribution_id + '>' +
                                        entry.canonical_bytes());
        }
        store_.advance_all("accepted");
        return report;
    }

    // Canonical ledger bytes across all windows of this scheduler.
    std::string ledger_digest() const {
        std::vector<std::string> sorted = ledger_bytes_;
        std::sort(sorted.begin(), sorted.end());
        std::string joined;
        for (const auto& row : sorted) joined += row + '\n';
        return digest64(joined);
    }

 private:
    chimera::multibody::ContributionExecutor* executor_ = nullptr;
    std::vector<Contribution> contributions_;
    std::map<std::string, std::vector<std::string>> produces_;
    std::map<std::string, std::string> routed_;
    std::vector<std::string> ledger_bytes_;
    OwnedStateStore& store_;
    std::set<std::string> ids_;      // (uniqueness set)
};

// ---------- S-B: the five generalized-force RHS contributions -----------------

// The approved DESIGN.md S-B seam (coupled_dynamics.hpp rate()), declared:
// five INDEPENDENT contributions combined in the FIXED textual order
//   rhs[i] = tau[i] + gravity[i] - bias[i] + external[i] - damping[i]*v[i]
// with the damping heat ledger accumulating damping[i]*v[i]^2 in the same
// coordinate order. The canonical contribution ids freeze the order; the fold
// below IS that order, bit-identical to the original inline expression.
inline const std::vector<std::string>& sb_contribution_ids() {
    static const std::vector<std::string> ids{
        "sb.a_drive_torque", "sb.b_gravity", "sb.c_bias", "sb.d_external",
        "sb.e_passive_damping"};
    return ids;
}

struct GeneralizedForce {
    std::vector<double> rhs;
    double heat = 0.0;
};

inline GeneralizedForce generalized_force(
    const std::vector<double>& tau, const std::vector<double>& gravity,
    const std::vector<double>& bias, const std::vector<double>& external,
    const std::vector<double>& v, const std::vector<double>& damping,
    chimera::multibody::ContributionExecutor* executor) {
    const std::size_t n = tau.size();
    require_worker_budget(executor ? executor->workers() : 1);
    GeneralizedForce out;
    out.rhs.assign(n, 0.0);
    const bool parallel = executor && executor->workers() > 1;
    if (!parallel) {
        // The serial path: the original statement, byte-for-byte.
        for (std::size_t i = 0; i < n; ++i) {
            out.rhs[i] = tau[i] + gravity[i] - bias[i] + external[i] -
                         damping[i] * v[i];
            out.heat += damping[i] * v[i] * v[i];
        }
        return out;
    }
    // Parallel path (measured independent-config batches only): the five
    // terms compute over the pool into fixed slots; the FOLD is unchanged.
    // Negation is exact and a-b rounds identically to a+(-b), so folding the
    // signed terms in canonical order reproduces the serial expression
    // bit-for-bit. The serial default never executes this branch.
    struct Terms {
        double gravity_term = 0.0, bias_term = 0.0, external_term = 0.0,
               damping_term = 0.0, damping_heat = 0.0;
    };
    std::vector<Terms> terms(n);
    executor->for_each(sb_contribution_ids().size(), [&](std::size_t slot) {
        // One declared contribution per slot (S-B ids, canonical order).
        for (std::size_t i = 0; i < n; ++i) {
            switch (slot) {
                case 1: terms[i].gravity_term = gravity[i]; break;
                case 2: terms[i].bias_term = -bias[i]; break;
                case 3: terms[i].external_term = external[i]; break;
                case 4:
                    terms[i].damping_term = -(damping[i] * v[i]);
                    terms[i].damping_heat = damping[i] * v[i] * v[i];
                    break;
                default: break;  // slot 0: the drive torque, already held in tau
            }
        }
    });
    for (std::size_t i = 0; i < n; ++i) {
        out.rhs[i] = tau[i];                        // sb.a_drive_torque
        out.rhs[i] = out.rhs[i] + terms[i].gravity_term;
        out.rhs[i] = out.rhs[i] + terms[i].bias_term;
        out.rhs[i] = out.rhs[i] + terms[i].external_term;
        out.rhs[i] = out.rhs[i] + terms[i].damping_term;
        out.heat += terms[i].damping_heat;          // canonical i-order ledger
    }
    return out;
}

}  // namespace chimera::combine
