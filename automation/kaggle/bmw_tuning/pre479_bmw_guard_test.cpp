// PRE479 host-only tests. These tests create no games, saves or APK.
#include "pre479_bmw_guard.hpp"
#include <cassert>
#include <cstdio>
using namespace nfsmw_bmw_tuning;

constexpr Request AllSyntheticGatesSatisfied() {
  Request r{};
  r.observed_car_type = kTargetCarTypeFromPRE455;
  r.observed_pvehicle_hash = kTargetPVehicleHashFromPRE474;
  r.category = Category::Engine;
  r.requested_level = 1;
  r.feature_enabled = true;
  r.proof.catalog_real_and_matched_to_BMW = true;
  r.proof.complete_BMW_performance_profile = true;
  r.proof.frontend_title_and_price_verified = true;
  r.proof.target_is_disposable_save = true;
  r.proof.save_roundtrip_verified = true;
  r.proof.runtime_physics_and_other_cars_verified = true;
  return r;
}

static_assert(!kRuntimeIntegrationProven);
static_assert(CategoryMax(Category::Nos) == 0);
static_assert(CategoryMax(Category::Engine) == 4);
static_assert(CategoryMax(Category::Chassis) == 3);
static_assert(EvaluateSyntheticContract(AllSyntheticGatesSatisfied())
              == Reason::AllowedBySyntheticContractOnly);
static_assert(EvaluateAnyRealGameRequest(AllSyntheticGatesSatisfied())
              == Reason::RuntimeNotIntegrated);
static_assert(EvaluateSyntheticContract(Request{}) == Reason::FeatureOff);

int main() {
  int tests_passed = 0;
  auto check=[&tests_passed](bool condition) {
    assert(condition);
    ++tests_passed;
  };
  const auto ok=AllSyntheticGatesSatisfied();
  check(EvaluateAnyRealGameRequest(ok)==Reason::RuntimeNotIntegrated);
  check(EvaluateSyntheticContract(ok)==Reason::AllowedBySyntheticContractOnly);
  auto x=ok; x.feature_enabled=false;
  check(EvaluateSyntheticContract(x)==Reason::FeatureOff);
  x=ok; x.observed_car_type=74;
  check(EvaluateSyntheticContract(x)==Reason::UnverifiedVehicleIdentity);
  x=ok; x.observed_pvehicle_hash=0x39DAE0F8u;
  check(EvaluateSyntheticContract(x)==Reason::UnverifiedVehicleIdentity);
  x=ok; x.category=Category::Nos;
  check(EvaluateSyntheticContract(x)==Reason::ProtectedNitroCategory);
  x=ok; x.requested_level=0;
  check(EvaluateSyntheticContract(x)==Reason::BadLevel);
  x=ok; x.requested_level=5;
  check(EvaluateSyntheticContract(x)==Reason::BadLevel);
  x=ok; x.proof.catalog_real_and_matched_to_BMW=false;
  check(EvaluateSyntheticContract(x)==Reason::UnverifiedCatalog);
  x=ok; x.proof.complete_BMW_performance_profile=false;
  check(EvaluateSyntheticContract(x)==Reason::UnverifiedBMWPhysicsProfile);
  x=ok; x.proof.frontend_title_and_price_verified=false;
  check(EvaluateSyntheticContract(x)==Reason::UnverifiedFrontendPrice);
  x=ok; x.proof.target_is_disposable_save=false;
  check(EvaluateSyntheticContract(x)==Reason::SaveNotDisposable);
  x=ok; x.proof.save_roundtrip_verified=false;
  check(EvaluateSyntheticContract(x)==Reason::UnverifiedSaveRoundTrip);
  x=ok; x.proof.runtime_physics_and_other_cars_verified=false;
  check(EvaluateSyntheticContract(x)==Reason::UnverifiedRuntimeRegression);
  std::printf("PRE479_CPP_TESTS_PASSED=%d\n",tests_passed);
  std::printf("PRE479_RUNTIME_MOD_ENABLED=0\n");
  return tests_passed == 14 ? 0 : 1;
}
