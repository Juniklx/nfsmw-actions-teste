#pragma once
// PRE348: bounded per-object, per-site Nitro value checkpoints. HOST ONLY.
// Uses only already-computed 32-bit stored float bits; no guest loads/writes.
// A slot is an ephemeral address-table index, never the player identity.
#include <atomic>
#include <cstdint>
namespace nfsmw_pre348 {
struct Snapshot {
  std::uint32_t site;
  std::uint32_t slot;
  std::uint32_t events_for_slot_site;
  std::uint32_t written_float_bits;
};
struct Meter {
  static constexpr std::uint32_t kSlots=16;
  static constexpr std::uint32_t kSites=5;
  std::atomic<std::uint32_t> counts[kSlots][kSites]{};
  bool record(std::uint32_t site,std::uint32_t slot,
              std::uint32_t already_written_bits,Snapshot& out) noexcept {
    if(site<1 || site>kSites || slot<1 || slot>kSlots) return false;
    const auto count=counts[slot-1][site-1].fetch_add(1,std::memory_order_relaxed)+1;
    // Log first and exact powers of two, at most 14 entries / slot/site.
    if(count>8192u || (count & (count-1u))!=0u) return false;
    out={site,slot,count,already_written_bits};
    return true;
  }
};
} // namespace nfsmw_pre348
