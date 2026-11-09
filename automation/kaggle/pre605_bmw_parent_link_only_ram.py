#!/usr/bin/env python3
"""PRE605: private read-only experiment on reconstructed PRE502 VPAK.
Adjust ONLY the synthetic BMW engine CollectionLoad parent hash from default
to existing stock BMW engine collection, echoing original Punto derived-parent
pattern. No fragment, APK, game asset, phone or save output.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
from datetime import datetime,timezone
from pre502_bmw_engine_combined_level1_scratch import (
  audit as rebuild,NEW_HASH,ENGINE_CLASS,EXP_START,DAT_START,OLD_VLT_LEN,hash32)
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash

OUT=Path("/tmp/nfsmw-pre605/report.json")
SRC_SHA="d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6"
VPAK_SIZE=698004
NEW_COL=EXP_START
def sha(v):return hashlib.sha256(v).hexdigest()
def audit():
  p604=json.loads(Path("docs/PRE604_BMW_PARENT_ORIGINAL_PUNTO_STRE_READONLY.json").read_text())
  p502=json.loads(Path("docs/PRE502_BMW_ENGINE_FULL_LEVEL1_COMBINED_SCRATCH.json").read_text())
  p591=json.loads(Path("docs/PRE591_BMW_REFSPEC_POINTER_ONLY_PRIVATE_METADATA.json").read_text())
  if (any(p.get("status")!="AUDIT_OK" for p in (p604,p502,p591)) or
      p604.get("candidate_parent_is_default") is not True or
      p604.get("candidate_parent_is_BMW_stock_collection") is not False or
      p604["original_engine_controls"]["punto_second"]["parent_hash"]!="a6ee7a11" or
      p604["original_engine_controls"]["bmw_stock"]["collection_hash"]!="cd88083f" or
      p591.get("counter_byte_changed_vs_PRE502")!=[256619] or
      p502.get("scratch_vpak_bytes")!=VPAK_SIZE):
      raise ValueError("PRE604 originals or PRE502/591 counter provenance missing")
  def analyze(original:bytes):
    if sha(original)!=SRC_SHA or len(original)!=VPAK_SIZE:
      raise ValueError("Authenticated PRE502 combined candidate differs")
    _,bl,vl,bo,vo=struct.unpack_from("<IIIII",original,16)
    if vo+vl!=len(original) or vl!=OLD_VLT_LEN+68:
      raise ValueError("Rebuilt VLT geometry changed")
    col_off=vo+NEW_COL
    c,cl,oldparent=struct.unpack_from(">III",original,col_off)
    default=hash32("default");stock=hash32("bmwm3gtr")
    if (c,cl,oldparent)!=(NEW_HASH,ENGINE_CLASS,default):
      raise ValueError("Synthetic source BMW collection name/class/parent changed")
    child=bytearray(original)
    struct.pack_into(">I",child,col_off+8,stock)
    fixed=bytes(child)
    actual_changes=[i for i,(a,b) in enumerate(zip(original,fixed)) if a!=b]
    if (not actual_changes or len(actual_changes)>4 or
        any(not col_off+8<=x<col_off+12 for x in actual_changes)):
      raise ValueError("Unexpected candidate edits beyond new collection parent")
    nc,ncl,np=struct.unpack_from(">III",fixed,col_off)
    if (nc,ncl,np)!=(NEW_HASH,ENGINE_CLASS,stock):
      raise ValueError("Corrected inherited BMW motor header parse invalid")
    # Confirm declared new VLT export record still refers to the same child.
    exports=fixed[vo+NEW_COL+36:vo+NEW_COL+36+48020]
    if exports[:4]!=b"ExpN":
      raise ValueError("Synthetic ExpN after added DatN not located")
    cnt=struct.unpack_from(">I",exports,8)[0]
    if cnt!=2400:raise ValueError("Synthetic 2400 exports changed")
    if struct.unpack_from(">i",fixed,128+256488)[0]!=1:
      raise ValueError("Counter must stay 1 in parent-only scratch")
    expected_original_name=original[col_off:col_off+4]
    if expected_original_name!=fixed[col_off:col_off+4]:
      raise ValueError("New engine hash unexpectedly altered")
    checksum=ea_data_hash(fixed)
    if checksum==0x4d05584a or checksum==0x296ad9ed:
      raise ValueError("Parent-adjusted VPAK hash unexpectedly collides")
    return {
      "source_PRE502_synthetic_sha256":SRC_SHA,
      "candidate_parent_adjusted_VPAK_sha256":sha(fixed),
      "candidate_parent_adjusted_VPAK_bytes":len(fixed),
      "candidate_parent_adjusted_EA_checksum_hex":f"{checksum:08x}",
      "new_collection_parent_before":f"{oldparent:08x}",
      "new_collection_parent_after":f"{np:08x}",
      "new_engine_collection_id_unchanged":f"{nc:08x}",
      "new_engine_class_id_unchanged":f"{ncl:08x}",
      "new_child_record_VPAK_offset":col_off,
      "parent_edit_vpak_absolute_byte_offsets":actual_changes,
      "all_other_PRE502_VPAK_bytes_unchanged":True,
      "BMW_engine_counter_still_one":True,
      "new_child_parent_is_stock_BMW":True,
      "original_Punto_derived_style_mirrored":True,
      "candidate_BMW_parent_fix_causes_save_load_success_proven":False,
      "candidate_BMW_parent_fix_causes_real_engine_tuning_proven":False
    }
  rebuilt=rebuild(consume_scratch=analyze)
  if rebuilt.get("status")!="AUDIT_OK":raise ValueError("Authenticated PRE502 rebuild failed")
  meta=rebuilt.get("_private_scratch_analysis")
  if not meta or meta.get("new_child_parent_is_stock_BMW") is not True:
    raise ValueError("PRE605 in-memory callback output missing")
  return {"stage":"PRE605_BMW_ENGINE_PARENT_LINK_ONLY_IN_RAM_HYPOTHESIS",
    "status":"AUDIT_OK",**meta,
    "candidate_was_retained_only_in_memory":True,
    "candidate_saved_as_drive_fragment":False,
    "user_phone_files_modified":False,
    "new_APK_built":False,
    "user_save_modified":False,
    "recompiled_guest_execution_tested":False,
    "safe_to_apply_on_phone_proven":False,
    "signing_key_accessed":False}
def main():
  p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);args=p.parse_args()
  OUT.parent.mkdir(parents=True,exist_ok=True)
  try:r=audit()
  except Exception as e:r={"stage":"PRE605_BMW_ENGINE_PARENT_LINK_ONLY_IN_RAM_HYPOTHESIS",
     "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
     "user_phone_files_modified":False,"new_APK_built":False,
     "user_save_modified":False,"signing_key_accessed":False}
  r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
  OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
  print("PRE605_STATUS",r["status"]);print("PRE605_ERROR",r.get("error_type","none"),r.get("error",""))
  return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
