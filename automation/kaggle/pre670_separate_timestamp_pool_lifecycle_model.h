// NFSMW PRE670: separate timestamp-query resource LIFECYCLE MODEL ONLY.
// Pure C++17, no Vulkan headers/functions/objects; no runtime app integration.
// Never equate a timestamp interval to exclusive VS/PS GPU shader time.
#pragma once
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
namespace nfsmw::pre670 {
constexpr bool kDefaultEnabled = false;
constexpr uint32_t kPairsPerSlot = 4;
constexpr uint32_t kQueriesPerSlot = 2 * kPairsPerSlot;
constexpr uint32_t kMaxSlots = 16;
static_assert(kQueriesPerSlot == 8);
enum class SlotState : uint8_t { Free, Recording, Submitted, FencePassed };
enum class FenceResult : uint8_t { Success, NotReady, Error };
struct Capability {
  bool requested = false;
  bool writer_available = false;
  bool reader_available = false;
  bool mock_separate_pool_created = false; // caller-supplied TEST INPUT, not Vulkan
  uint32_t slots = 0;
  uint32_t valid_bits = 0;
  double timestamp_period_ns = 0.0;
};
struct Slot {
  SlotState state = SlotState::Free;
  uint32_t pairs = 0;
};
class MockLifecycle final {
 public:
  bool Setup(const Capability& c) noexcept {
    enabled_ = false; faulted_ = false; slots_ = 0; bits_ = 0; period_ns_ = 0.0;
    for (auto& slot : slot_) slot = {};
    if (!c.requested || !c.writer_available || !c.reader_available ||
        !c.mock_separate_pool_created || c.slots == 0 || c.slots > kMaxSlots ||
        c.valid_bits == 0 || c.valid_bits > 64 ||
        !std::isfinite(c.timestamp_period_ns) || c.timestamp_period_ns <= 0.0)
      return false;
    slots_ = c.slots; bits_ = c.valid_bits; period_ns_ = c.timestamp_period_ns;
    enabled_ = true;
    return true;
  }
  bool Enabled() const noexcept { return enabled_; }
  bool Faulted() const noexcept { return faulted_; }
  uint32_t Slots() const noexcept { return slots_; }
  uint32_t QueryCount() const noexcept { return slots_ * kQueriesPerSlot; }
  // Model caller must assert its REAL vkWaitForFences returned VK_SUCCESS.
  // Merely waiting or observing VK_NOT_READY is NOT sufficient.
  bool BeginRecording(uint32_t slot, bool fence_completion_verified) noexcept {
    if (!ValidSlot(slot) || !fence_completion_verified ||
        slot_[slot].state != SlotState::Free) return false;
    slot_[slot].state = SlotState::Recording;
    slot_[slot].pairs = 0;
    return true;
  }
  // Exact query indices in an independent PROPOSED pool, not the C2 pool.
  bool QueryIndices(uint32_t slot,uint32_t pair,uint32_t& start,uint32_t& end) const noexcept {
    if (!ValidSlot(slot) || slot_[slot].state != SlotState::Recording ||
        pair >= kPairsPerSlot) return false;
    start = slot * kQueriesPerSlot + pair * 2;
    end = start + 1;
    return end < QueryCount();
  }
  bool Submit(uint32_t slot, bool vk_submit_succeeded, uint32_t balanced_pairs) noexcept {
    if (!ValidSlot(slot) || slot_[slot].state != SlotState::Recording ||
        balanced_pairs > kPairsPerSlot) return false;
    if (!vk_submit_succeeded) { FailClosed(); return false; }
    slot_[slot].pairs = balanced_pairs;
    slot_[slot].state = SlotState::Submitted;
    return true;
  }
  // Only a known abandoned, unsubmitted command buffer can be re-used.
  bool AbandonBeforeSubmit(uint32_t slot) noexcept {
    if (!ValidSlot(slot) || slot_[slot].state != SlotState::Recording) return false;
    slot_[slot] = {};
    return true;
  }
  // Caller must pass the actual vkGetFenceStatus/vkWaitForFences result.
  bool Fence(uint32_t slot, FenceResult result) noexcept {
    if (!ValidSlot(slot) || slot_[slot].state != SlotState::Submitted) return false;
    if (result == FenceResult::NotReady) return false;
    if (result == FenceResult::Error) { FailClosed(); return false; }
    slot_[slot].state = SlotState::FencePassed;
    return true;
  }
  // Query read is a separate gate after fence success. Failed read is a
  // diagnostic failure, never license to reset/recycle a pending query.
  bool CompleteReadback(uint32_t slot, bool read_succeeded, uint32_t pairs_read) noexcept {
    if (!ValidSlot(slot) || slot_[slot].state != SlotState::FencePassed ||
        !read_succeeded || slot_[slot].pairs != pairs_read) return false;
    slot_[slot] = {};
    return true;
  }
  SlotState State(uint32_t slot) const noexcept {
    return ValidSlot(slot) ? slot_[slot].state : SlotState::Submitted;
  }
  // Diagnostic numeric helper; not device execution or proof of shader timing.
  bool MockDeltaNs(uint64_t start, uint64_t end, double& delta_ns) const noexcept {
    if (!enabled_) return false;
    const uint64_t mask = bits_==64 ? std::numeric_limits<uint64_t>::max() :
      ((uint64_t(1) << bits_)-1u);
    const uint64_t ticks = (end-start) & mask;
    const double candidate = static_cast<double>(ticks)*period_ns_;
    if (!std::isfinite(candidate)) return false;
    delta_ns = candidate;
    return true;
  }
 private:
  bool ValidSlot(uint32_t s) const noexcept { return enabled_ && s < slots_; }
  void FailClosed() noexcept {
    enabled_ = false; faulted_ = true; slots_ = 0; bits_ = 0; period_ns_ = 0.0;
    for (auto& s : slot_) s = {};
  }
  std::array<Slot,kMaxSlots> slot_{};
  uint32_t slots_ = 0, bits_ = 0;
  double period_ns_ = 0.0;
  bool enabled_ = false, faulted_ = false;
};
} // namespace nfsmw::pre670
