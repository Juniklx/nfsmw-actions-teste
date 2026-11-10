// PRE672: fail-closed capability / command boundary MODEL for a potential
// dedicated Vulkan timestamp query pool. C++17 HOST ONLY, no Vulkan calls.
// No code from this header is called by the V51 runtime; no APK or GPU timing.
#pragma once
#include <array>
#include <cmath>
#include <cstdint>
namespace nfsmw::pre672 {
constexpr bool kDefaultEnabled = false;
constexpr uint32_t kPairsPerSlot = 4;
constexpr uint32_t kQueriesPerSlot = 2 * kPairsPerSlot;
constexpr uint32_t kMaxSlots = 16;
enum class VkFenceOutcome : uint8_t { Success, NotReady, Error };
enum class VkSubmitOutcome : uint8_t { Success, Error };
enum class QueryOutcome : uint8_t { Success, NotReady, Error };
enum class SlotPhase : uint8_t { Free, Recording, Submitted };
struct Capability {
  bool explicit_diagnostic_request = false;
  bool graphics_queue = false;
  bool timestamp_compute_and_graphics = false;
  uint32_t timestamp_valid_bits = 0;
  double timestamp_period_ns = 0.0;
  bool pfns_present = false;
  bool subpass_multiview_status_known = false;
  uint32_t view_mask = 0;
  bool per_tile_mode_status_known = false;
  bool per_tile_mode_active = true; // Unknown defaults to DENY.
  bool stages_support_checked = false;
  bool stages_supported = false;
  uint32_t command_slots = 0;
};
inline bool Supported(const Capability& c) noexcept {
  return c.explicit_diagnostic_request && c.graphics_queue &&
    c.timestamp_compute_and_graphics && c.pfns_present &&
    c.timestamp_valid_bits >= 1 && c.timestamp_valid_bits <= 64 &&
    std::isfinite(c.timestamp_period_ns) && c.timestamp_period_ns > 0.0 &&
    c.subpass_multiview_status_known && c.view_mask == 0 &&
    c.per_tile_mode_status_known && !c.per_tile_mode_active &&
    c.stages_support_checked && c.stages_supported &&
    c.command_slots > 0 && c.command_slots <= kMaxSlots;
}
struct Slot {
  SlotPhase phase = SlotPhase::Free;
  bool pair_open = false;
  uint32_t pairs = 0;
};
class GuardedLifecycle final {
 public:
  GuardedLifecycle() = default;
  GuardedLifecycle(const GuardedLifecycle&) = delete;
  GuardedLifecycle& operator=(const GuardedLifecycle&) = delete;
  bool Configure(const Capability& c) noexcept {
    if (enabled_ || !Supported(c)) return false;
    slots_ = c.command_slots;
    for (auto& s : slot_) s = Slot{};
    faulted_ = false;
    enabled_ = true;
    return true;
  }
  bool Enabled() const noexcept { return enabled_; }
  bool Faulted() const noexcept { return faulted_; }
  uint32_t QueryCount() const noexcept { return slots_ * kQueriesPerSlot; }
  // reset must be recorded outside the scene render pass; prior real fence
  // must have succeeded; "NotReady" and "Error" MUST NOT be treated as done.
  bool BeginSlot(uint32_t id, bool outside_render_pass,
                 VkFenceOutcome previous_fence) noexcept {
    if (!Valid(id) || !outside_render_pass ||
        slot_[id].phase != SlotPhase::Free) return false;
    if (previous_fence == VkFenceOutcome::Error) { Fail(); return false; }
    if (previous_fence != VkFenceOutcome::Success) return false;
    slot_[id] = Slot{SlotPhase::Recording, false, 0};
    return true;
  }
  // timestamps may be sampled only while known scene render pass is active;
  // no deferred sky mode and no dynamic switch away from shader pair.
  bool BeginPair(uint32_t id, bool scene_renderpass_active,
                 bool is_deferred_sky) noexcept {
    if (!Valid(id) || !scene_renderpass_active || is_deferred_sky) return false;
    auto& s=slot_[id];
    if (s.phase != SlotPhase::Recording || s.pair_open ||
        s.pairs >= kPairsPerSlot) return false;
    s.pair_open=true;
    return true;
  }
  bool EndPair(uint32_t id, bool scene_renderpass_active) noexcept {
    if (!Valid(id) || !scene_renderpass_active) return false;
    auto& s=slot_[id];
    if (s.phase != SlotPhase::Recording || !s.pair_open) return false;
    s.pair_open=false;
    ++s.pairs;
    return true;
  }
  // Before vkCmdEndRenderPass and vkEndCommandBuffer, unbalanced groups
  // cause a hard failure; caller must not record half a timestamp pair.
  bool ReadyToEndRenderPass(uint32_t id) const noexcept {
    return Valid(id) && slot_[id].phase == SlotPhase::Recording &&
      !slot_[id].pair_open;
  }
  bool ReadyToEndCommandBuffer(uint32_t id) const noexcept {
    return ReadyToEndRenderPass(id);
  }
  bool Submitted(uint32_t id, VkSubmitOutcome result) noexcept {
    if (!Valid(id) || !ReadyToEndCommandBuffer(id)) return false;
    if (result!=VkSubmitOutcome::Success) { Fail(); return false; }
    slot_[id].phase = SlotPhase::Submitted;
    return true;
  }
  // Query results must be read after real fence success and explicit
  // availability for *every* timestamp. No VK_QUERY_RESULT_WAIT_BIT.
  bool Reclaim(uint32_t id, VkFenceOutcome fence, QueryOutcome query,
               bool all_timestamp_values_available) noexcept {
    if (!Valid(id) || slot_[id].phase != SlotPhase::Submitted) return false;
    if (fence == VkFenceOutcome::Error) { Fail(); return false; }
    if (fence != VkFenceOutcome::Success) return false;
    if (query == QueryOutcome::Error) { Fail(); return false; }
    if (query == QueryOutcome::NotReady ||
        !all_timestamp_values_available) return false;
    slot_[id] = Slot{};
    return true;
  }
  bool QueryPair(uint32_t id,uint32_t pair,
                 uint32_t& first,uint32_t& last) const noexcept {
    if (!Valid(id) || slot_[id].phase!=SlotPhase::Recording ||
        pair >= kPairsPerSlot) return false;
    first = id*kQueriesPerSlot + pair*2;
    last = first+1;
    return last < QueryCount();
  }
 private:
  bool Valid(uint32_t id) const noexcept { return enabled_ && id < slots_; }
  void Fail() noexcept { enabled_=false;faulted_=true; }
  uint32_t slots_ = 0;
  bool enabled_ = false, faulted_ = false;
  std::array<Slot,kMaxSlots> slot_{};
};
} // namespace nfsmw::pre672
