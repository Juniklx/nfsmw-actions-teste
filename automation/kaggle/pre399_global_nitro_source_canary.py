#!/usr/bin/env python3
"""PRE399 validate global Nitro replacement against synthetic and authenticated PRE99 PAL.
Source-only, does not produce/modify APK or sign anything.
"""
from pathlib import Path
import json,sys,tarfile,tempfile
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre242_pal_float_dataflow_readonly import TARGETS
from pre247_pal_meter_passive_probe_patch import insert as pre247_insert, CPP_TEXT
from pre317_nitro_cycle_staging import inject as pre317_inject
from pre337_nitro_diversity_staging import inject as pre337_inject
from pre349_nitro_slot_value_staging import inject as pre349_inject
from pre383_nitro_lr_slot_callback_staging import inject as pre383_inject
from pre398_global_nitro_full_staging import patch_pal,reverse_pal,patch_callback,reverse_callback
OUT=Path("/tmp/nfsmw-pre399/PRE399_GLOBAL_NITRO_SOURCE_CANARY.json")
def synthetic():
    src='DEFINE_REX_FUNC(sub_82424AF0)\n'
    for n in range(1,6):
        src+=f"  REX_STORE_U32(r31.u32 + 252, temp.u32);\n  NFSMW_PRE247_TRACE_METER({n}, r31.u32 + 252, temp.u32);\n"
    src+='DEFINE_REX_FUNC(sub_82424B00)\n'
    staged=patch_pal(src)
    assert reverse_pal(staged)==src
    assert staged.count('REX_STORE_U32(r31.u32 + 252, 0x3F800000u)')==5
    assert staged.count('NFSMW_PRE247_TRACE_METER(')==5
    assert 'NFSMW_PRE247_TRACE_METER(5, r31.u32 + 252, 0x3F800000u)' in staged
    for bad in (staged,src.replace('NFSMW_PRE247_TRACE_METER(3,','NFSMW_PRE247_TRACE_METER(9,'),src.replace('r31.u32 + 252','r31.u32 + 253',1)):
        try:patch_pal(bad)
        except ValueError:pass
        else:raise AssertionError("PRE399 malformed PAL accepted")
    callback=pre383_inject(pre349_inject(pre337_inject(pre317_inject(CPP_TEXT))))
    changed=patch_callback(callback)
    assert reverse_callback(changed)==callback
    assert changed.count('NFSMW_PRE398_GLOBAL_NITRO_FULL')==1
    try:patch_callback(changed)
    except ValueError:pass
    else:raise AssertionError("PRE399 callback reapplied")
    return callback
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE399_GLOBAL_NITRO_SOURCE_CANARY","status":"FAILED",
      "owner_filter_required":False,"owner_verified":False,
      "apk_built":False,"all_cars_user_approved":True,"cheat_tested_on_device":False}
    try:
        callback=synthetic()
        with tempfile.TemporaryDirectory(prefix="pre399_") as td:
            archive=Path(td)/"pre99.tar.gz"
            download(drive_client(),archive)
            sha,_,size=sha_file(archive)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 mismatch")
            with tarfile.open(archive,"r:gz") as tf:
                item=tf.getmember(TARGETS["nitro"]["file"])
                f=tf.extractfile(item)
                if f is None:raise ValueError("PRE99 PAL source unavailable")
                raw=f.read()
            import hashlib
            if hashlib.sha256(raw).hexdigest()!=TARGETS["nitro"]["sha256"]:
                raise ValueError("PRE99 Nitro PAL sha mismatch")
            original=raw.decode("utf-8")
            diag,_=pre247_insert(original,"nitro",TARGETS["nitro"],1)
            changed=patch_pal(diag)
            if reverse_pal(changed)!=diag:raise ValueError("Exact reverse mismatch")
            assert changed.count("PRE398 global Nitro refill site")==5
            assert original.count("PRE398 global Nitro refill site")==0
            assert changed.count("REX_STORE_U32(")==diag.count("REX_STORE_U32(")
            assert changed.count("REX_LOAD_U32(")==diag.count("REX_LOAD_U32(")
            result.update({"status":"AUDIT_OK","pre99_sha256":sha,
              "original_shard_sha256":TARGETS["nitro"]["sha256"],
              "source_patch_reversible":True,"callback_patch_reversible":True,
              "nitro_store_sites":5,"unrelated_stores_changed":0,
              "extra_guest_reads":0,"guest_store_count_delta":0,
              "constant_float_bits":"0x3F800000","value_normalized":1.0,
              "callback_original_length":len(callback),
              "limitation":"Source-only canary; no runtime mechanics/AI behavior or signed Android build validation yet."})
    except Exception as exc:result["error_type"]=type(exc).__name__
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE399_STATUS",result["status"])
    print("PRE399_NITRO_SITES",result.get("nitro_store_sites",0))
    print("PRE399_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
