#!/usr/bin/env python3
"""PRE398 global Nitro cheat: replace ONLY five authenticated PAL Nitro stores with 1.0f bits.

No player-owner assumption. Game mechanic change deliberately affects all vehicles
using sub_82424AF0. Reversible from isolated PRE390 V45 build workspace.
No guest reads added, no extra stores, no save edits, no thermal/graphics changes.
"""
from pathlib import Path
import hashlib,re
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre242_pal_float_dataflow_readonly import TARGETS
from pre247_pal_meter_passive_probe_patch import CPP_REL
PAL_REL=TARGETS["nitro"]["file"].removeprefix("workspace/")
FUNCTION=TARGETS["nitro"]["function"]
MARKER="NFSMW_PRE398_GLOBAL_NITRO_FULL"
FULL="0x3F800000u"   # IEEE 754 binary32 1.0
PAIR=re.compile(
    r"(?m)^(?P<indent>[ \t]*)REX_STORE_U32\(r31\.u32 \+ 252, temp\.u32\);\n"
    r"(?P=indent)NFSMW_PRE247_TRACE_METER\((?P<site>[1-5]), r31\.u32 \+ 252, temp\.u32\);\n")
CALLBACK_ANCHOR="  if (site < 1 || site > 8) return;\n"
CALLBACK_CODE=r'''  if (site >= 1u && site <= 5u) {
    static std::atomic<bool> once_pre398{false};
    if (!once_pre398.exchange(true, std::memory_order_relaxed)) {
      REXLOG_INFO("[NFSMW_PRE398_GLOBAL_NITRO_FULL] active=1 affects_all_objects=1 full_bits=0x3F800000");
    }
  }
'''
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def make_pair(site:int,indent:str)->str:
    return (f"{indent}// PRE398 global Nitro refill site {site}\n"
            f"{indent}REX_STORE_U32(r31.u32 + 252, {FULL});\n"
            f"{indent}NFSMW_PRE247_TRACE_METER({site}, r31.u32 + 252, {FULL});\n")
def original_pair(site:int,indent:str)->str:
    return (f"{indent}REX_STORE_U32(r31.u32 + 252, temp.u32);\n"
            f"{indent}NFSMW_PRE247_TRACE_METER({site}, r31.u32 + 252, temp.u32);\n")
def patch_pal(src:str)->str:
    if "PRE398 global Nitro refill site" in src:raise ValueError("PRE398 already staged")
    body=body_for_function(src,FUNCTION)
    matches=list(PAIR.finditer(body))
    if len(matches)!=5 or sorted(int(m["site"]) for m in matches)!=[1,2,3,4,5]:
        raise ValueError("PRE398 Nitro source pattern mismatch")
    parts=[];pos=0
    for m in matches:
        parts.extend((body[pos:m.start()],make_pair(int(m["site"]),m["indent"])))
        pos=m.end()
    parts.append(body[pos:])
    updated="".join(parts)
    if src.count(body)!=1:raise ValueError("PRE398 Nitro function not unique")
    result=src.replace(body,updated,1)
    if reverse_pal(result)!=src:raise ValueError("PRE398 PAL exact reverse mismatch")
    for op in ("REX_STORE_U32(", "REX_LOAD_U32("):
        if result.count(op)!=src.count(op):raise ValueError("PRE398 unexpected guest operation count")
    if result.count("0x3F800000u")!=10:raise ValueError("PRE398 constant count mismatch")
    return result
def reverse_pal(src:str)->str:
    body=body_for_function(src,FUNCTION)
    changed=body
    for site in range(1,6):
        target=re.compile(r"(?m)^([ \t]*)// PRE398 global Nitro refill site "+str(site)+r"\n"
            r"\1REX_STORE_U32\(r31\.u32 \+ 252, 0x3F800000u\);\n"
            r"\1NFSMW_PRE247_TRACE_METER\("+str(site)+r", r31\.u32 \+ 252, 0x3F800000u\);\n")
        matches=list(target.finditer(changed))
        if len(matches)!=1:raise ValueError("PRE398 PAL revert site mismatch")
        m=matches[0]
        changed=changed[:m.start()]+original_pair(site,m.group(1))+changed[m.end():]
    if src.count(body)!=1:raise ValueError("PRE398 PAL revert body ambiguity")
    return src.replace(body,changed,1)
def patch_callback(src:str)->str:
    if MARKER in src or src.count(CALLBACK_ANCHOR)!=1:
        raise ValueError("PRE398 callback already modified or missing")
    out=src.replace(CALLBACK_ANCHOR,CALLBACK_ANCHOR+CALLBACK_CODE,1)
    if reverse_callback(out)!=src:raise ValueError("PRE398 callback exact reverse mismatch")
    return out
def reverse_callback(src:str)->str:
    if src.count(CALLBACK_CODE)!=1:raise ValueError("PRE398 callback marker mismatch")
    return src.replace(CALLBACK_CODE,"",1)
def apply(root:Path)->dict:
    root=Path(root);pal=root/PAL_REL;cb=root/CPP_REL
    if not pal.is_file() or not cb.is_file():raise ValueError("PRE398 staged source missing")
    before=pal.read_bytes();before_cb=cb.read_bytes()
    pal_src=before.decode("utf-8");cb_src=before_cb.decode("utf-8")
    if "NFSMW_PRE379_NITRO_ENTRY_TRACE" not in pal_src:
        raise ValueError("PRE398 requires completed V45 PRE389 PAL staging")
    if "NFSMW_PRE348_NITRO_SLOT_VALUES" not in cb_src:
        raise ValueError("PRE398 requires PRE349 callback baseline")
    new_pal=patch_pal(pal_src);new_cb=patch_callback(cb_src)
    backup=pal.with_suffix(pal.suffix+".pre398_original")
    backup_cb=cb.with_suffix(cb.suffix+".pre398_original")
    if backup.exists() or backup_cb.exists():raise ValueError("PRE398 backup already present")
    backup.write_bytes(before);backup_cb.write_bytes(before_cb)
    pal.write_text(new_pal,encoding="utf-8");cb.write_text(new_cb,encoding="utf-8")
    if pal.read_bytes()!=new_pal.encode() or cb.read_bytes()!=new_cb.encode() or backup.read_bytes()!=before or backup_cb.read_bytes()!=before_cb:
        raise ValueError("PRE398 stage readback failed")
    return {"status":"STAGED_GLOBAL_NITRO_ALL_CARS","nitro_stores_modified":5,
      "other_guest_stores_modified":0,"guest_store_count_delta":0,
      "extra_guest_loads":0,"reverse_exact":True,
      "all_car_objects_affected":True,"owner_filter_required":False,
      "cheat_enabled":True,"apk_built":False,"test_on_device":False,
      "pal_before_sha256":sha(before),"pal_after_sha256":sha(new_pal.encode()),
      "callback_before_sha256":sha(before_cb),"callback_after_sha256":sha(new_cb.encode())}
