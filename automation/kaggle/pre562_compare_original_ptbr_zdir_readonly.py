#!/usr/bin/env python3
"""PRE562: compare authenticated original PAL vs translated PTBR ZDIR records.

Read the two small ZDIR indices only via strict Drive HTTP206; verify exact
SHA256 before comparing. Report only bounded hash/position metadata.
Do not publish game data; no guest loader, APK, save or ZZDATA4 bytes touched.
"""
from __future__ import annotations
import argparse, hashlib, json, struct
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from pre461_zdir_candidate_hash_names_readonly import raw_zdir, INDEX_SHA
from pre459_pal_zip_car_catalog_readonly import session
from pre561_ptbr_zip_zdir_record_readonly import zip_directory,member_zdir,ZDIR_SHA,NAMES
OUT=Path("/tmp/nfsmw-pre562/report.json")
def unpack(data):
 if len(data)%24:raise ValueError("Invalid ZDIR stride")
 groups={}
 for i,(h,a,sec,total,size,checksum) in enumerate(struct.iter_unpack("<IiIIiI",data)):
  groups.setdefault(h,[]).append({
    "row":i,"archive":a,"sector":sec,"total":total,
    "size":size,"checksum_hex":f"{checksum:08x}"
  })
 return groups
def sample(h,v):
 return {"name_hash_hex":f"{h:08x}","row":v["row"],"archive":v["archive"],
         "sector":v["sector"],"size":v["size"],"checksum_hex":v["checksum_hex"]}
