#!/usr/bin/env python3
"""PRE349: stage PRE348 per-slot Nitro values after PRE337 in a disposable callback.
No original PAL store/load modifications, no APK, no signer, no saves.
"""
from pathlib import Path
import hashlib
from pre247_pal_meter_passive_probe_patch import CPP_REL,CPP_TEXT
from pre317_nitro_cycle_staging import inject as pre317_inject
from pre337_nitro_diversity_staging import inject as pre337_inject
from pre337_nitro_diversity_staging import INSERT as PRE337_INSERT
from pre337_nitro_diversity_staging import INCLUDE as PRE337_INCLUDE
from pre337_nitro_diversity_staging import GLOBAL as PRE337_GLOBAL

HEADER=Path(__file__).with_name("pre348_nitro_slot_values.hpp")
HEADER_NAME="pre348_nitro_slot_values.hpp"
INCLUDE='#include "'+HEADER_NAME+'"\n'
GLOBAL='static nfsmw_pre348::Meter g_pre348_nitro_slot_meter{};\n'
MARKER="NFSMW_PRE348_NITRO_SLOT_VALUES"
INSERT="""  if (site>=1u && site<=5u) {
    nfsmw_pre348::Snapshot snapshot{};
    const std::uint32_t slot = g_pre336_nitro_address_diversity.lookup_slot(guest_address);
    if (g_pre348_nitro_slot_meter.record(site,slot,stored_f32_bits,snapshot)) {
      REXLOG_INFO("[NFSMW_PRE348_NITRO_SLOT_VALUES] site={} slot={} samples={} written_f32_bits=0x{:08X}",
                  snapshot.site, snapshot.slot, snapshot.events_for_slot_site,
                  snapshot.written_float_bits);
    }
  }
"""
def baseline()->str:
    return pre337_inject(pre317_inject(CPP_TEXT))
def inject(src:str)->str:
    if src != baseline():
        raise ValueError("PRE349 requires exact PRE337 callback baseline")
    if src.count(PRE337_INCLUDE)!=1 or src.count(PRE337_GLOBAL)!=1 or src.count(PRE337_INSERT)!=1:
        raise ValueError("PRE349 PRE337 anchors absent/ambiguous")
    out=src.replace(PRE337_INCLUDE,PRE337_INCLUDE+INCLUDE,1)
    out=out.replace(PRE337_GLOBAL,PRE337_GLOBAL+GLOBAL,1)
    out=out.replace(PRE337_INSERT,PRE337_INSERT+INSERT,1)
    if out.count(MARKER)!=1 or reverse(out)!=src:
        raise ValueError("PRE349 idempotence/reversibility failure")
    for op in ("REX_STORE_U32(", "REX_LOAD_U32("):
        if out.count(op)!=src.count(op):
            raise ValueError("PRE349 changed guest memory operations")
    return out
def reverse(src:str)->str:
    return src.replace(PRE337_INSERT+INSERT,PRE337_INSERT,1).replace(
      PRE337_GLOBAL+GLOBAL,PRE337_GLOBAL,1).replace(
      PRE337_INCLUDE+INCLUDE,PRE337_INCLUDE,1)
def apply(root:Path)->dict:
    root=Path(root)
    cpp=root/CPP_REL
    if not cpp.is_file():raise ValueError("PRE349 callback missing")
    before=cpp.read_text(encoding="utf-8")
    if before != baseline():raise ValueError("PRE349 unexpected prior source")
    dest=cpp.parent/HEADER_NAME
    backup=cpp.with_suffix(cpp.suffix+".pre349_original")
    if dest.exists() or backup.exists():raise ValueError("PRE349 already staged")
    if not HEADER.is_file() or not HEADER.read_bytes().startswith(b"#pragma once\n"):
        raise ValueError("PRE349 header missing")
    after=inject(before)
    backup.write_text(before,encoding="utf-8")
    dest.write_bytes(HEADER.read_bytes())
    cpp.write_text(after,encoding="utf-8")
    if cpp.read_text(encoding="utf-8")!=after or backup.read_text(encoding="utf-8")!=before:
        raise ValueError("PRE349 readback mismatch")
    return {"status":"STAGED_PASSIVE_ONLY",
      "original_sha256":hashlib.sha256(before.encode()).hexdigest(),
      "patched_sha256":hashlib.sha256(after.encode()).hexdigest(),
      "reverse_exact":True,"guest_stores_rewritten":0,
      "extra_guest_loads":0,"cheat_enabled":False,
      "owner_verified":False,"apk_built":False}
