#!/usr/bin/env python3
"""PRE383: source-only composition of Nitro entry LR callback with PRE349 observer.
No guest access changes, no APK. The LR belongs to guest call context, not owner proof.
"""
from pre247_pal_meter_passive_probe_patch import CPP_TEXT
from pre317_nitro_cycle_staging import inject as cycle
from pre337_nitro_diversity_staging import inject as diversity
from pre349_nitro_slot_value_staging import inject as values
from pre379_nitro_lr_entry_staging import MARKER

CALLBACK=r'''
// PRE383: lr provenance of already registered PRE336 Nitro destination.
static std::atomic<std::uint32_t> g_pre383_calls_by_slot[16]{};
extern "C" void NFSMW_PRE379_NITRO_ENTRY_TRACE(unsigned int guest_lr,
                                              unsigned int guest_object_base) noexcept {
  if (!guest_object_base || guest_object_base > 0xFFFFFF02u) return;
  const auto slot = g_pre336_nitro_address_diversity.lookup_slot(
      guest_object_base + 252u);
  if(slot < 1u || slot > 16u) return; // no inference when not yet identified
  auto& n=g_pre383_calls_by_slot[slot-1u];
  const std::uint32_t ordinal=n.fetch_add(1u,std::memory_order_relaxed)+1u;
  if (ordinal > 1024u || (ordinal & (ordinal-1u))!=0u) return;
  (void)guest_lr; // keep host-only synthetic logging stub -Werror clean
  REXLOG_INFO("[NFSMW_PRE383_NITRO_CALLSITE] slot={} guest_lr=0x{:08X} samples={}",
              slot, guest_lr, ordinal);
}
'''
def baseline()->str:
    return values(diversity(cycle(CPP_TEXT)))
def inject(src:str)->str:
    if src!=baseline():raise ValueError("PRE383 requires exact PRE349 callback baseline")
    if MARKER in src or "NFSMW_PRE383_NITRO_CALLSITE" in src:
        raise ValueError("PRE383 already staged")
    result=src+CALLBACK
    if result.count("NFSMW_PRE383_NITRO_CALLSITE")!=1 or reverse(result)!=src:
        raise ValueError("PRE383 reversal mismatch")
    if result.count("REX_LOAD_U32(")!=src.count("REX_LOAD_U32(") or result.count("REX_STORE_U32(")!=src.count("REX_STORE_U32("):
        raise ValueError("PRE383 guest access delta")
    return result
def reverse(src:str)->str:
    if src.count(CALLBACK)!=1:raise ValueError("PRE383 callback missing/duplicated")
    return src.replace(CALLBACK,"",1)