def audit():
 gate=json.loads(Path("docs/PRE561_PTBR_ZIP_ZDIR_DIRECT_RECORD_READONLY.json").read_text())
 if gate.get("status")!="AUDIT_OK" or gate.get("zdir_matches_shevery_sha256") is not True:
  raise ValueError("PRE561 direct PTBR ZIP ZDIR gate not valid")
 orig=raw_zdir()
 if hashlib.sha256(orig).hexdigest()!=INDEX_SHA:raise ValueError("Original PAL ZDIR hash mismatch")
 sess=session();catalog,_=zip_directory(sess)
 matches=[e for e in catalog if e["name"].upper().endswith("NFS/ZDIR.BIN")]
 if len(matches)!=1:raise ValueError("PTBR ZIP has ambiguous index")
 translated=member_zdir(sess,matches[0])
 if hashlib.sha256(translated).hexdigest()!=ZDIR_SHA:raise ValueError("PTBR ZDIR hash mismatch")
 o=unpack(orig);t=unpack(translated)
 missing=sorted(set(o)-set(t));added=sorted(set(t)-set(o));both=set(t)&set(o)
 # Some resource hashes occur more than once. Never arbitrarily collapse them.
 single=[h for h in both if len(o[h])==1 and len(t[h])==1]
 same=sum(t[h][0]["archive"]==o[h][0]["archive"] and
          t[h][0]["sector"]==o[h][0]["sector"] and
          t[h][0]["size"]==o[h][0]["size"] and
          t[h][0]["checksum_hex"]==o[h][0]["checksum_hex"] for h in single)
 differences=[h for h in single if any(o[h][0][k]!=t[h][0][k]
                                  for k in ("archive","sector","size","checksum_hex","total"))]
 dup=set(h for h,group in o.items() if len(group)>1)|set(h for h,group in t.items() if len(group)>1)
 zero=[(h,v) for h,entries in t.items() for v in entries if v["sector"]==0]
 zeros_prev=[(h,v) for h,entries in o.items() for v in entries if v["sector"]==0]
 zero_changed=[(h,v) for h,v in zero if h in single and o[h][0]["sector"]!=0]
 attr=int(NAMES["GLOBAL_ATTRIBUTES"],16)
 if (attr not in both or len(o[attr])!=1 or len(t[attr])!=1 or
     t[attr][0]["row"]!=805 or o[attr][0]["row"]!=806):
  raise ValueError("Original/translation attributes indices mismatch")
 known_labels={int(v,16):k for k,v in NAMES.items()}
 top_changes=[]
 for h in sorted(differences,key=lambda q:(t[q][0]["sector"]!=0,t[q][0]["row"])):
  before=o[h][0];after=t[h][0]
  top_changes.append({
   "filename_hash_hex":f"{h:08x}",
   "known_label":known_labels.get(h),
   "original":sample(h,before),
   "translated":sample(h,after),
   "total_field_original":before["total"],
   "total_field_translated":after["total"]
  })
 return {
  "stage":"PRE562_ORIGINAL_PAL_VS_PTBR_ZDIR_RECORD_BY_HASH_DIFF_READONLY",
  "status":"AUDIT_OK",
  "original_sha256":INDEX_SHA,"translated_sha256":ZDIR_SHA,
  "original_record_count":len(orig)//24,"translated_record_count":len(translated)//24,
  "original_unique_filename_hashes":len(o),
  "translated_unique_filename_hashes":len(t),
  "original_hashes_with_duplicate_rows_count":sum(len(v)>1 for v in o.values()),
  "translated_hashes_with_duplicate_rows_count":sum(len(v)>1 for v in t.values()),
  "duplicate_hashes_not_assumed_unique":[f"{h:08x}" for h in sorted(dup)[:30]],
  "hashes_only_in_original_count":len(missing),
  "hashes_only_in_translated_count":len(added),
  "hashes_only_in_original":[f"{h:08x}" for h in missing[:25]],
  "hashes_only_in_translated":[f"{h:08x}" for h in added[:25]],
  "source_only_extra_row_occurrences":sum(max(0,len(o[h])-len(t.get(h,[]))) for h in o),
  "translation_only_extra_row_occurrences":sum(max(0,len(t[h])-len(o.get(h,[]))) for h in t),
  "filename_hashes_common_count":len(both),
  "unambiguous_common_hash_count":len(single),
  "unambiguous_same_archive_sector_size_checksum_count":same,
  "unambiguous_records_with_any_field_difference_count":len(differences),
  "changed_unambiguous_records_first_40":top_changes[:40],
  "original_zero_sector_count":len(zeros_prev),
  "translated_zero_sector_count":len(zero),
  "translated_zero_sector_originally_nonzero_unambiguous_count":len(zero_changed),
  "translated_zero_sector_originally_nonzero_hashes":[f"{h:08x}" for h,v in zero_changed[:25]],
  "translated_zero_sector_metadata":[
    {"name_hash_hex":f"{h:08x}",
     "known_label":known_labels.get(h),
     "translated":sample(h,v),
     "original":sample(h,o[h][0]) if h in o and len(o[h])==1 else None}
    for h,v in sorted(zero,key=lambda x:x[1]["row"])
   ],
  "attributes_record_original":sample(attr,o[attr][0]),
  "attributes_record_translated":sample(attr,t[attr][0]),
  "attributes_total_original":o[attr][0]["total"],
  "attributes_total_translated":t[attr][0]["total"],
  "translation_attributes_file_data_verified":False,
  "translation_loader_reads_attributes_at_record_offset_verified":False,
  "complete_game_archive_or_ZZDATA4_downloaded":False,
  "APK_built":False,"save_modified":False,"game_assets_modified":False,
  "signing_material_accessed":False,"BMW_tuning_enabled":False
 }
def main():
 a=argparse.ArgumentParser();a.add_argument("--run-id",required=True)
 args=a.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:
  r={"stage":"PRE562_ORIGINAL_PAL_VS_PTBR_ZDIR_RECORD_BY_HASH_DIFF_READONLY",
     "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:220],
     "complete_game_archive_or_ZZDATA4_downloaded":False,
     "APK_built":False,"save_modified":False,"game_assets_modified":False,
     "signing_material_accessed":False,"BMW_tuning_enabled":False}
 r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE562_STATUS",r["status"],flush=True)
 print("PRE562_DIFF_RECORDS",r.get("unambiguous_records_with_any_field_difference_count"),flush=True)
 print("PRE562_ZERO_SECTORS",r.get("translated_zero_sector_count"),flush=True)
 print("PRE562_ZERO_CHANGED",r.get("translated_zero_sector_originally_nonzero_count"),flush=True)
 print("PRE562_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
