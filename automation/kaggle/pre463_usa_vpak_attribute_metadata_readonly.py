#!/usr/bin/env python3
"""PRE463: read original USA 697856-byte VPAK attribute database for format metadata.
Game-file bytes stay only in private ephemeral runner. No modified game assets,
no save access or APK generation, USA not assumed equivalent to PAL.
"""
from __future__ import annotations
import argparse,hashlib,json,re,struct
from datetime import datetime,timezone
from pathlib import Path
from pre462_usa_raw_iso_attributes_readonly import Reader,PARTITION_BASE,EXPECTED_NFS_SECTOR,SECTOR,dir_entries,NAMES
OUT=Path("/tmp/nfsmw-pre463/report.json")
TARGET_HASH=NAMES["GLOBAL\\ATTRIBUTES.BIN"]
def locate():
    reader=Reader()
    nfs=reader.read(PARTITION_BASE+EXPECTED_NFS_SECTOR*SECTOR,2048)
    entries=dir_entries(nfs)
    byname={x["name"].upper():x for x in entries}
    z=byname.get("ZDIR.BIN")
    if z is None or not (0<z["size"]<90000):raise ValueError("ZDIR missing/bad size")
    data=reader.read(PARTITION_BASE+z["sector"]*SECTOR,z["size"])
    if len(data)%24:raise ValueError("Invalid ZDIR alignment")
    candidates=[]
    for h,archive,sector,_total,size,checksum in struct.iter_unpack("<IiIIiI",data):
        if h!=TARGET_HASH:continue
        blob=byname.get("ZZDATA"+str(archive)+".BIN")
        if blob is None or not (0<size<=1024*1024):raise ValueError("Unexpected VPAK blob")
        offset=sector*SECTOR
        if offset+size>blob["size"]:raise ValueError("VPAK outside ZZDATA")
        candidates.append({"archive":archive,"offset":offset,"size":size,
                           "absolute_offset":PARTITION_BASE+blob["sector"]*SECTOR+offset})
    if len(candidates)!=1:raise ValueError("Unique ATTRIBUTES.BIN record expected")
    return reader,candidates[0]

def audit():
    r,loc=locate()
    raw=r.read(loc["absolute_offset"],loc["size"])
    if raw[:4]!=b"VPAK":raise ValueError("Resource is not VPAK")
    n,string_off,string_len=struct.unpack_from("<III",raw,4)
    if not (0<n<=128 and 0<string_off<len(raw) and 0<string_len<len(raw)-string_off):
        raise ValueError("Unexpected VPAK header bounds")
    vaults=[]
    for i in range(n):
        base=16+i*20
        if base+20>len(raw):raise ValueError("VPAK metadata truncated")
        name_local,bin_size,vlt_size,bin_off,vlt_off=struct.unpack_from("<IIIII",raw,base)
        absolute_name=string_off+name_local
        if absolute_name>=string_off+string_len:raise ValueError("VPAK name outside string region")
        end=raw.find(b"\x00",absolute_name,string_off+string_len+1)
        if end<0:raise ValueError("VPAK unterminated vault name")
        name=raw[absolute_name:end].decode("ascii","replace")
        within=bin_off+bin_size<=len(raw) and vlt_off+vlt_size<=len(raw)
        vaults.append({"name":name,"bin_offset":bin_off,"bin_bytes":bin_size,
                       "vlt_offset":vlt_off,"vlt_bytes":vlt_size,
                       "sections_within_file":within,
                       "bin_head_hex":raw[bin_off:bin_off+8].hex() if within else None,
                       "vlt_head_hex":raw[vlt_off:vlt_off+8].hex() if within else None})
    if not all(v["sections_within_file"] for v in vaults):
        raise ValueError("VPAK section metadata is inconsistent")
    tokens=[s.decode("latin-1","replace") for s in re.findall(
        rb"[A-Za-z][A-Za-z0-9_./\\-]{3,80}",raw)]
    pattern=re.compile(r"(BMW|M3GTR|UPGRADE|PERFORMANCE|TUNING|SUSPENSION|BRAKES|ENGINE|TRANSMISSION|INDUCTION|NITRO|JUNKMAN|RACERS)",re.I)
    candidates=[s for s in tokens if pattern.search(s)]
    unique=list(dict.fromkeys(candidates))
    return {"stage":"PRE463_USA_VPAK_STRUCTURE_PRIVATE_READONLY",
      "status":"AUDIT_OK","source_edition":"USA reference, NOT PAL",
      "relative_location":loc,"vpak_sha256":hashlib.sha256(raw).hexdigest(),
      "vpak_bytes":len(raw),"header_magic":"VPAK",
      "header_num_vaults":n,"header_strings_offset":string_off,
      "header_strings_length":string_len,"vaults":vaults,
      "matched_ascii_token_occurrences":len(candidates),
      "matched_unique_ascii_token_count":len(unique),
      "matched_unique_ascii_tokens_sample":unique[:120],
      "bmw_tuning_part_ids_verified":False,"vpak_field_semantics_verified":False,
      "pal_binary_equivalence_verified":False,
      "strict_range_bytes_transferred":r.total,
      "raw_game_assets_published":False,"source_iso_edited":False,
      "apk_built":False,"save_modified":False,"feature_enabled":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=audit()
    except Exception as e:result={"stage":"PRE463_USA_VPAK_STRUCTURE_PRIVATE_READONLY",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
      "apk_built":False,"save_modified":False}
    result["run_id"]=args.run_id;result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("PRE463_STATUS",result["status"])
    print("PRE463_VAULTS",result.get("vaults",[]))
    print("PRE463_TOKENS",result.get("matched_unique_ascii_token_count","?"))
    print("PRE463_ERROR",result.get("error","none"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
