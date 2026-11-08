#!/usr/bin/env python3
"""PRE469: resolve Legacy AttribSys class hashes from full BIN printable names.
PRE468 collection export relationships + PRE463 authenticated VPAK source.
Does not confuse full BIN type names with StrE instance name table.
No writable files, save mutation, APK build or modified performance values.
"""
from __future__ import annotations
import argparse,hashlib,json,re,struct
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import hash32,EXPECTED_VPAK_SHA

OUT=Path("/tmp/nfsmw-pre469/report.json")
PRE468=Path("docs/PRE468_USA_BMW_VLT_COLLECTION_RELATIONSHIPS_READONLY.json")
NEEDLES=("UpgradeSpecs","eFEPartUpgradeLevels","JunkmanMod",
         "BMWM3GTR","bmwm3gtr","m3gtre46careerstart",
         "EngineRacer","SuspensionRacer")
def parse():
    old=json.loads(PRE468.read_text())
    if (old.get("status"),old.get("source_vpak_sha256"))!=("AUDIT_OK",EXPECTED_VPAK_SHA):
        raise ValueError("PRE468 source proof unavailable")
    reader,loc=locate()
    raw=reader.read(loc["absolute_offset"],loc["size"])
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_VPAK_SHA:raise ValueError("Source VPAK SHA changed")
    _,binlen,_vltlen,binoff,_vltoff=struct.unpack_from("<IIIII",raw,16)
    bin_data=raw[binoff:binoff+binlen]
    if bin_data[:4]!=b"StrE":raise ValueError("BIN source changed")
    strings_end=int.from_bytes(bin_data[4:8],"big")
    if not (8<strings_end<len(bin_data)):raise ValueError("Unexpected StrE end")
    rx=rb"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_./\\:\-]{2,100}\x00"
    objects=[]
    for m in re.finditer(rx,bin_data):
        text=m.group()[:-1].decode("ascii","replace")
        objects.append((text,m.start()))
    hmap=defaultdict(list)
    for value,offset in objects:
        if not any(x["name"]==value for x in hmap[hash32(value)]):
            hmap[hash32(value)].append({"name":value,"bin_offset":offset,
                   "inside_StrE":offset<strings_end})
    cls=[]
    for c in old["named_class_headers"]:
        h=int(c["class_hash"],16)
        cls.append({**c,"resolved_full_bin_names":hmap.get(h,[])[:6]})
    targets={}
    for name,rows in old["target_rows"].items():
        targets[name]=[]
        for r in rows:
            cls_h=int(r["class_hash"],16)
            par_h=int(r["parent_hash"],16)
            targets[name].append({**r,
                "full_bin_class_name_candidates":hmap.get(cls_h,[])[:6],
                "full_bin_parent_name_candidates":hmap.get(par_h,[])[:4]})
    field_probe={}
    for name in NEEDLES:
        field_probe[name]={
          "lookup2":f"{hash32(name):08x}",
          "full_bin_name_entries":hmap.get(hash32(name),[])[:6],
          "appears_as_class_header":any(x["class_hash"]==f"{hash32(name):08x}" for x in cls),
          "appears_as_pre468_target_collection":bool(old["target_rows"].get(name))
        }
    known=sum(bool(c["resolved_full_bin_names"]) for c in cls)
    return {"stage":"PRE469_USA_BMW_FULL_BIN_CLASS_NAMES_READONLY",
      "status":"AUDIT_OK","vpak_sha256":EXPECTED_VPAK_SHA,
      "pal_byte_identity_confirmed_in_PRE467":True,
      "source_class_hash_count":len(cls),
      "class_hashes_resolved_by_full_bin_strings":known,
      "all_string_candidates_count":len(objects),
      "preStrE_string_count":sum(off<strings_end for _,off in objects),
      "postStrE_string_count":sum(off>=strings_end for _,off in objects),
      "verified_class_name_candidates":cls,
      "bmw_variant_collections_with_class_candidates":targets,
      "related_field_and_class_identities":field_probe,
      "class_name_hash_matches_do_not_identify_upgrade_level_or_part_ids":True,
      "mod_enabled":False,"signed_apk_built":False,
      "game_assets_exported":False,"save_modified":False,
      "range_bytes":reader.total}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=parse()
    except Exception as e:r={"stage":"PRE469_USA_BMW_FULL_BIN_CLASS_NAMES_READONLY",
          "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
          "mod_enabled":False,"signed_apk_built":False,"save_modified":False}
    r["utc"]=datetime.now(timezone.utc).isoformat();r["run_id"]=a.run_id
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE469_STATUS",r["status"],flush=True)
    print("PRE469_CLASSES_RESOLVED",r.get("class_hashes_resolved_by_full_bin_strings"),flush=True)
    print("PRE469_TARGET_BMW_CLASSES",{
      k:[x["full_bin_class_name_candidates"] for x in v] for k,v in r.get("bmw_variant_collections_with_class_candidates",{}).items()
      if k in ("bmwm3gtr","m3gtre46careerstart")},flush=True)
    print("PRE469_ERROR",r.get("error","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
