#pragma once
// PRE479: Isolated read-only design contract for a future BMW M3 GTR
// performance-tuning modification. This header never accesses guest memory,
// filesystem, game saves, hooks, physics or signed APK content.
// Not connected to the Android runtime; OFF by construction.
#include <cstdint>

namespace nfsmw_bmw_tuning {

constexpr std::uint32_t kTargetCarTypeFromPRE455 = 41u;
constexpr std::uint32_t kTargetPVehicleHashFromPRE474 = 0xCD88083Fu;
// The runtime equivalence of these two identifiers still requires a
// read-only verification using the actual user's BMW career car.
constexpr bool kRuntimeIntegrationProven = false;

enum class Category : std::uint8_t {
  Tires = 0, Brakes = 1, Chassis = 2, Transmission = 3,
  Engine = 4, Induction = 5, Nos = 6
};
enum class Reason : std::uint8_t {
  AllowedBySyntheticContractOnly = 0,
  RuntimeNotIntegrated,
  FeatureOff,
  UnverifiedVehicleIdentity,
  ProtectedNitroCategory,
  BadLevel,
  UnverifiedCatalog,
  UnverifiedBMWPhysicsProfile,
  UnverifiedFrontendPrice,
  SaveNotDisposable,
  UnverifiedSaveRoundTrip,
  UnverifiedRuntimeRegression
};
struct Proofs final {
  bool catalog_real_and_matched_to_BMW = false;
  bool complete_BMW_performance_profile = false;
  bool frontend_title_and_price_verified = false;
  bool target_is_disposable_save = false;
  bool save_roundtrip_verified = false;
  bool runtime_physics_and_other_cars_verified = false;
};
struct Request final {
  std::uint32_t observed_car_type = 0;
  std::uint32_t observed_pvehicle_hash = 0;
  Category category = Category::Engine;
  std::int32_t requested_level = 0;
  bool feature_enabled = false;
  Proofs proof = {};
};
constexpr std::int32_t CategoryMax(const Category category) noexcept {
  switch (category) {
    case Category::Tires:        return 3;
    case Category::Brakes:       return 4;
    case Category::Chassis:      return 3;
    case Category::Transmission: return 4;
    case Category::Engine:       return 4;
    case Category::Induction:    return 3;
    case Category::Nos:          return 0; // Nitro PRE398 is explicitly protected.
  }
  return 0;
}
constexpr Reason EvaluateSyntheticContract(const Request &req) noexcept {
  if (!req.feature_enabled) return Reason::FeatureOff;
  if (req.observed_car_type != kTargetCarTypeFromPRE455 ||
      req.observed_pvehicle_hash != kTargetPVehicleHashFromPRE474) {
    return Reason::UnverifiedVehicleIdentity;
  }
  if (req.category == Category::Nos) return Reason::ProtectedNitroCategory;
  if (req.requested_level < 1 ||
      req.requested_level > CategoryMax(req.category)) {
    return Reason::BadLevel;
  }
  if (!req.proof.catalog_real_and_matched_to_BMW) return Reason::UnverifiedCatalog;
  if (!req.proof.complete_BMW_performance_profile) return Reason::UnverifiedBMWPhysicsProfile;
  if (!req.proof.frontend_title_and_price_verified) return Reason::UnverifiedFrontendPrice;
  if (!req.proof.target_is_disposable_save) return Reason::SaveNotDisposable;
  if (!req.proof.save_roundtrip_verified) return Reason::UnverifiedSaveRoundTrip;
  if (!req.proof.runtime_physics_and_other_cars_verified) return Reason::UnverifiedRuntimeRegression;
  return Reason::AllowedBySyntheticContractOnly;
}
constexpr Reason EvaluateAnyRealGameRequest(const Request &req) noexcept {
  // No code path can become active until a separately reviewed future
  // runtime-integration gate is explicitly implemented and proven.
  if (!kRuntimeIntegrationProven) return Reason::RuntimeNotIntegrated;
  return EvaluateSyntheticContract(req);
}
} // namespace nfsmw_bmw_tuning
