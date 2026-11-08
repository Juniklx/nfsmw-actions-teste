#include "pre483_bmw_transaction.hpp"
#include <cassert>
#include <cstdio>
using namespace nfsmw_bmw_tuning;
static_assert(!kRuntimeIntegrationProven);

Proposal GoodProposal() {
  Proposal p{};
  p.gated_request.observed_car_type=kTargetCarTypeFromPRE455;
  p.gated_request.observed_pvehicle_hash=kTargetPVehicleHashFromPRE474;
  p.gated_request.category=Category::Engine;
  p.gated_request.requested_level=1;
  p.gated_request.feature_enabled=true;
  auto &proof=p.gated_request.proof;
  proof.catalog_real_and_matched_to_BMW=true;
  proof.complete_BMW_performance_profile=true;
  proof.frontend_title_and_price_verified=true;
  proof.target_is_disposable_save=true;
  proof.save_roundtrip_verified=true;
  proof.runtime_physics_and_other_cars_verified=true;
  p.matching_FEPartInfo_exists=true;
  p.cost=100;
  p.save_label=kDisposableSaveLabel;
  p.simulated_physics_accepts=true;
  p.simulated_serialization_roundtrip_accepts=true;
  return p;
}
int main() {
  int checked=0;
  auto check=[&](bool b) {assert(b);checked++;};
  SyntheticState original{};
  original.installed.part[static_cast<int>(Category::Engine)]=0;
  original.installed.part[static_cast<int>(Category::Nos)]=3;
  original.installed.junkman=0x12;
  original.credits=1000;
  original.preview_visible=true;
  const auto good=GoodProposal();
  auto result=SimulateOffline(original,good);
  check(result.status==TransactionStatus::SyntheticAccepted);
  check(result.state.credits==900);
  check(result.state.installed.part[4]==1);
  check(result.state.installed.part[6]==3); // Nitro remains untouched
  check(result.state.installed.junkman==0x12);
  check(SameState(original,SyntheticState{original})); // caller input unchanged
  check(TryRealGameOperation(original,good).status==TransactionStatus::RuntimeDisabled);
  check(SameState(TryRealGameOperation(original,good).state,original));
  auto assert_rejected=[&](const Proposal &p,TransactionStatus why) {
    const auto r=SimulateOffline(original,p);
    assert(r.status==why);
    assert(SameState(r.state,original));
    checked+=2;
  };
  auto p=good;p.gated_request.feature_enabled=false;
  assert_rejected(p,TransactionStatus::GuardRejected);
  p=good;p.gated_request.observed_car_type=74;
  assert_rejected(p,TransactionStatus::GuardRejected);
  p=good;p.gated_request.observed_pvehicle_hash=0x39DAE0F8u;
  assert_rejected(p,TransactionStatus::GuardRejected);
  p=good;p.gated_request.category=Category::Nos;
  assert_rejected(p,TransactionStatus::GuardRejected);
  p=good;p.gated_request.requested_level=5;
  assert_rejected(p,TransactionStatus::GuardRejected);
  p=good;p.gated_request.proof.complete_BMW_performance_profile=false;
  assert_rejected(p,TransactionStatus::GuardRejected);
  p=good;p.save_label="MARCEK";
  assert_rejected(p,TransactionStatus::NotDisposableSave);
  p=good;p.save_label="";
  assert_rejected(p,TransactionStatus::NotDisposableSave);
  p=good;p.matching_FEPartInfo_exists=false;
  assert_rejected(p,TransactionStatus::NoMatchingFEPartInfo);
  p=good;p.cost=-1;
  assert_rejected(p,TransactionStatus::NegativeCost);
  p=good;p.cost=1001;
  assert_rejected(p,TransactionStatus::InsufficientCredits);
  p=good;p.simulated_physics_accepts=false;
  assert_rejected(p,TransactionStatus::PhysicsApplyFailed);
  p=good;p.simulated_serialization_roundtrip_accepts=false;
  assert_rejected(p,TransactionStatus::SerializationRoundtripFailed);
  p=good;p.gated_request.proof.save_roundtrip_verified=false;
  assert_rejected(p,TransactionStatus::GuardRejected);
  p=good;p.gated_request.proof.frontend_title_and_price_verified=false;
  assert_rejected(p,TransactionStatus::GuardRejected);
  p=good;p.gated_request.proof.runtime_physics_and_other_cars_verified=false;
  assert_rejected(p,TransactionStatus::GuardRejected);
  p=good;p.cost=0; // zero may be valid only when real FE record was found
  result=SimulateOffline(original,p);
  check(result.status==TransactionStatus::SyntheticAccepted);
  check(result.state.credits==1000);
  SyntheticState bad=original;bad.installed.part[4]=99;
  result=SimulateOffline(bad,good);
  check(result.status==TransactionStatus::InvalidPriorLevel);
  check(SameState(result.state,bad));
  std::printf("PRE483_CPP_CHECKS_PASSED=%d\n",checked);
  std::puts("PRE483_RUNTIME_ENABLED=0");
  std::puts("PRE483_REAL_SAVE_READ_OR_WRITE=0");
  return checked==44?0:1;
}
