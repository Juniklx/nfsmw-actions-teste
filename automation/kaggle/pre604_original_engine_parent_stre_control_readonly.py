#!/usr/bin/env python3
"""PRE604: original Punto engine second endpoint vs synthetic BMW parent/StrE.
Read-only, independently rebuild PRE502 synthetic in RAM and inspect
class-qualified CollectionLoad parent/StrE name coverage. No game patch emitted.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
from datetime import datetime,timezone
from pre502_bmw_engine_combined_level1_scratch import audit as rebuild,NEW_HASH,ENGINE_CLASS,EXP_START,OLD_VLT_OFF,OLD_VLT_LEN
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA,hash32,get_names,chunks
from pre476_pal_performance_reference_resolution_readonly import collect_rows

OUT=Path("/tmp/nfsmw-pre604/report.json")
EXPECTED_COMBINED="d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6"
def sha(v):return hashlib.sha256(v).hexdigest()
def check_source():
   r,loc=locate()
   raw=r.read(loc["absolute_offset"],loc["size"])
   if len(raw)!=697856 or sha(raw)!=EXPECTED_VPAK_SHA:
       raise ValueError("Original authenticated PAL VPAK checksum mismatch")
   _,bl,vl,bo,vo=struct.unpack_from("<IIIII",raw,16)
   if (bl,vl,bo,vo)!=(354959,342720,128,355136):
       raise ValueError("Original VPAK geometry mismatch")
   binv=raw[bo:bo+bl];vlt=raw[vo:vo+vl]
   rows,_=collect_rows(vlt)
   names={hash32(x) for x in get_names(binv,chunks(binv,"BIN")[0])}
   pairs={
      "bmw_stock":(ENGINE_CLASS,hash32("bmwm3gtr")),
      "punto_stock":(ENGINE_CLASS,hash32("punto")),
      "punto_second":(ENGINE_CLASS,0xA6F0F405)
   }
   originals={}
   for name,key in pairs.items():
       parts=rows.get(key,[])
       if len(parts)!=1:raise ValueError("Original class/collection missing "+name)
       off=parts[0]["record_offset_vlt"]
       c,cls,parent=struct.unpack_from(">III",vlt,off)
       if (c,cls)!= (key[1],key[0]):raise ValueError("Original collection header different")
       originals[name]={"collection_hash":f"{c:08x}","parent_hash":f"{parent:08x}",
          "name_hash_in_original_StrE":c in names,"record_offset":off}
   bmw=originals["bmw_stock"]; punto=originals["punto_stock"];second=originals["punto_second"]
   if (second["parent_hash"]!=punto["collection_hash"] or
       bmw["parent_hash"]!=f"{hash32('default'):08x}" or
       second["name_hash_in_original_StrE"] is not False):
       raise ValueError("Original derived Punto control or BMW parent mismatch")
   return originals,names,vlt

def audit():
    p474=json.loads(Path("docs/PRE474_PAL_BMW_PUNTO_PERFORMANCE_REF_ARRAYS.json").read_text())
    p476=json.loads(Path("docs/PRE476_PAL_BMW_PUNTO_REFERENCE_RESOLUTION_READONLY.json").read_text())
    p504=json.loads(Path("docs/PRE504_ORIGINAL_STRE_VLT_COLLECTION_NAME_COVERAGE_READONLY.json").read_text())
    p502=json.loads(Path("docs/PRE502_BMW_ENGINE_FULL_LEVEL1_COMBINED_SCRATCH.json").read_text())
    prev=json.loads(Path("docs/PRE603_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    if (any(x.get("status")!="AUDIT_OK" for x in (p474,p476,p504,p502,prev))
        or p504.get("original_VLT_collections_without_name_hash_in_StrE")!=1065
        or p502.get("scratch_export_count")!=2400
        or p502.get("new_collection_name_missing_original_StrE") is not True
        or prev.get("canonical_sha256")!="b4f7df4db565913856ef82eec71c15a0362c4c52df23d80d264246654e012bd6"):
        raise ValueError("PRE474/476/502/504/603 source proofs missing")
    punto=p474["vehicles"]["punto"]["categories_with_explicit_references"]["engine"]
    resolved=p476["vehicles"]["punto"]["engine"]["reference_resolution"]
    if (punto["capacity"]!=2 or punto["item_count"]!=2 or
        punto["pvehicle_upgrade_limit"]!=4 or
        punto["items"][1]["collection_hash"]!="a6f0f405" or
        punto["items"][1]["collection_name_candidates"]!=[] or
        resolved[1]["explicit_reference_exists_in_vlt"] is not True or
        resolved[1]["chain"][0]["parent_hash"]!="a6ee7a11"):
        raise ValueError("Original Punto non-StrE-derived engine control not exact")
    original,names,vlt=check_source()
    def consume_scratch(scratch):
        if len(scratch)!=698004 or sha(scratch)!=EXPECTED_COMBINED:
            raise ValueError("Synthetic PRE502 VPAK changed")
        _,bl,vl,bo,vo=struct.unpack_from("<IIIII",scratch,16)
        if (vo+vl!=len(scratch) or vl!=342788 or bl!=355088):
            raise ValueError("Synthetic VPAK geometry invalid")
        svlt=scratch[vo:vo+vl]
        c,cls,parent=struct.unpack_from(">III",svlt,EXP_START)
        if (c,cls)!=(NEW_HASH,ENGINE_CLASS):
            raise ValueError("Synthetic new CollectionLoad header missing")
        newparent=f"{parent:08x}"
        if (newparent!=original["bmw_stock"]["parent_hash"] or
            newparent==original["bmw_stock"]["collection_hash"] or
            NEW_HASH in names):
            raise ValueError("Expected synthetic copy-parent and StrE property changed")
        # Original BMW collection still contains stock layout and parent.
        return {
          "candidate_collection_hash":f"{NEW_HASH:08x}",
          "candidate_class_hash":f"{ENGINE_CLASS:08x}",
          "candidate_parent_hash":newparent,
          "candidate_parent_is_BMW_stock_collection":False,
          "candidate_parent_is_default":True,
          "candidate_collection_name_in_original_StrE":False,
          "synthetic_candidate_VPAK_sha256":sha(scratch),
          "synthetic_new_collection_original_header_except_name":True
        }
    scratch_rebuild=rebuild(consume_scratch=consume_scratch)
    if scratch_rebuild.get("status")!="AUDIT_OK":
        raise ValueError("PRE502 in RAM failed")
    details=scratch_rebuild.get("_private_scratch_analysis")
    if not details or details.get("candidate_parent_is_default") is not True:
        raise ValueError("PRE502 parent inspection callback missing")
    return {
      "stage":"PRE604_ORIGINAL_PUNTO_DERIVED_ENGINE_VS_SYNTHETIC_BMW_PARENT_AND_STRE",
      "status":"AUDIT_OK",
      "original_VPAK_sha256":EXPECTED_VPAK_SHA,
      "original_engine_controls":original,
      "Punto_engine_second_ref_count":2,
      "Punto_engine_upgrade_count":4,
      "original_Punto_second_engine_in_VLT":True,
      "original_Punto_second_engine_absent_StrE":True,
      "Punto_second_engine_parent_is_Punto_stock":True,
      **details,
      "candidate_parent_linkage_differs_from_original_Punto_derived_convention":True,
      "StrE_membership_structurally_not_required_for_every_existing_engine_collection":True,
      "StrE_membership_runtime_required_for_new_collection_proven":False,
      "candidate_BMW_parent_causes_corrupted_save_proven":False,
      "BMW_upgrade_GetMaxLevel_semantics_proven":False,
      "new_parent_variant_patched":False,
      "new_device_script_prepared":False,
      "guest_executed":False,
      "game_assets_modified":False,
      "save_modified":False,"APK_built":False,"signing_accessed":False
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=audit()
    except Exception as e:result={
      "stage":"PRE604_ORIGINAL_PUNTO_DERIVED_ENGINE_VS_SYNTHETIC_BMW_PARENT_AND_STRE",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:270],
      "guest_executed":False,"game_assets_modified":False,
      "save_modified":False,"APK_built":False,"signing_accessed":False}
    result["run_id"]=args.run_id;result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE604_STATUS",result["status"])
    print("PRE604_PARENT",result.get("candidate_parent_hash","unknown"))
    print("PRE604_ERROR",result.get("error_type","none"),result.get("error",""))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
