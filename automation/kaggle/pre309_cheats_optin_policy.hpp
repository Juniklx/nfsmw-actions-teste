#pragma once
// PRE309: opt-in, host-only cheat decision policy. NOT attached to game.
// Untrusted guest memory is never dereferenced here, and no save APIs exist.
#include <atomic>
#include <cstdint>
#include <cmath>
#include <limits>

namespace nfsmw_pre309 {

enum class Feature : std::uint8_t { Nitro, Speedbreaker, Money };
struct Switches {
  std::atomic<bool> nitro{false};
  std::atomic<bool> speedbreaker{false};
  std::atomic<bool> money{false};
  void reset() noexcept {
    nitro.store(false, std::memory_order_relaxed);
    speedbreaker.store(false, std::memory_order_relaxed);
    money.store(false, std::memory_order_relaxed);
  }
  bool enabled(Feature f) const noexcept {
    switch (f) {
      case Feature::Nitro: return nitro.load(std::memory_order_relaxed);
      case Feature::Speedbreaker: return speedbreaker.load(std::memory_order_relaxed);
      case Feature::Money: return money.load(std::memory_order_relaxed);
    }
    return false;
  }
};
// A permission gate is *not* a runtime finding. Production wiring must verify
// the actual guest function semantics and user opt-in before passing true.
struct Gate {
  bool verified_target{false};
  bool verified_owner{false};
  bool safe_session{false};
  bool explicit_user_opt_in{false};
};
inline bool permitted(const Switches& s, Feature f, Gate g) noexcept {
  return s.enabled(f) && g.verified_target && g.verified_owner
       && g.safe_session && g.explicit_user_opt_in;
}
// This is a pure policy, not a guest write. "full" comes from verified
// runtime semantics, never from a fixed game-wide 1.0 assumption.
inline float meter_value(const Switches& s, Feature f, Gate gate,
                         float original, float verified_full) noexcept {
  if (f==Feature::Money || !permitted(s,f,gate)) return original;
  if (!std::isfinite(original) || !std::isfinite(verified_full)
       || original < 0.0f || verified_full <= 0.0f
       || original > verified_full) return original;
  return verified_full;
}
// Money is never changed until a real account/credit dataflow has been
// validated. This pass-through is intentionally not a working money cheat.
inline std::uint32_t money_value(const Switches&, Gate,
                                 std::uint32_t original) noexcept {
  return original;
}
} // namespace nfsmw_pre309
