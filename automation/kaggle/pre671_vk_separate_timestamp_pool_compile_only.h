// PRE671 experimental, compile-only native Vulkan timestamp adapter.
// NO callsite in live render path; NO VkQueryPool object at runtime by default.
// This does NOT measure the exclusive execution time of VS62/PS58.
// A future device experiment must separately verify supported pipeline stages,
// timestampValidBits, timestampPeriod, driver behavior and overhead.
#pragma once
#include <vulkan/vulkan.h>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
namespace nfsmw::pre671 {
static constexpr bool kDefaultEnabled = false;
static constexpr uint32_t kQueriesPerSlot = 8;
static constexpr uint32_t kMaxPairsPerSlot = 4;
static constexpr uint32_t kMaxSlots = 16;
static_assert(kQueriesPerSlot == 2 * kMaxPairsPerSlot);
enum class State : uint8_t { Free, Recording, Submitted, Complete };
struct Functions {
  PFN_vkCreateQueryPool create = nullptr;
  PFN_vkDestroyQueryPool destroy = nullptr;
  PFN_vkCmdResetQueryPool reset = nullptr;
  PFN_vkCmdWriteTimestamp write = nullptr;
  PFN_vkGetQueryPoolResults results = nullptr;
  PFN_vkDeviceWaitIdle device_wait_idle = nullptr;
};
struct Samples {
  std::array<double, kMaxPairsPerSlot> intervals_ns{};
  uint32_t count = 0;
  // Intervals cover timestamp pipeline boundaries; no shader exclusivity claim.
};
struct Slot {
  State state = State::Free;
  bool pair_open = false;
  uint32_t pairs = 0;
};
class Adapter final {
 public:
  Adapter() = default;
  Adapter(const Adapter&) = delete;
  Adapter& operator=(const Adapter&) = delete;
  // Can allocate real VkQueryPool ONLY if caller explicitly requests it.
  // There is no integration that invokes this in the V51 draw path.
  bool Create(VkDevice device, const Functions& functions, bool request_enable,
              uint32_t slots, uint32_t queue_family_timestamp_valid_bits,
              float device_timestamp_period_ns) noexcept {
    if (pool_ != VK_NULL_HANDLE || device_ != VK_NULL_HANDLE) return false;
    if (!request_enable || !device ||
        slots == 0 || slots > kMaxSlots ||
        queue_family_timestamp_valid_bits == 0 ||
        queue_family_timestamp_valid_bits > 64 ||
        !std::isfinite(device_timestamp_period_ns) ||
        device_timestamp_period_ns <= 0.0f ||
        !functions.create || !functions.destroy || !functions.reset ||
        !functions.write || !functions.results || !functions.device_wait_idle)
      return false;
    VkQueryPoolCreateInfo info{};
    info.sType = VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO;
    info.queryType = VK_QUERY_TYPE_TIMESTAMP;
    info.queryCount = slots * kQueriesPerSlot;
    VkQueryPool candidate = VK_NULL_HANDLE;
    const VkResult result = functions.create(device, &info, nullptr, &candidate);
    if (result != VK_SUCCESS || candidate == VK_NULL_HANDLE) return false;
    functions_ = functions;
    device_ = device;
    pool_ = candidate;
    slots_ = slots;
    bits_ = queue_family_timestamp_valid_bits;
    period_ns_ = device_timestamp_period_ns;
    for (auto& s : state_) s = Slot{};
    enabled_ = true;
    return true;
  }
  bool Enabled() const noexcept { return enabled_ && pool_ != VK_NULL_HANDLE; }
  uint32_t QueryCount() const noexcept { return slots_ * kQueriesPerSlot; }
  // Call only OUTSIDE render pass and AFTER VK_SUCCESS on the previous
  // slot's fence. vkCmdResetQueryPool is recorded in the new command buffer.
  bool BeginSlot(uint32_t slot, VkCommandBuffer cmd,
                 VkResult actual_previous_fence_result) noexcept {
    if (!Valid(slot) || cmd == VK_NULL_HANDLE ||
        actual_previous_fence_result != VK_SUCCESS ||
        state_[slot].state != State::Free) return false;
    const uint32_t base = slot * kQueriesPerSlot;
    functions_.reset(cmd, pool_, base, kQueriesPerSlot);
    state_[slot] = Slot{State::Recording, false, 0};
    return true;
  }
  // Call within the actual graphics render pass at target draw-group start.
  bool BeginPair(uint32_t slot, VkCommandBuffer cmd) noexcept {
    if (!Valid(slot) || cmd == VK_NULL_HANDLE) return false;
    Slot& s = state_[slot];
    if (s.state != State::Recording || s.pair_open ||
        s.pairs >= kMaxPairsPerSlot) return false;
    const uint32_t index = slot * kQueriesPerSlot + s.pairs * 2;
    functions_.write(cmd, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, pool_, index);
    s.pair_open = true;
    return true;
  }
  // Call before leaving the pass or switching away from the sampled pair.
  bool EndPair(uint32_t slot, VkCommandBuffer cmd) noexcept {
    if (!Valid(slot) || cmd == VK_NULL_HANDLE) return false;
    Slot& s = state_[slot];
    if (s.state != State::Recording || !s.pair_open) return false;
    const uint32_t index = slot * kQueriesPerSlot + s.pairs * 2 + 1;
    functions_.write(cmd, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, pool_, index);
    s.pair_open = false;
    ++s.pairs;
    return true;
  }
  // External caller must pass the REAL result of vkQueueSubmit.
  bool Submitted(uint32_t slot, VkResult actual_submit_result) noexcept {
    if (!Valid(slot)) return false;
    Slot& s = state_[slot];
    if (s.state != State::Recording || s.pair_open) return false;
    if (actual_submit_result != VK_SUCCESS) { enabled_ = false; return false; }
    s.state = State::Submitted;
    return true;
  }
  // vkGetQueryPoolResults: no WAIT_BIT, read only after real fence VK_SUCCESS;
  // require both availability words. This call never blocks for a query.
  bool ReadAfterFence(uint32_t slot, VkResult actual_fence_result,
                      Samples& output) noexcept {
    if (!Valid(slot) || actual_fence_result != VK_SUCCESS ||
        state_[slot].state != State::Submitted) return false;
    Slot& s = state_[slot];
    if (!s.pairs) { s = Slot{}; output = {}; return true; }
    std::array<uint64_t, 4 * kMaxPairsPerSlot> values{};
    const uint32_t query_count = s.pairs * 2;
    const VkResult result = functions_.results(
      device_, pool_, slot * kQueriesPerSlot, query_count,
      size_t(query_count) * 2 * sizeof(uint64_t), values.data(),
      2 * sizeof(uint64_t),
      VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WITH_AVAILABILITY_BIT);
    if (result == VK_NOT_READY) return false;
    if (result != VK_SUCCESS) { enabled_ = false; return false; }
    Samples candidate{};
    candidate.count = s.pairs;
    const uint64_t mask = bits_ == 64
      ? std::numeric_limits<uint64_t>::max()
      : ((uint64_t(1) << bits_) - 1);
    for (uint32_t i = 0; i < s.pairs; ++i) {
      const uint32_t at = i * 4;
      if (values[at + 1] == 0 || values[at + 3] == 0) return false;
      const uint64_t ticks = (values[at + 2] - values[at]) & mask;
      const double interval = double(ticks) * double(period_ns_);
      if (!std::isfinite(interval)) { enabled_ = false; return false; }
      candidate.intervals_ns[i] = interval;
    }
    output = candidate;
    s = Slot{}; // slot may now be reused AFTER a new successful fence gate
    return true;
  }
  // Caller must discard unsubmitted command buffers, stop submitting,
  // then permit a deliberate blocking device-idle wait before destroying.
  // Never destroy a pool on submit/fence failure before synchronization.
  bool DestroyAfterDeviceIdle(bool unsubmitted_recordings_discarded) noexcept {
    if (!unsubmitted_recordings_discarded ||
        device_ == VK_NULL_HANDLE || pool_ == VK_NULL_HANDLE ||
        !functions_.device_wait_idle) return false;
    if (functions_.device_wait_idle(device_) != VK_SUCCESS) return false;
    functions_.destroy(device_, pool_, nullptr);
    pool_ = VK_NULL_HANDLE; device_ = VK_NULL_HANDLE;
    functions_ = Functions{}; slots_ = 0; bits_ = 0; period_ns_ = 0;
    enabled_ = false;
    for (auto& s : state_) s = Slot{};
    return true;
  }
 private:
  bool Valid(uint32_t slot) const noexcept {
    return Enabled() && slot < slots_;
  }
  Functions functions_{};
  VkDevice device_ = VK_NULL_HANDLE;
  VkQueryPool pool_ = VK_NULL_HANDLE;
  uint32_t slots_ = 0, bits_ = 0;
  float period_ns_ = 0;
  bool enabled_ = false;
  std::array<Slot, kMaxSlots> state_{};
};
} // namespace nfsmw::pre671
