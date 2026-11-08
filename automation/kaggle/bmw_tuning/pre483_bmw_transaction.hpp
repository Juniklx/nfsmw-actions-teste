#pragma once
// PRE483: pure host-only transaction simulation for future BMW tuning.
// No filesystem, Android, hooks, game guest memory, save files, or APK.
// A validated synthetic transaction does NOT permit real game integration.
#include "pre479_bmw_guard.hpp"
#include <array>
#include <cstdint>
#include <string_view>

namespace nfsmw_bmw_tuning {

constexpr std::string_view kDisposableSaveLabel = "DISPOSABLE_TEST_ONLY";
constexpr std::size_t kCategoryCount=7;

struct SyntheticPackage final {
  std::array<std::int32_t,kCategoryCount> part{};
  std::uint32_t junkman=0;
};
struct SyntheticState final {
  SyntheticPackage installed{};
  std::int64_t credits=0;
  bool applied_to_physics=false;
  bool preview_visible=false;
};
constexpr bool SameState(const SyntheticState &a,const SyntheticState &b) noexcept {
  if (a.credits!=b.credits || a.applied_to_physics!=b.applied_to_physics ||
      a.preview_visible!=b.preview_visible ||
      a.installed.junkman!=b.installed.junkman) return false;
  for (std::size_t i=0;i<kCategoryCount;i++)
    if (a.installed.part[i]!=b.installed.part[i]) return false;
  return true;
}
enum class TransactionStatus:std::uint8_t {
  SyntheticAccepted=0,
  RuntimeDisabled,
  GuardRejected,
  NotDisposableSave,
  NoMatchingFEPartInfo,
  NegativeCost,
  InsufficientCredits,
  InvalidPriorLevel,
  PhysicsApplyFailed,
  SerializationRoundtripFailed
};
struct Proposal final {
  Request gated_request{};
  bool matching_FEPartInfo_exists=false;
  std::int64_t cost=0;
  std::string_view save_label{};
  // Only dependency injection for offline tests: actual physics/save
  // implementations are NEVER invoked from this module.
  bool simulated_physics_accepts=false;
  bool simulated_serialization_roundtrip_accepts=false;
};
struct DryRunResult final {
  TransactionStatus status=TransactionStatus::RuntimeDisabled;
  SyntheticState state{};
  Reason gate_reason=Reason::RuntimeNotIntegrated;
};
// The input is const: the user's save and current state cannot be changed.
// Snapshot and commit happen solely in the returned local C++ value.
// Failed operations return a byte-for-byte logically equivalent snapshot.
inline DryRunResult SimulateOffline(const SyntheticState &original,
                                   const Proposal &proposal) noexcept {
  DryRunResult result{};
  result.state=original;
  result.gate_reason=EvaluateSyntheticContract(proposal.gated_request);
  if (result.gate_reason!=Reason::AllowedBySyntheticContractOnly) {
    result.status=TransactionStatus::GuardRejected;
    return result;
  }
  if (proposal.save_label!=kDisposableSaveLabel ||
      !proposal.gated_request.proof.target_is_disposable_save) {
    result.status=TransactionStatus::NotDisposableSave;
    return result;
  }
  if (!proposal.matching_FEPartInfo_exists) {
    result.status=TransactionStatus::NoMatchingFEPartInfo;
    return result;
  }
  if (proposal.cost<0) {
    result.status=TransactionStatus::NegativeCost;
    return result;
  }
  if (original.credits<proposal.cost) {
    result.status=TransactionStatus::InsufficientCredits;
    return result;
  }
  const auto slot=static_cast<std::size_t>(proposal.gated_request.category);
  if (slot>=kCategoryCount) {
    result.status=TransactionStatus::GuardRejected;
    return result;
  }
  const auto prev=original.installed.part[slot];
  if (prev<0 || prev>CategoryMax(proposal.gated_request.category)) {
    result.status=TransactionStatus::InvalidPriorLevel;
    return result;
  }
  SyntheticState candidate=original; // local-only transaction snapshot
  candidate.installed.part[slot]=proposal.gated_request.requested_level;
  candidate.credits-=proposal.cost;
  if (!proposal.simulated_physics_accepts) {
    result.status=TransactionStatus::PhysicsApplyFailed;
    return result;
  }
  candidate.applied_to_physics=true;
  if (!proposal.simulated_serialization_roundtrip_accepts) {
    result.status=TransactionStatus::SerializationRoundtripFailed;
    return result;
  }
  candidate.preview_visible=true;
  result.state=candidate;
  result.status=TransactionStatus::SyntheticAccepted;
  return result;
}

inline DryRunResult TryRealGameOperation(const SyntheticState &original,
                                        const Proposal &proposal) noexcept {
  // Hard OFF: the PRE479 guard specifically denies real integration
  // regardless of synthetic evidence or the state of feature flags.
  const auto gate=EvaluateAnyRealGameRequest(proposal.gated_request);
  (void)gate;
  return {TransactionStatus::RuntimeDisabled,original,
          Reason::RuntimeNotIntegrated};
}

} // namespace nfsmw_bmw_tuning
