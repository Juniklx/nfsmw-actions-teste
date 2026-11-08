#!/usr/bin/env python3
"""PRE389: stage passive caller-LR Nitro telemetry on isolated V44 patch chain.
Requires PRE247/349 already applied, no guest LOAD/STORE rewriting, reversible.
"""
from pathlib import Path
import hashlib
from pre247_pal_meter_passive_probe_patch import CPP_REL
from pre242_pal_float_dataflow_readonly import TARGETS
from pre379_nitro_lr_entry_staging import propose as propose_guest, reverse as reverse_guest
from pre383_nitro_lr_slot_callback_staging import inject as inject_host, reverse as reverse_host, baseline as host_baseline
PAL=TARGETS["nitro"]["file"].removeprefix("workspace/")
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def apply(root:Path)->dict:
    root=Path(root)
    pal=root/PAL
    callback=root/CPP_REL
    if not pal.is_file() or not callback.is_file():raise ValueError("PRE389 staged sources missing")
    raw_pal=pal.read_bytes()
    raw_host=callback.read_bytes()
    src_pal=raw_pal.decode("utf-8")
    src_host=raw_host.decode("utf-8")
    if src_host!=host_baseline():
        raise ValueError("PRE389 requires exact PRE349 callback baseline")
    if src_pal.count("NFSMW_PRE247_TRACE_METER(")<5:
        raise ValueError("PRE389 requires PRE247 Nitro guest trace already staged")
    if "NFSMW_PRE379_NITRO_ENTRY_TRACE" in src_pal:
        raise ValueError("PRE389 guest callback already injected")
    staged_pal=propose_guest(src_pal)
    staged_host=inject_host(src_host)
    if reverse_guest(staged_pal)!=src_pal or reverse_host(staged_host)!=src_host:
        raise ValueError("PRE389 exact reversal failure")
    for needle in ("REX_STORE_U32(", "REX_LOAD_U32("):
        if staged_pal.count(needle)!=src_pal.count(needle):
            raise ValueError("PRE389 guest memory operation delta")
    pal_backup=pal.with_suffix(pal.suffix+".pre389_original")
    callback_backup=callback.with_suffix(callback.suffix+".pre389_original")
    if pal_backup.exists() or callback_backup.exists():
        raise ValueError("PRE389 backups already exist")
    pal_backup.write_bytes(raw_pal)
    callback_backup.write_bytes(raw_host)
    pal.write_text(staged_pal,encoding="utf-8")
    callback.write_text(staged_host,encoding="utf-8")
    if (pal.read_bytes()!=staged_pal.encode() or callback.read_bytes()!=staged_host.encode()
        or pal_backup.read_bytes()!=raw_pal or callback_backup.read_bytes()!=raw_host):
        raise ValueError("PRE389 staging readback mismatch")
    return {"status":"STAGED_PASSIVE_ONLY","reverse_exact":True,
       "pal_before_sha256":sha(raw_pal),"pal_staged_sha256":sha(staged_pal.encode()),
       "callback_before_sha256":sha(raw_host),"callback_staged_sha256":sha(staged_host.encode()),
       "guest_stores_rewritten":0,"extra_guest_loads":0,"cheat_enabled":False,
       "owner_verified":False,"apk_built":False}
