#!/usr/bin/env python3
"""PRE337: reversible PRE336 observer staging on PRE317 passive callback.

Uses only existing guest_address argument; does not add guest reads,
change PAL stores, enable cheats, build an APK, access signing or saves.
"""
from pathlib import Path
import hashlib
from pre247_pal_meter_passive_probe_patch import CPP_REL, CPP_TEXT
from pre317_nitro_cycle_staging import inject as pre317_inject

HEADER=Path(__file__).with_name("pre336_nitro_address_diversity.hpp")
HEADER_NAME="pre336_nitro_address_diversity.hpp"
INCLUDE='#include "'+HEADER_NAME+'"\n'
ANCHOR='  if (site < 1 || site > 8) return;\n'
GLOBAL='static nfsmw_pre336::Diversity g_pre336_nitro_address_diversity{};\n'
MARKER='NFSMW_PRE336_NITRO_DIVERSITY'
INSERT="""  if (site >= 1u && site <= 5u) {
    nfsmw_pre336::Snapshot snapshot{};
    if (g_pre336_nitro_address_diversity.observe(site, guest_address, snapshot)) {
      REXLOG_INFO("[NFSMW_PRE336_NITRO_DIVERSITY] site={} slot={} distinct={} samples={} site_mask=0x{:02X} overflow={}",
                  snapshot.site, snapshot.object_slot, snapshot.unique_objects,
                  snapshot.events_site, snapshot.site_mask, snapshot.overflow);
    }
  }
"""
ORIGINAL_GLOBAL='// Log only already-computed store arguments. Bound volume to 12 per site.\n'
ORIGINAL_INCLUDE='#include <rex/logging/macros.h>\n'
def inject(src:str)->str:
    # PRE317 first: exact anchor count, no repeated instrumentation.
    if src.count(ANCHOR)!=1 or src.count('NFSMW_PRE316_NITRO_CYCLE')!=1:
        raise ValueError("PRE337 requires unique PRE317 callback")
    if HEADER_NAME in src or MARKER in src or "g_pre336_nitro_address_diversity" in src:
        raise ValueError("PRE337 already applied")
    if src.count(ORIGINAL_INCLUDE)!=1 or src.count(ORIGINAL_GLOBAL)!=1:
        raise ValueError("PRE337 callback prologue mismatch")
    out=src.replace(ORIGINAL_INCLUDE,ORIGINAL_INCLUDE+INCLUDE,1)
    out=out.replace(ORIGINAL_GLOBAL,ORIGINAL_GLOBAL+GLOBAL,1)
    out=out.replace(ANCHOR,ANCHOR+INSERT,1)
    if out.count(MARKER)!=1 or out.count("NFSMW_PRE247_CHEATS_DIAG")!=1 or out.count("NFSMW_PRE316_NITRO_CYCLE")!=1:
        raise ValueError("PRE337 callback marker mismatch")
    if out.count("REX_STORE_U32(")!=src.count("REX_STORE_U32(") or out.count("REX_LOAD_U32(")!=src.count("REX_LOAD_U32("):
        raise ValueError("PRE337 guest access delta detected")
    if reverse(out)!=src:raise ValueError("PRE337 staging is not exact reversible")
    return out
def reverse(modified:str)->str:
    return modified.replace(ANCHOR+INSERT,ANCHOR,1).replace(
      ORIGINAL_GLOBAL+GLOBAL,ORIGINAL_GLOBAL,1).replace(
      ORIGINAL_INCLUDE+INCLUDE,ORIGINAL_INCLUDE,1)
def apply(root:Path)->dict:
    root=Path(root)
    cpp=root/CPP_REL
    if not cpp.is_file():raise ValueError("PRE337 missing PRE317 callback")
    before=cpp.read_text(encoding="utf-8")
    expected=pre317_inject(CPP_TEXT)
    if before!=expected:raise ValueError("PRE337 requires exact PRE317 baseline")
    header=cpp.parent/HEADER_NAME
    if header.exists():raise ValueError("PRE337 header already present")
    if not HEADER.is_file() or not HEADER.read_bytes().startswith(b"#pragma once\n"):
        raise ValueError("PRE337 header missing/invalid")
    after=inject(before)
    backup=cpp.with_suffix(cpp.suffix+".pre337_original")
    if backup.exists():raise ValueError("PRE337 backup already present")
    backup.write_text(before,encoding="utf-8")
    header.write_bytes(HEADER.read_bytes())
    cpp.write_text(after,encoding="utf-8")
    if cpp.read_text(encoding="utf-8")!=after or backup.read_text(encoding="utf-8")!=before:
        raise ValueError("PRE337 readback failure")
    return {"status":"STAGED_PASSIVE_ONLY",
      "original_sha256":hashlib.sha256(before.encode()).hexdigest(),
      "staged_sha256":hashlib.sha256(after.encode()).hexdigest(),
      "guest_stores_rewritten":0,"extra_guest_loads":0,
      "cheat_enabled":False,"apk_built":False,"owner_verified":False,
      "reverse_exact":True}
