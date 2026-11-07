#pragma once
// PRE336: passive address diversity observer. No guest reads/writes; no raw addresses logged.
#include <atomic>
#include <cstdint>
namespace nfsmw_pre336 {
struct Snapshot {
  std::uint32_t site;
  std::uint32_t object_slot; // 1-based bounded identity within process, NOT player owner
  std::uint32_t unique_objects;
  std::uint32_t events_site;
  std::uint32_t site_mask;
  bool overflow;
};
struct Diversity {
  static constexpr std::uint32_t kSlots = 16;
  std::atomic<std::uint32_t> addresses[kSlots]{};
  std::atomic<std::uint32_t> site_masks[kSlots]{};
  std::atomic<std::uint32_t> events[5]{};
  std::atomic<std::uint32_t> unique{0};
  std::atomic<bool> exceeded{false};
  // PRE348: a lookup of an already recorded identity; no allocation or guest access.
  // Returns 0 for unknown/overflow addresses. This is NOT a player classification.
  std::uint32_t lookup_slot(std::uint32_t address) const noexcept {
    if (!address || address == 0xffffffffu) return 0;
    for(std::uint32_t i=0;i<kSlots;++i) {
      if(addresses[i].load(std::memory_order_acquire)==address) return i+1;
    }
    return 0;
  }
  bool observe(std::uint32_t site, std::uint32_t guest_address, Snapshot& out) noexcept {
    if(site < 1 || site > 5 || !guest_address || guest_address == 0xffffffffu)
      return false;
    // Preserve all original stores, do not dereference guest_address.
    std::uint32_t index = kSlots;
    bool newly_assigned = false;
    for(std::uint32_t i=0; i<kSlots; ++i) {
      auto existing = addresses[i].load(std::memory_order_acquire);
      if(existing == guest_address) {index=i;break;}
      if(existing != 0) continue;
      std::uint32_t expected = 0;
      if(addresses[i].compare_exchange_strong(expected,guest_address,
           std::memory_order_acq_rel,std::memory_order_acquire)) {
        index=i;newly_assigned=true;unique.fetch_add(1,std::memory_order_relaxed);break;
      }
      if(expected == guest_address) {index=i;break;}
    }
    const auto n=events[site-1].fetch_add(1,std::memory_order_relaxed)+1;
    if(index == kSlots) {
      // Fail closed: do not reuse slots, do not imply a known owner.
      exceeded.store(true,std::memory_order_relaxed);
      if(n==1 || (n<=8192 && (n & (n-1))==0))
        out={site,0,unique.load(std::memory_order_relaxed),n,0,true};
      else return false;
      return true;
    }
    const auto bit=1u << (site-1);
    const auto previous=site_masks[index].fetch_or(bit,std::memory_order_relaxed);
    const bool first_on_site=(previous & bit)==0;
    // Limit logs: first object or first new site on this object, then powers of two.
    if(!(newly_assigned || first_on_site || (n<=8192 && (n & (n-1))==0)))
      return false;
    out={site,index+1,unique.load(std::memory_order_relaxed),n,
         previous|bit,exceeded.load(std::memory_order_relaxed)};
    return true;
  }
};
} // nfsmw_pre336
