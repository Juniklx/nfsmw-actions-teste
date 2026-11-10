// PRE664 — host-only model of bounded contiguous-burst GPU timestamp sampling.
// No Vulkan calls, no device integration, no APK and no change to rendering.
#pragma once
#include <cstdint>
#include <limits>

namespace nfsmw::pre664 {
constexpr bool kDefaultEnabled = false;
constexpr uint32_t kMaxPairsPerSlot = 4;
constexpr uint32_t kQueriesPerSlot = 2 * kMaxPairsPerSlot;
static_assert(kQueriesPerSlot == 8, "PRE664 requires a separate eight-query budget");

enum class Action : uint8_t { None, Begin, End };
struct Decision {
  Action action = Action::None;
  uint32_t query = 0;
};
struct Draw {
  uint32_t pass = 0;
  uint32_t vs = 0;
  uint32_t ps = 0;
  bool deferred_sky = false;
};

class BoundedBurstModel final {
 public:
  // Caller must externally verify fence completion before reusing slot queries.
  // This boolean is an API contract, NOT a Vulkan fence implementation.
  bool BeginSlot(bool requested, bool prior_fence_completed, bool selected_slot) noexcept {
    enabled_ = false;
    if (!prior_fence_completed) {
      unsafe_reuse_rejected_ = SaturatingAdd(unsafe_reuse_rejected_);
      return false;
    }
    pair_count_ = completed_count_ = discarded_count_ = 0;
    active_ = false;
    skipping_target_ = false;
    enabled_ = requested && selected_slot;
    return enabled_;
  }

  Decision OnDraw(const Draw &d) noexcept {
    if (!enabled_) return {};
    // Only actual native Vulkan emissions may enter OnDraw. Sky deferred
    // for later execution is deliberately not considered in this model.
    const bool target = d.pass == 2 && d.vs == 62 && d.ps == 58 && !d.deferred_sky;
    if (active_) {
      if (target) return {};
      active_ = false;
      skipping_target_ = false;
      ++completed_count_;
      return {Action::End, (pair_count_ - 1u) * 2u + 1u};
    }
    if (!target) {
      skipping_target_ = false;
      return {};
    }
    if (pair_count_ >= kMaxPairsPerSlot) {
      if (!skipping_target_) discarded_count_ = SaturatingAdd(discarded_count_);
      skipping_target_ = true;
      return {};
    }
    const uint32_t query = pair_count_ * 2u;
    ++pair_count_;
    active_ = true;
    return {Action::Begin, query};
  }

  Decision EndCommandBuffer() noexcept {
    if (!enabled_ || !active_) return {};
    active_ = false;
    ++completed_count_;
    return {Action::End, (pair_count_ - 1u) * 2u + 1u};
  }

  uint32_t StartedPairs() const noexcept { return pair_count_; }
  uint32_t CompletedPairs() const noexcept { return completed_count_; }
  uint32_t SkippedBursts() const noexcept { return discarded_count_; }
  uint32_t UnsafeReuseRejects() const noexcept { return unsafe_reuse_rejected_; }
  bool Enabled() const noexcept { return enabled_; }

 private:
  static uint32_t SaturatingAdd(uint32_t n) noexcept {
    return n == std::numeric_limits<uint32_t>::max() ? n : n + 1;
  }
  uint32_t pair_count_ = 0;
  uint32_t completed_count_ = 0;
  uint32_t discarded_count_ = 0;
  uint32_t unsafe_reuse_rejected_ = 0;
  bool active_ = false;
  bool enabled_ = false;
  bool skipping_target_ = false;
};
} // namespace nfsmw::pre664
