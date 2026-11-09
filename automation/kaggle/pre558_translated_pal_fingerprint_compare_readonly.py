#!/usr/bin/env python3
"""PRE558: compare Shevery user-reported translated-folder hashes against pinned
original PAL hashes; never claim this CI read the phone or its files.
Metadata-only. No APK, original game files, translated files or saves written.
"""
from __future__ import annotations
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
OUT=Path("/tmp/nfsmw-pre558/report.json")
EV=Path("docs/PRE558_SHEVERY_TRANSLATED_PAL_FINGERPRINTS_USER_REPORTED_20261108.json")
P555=Path("docs/PRE555_PAL_EXTRACTED_FOLDER_HOSTPATH_VFS_READONLY.json")
P557=Path("docs/PRE557_ORIGINAL_PAL_ZZDATA4_FULL_SHA256_READONLY.json")
P551=Path("docs/PRE551_PAL_ORIGINAL_ZZDATA4_PADDING_AND_VIRTUAL_RESOURCE_READONLY.json")
PAL_ZDIR="7f37d29f958454ec73d5dbd30068a6acb23cf92d5056fa2d944ca5c87c6637ee"
PAL_ZZ="8b0e6c09b9e55e78d319521b634119055ad6fb2f144aa13660f60bdea7cf05d3"
REPORTED_ZDIR="832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf"
REPORTED_ZZ="7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951"
def load(p):
 v=json.loads(p.read_text())
 return v
def audit():
 u=load(EV);p555=load(P555);p557=load(P557);p551=load(P551)
 if (p555.get("status")!="AUDIT_OK" or p557.get("status")!="AUDIT_OK" or
     p551.get("status")!="AUDIT_OK" or
     p555.get("user_reported_current_game_source")!="EXTRACTED_FOLDER_NOT_ISO" or
     p557.get("original_pal_uncompressed_member_sha256")!=PAL_ZZ or
     p557.get("original_pal_ZDIR_sha256")!=PAL_ZDIR or
     p551.get("source_PAL_original_ZDIR_sha256")!=PAL_ZDIR or
     p551.get("source_PAL_index_row")!=806):
  raise ValueError("Original PAL source anchors or folder evidence differ")
 if (u.get("origin")!="Direct text output pasted by the user from Shevery in current chat; not an independent connected device read" or
     u.get("paths_disclosed") is not False or
     len(u.get("files",[]))!=2):
  raise ValueError("Shevery-provided evidence provenance invalid")
 docs={x["name"]:x for x in u["files"]}
 expected={"NFS/ZDIR.BIN":(33312,REPORTED_ZDIR),
           "NFS/ZZDATA4.BIN":(401068032,REPORTED_ZZ)}
 if set(docs)!=set(expected):
  raise ValueError("Unexpected translated file names")
 for path,(size,digest) in expected.items():
  entry=docs[path]
  if (entry.get("bytes")!=size or entry.get("sha256")!=digest or
      len(digest)!=64 or not all(x in "0123456789abcdef" for x in digest)):
   raise ValueError("User report changed for "+path)
 original_size=1390*24
 translated_size=docs["NFS/ZDIR.BIN"]["bytes"]
 if (original_size-translated_size!=48 or
     original_size%24 or translated_size%24 or
     expected["NFS/ZZDATA4.BIN"][0]!=p557["original_pal_uncompressed_member_bytes"]):
  raise ValueError("PAL structural comparison no longer matches")
 return {
  "stage":"PRE558_ORIGINAL_VS_TRANSLATED_PAL_ZDIR_ZZDATA4_FINGERPRINT_COMPARE",
  "status":"AUDIT_OK",
  "translated_source_provenance":"USER_PASTED_SHEVERY_HASHES_NOT_REMOTE_FILE_VERIFICATION",
  "user_current_game_root":"EXTRACTED_FOLDER_PAL_PTBR_REPORTED",
  "original_pal_ZDIR_bytes":original_size,
  "translated_pal_ZDIR_bytes_reported":translated_size,
  "original_pal_ZDIR_sha256":PAL_ZDIR,
  "translated_pal_ZDIR_sha256_reported":REPORTED_ZDIR,
  "translated_zdir_size_difference_bytes":original_size-translated_size,
  "original_zdir_record_count_assuming_24_byte_rows":1390,
  "translated_zdir_record_count_assuming_same_24_byte_rows":translated_size//24,
  "size_delta_equivalent_record_count":(original_size-translated_size)//24,
  "which_entries_changed_identified":False,
  "original_ZDIR_row_806_transferable_to_translation":False,
  "original_pal_ZZDATA4_bytes":p557["original_pal_uncompressed_member_bytes"],
  "translated_pal_ZZDATA4_bytes_reported":expected["NFS/ZZDATA4.BIN"][0],
  "original_pal_ZZDATA4_sha256":PAL_ZZ,
  "translated_pal_ZZDATA4_sha256_reported":REPORTED_ZZ,
  "same_ZZDATA4_length":True,
  "same_ZZDATA4_content":False,
  "translation_attributes_resource_offset_verified":False,
  "translation_ATTRIBUTES_VPAK_SHA256_verified":False,
  "original_PAL_global_attributes_name_hash_hex":"9775379a",
  "prior_original_PAL_global_attributes_record_row":806,
  "next_gate":"READ_ONLY_TRANSLATED_ZDIR_RESOURCE_HASH_RECORD_AT_24_BYTE_GRANULARITY",
  "on_device_read_this_CI":False,
  "APK_built":False,"game_assets_modified":False,"save_modified":False,
  "signing_material_accessed":False,"BMW_tuning_enabled":False
 }
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
 a=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as ex:
  r={"stage":"PRE558_ORIGINAL_VS_TRANSLATED_PAL_ZDIR_ZZDATA4_FINGERPRINT_COMPARE",
     "status":"FAILED","error_type":type(ex).__name__,"error":str(ex)[:200],
     "on_device_read_this_CI":False,"APK_built":False,"game_assets_modified":False,
     "save_modified":False,"signing_material_accessed":False,"BMW_tuning_enabled":False}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE558_STATUS",r["status"],flush=True)
 print("PRE558_ZDIR_SIZE_DELTA",r.get("translated_zdir_size_difference_bytes"),flush=True)
 print("PRE558_ZZDATA_CONTENT_SAME",r.get("same_ZZDATA4_content"),flush=True)
 print("PRE558_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
