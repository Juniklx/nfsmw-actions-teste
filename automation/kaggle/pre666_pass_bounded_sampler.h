// PRE666: revised HOST-ONLY state machine for timestamp burst boundary plans.
// Explicit render-pass boundary; called BEFORE a successful native Vulkan draw.
// No Vulkan API calls. No app integration, no APK, no real GPU measurements.
#pragma once
#include <cstdint>
#include <limits>
namespace nfsmw::pre666 {
constexpr bool kDefaultEnabled = false;
constexpr uint32_t kMaxBurstsPerSlot = 4;
constexpr uint32_t kQueriesPerSlot = kMaxBurstsPerSlot * 2;
static_assert(kQueriesPerSlot == 8);
enum class Action : uint8_t { None, Begin, End };
struct Decision { Action action = Action::None; uint32_t query_local = 0; };
struct Draw { uint32_t category=0, vs=0, ps=0; bool deferred_sky=false; };

// Caller owns all real GPU and device objects. Fence state is an input assumption;
// this class NEVER checks a Vulkan fence, nor records any Vulkan command.
class PassBoundedModel final {
 public:
  bool BeginWorkSlot(bool requested, bool previous_fence_completed, bool selected) noexcept {
    enabled_=false;
    if (!previous_fence_completed) { unsafe_reuse_rejects_=Saturating(unsafe_reuse_rejects_); return false; }
    if (open_) { recording_abort_count_=Saturating(recording_abort_count_); }
    open_=false; skipped_burst_=false; starts_=ends_=skipped_=0;
    enabled_=requested && selected;
    return enabled_;
  }

  // Must be called just before the corresponding real vkCmdDraw[Indexed].
  // If Action::End is produced, timestamp would be recorded BEFORE that other
  // draw, so the previously sampled burst cannot include its GPU commands.
  Decision BeforeDraw(const Draw& draw) noexcept {
    if (!enabled_) return {};
    const bool is_target=draw.category==2 && draw.vs==62 && draw.ps==58 && !draw.deferred_sky;
    if (open_) {
      if (is_target) return {};
      open_=false; ++ends_; skipped_burst_=false;
      return {Action::End, (starts_-1u)*2u+1u};
    }
    if (!is_target) {skipped_burst_=false; return {};}
    if (starts_>=kMaxBurstsPerSlot) {
      if (!skipped_burst_) skipped_=Saturating(skipped_);
      skipped_burst_=true;
      return {};
    }
    const uint32_t query=starts_*2u;
    ++starts_; open_=true;
    return {Action::Begin,query};
  }
  // Must happen BEFORE the actual vkCmdEndRenderPass. Failure to signal it
  // would incorrectly merge two separate passes of the same VS/PS category.
  Decision BeforeEndRenderPass() noexcept { return Close(); }
  // Final defense before vkEndCommandBuffer, for exceptional paths.
  Decision BeforeEndCommandBuffer() noexcept { return Close(); }
  void AbandonRecording() noexcept {
    if (open_) recording_abort_count_=Saturating(recording_abort_count_);
    open_=false; enabled_=false; starts_=ends_=skipped_=0; skipped_burst_=false;
  }
  bool Enabled() const noexcept { return enabled_; }
  uint32_t Starts() const noexcept { return starts_; }
  uint32_t Ends() const noexcept { return ends_; }
  uint32_t SkippedBursts() const noexcept { return skipped_; }
  uint32_t UnsafeReuseRejects() const noexcept { return unsafe_reuse_rejects_; }
  uint32_t RecordingAborts() const noexcept { return recording_abort_count_; }
  bool Balanced() const noexcept { return !open_ && starts_==ends_; }
 private:
  static uint32_t Saturating(uint32_t x) noexcept {
    return x==std::numeric_limits<uint32_t>::max() ? x : x+1u;
  }
  Decision Close() noexcept {
    if (!enabled_ || !open_) return {};
    open_=false; ++ends_; skipped_burst_=false;
    return {Action::End,(starts_-1u)*2u+1u};
  }
  uint32_t starts_=0, ends_=0, skipped_=0, unsafe_reuse_rejects_=0, recording_abort_count_=0;
  bool enabled_=false,open_=false,skipped_burst_=false;
};
} // namespace nfsmw::pre666
