#!/usr/bin/env python3
"""PRE501 — isolate exact BMW pvehicle engine_upgrades field, RAM ONLY.

Based on authenticated PAL original ATTRIBUTES.BIN and PRE473/PRE500. Model
a single engine performance upgrade level without writing the VPAK, APK, ISO,
guest state, or save. This only proves an isolated counter edit is possible;
it does NOT mean the Xbox PAL game accepts the rebuilt engine collection.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from datetime import datetime,timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA

OUT=Path("/tmp/nfsmw-pre501/report.json")
BMW="bmwm3gtr"
CAREER="m3gtre46careerstart"
PUNTO="punto"
COUNTER_OFFSET=40
DEFAULT_FIELDS={"engine_upgrades":40,"transmission_upgrades":44,
   "nos_upgrades":48,"brakes_upgrades":52,"tires_upgrades":60,
   "induction_upgrades":68,"chassis_upgrades":72}
def digest(a):return hashlib.sha256(a).hexdigest()
def audit():
    proof=json.loads(Path("docs/PRE473_PAL_PVEHICLE_BMW_UPGRADE_COUNTERS_READONLY.json").read_text())
    recon=json.loads(Path("docs/PRE500_BMW_ENGINE_FULL_VPAK_SCRATCH_REBUILD.json").read_text())
    identity=json.loads(Path("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json").read_text())
    if (proof.get("status")!="AUDIT_OK" or proof.get("vpak_sha256")!=EXPECTED_VPAK_SHA
        or recon.get("status")!="AUDIT_OK" or recon.get("source_pal_sha256")!=EXPECTED_VPAK_SHA
        or recon.get("new_engine_ExpN_RefSpec_PtrN_reparsed") is not True
        or identity.get("pal_resource_identical_to_usa_reference") is not True):
        raise ValueError("Original or scratch BMW proof not verified")
    if proof.get("field_offsets")!=DEFAULT_FIELDS:
        raise ValueError("Source PAL pvehicle counter layout changed")
    byname={}
    for vehicle in proof["selected_variants_and_control_records"]:
        if not vehicle.get("candidate_names"):continue
        name=vehicle["candidate_names"][0]
        byname[name]=vehicle
    if not all(k in byname for k in (BMW,CAREER,PUNTO)):
        raise ValueError("Missing original named vehicle controls")
    offsets={k:byname[k]["bin_layout_offset"] for k in (BMW,CAREER,PUNTO)}
    if offsets!={BMW:256448,CAREER:269568,PUNTO:258352}:
        raise ValueError("Original BMW/careerstart/Punto layout offsets unexpected")
    reader,position=locate()
    original=reader.read(position["absolute_offset"],position["size"])
    if len(original)!=697856 or digest(original)!=EXPECTED_VPAK_SHA:
        raise ValueError("Original source resource changed")
    _,bl,vl,bo,vo=struct.unpack_from("<IIIII",original,16)
    if (bl,vl,bo,vo)!=(354959,342720,128,355136):
        raise ValueError("Original vault offset mismatch")
    B=original[bo:bo+bl]
    originals={}
    for name in (BMW,CAREER,PUNTO):
        base=offsets[name]
        originals[name]={k:struct.unpack_from(">i",B,base+offset)[0]
                         for k,offset in DEFAULT_FIELDS.items()}
        if originals[name]!=byname[name]["upgrade_counters_original_signed_i32"]:
            raise ValueError("Original PAL 7-category signed BE counters disagree for "+name)
    if originals[BMW]["engine_upgrades"]!=0 or originals[CAREER]["engine_upgrades"]!=0 or originals[PUNTO]["engine_upgrades"]!=4:
        raise ValueError("Stock BMW/Punto engine tier preconditions changed")
    if originals[BMW]["nos_upgrades"]!=3:
        raise ValueError("Nitro counter for BMW no longer matches original")
    patch_absolute=bo+offsets[BMW]+COUNTER_OFFSET
    scratch=bytearray(original)
    struct.pack_into(">i",scratch,patch_absolute,1)  # one synthetic test level
    if len(scratch)!=len(original) or scratch[:bo]!=original[:bo]:
        raise ValueError("Scratch changed resource geometry")
    newB=scratch[bo:bo+bl]
    if struct.unpack_from(">i",newB,offsets[BMW]+COUNTER_OFFSET)[0]!=1:
        raise ValueError("BMW engine tier scratch change failed")
    if any(struct.unpack_from(">i",newB,offsets[BMW]+offset)[0]!=value
           for k,offset in DEFAULT_FIELDS.items() if k!="engine_upgrades"
           for value in [originals[BMW][k]]):
        raise ValueError("BMW NOS/other categories changed")
    for name in (CAREER,PUNTO):
        if any(struct.unpack_from(">i",newB,offsets[name]+offset)[0]!=v
               for k,offset in DEFAULT_FIELDS.items()
               for v in [originals[name][k]]):
            raise ValueError(name+" counters changed")
    allowed=set(range(patch_absolute,patch_absolute+4))
    actual=[i for i,(a,b) in enumerate(zip(original,scratch)) if a!=b]
    if not actual or any(i not in allowed for i in actual):
        raise ValueError("Scratch changed bytes outside BMW engine counter")
    if bytes(scratch[:patch_absolute])!=original[:patch_absolute] or bytes(scratch[patch_absolute+4:])!=original[patch_absolute+4:]:
        raise ValueError("Original source bytes outside engine counter altered")
    # PRE500's new engine RefSpec count is exactly 2, consistent with a
    # STOCK level 0 and one synthetic level 1, but runtime is not proved.
    if recon["original_export_count"]!=2399 or recon["scratch_export_count"]!=2400:
        raise ValueError("PRE500 independent collection model changed")
    return {
      "stage":"PRE501_PAL_BMW_ENGINE_SINGLE_LEVEL_COUNTER_RAM_ONLY",
      "status":"AUDIT_OK","source_sha256":EXPECTED_VPAK_SHA,
      "original_BMW_engine_upgrade_counter":0,
      "synthetic_BMW_engine_upgrade_counter":1,
      "scratch_engine_counter_bin_relative_offset":offsets[BMW]+COUNTER_OFFSET,
      "scratch_engine_counter_vpak_absolute_offset":patch_absolute,
      "scratch_change_only_BMW_engine_counter":True,
      "source_PAL_pvehicle_int_endianness":"big-endian signed 32-bit",
      "original_Punto_engine_max_level":4,
      "Punto_all_original_upgrade_limits_unchanged":True,
      "BMW_careerstart_all_original_upgrade_limits_unchanged":True,
      "BMW_original_nitro_upgrade_limit":3,
      "BMW_original_nitro_unchanged":True,
      "BMW_other_six_original_categories_unchanged":True,
      "PRE500_second_engine_ref_count":2,
      "in_memory_counter_compatible_with_two_level_model_only":True,
      "PRE500_new_engine_collection_and_counter_tested_in_one_combined_VPAK":False,
      "game_runtime_GetMaxLevel_behavior_verified":False,
      "game_runtime_SetLevel_behavior_verified":False,
      "part_shop_available":False,
      "gameplay_physics_proven":False,
      "experimental_candidate_only":True,
      "original_game_asset_modified":False,
      "modified_game_file_written":False,
      "apk_built":False,"save_modified":False,
      "tuning_enabled":False,
      "byte_ranges_read":reader.total
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as exc:r={
      "stage":"PRE501_PAL_BMW_ENGINE_SINGLE_LEVEL_COUNTER_RAM_ONLY",
      "status":"FAILED","error_type":type(exc).__name__,"error":str(exc)[:240],
      "original_game_asset_modified":False,
      "modified_game_file_written":False,"apk_built":False,
      "save_modified":False,"tuning_enabled":False
    }
    r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE501_STATUS",r["status"],flush=True)
    print("PRE501_SCRATCH_ENGINE_LEVEL",r.get("synthetic_BMW_engine_upgrade_counter","none"),flush=True)
    print("PRE501_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
