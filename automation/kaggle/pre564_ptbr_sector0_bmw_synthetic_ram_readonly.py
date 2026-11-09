#!/usr/bin/env python3
"""PRE564: translated PAL in-memory ZDIR + synthetic BMW engine VPAK resource,
no original game-data write. Reuse authenticated PRE502 synthetic scratch
with PRE563 translation's byte-exact original VPAK at sector zero.
Not execution of the guest loader, no FE purchase, no real tuning.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from datetime import datetime,timezone
from pathlib import Path
from pre459_pal_zip_car_catalog_readonly import session
from pre561_ptbr_zip_zdir_record_readonly import zip_directory,member_zdir,ZDIR_SHA
from pre502_bmw_engine_combined_level1_scratch import audit as build_scratch
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash
OUT=Path("/tmp/nfsmw-pre564/report.json")
ROW=805;SIZE=698004;ORIG=697856;RESERVED=698368;NEW_EA=0x4d05584a
NEW_SHA="d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6"
OLD_RESOURCE_SHA="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad"
OLD_EA=0x296ad9ed
TARGET_HASH=0x9775379a
def audit():
 p563=json.loads(Path("docs/PRE563_PTBR_ZZDATA4_ATTRIBUTES_FIRST_REGION_READONLY.json").read_text())
 p562=json.loads(Path("docs/PRE562_ORIGINAL_VS_PTBR_ZDIR_RECORD_DIFF_READONLY.json").read_text())
 p518=json.loads(Path("docs/PRE518_BMW_RAM_VPAK_ZDIR_CHECKSUM_READONLY.json").read_text())
 if (p563.get("status")!="AUDIT_OK" or
     p563.get("first_resource_identical_to_original_PAL_ATTRIBUTES_VPAK") is not True or
     p563.get("first_region_trailing_all_zero") is not True or
     p563.get("first_next_positive_ZZDATA4_sector_from_ZDIR")!=341 or
     p563.get("translated_ZZDATA4_full_file_matches_Shevery_SHA256") is not True or
     p562.get("status")!="AUDIT_OK" or
     p562.get("attributes_record_translated",{}).get("row")!=ROW or
     p562.get("attributes_record_translated",{}).get("sector")!=0 or
     p518.get("status")!="AUDIT_OK" or
     p518.get("synthetic_scratch_VPAK_sha256")!=NEW_SHA or
     p518.get("synthetic_scratch_VPAK_bytes")!=SIZE or
     p518.get("synthetic_scratch_EA_data_hash_hex")!=f"{NEW_EA:08x}"):
  raise ValueError("PRE563 PTBR resource identity or PRE502/518 scratch boundaries not met")
 s=session();entries,cd_sha=zip_directory(s)
 targets=[e for e in entries if e["name"].upper().endswith("NFS/ZDIR.BIN")]
 if len(targets)!=1:raise ValueError("PTBR source index ambiguous")
 zdir=member_zdir(s,targets[0])
 row=struct.unpack_from("<IiIIiI",zdir,ROW*24)
 if row!=(TARGET_HASH,4,0,0,ORIG,OLD_EA):
  raise ValueError("Translated attribute index original row differs")
 found=[i for i,(hashname,arch,sec,total,sz,ck) in
        enumerate(struct.iter_unpack("<IiIIiI",zdir)) if hashname==TARGET_HASH]
 if found!=[ROW]:raise ValueError("Duplicated translated attributes hash")
 def virtual_read(scratch:bytes):
  if (len(scratch)!=SIZE or hashlib.sha256(scratch).hexdigest()!=NEW_SHA or
      ea_data_hash(scratch)!=NEW_EA):
   raise ValueError("Scratch VPAK bytes/checksum changed")
  # Simulate the sector-0 data region from the authenticated source translation,
  # verified in PRE563; source folder and Drive bytes are NEVER modified.
  region=bytearray(RESERVED)
  region[:len(scratch)]=scratch
  virtual_zdir=bytearray(zdir)
  struct.pack_into("<i",virtual_zdir,ROW*24+16,SIZE)
  struct.pack_into("<I",virtual_zdir,ROW*24+20,NEW_EA)
  if(zdir[:ROW*24]!=virtual_zdir[:ROW*24] or
     zdir[(ROW+1)*24:]!=virtual_zdir[(ROW+1)*24:] or
     bytes(region[SIZE:])!=bytes(RESERVED-SIZE)):
   raise ValueError("Unexpected simulation changes outside attributes")
  h,a,sec,total,sz,crc=struct.unpack_from("<IiIIiI",virtual_zdir,ROW*24)
  if (h,a,sec,total,sz,crc)!=(TARGET_HASH,4,0,0,SIZE,NEW_EA):
   raise ValueError("Synthetic translated ZDIR target record inconsistent")
  virtual_region=bytes(region[sec*2048:sec*2048+sz])
  if(hashlib.sha256(virtual_region).hexdigest()!=NEW_SHA or
     ea_data_hash(virtual_region)!=NEW_EA):
   raise ValueError("Virtual translated archive readback failed")
  oldrec=zdir[ROW*24:ROW*24+24];newrec=virtual_zdir[ROW*24:ROW*24+24]
  changed=[i for i,(x,y) in enumerate(zip(oldrec,newrec)) if x!=y]
  if changed!=[16,20,21,22,23]:
   raise ValueError("Unexpected byte-diff set inside translated index row")
  return {
    "translated_virtual_ZDIR_record_SHA256":hashlib.sha256(newrec).hexdigest(),
    "translated_virtual_ZDIR_all_other_bytes_unchanged":True,
    "translated_virtual_ZDIR_target_modified_byte_offsets":changed,
    "translated_virtual_synthetic_resource_SHA256":NEW_SHA,
    "translated_virtual_EA_crc_hex":f"{NEW_EA:08x}",
    "translated_virtual_attributes_offset_bytes":0,
    "translated_virtual_reserved_bytes":RESERVED,
    "translated_virtual_remaining_sector_padding_zero_bytes":RESERVED-SIZE,
    "translated_virtual_ZDIR_readback_matches_synthetic_bmw_scratch":True,
    "translated_virtual_nontarget_archive_sectors_unchanged_in_this_memory_model":True
  }
 prototype=build_scratch(consume_scratch=virtual_read)
 proof=prototype.pop("_private_scratch_analysis",None)
 if (prototype.get("status")!="AUDIT_OK" or
     prototype.get("scratch_vpak_bytes")!=SIZE or
     prototype.get("new_engine_ExpN_RefSpec_PtrN_reparsed") is not True or
     prototype.get("safe_to_enable_or_build_tuning") is not False or
     proof is None):
  raise ValueError("PRE502 original scratch reconstruction invalid")
 return {
  "stage":"PRE564_PTBR_SECTOR0_ZDIR_BMW_SYNTHETIC_IN_RAM_RESOURCE_LOOKUP",
  "status":"AUDIT_OK",
  "translated_source_ZDIR_sha256":ZDIR_SHA,
  "translated_source_original_attributes_resource_sha256":OLD_RESOURCE_SHA,
  "translated_source_index_row":ROW,
  "translated_source_resource_sector":0,
  "translated_source_original_attributes_size":ORIG,
  "source_translation_nontarget_files_not_loaded_or_modified":True,
  "synthetic_engine_torque_gain_bp":500,
  "synthetic_engine_upgrade_counter_from_to":"0->1",
  "PRE502_synthetic_new_engine_reparsed":True,
  **proof,
  "synthetic_overlay_created_only_in_private_RAM":True,
  "original_translated_game_file_written":False,
  "modified_ptbr_ZDIR_or_ZZDATA4_exported":False,
  "real_guest_loader_executed":False,
  "real_BMW_tuning_installed":False,
  "frontend_price_and_checkout_validated":False,
  "save_persistence_validated":False,
  "APK_built":False,"save_modified":False,"signing_material_accessed":False,
  "BMW_tuning_enabled":False
 }
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:
  r={"stage":"PRE564_PTBR_SECTOR0_ZDIR_BMW_SYNTHETIC_IN_RAM_RESOURCE_LOOKUP",
     "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
     "original_translated_game_file_written":False,"APK_built":False,
     "save_modified":False,"signing_material_accessed":False,"BMW_tuning_enabled":False}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE564_STATUS",r["status"],flush=True)
 print("PRE564_ZDIR_BYTE_OFFSETS",r.get("translated_virtual_ZDIR_target_modified_byte_offsets"),flush=True)
 print("PRE564_VPAK_RAM_READBACK",r.get("translated_virtual_ZDIR_readback_matches_synthetic_bmw_scratch"),flush=True)
 print("PRE564_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
